//! WF18, dossier replay campaign: the pin of the grader, the stored digests, the stored grades
//! and the refusals that follow from each.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf18-tests:v1

use pfp_operads::datum::Datum;
use pfp_operads::families::duality::pin;
use pfp_operads::families::wf18::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

fn canonical(value: &Value) -> String {
    Datum::parse(&value.to_string())
        .expect("a datum")
        .canonical()
}

fn feasible() -> Value {
    json!({"n": 3, "edges": [[0, 1, 2], [1, 2, -1], [0, 2, 3], [2, 0, 1]]})
}

fn negative() -> Value {
    json!({"n": 3, "edges": [[0, 1, 1], [1, 2, -3], [2, 0, 1]]})
}

fn cell(id: &str, input: &Value, raw: &str, grade: &str) -> Value {
    json!({
        "cell_id": id,
        "input": input,
        "input_sha256": sha(&canonical(input)),
        "raw_reply": raw,
        "raw_reply_sha256": sha(raw),
        "grade": grade,
    })
}

fn cells() -> Vec<Value> {
    vec![
        cell(
            "c1",
            &feasible(),
            "{\"potential\": [0, 2, 1]}",
            "HOST_CERTIFIED",
        ),
        cell(
            "c2",
            &negative(),
            "{\"negative_cycle\": [0, 1, 2]}",
            "TYPED_REFUSAL",
        ),
        cell("c3", &feasible(), "{\"potential\": [0, 0, 0]}", "REFUSED"),
    ]
}

fn pins() -> Value {
    json!({"cycle_duality": pin()})
}

fn task_of(cells: &[Value], pins: &Value) -> Value {
    json!({
        "statement": "Replay the frozen dossier.",
        "dossier": {"grader": "cycle_duality", "source_pins": pins, "cells": cells},
    })
}

fn task() -> Value {
    task_of(&cells(), &pins())
}

fn request(task: &Value, replies: &[Value]) -> String {
    json!({"workflow": "WF18", "task": task, "sealed": {}, "replies": replies}).to_string()
}

