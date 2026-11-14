//! WF26, multi-round antibody dialogue: which constraint each kind of mistake adds, how the set
//! is carried forward, and how the dialogue ends.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf26-tests:v1

use pfp_operads::families::monic::EPITOPES;
use pfp_operads::families::wf26::{ANTIBODIES, FAMILY};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

/// The roots 1, 2, 3: the answer is x^3 - 6x^2 + 11x - 6.
fn task(limit: usize) -> Value {
    json!({"statement": "Give the monic polynomial with roots 1, 2, 3.",
           "roots": [1, 2, 3], "max_attempts": limit})
}

fn prompt(limit: usize) -> String {
    format!(
        concat!(
            "WF26 Multi-round antibody dialogue. ",
            "Give the monic polynomial with roots 1, 2, 3.\n",
            r#"{{"max_attempts":{},"roots":[1,2,3]}}"#
        ),
        limit
    )
}

const NONMONIC: &str = concat!(
    r#"{"constraint":"The leading coefficient must be 1.","#,
    r#""epitope":"NONMONIC_LEADING_COEFFICIENT"}"#
);
const SIGNS: &str = concat!(
    r#"{"constraint":"Some coefficient signs are wrong; "#,
    r#"the sign of each coefficient follows Vieta.","epitope":"SIGN_MISMATCH"}"#
);
const VALUE: &str = concat!(
    r#"{"constraint":"The coefficients do not vanish at the stated roots.","#,
    r#""epitope":"WRONG_VALUE"}"#
);
const NOTATION: &str = concat!(
    r#"{"constraint":"Write integers as integers and other rationals as p/q in lowest terms.","#,
    r#""epitope":"RATIONAL_NONCANONICAL"}"#
);
const SHAPE: &str = concat!(
    r#"{"constraint":"Reply with one JSON object of the form "#,
    r#"{\"coefficients\": [...]} and nothing else.","epitope":"MALFORMED_JSON"}"#
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
    json!({"workflow": "WF26", "task": task, "replies": replies}).to_string()
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

/// A reply as the model writes it: text holding the coefficient object.
fn text(coefficients: Value) -> Value {
    Value::String(json!({ "coefficients": coefficients }).to_string())
}

fn right() -> Value {
    text(json!([1, -6, 11, -6]))
}

/// The prompt after a rejection that leaves these antibodies.
fn carrying(limit: usize, antibodies: &[&str]) -> String {
    format!(
        "{}\nHost residual: {{\"antibodies\":[{}]}}",
        prompt(limit),
        antibodies.join(",")
    )
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF26",
            "Multi-round antibody dialogue",
            "epitope_antibody_exact_oracle"
        )
    );
}

#[test]
fn every_kind_of_mistake_has_one_antibody() {
    assert_eq!(ANTIBODIES.map(|(epitope, _)| epitope), EPITOPES);
    for (_, constraint) in ANTIBODIES {
        assert!(
            !constraint.chars().any(|c| c.is_ascii_digit() && c != '1'),
            "{constraint}"
        );
    }
}

#[test]
fn the_first_question_is_the_task_as_written() {
    let first = ask(&task(3), vec![]);
    assert_eq!(first["stage"], "attempt:0");
    assert_eq!(first["prompt"], prompt(3));
    assert_eq!(first["prompt_sha256"], sha(&prompt(3)));
}

