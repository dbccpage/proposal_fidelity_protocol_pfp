//! WF30, constraint-forcing anti-recitation: forced prefix, forbidden comparators, the size
//! bound, and sorting by the 0-1 principle.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf30-tests:v1

use pfp_operads::families::wf30::{apply, unsorted_inputs, FAMILY, MAX_WIRES, MIN_WIRES};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

fn task() -> Value {
    json!({"statement": "Give a 4-wire sorting network whose first comparator is [0, 3], without [0, 2].",
           "n": 4, "forced_prefix": [[0, 3]], "forbidden": [[0, 2]], "max_comparators": 6})
}

fn good() -> Value {
    json!([[0, 3], [1, 2], [0, 1], [2, 3], [1, 2]])
}

fn run(task: Value, content: Value) -> (bool, Value) {
    let request = json!({"workflow": "WF30", "task": task, "replies": [{"content": content}]});
    match judge(&request.to_string()) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn network(task: Value, network: Value) -> (bool, Value) {
    run(task, json!({ "network": network }))
}

fn predicate(report: &Value, name: &str) -> Value {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .find(|row| row["name"] == name)
        .unwrap_or_else(|| panic!("no predicate {name}"))
        .clone()
}

fn bad_task(task: Value) -> String {
    match next(&json!({"workflow": "WF30", "task": task}).to_string()) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

fn malformed(content: Value) -> String {
    let (passed, report) = run(task(), content);
    assert!(!passed);
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    assert_eq!(report["predicates"], json!([]));
    report["detail"]["reason"]
        .as_str()
        .expect("reason")
        .to_owned()
}

#[test]
fn the_family_is_registered_under_its_names() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF30",
            "Constraint-forcing anti-recitation",
            "comparator_network_zero_one_principle"
        )
    );
    assert_eq!((MIN_WIRES, MAX_WIRES), (2, 10));
}

#[test]
fn a_network_that_keeps_the_constraints_and_sorts_is_certified() {
    let (passed, report) = network(task(), good());
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "CERTIFIED");
    assert_eq!(
        report["detail"],
        json!({"comparators": 5, "binary_failures": 0})
    );
    let written = "[[0,3],[1,2],[0,1],[2,3],[1,2]]";
    assert_eq!(
        report["predicates"],
        json!([
            {"name": "forced_prefix_kept", "passed": true, "evidence_sha256": sha(written)},
            {"name": "no_forbidden_comparator", "passed": true, "evidence_sha256": sha(written)},
            {"name": "within_size_bound", "passed": true, "evidence_sha256": sha("5")},
            {"name": "sorts_all_binary_inputs", "passed": true, "evidence_sha256": sha("[]")},
        ])
    );
    assert_eq!(report["asked"].as_array().map(Vec::len), Some(1));
    assert_eq!(report["asked"][0]["stage"], "solve");
}

#[test]
fn the_recited_textbook_network_breaks_the_constraints_although_it_sorts() {
    let (passed, report) = network(task(), json!([[0, 1], [2, 3], [0, 2], [1, 3], [1, 2]]));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "FORCED_PREFIX_KEPT");
    assert_eq!(
        report["detail"],
        json!({"comparators": 5, "binary_failures": 0,
               "failed": ["forced_prefix_kept", "no_forbidden_comparator"]})
    );
    assert_eq!(
        predicate(&report, "sorts_all_binary_inputs")["passed"],
        true
    );
    assert_eq!(predicate(&report, "within_size_bound")["passed"], true);
}

#[test]
fn a_network_that_keeps_the_prefix_but_does_not_sort_is_refused() {
    let (passed, report) = network(task(), json!([[0, 3], [1, 2]]));
    assert!(!passed);
    assert_eq!(report["code"], "SORTS_ALL_BINARY_INPUTS");
    assert_eq!(
        report["detail"],
        json!({"comparators": 2, "binary_failures": 6, "failed": ["sorts_all_binary_inputs"]})
    );
    assert_eq!(
        predicate(&report, "sorts_all_binary_inputs"),
        json!({"name": "sorts_all_binary_inputs", "passed": false, "evidence_sha256": sha("[0,0,1,0]")})
    );
}

