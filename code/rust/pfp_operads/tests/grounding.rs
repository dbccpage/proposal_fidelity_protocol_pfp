//! The grounded slots of a solver reply, and the typing of a bare candidate list.

use std::process::Command as Process;

use pfp_operads::envelope::typing;
use pfp_operads::grounding::{grounded_slots, grounding, SUM_SLOTS};
use pfp_operads::host::{respond, Command};
use serde_json::{json, Value};

fn candidate(id: &str) -> Value {
    json!({
        "id": id,
        "operation": "add every member of the list",
        "source_colours": ["IntegerList"],
        "target_colour": "Integer",
        "arity": 1,
        "source": {"kind": "seed_prompt", "quote": "input.values"},
        "witness_refs": ["task_result"]
    })
}

fn row(value: Value) -> Value {
    json!({"disposition": "provided", "value": value, "reason": ""})
}

/// A solver reply whose four grounded slots restate the public input.
fn lawful() -> Value {
    json!({
        "checker": "integer_sum_v1",
        "values": [17, 25, -4],
        "candidates": [candidate("sum")],
        "slot_report": {
            "carrier": row(json!("Integers under addition.")),
            "concrete_spans": row(json!({"source": "input.values", "literal": [17, 25, -4]})),
            "parameter_bindings": row(json!({"values": [17, 25, -4], "arithmetic": "integer_exact"})),
            "instantiated_arguments": row(json!({"operad_id": "sum", "arguments": [17, 25, -4]})),
            "preservation_obligations": row(json!({
                "all_operands_once": true, "signed_integers": true, "rounding": "forbidden"
            }))
        }
    })
}

fn edited(edit: impl FnOnce(&mut Value)) -> Value {
    let mut request = lawful();
    edit(&mut request);
    request
}

fn errors(request: &Value) -> Vec<String> {
    grounding(&request.to_string()).expect("readable").errors
}

fn slot(name: &str, edit: impl FnOnce(&mut Value)) -> Vec<String> {
    errors(&edited(|r| edit(&mut r["slot_report"][name]["value"])))
}

const MISMATCH: &str = "PUBLIC_BINDING_OR_DECLARED_CONSTRAINT_MISMATCH";

fn mismatch(name: &str) -> [String; 1] {
    [format!("L2_GROUNDING:{name}:{MISMATCH}")]
}

#[test]
fn a_reply_that_restates_the_public_input_is_grounded() {
    let report = grounding(&lawful().to_string()).expect("readable");
    assert!(report.valid && report.errors.is_empty());
    assert_eq!(report.checked_slots, SUM_SLOTS);
    let mut sorted = SUM_SLOTS;
    sorted.sort_unstable();
    assert_eq!(sorted, SUM_SLOTS, "the slots are checked in sorted order");
    assert_eq!(grounded_slots("integer_sum_v1"), SUM_SLOTS);
    assert!(grounded_slots("schema_only").is_empty());
}

#[test]
fn the_span_slot_names_the_input_and_copies_its_values_exactly() {
    let name = "concrete_spans";
    assert_eq!(slot(name, |v| v["literal"][2] = json!(-3)), mismatch(name));
    assert_eq!(
        slot(name, |v| v["literal"][0] = json!(17.0)),
        mismatch(name)
    );
    assert_eq!(
        slot(name, |v| v["literal"] = json!([17, 25])),
        mismatch(name)
    );
    assert_eq!(
        slot(name, |v| v["literal"] = json!([25, 17, -4])),
        mismatch(name)
    );
    assert_eq!(slot(name, |v| v["source"] = json!("input")), mismatch(name));
    assert_eq!(slot(name, |v| v["note"] = json!("extra")), mismatch(name));
    assert_eq!(
        slot(name, |v| *v = json!("Finite integer task")),
        mismatch(name)
    );
    // null is a value that restates nothing; only a missing key is a missing value.
    assert_eq!(slot(name, |v| *v = json!(null)), mismatch(name));
}

#[test]
fn values_beyond_sixty_four_bits_are_compared_exactly() {
    let big = "123456789012345678901234567890";
    let near = "123456789012345678901234567891";
    let request = |literal: &str| {
        lawful()
            .to_string()
            .replace("[17,25,-4]", &format!("[{big},25,-4]"))
            .replacen(
                &format!("\"literal\":[{big}"),
                &format!("\"literal\":[{literal}"),
                1,
            )
    };
    assert!(grounding(&request(big)).expect("readable").valid);
    assert_eq!(
        grounding(&request(near)).expect("readable").errors,
        mismatch("concrete_spans")
    );
}

