//! WF36, guarded staged slot materialisation: the guard, the rank test behind an abstention,
//! the retry with the syndrome, and the potential of the second stage.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf36-tests:v1

use pfp_operads::families::wf36::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

/// Edges 0->1, 1->2, 2->0, 2->3, 3->0. Spanning from 0 leaves edges 1 and 3 as chords, so the
/// cycles are `e1 + e2 + e0` and `e3 + e4 - e2`.
fn task() -> Value {
    json!({
        "statement": "Fill the null edge slots so every cycle sums to zero, then give a potential.",
        "edges": [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]],
        "values": [1, 2, null, 1, null],
    })
}

fn good() -> Value {
    json!({"slots": {"2": -3, "4": -4}})
}

/// A fill whose second cycle sums to 1.
fn near() -> Value {
    json!({"slots": {"2": -3, "4": -3}})
}

fn phi() -> Value {
    json!({"potential": [0, 1, 3, 4]})
}

fn request(task: &Value, replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF36", "task": task, "replies": replies}).to_string()
}

fn all(replies: Vec<Value>) -> Vec<Option<Value>> {
    replies.into_iter().map(Some).collect()
}

fn run_task(task: &Value, replies: Vec<Option<Value>>) -> (bool, Value) {
    match judge(&request(task, &replies)) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn run(replies: Vec<Value>) -> (bool, Value) {
    run_task(&task(), all(replies))
}

fn turn(task: &Value, replies: Vec<Option<Value>>) -> Value {
    match next(&request(task, &replies)) {
        Outcome::Pass { result } => result,
        other => panic!("expected a turn, got {other:?}"),
    }
}

fn bad_task(task: Value) -> String {
    match next(&request(&task, &[])) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
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
    let (passed, report) = run(replies);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    report["detail"]["reason"]
        .as_str()
        .expect("a reason")
        .to_owned()
}

#[test]
fn the_registry_names_the_family() {
    assert_eq!(FAMILY.workflow, "WF36");
    assert_eq!(FAMILY.name, "Guarded staged slot materialisation");
    assert_eq!(FAMILY.host_check, "exact_cochain_check");
}

#[test]
fn a_fill_with_a_zero_syndrome_and_its_potential_are_certified() {
    let (passed, report) = run(vec![good(), phi()]);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "MATERIALISED");
    assert_eq!(
        report["detail"],
        json!({"syndromes": [[0, 0]], "residual": [0, 0, 0, 0, 0]})
    );
    assert_eq!(
        outcomes(&report),
        [
            ("guard_complete", true),
            ("guard_green_within_one_retry", true),
            ("stage2_potential_explains_slots", true),
        ]
    );
    let digests: Vec<&str> = report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| row["evidence_sha256"].as_str().expect("a digest"))
        .collect();
    assert_eq!(digests, [sha("[0,1]"), sha("[[0,0]]"), sha("[0,0,0,0,0]")]);
    let stages: Vec<&str> = report["asked"]
        .as_array()
        .expect("asked")
        .iter()
        .map(|row| row["stage"].as_str().expect("a stage"))
        .collect();
    assert_eq!(stages, ["stage1:0", "stage2"]);
}

#[test]
fn a_second_fill_is_asked_with_the_syndrome_of_the_first() {
    let (passed, report) = run(vec![near(), good(), phi()]);
    assert!(passed);
    assert_eq!(report["code"], "MATERIALISED_AFTER_RETRY");
    assert_eq!(report["detail"]["syndromes"], json!([[0, 1], [0, 0]]));
    let second = turn(&task(), all(vec![near()]));
    assert_eq!(second["ask"]["stage"], "stage1:1");
    let prompt = second["ask"]["prompt"].as_str().expect("a prompt");
    assert!(prompt.ends_with("\nGuard syndrome: [0,1]"), "{prompt}");
    let first = turn(&task(), vec![]);
    let opening = first["ask"]["prompt"].as_str().expect("a prompt");
    assert!(opening.starts_with("WF36 Guarded staged slot materialisation. Fill the null"));
    assert!(
        prompt.starts_with(opening),
        "the retry repeats the first prompt"
    );
}

