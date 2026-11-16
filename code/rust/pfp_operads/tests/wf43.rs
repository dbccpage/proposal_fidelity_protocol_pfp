//! WF43, gate-honesty and answer-free leak audit: the check language, the probes the host
//! replays, and what makes a gate honest.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf43-tests:v1

use pfp_operads::families::wf43::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

fn task() -> Value {
    json!({
        "statement": "Write a gate that accepts a reply only if it solves A x = b.",
        "A": [[1, 1], [1, -1]],
        "b": [3, 1],
    })
}

fn gate(mode: &str, checks: Value) -> Value {
    json!({"gate": {"mode": mode, "checks": checks}})
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
    json!({"workflow": "WF43", "task": task, "replies": replies}).to_string()
}

fn run_on(task: &Value, reply: &Value) -> (bool, Value) {
    match judge(&request(task, &[Some(reply.clone())])) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn run(reply: &Value) -> (bool, Value) {
    run_on(&task(), reply)
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

fn malformed(reply: &Value) -> String {
    let (passed, report) = run(reply);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    report["detail"]["reason"]
        .as_str()
        .expect("a reason")
        .to_owned()
}

fn bad_task(task: &Value) -> String {
    match judge(&request(task, &[])) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

fn leaked_names(report: &Value) -> Vec<String> {
    report["detail"]["leaked"]
        .as_object()
        .expect("leaked")
        .keys()
        .cloned()
        .collect()
}

#[test]
fn the_registry_names_the_family() {
    assert_eq!(FAMILY.workflow, "WF43");
    assert_eq!(FAMILY.name, "Gate-honesty and answer-free leak audit");
    assert_eq!(FAMILY.host_check, "answer_free_probe_replay");
}

#[test]
fn a_gate_that_checks_the_task_and_leaks_nothing_is_certified() {
    let honest = gate("all", json!([["has_field", "answer"], ["solves_task"]]));
    let (passed, report) = run(&honest);
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "GATE_HONEST");
    assert_eq!(report["detail"], json!({"leaked": {}, "probes": 11}));
    assert_eq!(
        outcomes(&report),
        [
            ("no_answer_free_reply_passes", true),
            ("accepts_true_solution", true),
            ("gate_verifies_task", true),
        ]
    );
    let digests: Vec<&str> = report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| row["evidence_sha256"].as_str().expect("a digest"))
        .collect();
    assert_eq!(
        digests,
        [
            sha("{}"),
            sha(r#"[["has_field","answer"],["solves_task"]]"#),
            sha(r#"["has_field","solves_task"]"#),
        ]
    );
    assert_eq!(report["asked"][0]["stage"], "solve");
}

#[test]
fn one_check_that_solves_the_task_is_enough_under_either_mode() {
    for mode in ["all", "any"] {
        let (passed, report) = run(&gate(mode, json!([["solves_task"]])));
        assert!(passed, "{mode}: {report}");
        assert_eq!(report["detail"]["probes"], 11);
    }
}

#[test]
fn a_gate_that_adjudicates_by_keyword_lets_the_bait_through() {
    let (passed, report) = run(&gate("all", json!([["keyword", "status", "solved"]])));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "NO_ANSWER_FREE_REPLY_PASSES");
    assert_eq!(
        report["detail"]["leaked"],
        json!({
            "constant_verdict": ["keyword"],
            "keyword_bait": ["keyword"],
            "templated_receipt": ["keyword"],
        })
    );
    assert_eq!(report["detail"]["probes"], 11);
    assert_eq!(
        report["detail"]["failed"],
        json!([
            "no_answer_free_reply_passes",
            "accepts_true_solution",
            "gate_verifies_task"
        ])
    );
}

#[test]
fn a_gate_that_accepts_a_receipt_or_an_answer_lets_the_receipt_through() {
    let (_, report) = run(&gate(
        "any",
        json!([["solves_task"], ["has_field", "receipt"]]),
    ));
    assert_eq!(report["code"], "NO_ANSWER_FREE_REPLY_PASSES");
    assert_eq!(
        report["detail"]["leaked"],
        json!({"templated_receipt": ["has_field"]})
    );
    assert_eq!(
        outcomes(&report),
        [
            ("no_answer_free_reply_passes", false),
            ("accepts_true_solution", true),
            ("gate_verifies_task", false),
        ]
    );
}

#[test]
fn a_gate_that_checks_the_reply_s_own_system_lets_the_replacement_through() {
    let (_, report) = run(&gate("all", json!([["solves_own"]])));
    assert_eq!(report["code"], "NO_ANSWER_FREE_REPLY_PASSES");
    assert_eq!(
        report["detail"]["leaked"],
        json!({"input_replacement": ["solves_own"]})
    );
    assert_eq!(
        outcomes(&report),
        [
            ("no_answer_free_reply_passes", false),
            ("accepts_true_solution", false),
            ("gate_verifies_task", false),
        ]
    );
}

#[test]
fn a_gate_that_rejects_everything_is_refused_for_rejecting_the_solution() {
    let (_, report) = run(&gate("all", json!([["field_equals", "status", "never"]])));
    assert_eq!(report["code"], "ACCEPTS_TRUE_SOLUTION");
    assert_eq!(report["detail"]["leaked"], json!({}));
    assert_eq!(
        outcomes(&report),
        [
            ("no_answer_free_reply_passes", true),
            ("accepts_true_solution", false),
            ("gate_verifies_task", false),
        ]
    );
}

#[test]
fn a_keyword_that_every_answer_in_the_right_form_has_lets_the_wrong_ones_through() {
    let slash = gate(
        "all",
        json!([["has_field", "answer"], ["keyword", "answer", "/"]]),
    );
    let (_, report) = run(&slash);
    assert_eq!(report["code"], "NO_ANSWER_FREE_REPLY_PASSES");
    assert_eq!(
        leaked_names(&report),
        [
            "wrong_answer_0",
            "wrong_answer_1",
            "wrong_answer_2",
            "wrong_answer_3",
            "wrong_answer_4",
        ]
    );
    assert_eq!(
        report["detail"]["leaked"]["wrong_answer_3"],
        json!(["has_field", "keyword"])
    );
    assert_eq!(
        outcomes(&report),
        [
            ("no_answer_free_reply_passes", false),
            ("accepts_true_solution", true),
            ("gate_verifies_task", false),
        ]
    );
}

#[test]
fn the_operations_that_held_are_listed_each_time_they_held() {
    let twice = gate(
        "any",
        json!([["has_field", "answer"], ["has_field", "answer"]]),
    );
    let (_, report) = run(&twice);
    assert_eq!(
        report["detail"]["leaked"]["wrong_answer_0"],
        json!(["has_field", "has_field"])
    );
}

#[test]
fn a_gate_that_verifies_the_task_only_under_any_needs_every_check_to_do_so() {
    let (_, report) = run(&gate("any", json!([["solves_task"], ["solves_task"]])));
    assert_eq!(report["code"], "GATE_HONEST");
    let (_, report) = run(&gate(
        "all",
        json!([["has_field", "answer"], ["solves_task"]]),
    ));
    assert_eq!(report["code"], "GATE_HONEST");
    let (_, report) = run(&gate("all", json!([["has_field", "answer"]])));
    assert_eq!(report["code"], "NO_ANSWER_FREE_REPLY_PASSES");
}

#[test]
fn a_check_with_the_wrong_number_of_arguments_does_not_pass() {
    let cases = [
        json!([["solves_task", "extra"]]),
        json!([["solves_own", 1]]),
        json!([["has_field"]]),
        json!([["has_field", "answer", "more"]]),
        json!([["field_equals", "status"]]),
        json!([["field_equals", "status", "solved", "more"]]),
        json!([["keyword", "status"]]),
        json!([["keyword", "status", "solved", "more"]]),
    ];
    for checks in cases {
        let (_, report) = run(&gate("all", checks.clone()));
        assert_eq!(report["code"], "ACCEPTS_TRUE_SOLUTION", "{checks}");
        assert_eq!(report["detail"]["leaked"], json!({}), "{checks}");
    }
    let (_, report) = run(&gate("any", json!([["has_field"], ["solves_task"]])));
    assert_eq!(report["code"], "GATE_VERIFIES_TASK");
    assert_eq!(report["detail"]["leaked"], json!({}));
}

#[test]
fn a_field_named_by_a_list_or_an_object_does_not_pass() {
    let cases = [
        json!([["has_field", ["answer"]]]),
        json!([["field_equals", ["answer"], null]]),
        json!([["field_equals", {"answer": 1}, null]]),
        json!([["keyword", ["answer"], ""]]),
        json!([["keyword", {"a": 1}, ""]]),
        json!([["keyword", "answer", 7]]),
        json!([["keyword", "answer", ["/"]]]),
    ];
    for checks in cases {
        let (_, report) = run(&gate("all", checks.clone()));
        assert_eq!(report["code"], "ACCEPTS_TRUE_SOLUTION", "{checks}");
    }
}

#[test]
fn a_field_named_by_anything_else_names_no_field() {
    for name in [json!(1), json!(null), json!(true), json!(2.5)] {
        let (_, report) = run(&gate("all", json!([["has_field", name.clone()]])));
        assert_eq!(report["code"], "ACCEPTS_TRUE_SOLUTION", "{name}");
        let against_null = gate("any", json!([["field_equals", name.clone(), null]]));
        let (_, report) = run(&against_null);
        assert_eq!(
            report["detail"]["leaked"]
                .as_object()
                .expect("leaked")
                .len(),
            11,
            "{name}"
        );
        let against_text = gate("any", json!([["field_equals", name.clone(), "x"]]));
        let (_, report) = run(&against_text);
        assert_eq!(report["detail"]["leaked"], json!({}), "{name}");
        let empty = gate("any", json!([["keyword", name.clone(), ""]]));
        let (_, report) = run(&empty);
        assert_eq!(
            report["detail"]["leaked"]
                .as_object()
                .expect("leaked")
                .len(),
            11,
            "{name}"
        );
        let word = gate("any", json!([["keyword", name.clone(), "x"]]));
        let (_, report) = run(&word);
        assert_eq!(report["detail"]["leaked"], json!({}), "{name}");
    }
}

#[test]
fn a_field_a_reply_lacks_reads_as_null_when_compared_and_as_no_text_for_a_keyword() {
    let against_null = gate(
        "all",
        json!([["solves_task"], ["field_equals", "absent", null]]),
    );
    let (passed, _) = run(&against_null);
    assert!(passed);
    let against_text = gate(
        "all",
        json!([["solves_task"], ["field_equals", "absent", "x"]]),
    );
    let (_, report) = run(&against_text);
    assert_eq!(report["code"], "ACCEPTS_TRUE_SOLUTION");
    let (_, report) = run(&gate("any", json!([["keyword", "absent", ""]])));
    assert_eq!(
        report["detail"]["leaked"]
            .as_object()
            .expect("leaked")
            .len(),
        11
    );
    let (_, report) = run(&gate("any", json!([["keyword", "absent", "x"]])));
    assert_eq!(report["detail"]["leaked"], json!({}));
    let (_, report) = run(&gate("any", json!([["keyword", "absent", "null"]])));
    assert_eq!(report["detail"]["leaked"], json!({}));
}

#[test]
fn a_keyword_is_looked_for_in_the_text_or_the_canonical_form_of_the_field() {
    let in_text = gate("any", json!([["keyword", "note", "correct"]]));
    assert_eq!(leaked_names(&run(&in_text).1), ["keyword_bait"]);
    let in_object = gate(
        "any",
        json!([["keyword", "receipt", "\"checker\":\"exact\""]]),
    );
    assert_eq!(leaked_names(&run(&in_object).1), ["templated_receipt"]);
    let in_list = gate("any", json!([["keyword", "answer", "[\"2/1\",\"1/1\"]"]]));
    assert!(run(&in_list).1["detail"]["leaked"]
        .as_object()
        .expect("leaked")
        .is_empty());
    let in_answer = gate("any", json!([["keyword", "answer", "3/1\",\"1/1"]]));
    assert_eq!(leaked_names(&run(&in_answer).1), ["wrong_answer_0"]);
}

#[test]
fn field_equals_compares_a_field_to_a_value_of_any_kind() {
    let status = gate("any", json!([["field_equals", "status", "solved"]]));
    assert_eq!(
        leaked_names(&run(&status).1),
        ["constant_verdict", "keyword_bait", "templated_receipt"]
    );
    let refusal = gate(
        "any",
        json!([["field_equals", "refusal", "UNRESOLVED_INCONSISTENT"]]),
    );
    assert_eq!(leaked_names(&run(&refusal).1), ["constant_refusal"]);
    let list = gate("any", json!([["field_equals", "b", [1]]]));
    assert_eq!(leaked_names(&run(&list).1), ["input_replacement"]);
    let kind = gate("any", json!([["field_equals", "b", ["1"]]]));
    assert!(leaked_names(&run(&kind).1).is_empty());
}

#[test]
fn the_probes_depend_on_the_answer() {
    let cases = [
        (json!({"A": [[2]], "b": [4]}), 10),
        (json!({"A": [[1, 0], [0, 1]], "b": [0, 0]}), 10),
        (json!({"A": [[2, 0], [0, 3]], "b": [1, 1]}), 11),
        (
            json!({"A": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "b": [1, 2, 3]}),
            12,
        ),
        (json!({"A": [["1/2"]], "b": ["1/4"]}), 10),
    ];
    for (system, probes) in cases {
        let mut custom = task();
        custom["A"] = system["A"].clone();
        custom["b"] = system["b"].clone();
        let (passed, report) = run_on(&custom, &gate("all", json!([["solves_task"]])));
        assert!(passed, "{system}: {report}");
        assert_eq!(report["detail"]["probes"], probes, "{system}");
    }
}

#[test]
fn the_wrong_answers_are_the_ones_off_in_the_same_form() {
    let mut custom = task();
    custom["A"] = json!([[2, 0], [0, 3]]);
    custom["b"] = json!([1, 1]);
    let any_answer = gate("any", json!([["has_field", "answer"]]));
    let (_, report) = run_on(&custom, &any_answer);
    assert_eq!(
        report["detail"]["leaked"]
            .as_object()
            .expect("leaked")
            .len(),
        6
    );
    let keyword = gate("any", json!([["keyword", "answer", "3/2"]]));
    let (_, report) = run_on(&custom, &keyword);
    assert_eq!(leaked_names(&report), ["wrong_answer_0", "wrong_answer_2"]);
    let keyword = gate("any", json!([["keyword", "answer", "\"0/1\",\"0/1\""]]));
    let (_, report) = run_on(&custom, &keyword);
    assert_eq!(leaked_names(&report), ["wrong_answer_3"]);
    let keyword = gate("any", json!([["keyword", "answer", "\"1/2\",\"1/3\""]]));
    let (_, report) = run_on(&custom, &keyword);
    assert!(
        leaked_names(&report).is_empty(),
        "the right answer is no probe"
    );
    let keyword = gate("any", json!([["keyword", "answer", "\"1/1\",\"5/6\""]]));
    let (_, report) = run_on(&custom, &keyword);
    assert_eq!(leaked_names(&report), ["wrong_answer_4"]);
}

#[test]
fn an_answer_of_another_length_does_not_solve_the_system() {
    let mut custom = task();
    custom["b"] = json!([1, 1]);
    let (passed, report) = run_on(&custom, &gate("all", json!([["solves_task"]])));
    assert!(passed, "{report}");
    assert_eq!(report["detail"]["leaked"], json!({}));
}

#[test]
fn a_keyword_is_matched_exactly_as_written() {
    let cases: [(&str, &[&str]); 4] = [
        ("HOST", &["constant_verdict"]),
        ("host", &[]),
        ("certified", &[]),
        ("\"HOST", &[]),
    ];
    for (word, expected) in cases {
        let (_, report) = run(&gate("any", json!([["keyword", "verdict", word]])));
        assert_eq!(leaked_names(&report), expected, "{word}");
    }
}

#[test]
fn every_probe_is_named_and_carries_the_fields_the_gates_read() {
    let (_, report) = run(&gate("any", json!([["field_equals", "absent", null]])));
    assert_eq!(
        leaked_names(&report),
        [
            "constant_refusal",
            "constant_verdict",
            "empty_object",
            "input_replacement",
            "keyword_bait",
            "templated_receipt",
            "wrong_answer_0",
            "wrong_answer_1",
            "wrong_answer_2",
            "wrong_answer_3",
            "wrong_answer_4",
        ]
    );
    let verdict = gate(
        "any",
        json!([["field_equals", "verdict", "HOST_CERTIFIED"]]),
    );
    assert_eq!(leaked_names(&run(&verdict).1), ["constant_verdict"]);
    let receipt = json!({"checker": "exact", "sha256": "0".repeat(64)});
    let templated = gate("any", json!([["field_equals", "receipt", receipt]]));
    assert_eq!(leaked_names(&run(&templated).1), ["templated_receipt"]);
}

#[test]
fn a_task_must_state_a_system_with_one_solution() {
    let edit = |key: &str, value: Value| {
        let mut changed = task();
        changed[key] = value;
        changed
    };
    assert_eq!(
        bad_task(&edit("b", json!([3, 1, 5]))),
        "A must be rectangular, with a column, and match b"
    );
    assert_eq!(
        bad_task(&edit("A", json!([[1, 1], [2, 2]]))),
        "the audited task must have a unique solution"
    );
    assert_eq!(
        bad_task(&json!({"statement": "s", "A": [[1, 1]], "b": [3]})),
        "the audited task must have a unique solution"
    );
    assert_eq!(
        bad_task(&json!({"statement": "s", "A": [[1, 1], [1, 1]], "b": [3, 2]})),
        "the audited task must have a unique solution"
    );
    assert_eq!(
        bad_task(&edit("A", json!([]))),
        "A must be a nonempty list of rows"
    );
    assert_eq!(
        bad_task(&edit("A", json!([[1, "x"], [1, -1]]))),
        "every row of A must be a list of exact rationals"
    );
    assert_eq!(
        bad_task(&edit("b", json!("3 1"))),
        "b must be a list of exact rationals"
    );
}

#[test]
fn a_reply_must_be_an_object_with_a_gate_of_a_mode_and_checks() {
    let cases = [
        (json!("all"), "gate object required"),
        (json!([["solves_task"]]), "gate object required"),
        (json!({}), "gate object required"),
        (json!({"gate": "all"}), "gate object required"),
        (json!({"gate": [["solves_task"]]}), "gate object required"),
        (json!({"gate": null}), "gate object required"),
    ];
    for (reply, reason) in cases {
        assert_eq!(malformed(&reply), reason, "{reply}");
    }
    let shape = "gate needs mode all|any and a non-empty check list";
    let cases = [
        json!({"gate": {"checks": [["solves_task"]]}}),
        json!({"gate": {"mode": "some", "checks": [["solves_task"]]}}),
        json!({"gate": {"mode": "ALL", "checks": [["solves_task"]]}}),
        json!({"gate": {"mode": ["all"], "checks": [["solves_task"]]}}),
        json!({"gate": {"mode": "all"}}),
        json!({"gate": {"mode": "all", "checks": []}}),
        json!({"gate": {"mode": "all", "checks": "solves_task"}}),
        json!({"gate": {"mode": "all", "checks": {"solves_task": []}}}),
    ];
    for reply in cases {
        assert_eq!(malformed(&reply), shape, "{reply}");
    }
}

#[test]
fn every_check_must_name_an_operation_of_the_language() {
    let cases = [
        json!([["solves_task"], ["verifies"]]),
        json!([["Solves_task"]]),
        json!([[]]),
        json!(["solves_task"]),
        json!([[1, 2]]),
        json!([[null]]),
        json!([[["solves_task"]]]),
        json!([{"op": "solves_task"}]),
    ];
    for checks in cases {
        assert_eq!(
            malformed(&gate("all", checks.clone())),
            "unknown check",
            "{checks}"
        );
    }
}

#[test]
fn the_gate_is_read_whole_before_any_probe_is_replayed() {
    let reply = gate("all", json!([["solves_task"], ["unknown"]]));
    let (passed, report) = run(&reply);
    assert!(!passed);
    assert_eq!(report["predicates"], json!([]));
}

#[test]
fn a_missing_reply_stops_the_run() {
    let Outcome::Fail { result } = judge(&request(&task(), &[None])) else {
        panic!("expected a refused run");
    };
    assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
    assert_eq!(result["predicates"], json!([]));
}

#[test]
fn the_prompt_is_the_family_prompt_for_the_task() {
    let Outcome::Pass { result } = next(&request(&task(), &[])) else {
        panic!("expected a turn");
    };
    let prompt = result["ask"]["prompt"].as_str().expect("a prompt");
    assert!(prompt.starts_with(
        "WF43 Gate-honesty and answer-free leak audit. Write a gate that accepts a reply"
    ));
}

#[test]
fn a_second_reply_is_not_accepted() {
    let honest = gate("all", json!([["solves_task"]]));
    match judge(&request(&task(), &[Some(honest.clone()), Some(honest)])) {
        Outcome::Refused { refusal } => assert_eq!(refusal.code, "BAD_REQUEST"),
        other => panic!("expected a refusal, got {other:?}"),
    }
}
