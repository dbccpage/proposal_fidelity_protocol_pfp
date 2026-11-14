//! WF38, diagnostic-trace proposal selection: the defect the host recomputes for each
//! candidate, the ranking by defect, size and name, and what a candidate says of itself.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf38-tests:v1

use pfp_operads::families::wf38::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const STATEMENT: &str = "Propose corrections to the edge values and let the host rank them.";

/// Two triangles that share the edge 2. With 1 on every edge the cycle 0-1-2 sums to 3 and
/// the cycle 2-3-0 less the shared edge to 1, so the defect is 4.
fn task() -> Value {
    json!({"statement": STATEMENT,
           "edges": [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]],
           "labels": [1, 1, 1, 1, 1]})
}

fn prompt() -> String {
    format!(
        "WF38 Diagnostic-trace proposal selection. {STATEMENT}\n{}",
        r#"{"edges":[[0,1],[1,2],[2,0],[2,3],[3,0]],"labels":[1,1,1,1,1]}"#
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
    json!({"workflow": "WF38", "task": task, "replies": replies}).to_string()
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

fn candidate(name: &str, delta: Value) -> Value {
    json!({"name": name, "delta": delta})
}

fn reply(candidates: Vec<Value>) -> Value {
    json!({ "candidates": candidates })
}

/// Clears the first cycle and leaves the second: defect 1, size 3.
fn first_only(name: &str) -> Value {
    candidate(name, json!([[1, -3]]))
}

/// Clears both cycles on their own edges: defect 0, size 4.
fn both(name: &str) -> Value {
    candidate(name, json!([[1, -3], [3, -1]]))
}

/// Lowers the shared edge, which moves the two cycle sums opposite ways: defect 4, size 1.
fn shared(name: &str) -> Value {
    candidate(name, json!([[2, -1]]))
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF38",
            "Diagnostic-trace proposal selection",
            "host_recomputed_defect_ranking"
        )
    );
}

#[test]
fn the_one_question_is_the_task_as_written() {
    let first = ask(&task(), vec![]);
    assert_eq!(first["stage"], "solve");
    assert_eq!(first["prompt"], prompt());
    assert_eq!(first["prompt_sha256"], sha(&prompt()));
    assert_eq!(ask(&task(), vec![reply(vec![])]), Value::Null);
}

#[test]
fn the_candidate_that_leaves_the_least_defect_is_selected() {
    let (passed, report) = run(
        &task(),
        vec![reply(vec![first_only("a"), shared("b"), both("c")])],
    );
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "SELECTED");
    let scores = json!({"a": ["1/1", "3/1"], "b": ["4/1", "1/1"], "c": ["0/1", "4/1"]});
    assert_eq!(
        report["detail"],
        json!({"winner": "c", "phi0": "4/1", "phi": "0/1", "scores": scores,
               "ranking": ["c", "a"]})
    );
    let evidence = r#"["4/1",{"a":["1/1","3/1"],"b":["4/1","1/1"],"c":["0/1","4/1"]}]"#;
    assert_eq!(
        report["predicates"],
        json!([{"name": "strict_defect_decrease_exists", "passed": true,
                "evidence_sha256": sha(evidence)}])
    );
}

#[test]
fn only_a_strict_decrease_is_ranked() {
    let unchanged = candidate("unchanged", json!([]));
    let worse = candidate("worse", json!([[1, 1]]));
    let (passed, report) = run(
        &task(),
        vec![reply(vec![
            unchanged,
            worse,
            shared("shared"),
            first_only("better"),
        ])],
    );
    assert!(passed);
    assert_eq!(report["detail"]["winner"], "better");
    assert_eq!(report["detail"]["phi"], "1/1");
    assert_eq!(report["detail"]["ranking"], json!(["better"]));
    assert_eq!(
        report["detail"]["scores"],
        json!({"better": ["1/1", "3/1"], "shared": ["4/1", "1/1"],
               "unchanged": ["4/1", "0/1"], "worse": ["5/1", "1/1"]})
    );
}

