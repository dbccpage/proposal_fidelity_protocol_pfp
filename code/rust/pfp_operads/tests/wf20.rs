//! WF20, derivation loop with lift grants: when a grant is given, what it holds, the request a
//! reply may not make, and how the loop ends.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf20-tests:v1

use pfp_operads::datum::Datum;
use pfp_operads::families::wf20::{grant, Halt, FAMILY, LIFTS, LOOP_LIMIT};
use pfp_operads::families::{judge, next};
use pfp_operads::graph::Graph;
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

/// Two triangles sharing the edge 2, with the first triangle odd. The chords of the spanning
/// forest are the edges 1 and 3.
fn task() -> Value {
    json!({"statement": "Flip the fewest edge labels so every cycle has an even label sum.",
           "edges": [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]], "labels": [1, 0, 0, 0, 0]})
}

const PROMPT: &str = concat!(
    "WF20 Derivation loop with lift grants. ",
    "Flip the fewest edge labels so every cycle has an even label sum.\n",
    r#"{"edges":[[0,1],[1,2],[2,0],[2,3],[3,0]],"labels":[1,0,0,0,0]}"#
);

/// What the host finds after one flip of the shared edge: the second cycle is odd.
const SECOND_ODD: &str = r#"{"flip_count":1,"minimal_known":false,"odd_cycles":[1]}"#;
/// What it finds after one flip of an edge only the second triangle has: both cycles are odd.
const BOTH_ODD: &str = r#"{"flip_count":1,"minimal_known":false,"odd_cycles":[0,1]}"#;

const CYCLES: &str =
    r#"LIFT_REQUEST grant: {"fundamental_cycles":[[[1,1],[2,1],[0,1]],[[3,1],[4,1],[2,-1]]]}"#;
const CHORDS: &str = r#"LIFT_REQUEST grant: {"chords":[1,3]}"#;

fn request(task: &Value, replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF20", "task": task, "replies": replies}).to_string()
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

fn flip(edges: &[usize]) -> Value {
    json!({ "flip": edges })
}

fn flips(edges: &[usize]) -> Vec<Value> {
    edges.iter().map(|&edge| flip(&[edge])).collect()
}

fn asking(edge: usize, lift: Value) -> Value {
    json!({"flip": [edge], "lift_request": lift})
}

fn limited(limit: Value) -> Value {
    let mut task = task();
    task["max_attempts"] = limit;
    task
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF20",
            "Derivation loop with lift grants",
            "structural_lift_grant_loop"
        )
    );
    assert_eq!(LOOP_LIMIT, 5);
    assert_eq!(LIFTS, ["fundamental_cycles", "chords"]);
}

#[test]
fn each_way_a_loop_can_end_has_its_own_name() {
    let names = [
        Halt::Certificate,
        Halt::Budget,
        Halt::Fuel,
        Halt::Limit,
        Halt::Scope,
    ]
    .map(Halt::name);
    assert_eq!(names, ["certificate", "budget", "fuel", "limit", "scope"]);
}