#[test]
fn the_expected_polynomial_on_the_first_round_is_certified_with_no_antibody() {
    let (passed, report) = run(&task(3), vec![right()]);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "ACCEPTED_FIRST_TRY");
    assert_eq!(
        report["detail"],
        json!({"antibodies": 0, "attempts": 1,
               "trail": [{"attempt": 0, "measure": "CLEAN", "residual": {"antibodies": []}}]})
    );
    assert_eq!(
        report["predicates"],
        json!([{"name": "accepted_within_limit", "passed": true,
                "evidence_sha256": sha(
                    r#"[{"attempt":0,"measure":"CLEAN","residual":{"antibodies":[]}}]"#)}])
    );
}

#[test]
fn each_kind_of_mistake_adds_its_own_constraint_to_the_next_prompt() {
    for (reply, antibody) in [
        (text(json!([2, -12, 22, -12])), NONMONIC),
        (text(json!([1, 6, 11, 6])), SIGNS),
        (text(json!([1, -6, 11, -5])), VALUE),
        (text(json!([1, "-6/1", 11, -6])), NOTATION),
        (json!("coefficients: 1, -6, 11, -6"), SHAPE),
    ] {
        let second = ask(&task(3), vec![reply]);
        assert_eq!(second["stage"], "attempt:1");
        let expected = carrying(3, &[antibody]);
        assert_eq!(second["prompt"], expected);
        assert_eq!(second["prompt_sha256"], sha(&expected));
    }
}

#[test]
fn the_set_grows_in_the_order_the_mistakes_were_seen() {
    let third = ask(
        &task(3),
        vec![text(json!([2, -12, 22, -12])), text(json!([1, 6, 11, 6]))],
    );
    assert_eq!(third["stage"], "attempt:2");
    assert_eq!(third["prompt"], carrying(3, &[NONMONIC, SIGNS]));
    let other = ask(
        &task(3),
        vec![text(json!([1, 6, 11, 6])), text(json!([2, -12, 22, -12]))],
    );
    assert_eq!(other["prompt"], carrying(3, &[SIGNS, NONMONIC]));
}

#[test]
fn a_mistake_seen_before_adds_nothing() {
    let third = ask(&task(3), vec![text(json!([2, -12, 22, -12])); 2]);
    assert_eq!(third["prompt"], carrying(3, &[NONMONIC]));
    let mixed = ask(
        &task(5),
        vec![
            text(json!([3, 0, 0, 0])),
            text(json!([1, 6, 11, 6])),
            text(json!([2, 0, 0, 0])),
            text(json!([1, 6, -11, 6])),
        ],
    );
    assert_eq!(mixed["stage"], "attempt:4");
    assert_eq!(mixed["prompt"], carrying(5, &[NONMONIC, SIGNS]));
}

#[test]
fn a_repair_within_the_limit_is_certified_with_its_antibodies_counted() {
    let (passed, report) = run(
        &task(3),
        vec![
            text(json!([2, -12, 22, -12])),
            text(json!([1, 6, 11, 6])),
            right(),
        ],
    );
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "REPAIRED");
    assert_eq!(report["detail"]["attempts"], 3);
    assert_eq!(report["detail"]["antibodies"], 2);
    let nonmonic: Value = serde_json::from_str(NONMONIC).expect("JSON");
    let signs: Value = serde_json::from_str(SIGNS).expect("JSON");
    assert_eq!(
        report["detail"]["trail"],
        json!([
            {"attempt": 0, "measure": "NONMONIC_LEADING_COEFFICIENT",
             "residual": {"antibodies": [nonmonic]}},
            {"attempt": 1, "measure": "SIGN_MISMATCH",
             "residual": {"antibodies": [nonmonic, signs]}},
            {"attempt": 2, "measure": "CLEAN", "residual": {"antibodies": [nonmonic, signs]}},
        ])
    );
    assert_eq!(report["every_predicate_passed"], true);
}

#[test]
fn the_same_mistake_every_round_is_refused_at_the_limit() {
    let (passed, report) = run(&task(3), vec![text(json!([2, -12, 22, -12])); 3]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "REPAIR_LIMIT_EXHAUSTED");
    assert_eq!(report["detail"]["attempts"], 3);
    assert_eq!(report["detail"]["antibodies"], 1);
    assert_eq!(report["predicates"][0]["name"], "accepted_within_limit");
    assert_eq!(report["predicates"][0]["passed"], false);
    let (_, never) = run(&task(3), vec![json!("1, -6, 11, -6"); 3]);
    assert_eq!(never["code"], "REPAIR_LIMIT_EXHAUSTED");
    assert_eq!(never["detail"]["trail"][2]["measure"], "MALFORMED_JSON");
    assert_eq!(never["detail"]["antibodies"], 1);
}

#[test]
fn a_reply_that_is_not_text_uses_a_round_and_adds_no_antibody() {
    let object = json!({"coefficients": [1, -6, 11, -6]});
    let second = ask(&task(3), vec![object.clone()]);
    assert_eq!(
        second["prompt"],
        format!(
            "{}\nHost residual: {}",
            prompt(3),
            r#"{"malformed":"reply must be text"}"#
        )
    );
    let (passed, report) = run(&task(3), vec![object.clone(), json!(7), json!(null)]);
    assert!(!passed);
    assert_eq!(report["code"], "REPAIR_LIMIT_EXHAUSTED");
    assert_eq!(report["detail"]["antibodies"], 0);
    assert_eq!(
        report["detail"]["trail"][0],
        json!({"attempt": 0, "measure": null, "residual": {"malformed": "reply must be text"}})
    );
    // The antibodies already collected come back with the next reply that is text.
    let fourth = ask(
        &task(4),
        vec![
            text(json!([1, 6, 11, 6])),
            object,
            text(json!([1, 6, 11, 6])),
        ],
    );
    assert_eq!(fourth["prompt"], carrying(4, &[SIGNS]));
}

#[test]
fn the_limit_is_the_tasks_or_three() {
    let (_, one) = run(&task(1), vec![text(json!([1, 6, 11, 6]))]);
    assert_eq!(one["code"], "REPAIR_LIMIT_EXHAUSTED");
    assert_eq!(one["detail"]["attempts"], 1);
    let unlimited = json!({"roots": [1, 2, 3]});
    let wrong = text(json!([1, 6, 11, 6]));
    assert_eq!(
        ask(&unlimited, vec![wrong.clone(); 2])["stage"],
        "attempt:2"
    );
    let (_, three) = run(&unlimited, vec![wrong; 3]);
    assert_eq!(three["detail"]["attempts"], 3);
}

#[test]
fn rational_roots_are_expanded_exactly() {
    // (x - 1/2)(x + 2/3) = x^2 + x/6 - 1/3
    let halves = json!({"roots": ["1/2", "-2/3"]});
    let (passed, _) = run(&halves, vec![text(json!([1, "1/6", "-1/3"]))]);
    assert!(passed);
    let (wrong, report) = run(&halves, vec![text(json!([1, "-1/6", "-1/3"])); 3]);
    assert!(!wrong);
    assert_eq!(report["detail"]["trail"][0]["measure"], "SIGN_MISMATCH");
}

#[test]
fn a_missing_reply_ends_the_dialogue_with_the_rounds_so_far() {
    let outcome = judge(&request(
        &task(3),
        &[Some(text(json!([1, 6, 11, 6]))), None],
    ));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["code"], "REPAIR_LIMIT_EXHAUSTED");
    assert_eq!(result["detail"]["attempts"], 1);
    assert_eq!(result["detail"]["antibodies"], 1);
}

#[test]
fn a_task_the_host_cannot_read_is_refused_before_anything_is_asked() {
    assert_eq!(bad_task(json!({"roots": []})), "roots required");
    assert_eq!(bad_task(json!({"max_attempts": 3})), "roots required");
    assert_eq!(
        bad_task(json!({"roots": [1, 2.5]})),
        "every root must be an exact rational"
    );
    assert_eq!(bad_task(task(0)), "max_attempts must be in 1..8");
    assert_eq!(bad_task(task(9)), "max_attempts must be in 1..8");
    let mut loose = task(3);
    loose["max_attempts"] = json!("3");
    assert_eq!(bad_task(loose), "max_attempts must be an exact int");
    assert!(matches!(
        next(&request(&task(8), &[])),
        Outcome::Pass { .. }
    ));
}