#[test]
fn the_forced_prefix_must_be_the_start_of_the_network() {
    let free = json!({"n": 2, "forced_prefix": [[0, 1], [0, 1]]});
    assert!(network(free.clone(), json!([[0, 1], [0, 1]])).0);
    assert!(network(free.clone(), json!([[0, 1], [0, 1], [0, 1]])).0);
    let (passed, report) = network(free.clone(), json!([[0, 1]]));
    assert!(!passed);
    assert_eq!(report["code"], "FORCED_PREFIX_KEPT");
    assert_eq!(report["detail"]["binary_failures"], 0);
    let three = json!({"n": 3, "forced_prefix": [[1, 2]]});
    let (_, report) = network(three, json!([[0, 1], [1, 2], [0, 1]]));
    assert_eq!(report["code"], "FORCED_PREFIX_KEPT");
}

#[test]
fn a_forbidden_comparator_anywhere_in_the_network_is_refused() {
    let task = json!({"n": 3, "forbidden": [[0, 2], [1, 2]]});
    let (passed, report) = network(task.clone(), json!([[0, 1], [1, 2], [0, 1]]));
    assert!(!passed);
    assert_eq!(report["code"], "NO_FORBIDDEN_COMPARATOR");
    assert_eq!(
        report["detail"]["failed"],
        json!(["no_forbidden_comparator"])
    );
    let (passed, _) = network(
        json!({"n": 3, "forbidden": [[0, 2]]}),
        json!([[0, 1], [1, 2], [0, 1]]),
    );
    assert!(passed);
}

#[test]
fn the_size_bound_admits_exactly_that_many_comparators() {
    let bounded = |bound: u64| json!({"n": 2, "max_comparators": bound});
    assert!(network(bounded(2), json!([[0, 1], [0, 1]])).0);
    assert!(network(bounded(3), json!([[0, 1], [0, 1]])).0);
    let (passed, report) = network(bounded(1), json!([[0, 1], [0, 1]]));
    assert!(!passed);
    assert_eq!(report["code"], "WITHIN_SIZE_BOUND");
    assert_eq!(
        predicate(&report, "within_size_bound"),
        json!({"name": "within_size_bound", "passed": false, "evidence_sha256": sha("2")})
    );
    let (passed, report) = network(bounded(0), json!([]));
    assert!(!passed);
    assert_eq!(report["code"], "SORTS_ALL_BINARY_INPUTS");
    assert_eq!(predicate(&report, "within_size_bound")["passed"], true);
    assert!(network(json!({"n": 2}), json!([[0, 1], [0, 1], [0, 1], [0, 1]])).0);
}

#[test]
fn the_empty_network_leaves_every_unsorted_input_unsorted() {
    let (_, report) = network(json!({"n": 2}), json!([]));
    assert_eq!(
        report["detail"],
        json!({"comparators": 0, "binary_failures": 1,
                                       "failed": ["sorts_all_binary_inputs"]})
    );
    assert_eq!(
        predicate(&report, "sorts_all_binary_inputs")["evidence_sha256"],
        sha("[1,0]")
    );
    let (_, report) = network(json!({"n": 10}), json!([]));
    assert_eq!(report["detail"]["binary_failures"], 1013);
}

#[test]
fn the_network_runs_its_comparators_in_order() {
    assert_eq!(apply(&[(0, 1)], &[1, 0]), vec![0, 1]);
    assert_eq!(apply(&[(0, 1)], &[0, 1]), vec![0, 1]);
    assert_eq!(apply(&[(0, 1)], &[1, 1]), vec![1, 1]);
    assert_eq!(apply(&[], &[1, 0]), vec![1, 0]);
    assert_eq!(apply(&[(0, 2), (0, 1)], &[1, 1, 0]), vec![0, 1, 1]);
    assert_eq!(apply(&[(0, 1), (0, 2)], &[1, 0, 0]), vec![0, 1, 0]);
    assert_eq!(apply(&[(0, 1)], &[3, 2]), vec![2, 3]);
    assert_eq!(apply(&[(0, 2), (2, 0), (0, 1)], &[1, 0]), vec![0, 1]);
    assert_eq!(apply(&[(5, 6)], &[1, 0]), vec![1, 0]);
}

#[test]
fn unsorted_inputs_come_in_counting_order_with_the_first_wire_most_significant() {
    assert_eq!(
        unsorted_inputs(&[], 3),
        vec![vec![0, 1, 0], vec![1, 0, 0], vec![1, 0, 1], vec![1, 1, 0]]
    );
    assert_eq!(
        unsorted_inputs(&[(0, 1)], 3),
        vec![vec![0, 1, 0], vec![1, 0, 0], vec![1, 1, 0]]
    );
    assert_eq!(
        unsorted_inputs(&[(0, 1), (1, 2), (0, 1)], 3),
        Vec::<Vec<u8>>::new()
    );
    assert_eq!(unsorted_inputs(&[], 1), Vec::<Vec<u8>>::new());
    assert_eq!(unsorted_inputs(&[], 2), vec![vec![1, 0]]);
}