#[test]
fn the_second_stage_is_asked_with_the_filled_values() {
    let asked = turn(&task(), all(vec![good()]));
    assert_eq!(asked["ask"]["stage"], "stage2");
    let prompt = asked["ask"]["prompt"].as_str().expect("a prompt");
    assert!(prompt.ends_with("\nSlots: [1,2,-3,1,-4]"), "{prompt}");
    let opening = turn(&task(), vec![]);
    let opening = opening["ask"]["prompt"].as_str().expect("a prompt");
    assert!(prompt.starts_with(opening), "{prompt}");
    let after_retry = turn(&task(), all(vec![near(), good()]));
    let after_retry = after_retry["ask"]["prompt"].as_str().expect("a prompt");
    assert!(
        after_retry.ends_with("\nSlots: [1,2,-3,1,-4]"),
        "{after_retry}"
    );
    assert!(after_retry.starts_with(opening), "{after_retry}");
    assert_eq!(turn(&task(), all(vec![good(), phi()]))["ask"], Value::Null);
}

#[test]
fn the_evidence_of_each_predicate_is_what_it_looked_at() {
    let mut listed = task();
    listed["guard_rows"] = json!([1, 0, 1]);
    let (_, report) = run_task(&listed, all(vec![good(), phi()]));
    let digests: Vec<&str> = report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| row["evidence_sha256"].as_str().expect("a digest"))
        .collect();
    assert_eq!(digests, [sha("[0,1]"), sha("[[0,0]]"), sha("[0,0,0,0,0]")]);
    let mut partial = task();
    partial["guard_rows"] = json!([1]);
    let (_, report) = run_task(&partial, vec![]);
    assert_eq!(report["predicates"][0]["evidence_sha256"], sha("[1]"));
}

#[test]
fn a_fill_that_stays_red_after_the_retry_is_refused_with_every_syndrome() {
    let (passed, report) = run(vec![near(), near()]);
    assert!(!passed);
    assert_eq!(report["code"], "GUARD_RED_AFTER_RETRY");
    assert_eq!(report["detail"], json!({"syndromes": [[0, 1], [0, 1]]}));
    assert_eq!(
        outcomes(&report),
        [
            ("guard_complete", true),
            ("guard_green_within_one_retry", false)
        ]
    );
    assert_eq!(report["asked"].as_array().expect("asked").len(), 2);
}

#[test]
fn a_third_reply_after_two_red_fills_is_not_accepted() {
    match judge(&request(&task(), &all(vec![near(), near(), phi()]))) {
        Outcome::Refused { refusal } => assert_eq!(refusal.code, "BAD_REQUEST"),
        other => panic!("expected a refusal, got {other:?}"),
    }
}

#[test]
fn a_potential_that_drifts_from_the_slots_leaves_a_residual() {
    let drift = json!({"potential": [0, 1, 3, 5]});
    let (passed, report) = run(vec![good(), drift]);
    assert!(!passed);
    assert_eq!(report["code"], "STAGE2_POTENTIAL_EXPLAINS_SLOTS");
    assert_eq!(report["detail"]["residual"], json!([0, 0, 0, -1, 1]));
    assert_eq!(report["detail"]["syndromes"], json!([[0, 0]]));
    assert_eq!(
        report["detail"]["failed"],
        json!(["stage2_potential_explains_slots"])
    );
}

#[test]
fn an_abstention_is_a_typed_refusal_when_no_fill_exists() {
    let mut blocked = task();
    blocked["values"] = json!([1, 2, 0, null, null]);
    let (passed, report) = run_task(&blocked, all(vec![json!({"abstain": true})]));
    assert!(passed);
    assert_eq!(report["verdict"], "TYPED_REFUSAL");
    assert_eq!(report["code"], "ABSTAIN_NOT_MATERIALISABLE");
    assert_eq!(
        report["detail"],
        json!({"rank_S_slots": 1, "rank_augmented": 2})
    );
    assert_eq!(
        outcomes(&report),
        [
            ("guard_complete", true),
            ("abstention_matches_rank_test", true)
        ]
    );
}

