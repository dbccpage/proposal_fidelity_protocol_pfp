//! The reply envelope: the structure rules in their fixed order, then the canon typing.

use std::process::Command as Process;

use core_operad_canon::type_by_id;
use pfp_operads::envelope::{envelope, TaskValueColour, COLOUR_TYPE, LICENSED};
use pfp_operads::host::{respond, Command};
use serde_json::{json, Value};

fn slot(name: &str) -> Value {
    json!({"slot": name, "disposition": "provided", "value": "stated", "reason": ""})
}

fn candidate(id: &str) -> Value {
    json!({
        "id": id,
        "operation": "sum the inputs",
        "source_colours": ["IntegerList"],
        "target_colour": "Integer",
        "arity": 1,
        "source": {"kind": "seed_prompt", "quote": "input.values"},
        "witness_refs": ["task_result"]
    })
}

fn step(id: &str, op: &str) -> Value {
    json!({
        "id": id,
        "op": op,
        "operad_id": "sum",
        "before": "input list",
        "after": "proposed sum",
        "local_log": "candidate total emitted",
        "refusal": null,
        "witness_refs": ["task_result"]
    })
}

/// A reply with nothing wrong: three slots, one licensed candidate, one move.
fn lawful() -> Value {
    json!({
        "catalogue": ["carrier", "operands", "terminal"],
        "required": ["carrier", "terminal"],
        "sources": {
            "seed_prompt": "Add every integer in input.values.",
            "input_json": "{\"values\":[17,25,-4]}"
        },
        "checker": "integer_sum_v1",
        "answer": {
            "task_result": {"total": 38},
            "slot_report": [slot("carrier"), slot("operands"), slot("terminal")],
            "operad_candidates": [candidate("sum")],
            "ddc_moves": [step("t1", "T")]
        }
    })
}

fn errors(request: &Value) -> Vec<String> {
    envelope(&request.to_string()).expect("readable").errors
}

fn edited(edit: impl FnOnce(&mut Value)) -> Value {
    let mut request = lawful();
    edit(&mut request);
    request
}

fn refused(request: &Value) -> &'static str {
    envelope(&request.to_string()).expect_err("refused").code
}

#[test]
fn a_lawful_reply_is_accepted_typed_and_bound_to_the_licensed_operation() {
    let report = envelope(&lawful().to_string()).expect("readable");
    assert!(report.accepted);
    assert_eq!(report.errors, Vec::<String>::new());
    assert_eq!(report.ddc_trace, "T");
    assert_eq!(
        serde_json::to_value(&report.candidates).expect("encodes"),
        json!([{"id": "sum", "typed": true, "licensed_as": "integer_list_sum"}])
    );
}

#[test]
fn every_catalogue_slot_is_reported_exactly_once() {
    let missing = edited(|r| {
        r["answer"]["slot_report"] = json!([slot("carrier"), slot("terminal")]);
    });
    let twice = edited(|r| {
        r["answer"]["slot_report"] = json!([
            slot("carrier"),
            slot("carrier"),
            slot("operands"),
            slot("terminal")
        ]);
    });
    let stranger = edited(|r| {
        r["answer"]["slot_report"] = json!([
            slot("carrier"),
            slot("operands"),
            slot("terminal"),
            slot("extra")
        ]);
    });
    for request in [missing, twice, stranger] {
        assert_eq!(errors(&request), ["SLOT_COVERAGE_OR_DUPLICATES"]);
    }
}

#[test]
fn a_provided_slot_has_a_value_and_any_other_slot_has_only_a_reason() {
    let row = |disposition: &str, value: &str, reason: &str| {
        edited(|r| {
            r["answer"]["slot_report"][1] = json!({
                "slot": "operands", "disposition": disposition, "value": value, "reason": reason
            });
        })
    };
    assert_eq!(
        errors(&row("provided", " \t\u{1f}", "")),
        ["EMPTY_PROVIDED_SLOT:operands"]
    );
    assert_eq!(errors(&row("provided", "x", "")), Vec::<String>::new());
    assert_eq!(
        errors(&row("not_applicable", "x", "does not apply")),
        ["MISSING_SLOT_REASON:operands"]
    );
    assert_eq!(
        errors(&row("unresolved", "", " \u{1c}")),
        ["MISSING_SLOT_REASON:operands"]
    );
    assert_eq!(
        errors(&row("unresolved", " ", "not stated")),
        ["MISSING_SLOT_REASON:operands"]
    );
    assert_eq!(
        errors(&row("unresolved", "", "not stated")),
        Vec::<String>::new()
    );
    assert_eq!(
        errors(&row("not_applicable", "", "does not apply")),
        Vec::<String>::new()
    );
}