fn run(task: &Value) -> (bool, Value) {
    match judge(&request(task, &[])) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
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

fn bad_task(task: &Value) -> String {
    match judge(&request(task, &[])) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

fn edit(path: &[&str], value: Value) -> Value {
    let mut task = task();
    let mut place = &mut task;
    for key in path {
        place = match key.parse::<usize>() {
            Ok(index) => &mut place[index],
            Err(_) => &mut place[*key],
        };
    }
    *place = value;
    task
}

fn cleared(path: &[&str]) -> Value {
    let mut task = task();
    let (last, parents) = path.split_last().expect("a path");
    let mut place = &mut task;
    for key in parents {
        place = match key.parse::<usize>() {
            Ok(index) => &mut place[index],
            Err(_) => &mut place[*key],
        };
    }
    place.as_object_mut().expect("an object").remove(*last);
    task
}

#[test]
fn the_registry_names_the_family() {
    assert_eq!(FAMILY.workflow, "WF18");
    assert_eq!(FAMILY.name, "Dossier replay campaign");
    assert_eq!(FAMILY.host_check, "dossier_replay_reproduces_grades");
}

#[test]
fn a_dossier_whose_every_grade_reproduces_is_certified() {
    let (passed, report) = run(&task());
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "REPLAY_REPRODUCED");
    assert_eq!(report["detail"], json!({"cells": 3, "mismatched": []}));
    assert_eq!(
        outcomes(&report),
        [
            ("source_pin_matches", true),
            ("stored_bytes_match_digests", true),
            ("every_grade_reproduces", true),
            ("zero_model_calls", true),
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
        [sha("\"cycle_duality\""), sha("[]"), sha("[]"), sha("0")]
    );
    assert_eq!(report["asked"], json!([]));
}

#[test]
fn the_host_asks_nothing() {
    match next(&request(&task(), &[])) {
        Outcome::Pass { result } => {
            assert_eq!(result["ask"], Value::Null);
            assert_eq!(result["asked"], json!([]));
        }
        other => panic!("expected a turn, got {other:?}"),
    }
}

#[test]
fn a_reply_that_nothing_asked_for_is_not_accepted() {
    match judge(&request(&task(), &[json!({"content": {"potential": [0]}})])) {
        Outcome::Refused { refusal } => assert_eq!(refusal.code, "BAD_REQUEST"),
        other => panic!("expected a refusal, got {other:?}"),
    }
}

#[test]
fn a_reply_byte_that_drifted_is_refused_with_the_cell() {
    let mut drifted = cells();
    drifted[0]["raw_reply"] = json!("{\"potential\": [0, 2, 2]}");
    let (passed, report) = run(&task_of(&drifted, &pins()));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "STORED_BYTES_DRIFTED");
    assert_eq!(report["detail"], json!({"drift": ["c1:raw_reply"]}));
    assert_eq!(
        outcomes(&report),
        [
            ("source_pin_matches", true),
            ("stored_bytes_match_digests", false),
            ("every_grade_reproduces", false),
            ("zero_model_calls", true),
        ]
    );
}

#[test]
fn an_input_that_drifted_is_refused_with_the_cell() {
    let mut drifted = cells();
    drifted[2]["input"]["edges"][0][2] = json!(9);
    let (_, report) = run(&task_of(&drifted, &pins()));
    assert_eq!(report["code"], "STORED_BYTES_DRIFTED");
    assert_eq!(report["detail"], json!({"drift": ["c3:input"]}));
    let held: Vec<bool> = outcomes(&report).iter().map(|row| row.1).collect();
    assert_eq!(held, [true, false, true, true]);
}

#[test]
fn drift_is_listed_by_cell_with_the_reply_before_the_input() {
    let mut drifted = cells();
    drifted[0]["input"]["n"] = json!(4);
    drifted[0]["raw_reply"] = json!("{\"potential\": [0, 2, 1]} ");
    drifted[1]["input"]["n"] = json!(5);
    drifted[2]["raw_reply"] = json!("{\"potential\": [0, 0, 0]} ");
    let (_, report) = run(&task_of(&drifted, &pins()));
    assert_eq!(
        report["detail"],
        json!({"drift": ["c1:raw_reply", "c1:input", "c2:input", "c3:raw_reply"]})
    );
}

#[test]
fn a_digest_that_is_missing_or_not_text_is_drift() {
    let mut missing = cells();
    missing[1]
        .as_object_mut()
        .expect("a cell")
        .remove("raw_reply_sha256");
    missing[2]
        .as_object_mut()
        .expect("a cell")
        .remove("input_sha256");
    missing[0]["input_sha256"] = json!(5);
    let (_, report) = run(&task_of(&missing, &pins()));
    assert_eq!(
        report["detail"],
        json!({"drift": ["c1:input", "c2:raw_reply", "c3:input"]})
    );
}

#[test]
fn a_digest_is_the_hash_of_the_reply_text_and_of_the_inputs_canonical_form() {
    let mut other = cells();
    other[0]["raw_reply_sha256"] = json!(sha("{\"potential\": [0, 2, 1]}\n"));
    other[1]["input_sha256"] = json!(sha(
        &serde_json::to_string_pretty(&negative()).expect("text")
    ));
    let (_, report) = run(&task_of(&other, &pins()));
    assert_eq!(
        report["detail"],
        json!({"drift": ["c1:raw_reply", "c2:input"]})
    );
    let mut shouted = cells();
    shouted[0]["raw_reply_sha256"] = json!(sha("{\"potential\": [0, 2, 1]}").to_uppercase());
    let (_, report) = run(&task_of(&shouted, &pins()));
    assert_eq!(report["detail"], json!({"drift": ["c1:raw_reply"]}));
}

#[test]
fn a_grade_that_does_not_reproduce_is_refused_with_the_cell() {
    let mut regraded = cells();
    regraded[1]["grade"] = json!("HOST_CERTIFIED");
    let (passed, report) = run(&task_of(&regraded, &pins()));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "EVERY_GRADE_REPRODUCES");
    assert_eq!(
        report["detail"],
        json!({"cells": 3, "mismatched": ["c2"], "failed": ["every_grade_reproduces"]})
    );
    let held: Vec<bool> = outcomes(&report).iter().map(|row| row.1).collect();
    assert_eq!(held, [true, true, false, true]);
}

fn digests(report: &Value) -> Vec<&str> {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| row["evidence_sha256"].as_str().expect("a digest"))
        .collect()
}

#[test]
fn the_evidence_of_each_predicate_is_the_names_it_lists() {
    let mut drifted = cells();
    drifted[0]["raw_reply"] = json!("{\"potential\": [0, 2, 2]}");
    drifted[2]["input"]["n"] = json!(4);
    let (_, report) = run(&task_of(&drifted, &pins()));
    assert_eq!(
        digests(&report),
        [
            sha("\"cycle_duality\""),
            sha("[\"c1:raw_reply\",\"c3:input\"]"),
            sha("[\"c1\"]"),
            sha("0")
        ]
    );
    let mut regraded = cells();
    regraded[1]["grade"] = json!("HOST_CERTIFIED");
    let (_, report) = run(&task_of(&regraded, &pins()));
    assert_eq!(
        digests(&report),
        [
            sha("\"cycle_duality\""),
            sha("[]"),
            sha("[\"c2\"]"),
            sha("0")
        ]
    );
}