#[test]
fn an_abstention_when_a_fill_exists_is_refused() {
    let (passed, report) = run(vec![json!({"abstain": true})]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "FALSE_ABSTENTION");
    assert_eq!(
        report["detail"],
        json!({"rank_S_slots": 2, "rank_augmented": 2})
    );
    assert_eq!(
        outcomes(&report),
        [
            ("guard_complete", true),
            ("abstention_matches_rank_test", false)
        ]
    );
}

#[test]
fn the_second_reply_may_abstain_too() {
    let (_, report) = run(vec![near(), json!({"abstain": true})]);
    assert_eq!(report["code"], "FALSE_ABSTENTION");
    let mut blocked = task();
    blocked["values"] = json!([1, 2, 0, null, null]);
    let (passed, report) = run_task(
        &blocked,
        all(vec![
            json!({"slots": {"3": 0, "4": 0}}),
            json!({"abstain": true}),
        ]),
    );
    assert!(passed);
    assert_eq!(report["code"], "ABSTAIN_NOT_MATERIALISABLE");
}

#[test]
fn only_true_abstains() {
    for value in [json!("true"), json!(1), json!(false), Value::Null] {
        let reply = json!({"abstain": value});
        assert_eq!(
            malformed(vec![reply.clone()]),
            "one slot per null edge",
            "{reply}"
        );
    }
}

#[test]
fn a_guard_that_leaves_a_cycle_out_is_refused_with_a_witness_it_misses() {
    let mut partial = task();
    partial["guard_rows"] = json!([0]);
    let (passed, report) = run_task(&partial, vec![]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "PARTIAL_GUARD");
    assert_eq!(
        report["detail"],
        json!({
            "kernel_witness": [0, 0, 0, 1, 0],
            "guard_syndrome": [0],
            "full_syndrome": [0, 1],
        })
    );
    assert_eq!(outcomes(&report), [("guard_complete", false)]);
}

#[test]
fn a_guard_that_lists_a_row_twice_misses_the_other_row() {
    let mut partial = task();
    partial["guard_rows"] = json!([0, 0]);
    let (_, report) = run_task(&partial, vec![]);
    assert_eq!(report["code"], "PARTIAL_GUARD");
    assert_eq!(report["detail"]["guard_syndrome"], json!([0, 0]));
    let mut other = task();
    other["guard_rows"] = json!([1]);
    let (_, report) = run_task(&other, vec![]);
    assert_eq!(
        report["detail"],
        json!({
            "kernel_witness": [0, 1, 0, 0, 0],
            "guard_syndrome": [0],
            "full_syndrome": [1, 0],
        })
    );
}

#[test]
fn a_guard_that_leaves_every_row_out_is_refused_with_the_witness_of_the_first() {
    let mut empty = task();
    empty["guard_rows"] = json!([]);
    let (_, report) = run_task(&empty, vec![]);
    assert_eq!(report["code"], "PARTIAL_GUARD");
    assert_eq!(
        report["detail"],
        json!({
            "kernel_witness": [0, 1, 0, 0, 0],
            "guard_syndrome": [],
            "full_syndrome": [1, 0],
        })
    );
}

#[test]
fn a_guard_in_any_order_with_repeats_is_complete() {
    for rows in [json!([1, 0]), json!([0, 1, 1, 0]), json!([0, 1])] {
        let mut ordered = task();
        ordered["guard_rows"] = rows.clone();
        let (passed, report) = run_task(&ordered, all(vec![good(), phi()]));
        assert!(passed, "{rows}");
        assert_eq!(report["code"], "MATERIALISED");
        let digest = report["predicates"][0]["evidence_sha256"]
            .as_str()
            .expect("digest");
        assert_eq!(digest, sha("[0,1]"));
    }
}

