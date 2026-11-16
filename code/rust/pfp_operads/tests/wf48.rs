//! WF48, commit-reveal with a hostile mutation gate: the manifest commitment, the commit and
//! reveal, the three registered checkers and the mutants they must reject.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf48-tests:v1

use pfp_operads::families::wf48::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

/// The digest of a salt, a zero byte and the canonical form of a value.
fn commit(salt: &str, artifact: &Value) -> String {
    let mut bytes = salt.as_bytes().to_vec();
    bytes.push(0);
    bytes.extend(artifact.to_string().as_bytes());
    hex::encode(Sha256::digest(bytes))
}

fn manifest(checkers: Value) -> Value {
    json!({ "checkers": checkers })
}

fn standard() -> Value {
    manifest(json!(["residual.v1", "tree_integration.v1"]))
}

fn task_with(manifest: &Value, salt: &str) -> Value {
    json!({
        "statement": "Commit to a potential phi with delta phi = c, then reveal it.",
        "edges": [[0, 1], [1, 2], [2, 0], [2, 3]],
        "c": [1, 2, -3, 1],
        "judge_manifest": manifest,
        "manifest_commitment": commit(salt, manifest),
    })
}

fn task() -> Value {
    task_with(&standard(), "judge-salt-17")
}

fn sealed() -> Value {
    json!({"manifest_salt": "judge-salt-17"})
}

fn phi() -> Value {
    json!([0, 1, 3, 4])
}

fn committed(artifact: &Value) -> Value {
    json!({ "commitment": commit("s4lt", artifact) })
}

fn revealed(artifact: &Value) -> Value {
    json!({"salt": "s4lt", "artifact": artifact})
}

fn request(task: &Value, sealed: &Value, replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF48", "task": task, "sealed": sealed, "replies": replies}).to_string()
}

fn run_with(task: &Value, sealed: &Value, replies: Vec<Value>) -> (bool, Value) {
    let replies: Vec<Option<Value>> = replies.into_iter().map(Some).collect();
    match judge(&request(task, sealed, &replies)) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn run_task(task: &Value, artifact: &Value) -> (bool, Value) {
    run_with(
        task,
        &sealed(),
        vec![committed(artifact), revealed(artifact)],
    )
}

fn run(artifact: &Value) -> (bool, Value) {
    run_task(&task(), artifact)
}

fn outcomes(report: &Value) -> Vec<(&str, bool)> {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| {
            (
                row["name"].as_str().expect("a name"),
                row["passed"].as_bool().expect("an outcome"),
            )
        })
        .collect()
}

fn malformed(replies: Vec<Value>) -> String {
    let (passed, report) = run_with(&task(), &sealed(), replies);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    report["detail"]["reason"]
        .as_str()
        .expect("a reason")
        .to_owned()
}