#[test]
fn a_required_slot_must_be_provided() {
    let request = edited(|r| {
        r["answer"]["slot_report"][0] = json!({
            "slot": "carrier", "disposition": "unresolved", "value": "", "reason": "unknown"
        });
    });
    assert_eq!(errors(&request), ["REQUIRED_SLOT_UNRESOLVED:carrier"]);
}

#[test]
fn a_candidate_states_its_arity_quotes_a_source_and_cites_known_things() {
    let with =
        |field: &str, value: Value| edited(|r| r["answer"]["operad_candidates"][0][field] = value);
    assert_eq!(errors(&with("arity", json!(2))), ["ARITY_MISMATCH:sum"]);
    assert_eq!(errors(&with("arity", json!(1.5))), ["ARITY_MISMATCH:sum"]);
    assert_eq!(errors(&with("arity", json!("1"))), ["ARITY_MISMATCH:sum"]);
    assert_eq!(errors(&with("arity", json!(-1))), ["ARITY_MISMATCH:sum"]);
    assert!(errors(&with("arity", json!(1.0))).is_empty());
    assert_eq!(errors(&with("arity", json!(0))), ["ARITY_MISMATCH:sum"]);
    assert_eq!(
        errors(&with(
            "source",
            json!({"kind": "seed_prompt", "quote": "[17,25,-4]"})
        )),
        ["SOURCE_QUOTE_MISSING:sum"]
    );
    assert_eq!(
        errors(&with(
            "source",
            json!({"kind": "input_json", "quote": "[17,25,-4]"})
        )),
        Vec::<String>::new()
    );
    assert_eq!(
        errors(&with(
            "source",
            json!({"kind": "wiki", "quote": "input.values"})
        )),
        ["SOURCE_QUOTE_MISSING:sum"]
    );
    assert_eq!(
        errors(&with("witness_refs", json!(["task_result", "elsewhere"]))),
        ["UNKNOWN_WITNESS_REF:sum"]
    );
    assert_eq!(
        errors(&with(
            "witness_refs",
            json!(["carrier", "sum", "task_result"])
        )),
        Vec::<String>::new()
    );
}

#[test]
fn a_repeated_candidate_id_is_an_error_and_both_copies_are_listed() {
    let request = edited(|r| {
        r["answer"]["operad_candidates"] = json!([candidate("sum"), candidate("sum")]);
    });
    let report = envelope(&request.to_string()).expect("readable");
    assert_eq!(report.errors, ["DUPLICATE_OPERAD_ID"]);
    assert_eq!(report.candidates.len(), 2);
}

#[test]
fn a_move_is_logged_or_refused_and_names_only_known_things() {
    let with = |field: &str, value: Value| edited(|r| r["answer"]["ddc_moves"][0][field] = value);
    assert_eq!(
        errors(&with("local_log", Value::Null)),
        ["DDC_LOG_OR_REFUSAL_REQUIRED:t1"]
    );
    assert_eq!(
        errors(&with("local_log", json!(" \n"))),
        ["DDC_LOG_OR_REFUSAL_REQUIRED:t1"]
    );
    let refusal_only = edited(|r| {
        r["answer"]["ddc_moves"][0]["local_log"] = Value::Null;
        r["answer"]["ddc_moves"][0]["refusal"] = json!("out of budget");
    });
    assert_eq!(errors(&refusal_only), Vec::<String>::new());
    assert_eq!(
        errors(&with("operad_id", json!("product"))),
        ["UNKNOWN_OPERAD_REF:t1"]
    );
    assert_eq!(
        errors(&with("operad_id", Value::Null)),
        Vec::<String>::new()
    );
    assert_eq!(
        errors(&with("witness_refs", json!(["nowhere"]))),
        ["UNKNOWN_WITNESS_REF:t1"]
    );
    let twice = edited(|r| {
        r["answer"]["ddc_moves"] = json!([step("t1", "T"), step("t1", "T")]);
    });
    assert_eq!(errors(&twice), ["DUPLICATE_DDC_ID"]);
}

#[test]
fn the_ddc_word_keeps_reply_order_and_only_canon_letters() {
    let request = edited(|r| {
        r["answer"]["ddc_moves"] = json!([
            step("m1", "C"),
            step("m2", "Λ"),
            step("m3", "Meta"),
            step("m4", "T")
        ]);
    });
    let report = envelope(&request.to_string()).expect("readable");
    assert_eq!(report.ddc_trace, "CΛT");
    assert_eq!(report.errors, ["UNKNOWN_DDC_LETTER:m3"]);
    assert!(!report.accepted);
}