#[test]
fn a_reply_without_a_network_list_is_malformed() {
    let reason = "the reply must be an object with a network list";
    assert_eq!(malformed(json!({})), reason);
    assert_eq!(malformed(json!({"network": "x"})), reason);
    assert_eq!(malformed(json!({"network": {"0": [0, 1]}})), reason);
    assert_eq!(malformed(json!([[0, 1]])), reason);
    assert_eq!(malformed(json!(null)), reason);
}

#[test]
fn a_comparator_that_is_not_an_ordered_pair_of_wires_is_malformed() {
    let pair = "a comparator is a pair [i, j]";
    assert_eq!(malformed(json!({"network": [[0]]})), pair);
    assert_eq!(malformed(json!({"network": [[0, 1, 2]]})), pair);
    assert_eq!(malformed(json!({"network": [[0, 3], 5]})), pair);
    assert_eq!(malformed(json!({"network": [[]]})), pair);
    let order = "a comparator must satisfy 0 <= i < j < n";
    assert_eq!(malformed(json!({"network": [[1, 0]]})), order);
    assert_eq!(malformed(json!({"network": [[1, 1]]})), order);
    assert_eq!(malformed(json!({"network": [[0, 4]]})), order);
    assert_eq!(malformed(json!({"network": [[-1, 2]]})), order);
    assert_eq!(malformed(json!({"network": [[0, 1.0]]})), order);
    assert_eq!(malformed(json!({"network": [[0, "1"]]})), order);
    assert_eq!(malformed(json!({"network": [[true, 1]]})), order);
    assert_eq!(
        malformed(json!({"network": [[0, 3], [0, 1], [2, 4]]})),
        order
    );
}

#[test]
fn the_highest_wire_is_a_valid_end_of_a_comparator() {
    let (passed, report) = network(json!({"n": 4}), json!([[0, 3], [2, 3]]));
    assert!(!passed);
    assert_eq!(report["code"], "SORTS_ALL_BINARY_INPUTS");
}

#[test]
fn a_missing_reply_is_refused_without_a_predicate() {
    let request = json!({"workflow": "WF30", "task": task(), "replies": [null]});
    match judge(&request.to_string()) {
        Outcome::Fail { result } => {
            assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
            assert_eq!(result["predicates"], json!([]));
        }
        other => panic!("expected FAIL, got {other:?}"),
    }
}

#[test]
fn the_number_of_wires_is_an_exact_integer_from_two_to_ten() {
    let wires = "n must be an exact integer from 2 to 10";
    assert_eq!(bad_task(json!({})), wires);
    assert_eq!(bad_task(json!({"n": 1})), wires);
    assert_eq!(bad_task(json!({"n": 11})), wires);
    assert_eq!(bad_task(json!({"n": 0})), wires);
    assert_eq!(bad_task(json!({"n": -4})), wires);
    assert_eq!(bad_task(json!({"n": 4.0})), wires);
    assert_eq!(bad_task(json!({"n": "4"})), wires);
    assert_eq!(bad_task(json!({"n": true})), wires);
    for wires in [2, 10] {
        let request = json!({"workflow": "WF30", "task": {"n": wires}}).to_string();
        assert!(matches!(next(&request), Outcome::Pass { .. }));
    }
}

#[test]
fn the_task_s_own_comparators_and_bound_are_read_strictly() {
    assert_eq!(
        bad_task(json!({"n": 4, "forced_prefix": 3})),
        "forced_prefix must be a list of comparators"
    );
    assert_eq!(
        bad_task(json!({"n": 4, "forbidden": {"a": 1}})),
        "forbidden must be a list of comparators"
    );
    assert_eq!(
        bad_task(json!({"n": 4, "forced_prefix": [[0, 4]]})),
        "a comparator must satisfy 0 <= i < j < n"
    );
    assert_eq!(
        bad_task(json!({"n": 4, "forbidden": [[2]]})),
        "a comparator is a pair [i, j]"
    );
    let bound = "max_comparators must be an exact integer, zero or more";
    assert_eq!(bad_task(json!({"n": 4, "max_comparators": -1})), bound);
    assert_eq!(bad_task(json!({"n": 4, "max_comparators": 2.5})), bound);
    assert_eq!(bad_task(json!({"n": 4, "max_comparators": "6"})), bound);
    assert_eq!(bad_task(json!({"n": 4, "max_comparators": null})), bound);
}