#[test]
fn the_mismatched_cells_are_listed_in_order_of_name() {
    let wrong = |id: &str| cell(id, &feasible(), "{\"potential\": [0, 2, 1]}", "REFUSED");
    let cells = [
        wrong("z"),
        wrong("m"),
        cell(
            "k",
            &feasible(),
            "{\"potential\": [0, 2, 1]}",
            "HOST_CERTIFIED",
        ),
        wrong("a"),
        wrong("c10"),
        wrong("c2"),
    ];
    let (_, report) = run(&task_of(&cells, &pins()));
    assert_eq!(
        report["detail"]["mismatched"],
        json!(["a", "c10", "c2", "m", "z"])
    );
}

#[test]
fn every_kind_of_grade_is_regraded() {
    let mut task = cells();
    task.push(cell(
        "c4",
        &negative(),
        "{\"potential\": [0, 0, 0]}",
        "REFUSED",
    ));
    task.push(cell("c5", &negative(), "not json", "REFUSED"));
    task.push(cell(
        "c6",
        &feasible(),
        "{\"negative_cycle\": [0, 1, 2]}",
        "REFUSED",
    ));
    let (passed, report) = run(&task_of(&task, &pins()));
    assert!(passed, "{report}");
    assert_eq!(report["detail"]["cells"], 6);
    let mut wrong = task.clone();
    wrong[3]["grade"] = json!("HOST_CERTIFIED");
    wrong[4]["grade"] = json!("TYPED_REFUSAL");
    wrong[5]["grade"] = json!("hOST_CERTIFIED");
    let (_, report) = run(&task_of(&wrong, &pins()));
    assert_eq!(report["detail"]["mismatched"], json!(["c4", "c5", "c6"]));
}

#[test]
fn a_parallel_edge_violation_a_grader_might_miss_is_regraded_as_refused() {
    let parallel = json!({"n": 2, "edges": [[0, 1, -10], [0, 1, 5]]});
    let mut with = cells();
    with.push(cell(
        "c4",
        &parallel,
        "{\"potential\": [0, 5]}",
        "HOST_CERTIFIED",
    ));
    let (_, report) = run(&task_of(&with, &pins()));
    assert_eq!(report["code"], "EVERY_GRADE_REPRODUCES");
    assert_eq!(report["detail"]["mismatched"], json!(["c4"]));
}

#[test]
fn a_pin_that_does_not_match_the_grader_refuses_first() {
    let wrong = json!({"cycle_duality": "0".repeat(64)});
    let (passed, report) = run(&task_of(&cells(), &wrong));
    assert!(!passed);
    assert_eq!(report["code"], "SOURCE_PIN_DRIFT");
    assert_eq!(report["detail"], json!({}));
    assert_eq!(
        outcomes(&report),
        [
            ("source_pin_matches", false),
            ("stored_bytes_match_digests", true),
            ("every_grade_reproduces", true),
            ("zero_model_calls", true),
        ]
    );
    let mut drifted = cells();
    drifted[0]["raw_reply"] = json!("{\"potential\": [0, 0, 0]}");
    let (_, report) = run(&task_of(&drifted, &wrong));
    assert_eq!(report["code"], "SOURCE_PIN_DRIFT");
    let held: Vec<bool> = outcomes(&report).iter().map(|row| row.1).collect();
    assert_eq!(held, [false, false, false, true]);
}

#[test]
fn a_pin_that_is_missing_or_not_text_does_not_match() {
    for pins in [
        json!({}),
        json!({"cycle_duality": 5}),
        json!({"cycle_duality": null}),
        json!({"cycle_duality": pin().to_uppercase()}),
        json!({"cycle_duality": format!("{} ", pin())}),
        json!({"other": pin()}),
    ] {
        let (_, report) = run(&task_of(&cells(), &pins));
        assert_eq!(report["code"], "SOURCE_PIN_DRIFT", "{pins}");
    }
}

#[test]
fn pins_of_other_graders_are_ignored() {
    let more = json!({"cycle_duality": pin(), "other": "x", "third": 5});
    let (passed, report) = run(&task_of(&cells(), &more));
    assert!(passed, "{report}");
}

