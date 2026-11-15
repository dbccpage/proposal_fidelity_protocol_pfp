//! WF27, hinted retraction: the structural hint under each rejected attempt, and the stop when a
//! residual comes back three attempts later.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf27-tests:v1

use pfp_operads::families::wf27::{FAMILY, PERIOD};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

/// Two triangles sharing the edge 2, with the first triangle odd. The first cycle runs through
/// the vertices 0, 1, 2 and the second through 0, 2, 3.
fn task(limit: usize) -> Value {
    json!({"statement": "Flip the fewest edge labels so every cycle has an even label sum.",
           "edges": [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]], "labels": [1, 0, 0, 0, 0],
           "max_attempts": limit})
}

fn prompt(limit: usize) -> String {
    format!(
        concat!(
            "WF27 Hinted retraction with a stationary-loop detector. ",
            "Flip the fewest edge labels so every cycle has an even label sum.\n",
            r#"{{"edges":[[0,1],[1,2],[2,0],[2,3],[3,0]],"labels":[1,0,0,0,0],"max_attempts":{}}}"#
        ),
        limit
    )
}

/// What the host finds after one flip of the shared edge: the second cycle is odd.
const SECOND_ODD: &str = r#"{"flip_count":1,"minimal_known":false,"odd_cycles":[1]}"#;
/// What it finds after one flip of an edge only the second triangle has: both cycles are odd.
const BOTH_ODD: &str = r#"{"flip_count":1,"minimal_known":false,"odd_cycles":[0,1]}"#;

fn request(task: &Value, replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF27", "task": task, "replies": replies}).to_string()
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

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF27",
            "Hinted retraction with a stationary-loop detector",
            "xor_residual_gate_stationary_loop"
        )
    );
    assert_eq!(PERIOD, 3);
}

#[test]
fn the_first_question_is_the_task_as_written() {
    let first = ask(&task(3), vec![]);
    assert_eq!(first["stage"], "attempt:0");
    assert_eq!(first["prompt"], prompt(3));
    assert_eq!(first["prompt_sha256"], sha(&prompt(3)));
}

#[test]
fn a_rejected_attempt_adds_the_residual_and_the_vertices_of_each_odd_cycle() {
    let second = ask(&task(3), flips(&[2]));
    assert_eq!(second["stage"], "attempt:1");
    let expected = format!(
        "{}\nHost residual: {SECOND_ODD}\nStructural hint: {}",
        prompt(3),
        r#"{"cycle_vertices":[[0,2,3]],"odd_cycles":[1]}"#
    );
    assert_eq!(second["prompt"], expected);
    assert_eq!(second["prompt_sha256"], sha(&expected));
}

#[test]
fn each_prompt_carries_only_the_latest_residual_and_hint() {
    let third = ask(&task(3), flips(&[2, 3]));
    assert_eq!(third["stage"], "attempt:2");
    assert_eq!(
        third["prompt"],
        format!(
            "{}\nHost residual: {BOTH_ODD}\nStructural hint: {}",
            prompt(3),
            r#"{"cycle_vertices":[[0,1,2],[0,2,3]],"odd_cycles":[0,1]}"#
        )
    );
}