#[test]
fn the_binding_slot_copies_the_values_and_declares_exact_arithmetic() {
    let name = "parameter_bindings";
    assert_eq!(slot(name, |v| v["values"][1] = json!(26)), mismatch(name));
    assert_eq!(
        slot(name, |v| v["arithmetic"] = json!("float")),
        mismatch(name)
    );
    assert_eq!(
        slot(name, |v| v["values"] = json!("17,25,-4")),
        mismatch(name)
    );
}

#[test]
fn the_argument_slot_names_a_licensed_candidate_and_applies_it_to_the_values() {
    let name = "instantiated_arguments";
    let unbound = [format!(
        "L2_GROUNDING:{name}:UNBOUND_INTEGER_LIST_OPERATION"
    )];
    assert_eq!(slot(name, |v| v["operad_id"] = json!("invented")), unbound);
    assert_eq!(slot(name, |v| v["operad_id"] = json!(7)), unbound);
    assert_eq!(slot(name, |v| *v = json!("Finite integer task")), unbound);
    assert_eq!(
        slot(name, |v| v["arguments"][2] = json!(-3)),
        mismatch(name)
    );
    assert_eq!(
        slot(name, |v| v["arguments"][0] = json!(17.0)),
        mismatch(name)
    );
    assert_eq!(slot(name, |v| v["extra"] = json!(0)), mismatch(name));
    // A candidate that is named but not licensed binds nothing.
    let unlicensed =
        |field: &str, value: Value| errors(&edited(|r| r["candidates"][0][field] = value));
    assert_eq!(unlicensed("target_colour", json!("IntegerList")), unbound);
    assert_eq!(unlicensed("source_colours", json!(["Integer"])), unbound);
    assert_eq!(unlicensed("arity", json!(2)), unbound);
    // A second, licensed candidate may be the one named.
    let second = edited(|r| {
        r["candidates"][0]["target_colour"] = json!("Text");
        r["candidates"]
            .as_array_mut()
            .expect("a list")
            .push(candidate("total"));
        r["slot_report"]["instantiated_arguments"]["value"]["operad_id"] = json!("total");
    });
    assert!(errors(&second).is_empty());
}

#[test]
fn the_obligation_slot_declares_all_three_obligations() {
    let name = "preservation_obligations";
    assert_eq!(
        slot(name, |v| v["all_operands_once"] = json!(false)),
        mismatch(name)
    );
    assert_eq!(
        slot(name, |v| v["all_operands_once"] = json!(1)),
        mismatch(name)
    );
    assert_eq!(
        slot(name, |v| v["signed_integers"] = json!(false)),
        mismatch(name)
    );
    assert_eq!(
        slot(name, |v| v["rounding"] = json!("nearest")),
        mismatch(name)
    );
}

#[test]
fn every_failing_slot_is_reported_in_slot_order_and_the_rest_are_listed_as_checked() {
    let request = edited(|r| {
        let rows = r["slot_report"].as_object_mut().expect("a map");
        rows.remove("concrete_spans");
        rows["parameter_bindings"] = json!({"disposition": "provided", "reason": ""});
        rows["instantiated_arguments"]["value"]["operad_id"] = json!("invented");
    });
    let report = grounding(&request.to_string()).expect("readable");
    assert!(!report.valid);
    assert_eq!(
        report.errors,
        [
            "L2_GROUNDING:concrete_spans:MISSING_SLOT",
            "L2_GROUNDING:instantiated_arguments:UNBOUND_INTEGER_LIST_OPERATION",
            "L2_GROUNDING:parameter_bindings:MISSING_VALUE"
        ]
    );
    assert_eq!(report.checked_slots, ["preservation_obligations"]);
}

#[test]
fn a_grounding_request_is_closed_and_needs_a_grounding_checker_and_integer_values() {
    let refused = |request: Value| grounding(&request.to_string()).expect_err("refused").code;
    assert_eq!(refused(edited(|r| r["extra"] = json!(1))), "BAD_REQUEST");
    assert_eq!(
        refused(edited(|r| r["checker"] = json!("schema_only"))),
        "UNKNOWN_CHECKER"
    );
    assert_eq!(refused(edited(|r| r["values"][0] = json!(1.5))), "BAD_CASE");
    assert_eq!(
        refused(edited(|r| r["candidates"][0]["cost"] = json!(1))),
        "BAD_REQUEST"
    );
    assert_eq!(grounding("[]").expect_err("refused").code, "BAD_REQUEST");
}