#[test]
fn equal_defects_are_ranked_by_the_size_of_the_correction_then_by_name() {
    // The same repair written wastefully: defect 0, size 6.
    let wasteful = candidate("a", json!([[1, -1], [1, -2], [3, -1], [3, 1], [3, -1]]));
    // Another repair of the same size as `both`, on the outer edges 0 and 4.
    let outer = candidate("m", json!([[0, -3], [4, -1]]));
    let halves = candidate("k", json!([[1, "-3/2"], [1, "-3/2"], [3, -1]]));
    let (passed, report) = run(
        &task(),
        vec![reply(vec![
            wasteful,
            both("z"),
            outer,
            halves,
            first_only("b"),
        ])],
    );
    assert!(passed);
    assert_eq!(report["detail"]["winner"], "k");
    assert_eq!(
        report["detail"]["ranking"],
        json!(["k", "m", "z", "a", "b"])
    );
    assert_eq!(report["detail"]["scores"]["a"], json!(["0/1", "6/1"]));
    assert_eq!(report["detail"]["scores"]["k"], json!(["0/1", "4/1"]));
    assert_eq!(report["detail"]["scores"]["m"], json!(["0/1", "4/1"]));
}

#[test]
fn a_smaller_defect_outranks_a_smaller_correction() {
    let (_, report) = run(&task(), vec![reply(vec![first_only("a"), both("b")])]);
    assert_eq!(report["detail"]["ranking"], json!(["b", "a"]));
    // A half step on the first cycle: defect 5/2, size 3/2.
    let half = candidate("a", json!([[0, "-3/2"]]));
    let (_, report) = run(&task(), vec![reply(vec![half, first_only("b")])]);
    assert_eq!(report["detail"]["ranking"], json!(["b", "a"]));
    assert_eq!(report["detail"]["scores"]["a"], json!(["5/2", "3/2"]));
    assert_eq!(report["detail"]["phi"], "1/1");
}

#[test]
fn what_a_candidate_says_of_itself_is_not_read() {
    let mut boastful = shared("a");
    boastful["phi"] = json!("0/1");
    boastful["score"] = json!(100);
    boastful["size"] = json!(0);
    let (passed, report) = run(
        &task(),
        vec![reply(vec![boastful.clone(), first_only("b")])],
    );
    assert!(passed);
    assert_eq!(report["detail"]["winner"], "b");
    assert_eq!(report["detail"]["scores"]["a"], json!(["4/1", "1/1"]));
    let (alone, report) = run(&task(), vec![reply(vec![boastful])]);
    assert!(!alone);
    assert_eq!(report["code"], "NO_STRICT_DECREASE");
}