#[test]
fn another_graph_is_read_with_its_own_cycles() {
    let triangle = json!({
        "statement": "s",
        "edges": [[0, 1], [1, 2], [2, 0], [0, 2]],
        "values": [1, 1, null, null],
    });
    assert_eq!(turn(&triangle, vec![])["ask"]["stage"], "stage1:0");
    let fill = json!({"slots": {"2": -2, "3": 2}});
    let (passed, report) = run_task(&triangle, all(vec![fill, json!({"potential": [0, 1, 2]})]));
    assert!(passed, "{report}");
    assert_eq!(report["detail"]["syndromes"], json!([[0, 0]]));
}

#[test]
fn a_graph_without_cycles_has_an_empty_syndrome() {
    let path = json!({
        "statement": "Fill the slot.",
        "edges": [[0, 1], [1, 2]],
        "values": [1, null],
    });
    let (passed, report) = run_task(
        &path,
        all(vec![
            json!({"slots": {"1": 5}}),
            json!({"potential": [0, 1, 6]}),
        ]),
    );
    assert!(passed);
    assert_eq!(report["code"], "MATERIALISED");
    assert_eq!(
        report["detail"],
        json!({"syndromes": [[]], "residual": [0, 0]})
    );
}

#[test]
fn a_task_with_no_slots_is_filled_by_an_empty_object_and_cannot_abstain_truthfully() {
    let mut closed = task();
    closed["values"] = json!([1, 2, -3, 1, -4]);
    let (passed, report) = run_task(&closed, all(vec![json!({"slots": {}}), phi()]));
    assert!(passed);
    assert_eq!(report["code"], "MATERIALISED");
    let (_, report) = run_task(&closed, all(vec![json!({"abstain": true})]));
    assert_eq!(report["code"], "FALSE_ABSTENTION");
    assert_eq!(
        report["detail"],
        json!({"rank_S_slots": 0, "rank_augmented": 0})
    );
    let mut broken = task();
    broken["values"] = json!([1, 2, 0, 1, -4]);
    let (passed, report) = run_task(&broken, all(vec![json!({"abstain": true})]));
    assert!(passed);
    assert_eq!(
        report["detail"],
        json!({"rank_S_slots": 0, "rank_augmented": 1})
    );
}

#[test]
fn a_missing_reply_stops_the_run_naming_the_stage() {
    let cases = [
        (vec![None], "stage1:0"),
        (vec![Some(near()), None], "stage1:1"),
        (vec![Some(good()), None], "stage2"),
        (vec![Some(near()), Some(good()), None], "stage2"),
    ];
    for (replies, stage) in cases {
        let (passed, report) = run_task(&task(), replies);
        assert!(!passed, "{stage}");
        assert_eq!(report["code"], "NO_ADMISSIBLE_REPLY");
        assert_eq!(report["detail"], json!({"stage": stage}));
    }
}

#[test]
fn a_fill_must_name_every_slot_and_no_other_edge() {
    let cases = [
        json!({"slots": {"2": -3}}),
        json!({"slots": {"2": -3, "4": -4, "1": 2}}),
        json!({"slots": {"2": -3, "3": -4}}),
        json!({"slots": {"2": -3, "04": -4}}),
        json!({"slots": [-3, -4]}),
        json!({"slots": "none"}),
        json!({}),
    ];
    for reply in cases {
        assert_eq!(
            malformed(vec![reply.clone()]),
            "one slot per null edge",
            "{reply}"
        );
    }
    assert_eq!(
        malformed(vec![json!([1, 2])]),
        "stage1:0 reply must be an object"
    );
    assert_eq!(
        malformed(vec![near(), json!("again")]),
        "stage1:1 reply must be an object"
    );
}

#[test]
fn every_slot_must_be_an_exact_integer() {
    for slot in [
        json!(-3.5),
        json!("-3"),
        json!(null),
        json!(true),
        json!([-3]),
    ] {
        let reply = json!({"slots": {"2": slot, "4": -4}});
        assert_eq!(
            malformed(vec![reply.clone()]),
            "slot must be an exact int",
            "{reply}"
        );
    }
}

