//! WF9, bounded check-and-repair: the attempt limit, the residual carried into the next prompt,
//! and the verdict of each way a run can end.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf09-tests:v1

use pfp_operads::families::wf09::{DEFAULT_ATTEMPTS, FAMILY, MAX_ATTEMPTS};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

/// Two triangles sharing the edge 2, with the first triangle odd. One flip of edge 0 or edge 1
/// mends it.
fn task() -> Value {
    json!({"statement": "Flip the fewest edge labels so every cycle has an even label sum.",
           "edges": [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]], "labels": [1, 0, 0, 0, 0],
           "max_attempts": 3})
}

const PROMPT: &str = concat!(
    "WF9 Bounded check-and-repair. ",
    "Flip the fewest edge labels so every cycle has an even label sum.\n",
    r#"{"edges":[[0,1],[1,2],[2,0],[2,3],[3,0]],"labels":[1,0,0,0,0],"max_attempts":3}"#
);

fn request(task: &Value, replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF9", "task": task, "replies": replies}).to_string()
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

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF9",
            "Bounded check-and-repair",
            "xor_cycle_minimal_repair"
        )
    );
    assert_eq!((DEFAULT_ATTEMPTS, MAX_ATTEMPTS), (3, 8));
}

#[test]
fn the_first_question_is_the_task_as_written() {
    let first = ask(&task(), vec![]);
    assert_eq!(first["stage"], "attempt:0");
    assert_eq!(first["prompt"], PROMPT);
    assert_eq!(first["prompt_sha256"], sha(PROMPT));
}