fn bad_task(task: &Value, sealed: &Value) -> String {
    match judge(&request(task, sealed, &[])) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

#[test]
fn the_registry_names_the_family() {
    assert_eq!(FAMILY.workflow, "WF48");
    assert_eq!(FAMILY.name, "Commit-reveal with a hostile mutation gate");
    assert_eq!(FAMILY.host_check, "dual_checker_mutation_suite");
}

#[test]
fn a_committed_artifact_that_both_checkers_hold_to_is_certified() {
    let (passed, report) = run(&phi());
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "COMMIT_REVEAL_CERTIFIED");
    assert_eq!(
        report["detail"],
        json!({"kills": {"residual.v1": "12/12", "tree_integration.v1": "12/12"}})
    );
    let names = [
        "manifest_commitment_matches",
        "two_independent_registered_checkers",
        "reveal_matches_commitment",
        "residual.v1:accepts_artifact_and_gauge",
        "residual.v1:kills_every_mutant",
        "tree_integration.v1:accepts_artifact_and_gauge",
        "tree_integration.v1:kills_every_mutant",
    ];
    let held: Vec<(&str, bool)> = names.iter().map(|name| (*name, true)).collect();
    assert_eq!(outcomes(&report), held);
    let digests: Vec<&str> = report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| row["evidence_sha256"].as_str().expect("a digest"))
        .collect();
    let checkers = sha(r#"["residual.v1","tree_integration.v1"]"#);
    let kills = sha(r#""12/12""#);
    let given = commit("s4lt", &phi());
    assert_eq!(
        digests,
        [
            checkers.clone(),
            checkers,
            sha(&format!("\"{given}\"")),
            kills.clone(),
            kills.clone(),
            kills.clone(),
            kills,
        ]
    );
}

#[test]
fn the_commit_and_the_reveal_are_asked_in_turn_with_the_commitment_between() {
    let given = commit("s4lt", &phi());
    let asked = |replies: Vec<Option<Value>>| match next(&request(&task(), &sealed(), &replies)) {
        Outcome::Pass { result } => result,
        other => panic!("expected a turn, got {other:?}"),
    };
    let first = asked(vec![]);
    assert_eq!(first["ask"]["stage"], "commit");
    let prompt = first["ask"]["prompt"].as_str().expect("a prompt");
    assert!(prompt
        .starts_with("WF48 Commit-reveal with a hostile mutation gate. Commit to a potential"));
    assert!(prompt.ends_with("\nCommit H(salt || potential) only."));
    assert!(!prompt.contains("judge-salt-17"));
    let second = asked(vec![Some(committed(&phi()))]);
    assert_eq!(second["ask"]["stage"], "reveal");
    let prompt = second["ask"]["prompt"].as_str().expect("a prompt");
    assert!(prompt.ends_with(&format!("\nCommitment recorded: {given}\nReveal now.")));
    let opening = first["ask"]["prompt"].as_str().expect("a prompt");
    let opening = opening.strip_suffix("\nCommit H(salt || potential) only.");
    assert!(prompt.starts_with(opening.expect("the commit line")));
    let done = asked(vec![Some(committed(&phi())), Some(revealed(&phi()))]);
    assert_eq!(done["ask"], Value::Null);
}

fn task_on(checkers: &Value, edges: &Value, c: &Value) -> Value {
    let mut task = task_with(&manifest(checkers.clone()), "judge-salt-17");
    task["edges"] = edges.clone();
    task["c"] = c.clone();
    task
}

#[test]
fn the_residual_lets_each_part_of_a_graph_float_and_the_tree_integral_does_not() {
    let both = json!(["residual.v1", "tree_integration.v1"]);
    let split = task_on(&both, &json!([[0, 1], [2, 3]]), &json!([1, 1]));
    let (passed, report) = run_task(&split, &json!([0, 1, 10, 11]));
    assert!(!passed);
    assert_eq!(
        report["code"],
        "TREE_INTEGRATION.V1:ACCEPTS_ARTIFACT_AND_GAUGE"
    );
    let outcomes = outcomes(&report);
    assert!(outcomes.contains(&("residual.v1:accepts_artifact_and_gauge", true)));
    assert!(outcomes.contains(&("residual.v1:kills_every_mutant", true)));
    let (passed, _) = run_task(&split, &json!([0, 1, 0, 1]));
    assert!(passed);
}

#[test]
fn a_checker_that_only_counts_values_counts_the_vertices_and_not_the_edges() {
    let checkers = json!(["residual.v1", "length_only.v1"]);
    let five = task_on(
        &checkers,
        &json!([[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]]),
        &json!([1, 2, -3, 1, -4]),
    );
    let (passed, report) = run_task(&five, &phi());
    assert!(!passed);
    assert_eq!(report["code"], "LENGTH_ONLY.V1:KILLS_EVERY_MUTANT");
    assert_eq!(
        report["detail"]["kills"],
        json!({"length_only.v1": "1/12", "residual.v1": "12/12"})
    );
}

#[test]
fn a_graph_with_one_vertex_has_its_potential_read_at_that_vertex() {
    let checkers = json!(["tree_integration.v1", "residual.v1"]);
    let loop_only = task_on(&checkers, &json!([[0, 0]]), &json!([0]));
    let (passed, report) = run_task(&loop_only, &json!([5]));
    assert!(!passed);
    assert_eq!(report["code"], "TREE_INTEGRATION.V1:KILLS_EVERY_MUTANT");
    assert_eq!(report["detail"]["kills"]["tree_integration.v1"], "1/3");
}

#[test]
fn an_artifact_shifted_by_a_constant_is_the_same_potential() {
    for shifted in [
        json!([5, 6, 8, 9]),
        json!([-7, -6, -4, -3]),
        json!([0, 1, 3, 4]),
    ] {
        let (passed, report) = run(&shifted);
        assert!(passed, "{shifted}: {report}");
    }
}

#[test]
fn a_reveal_that_is_not_what_was_committed_is_refused() {
    let replies = vec![committed(&json!([0, 1, 3, 5])), revealed(&phi())];
    let (passed, report) = run_with(&task(), &sealed(), replies);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "ARTIFACT_CHANGED_AFTER_COMMIT");
    assert_eq!(report["detail"], json!({}));
    assert_eq!(
        outcomes(&report),
        [
            ("manifest_commitment_matches", true),
            ("two_independent_registered_checkers", true),
            ("reveal_matches_commitment", false),
        ]
    );
}