#[test]
fn a_hint_names_vertices_by_their_own_names_in_ascending_order() {
    let named = json!({"edges": [[30, -4], [-4, 7], [7, 30]], "labels": [1, 0, 0]});
    let second = ask(&named, vec![flip(&[])]);
    let text = second["prompt"].as_str().expect("text");
    assert!(
        text.ends_with(r#"Structural hint: {"cycle_vertices":[[-4,7,30]],"odd_cycles":[0]}"#),
        "{text}"
    );
}

#[test]
fn an_unreadable_reply_gets_its_reason_and_an_empty_hint() {
    let second = ask(&task(3), vec![json!({"flip": [5]})]);
    assert_eq!(
        second["prompt"],
        format!(
            "{}\nHost residual: {}\nStructural hint: {}",
            prompt(3),
            r#"{"malformed":"flip index out of range"}"#,
            r#"{"cycle_vertices":[],"odd_cycles":[]}"#
        )
    );
}

#[test]
fn a_least_repair_is_certified_on_the_first_attempt_or_a_later_one() {
    let (passed, first) = run(&task(3), flips(&[1]));
    assert!(passed);
    assert_eq!(first["verdict"], "HOST_CERTIFIED");
    assert_eq!(first["code"], "ACCEPTED_FIRST_TRY");
    let accepted = json!({"flip_count": 1, "minimal_known": true, "odd_cycles": []});
    assert_eq!(
        first["detail"],
        json!({"attempts": 1,
               "trail": [{"attempt": 0, "measure": 0, "residual": accepted}]})
    );
    assert_eq!(
        first["predicates"],
        json!([{"name": "accepted_within_limit", "passed": true,
                "evidence_sha256": sha(concat!(
                    r#"[{"attempt":0,"measure":0,"#,
                    r#""residual":{"flip_count":1,"minimal_known":true,"odd_cycles":[]}}]"#))}])
    );
    let (later, second) = run(&task(3), flips(&[2, 0]));
    assert!(later);
    assert_eq!(second["code"], "REPAIRED");
    assert_eq!(second["detail"]["attempts"], 2);
    assert_eq!(second["detail"]["trail"][0]["measure"], 1);
    assert_eq!(second["detail"]["trail"][1]["residual"], accepted);
}

#[test]
fn the_same_residual_three_attempts_later_stops_the_run() {
    let (passed, report) = run(&task(5), flips(&[2, 3, 4, 2]));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "STATIONARY_LOOP");
    assert_eq!(
        report["detail"],
        json!({"turn": 3, "repeats_turn": 0,
               "residual": {"flip_count": 1, "minimal_known": false, "odd_cycles": [1]},
               "hint": {"cycle_vertices": [[0, 2, 3]], "odd_cycles": [1]}})
    );
    let row = |attempt: usize, measure: usize, residual: &str| {
        format!(r#"{{"attempt":{attempt},"measure":{measure},"residual":{residual}}}"#)
    };
    let trail = format!(
        "[{},{},{},{}]",
        row(0, 1, SECOND_ODD),
        row(1, 2, BOTH_ODD),
        row(2, 2, BOTH_ODD),
        row(3, 1, SECOND_ODD)
    );
    assert_eq!(
        report["predicates"],
        json!([{"name": "residual_not_stationary", "passed": false,
                "evidence_sha256": sha(&trail)}])
    );
    assert_eq!(report["asked"].as_array().map(Vec::len), Some(4));
}

#[test]
fn the_host_compares_with_the_attempt_three_back_and_no_other() {
    // The same residual one and two attempts later is not the signal.
    let (_, three) = run(&task(3), flips(&[2, 2, 2]));
    assert_eq!(three["code"], "TURN_CAP_EXHAUSTED");
    assert_eq!(ask(&task(5), flips(&[2, 2, 2]))["stage"], "attempt:3");
    // Attempt 3 differs from attempt 0, so the run goes on; attempt 4 repeats attempt 1.
    assert_eq!(ask(&task(5), flips(&[2, 3, 3, 3]))["stage"], "attempt:4");
    let (_, later) = run(&task(5), flips(&[2, 3, 3, 3, 4]));
    assert_eq!(later["code"], "STATIONARY_LOOP");
    assert_eq!(later["detail"]["turn"], 4);
    assert_eq!(later["detail"]["repeats_turn"], 1);
    assert_eq!(later["detail"]["hint"]["odd_cycles"], json!([0, 1]));
    // The residual must be the same in every part: one more flip is a different residual.
    let mut replies = flips(&[2, 3, 4]);
    replies.push(flip(&[0, 1, 2]));
    assert_eq!(ask(&task(5), replies)["stage"], "attempt:4");
}

#[test]
fn a_reply_the_host_cannot_read_is_never_taken_as_a_loop() {
    let (passed, report) = run(&task(5), vec![json!({}); 5]);
    assert!(!passed);
    assert_eq!(report["code"], "TURN_CAP_EXHAUSTED");
    assert_eq!(report["detail"]["attempts"], 5);
    assert_eq!(
        report["detail"]["trail"][4],
        json!({"attempt": 4, "measure": null, "residual": {"malformed": "flip list required"}})
    );
    assert_eq!(report["predicates"][0]["name"], "accepted_within_limit");
    assert_eq!(report["predicates"][0]["passed"], false);
}

#[test]
fn the_attempt_limit_ends_the_run_as_turn_cap_exhausted() {
    let (passed, report) = run(&task(2), flips(&[2, 3]));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "TURN_CAP_EXHAUSTED");
    assert_eq!(report["detail"]["attempts"], 2);
    assert_eq!(report["detail"]["trail"][1]["measure"], 2);
    assert_eq!(report["every_predicate_passed"], false);
    let mut unlimited = task(3);
    unlimited
        .as_object_mut()
        .expect("object")
        .remove("max_attempts");
    assert_eq!(ask(&unlimited, flips(&[2, 3]))["stage"], "attempt:2");
    let (_, default) = run(&unlimited, flips(&[2, 3, 4]));
    assert_eq!(default["detail"]["attempts"], 3);
}

#[test]
fn a_missing_reply_ends_the_run_with_the_attempts_made_so_far() {
    let outcome = judge(&request(&task(3), &[Some(flip(&[2])), None]));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["code"], "TURN_CAP_EXHAUSTED");
    assert_eq!(result["detail"]["attempts"], 1);
    assert_eq!(result["asked"].as_array().map(Vec::len), Some(2));
}

#[test]
fn a_task_the_host_cannot_read_is_refused_before_anything_is_asked() {
    let with = |key: &str, value: Value| {
        let mut task = task(3);
        task[key] = value;
        task
    };
    assert_eq!(
        bad_task(with("labels", json!([1, 0, 0, 0, "1"]))),
        "every label must be the exact integer 0 or 1"
    );
    assert_eq!(
        bad_task(with("edges", json!("ring"))),
        "edges and labels must be lists"
    );
    assert_eq!(bad_task(task(0)), "max_attempts must be in 1..8");
    assert_eq!(bad_task(task(9)), "max_attempts must be in 1..8");
    assert_eq!(
        bad_task(with("max_attempts", json!(2.5))),
        "max_attempts must be an exact int"
    );
    assert!(matches!(
        next(&request(&task(8), &[])),
        Outcome::Pass { .. }
    ));
}