#[test]
fn no_strict_decrease_is_refused_with_every_score() {
    let (passed, report) = run(
        &task(),
        vec![reply(vec![shared("a"), candidate("b", json!([]))])],
    );
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "NO_STRICT_DECREASE");
    assert_eq!(
        report["detail"],
        json!({"phi0": "4/1", "scores": {"a": ["4/1", "1/1"], "b": ["4/1", "0/1"]}})
    );
    assert_eq!(
        outcomes(&report),
        [("strict_defect_decrease_exists", false)]
    );
    assert_eq!(
        evidence(&report, "strict_defect_decrease_exists"),
        &json!(sha(r#"["4/1",{"a":["4/1","1/1"],"b":["4/1","0/1"]}]"#))
    );
    let (none, report) = run(&task(), vec![reply(vec![])]);
    assert!(!none);
    assert_eq!(report["code"], "NO_STRICT_DECREASE");
    assert_eq!(report["detail"], json!({"phi0": "4/1", "scores": {}}));
}

#[test]
fn nothing_lowers_the_defect_of_a_coboundary() {
    let mut exact = task();
    exact["labels"] = json!([1, 1, -2, -3, 1]);
    let (passed, report) = run(
        &exact,
        vec![reply(vec![both("a"), candidate("b", json!([]))])],
    );
    assert!(!passed);
    assert_eq!(report["code"], "NO_STRICT_DECREASE");
    assert_eq!(report["detail"]["phi0"], "0/1");
    assert_eq!(report["detail"]["scores"]["b"], json!(["0/1", "0/1"]));
    assert_eq!(report["detail"]["scores"]["a"], json!(["4/1", "4/1"]));
}

#[test]
fn a_candidate_list_the_host_cannot_read_is_malformed() {
    let list = "candidates must be a list";
    assert_eq!(malformed(&task(), vec![json!({})]), list);
    assert_eq!(
        malformed(&task(), vec![json!({"candidates": {"a": []}})]),
        list
    );
    assert_eq!(malformed(&task(), vec![json!("candidate a")]), list);
    assert_eq!(malformed(&task(), vec![json!([first_only("a")])]), list);
    let name = "every candidate needs a text name";
    assert_eq!(
        malformed(&task(), vec![reply(vec![json!({"delta": []})])]),
        name
    );
    assert_eq!(
        malformed(&task(), vec![reply(vec![json!({"name": 7, "delta": []})])]),
        name
    );
    assert_eq!(malformed(&task(), vec![reply(vec![json!("a")])]), name);
    let delta = "every candidate needs a delta list";
    assert_eq!(
        malformed(&task(), vec![reply(vec![json!({"name": "a"})])]),
        delta
    );
    assert_eq!(
        malformed(&task(), vec![reply(vec![candidate("a", json!({"1": -3}))])]),
        delta
    );
    // A later candidate is read as closely as the first.
    assert_eq!(
        malformed(&task(), vec![reply(vec![both("a"), json!({"name": "b"})])]),
        delta
    );
    let (_, report) = run(&task(), vec![json!({})]);
    assert_eq!(report["predicates"], json!([]));
}

#[test]
fn candidate_names_are_distinct() {
    let distinct = "candidate names must be distinct";
    assert_eq!(
        malformed(&task(), vec![reply(vec![both("a"), first_only("a")])]),
        distinct
    );
    assert_eq!(
        malformed(
            &task(),
            vec![reply(vec![both("a"), shared("b"), both("a")])]
        ),
        distinct
    );
    // The second candidate's own corrections are read before its name is compared.
    assert_eq!(
        malformed(
            &task(),
            vec![reply(vec![both("a"), candidate("a", json!([[9, 1]]))])]
        ),
        "edge index out of range"
    );
}

#[test]
fn each_correction_is_an_edge_in_range_and_an_exact_rational() {
    let delta = |delta: Value| malformed(&task(), vec![reply(vec![candidate("a", delta)])]);
    let entry = "delta entries are [edge, value]";
    assert_eq!(delta(json!([1, -3])), entry);
    assert_eq!(delta(json!([[1]])), entry);
    assert_eq!(delta(json!([[1, -3, 0]])), entry);
    assert_eq!(delta(json!([{"edge": 1, "value": -3}])), entry);
    let value = "delta value must be an exact rational";
    assert_eq!(delta(json!([[1, -3.0]])), value);
    assert_eq!(delta(json!([[1, "three"]])), value);
    // The value is read before the edge.
    assert_eq!(delta(json!([["one", 0.5]])), value);
    let edge = "delta edge must be an exact int";
    assert_eq!(delta(json!([["1", -3]])), edge);
    assert_eq!(delta(json!([[1.0, -3]])), edge);
    let range = "edge index out of range";
    assert_eq!(delta(json!([[5, -3]])), range);
    assert_eq!(delta(json!([[-1, -3]])), range);
    // A good correction does not excuse the one after it.
    assert_eq!(delta(json!([[1, -3], [5, 1]])), range);
    let (passed, _) = run(&task(), vec![reply(vec![candidate("a", json!([[4, -1]]))])]);
    assert!(passed);
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
    assert_eq!(
        bad_task(json!({"edges": "kite", "labels": []})),
        "edges must be a nonempty list of pairs of exact integers"
    );
    assert_eq!(
        bad_task(json!({"edges": [[0, 3]], "labels": [1]})),
        "vertices must be 0..n-1"
    );
    assert_eq!(
        bad_task(json!({"edges": [[0, 1]], "labels": ["one"]})),
        "labels must be one exact rational per edge"
    );
}