#[test]
fn the_reveal_must_use_the_salt_that_was_committed_with() {
    let replies = vec![
        committed(&phi()),
        json!({"salt": "other", "artifact": phi()}),
    ];
    let (_, report) = run_with(&task(), &sealed(), replies);
    assert_eq!(report["code"], "ARTIFACT_CHANGED_AFTER_COMMIT");
    let replies = vec![committed(&phi()), json!({"salt": "", "artifact": phi()})];
    let (_, report) = run_with(&task(), &sealed(), replies);
    assert_eq!(report["code"], "ARTIFACT_CHANGED_AFTER_COMMIT");
    let replies = vec![
        json!({"commitment": commit("s4lt", &phi()).to_uppercase()}),
        revealed(&phi()),
    ];
    let (_, report) = run_with(&task(), &sealed(), replies);
    assert_eq!(report["code"], "ARTIFACT_CHANGED_AFTER_COMMIT");
}

#[test]
fn the_commitment_is_a_zero_byte_between_the_salt_and_the_artifact() {
    let glued = sha(&format!("s4lt{}", phi()));
    let replies = vec![json!({"commitment": glued}), revealed(&phi())];
    let (_, report) = run_with(&task(), &sealed(), replies);
    assert_eq!(report["code"], "ARTIFACT_CHANGED_AFTER_COMMIT");
    let spaced = sha(&format!("s4lt {}", phi()));
    let replies = vec![json!({"commitment": spaced}), revealed(&phi())];
    let (_, report) = run_with(&task(), &sealed(), replies);
    assert_eq!(report["code"], "ARTIFACT_CHANGED_AFTER_COMMIT");
}

#[test]
fn an_artifact_that_is_not_the_potential_is_refused_by_both_checkers() {
    let (passed, report) = run(&json!([0, 1, 3, 5]));
    assert!(!passed);
    assert_eq!(report["code"], "RESIDUAL.V1:ACCEPTS_ARTIFACT_AND_GAUGE");
    let held = outcomes(&report);
    assert_eq!(held[3], ("residual.v1:accepts_artifact_and_gauge", false));
    assert_eq!(
        held[5],
        ("tree_integration.v1:accepts_artifact_and_gauge", false)
    );
    assert_eq!(
        report["detail"]["failed"].as_array().expect("failed")[0],
        "residual.v1:accepts_artifact_and_gauge"
    );
}

#[test]
fn only_the_mutant_that_lowers_a_wrong_entry_back_to_the_potential_is_accepted() {
    let (_, report) = run(&json!([0, 1, 3, 5]));
    assert_eq!(
        report["detail"]["kills"],
        json!({"residual.v1": "11/12", "tree_integration.v1": "11/12"})
    );
}

#[test]
fn a_potential_of_the_wrong_length_is_rejected_whatever_it_holds() {
    for short in [json!([0, 1, 3]), json!([]), json!([0, 1, 3, 4, 5])] {
        let (passed, report) = run(&short);
        assert!(!passed, "{short}");
        assert_eq!(
            report["code"], "RESIDUAL.V1:ACCEPTS_ARTIFACT_AND_GAUGE",
            "{short}"
        );
    }
    let (_, report) = run(&json!([]));
    assert_eq!(report["detail"]["kills"]["residual.v1"], "1/1");
    let (_, report) = run(&json!([0, 1, 3, 4, 5]));
    assert_eq!(report["detail"]["kills"]["residual.v1"], "14/15");
}