#[test]
fn errors_come_in_the_fixed_order() {
    let request = edited(|r| {
        r["answer"]["slot_report"] = json!([
            {"slot": "carrier", "disposition": "unresolved", "value": "x", "reason": ""},
            {"slot": "operands", "disposition": "provided", "value": "", "reason": ""}
        ]);
        let mut bad = candidate("sum");
        bad["arity"] = json!(3);
        bad["source"]["quote"] = json!("absent");
        bad["witness_refs"] = json!(["nowhere"]);
        r["answer"]["operad_candidates"] = json!([bad, candidate("sum")]);
        let mut wrong = step("t1", "Q");
        wrong["local_log"] = Value::Null;
        wrong["operad_id"] = json!("product");
        wrong["witness_refs"] = json!(["nowhere"]);
        r["answer"]["ddc_moves"] = json!([wrong, step("t1", "T")]);
    });
    assert_eq!(
        errors(&request),
        [
            "SLOT_COVERAGE_OR_DUPLICATES",
            "MISSING_SLOT_REASON:carrier",
            "REQUIRED_SLOT_UNRESOLVED:carrier",
            "EMPTY_PROVIDED_SLOT:operands",
            "DUPLICATE_OPERAD_ID",
            "ARITY_MISMATCH:sum",
            "SOURCE_QUOTE_MISSING:sum",
            "UNKNOWN_WITNESS_REF:sum",
            "DUPLICATE_DDC_ID",
            "DDC_LOG_OR_REFUSAL_REQUIRED:t1",
            "UNKNOWN_OPERAD_REF:t1",
            "UNKNOWN_WITNESS_REF:t1",
            "UNKNOWN_DDC_LETTER:t1",
        ]
    );
}

fn typing(sources: Value, target: &str, checker: &str) -> Value {
    let request = edited(|r| {
        let arity = sources.as_array().map_or(0, Vec::len);
        r["checker"] = json!(checker);
        r["answer"]["operad_candidates"][0]["source_colours"] = sources;
        r["answer"]["operad_candidates"][0]["target_colour"] = json!(target);
        r["answer"]["operad_candidates"][0]["arity"] = json!(arity);
    });
    let report = envelope(&request.to_string()).expect("readable");
    assert!(report.accepted, "typing never changes the verdict");
    serde_json::to_value(&report.candidates[0]).expect("encodes")
}

#[test]
fn a_candidate_is_typed_only_by_canon_colours_and_typing_never_changes_the_verdict() {
    let read = |typed: bool, licensed: Value| json!({"id": "sum", "typed": typed, "licensed_as": licensed});
    assert_eq!(
        typing(json!(["Z", "Z", "Z"]), "Z", "integer_sum_v1"),
        read(false, Value::Null)
    );
    assert_eq!(
        typing(json!(["IntegerList"]), "total", "integer_sum_v1"),
        read(false, Value::Null)
    );
    assert_eq!(
        typing(json!(["integers"]), "Integer", "integer_sum_v1"),
        read(false, Value::Null)
    );
    assert_eq!(
        typing(json!(["Integer", "Integer"]), "Integer", "integer_sum_v1"),
        read(true, Value::Null)
    );
}

#[test]
fn only_the_checkers_own_signature_is_licensed() {
    let licensed = |sources: Value, target: &str, checker: &str| {
        typing(sources, target, checker)["licensed_as"].clone()
    };
    assert_eq!(
        licensed(json!(["IntegerList"]), "Integer", "integer_sum_v1"),
        json!("integer_list_sum")
    );
    assert_eq!(
        licensed(json!(["IntegerList"]), "Integer", "schema_only"),
        Value::Null
    );
    assert_eq!(
        licensed(json!(["IntegerList"]), "IntegerList", "integer_sum_v1"),
        Value::Null
    );
    assert_eq!(
        licensed(json!(["Integer"]), "Integer", "integer_sum_v1"),
        Value::Null
    );
    assert_eq!(
        licensed(
            json!(["IntegerList", "IntegerList"]),
            "Integer",
            "integer_sum_v1"
        ),
        Value::Null
    );
    assert_eq!(
        licensed(json!([]), "Integer", "integer_sum_v1"),
        Value::Null
    );
}

#[test]
fn the_colours_and_the_licensed_table_are_the_canons() {
    let canon = type_by_id(COLOUR_TYPE).expect("the canon has the type");
    let names: Vec<&str> = TaskValueColour::ALL.iter().map(|c| c.as_str()).collect();
    assert_eq!(names, canon.values);
    assert!(canon.closed);
    assert_eq!(LICENSED.len(), 1);
    let sum = LICENSED[0];
    assert_eq!(
        (sum.name, sum.checker, sum.sources, sum.target),
        (
            "integer_list_sum",
            "integer_sum_v1",
            &[TaskValueColour::IntegerList][..],
            TaskValueColour::Integer
        )
    );
}

