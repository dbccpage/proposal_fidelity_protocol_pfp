//! WF40, restart boundary: the repair loop on potentials, the receipts of its failed attempts,
//! and the one boundary action each kind of measured value admits.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf40-tests:v1

use pfp_operads::families::wf40::{ACTIONS, FAMILY};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const STATEMENT: &str = "Find potentials matching the edge values, or take the boundary action.";

/// A square 0-1-2-3 with the diagonal 0-2 as its last edge, and the triangle 0-1-2 as a face.
const EDGES: &str = "[[0,1],[1,2],[2,3],[3,0],[0,2]]";
const FACES: &str = "[[[0,1],[1,1],[4,-1]]]";

/// The coboundary of the potentials 0, 2, 5, 3.
const EXACT: &str = "[2,3,-2,-3,5]";
/// Zero round the face, and one off round the other triangle.
const WINDING: &str = "[2,3,-2,-2,5]";
/// Minus one round the face.
const UNCLOSED: &str = "[2,3,-2,-3,6]";

fn parsed(text: &str) -> Value {
    serde_json::from_str(text).expect("JSON")
}

fn task(values: &str, limit: usize) -> Value {
    json!({"statement": STATEMENT, "edges": parsed(EDGES), "faces": parsed(FACES),
           "c": parsed(values), "max_attempts": limit})
}