#[test]
fn a_dossier_states_its_grader_pins_and_cells() {
    let cases = [
        (cleared(&["dossier"]), "dossier must be an object"),
        (edit(&["dossier"], json!([])), "dossier must be an object"),
        (
            cleared(&["dossier", "source_pins"]),
            "source_pins must be an object",
        ),
        (
            edit(&["dossier", "source_pins"], json!("x")),
            "source_pins must be an object",
        ),
        (
            cleared(&["dossier", "grader"]),
            "grader must be cycle_duality",
        ),
        (
            edit(&["dossier", "grader"], json!("other")),
            "grader must be cycle_duality",
        ),
        (
            edit(&["dossier", "grader"], json!(5)),
            "grader must be cycle_duality",
        ),
        (
            cleared(&["dossier", "cells"]),
            "cells must be a nonempty list",
        ),
        (
            edit(&["dossier", "cells"], json!([])),
            "cells must be a nonempty list",
        ),
        (
            edit(&["dossier", "cells"], json!({})),
            "cells must be a nonempty list",
        ),
    ];
    for (bad, reason) in cases {
        assert_eq!(bad_task(&bad), reason, "{bad}");
    }
}

#[test]
fn the_dossier_is_read_in_the_order_the_task_lists_its_parts() {
    let mut both = edit(&["dossier", "grader"], json!("other"));
    both["dossier"]["source_pins"] = json!(5);
    assert_eq!(bad_task(&both), "source_pins must be an object");
    let mut cells = edit(&["dossier", "cells"], json!([]));
    cells["dossier"]["grader"] = json!("other");
    assert_eq!(bad_task(&cells), "grader must be cycle_duality");
}

#[test]
fn a_cell_states_its_input_its_name_its_reply_and_its_grade() {
    let cases = [
        (
            cleared(&["dossier", "cells", "0", "input"]),
            "a cell needs its input",
        ),
        (
            cleared(&["dossier", "cells", "1", "cell_id"]),
            "a cell needs cell_id as text",
        ),
        (
            edit(&["dossier", "cells", "1", "cell_id"], json!(2)),
            "a cell needs cell_id as text",
        ),
        (
            cleared(&["dossier", "cells", "2", "raw_reply"]),
            "a cell needs raw_reply as text",
        ),
        (
            edit(
                &["dossier", "cells", "2", "raw_reply"],
                json!({"potential": [0]}),
            ),
            "a cell needs raw_reply as text",
        ),
        (
            cleared(&["dossier", "cells", "0", "grade"]),
            "a cell needs grade as text",
        ),
        (
            edit(&["dossier", "cells", "0", "grade"], json!(null)),
            "a cell needs grade as text",
        ),
        (
            edit(&["dossier", "cells", "0"], json!("c1")),
            "a cell needs its input",
        ),
    ];
    for (bad, reason) in cases {
        assert_eq!(bad_task(&bad), reason, "{bad}");
    }
}

#[test]
fn a_cell_is_read_in_the_order_its_parts_are_listed() {
    let mut cell = edit(&["dossier", "cells", "0", "cell_id"], json!(7));
    cell["dossier"]["cells"][0]["raw_reply"] = json!(7);
    cell["dossier"]["cells"][0]["grade"] = json!(7);
    assert_eq!(bad_task(&cell), "a cell needs cell_id as text");
    let mut input = edit(&["dossier", "cells", "0", "input"], json!({"edges": []}));
    input["dossier"]["cells"][0]["raw_reply"] = json!(7);
    assert_eq!(bad_task(&input), "n must be an exact integer");
    let mut reply = cleared(&["dossier", "cells", "0", "raw_reply"]);
    reply["dossier"]["cells"][0]["grade"] = json!(7);
    assert_eq!(bad_task(&reply), "a cell needs raw_reply as text");
}

#[test]
fn the_input_of_a_cell_is_a_weighted_digraph() {
    let cases = [
        (json!({"n": 2.5, "edges": []}), "n must be an exact integer"),
        (json!({"n": 2}), "edges must be a list"),
        (
            json!({"n": 2, "edges": [[0, 1]]}),
            "an edge is two integer ends and an exact rational weight",
        ),
    ];
    for (input, reason) in cases {
        let bad = edit(&["dossier", "cells", "1", "input"], input);
        assert_eq!(bad_task(&bad), reason, "{bad}");
    }
}

#[test]
fn each_cell_needs_its_own_name() {
    let mut twice = cells();
    twice[2]["cell_id"] = json!("c1");
    assert_eq!(
        bad_task(&task_of(&twice, &pins())),
        "each cell needs its own cell_id"
    );
    let mut once = cells();
    once[2]["cell_id"] = json!("C1");
    let (passed, _) = run(&task_of(&once, &pins()));
    assert!(passed);
}

#[test]
fn a_dossier_of_one_cell_is_replayed() {
    let one = [cell(
        "only",
        &negative(),
        "{\"negative_cycle\": [1, 2, 0]}",
        "TYPED_REFUSAL",
    )];
    let (passed, report) = run(&task_of(&one, &pins()));
    assert!(passed);
    assert_eq!(report["detail"], json!({"cells": 1, "mismatched": []}));
}
