//! WF7, typed refusal: the rank test against answers, refusals, bluffs and false refusals.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf07-tests:v1

use pfp_operads::families::wf07::{FAMILY, INCONSISTENT, UNDERDETERMINED};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

fn solvable() -> Value {
    json!({"statement": "Solve A x = b exactly or refuse with a code.", "A": [[1, 1], [1, -1]], "b": [3, 1]})
}

fn inconsistent() -> Value {
    json!({"A": [[1, 1], [2, 2]], "b": [3, 7]})
}

fn underdetermined() -> Value {
    json!({"A": [[1, 1], [2, 2]], "b": [3, 6]})
}

/// The report of the run with this one reply, and whether the host passed it.
fn run(task: Value, content: Value) -> (bool, Value) {
    let request = json!({"workflow": "WF7", "task": task, "replies": [{"content": content}]});
    match judge(&request.to_string()) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn verdict(task: Value, content: Value) -> (String, String) {
    let (_, report) = run(task, content);
    (
        report["verdict"].as_str().expect("verdict").to_owned(),
        report["code"].as_str().expect("code").to_owned(),
    )
}

fn pair(verdict: &str, code: &str) -> (String, String) {
    (verdict.to_owned(), code.to_owned())
}

fn bad_task(task: Value) -> String {
    match next(&json!({"workflow": "WF7", "task": task}).to_string()) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        ("WF7", "Typed refusal", "typed_refusal_rank_test")
    );
    assert_eq!(
        (INCONSISTENT, UNDERDETERMINED),
        ("UNRESOLVED_INCONSISTENT", "UNRESOLVED_UNDERDETERMINED")
    );
}

#[test]
fn the_one_solution_is_certified_with_the_rank_witness() {
    let (passed, report) = run(solvable(), json!({"answer": [2, 1]}));
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "CERTIFIED");
    assert_eq!(
        report["detail"],
        json!({"witness": {"n": 2, "rank_A": 2, "rank_Ab": 2, "status": "unique"}})
    );
    assert_eq!(
        report["predicates"],
        json!([{
            "name": "answer_equals_unique_solution",
            "passed": true,
            "evidence_sha256": sha(r#"{"n":2,"rank_A":2,"rank_Ab":2,"status":"unique"}"#),
        }])
    );
}

#[test]
fn the_solution_may_be_written_as_fractions() {
    assert_eq!(
        verdict(solvable(), json!({"answer": ["4/2", "3/3"]})),
        pair("HOST_CERTIFIED", "CERTIFIED")
    );
    let halves = json!({"A": [[2, 0], [0, "1/3"]], "b": [1, "1/2"]});
    assert_eq!(
        verdict(halves.clone(), json!({"answer": ["1/2", "3/2"]})),
        pair("HOST_CERTIFIED", "CERTIFIED")
    );
    assert_eq!(
        verdict(halves, json!({"answer": ["1/2", "2/3"]})),
        pair("REFUSED", "ANSWER_EQUALS_UNIQUE_SOLUTION")
    );
}

#[test]
fn a_wrong_short_long_or_missing_answer_to_a_solvable_system_is_refused() {
    for answer in [json!([1, 2]), json!([2]), json!([2, 1, 0]), json!([])] {
        let (passed, report) = run(solvable(), json!({ "answer": answer }));
        assert!(!passed);
        assert_eq!(report["code"], "ANSWER_EQUALS_UNIQUE_SOLUTION");
        assert_eq!(report["predicates"][0]["passed"], false);
        assert_eq!(
            report["detail"]["failed"],
            json!(["answer_equals_unique_solution"])
        );
        assert_eq!(report["detail"]["witness"]["status"], "unique");
    }
    assert_eq!(
        verdict(solvable(), json!({})),
        pair("REFUSED", "ANSWER_EQUALS_UNIQUE_SOLUTION")
    );
}