fn spec(values: &str) -> String {
    format!(r#"{{"c":{values},"edges":{EDGES},"faces":{FACES}}}"#)
}

fn prompt(values: &str, limit: usize) -> String {
    format!(
        concat!(
            "WF40 Restart boundary after exhausted repair. {}\n",
            r#"{{"c":{},"edges":{},"faces":{},"max_attempts":{}}}"#
        ),
        STATEMENT, values, EDGES, FACES, limit
    )
}

/// The residual of potentials that are all zero: every edge is off by its own value.
fn all_off(misfit: usize) -> String {
    format!(r#"{{"defect_l1":"{misfit}","off_edges":[0,1,2,3,4]}}"#)
}

/// The receipt of one failed attempt: the digest of the spec, the attempt and its residual.
fn receipt(values: &str, attempt: usize, residual: &str) -> String {
    sha(&format!(
        r#"{{"attempt":{attempt},"residual":{residual},"spec":"{}"}}"#,
        sha(&spec(values))
    ))
}

/// The receipts of two attempts with zero potentials.
fn receipts(values: &str, misfit: usize) -> Vec<String> {
    vec![
        receipt(values, 0, &all_off(misfit)),
        receipt(values, 1, &all_off(misfit)),
    ]
}

fn zeros() -> Value {
    json!({"phi": [0, 0, 0, 0]})
}

fn solved() -> Value {
    json!({"phi": [0, 2, 5, 3]})
}

/// Two failed attempts, then this boundary reply.
fn after_two(boundary: Value) -> Vec<Value> {
    vec![zeros(), zeros(), boundary]
}

fn seed(values: &str, kept: &[String]) -> Value {
    json!({"spec": parsed(&spec(values)), "receipts": kept})
}

fn restart(seed: Value) -> Value {
    json!({"restart": {"seed": seed}})
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
    json!({"workflow": "WF40", "task": task, "replies": replies}).to_string()
}

fn all(replies: Vec<Value>) -> Vec<Option<Value>> {
    replies.into_iter().map(Some).collect()
}

/// The report of a finished run, and whether the host passed it.
fn run(task: &Value, replies: Vec<Value>) -> (bool, Value) {
    match judge(&request(task, &all(replies))) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

/// The next question of a run that is not finished.
fn ask(task: &Value, replies: Vec<Value>) -> Value {
    match next(&request(task, &all(replies))) {
        Outcome::Pass { result } => result["ask"].clone(),
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

/// The reason of a run refused because a reply could not be read.
fn malformed(task: &Value, replies: Vec<Value>) -> String {
    let (passed, report) = run(task, replies);
    assert!(!passed);
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    report["detail"]["reason"]
        .as_str()
        .expect("a reason")
        .to_owned()
}

fn row(name: &str, passed: bool, evidence: &str) -> Value {
    json!({"name": name, "passed": passed, "evidence_sha256": sha(evidence)})
}

fn names(report: &Value) -> Vec<(&str, bool)> {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .filter_map(|row| Some((row["name"].as_str()?, row["passed"].as_bool()?)))
        .collect()
}

fn list(texts: &[String]) -> String {
    format!(r#"["{}"]"#, texts.join(r#"",""#))
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF40",
            "Restart boundary after exhausted repair",
            "cochain_trichotomy_boundary"
        )
    );
    assert_eq!(ACTIONS, ["refusal", "lift", "restart"]);
}

#[test]
fn the_first_question_is_the_task_as_written() {
    let first = ask(&task(EXACT, 2), vec![]);
    assert_eq!(first["stage"], "attempt:0");
    assert_eq!(first["prompt"], prompt(EXACT, 2));
    assert_eq!(first["prompt_sha256"], sha(&prompt(EXACT, 2)));
}

#[test]
fn potentials_whose_coboundary_is_the_measured_values_are_a_repair() {
    let (passed, report) = run(&task(EXACT, 2), vec![solved()]);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "REPAIRED");
    assert_eq!(report["detail"], json!({"attempts": 1}));
    assert_eq!(
        report["predicates"],
        json!([row("repaired_within_limit", true, r#""certificate""#)])
    );
    // Potentials are fixed up to a constant, and may be written as fractions.
    let shifted = json!({"phi": ["1/2", "5/2", "11/2", "7/2"]});
    let (later, second) = run(&task(EXACT, 2), vec![zeros(), shifted]);
    assert!(later);
    assert_eq!(second["detail"], json!({"attempts": 2}));
}

#[test]
fn potentials_are_listed_by_vertex_name_whatever_order_the_edges_name_them_in() {
    // phi(0) = 1, phi(1) = 3, phi(2) = 6 on edges that name the vertex 2 first.
    let named = json!({"edges": [[2, 1], [1, 0], [0, 2]], "faces": [], "c": [-3, -2, 5]});
    let (passed, _) = run(&named, vec![json!({"phi": [1, 3, 6]})]);
    assert!(passed);
    let second = ask(&named, vec![json!({"phi": [6, 3, 1]})]);
    let text = second["prompt"].as_str().expect("text");
    assert!(
        text.ends_with(r#"Host residual: {"defect_l1":"20","off_edges":[0,1,2]}"#),
        "{text}"
    );
}

#[test]
fn a_rejected_attempt_is_told_the_size_of_the_misfit_and_the_edges_that_are_off() {
    let second = ask(&task(EXACT, 3), vec![zeros()]);
    assert_eq!(second["stage"], "attempt:1");
    assert_eq!(
        second["prompt"],
        format!("{}\nHost residual: {}", prompt(EXACT, 3), all_off(15))
    );
    // Right everywhere but at the vertex 3: only its two edges are off, by 3 each.
    let partly = ask(&task(EXACT, 3), vec![json!({"phi": [0, 2, 5, 0]})]);
    assert_eq!(
        partly["prompt"],
        format!(
            "{}\nHost residual: {}",
            prompt(EXACT, 3),
            r#"{"defect_l1":"6","off_edges":[2,3]}"#
        )
    );
    // A misfit that is not whole is written as a fraction.
    let half = ask(&task(EXACT, 3), vec![json!({"phi": [0, 2, 5, "7/2"]})]);
    assert_eq!(
        half["prompt"],
        format!(
            "{}\nHost residual: {}",
            prompt(EXACT, 3),
            r#"{"defect_l1":"1","off_edges":[2,3]}"#
        )
    );
    let third = ask(&task(EXACT, 3), vec![json!({"phi": [0, 2, 5, "10/3"]})]);
    assert!(third["prompt"]
        .as_str()
        .expect("text")
        .ends_with(r#"{"defect_l1":"2/3","off_edges":[2,3]}"#));
}

#[test]
fn an_attempt_that_does_not_improve_is_granted_the_cycles_of_the_graph() {
    let third = ask(&task(EXACT, 3), vec![zeros(), zeros()]);
    assert_eq!(third["stage"], "attempt:2");
    assert_eq!(
        third["prompt"],
        format!(
            "{}\nHost residual: {}\nLIFT_REQUEST grant: {}",
            prompt(EXACT, 3),
            all_off(15),
            r#"{"fundamental_cycles":[[[1,1],[4,-1],[0,1]],[[2,1],[3,1],[4,1]]]}"#
        )
    );
    // 15, then 6: better, so no grant. Measures are compared as numbers: 2/3 is below 1.
    let better = ask(&task(EXACT, 3), vec![zeros(), json!({"phi": [0, 2, 5, 0]})]);
    assert!(!better["prompt"].as_str().expect("text").contains("grant"));
    let finer = ask(
        &task(EXACT, 3),
        vec![
            json!({"phi": [0, 2, 5, "7/2"]}),
            json!({"phi": [0, 2, 5, "10/3"]}),
        ],
    );
    assert!(!finer["prompt"].as_str().expect("text").contains("grant"));
}

#[test]
fn potentials_the_host_cannot_read_are_an_attempt_with_a_reason() {
    for (reply, reason) in [
        (json!({}), "phi list required"),
        (json!({"phi": "0, 2, 5, 3"}), "phi list required"),
        (json!({"phi": [0, 2, 5]}), "one potential per vertex"),
        (json!({"phi": [0, 2, 5, 3, 0]}), "one potential per vertex"),
        (
            json!({"phi": [0, 2, 5, 3.5]}),
            "phi must be an int or a p/q string",
        ),
    ] {
        let second = ask(&task(EXACT, 2), vec![reply]);
        assert_eq!(
            second["prompt"],
            format!(
                "{}\nHost residual: {{\"malformed\":\"{reason}\"}}",
                prompt(EXACT, 2)
            )
        );
    }
}

#[test]
fn a_repair_that_asks_for_a_grant_outside_the_structure_is_refused() {
    let greedy = json!({"phi": [0, 2, 5, 3], "lift_request": "c"});
    let (passed, report) = run(&task(EXACT, 2), vec![zeros(), greedy]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "REPAIRED_WITHIN_LIMIT");
    assert_eq!(
        report["detail"],
        json!({"attempts": 2, "failed": ["repaired_within_limit"]})
    );
    assert_eq!(
        report["predicates"],
        json!([row("repaired_within_limit", false, r#""scope""#)])
    );
}

#[test]
fn exhausted_repair_is_shown_its_receipts_and_asked_for_a_boundary_action() {
    let boundary = ask(&task(EXACT, 2), vec![zeros(), zeros()]);
    assert_eq!(boundary["stage"], "boundary");
    let expected = format!(
        "{}\nRefusal receipts: {}",
        prompt(EXACT, 2),
        list(&receipts(EXACT, 15))
    );
    assert_eq!(boundary["prompt"], expected);
    assert_eq!(boundary["prompt_sha256"], sha(&expected));
    // A receipt covers the attempt's own residual.
    let mixed = ask(
        &task(EXACT, 2),
        vec![json!({"phi": [0, 2, 5, 0]}), json!({})],
    );
    let shown = vec![
        receipt(EXACT, 0, r#"{"defect_l1":"6","off_edges":[2,3]}"#),
        receipt(EXACT, 1, r#"{"malformed":"phi list required"}"#),
    ];
    assert_eq!(
        mixed["prompt"],
        format!("{}\nRefusal receipts: {}", prompt(EXACT, 2), list(&shown))
    );
}

#[test]
fn a_missing_reply_ends_repair_and_the_boundary_is_asked_with_the_receipts_so_far() {
    let none = next(&request(&task(EXACT, 2), &[None]));
    let Outcome::Pass { result } = none else {
        panic!("expected a turn, got {none:?}");
    };
    assert_eq!(result["ask"]["stage"], "boundary");
    assert_eq!(
        result["ask"]["prompt"],
        format!("{}\nRefusal receipts: []", prompt(EXACT, 2))
    );
    let one = next(&request(&task(EXACT, 2), &[Some(zeros()), None]));
    let Outcome::Pass { result } = one else {
        panic!("expected a turn, got {one:?}");
    };
    assert_eq!(
        result["ask"]["prompt"],
        format!(
            "{}\nRefusal receipts: {}",
            prompt(EXACT, 2),
            list(&receipts(EXACT, 15)[..1])
        )
    );
    let silent = judge(&request(
        &task(EXACT, 2),
        &[Some(zeros()), Some(zeros()), None],
    ));
    let Outcome::Fail { result } = silent else {
        panic!("expected a failed run, got {silent:?}");
    };
    assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
}

#[test]
fn a_boundary_reply_takes_exactly_one_action() {
    let both = json!({"refusal": {"face": 0}, "restart": {}});
    for (reply, taken) in [
        (json!({}), json!([])),
        (json!({"retry": {}}), json!([])),
        (both, json!(["refusal", "restart"])),
        (
            json!({"lift": 1, "refusal": 2, "restart": 3}),
            json!(["refusal", "lift", "restart"]),
        ),
    ] {
        let (passed, report) = run(&task(EXACT, 2), after_two(reply));
        assert!(!passed);
        assert_eq!(report["verdict"], "REFUSED");
        assert_eq!(report["code"], "NOT_EXACTLY_ONE_ACTION");
        assert_eq!(report["detail"], json!({ "actions": taken }));
        assert_eq!(
            report["predicates"],
            json!([row("exactly_one_action", false, &taken.to_string())])
        );
    }
    assert_eq!(
        malformed(&task(EXACT, 2), after_two(json!("restart"))),
        "boundary reply must be an object"
    );
    for action in ACTIONS {
        assert_eq!(
            malformed(&task(EXACT, 2), after_two(json!({ action: [0] }))),
            format!("{action} must be an object")
        );
    }
}

#[test]
fn values_that_do_not_close_round_a_face_admit_a_refusal_naming_that_face() {
    let (passed, report) = run(
        &task(UNCLOSED, 2),
        after_two(json!({"refusal": {"face": 0}})),
    );
    assert!(passed);
    assert_eq!(report["verdict"], "TYPED_REFUSAL");
    assert_eq!(report["code"], "UNCLOSED_COCHAIN");
    assert_eq!(
        report["detail"],
        json!({"action": "refusal", "cochain_class": "unclosed", "delta": "2", "face": 0})
    );
    assert_eq!(
        report["predicates"],
        json!([
            row("exactly_one_action", true, r#"["refusal"]"#),
            row(
                "action_matches_trichotomy",
                true,
                r#"{"action":"refusal","cochain_class":"unclosed","delta":"2"}"#
            ),
            row("face_witness_nonzero", true, r#""-1/1""#),
        ])
    );
}

#[test]
fn a_refusal_must_name_a_face_the_values_do_not_close_round() {
    // The values sum to -1 round the first face and to 0 round the second. The forest potential
    // leaves the edge 1 off by one.
    let mut two = task("[2,3,-2,-4,6]", 2);
    two["faces"] = json!([[[0, 1], [1, 1], [4, -1]], [[2, 1], [3, 1], [4, 1]]]);
    let (passed, right) = run(&two, after_two(json!({"refusal": {"face": 0}})));
    assert!(passed);
    assert_eq!(right["detail"]["face"], 0);
    let (wrong, report) = run(&two, after_two(json!({"refusal": {"face": 1}})));
    assert!(!wrong);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "FACE_WITNESS_NONZERO");
    assert_eq!(
        report["detail"],
        json!({"action": "refusal", "cochain_class": "unclosed", "delta": "1"})
    );
    assert_eq!(
        names(&report),
        [
            ("exactly_one_action", true),
            ("action_matches_trichotomy", true),
            ("face_witness_nonzero", false)
        ]
    );
    assert_eq!(report["predicates"][2]["evidence_sha256"], sha(r#""0/1""#));
    for (body, reason) in [
        (json!({}), "face must be an exact int"),
        (json!({"face": "0"}), "face must be an exact int"),
        (json!({"face": 2}), "face index out of range"),
        (json!({"face": -1}), "face index out of range"),
    ] {
        assert_eq!(
            malformed(&two, after_two(json!({ "refusal": body }))),
            reason
        );
    }
}

#[test]
fn a_refusal_on_values_that_close_is_refused() {
    for (values, class, delta) in [(EXACT, "exact", "0"), (WINDING, "closed_non_exact", "1")] {
        let (passed, report) = run(&task(values, 2), after_two(json!({"refusal": {"face": 0}})));
        assert!(!passed);
        assert_eq!(report["verdict"], "REFUSED");
        assert_eq!(report["code"], "ACTION_MATCHES_TRICHOTOMY");
        assert_eq!(
            report["detail"],
            json!({"action": "refusal", "cochain_class": class, "delta": delta})
        );
        assert_eq!(
            names(&report),
            [
                ("exactly_one_action", true),
                ("action_matches_trichotomy", false),
                ("face_witness_nonzero", false)
            ]
        );
    }
}

#[test]
fn closed_values_that_are_no_coboundary_admit_a_lift() {
    let lift = json!({"lift": {"h": [0, 0, 0, 1, 0], "k": 1, "phi": [0, 2, 5, 3]}});
    let (passed, report) = run(&task(WINDING, 2), after_two(lift));
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "LIFT_AUTHORISED");
    assert_eq!(
        report["detail"],
        json!({"action": "lift", "cochain_class": "closed_non_exact", "delta": "1"})
    );
    assert_eq!(
        report["predicates"],
        json!([
            row("exactly_one_action", true, r#"["lift"]"#),
            row(
                "action_matches_trichotomy",
                true,
                r#"{"action":"lift","cochain_class":"closed_non_exact","delta":"1"}"#
            ),
            row("lift_authorised_by_positive_delta", true, r#""1/1""#),
            row(
                "preservation_witness_closed",
                true,
                r#"["0/1","0/1","0/1","1/1","0/1"]"#
            ),
            row(
                "lift_reproduces_claims",
                true,
                r#"["2/1","3/1","-2/1","-2/1","5/1"]"#
            ),
        ])
    );
    // The same lift with the witness halved and its weight doubled, on the other chord.
    let scaled = json!({"lift": {"h": [0, 0, "1/2", 0, 0], "k": 2, "phi": [0, 2, 5, 2]}});
    let (again, _) = run(&task(WINDING, 2), after_two(scaled));
    assert!(again);
}

#[test]
fn a_lift_needs_a_closed_witness_that_reproduces_the_values() {
    // The witness is not zero round the face.
    let open = json!({"lift": {"h": [1, 0, 0, 1, 0], "k": 1, "phi": [0, 1, 4, 3]}});
    let (passed, report) = run(&task(WINDING, 2), after_two(open));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "PRESERVATION_WITNESS_CLOSED");
    assert_eq!(
        report["detail"]["failed"],
        json!(["preservation_witness_closed", "lift_reproduces_claims"])
    );
    // A closed witness with the wrong weight: the fit is 2 on the edge 3 where -2 was measured.
    let heavy = json!({"lift": {"h": [0, 0, 0, 1, 0], "k": 5, "phi": [0, 2, 5, 3]}});
    let (_, wrong) = run(&task(WINDING, 2), after_two(heavy));
    assert_eq!(wrong["code"], "LIFT_REPRODUCES_CLAIMS");
    assert_eq!(
        wrong["detail"],
        json!({"action": "lift", "cochain_class": "closed_non_exact", "delta": "1",
               "failed": ["lift_reproduces_claims"]})
    );
    assert_eq!(
        wrong["predicates"][4],
        row(
            "lift_reproduces_claims",
            false,
            r#"["2/1","3/1","-2/1","2/1","5/1"]"#
        )
    );
}

#[test]
fn a_lift_on_exact_or_unclosed_values_is_refused() {
    let lift = json!({"lift": {"h": [0, 0, 0, 0, 0], "k": 1, "phi": [0, 2, 5, 3]}});
    let (passed, exact) = run(&task(EXACT, 2), after_two(lift));
    assert!(!passed);
    assert_eq!(exact["code"], "ACTION_MATCHES_TRICHOTOMY");
    assert_eq!(
        exact["detail"]["failed"],
        json!([
            "action_matches_trichotomy",
            "lift_authorised_by_positive_delta"
        ])
    );
    assert_eq!(
        exact["predicates"][2],
        row("lift_authorised_by_positive_delta", false, r#""0/1""#)
    );
    // The only witness that reproduces unclosed values is itself unclosed.
    let open = json!({"lift": {"h": [0, 0, 0, 0, 1], "k": 1, "phi": [0, 2, 5, 3]}});
    let (_, unclosed) = run(&task(UNCLOSED, 2), after_two(open));
    assert_eq!(unclosed["code"], "ACTION_MATCHES_TRICHOTOMY");
    assert_eq!(
        unclosed["detail"]["failed"],
        json!(["action_matches_trichotomy", "preservation_witness_closed"])
    );
}

#[test]
fn a_lift_the_host_cannot_read_is_malformed_by_its_reason() {
    for (body, reason) in [
        (json!({"k": 1, "phi": [0, 2, 5, 3]}), "h is an edge cochain"),
        (
            json!({"h": [0, 0, 0, 1], "k": 1, "phi": [0, 2, 5, 3]}),
            "h is an edge cochain",
        ),
        (
            json!({"h": [0, 0, 0, 1, 0, 0], "k": 1, "phi": [0, 2, 5, 3]}),
            "h is an edge cochain",
        ),
        (
            json!({"h": [0, 0, 0, 1.5, 0], "k": 1, "phi": [0, 2, 5, 3]}),
            "h must be an int or a p/q string",
        ),
        (json!({"h": [0, 0, 0, 1, 0], "k": 1}), "phi list required"),
        (
            json!({"h": [0, 0, 0, 1, 0], "k": 1, "phi": [0, 2, 5]}),
            "one potential per vertex",
        ),
        (
            json!({"h": [0, 0, 0, 1, 0], "k": 1, "phi": [0, 2, 5, "three"]}),
            "phi must be an int or a p/q string",
        ),
        (
            json!({"h": [0, 0, 0, 1, 0], "phi": [0, 2, 5, 3]}),
            "k must be an int or a p/q string",
        ),
        (
            json!({"h": [0, 0, 0, 1, 0], "k": [1], "phi": [0, 2, 5, 3]}),
            "k must be an int or a p/q string",
        ),
    ] {
        assert_eq!(
            malformed(&task(WINDING, 2), after_two(json!({ "lift": body }))),
            reason
        );
    }
}

#[test]
fn exact_values_admit_a_restart_seeded_with_the_spec_and_shown_receipts() {
    let shown = receipts(EXACT, 15);
    let mut replies = after_two(restart(seed(EXACT, &shown)));
    let again = ask(&task(EXACT, 2), replies.clone());
    assert_eq!(again["stage"], "restart:attempt:0");
    let expected = format!(
        concat!(
            "WF40 Restart boundary after exhausted repair. {}\n",
            r#"{{"c":{},"edges":{},"faces":{},"max_attempts":2,"refusal_receipts":{}}}"#
        ),
        STATEMENT,
        EXACT,
        EDGES,
        FACES,
        list(&shown)
    );
    assert_eq!(again["prompt"], expected);
    replies.push(solved());
    let (passed, report) = run(&task(EXACT, 2), replies);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "RESTART_REPAIRED");
    assert_eq!(
        report["detail"],
        json!({"action": "restart", "cochain_class": "exact", "delta": "0",
               "restart_attempts": 1})
    );
    assert_eq!(
        report["predicates"],
        json!([
            row("exactly_one_action", true, r#"["restart"]"#),
            row(
                "action_matches_trichotomy",
                true,
                r#"{"action":"restart","cochain_class":"exact","delta":"0"}"#
            ),
            row(
                "seed_only_spec_and_receipts",
                true,
                r#"["receipts","spec"]"#
            ),
            row(
                "seed_spec_immutable",
                true,
                &format!("\"{}\"", sha(&spec(EXACT)))
            ),
            row("receipts_verified", true, &list(&shown)),
            row("restart_certified", true, r#""certificate""#),
        ])
    );
}

#[test]
fn a_restart_keeps_only_the_receipts_it_names_and_runs_under_the_task_limit() {
    let shown = receipts(EXACT, 15);
    let mut unlimited = task(EXACT, 5);
    unlimited
        .as_object_mut()
        .expect("object")
        .remove("max_attempts");
    let mut replies = vec![zeros(); 5];
    let five: Vec<String> = (0..5).map(|at| receipt(EXACT, at, &all_off(15))).collect();
    replies.push(restart(seed(EXACT, &five[3..4])));
    let again = ask(&unlimited, replies.clone());
    assert_eq!(again["stage"], "restart:attempt:0");
    assert!(again["prompt"].as_str().expect("text").ends_with(&format!(
        r#"{{"c":{EXACT},"edges":{EDGES},"faces":{FACES},"refusal_receipts":["{}"]}}"#,
        five[3]
    )));
    // The restart has the task's own number of attempts, and its second prompt its residual.
    let mut limited = after_two(restart(seed(EXACT, &shown[..1])));
    limited.push(zeros());
    let second = ask(&task(EXACT, 2), limited.clone());
    assert_eq!(second["stage"], "restart:attempt:1");
    assert!(second["prompt"]
        .as_str()
        .expect("text")
        .ends_with(&format!("\nHost residual: {}", all_off(15))));
    limited.push(json!({"phi": ["1", "3", "6", "4"]}));
    let (passed, report) = run(&task(EXACT, 2), limited);
    assert!(passed);
    assert_eq!(report["detail"]["restart_attempts"], 2);
}

#[test]
fn a_restart_that_does_not_repair_is_refused() {
    let shown = receipts(EXACT, 15);
    let mut replies = after_two(restart(seed(EXACT, &shown)));
    replies.extend([zeros(), zeros()]);
    let (passed, report) = run(&task(EXACT, 2), replies);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "RESTART_CERTIFIED");
    assert_eq!(
        report["detail"],
        json!({"action": "restart", "cochain_class": "exact", "delta": "0",
               "failed": ["restart_certified"], "restart_attempts": 2})
    );
    assert_eq!(
        report["predicates"][5],
        row("restart_certified", false, r#""limit""#)
    );
}

#[test]
fn a_seed_that_carries_anything_else_is_refused() {
    let shown = receipts(EXACT, 15);
    let mut carrying = seed(EXACT, &shown);
    carrying["history"] = json!([zeros(), zeros()]);
    let (passed, report) = run(&task(EXACT, 2), after_two(restart(carrying)));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "SEED_ONLY_SPEC_AND_RECEIPTS");
    assert_eq!(
        report["detail"],
        json!({"action": "restart", "cochain_class": "exact", "delta": "0"})
    );
    assert_eq!(
        report["predicates"][2],
        row(
            "seed_only_spec_and_receipts",
            false,
            r#"["history","receipts","spec"]"#
        )
    );
    // A seed with a part missing fails the same check.
    let (_, bare) = run(
        &task(EXACT, 2),
        after_two(restart(json!({"spec": parsed(&spec(EXACT))}))),
    );
    assert_eq!(bare["code"], "SEED_ONLY_SPEC_AND_RECEIPTS");
    assert_eq!(
        names(&bare)[2..],
        [
            ("seed_only_spec_and_receipts", false),
            ("seed_spec_immutable", true),
            ("receipts_verified", false)
        ]
    );
}

#[test]
fn a_seed_with_other_measured_values_is_a_new_problem() {
    let shown = receipts(EXACT, 15);
    for values in [UNCLOSED, r#"["2",3,-2,-3,5]"#, "[2,3,-2,-3]"] {
        let (passed, report) = run(&task(EXACT, 2), after_two(restart(seed(values, &shown))));
        assert!(!passed);
        assert_eq!(report["verdict"], "REFUSED");
        assert_eq!(report["code"], "NEW_PROBLEM_NOT_REPAIR");
        assert_eq!(
            report["detail"],
            json!({"action": "restart", "cochain_class": "exact", "delta": "0"})
        );
        assert_eq!(
            names(&report),
            [
                ("exactly_one_action", true),
                ("action_matches_trichotomy", true),
                ("seed_only_spec_and_receipts", true),
                ("claim_set_unchanged", false)
            ]
        );
        assert_eq!(
            report["predicates"][3]["evidence_sha256"],
            sha(&spec(values))
        );
    }
}

#[test]
fn a_seed_with_another_graph_or_other_faces_is_refused() {
    let shown = receipts(EXACT, 15);
    let changed = |key: &str, value: Value| {
        let mut seed = seed(EXACT, &shown);
        seed["spec"][key] = value;
        seed
    };
    for seed in [
        changed("edges", json!([[0, 1], [1, 2], [2, 3], [3, 0], [2, 0]])),
        changed("faces", json!([])),
        json!({"spec": "the same", "receipts": shown}),
        json!({"receipts": shown, "spec": null}),
    ] {
        let (passed, report) = run(&task(EXACT, 2), after_two(restart(seed)));
        assert!(!passed);
        assert_eq!(report["code"], "SEED_SPEC_IMMUTABLE");
        assert_eq!(
            report["predicates"][3],
            row(
                "seed_spec_immutable",
                false,
                &format!("\"{}\"", sha(&spec(EXACT)))
            )
        );
    }
    // Both the graph and the values changed: not the same problem with new values, a new spec.
    let mut both = seed(UNCLOSED, &shown);
    both["spec"]["faces"] = json!([]);
    let (_, report) = run(&task(EXACT, 2), after_two(restart(both)));
    assert_eq!(report["code"], "SEED_SPEC_IMMUTABLE");
    // The same when the faces are kept and the edges and the values are not.
    let mut other = seed(UNCLOSED, &shown);
    other["spec"]["edges"] = json!([[0, 1], [1, 2], [2, 3], [3, 0], [2, 0]]);
    let (_, report) = run(&task(EXACT, 2), after_two(restart(other)));
    assert_eq!(report["code"], "SEED_SPEC_IMMUTABLE");
}

#[test]
fn a_seed_must_keep_at_least_one_receipt_and_only_receipts_that_were_shown() {
    let shown = receipts(EXACT, 15);
    let forged = receipt(EXACT, 2, &all_off(15));
    for kept in [
        json!([]),
        json!([forged]),
        json!([shown[0], forged]),
        json!(shown[0]),
        json!(null),
    ] {
        let seed = json!({"spec": parsed(&spec(EXACT)), "receipts": kept});
        let (passed, report) = run(&task(EXACT, 2), after_two(restart(seed)));
        assert!(!passed);
        assert_eq!(report["code"], "RECEIPTS_VERIFIED");
        assert_eq!(
            report["predicates"][4],
            row("receipts_verified", false, &list(&shown))
        );
        assert_eq!(report["asked"].as_array().map(Vec::len), Some(3));
    }
    for kept in [json!([shown[1]]), json!([shown[1], shown[0], shown[1]])] {
        let seed = json!({"spec": parsed(&spec(EXACT)), "receipts": kept});
        let turn = ask(&task(EXACT, 2), after_two(restart(seed)));
        assert_eq!(turn["stage"], "restart:attempt:0");
    }
}

#[test]
fn a_restart_on_values_that_are_no_coboundary_is_refused() {
    for (values, misfit) in [(WINDING, 14), (UNCLOSED, 16)] {
        let seed = seed(values, &receipts(values, misfit));
        let (passed, report) = run(&task(values, 2), after_two(restart(seed)));
        assert!(!passed);
        assert_eq!(report["code"], "ACTION_MATCHES_TRICHOTOMY");
        assert_eq!(
            names(&report),
            [
                ("exactly_one_action", true),
                ("action_matches_trichotomy", false),
                ("seed_only_spec_and_receipts", true),
                ("seed_spec_immutable", true),
                ("receipts_verified", true)
            ]
        );
    }
}

#[test]
fn a_restart_without_a_seed_is_malformed() {
    for body in [json!({}), json!({"seed": "spec"}), json!({"seed": [1]})] {
        assert_eq!(
            malformed(&task(EXACT, 2), after_two(json!({ "restart": body }))),
            "restart needs a seed"
        );
    }
}

#[test]
fn a_task_the_host_cannot_read_is_refused_before_anything_is_asked() {
    let with = |key: &str, value: Value| {
        let mut task = task(EXACT, 2);
        task[key] = value;
        task
    };
    for edges in [
        json!("square"),
        json!([[0, 1], [1]]),
        json!([[0, 1], [1, "2"]]),
    ] {
        assert_eq!(
            bad_task(with("edges", edges)),
            "edges must be a list of pairs of exact integers"
        );
    }
    let gap = json!({"edges": [[0, 1], [1, 3]], "c": [1, 1], "faces": []});
    assert_eq!(bad_task(gap), "vertices must be 0..n-1");
    for values in [
        json!([2, 3, -2, -3]),
        json!([2, 3, -2, -3, 5, 0]),
        json!([2, 3, -2, -3, 0.5]),
    ] {
        assert_eq!(
            bad_task(with("c", values)),
            "c must be one exact rational per edge"
        );
    }
    assert_eq!(bad_task(with("faces", json!({}))), "faces must be a list");
    for faces in [
        json!([7]),
        json!([[[0, 1], [1]]]),
        json!([[[0, 1], [5, 1]]]),
        json!([[[0, 1], [1, 2]]]),
        json!([[[0, 1], [1, 0]]]),
        json!([[[0, 1], ["1", 1]]]),
        json!([[[0, 1, 1], [1, 1], [2, 1], [3, 1]]]),
    ] {
        assert_eq!(
            bad_task(with("faces", faces)),
            "each face is a list of [edge, sign] with the edge in range and sign 1 or -1"
        );
    }
    for faces in [json!([[[0, 1], [1, 1]]]), json!([[[0, 1], [1, 1], [4, 1]]])] {
        assert_eq!(
            bad_task(with("faces", faces)),
            "every face must be a closed cycle"
        );
    }
    assert_eq!(bad_task(task(EXACT, 0)), "max_attempts must be in 1..5");
    assert_eq!(bad_task(task(EXACT, 6)), "max_attempts must be in 1..5");
    // Rational values and an empty face are a task like any other.
    let fine = with("c", json!(["4/2", 3, -2, -3, "5"]));
    assert!(matches!(next(&request(&fine, &[])), Outcome::Pass { .. }));
    assert!(matches!(
        next(&request(&with("faces", json!([[]])), &[])),
        Outcome::Pass { .. }
    ));
}