#[test]
fn a_request_is_closed_and_typed() {
    assert_eq!(refused(&edited(|r| r["extra"] = json!(1))), "BAD_REQUEST");
    assert_eq!(
        refused(&edited(
            |r| r["answer"]["slot_report"][0]["note"] = json!("x")
        )),
        "BAD_REQUEST"
    );
    assert_eq!(
        refused(&edited(|r| {
            r["answer"]["slot_report"][0]["disposition"] = json!("maybe");
        })),
        "BAD_REQUEST"
    );
    assert_eq!(
        refused(&edited(|r| {
            r["answer"]["operad_candidates"][0]["body"] = json!("sum");
        })),
        "BAD_REQUEST"
    );
    assert_eq!(
        refused(&edited(|r| {
            r["answer"]["operad_candidates"][0]["source"]["page"] = json!("one");
        })),
        "BAD_REQUEST"
    );
    assert_eq!(
        refused(&edited(|r| r["answer"]["ddc_moves"][0]["cost"] = json!(1))),
        "BAD_REQUEST"
    );
    assert_eq!(
        envelope("not json").expect_err("refused").code,
        "BAD_REQUEST"
    );
    // The answer itself may carry more, such as the task result.
    assert!(errors(&edited(|r| r["answer"]["notes"] = json!("kept"))).is_empty());
}

fn status(command: &Command) -> Value {
    serde_json::to_value(respond(command)).expect("encodes")
}

#[test]
fn respond_reports_the_envelope_and_the_version() {
    let pass = status(&Command::Envelope(lawful().to_string()));
    assert_eq!(pass["status"], "PASS");
    assert_eq!(pass["result"]["accepted"], true);
    let broken = edited(|r| r["answer"]["operad_candidates"][0]["arity"] = json!(4));
    let fail = status(&Command::Envelope(broken.to_string()));
    assert_eq!(fail["status"], "FAIL");
    assert_eq!(fail["result"]["errors"], json!(["ARITY_MISMATCH:sum"]));
    let refusal = status(&Command::Envelope("{}".to_owned()));
    assert_eq!(refusal["status"], "REFUSED");
    assert_eq!(refusal["refusal"]["code"], "BAD_REQUEST");
    assert_eq!(
        status(&Command::Version),
        json!({"status": "PASS", "result": {
            "name": "pfp_operads",
            "version": env!("CARGO_PKG_VERSION"),
            "canon": "core.operad-canon.v1"
        }})
    );
}

#[test]
fn the_command_reads_an_envelope_file_and_states_its_version() {
    let directory =
        std::env::temp_dir().join(format!("pfp_operad_envelope_{}", std::process::id()));
    std::fs::create_dir_all(&directory).expect("scratch directory");
    let good = directory.join("good.json");
    let bad = directory.join("bad.json");
    std::fs::write(&good, lawful().to_string()).expect("written");
    let broken = edited(|r| r["answer"]["ddc_moves"][0]["operad_id"] = json!("product"));
    std::fs::write(&bad, broken.to_string()).expect("written");
    let run = |args: &[&str]| {
        let output = Process::new(env!("CARGO_BIN_EXE_pfp_operad"))
            .args(args)
            .output()
            .expect("the command runs");
        let line: Value = serde_json::from_slice(&output.stdout).unwrap_or(Value::Null);
        (output.status.code(), line)
    };
    let (code, line) = run(&["envelope", good.to_str().expect("utf-8 path")]);
    assert_eq!((code, &line["status"]), (Some(0), &json!("PASS")));
    let (code, line) = run(&["envelope", bad.to_str().expect("utf-8 path")]);
    assert_eq!((code, &line["status"]), (Some(1), &json!("FAIL")));
    assert_eq!(line["result"]["errors"], json!(["UNKNOWN_OPERAD_REF:t1"]));
    let (code, line) = run(&["version"]);
    assert_eq!(
        (code, &line["result"]["name"]),
        (Some(0), &json!("pfp_operads"))
    );
    assert_eq!(run(&["envelope"]).0, Some(2));
    assert_eq!(run(&["version", "now"]).0, Some(2));
    std::fs::remove_dir_all(&directory).expect("scratch removed");
}

#[test]
fn the_shipped_example_is_accepted() {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/envelope.json");
    let report = envelope(&std::fs::read_to_string(path).expect("example")).expect("readable");
    assert!(report.accepted);
    assert_eq!(report.candidates[0].licensed_as, Some("integer_list_sum"));
}