#[test]
fn a_grant_is_the_cycles_of_the_graph_or_its_chords() {
    let edges = Datum::parse("[[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]]").expect("JSON");
    let graph = Graph::read(&edges).expect("a graph");
    assert_eq!(
        grant(&graph, "fundamental_cycles").canonical(),
        r#"{"fundamental_cycles":[[[1,1],[2,1],[0,1]],[[3,1],[4,1],[2,-1]]]}"#
    );
    assert_eq!(grant(&graph, "chords").canonical(), r#"{"chords":[1,3]}"#);
    let tree = Graph::read(&Datum::parse("[[0, 1], [1, 2]]").expect("JSON")).expect("a graph");
    assert_eq!(
        grant(&tree, "fundamental_cycles").canonical(),
        r#"{"fundamental_cycles":[]}"#
    );
    assert_eq!(grant(&tree, "chords").canonical(), r#"{"chords":[]}"#);
}

#[test]
fn the_first_question_is_the_task_as_written() {
    let first = ask(&task(), vec![]);
    assert_eq!(first["stage"], "attempt:0");
    assert_eq!(first["prompt"], PROMPT);
    assert_eq!(first["prompt_sha256"], sha(PROMPT));
}

#[test]
fn an_accepted_first_attempt_is_derived_with_no_grant() {
    let (passed, report) = run(&task(), flips(&[0]));
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "DERIVED");
    assert_eq!(report["detail"], json!({"attempts": 1, "grants": []}));
    assert_eq!(
        report["predicates"],
        json!([{"name": "certificate_within_loop_limit", "passed": true,
                "evidence_sha256": sha(r#""certificate""#)}])
    );
}

#[test]
fn a_first_rejection_adds_the_residual_and_no_grant() {
    // A first attempt has nothing to be compared with, so it cannot stall, whatever it asks.
    for reply in [flip(&[2]), asking(2, json!("chords"))] {
        let second = ask(&task(), vec![reply]);
        assert_eq!(second["stage"], "attempt:1");
        assert_eq!(
            second["prompt"],
            format!("{PROMPT}\nHost residual: {SECOND_ODD}")
        );
    }
}

#[test]
fn an_attempt_that_does_not_improve_is_granted_the_cycles() {
    // One odd cycle, then two: worse.
    let third = ask(&task(), flips(&[2, 3]));
    assert_eq!(third["stage"], "attempt:2");
    let expected = format!("{PROMPT}\nHost residual: {BOTH_ODD}\n{CYCLES}");
    assert_eq!(third["prompt"], expected);
    assert_eq!(third["prompt_sha256"], sha(&expected));
    // One odd cycle, then one: no better.
    let level = ask(&task(), flips(&[2, 2]));
    assert_eq!(
        level["prompt"],
        format!("{PROMPT}\nHost residual: {SECOND_ODD}\n{CYCLES}")
    );
}

#[test]
fn an_attempt_that_improves_is_not_granted_anything() {
    // Two odd cycles, then one: better.
    let third = ask(&task(), flips(&[3, 2]));
    assert_eq!(
        third["prompt"],
        format!("{PROMPT}\nHost residual: {SECOND_ODD}")
    );
}

#[test]
fn a_stalled_reply_that_asks_for_chords_is_granted_the_chords() {
    let third = ask(&task(), vec![flip(&[2]), asking(3, json!("chords"))]);
    assert_eq!(
        third["prompt"],
        format!("{PROMPT}\nHost residual: {BOTH_ODD}\n{CHORDS}")
    );
    let named = ask(
        &task(),
        vec![flip(&[2]), asking(3, json!("fundamental_cycles"))],
    );
    assert_eq!(
        named["prompt"],
        format!("{PROMPT}\nHost residual: {BOTH_ODD}\n{CYCLES}")
    );
    let null = ask(&task(), vec![flip(&[2]), asking(3, Value::Null)]);
    assert_eq!(null["prompt"], named["prompt"]);
}

#[test]
fn a_grant_stays_under_every_later_prompt_and_the_residual_is_the_latest() {
    // Attempt 1 stalls and is granted the cycles. Attempt 2 improves on it. Attempt 3 is level
    // with attempt 2 and asks for the chords.
    let replies = vec![
        flip(&[2]),
        flip(&[3]),
        flip(&[2]),
        asking(2, json!("chords")),
    ];
    let fourth = ask(&task(), replies[..3].to_vec());
    assert_eq!(fourth["stage"], "attempt:3");
    assert_eq!(
        fourth["prompt"],
        format!("{PROMPT}\nHost residual: {SECOND_ODD}\n{CYCLES}")
    );
    let fifth = ask(&task(), replies.clone());
    assert_eq!(fifth["stage"], "attempt:4");
    assert_eq!(
        fifth["prompt"],
        format!("{PROMPT}\nHost residual: {SECOND_ODD}\n{CYCLES}\n{CHORDS}")
    );
    let mut finished = replies;
    finished.push(flip(&[1]));
    let (passed, report) = run(&task(), finished);
    assert!(passed);
    assert_eq!(report["code"], "DERIVED");
    assert_eq!(
        report["detail"],
        json!({"attempts": 5,
               "grants": [{"attempt": 1, "kind": "fundamental_cycles"},
                          {"attempt": 3, "kind": "chords"}]})
    );
}

#[test]
fn an_unreadable_reply_stalls_once_a_readable_one_has_been_seen() {
    // Nothing readable yet: no grant.
    let second = ask(&task(), vec![json!({})]);
    assert_eq!(
        second["prompt"],
        format!(
            "{PROMPT}\nHost residual: {}",
            r#"{"malformed":"flip list required"}"#
        )
    );
    // After a readable attempt, an unreadable one is no improvement.
    let third = ask(&task(), vec![flip(&[3]), json!({"flip": [9]})]);
    assert_eq!(
        third["prompt"],
        format!(
            "{PROMPT}\nHost residual: {}\n{CYCLES}",
            r#"{"malformed":"flip index out of range"}"#
        )
    );
    // The next readable attempt is compared with the last readable one, two back: two odd
    // cycles then one is an improvement, so there is still one grant.
    let fourth = ask(&task(), vec![flip(&[3]), json!({"flip": [9]}), flip(&[2])]);
    assert_eq!(
        fourth["prompt"],
        format!("{PROMPT}\nHost residual: {SECOND_ODD}\n{CYCLES}")
    );
    // One odd cycle, unreadable, then one again: level with the last readable, a second grant.
    let again = ask(&task(), vec![flip(&[2]), json!({"flip": [9]}), flip(&[2])]);
    assert_eq!(
        again["prompt"],
        format!("{PROMPT}\nHost residual: {SECOND_ODD}\n{CYCLES}\n{CYCLES}")
    );
}

#[test]
fn a_request_for_anything_else_ends_the_run_even_with_a_right_answer() {
    let (passed, report) = run(
        &task(),
        vec![flip(&[2]), asking(0, json!("the_minimal_repair"))],
    );
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "LIFT_SCOPE_VIOLATION");
    assert_eq!(
        report["detail"],
        json!({"trail": [
            {"attempt": 0, "measure": 1,
             "residual": {"flip_count": 1, "minimal_known": false, "odd_cycles": [1]}},
            {"attempt": 1, "lift_request": "the_minimal_repair"},
        ]})
    );
    assert_eq!(
        report["predicates"],
        json!([{"name": "lift_request_structural", "passed": false,
                "evidence_sha256":
                    sha(r#"{"attempt":1,"lift_request":"the_minimal_repair"}"#)}])
    );
}

#[test]
fn a_request_that_is_not_text_is_named_by_its_json() {
    for (asked, named) in [
        (json!(["chords"]), r#"["chords"]"#),
        (json!(1), "1"),
        (json!(false), "false"),
        (json!({"kind": "chords"}), r#"{"kind":"chords"}"#),
        (json!("Chords"), "Chords"),
        (json!(""), ""),
    ] {
        let (_, report) = run(&task(), vec![asking(0, asked)]);
        assert_eq!(report["code"], "LIFT_SCOPE_VIOLATION");
        assert_eq!(
            report["detail"]["trail"],
            json!([{"attempt": 0, "lift_request": named}])
        );
    }
}

#[test]
fn using_every_attempt_halts_on_the_limit() {
    let (passed, report) = run(&task(), flips(&[2, 3, 2, 3, 2]));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "HALTED_ON_LIMIT");
    assert_eq!(
        report["detail"],
        json!({"attempts": 5,
               "grants": [{"attempt": 1, "kind": "fundamental_cycles"},
                          {"attempt": 3, "kind": "fundamental_cycles"}]})
    );
    assert_eq!(
        report["predicates"],
        json!([{"name": "certificate_within_loop_limit", "passed": false,
                "evidence_sha256": sha(r#""limit""#)}])
    );
    assert_eq!(ask(&task(), flips(&[2, 3, 2, 3]))["stage"], "attempt:4");
}

#[test]
fn the_task_may_set_a_lower_limit() {
    let (_, one) = run(&limited(json!(1)), flips(&[2]));
    assert_eq!(one["code"], "HALTED_ON_LIMIT");
    assert_eq!(one["detail"], json!({"attempts": 1, "grants": []}));
    assert_eq!(
        ask(&limited(json!(2)), flips(&[2]))["prompt"],
        format!(
            "{}\nHost residual: {SECOND_ODD}",
            PROMPT.replace("]}", r#"],"max_attempts":2}"#)
        )
    );
}

#[test]
fn a_missing_reply_halts_on_the_budget() {
    let outcome = judge(&request(&task(), &[Some(flip(&[2])), None]));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["code"], "HALTED_ON_BUDGET");
    assert_eq!(result["detail"], json!({"attempts": 1, "grants": []}));
    assert_eq!(
        result["predicates"][0]["evidence_sha256"],
        sha(r#""budget""#)
    );
}

#[test]
fn a_task_the_host_cannot_read_is_refused_before_anything_is_asked() {
    let mut odd = task();
    odd["labels"] = json!([1, 0, 0, 0, true]);
    assert_eq!(
        bad_task(odd),
        "every label must be the exact integer 0 or 1"
    );
    let mut short = task();
    short["labels"] = json!([1]);
    assert_eq!(bad_task(short), "one label per edge");
    assert_eq!(bad_task(limited(json!(0))), "max_attempts must be in 1..5");
    assert_eq!(bad_task(limited(json!(6))), "max_attempts must be in 1..5");
    assert_eq!(
        bad_task(limited(json!("5"))),
        "max_attempts must be an exact int"
    );
    assert!(matches!(
        next(&request(&limited(json!(5)), &[])),
        Outcome::Pass { .. }
    ));
}