#[test]
fn a_checker_that_only_counts_values_lets_every_mutant_but_one_live() {
    let weak = manifest(json!(["residual.v1", "length_only.v1"]));
    let (passed, report) = run_task(&task_with(&weak, "judge-salt-17"), &phi());
    assert!(!passed);
    assert_eq!(report["code"], "LENGTH_ONLY.V1:KILLS_EVERY_MUTANT");
    assert_eq!(
        report["detail"]["kills"],
        json!({"residual.v1": "12/12", "length_only.v1": "1/12"})
    );
    assert_eq!(
        outcomes(&report)[3..],
        [
            ("residual.v1:accepts_artifact_and_gauge", true),
            ("residual.v1:kills_every_mutant", true),
            ("length_only.v1:accepts_artifact_and_gauge", true),
            ("length_only.v1:kills_every_mutant", false),
        ]
    );
    assert_eq!(
        report["detail"]["failed"],
        json!(["length_only.v1:kills_every_mutant"])
    );
}

#[test]
fn the_mutants_are_the_bumps_the_unequal_swaps_and_the_truncation() {
    let weak = manifest(json!(["length_only.v1", "residual.v1"]));
    let cases = [
        (json!([0, 1, 3, 4]), "1/12"),
        (json!([0, 0, 0, 0]), "1/9"),
        (json!([7, 7, 2, 2]), "1/10"),
        (json!([3, 1, 4, 1]), "1/12"),
    ];
    for (artifact, killed) in cases {
        let (_, report) = run_task(&task_with(&weak, "judge-salt-17"), &artifact);
        assert_eq!(
            report["detail"]["kills"]["length_only.v1"], killed,
            "{artifact}"
        );
    }
    let (_, report) = run_task(&task_with(&weak, "judge-salt-17"), &json!([5]));
    assert_eq!(report["detail"]["kills"]["length_only.v1"], "3/3");
}

#[test]
fn a_tree_checker_that_sees_an_inexact_cochain_rejects_what_the_tree_fits() {
    let both = manifest(json!(["length_only.v1", "tree_integration.v1"]));
    let mut open = task_with(&both, "judge-salt-17");
    open["c"] = json!([1, 5, -3, 1]);
    let (passed, report) = run_task(&open, &phi());
    assert!(!passed);
    assert_eq!(
        outcomes(&report)[3..5],
        [
            ("length_only.v1:accepts_artifact_and_gauge", true),
            ("length_only.v1:kills_every_mutant", false),
        ]
    );
    let held = outcomes(&report);
    assert_eq!(
        held[5],
        ("tree_integration.v1:accepts_artifact_and_gauge", false)
    );
}

#[test]
fn the_checkers_are_judged_in_the_order_the_manifest_gives_them() {
    let flipped = manifest(json!(["tree_integration.v1", "residual.v1"]));
    let (passed, report) = run_task(&task_with(&flipped, "judge-salt-17"), &phi());
    assert!(passed);
    let held = outcomes(&report);
    assert_eq!(held[3].0, "tree_integration.v1:accepts_artifact_and_gauge");
    assert_eq!(held[5].0, "residual.v1:accepts_artifact_and_gauge");
}

#[test]
fn a_manifest_that_was_swapped_after_it_was_committed_is_refused_before_anything_is_asked() {
    let mut swapped = task();
    swapped["judge_manifest"] = manifest(json!(["residual.v1", "length_only.v1"]));
    let Outcome::Fail { result } = judge(&request(&swapped, &sealed(), &[])) else {
        panic!("expected a refused run");
    };
    assert_eq!(result["verdict"], "REFUSED");
    assert_eq!(result["code"], "MANIFEST_COMMITMENT_MATCHES");
    assert_eq!(
        result["detail"],
        json!({"failed": ["manifest_commitment_matches"]})
    );
    assert_eq!(result["asked"], json!([]));
    assert_eq!(
        outcomes(&result),
        [
            ("manifest_commitment_matches", false),
            ("two_independent_registered_checkers", true),
        ]
    );
}

#[test]
fn a_manifest_committed_under_another_salt_does_not_match() {
    let (_, report) = run_with(&task(), &json!({"manifest_salt": "judge-salt-18"}), vec![]);
    assert_eq!(report["code"], "MANIFEST_COMMITMENT_MATCHES");
    let (_, report) = run_with(&task(), &json!({}), vec![]);
    assert_eq!(report["code"], "MANIFEST_COMMITMENT_MATCHES");
    let (_, report) = run_with(&task(), &Value::Null, vec![]);
    assert_eq!(report["code"], "MANIFEST_COMMITMENT_MATCHES");
}