#[test]
fn typing_reads_a_bare_candidate_list() {
    let mut odd = candidate("odd");
    odd["target_colour"] = json!("Z");
    let mut wide = candidate("wide");
    wide["arity"] = json!(2);
    let request = json!({"checker": "integer_sum_v1", "candidates": [candidate("sum"), odd, wide]});
    assert_eq!(
        serde_json::to_value(typing(&request.to_string()).expect("readable")).expect("encodes"),
        json!({"candidates": [
            {"id": "sum", "typed": true, "licensed_as": "integer_list_sum"},
            {"id": "odd", "typed": false, "licensed_as": null},
            {"id": "wide", "typed": true, "licensed_as": null}
        ]})
    );
    let other = json!({"checker": "schema_only", "candidates": [candidate("sum")]});
    assert_eq!(
        typing(&other.to_string()).expect("readable").candidates[0].licensed_as,
        None
    );
    let open = json!({"checker": "integer_sum_v1", "candidates": [], "answer": {}});
    assert_eq!(
        typing(&open.to_string()).expect_err("refused").code,
        "BAD_REQUEST"
    );
}

fn status(command: &Command) -> Value {
    serde_json::to_value(respond(command)).expect("encodes")
}

#[test]
fn respond_reports_grounding_and_typing() {
    assert_eq!(
        status(&Command::Grounding(lawful().to_string()))["status"],
        "PASS"
    );
    let broken = edited(|r| r["slot_report"]["concrete_spans"]["value"]["source"] = json!("x"));
    let fail = status(&Command::Grounding(broken.to_string()));
    assert_eq!(fail["status"], "FAIL");
    assert_eq!(fail["result"]["valid"], false);
    assert_eq!(
        status(&Command::Grounding("{}".to_owned()))["refusal"]["code"],
        "BAD_REQUEST"
    );
    let request = json!({"checker": "integer_sum_v1", "candidates": [candidate("sum")]});
    let typed = status(&Command::Typing(request.to_string()));
    assert_eq!(typed["status"], "PASS");
    assert_eq!(
        typed["result"]["candidates"][0]["licensed_as"],
        "integer_list_sum"
    );
}

#[test]
fn the_command_rechecks_a_grounding_file_and_types_a_candidate_file() {
    let directory =
        std::env::temp_dir().join(format!("pfp_operad_grounding_{}", std::process::id()));
    std::fs::create_dir_all(&directory).expect("scratch directory");
    let bad = directory.join("bad.json");
    let broken = edited(|r| r["slot_report"]["concrete_spans"]["value"]["literal"] = json!([]));
    std::fs::write(&bad, broken.to_string()).expect("written");
    let list = directory.join("list.json");
    let request = json!({"checker": "integer_sum_v1", "candidates": [candidate("sum")]});
    std::fs::write(&list, request.to_string()).expect("written");
    let run = |args: &[&str]| {
        let output = Process::new(env!("CARGO_BIN_EXE_pfp_operad"))
            .args(args)
            .output()
            .expect("the command runs");
        let line: Value = serde_json::from_slice(&output.stdout).unwrap_or(Value::Null);
        (output.status.code(), line)
    };
    let example = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/grounding.json");
    let (code, line) = run(&["grounding", example.to_str().expect("utf-8 path")]);
    assert_eq!((code, &line["status"]), (Some(0), &json!("PASS")));
    let (code, line) = run(&["grounding", bad.to_str().expect("utf-8 path")]);
    assert_eq!((code, &line["status"]), (Some(1), &json!("FAIL")));
    let (code, line) = run(&["typing", list.to_str().expect("utf-8 path")]);
    assert_eq!(
        (code, &line["result"]["candidates"][0]["typed"]),
        (Some(0), &json!(true))
    );
    assert_eq!(run(&["grounding"]).0, Some(2));
    assert_eq!(run(&["typing"]).0, Some(2));
    std::fs::remove_dir_all(&directory).expect("scratch removed");
}
