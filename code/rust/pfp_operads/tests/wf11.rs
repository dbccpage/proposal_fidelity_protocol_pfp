//! WF11, dual-certificate synthesis: an optimum certified by an exact dual, a bound that is
//! not a certificate, and infeasibility certified by a Farkas vector.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf11-tests:v1

use pfp_operads::families::wf11::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const STATEMENT: &str = "Maximise c.x subject to A x <= b and x >= 0, with a certificate.";

/// Maximise x + y subject to x + 2y <= 4 and 3x + y <= 6. The optimum 14/5 is at (8/5, 6/5),
/// and the dual optimum at (2/5, 1/5).
fn task() -> Value {
    json!({"statement": STATEMENT, "A": [[1, 2], [3, 1]], "b": [4, 6], "c": [1, 1]})
}

/// x + y <= 1 and x + y >= 2: no point satisfies both.
fn empty() -> Value {
    json!({"statement": STATEMENT, "A": [[1, 1], [-1, -1]], "b": [1, -2], "c": [1, 0]})
}

/// Maximise 3x + 2y subject to x + y <= 4, x + 3y <= 6 and x <= 3: three rows, two columns.
/// The optimum 11 is at (3, 1), with the dual (2, 0, 1).
fn tall() -> Value {
    json!({"A": [[1, 1], [1, 3], [1, 0]], "b": [4, 6, 3], "c": [3, 2]})
}

fn prompt() -> String {
    format!(
        "WF11 Dual-certificate synthesis. {STATEMENT}\n{}",
        r#"{"A":[[1,2],[3,1]],"b":[4,6],"c":[1,1]}"#
    )
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
    json!({"workflow": "WF11", "task": task, "replies": replies}).to_string()
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
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    report["detail"]["reason"]
        .as_str()
        .expect("a reason")
        .to_owned()
}

/// The predicates of a report as name and outcome, in the order they were recorded.
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

/// The digest of the evidence recorded under a predicate.
fn evidence<'r>(report: &'r Value, name: &str) -> &'r Value {
    let rows = report["predicates"].as_array().expect("predicates");
    let row = rows.iter().find(|row| row["name"] == name);
    &row.unwrap_or_else(|| panic!("no predicate {name}"))["evidence_sha256"]
}

fn pair(x: Value, y: Value) -> Value {
    json!({"x": x, "y": y})
}

fn best() -> Value {
    pair(json!(["8/5", "6/5"]), json!(["2/5", "1/5"]))
}

const OPTIMUM: [&str; 4] = [
    "primal_feasible",
    "dual_feasible",
    "zero_duality_gap",
    "complementary_slackness",
];

/// The four checks of an optimum with these outcomes.
fn four(passed: [bool; 4]) -> Vec<(&'static str, bool)> {
    OPTIMUM.into_iter().zip(passed).collect()
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF11",
            "Dual-certificate synthesis",
            "lp_dual_and_farkas_certificate"
        )
    );
}

#[test]
fn the_one_question_is_the_task_as_written() {
    let first = ask(&task(), vec![]);
    assert_eq!(first["stage"], "solve");
    assert_eq!(first["prompt"], prompt());
    assert_eq!(first["prompt_sha256"], sha(&prompt()));
    assert_eq!(ask(&task(), vec![best()]), Value::Null);
}