#[test]
fn a_manifest_committed_without_a_salt_matches_a_run_with_none() {
    let unsalted = task_with(&standard(), "");
    let (passed, report) = run_with(
        &unsalted,
        &json!({}),
        vec![committed(&phi()), revealed(&phi())],
    );
    assert!(passed, "{report}");
    let (passed, _) = run_with(
        &unsalted,
        &Value::Null,
        vec![committed(&phi()), revealed(&phi())],
    );
    assert!(passed);
}

#[test]
fn the_whole_manifest_is_committed_not_only_its_checkers() {
    let mut extended = standard();
    extended["note"] = json!("pinned");
    let committed_task = task_with(&extended, "judge-salt-17");
    let (passed, _) = run_task(&committed_task, &phi());
    assert!(passed);
    let mut dropped = committed_task;
    dropped["judge_manifest"] = standard();
    let (_, report) = run_with(&dropped, &sealed(), vec![]);
    assert_eq!(report["code"], "MANIFEST_COMMITMENT_MATCHES");
}

#[test]
fn a_manifest_needs_two_different_registered_checkers() {
    let cases = [
        json!(["residual.v1", "residual.v1"]),
        json!(["residual.v1"]),
        json!([]),
        json!(["residual.v1", "tree_integration.v1", "length_only.v1"]),
        json!(["tree_integration.v1", "magic.v1", "residual.v1"]),
        json!(["residual.v1", "magic.v1"]),
        json!(["Residual.v1", "tree_integration.v1"]),
        json!(["residual.v1", 7]),
        json!([null, null]),
    ];
    for checkers in cases {
        let listed = manifest(checkers.clone());
        let (passed, report) = run_with(&task_with(&listed, "judge-salt-17"), &sealed(), vec![]);
        assert!(!passed, "{checkers}");
        assert_eq!(
            report["code"], "TWO_INDEPENDENT_REGISTERED_CHECKERS",
            "{checkers}"
        );
        assert_eq!(
            outcomes(&report),
            [
                ("manifest_commitment_matches", true),
                ("two_independent_registered_checkers", false),
            ],
            "{checkers}"
        );
        assert_eq!(report["asked"], json!([]), "{checkers}");
    }
}

#[test]
fn both_manifest_failures_are_listed_and_the_first_names_the_refusal() {
    let mut bad = task_with(
        &manifest(json!(["residual.v1", "residual.v1"])),
        "judge-salt-17",
    );
    bad["manifest_commitment"] = json!("0000");
    let (_, report) = run_with(&bad, &sealed(), vec![]);
    assert_eq!(report["code"], "MANIFEST_COMMITMENT_MATCHES");
    assert_eq!(
        report["detail"],
        json!({"failed": ["manifest_commitment_matches", "two_independent_registered_checkers"]})
    );
}

#[test]
fn the_three_registered_checkers_are_the_pairs_a_manifest_may_name() {
    let pairs = [
        ["residual.v1", "length_only.v1"],
        ["length_only.v1", "tree_integration.v1"],
        ["tree_integration.v1", "residual.v1"],
    ];
    for pair in pairs {
        let listed = manifest(json!(pair));
        let (_, report) = run_with(
            &task_with(&listed, "judge-salt-17"),
            &sealed(),
            vec![committed(&phi()), revealed(&phi())],
        );
        assert_ne!(
            report["code"], "TWO_INDEPENDENT_REGISTERED_CHECKERS",
            "{pair:?}"
        );
        assert_eq!(
            report["asked"].as_array().expect("asked").len(),
            2,
            "{pair:?}"
        );
    }
}

#[test]
fn the_commit_reply_must_be_an_object_with_a_commitment_that_is_text() {
    assert_eq!(
        malformed(vec![json!("abc")]),
        "commit reply must be an object"
    );
    assert_eq!(
        malformed(vec![json!(["abc"])]),
        "commit reply must be an object"
    );
    for bad in [
        json!({}),
        json!({"commitment": 5}),
        json!({"commitment": null}),
        json!({"commitment": ["a"]}),
    ] {
        assert_eq!(
            malformed(vec![bad.clone()]),
            "commitment must be a hex string",
            "{bad}"
        );
    }
}