#[test]
fn an_unanswerable_system_is_refused_with_the_code_of_its_kind() {
    let (passed, report) = run(
        inconsistent(),
        json!({"refusal": "UNRESOLVED_INCONSISTENT"}),
    );
    assert!(passed);
    assert_eq!(report["verdict"], "TYPED_REFUSAL");
    assert_eq!(report["code"], "UNRESOLVED_INCONSISTENT");
    assert_eq!(
        report["detail"],
        json!({"witness": {"n": 2, "rank_A": 1, "rank_Ab": 2, "status": "inconsistent"}})
    );
    assert_eq!(
        report["predicates"],
        json!([{
            "name": "refusal_code_matches_rank_test",
            "passed": true,
            "evidence_sha256": sha(r#"{"n":2,"rank_A":1,"rank_Ab":2,"status":"inconsistent"}"#),
        }])
    );
    let (passed, report) = run(
        underdetermined(),
        json!({"refusal": "UNRESOLVED_UNDERDETERMINED"}),
    );
    assert!(passed);
    assert_eq!(report["code"], "UNRESOLVED_UNDERDETERMINED");
    assert_eq!(
        report["detail"]["witness"],
        json!({"n": 2, "rank_A": 1, "rank_Ab": 1, "status": "underdetermined"})
    );
}

#[test]
fn a_refusal_with_the_wrong_code_is_refused() {
    for (task, code) in [
        (underdetermined(), json!("UNRESOLVED_INCONSISTENT")),
        (inconsistent(), json!("UNRESOLVED_UNDERDETERMINED")),
        (inconsistent(), json!("unresolved_inconsistent")),
        (inconsistent(), json!(7)),
        (inconsistent(), json!(null)),
        (inconsistent(), json!(["UNRESOLVED_INCONSISTENT"])),
    ] {
        let (passed, report) = run(task, json!({ "refusal": code }));
        assert!(!passed);
        assert_eq!(report["code"], "WRONG_REFUSAL_CODE");
        assert_eq!(
            report["predicates"][0]["name"],
            "refusal_code_matches_rank_test"
        );
        assert_eq!(report["predicates"][0]["passed"], false);
    }
}

#[test]
fn a_refusal_of_a_solvable_system_is_a_false_refusal() {
    for code in ["UNRESOLVED_INCONSISTENT", "UNRESOLVED_UNDERDETERMINED"] {
        let (passed, report) = run(solvable(), json!({ "refusal": code }));
        assert!(!passed);
        assert_eq!(report["verdict"], "REFUSED");
        assert_eq!(report["code"], "FALSE_REFUSAL");
        assert_eq!(
            report["predicates"],
            json!([{
                "name": "no_false_refusal",
                "passed": false,
                "evidence_sha256": sha(r#"{"n":2,"rank_A":2,"rank_Ab":2,"status":"unique"}"#),
            }])
        );
        assert_eq!(report["detail"]["witness"]["status"], "unique");
    }
}

#[test]
fn an_answer_to_an_unanswerable_system_is_a_bluff() {
    for (task, status) in [
        (inconsistent(), "inconsistent"),
        (underdetermined(), "underdetermined"),
    ] {
        for content in [json!({"answer": [1, 2]}), json!({"answer": []}), json!({})] {
            let (passed, report) = run(task.clone(), content);
            assert!(!passed);
            assert_eq!(report["code"], "BLUFF");
            assert_eq!(report["predicates"][0]["name"], "no_bluff");
            assert_eq!(report["predicates"][0]["passed"], false);
            assert_eq!(report["detail"]["witness"]["status"], status);
        }
    }
}

#[test]
fn a_reply_with_an_answer_and_a_refusal_is_read_as_a_refusal() {
    assert_eq!(
        verdict(
            solvable(),
            json!({"answer": [2, 1], "refusal": "UNRESOLVED_INCONSISTENT"})
        ),
        pair("REFUSED", "FALSE_REFUSAL")
    );
    assert_eq!(
        verdict(
            inconsistent(),
            json!({"answer": ["bad"], "refusal": "UNRESOLVED_INCONSISTENT"})
        ),
        pair("TYPED_REFUSAL", "UNRESOLVED_INCONSISTENT")
    );
}

#[test]
fn an_answer_that_is_not_a_list_of_exact_rationals_is_malformed_whatever_the_system() {
    for task in [solvable(), inconsistent()] {
        for answer in [
            json!([2, 1.0]),
            json!([2, "1.0"]),
            json!([2, true]),
            json!("21"),
            json!({"x": 2}),
            json!(null),
            json!(2),
        ] {
            let (passed, report) = run(task.clone(), json!({ "answer": answer }));
            assert!(!passed);
            assert_eq!(report["code"], "MALFORMED_CANDIDATE");
            assert_eq!(
                report["detail"],
                json!({"reason": "answer must be a list of exact rationals"})
            );
            assert_eq!(report["predicates"], json!([]));
        }
    }
}

#[test]
fn a_reply_that_is_not_an_object_is_malformed() {
    for content in [
        json!([2, 1]),
        json!("UNRESOLVED_INCONSISTENT"),
        json!(3),
        json!(null),
    ] {
        let (_, report) = run(solvable(), content);
        assert_eq!(report["code"], "MALFORMED_CANDIDATE");
        assert_eq!(
            report["detail"],
            json!({"reason": "the reply must be an object"})
        );
    }
}

#[test]
fn an_overdetermined_system_with_one_solution_is_answerable() {
    let task = json!({"A": [[0, 1], [1, 0], [1, 1]], "b": [5, 7, 12]});
    let (passed, report) = run(task.clone(), json!({"answer": [7, 5]}));
    assert!(passed);
    assert_eq!(
        report["detail"]["witness"],
        json!({"n": 2, "rank_A": 2, "rank_Ab": 2, "status": "unique"})
    );
    let wide = json!({"A": [[1, 2, 3]], "b": [6]});
    let (_, report) = run(wide, json!({"refusal": "UNRESOLVED_UNDERDETERMINED"}));
    assert_eq!(
        report["detail"]["witness"],
        json!({"n": 3, "rank_A": 1, "rank_Ab": 1, "status": "underdetermined"})
    );
}

#[test]
fn a_task_that_is_not_an_exact_rectangular_system_is_refused() {
    let rows = "A must be a nonempty list of rows";
    assert_eq!(bad_task(json!({"b": [1]})), rows);
    assert_eq!(bad_task(json!({"A": [], "b": []})), rows);
    assert_eq!(bad_task(json!({"A": "x", "b": [1]})), rows);
    let exact = "every row of A must be a list of exact rationals";
    assert_eq!(bad_task(json!({"A": [1], "b": [1]})), exact);
    assert_eq!(bad_task(json!({"A": [[1.5]], "b": [1]})), exact);
    assert_eq!(bad_task(json!({"A": [[1], ["x"]], "b": [1, 2]})), exact);
    let b = "b must be a list of exact rationals";
    assert_eq!(bad_task(json!({"A": [[1]]})), b);
    assert_eq!(bad_task(json!({"A": [[1]], "b": 1})), b);
    assert_eq!(bad_task(json!({"A": [[1]], "b": [0.5]})), b);
    let shape = "A must be rectangular, with a column, and match b";
    assert_eq!(bad_task(json!({"A": [[1, 2], [3]], "b": [1, 2]})), shape);
    assert_eq!(bad_task(json!({"A": [[1], [3, 4]], "b": [1, 2]})), shape);
    assert_eq!(bad_task(json!({"A": [[]], "b": [1]})), shape);
    assert_eq!(bad_task(json!({"A": [[1, 2]], "b": [1, 2]})), shape);
    assert_eq!(bad_task(json!({"A": [[1], [2]], "b": [1]})), shape);
}

#[test]
fn the_smallest_system_is_accepted() {
    assert_eq!(
        verdict(json!({"A": [[2]], "b": [1]}), json!({"answer": ["1/2"]})),
        pair("HOST_CERTIFIED", "CERTIFIED")
    );
    assert_eq!(
        verdict(
            json!({"A": [[0]], "b": [1]}),
            json!({"refusal": "UNRESOLVED_INCONSISTENT"})
        ),
        pair("TYPED_REFUSAL", "UNRESOLVED_INCONSISTENT")
    );
    assert_eq!(
        verdict(
            json!({"A": [[0]], "b": [0]}),
            json!({"refusal": "UNRESOLVED_UNDERDETERMINED"})
        ),
        pair("TYPED_REFUSAL", "UNRESOLVED_UNDERDETERMINED")
    );
}