#[test]
fn a_potential_is_one_exact_integer_per_vertex() {
    let cases = [
        (json!({}), "potential needs one integer per vertex 0..n-1"),
        (
            json!({"potential": [0, 1, 3]}),
            "potential needs one integer per vertex 0..n-1",
        ),
        (
            json!({"potential": [0, 1, 3, 4, 5]}),
            "potential needs one integer per vertex 0..n-1",
        ),
        (
            json!({"potential": [0, 1, "3", 4]}),
            "potential needs one integer per vertex 0..n-1",
        ),
        (
            json!({"potential": [0, 1, 3, 4.0]}),
            "potential needs one integer per vertex 0..n-1",
        ),
        (
            json!({"potential": "0134"}),
            "potential needs one integer per vertex 0..n-1",
        ),
        (
            json!({"potential": {"0": 0}}),
            "potential needs one integer per vertex 0..n-1",
        ),
        (json!([0, 1, 3, 4]), "stage2 reply must be an object"),
    ];
    for (reply, reason) in cases {
        assert_eq!(malformed(vec![good(), reply.clone()]), reason, "{reply}");
    }
}

#[test]
fn a_task_must_be_readable_before_anything_is_asked() {
    let edit = |key: &str, value: Value| {
        let mut changed = task();
        changed[key] = value;
        changed
    };
    let cases = [
        (
            edit("values", json!([1, 2, null, 1])),
            "values must be one exact integer or null per edge",
        ),
        (
            edit("values", json!([1, 2, null, 1, null, 9])),
            "values must be one exact integer or null per edge",
        ),
        (
            edit("values", json!([1, 2, "x", 1, null])),
            "values must be one exact integer or null per edge",
        ),
        (
            edit("values", json!([1, 2, 0.5, 1, null])),
            "values must be one exact integer or null per edge",
        ),
        (
            edit("values", json!("1 2")),
            "values must be one exact integer or null per edge",
        ),
        (
            edit("guard_rows", json!([2])),
            "guard_rows must be rows of the cycle matrix",
        ),
        (
            edit("guard_rows", json!([-1])),
            "guard_rows must be rows of the cycle matrix",
        ),
        (
            edit("guard_rows", json!("0")),
            "guard_rows must be rows of the cycle matrix",
        ),
        (
            edit("guard_rows", json!([0, 1.0])),
            "guard_rows must be rows of the cycle matrix",
        ),
        (
            edit("edges", json!([])),
            "edges must be a nonempty list of pairs of exact integers",
        ),
        (
            edit("edges", json!([[0, 1], [1, 2], [2, 0], [2, 4], [4, 0]])),
            "vertices must be 0..n-1",
        ),
        (
            edit(
                "edges",
                json!([["a", "b"], ["b", "c"], ["c", "a"], ["c", "d"], ["d", "a"]]),
            ),
            "edges must be a nonempty list of pairs of exact integers",
        ),
    ];
    for (bad, reason) in cases {
        assert_eq!(bad_task(bad.clone()), reason, "{bad}");
    }
}

#[test]
fn a_task_with_no_values_key_is_refused() {
    let mut bad = task();
    bad.as_object_mut().expect("object").remove("values");
    assert_eq!(
        bad_task(bad),
        "values must be one exact integer or null per edge"
    );
}

#[test]
fn values_and_slots_may_be_integers_of_any_size() {
    let mut huge = task();
    huge["values"] = json!([1, 2, null, 1, null]);
    let fill = json!({"slots": {"2": 7_777_777, "4": -4}});
    let text = request(&huge, &all(vec![fill.clone(), fill]))
        .replace("7777777", "123456789012345678901234567890");
    let Outcome::Fail { result: report } = judge(&text) else {
        panic!("expected a refused run");
    };
    assert_eq!(report["code"], "GUARD_RED_AFTER_RETRY");
    assert_eq!(
        report["detail"]["syndromes"][0][0],
        json!("123456789012345678901234567893")
    );
}