#[test]
fn a_least_repair_on_the_first_attempt_is_certified() {
    let (passed, report) = run(&task(), vec![flip(&[0])]);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "ACCEPTED_FIRST_TRY");
    let row = json!({"attempt": 0, "measure": 0,
                     "residual": {"flip_count": 1, "minimal_known": true, "odd_cycles": []}});
    assert_eq!(report["detail"], json!({"attempts": 1, "trail": [row]}));
    assert_eq!(
        report["predicates"],
        json!([{"name": "accepted_within_limit", "passed": true,
                "evidence_sha256": sha(concat!(
                    r#"[{"attempt":0,"measure":0,"#,
                    r#""residual":{"flip_count":1,"minimal_known":true,"odd_cycles":[]}}]"#))}])
    );
    assert_eq!(report["every_predicate_passed"], true);
    assert_eq!(report["asked"].as_array().map(Vec::len), Some(1));
}

#[test]
fn a_rejected_attempt_puts_its_residual_under_the_next_prompt() {
    let second = ask(&task(), vec![flip(&[2])]);
    assert_eq!(second["stage"], "attempt:1");
    let prompt = format!(
        "{PROMPT}\nHost residual: {}",
        r#"{"flip_count":1,"minimal_known":false,"odd_cycles":[1]}"#
    );
    assert_eq!(second["prompt"], prompt);
    assert_eq!(second["prompt_sha256"], sha(&prompt));
}

#[test]
fn each_prompt_carries_only_the_latest_residual() {
    let third = ask(&task(), vec![flip(&[2]), flip(&[3])]);
    assert_eq!(third["stage"], "attempt:2");
    assert_eq!(
        third["prompt"],
        format!(
            "{PROMPT}\nHost residual: {}",
            r#"{"flip_count":1,"minimal_known":false,"odd_cycles":[0,1]}"#
        )
    );
}

#[test]
fn a_repair_accepted_on_a_later_attempt_is_certified_as_repaired() {
    let (passed, report) = run(&task(), vec![flip(&[2]), flip(&[0])]);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "REPAIRED");
    assert_eq!(report["detail"]["attempts"], 2);
    assert_eq!(
        report["detail"]["trail"],
        json!([
            {"attempt": 0, "measure": 1,
             "residual": {"flip_count": 1, "minimal_known": false, "odd_cycles": [1]}},
            {"attempt": 1, "measure": 0,
             "residual": {"flip_count": 1, "minimal_known": true, "odd_cycles": []}},
        ])
    );
    let (_, third) = run(&task(), vec![flip(&[2]), flip(&[3]), flip(&[1])]);
    assert_eq!(
        (&third["code"], &third["detail"]["attempts"]),
        (&json!("REPAIRED"), &json!(3))
    );
}

#[test]
fn a_repair_that_is_not_the_least_is_never_accepted() {
    let (passed, report) = run(&task(), vec![flip(&[0, 3, 4]); 3]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "REPAIR_LIMIT_EXHAUSTED");
    assert_eq!(report["detail"]["attempts"], 3);
    let row = |attempt: usize| {
        json!({"attempt": attempt, "measure": 0,
               "residual": {"flip_count": 3, "minimal_known": true, "odd_cycles": []}})
    };
    assert_eq!(report["detail"]["trail"], json!([row(0), row(1), row(2)]));
    assert_eq!(report["predicates"][0]["name"], "accepted_within_limit");
    assert_eq!(report["predicates"][0]["passed"], false);
    assert_eq!(report["every_predicate_passed"], false);
}

#[test]
fn the_run_ends_at_the_limit_the_task_states() {
    let limited = |limit: usize| {
        let mut task = task();
        task["max_attempts"] = json!(limit);
        task
    };
    let (_, one) = run(&limited(1), vec![flip(&[2])]);
    assert_eq!(one["code"], "REPAIR_LIMIT_EXHAUSTED");
    assert_eq!(one["detail"]["attempts"], 1);
    // With a limit of two the same first reply leaves a second question.
    assert_eq!(ask(&limited(2), vec![flip(&[2])])["stage"], "attempt:1");
    let (_, eight) = run(&limited(8), vec![flip(&[2]); 8]);
    assert_eq!(eight["detail"]["attempts"], 8);
    assert_eq!(ask(&limited(8), vec![flip(&[2]); 7])["stage"], "attempt:7");
}

#[test]
fn a_task_that_states_no_limit_gets_three_attempts() {
    let mut task = task();
    task.as_object_mut().expect("object").remove("max_attempts");
    assert_eq!(ask(&task, vec![flip(&[2]); 2])["stage"], "attempt:2");
    let (_, report) = run(&task, vec![flip(&[2]); 3]);
    assert_eq!(report["code"], "REPAIR_LIMIT_EXHAUSTED");
    assert_eq!(report["detail"]["attempts"], 3);
}

#[test]
fn a_reply_the_host_cannot_read_uses_up_an_attempt_and_says_why() {
    let second = ask(&task(), vec![json!({"flip": ["1"]})]);
    assert_eq!(
        second["prompt"],
        format!(
            "{PROMPT}\nHost residual: {}",
            r#"{"malformed":"flip must be an exact int"}"#
        )
    );
    let (passed, report) = run(
        &task(),
        vec![json!({"flip": ["1"]}), json!({"flip": [9]}), json!({})],
    );
    assert!(!passed);
    assert_eq!(report["code"], "REPAIR_LIMIT_EXHAUSTED");
    assert_eq!(
        report["detail"]["trail"],
        json!([
            {"attempt": 0, "measure": null, "residual": {"malformed": "flip must be an exact int"}},
            {"attempt": 1, "measure": null, "residual": {"malformed": "flip index out of range"}},
            {"attempt": 2, "measure": null, "residual": {"malformed": "flip list required"}},
        ])
    );
    let (mended, after) = run(&task(), vec![json!("flip 0"), flip(&[1])]);
    assert!(mended);
    assert_eq!(after["code"], "REPAIRED");
}

#[test]
fn a_missing_reply_ends_the_run_with_the_attempts_made_so_far() {
    let outcome = judge(&request(&task(), &[Some(flip(&[2])), None]));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["code"], "REPAIR_LIMIT_EXHAUSTED");
    assert_eq!(result["detail"]["attempts"], 1);
    assert_eq!(result["predicates"][0]["passed"], false);
    assert_eq!(result["asked"].as_array().map(Vec::len), Some(2));
    let Outcome::Fail { result: none } = judge(&request(&task(), &[None])) else {
        panic!("expected a failed run");
    };
    assert_eq!(none["detail"], json!({"attempts": 0, "trail": []}));
    assert_eq!(none["predicates"][0]["evidence_sha256"], sha("[]"));
}

#[test]
fn a_reply_after_the_run_has_ended_is_a_bad_request() {
    let outcome = judge(&request(&task(), &all(vec![flip(&[0]), flip(&[1])])));
    let Outcome::Refused { refusal } = outcome else {
        panic!("expected a refusal, got {outcome:?}");
    };
    assert_eq!(refusal.code, "BAD_REQUEST");
}

#[test]
fn an_even_graph_is_repaired_by_flipping_nothing() {
    let even = json!({"edges": [[0, 1], [1, 2], [2, 0]], "labels": [1, 1, 0]});
    let (passed, report) = run(&even, vec![flip(&[])]);
    assert!(passed);
    assert_eq!(report["code"], "ACCEPTED_FIRST_TRY");
    let (wasteful, _) = run(&even, vec![flip(&[0, 1]); 3]);
    assert!(!wasteful);
}

#[test]
fn a_task_the_host_cannot_read_is_refused_before_anything_is_asked() {
    let with = |key: &str, value: Value| {
        let mut task = task();
        task[key] = value;
        task
    };
    assert_eq!(
        bad_task(with("labels", json!([1, 0, 0, 0, 2]))),
        "every label must be the exact integer 0 or 1"
    );
    assert_eq!(
        bad_task(with("edges", json!([[0, 1], [1, 2], [2, 0], [2, 3], [3]]))),
        "each edge is a pair of exact integers"
    );
    assert_eq!(
        bad_task(with("labels", json!([1, 0]))),
        "one label per edge"
    );
    assert_eq!(
        bad_task(json!({"labels": [1]})),
        "edges and labels must be lists"
    );
    assert_eq!(
        bad_task(with("max_attempts", json!(0))),
        "max_attempts must be in 1..8"
    );
    assert_eq!(
        bad_task(with("max_attempts", json!(9))),
        "max_attempts must be in 1..8"
    );
    assert_eq!(
        bad_task(with("max_attempts", json!("3"))),
        "max_attempts must be an exact int"
    );
    assert!(matches!(
        next(&request(&with("max_attempts", json!(8)), &[])),
        Outcome::Pass { .. }
    ));
}