#[test]
fn a_primal_and_dual_pair_with_no_gap_is_certified() {
    let (passed, report) = run(&task(), vec![best()]);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "OPTIMAL");
    assert_eq!(report["detail"], json!({"value": "14/5", "gap": "0/1"}));
    assert_eq!(outcomes(&report), four([true; 4]));
    let zeros = r#"["0/1","0/1"]"#;
    assert_eq!(
        evidence(&report, "primal_feasible"),
        &json!(sha(&format!(r#"[["8/5","6/5"],{zeros}]"#)))
    );
    assert_eq!(
        evidence(&report, "dual_feasible"),
        &json!(sha(&format!(r#"[["2/5","1/5"],{zeros}]"#)))
    );
    assert_eq!(
        evidence(&report, "zero_duality_gap"),
        &json!(sha("\"0/1\""))
    );
    assert_eq!(
        evidence(&report, "complementary_slackness"),
        &json!(sha(&format!("[{zeros},{zeros}]")))
    );
}

#[test]
fn rows_and_columns_are_not_confused_when_their_counts_differ() {
    let (passed, report) = run(&tall(), vec![pair(json!([3, 1]), json!([2, 0, 1]))]);
    assert!(passed);
    assert_eq!(report["detail"], json!({"value": "11/1", "gap": "0/1"}));
    // The slack of each row, then the reduced cost of each column.
    assert_eq!(
        evidence(&report, "complementary_slackness"),
        &json!(sha(r#"[["0/1","0/1","0/1"],["0/1","0/1"]]"#))
    );
    let (_, loose) = run(&tall(), vec![pair(json!([3, 0]), json!([3, 0, 0]))]);
    assert_eq!(loose["code"], "WEAK_DUALITY_ONLY_BOUND");
    assert_eq!(loose["detail"], json!({"gap": "3/1"}));
    assert_eq!(
        evidence(&loose, "primal_feasible"),
        &json!(sha(r#"[["3/1","0/1"],["1/1","3/1","0/1"]]"#))
    );
    assert_eq!(
        evidence(&loose, "dual_feasible"),
        &json!(sha(r#"[["3/1","0/1","0/1"],["0/1","1/1"]]"#))
    );
}

#[test]
fn a_feasible_pair_with_a_gap_is_a_bound_and_not_a_certificate() {
    // x = (2, 0) is worth 2, and y = (1, 0) bounds the optimum by 4.
    let (passed, report) = run(&task(), vec![pair(json!([2, 0]), json!([1, 0]))]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "WEAK_DUALITY_ONLY_BOUND");
    assert_eq!(report["detail"], json!({"gap": "2/1"}));
    assert_eq!(outcomes(&report), four([true, true, false, false]));
    assert_eq!(
        evidence(&report, "zero_duality_gap"),
        &json!(sha("\"2/1\""))
    );
    assert_eq!(report["every_predicate_passed"], false);
}

#[test]
fn slackness_is_checked_on_both_sides() {
    // Row 0 has room 2 and weight 1; no variable is priced above its cost where it is used.
    let (_, rows) = run(&task(), vec![pair(json!([2, 0]), json!([1, 0]))]);
    assert_eq!(
        evidence(&rows, "complementary_slackness"),
        &json!(sha(r#"[["2/1","0/1"],["0/1","1/1"]]"#))
    );
    // No row has room, and both variables are used while priced above their cost.
    let (_, columns) = run(&task(), vec![pair(json!(["8/5", "6/5"]), json!([1, 1]))]);
    assert_eq!(columns["code"], "WEAK_DUALITY_ONLY_BOUND");
    assert_eq!(columns["detail"], json!({"gap": "36/5"}));
    assert_eq!(outcomes(&columns), four([true, true, false, false]));
    assert_eq!(
        evidence(&columns, "complementary_slackness"),
        &json!(sha(r#"[["0/1","0/1"],["3/1","2/1"]]"#))
    );
}

#[test]
fn a_point_outside_the_constraints_is_refused_as_infeasible() {
    // x = (2, 2) breaks the first row by 2 and is worth more than any feasible point.
    let (passed, report) = run(&task(), vec![pair(json!([2, 2]), json!(["2/5", "1/5"]))]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "PRIMAL_FEASIBLE");
    assert_eq!(
        report["detail"],
        json!({"value": "4/1", "gap": "-6/5",
               "failed": ["primal_feasible", "zero_duality_gap", "complementary_slackness"]})
    );
    assert_eq!(outcomes(&report), four([false, true, false, false]));
    assert_eq!(
        evidence(&report, "primal_feasible"),
        &json!(sha(r#"[["2/1","2/1"],["-2/1","-2/1"]]"#))
    );
    let (_, negative) = run(&task(), vec![pair(json!([-1, 0]), json!(["2/5", "1/5"]))]);
    assert_eq!(negative["code"], "PRIMAL_FEASIBLE");
    assert_eq!(outcomes(&negative)[0], ("primal_feasible", false));
    assert_eq!(
        evidence(&negative, "primal_feasible"),
        &json!(sha(r#"[["-1/1","0/1"],["5/1","9/1"]]"#))
    );
}

#[test]
fn a_dual_outside_its_constraints_is_refused_as_infeasible() {
    // y = (0, 0) prices both variables below their cost.
    let (passed, report) = run(&task(), vec![pair(json!(["8/5", "6/5"]), json!([0, 0]))]);
    assert!(!passed);
    assert_eq!(report["code"], "DUAL_FEASIBLE");
    assert_eq!(report["detail"]["gap"], "-14/5");
    assert_eq!(outcomes(&report), four([true, false, false, false]));
    assert_eq!(
        evidence(&report, "dual_feasible"),
        &json!(sha(r#"[["0/1","0/1"],["-1/1","-1/1"]]"#))
    );
    // y = (-1, 1) prices x at 2 and y at -1, with a negative weight.
    let (_, negative) = run(&task(), vec![pair(json!(["8/5", "6/5"]), json!([-1, 1]))]);
    assert_eq!(negative["code"], "DUAL_FEASIBLE");
    assert_eq!(
        evidence(&negative, "dual_feasible"),
        &json!(sha(r#"[["-1/1","1/1"],["1/1","-2/1"]]"#))
    );
    // y = (-1, 3) prices x at 8 and y at 1, at or above their costs, with a negative weight.
    let (_, weight) = run(&task(), vec![pair(json!(["8/5", "6/5"]), json!([-1, 3]))]);
    assert_eq!(weight["code"], "DUAL_FEASIBLE");
    assert_eq!(
        evidence(&weight, "dual_feasible"),
        &json!(sha(r#"[["-1/1","3/1"],["7/1","0/1"]]"#))
    );
}

#[test]
fn a_zero_gap_alone_certifies_nothing() {
    // The origin and the zero dual agree at 0, and the zero dual is not feasible.
    let (passed, report) = run(&task(), vec![pair(json!([0, 0]), json!([0, 0]))]);
    assert!(!passed);
    assert_eq!(report["code"], "DUAL_FEASIBLE");
    assert_eq!(
        report["detail"],
        json!({"value": "0/1", "gap": "0/1", "failed": ["dual_feasible"]})
    );
    assert_eq!(outcomes(&report), four([true, false, true, true]));
}

#[test]
fn a_farkas_vector_stands_as_the_certificate_of_infeasibility() {
    // Row 0 plus row 1 reads 0 <= -1.
    let (passed, report) = run(&empty(), vec![json!({"farkas": [1, 1]})]);
    assert!(passed);
    assert_eq!(report["verdict"], "TYPED_REFUSAL");
    assert_eq!(report["code"], "PRIMAL_INFEASIBLE");
    assert_eq!(
        report["detail"],
        json!({"farkas": ["1/1", "1/1"], "by": "-1/1"})
    );
    assert_eq!(
        report["predicates"],
        json!([
            {"name": "farkas_y_nonnegative", "passed": true,
             "evidence_sha256": sha(r#"["1/1","1/1"]"#)},
            {"name": "farkas_aty_nonnegative", "passed": true,
             "evidence_sha256": sha(r#"["0/1","0/1"]"#)},
            {"name": "farkas_by_negative", "passed": true, "evidence_sha256": sha("\"-1/1\"")},
        ])
    );
    let (scaled, report) = run(&empty(), vec![json!({"farkas": ["1/2", "1/2"]})]);
    assert!(scaled);
    assert_eq!(
        report["detail"],
        json!({"farkas": ["1/2", "1/2"], "by": "-1/2"})
    );
}

#[test]
fn each_farkas_condition_is_checked() {
    let farkas = |y: Value| run(&empty(), vec![json!({ "farkas": y })]);
    // Negative weights: the combination is not a consequence of the rows.
    let (passed, negative) = farkas(json!([-1, -1]));
    assert!(!passed);
    assert_eq!(negative["verdict"], "REFUSED");
    assert_eq!(negative["code"], "FARKAS_Y_NONNEGATIVE");
    assert_eq!(
        negative["detail"],
        json!({"failed": ["farkas_y_nonnegative", "farkas_by_negative"]})
    );
    // (1, 2) leaves -x - y on the left, which is not bounded below by zero.
    let (_, left) = farkas(json!([1, 2]));
    assert_eq!(left["code"], "FARKAS_ATY_NONNEGATIVE");
    assert_eq!(
        left["detail"],
        json!({"failed": ["farkas_aty_nonnegative"]})
    );
    assert_eq!(
        evidence(&left, "farkas_aty_nonnegative"),
        &json!(sha(r#"["-1/1","-1/1"]"#))
    );
    assert_eq!(
        evidence(&left, "farkas_by_negative"),
        &json!(sha("\"-3/1\""))
    );
    // (2, 1) reads x + y <= 0, which the origin satisfies.
    let (_, level) = farkas(json!([2, 1]));
    assert_eq!(level["code"], "FARKAS_BY_NEGATIVE");
    assert_eq!(level["detail"], json!({"failed": ["farkas_by_negative"]}));
    assert_eq!(
        outcomes(&level),
        [
            ("farkas_y_nonnegative", true),
            ("farkas_aty_nonnegative", true),
            ("farkas_by_negative", false)
        ]
    );
    assert_eq!(
        evidence(&level, "farkas_aty_nonnegative"),
        &json!(sha(r#"["1/1","1/1"]"#))
    );
    assert_eq!(
        evidence(&level, "farkas_by_negative"),
        &json!(sha("\"0/1\""))
    );
}

#[test]
fn a_feasible_programme_has_no_farkas_vector() {
    for y in [json!([0, 0]), json!([1, 0]), json!([1, 1])] {
        let (passed, report) = run(&task(), vec![json!({ "farkas": y })]);
        assert!(!passed, "{y}");
        assert_eq!(report["code"], "FARKAS_BY_NEGATIVE");
    }
}

#[test]
fn a_farkas_vector_is_read_before_a_pair() {
    let mut reply = best();
    reply["farkas"] = json!([0, 0]);
    let (passed, report) = run(&task(), vec![reply]);
    assert!(!passed);
    assert_eq!(report["code"], "FARKAS_BY_NEGATIVE");
    assert_eq!(outcomes(&report).len(), 3);
}

#[test]
fn a_reply_without_a_certificate_is_malformed() {
    let either = "reply must carry x and y, or a farkas vector";
    assert_eq!(malformed(&task(), vec![json!({})]), either);
    assert_eq!(
        malformed(&task(), vec![json!({"x": ["8/5", "6/5"]})]),
        either
    );
    assert_eq!(
        malformed(&task(), vec![json!({"y": ["2/5", "1/5"]})]),
        either
    );
    assert_eq!(malformed(&task(), vec![json!({"value": "14/5"})]), either);
    let object = "reply must be an object";
    assert_eq!(malformed(&task(), vec![json!("optimal at 14/5")]), object);
    assert_eq!(
        malformed(&task(), vec![json!([["8/5", "6/5"], ["2/5", "1/5"]])]),
        object
    );
}

#[test]
fn a_vector_of_the_wrong_length_or_kind_is_malformed() {
    let x = "x must be 2 exact rationals";
    assert_eq!(malformed(&task(), vec![pair(json!([1]), json!([1, 1]))]), x);
    assert_eq!(
        malformed(&task(), vec![pair(json!([1, 1, 1]), json!([1, 1]))]),
        x
    );
    assert_eq!(
        malformed(&task(), vec![pair(json!([1.6, 1.2]), json!([1, 1]))]),
        x
    );
    assert_eq!(
        malformed(&task(), vec![pair(json!("origin"), json!([1, 1]))]),
        x
    );
    // Both are unreadable: the point is named first.
    assert_eq!(malformed(&task(), vec![pair(json!([1]), json!([1]))]), x);
    let y = "y must be 2 exact rationals";
    assert_eq!(malformed(&task(), vec![pair(json!([1, 1]), json!([1]))]), y);
    assert_eq!(
        malformed(&task(), vec![pair(json!([1, 1]), json!([1, "a"]))]),
        y
    );
    // One entry per column for the point and one per row for the weights.
    assert_eq!(
        malformed(&tall(), vec![pair(json!([3, 1, 0]), json!([2, 0, 1]))]),
        x
    );
    assert_eq!(
        malformed(&tall(), vec![pair(json!([3, 1]), json!([2, 0]))]),
        "y must be 3 exact rationals"
    );
    assert_eq!(
        malformed(&tall(), vec![json!({"farkas": [1, 1]})]),
        "farkas must be 3 exact rationals"
    );
    assert_eq!(
        malformed(&empty(), vec![json!({"farkas": null})]),
        "farkas must be 2 exact rationals"
    );
    let (_, report) = run(&task(), vec![pair(json!([1]), json!([1, 1]))]);
    assert_eq!(report["predicates"], json!([]));
}

#[test]
fn a_missing_reply_is_refused() {
    let outcome = judge(&request(&task(), &[None]));
    let Outcome::Fail { result } = outcome else {
        panic!("expected a failed run, got {outcome:?}");
    };
    assert_eq!(result["verdict"], "REFUSED");
    assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
}

#[test]
fn a_task_the_host_cannot_read_is_refused_before_anything_is_asked() {
    let lists = "A, b and c must be lists";
    assert_eq!(bad_task(json!({"b": [1], "c": [1]})), lists);
    assert_eq!(bad_task(json!({"A": [[1]], "c": [1]})), lists);
    assert_eq!(bad_task(json!({"A": [[1]], "b": [1]})), lists);
    assert_eq!(bad_task(json!({"A": [[1]], "b": 1, "c": [1]})), lists);
    let empty = "A needs at least one row and c at least one entry";
    assert_eq!(bad_task(json!({"A": [], "b": [], "c": [1]})), empty);
    assert_eq!(bad_task(json!({"A": [[]], "b": [1], "c": []})), empty);
    let shape = "A needs one row per entry of b and one column per entry of c";
    assert_eq!(
        bad_task(json!({"A": [[1, 2]], "b": [1, 2], "c": [1, 1]})),
        shape
    );
    assert_eq!(
        bad_task(json!({"A": [[1, 2], [3]], "b": [1, 2], "c": [1, 1]})),
        shape
    );
    assert_eq!(
        bad_task(json!({"A": [[1, 2], [3, 4]], "b": [1, 2], "c": [1]})),
        shape
    );
    assert_eq!(bad_task(json!({"A": [7], "b": [1], "c": [1]})), shape);
    let exact = "A, b and c must hold exact rationals";
    assert_eq!(bad_task(json!({"A": [[0.5]], "b": [1], "c": [1]})), exact);
    assert_eq!(bad_task(json!({"A": [[1]], "b": [0.5], "c": [1]})), exact);
    assert_eq!(bad_task(json!({"A": [[1]], "b": [1], "c": ["x"]})), exact);
    assert_eq!(
        ask(&json!({"A": [["1/2"]], "b": ["-1/3"], "c": [0]}), vec![])["stage"],
        "solve"
    );
}