#[test]
fn the_reveal_must_be_an_object_with_an_artifact_of_integers_and_a_salt() {
    let given = committed(&phi());
    assert_eq!(
        malformed(vec![given.clone(), json!("s4lt")]),
        "reveal reply must be an object"
    );
    let cases = [
        json!({"salt": "s4lt"}),
        json!({"salt": "s4lt", "artifact": "0134"}),
        json!({"salt": "s4lt", "artifact": [0, 1, 3, 4.0]}),
        json!({"salt": "s4lt", "artifact": [0, 1, "3", 4]}),
        json!({"salt": "s4lt", "artifact": [0, 1, true, 4]}),
        json!({"salt": "s4lt", "artifact": null}),
        json!({"salt": "s4lt", "artifact": {"0": 0}}),
    ];
    for bad in cases {
        assert_eq!(
            malformed(vec![given.clone(), bad.clone()]),
            "artifact must be a list of exact integers",
            "{bad}"
        );
    }
    for bad in [
        json!({"artifact": [0]}),
        json!({"salt": 4, "artifact": [0]}),
        json!({"salt": null, "artifact": [0]}),
    ] {
        assert_eq!(
            malformed(vec![given.clone(), bad.clone()]),
            "salt must be a string",
            "{bad}"
        );
    }
    assert_eq!(
        malformed(vec![given, json!({"salt": 4})]),
        "artifact must be a list of exact integers"
    );
}

#[test]
fn a_run_that_loses_a_reply_says_which_step() {
    let cases = [
        (vec![None], "commit"),
        (vec![Some(committed(&phi())), None], "reveal"),
    ];
    for (replies, stage) in cases {
        let Outcome::Fail { result } = judge(&request(&task(), &sealed(), &replies)) else {
            panic!("expected a refused run");
        };
        assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
        assert_eq!(result["detail"], json!({"stage": stage}));
    }
}

#[test]
fn a_task_must_commit_a_manifest_and_state_a_cochain() {
    let edit = |key: &str, value: Value| {
        let mut changed = task();
        changed[key] = value;
        changed
    };
    let remove = |key: &str| {
        let mut changed = task();
        changed.as_object_mut().expect("object").remove(key);
        changed
    };
    let cases = [
        (
            remove("judge_manifest"),
            "judge_manifest must name its checkers",
        ),
        (
            edit(
                "judge_manifest",
                json!(["residual.v1", "tree_integration.v1"]),
            ),
            "judge_manifest must name its checkers",
        ),
        (
            edit("judge_manifest", json!({"checkers": "residual.v1"})),
            "judge_manifest must name its checkers",
        ),
        (
            edit("judge_manifest", json!({})),
            "judge_manifest must name its checkers",
        ),
        (
            remove("manifest_commitment"),
            "manifest_commitment must be text",
        ),
        (
            edit("manifest_commitment", json!(7)),
            "manifest_commitment must be text",
        ),
        (
            edit("c", json!([1, 2, -3])),
            "c must be one exact integer per edge",
        ),
        (
            edit("c", json!([1, 2, -3, 1.5])),
            "c must be one exact integer per edge",
        ),
        (remove("c"), "c must be one exact integer per edge"),
        (
            edit("edges", json!([])),
            "edges must be a nonempty list of pairs of exact integers",
        ),
        (
            edit("edges", json!([[0, 1], [1, 2], [2, 0], [2, 5]])),
            "vertices must be 0..n-1",
        ),
    ];
    for (bad, reason) in cases {
        assert_eq!(bad_task(&bad, &sealed()), reason, "{bad}");
    }
    assert_eq!(
        bad_task(&task(), &json!({"manifest_salt": 17})),
        "manifest_salt must be text"
    );
}

#[test]
fn a_second_reply_after_the_reveal_is_not_accepted() {
    let replies: Vec<Option<Value>> = vec![
        Some(committed(&phi())),
        Some(revealed(&phi())),
        Some(revealed(&phi())),
    ];
    match judge(&request(&task(), &sealed(), &replies)) {
        Outcome::Refused { refusal } => assert_eq!(refusal.code, "BAD_REQUEST"),
        other => panic!("expected a refusal, got {other:?}"),
    }
}

#[test]
fn the_sealed_salt_is_never_put_in_a_prompt() {
    let replies: Vec<Option<Value>> = vec![
        Some(json!({"commitment": "judge-salt-17"})),
        Some(revealed(&phi())),
    ];
    match judge(&request(&task(), &sealed(), &replies)) {
        Outcome::Refused { refusal } => assert_eq!(refusal.code, "SEALED_LEAK"),
        other => panic!("expected a refusal, got {other:?}"),
    }
}
