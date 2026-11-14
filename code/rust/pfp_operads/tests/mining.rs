//! The mining screen and signature reuse.

use std::process::Command as Process;

use pfp_operads::grounding::SUM_SLOTS;
use pfp_operads::host::{respond, Command};
use pfp_operads::mining::{mining, reuse};
use serde_json::{json, Value};

fn candidate(id: &str) -> Value {
    json!({
        "id": id,
        "operation": "add every member of the list",
        "source_colours": ["IntegerList"],
        "target_colour": "Integer",
        "arity": 1,
        "source": {"kind": "seed_prompt", "quote": "input.values"},
        "witness_refs": ["task_result", "operands"]
    })
}

fn guidance(slot: &str) -> Value {
    json!({
        "slot": slot,
        "source": {"kind": "input_json", "quote": "values"},
        "guidance": "Copy the public input exactly."
    })
}

/// A mining reply with nothing wrong.
fn lawful() -> Value {
    json!({
        "catalogue": ["carrier", "operands", "terminal"],
        "sources": {
            "seed_prompt": "Add every integer in input.values.",
            "input_json": "{\"values\":\"<redacted>\"}"
        },
        "checker": "integer_sum_v1",
        "answer": {
            "operad_candidates": [candidate("sum")],
            "focus_slots": ["operands"],
            "failure_triggers": ["An operand is dropped."],
            "l2_guidance": SUM_SLOTS.iter().map(|slot| guidance(slot)).collect::<Vec<_>>()
        }
    })
}

fn edited(edit: impl FnOnce(&mut Value)) -> Value {
    let mut request = lawful();
    edit(&mut request);
    request
}

fn errors(request: &Value) -> Vec<String> {
    mining(&request.to_string()).expect("readable").errors
}

fn refused(request: &Value) -> &'static str {
    mining(&request.to_string()).expect_err("refused").code
}

#[test]
fn a_lawful_mining_reply_is_accepted_with_its_candidates_typed_and_located() {
    let report = mining(&lawful().to_string()).expect("readable");
    assert!(report.accepted && report.errors.is_empty());
    assert_eq!(
        serde_json::to_value(&report.candidates).expect("encodes"),
        json!([{
            "id": "sum",
            "pointer": "/answer/operad_candidates/0",
            "duplicate_of": null,
            "typed": true,
            "licensed_as": "integer_list_sum"
        }])
    );
}

#[test]
fn a_digit_outside_a_source_quote_is_refused_wherever_it_is() {
    let digit = |edit: fn(&mut Value)| errors(&edited(|r| edit(&mut r["answer"])));
    assert_eq!(
        digit(|a| a["operad_candidates"][0]["operation"] = json!("The total is 38")),
        ["NUMERICAL_GUIDANCE_FORBIDDEN:operad_candidates/0/operation"]
    );
    assert_eq!(
        digit(|a| a["l2_guidance"][2]["guidance"] = json!("about 4 values")),
        ["NUMERICAL_GUIDANCE_FORBIDDEN:l2_guidance/2/guidance"]
    );
    assert_eq!(
        digit(|a| a["failure_triggers"][0] = json!("off by 1")),
        ["NUMERICAL_GUIDANCE_FORBIDDEN:failure_triggers/0"]
    );
    // A digit in any script counts; a letter-like number sign does not.
    assert_eq!(
        digit(|a| a["failure_triggers"][0] = json!("total \u{0663}")),
        ["NUMERICAL_GUIDANCE_FORBIDDEN:failure_triggers/0"]
    );
    assert!(digit(|a| a["failure_triggers"][0] = json!("part \u{2167} of the list")).is_empty());
    // Numbers, booleans and null are not text.
    assert!(digit(|a| a["notes"] = json!([38, 3.5, true, null, {"n": -4}])).is_empty());
}

#[test]
fn a_source_quote_may_hold_digits_and_nothing_else_named_quote_may() {
    let quoted = edited(|r| {
        r["sources"]["seed_prompt"] = json!("Add the 3 integers in input.values.");
        r["answer"]["operad_candidates"][0]["source"]["quote"] = json!("the 3 integers");
    });
    assert!(errors(&quoted).is_empty());
    let loose = edited(|r| r["answer"]["notes"] = json!({"quote": "38", "source": "17"}));
    assert_eq!(
        errors(&loose),
        [
            "NUMERICAL_GUIDANCE_FORBIDDEN:notes/quote",
            "NUMERICAL_GUIDANCE_FORBIDDEN:notes/source"
        ]
    );
    let beside = edited(|r| r["answer"]["notes"] = json!({"source": {"page": "38"}}));
    assert_eq!(
        errors(&beside),
        ["NUMERICAL_GUIDANCE_FORBIDDEN:notes/source/page"]
    );
}

#[test]
fn digit_errors_come_in_the_order_the_reply_was_written() {
    let text = lawful().to_string().replacen(
        "\"answer\":{",
        "\"answer\":{\"zeta\":\"9\",\"alpha\":[\"x\",\"8\"],",
        1,
    );
    assert_eq!(
        mining(&text).expect("readable").errors,
        [
            "NUMERICAL_GUIDANCE_FORBIDDEN:zeta",
            "NUMERICAL_GUIDANCE_FORBIDDEN:alpha/1"
        ]
    );
}

#[test]
fn a_mined_candidate_states_its_arity_quotes_a_source_and_cites_slots_only() {
    let with = |field: &str, value: Value| {
        errors(&edited(|r| {
            r["answer"]["operad_candidates"][0][field] = value
        }))
    };
    assert_eq!(with("arity", json!(2)), ["MINED_ARITY_MISMATCH:sum"]);
    assert!(with("arity", json!(1.0)).is_empty());
    assert_eq!(
        with(
            "source",
            json!({"kind": "seed_prompt", "quote": "not in the seed"})
        ),
        ["MINED_SOURCE_QUOTE_MISSING:sum"]
    );
    assert_eq!(
        with("source", json!({"kind": "memory", "quote": "input.values"})),
        ["MINED_SOURCE_QUOTE_MISSING:sum"]
    );
    assert_eq!(
        with("witness_refs", json!(["invented"])),
        ["MINED_WITNESS_REF_UNKNOWN:sum"]
    );
    assert_eq!(
        with("witness_refs", json!(["operands", "invented"])),
        ["MINED_WITNESS_REF_UNKNOWN:sum"]
    );
    // Unlike a solver reply, a mining reply may not cite another candidate.
    let cites_candidate = edited(|r| {
        let mut other = candidate("other");
        other["operation"] = json!("another reading");
        other["witness_refs"] = json!(["sum"]);
        r["answer"]["operad_candidates"]
            .as_array_mut()
            .expect("a list")
            .push(other);
    });
    assert_eq!(
        errors(&cites_candidate),
        ["MINED_WITNESS_REF_UNKNOWN:other"]
    );
    assert!(with("witness_refs", json!([])).is_empty());
}

#[test]
fn a_repeated_candidate_is_an_error_and_points_at_its_first_copy() {
    let request = edited(|r| {
        let ops = r["answer"]["operad_candidates"]
            .as_array_mut()
            .expect("a list");
        let mut renamed = candidate("sum");
        renamed["operation"] = json!("a different reading");
        ops.push(renamed);
        ops.push(candidate("sum"));
        ops.push(candidate("total"));
        ops.push(candidate("sum"));
    });
    let report = mining(&request.to_string()).expect("readable");
    assert_eq!(report.errors, ["DUPLICATE_MINED_OPERAD_ID"]);
    let duplicates: Vec<_> = report
        .candidates
        .iter()
        .map(|row| row.duplicate_of.as_deref())
        .collect();
    let first = Some("/answer/operad_candidates/0");
    assert_eq!(duplicates, [None, None, first, None, first]);
    assert_eq!(report.candidates[3].pointer, "/answer/operad_candidates/3");
}

#[test]
fn guidance_covers_each_grounded_slot_once_and_quotes_a_source() {
    let guide = |edit: fn(&mut Vec<Value>)| {
        errors(&edited(|r| {
            edit(r["answer"]["l2_guidance"].as_array_mut().expect("a list"))
        }))
    };
    assert_eq!(
        guide(|rows| {
            rows.pop();
        }),
        ["MISSING_TASK_L2_GUIDANCE"]
    );
    assert_eq!(
        guide(|rows| rows[1] = rows[0].clone()),
        ["DUPLICATE_L2_GUIDANCE_SLOT", "MISSING_TASK_L2_GUIDANCE"]
    );
    assert_eq!(
        guide(|rows| rows.push(guidance("carrier"))),
        ["MISSING_TASK_L2_GUIDANCE"]
    );
    assert_eq!(
        guide(|rows| rows[0]["source"]["quote"] = json!("not a real input span")),
        ["L2_SOURCE_QUOTE_MISSING:concrete_spans"]
    );
    assert!(guide(|rows| rows.reverse()).is_empty());
    // A checker with no grounded slots asks for no guidance.
    let ungrounded = edited(|r| {
        r["checker"] = json!("schema_only");
        r["answer"]["l2_guidance"] = json!([]);
    });
    let report = mining(&ungrounded.to_string()).expect("readable");
    assert!(report.accepted);
    assert_eq!(report.candidates[0].licensed_as, None);
    let volunteered = edited(|r| {
        r["checker"] = json!("schema_only");
        r["answer"]["l2_guidance"] = json!([guidance("carrier")]);
    });
    assert!(errors(&volunteered).is_empty());
}

#[test]
fn errors_come_in_the_fixed_order() {
    let request = edited(|r| {
        let answer = &mut r["answer"];
        answer["failure_triggers"][0] = json!("off by 1");
        let mut bad = candidate("sum");
        bad["arity"] = json!(3);
        bad["source"]["quote"] = json!("absent");
        bad["witness_refs"] = json!(["nobody"]);
        answer["operad_candidates"]
            .as_array_mut()
            .expect("a list")
            .push(bad);
        answer["l2_guidance"][3]["source"]["quote"] = json!("absent");
        answer["l2_guidance"][1] = guidance("concrete_spans");
    });
    assert_eq!(
        errors(&request),
        [
            "NUMERICAL_GUIDANCE_FORBIDDEN:failure_triggers/0",
            "DUPLICATE_MINED_OPERAD_ID",
            "MINED_ARITY_MISMATCH:sum",
            "MINED_SOURCE_QUOTE_MISSING:sum",
            "MINED_WITNESS_REF_UNKNOWN:sum",
            "DUPLICATE_L2_GUIDANCE_SLOT",
            "MISSING_TASK_L2_GUIDANCE",
            "L2_SOURCE_QUOTE_MISSING:preservation_obligations"
        ]
    );
}

#[test]
fn a_mining_request_is_closed_and_typed() {
    assert_eq!(refused(&edited(|r| r["extra"] = json!(1))), "BAD_REQUEST");
    assert_eq!(
        refused(&edited(
            |r| r["answer"]["l2_guidance"][0]["extra"] = json!("")
        )),
        "BAD_REQUEST"
    );
    assert_eq!(
        refused(&edited(
            |r| r["answer"]["operad_candidates"][0]["cost"] = json!(0)
        )),
        "BAD_REQUEST"
    );
    assert_eq!(
        refused(&edited(|r| {
            r["answer"]
                .as_object_mut()
                .expect("a map")
                .remove("l2_guidance");
        })),
        "BAD_REQUEST"
    );
    assert_eq!(mining("not json").expect_err("refused").code, "BAD_REQUEST");
}

fn reused(mined: Value, emitted: Value) -> Vec<String> {
    reuse(&json!({"mined": mined, "emitted": emitted}).to_string())
        .expect("readable")
        .reused
}

#[test]
fn reuse_lists_emitted_candidates_with_a_mined_signature_in_emitted_order() {
    let mut pair = candidate("pair");
    pair["source_colours"] = json!(["Integer", "Integer"]);
    pair["arity"] = json!(2);
    let mut swapped = candidate("swapped");
    swapped["source_colours"] = json!(["Integer"]);
    swapped["target_colour"] = json!("IntegerList");
    let mut scalar = candidate("scalar");
    scalar["source_colours"] = json!(["Integer"]);
    assert_eq!(
        reused(
            json!([candidate("mined")]),
            json!([pair, candidate("b"), swapped, scalar, candidate("a")])
        ),
        ["b", "a"]
    );
    assert!(reused(json!([]), json!([candidate("a")])).is_empty());
}

#[test]
fn a_record_without_a_typed_signature_matches_nothing() {
    let with = |field: &str, value: Value| {
        let mut op = candidate("odd");
        op[field] = value;
        op
    };
    let odd = json!([
        with("arity", json!(1.0)),
        with("arity", json!("1")),
        with("arity", json!(true)),
        with("source_colours", json!("IntegerList")),
        with("source_colours", json!([1])),
        with("target_colour", json!(null)),
        json!("not a record"),
        json!({"id": "bare"})
    ]);
    assert!(reused(json!([candidate("mined")]), odd.clone()).is_empty());
    // Two records that both lack a signature do not match each other.
    assert!(reused(odd.clone(), odd).is_empty());
    // The stated arity is part of the signature even when it disagrees with the colours.
    let wide = with("arity", json!(2));
    assert!(reused(json!([candidate("mined")]), json!([wide.clone()])).is_empty());
    assert_eq!(reused(json!([wide.clone()]), json!([wide])), ["odd"]);
    assert_eq!(
        reuse("{\"mined\": []}").expect_err("refused").code,
        "BAD_REQUEST"
    );
    let open = json!({"mined": [], "emitted": [], "extra": true});
    assert_eq!(
        reuse(&open.to_string()).expect_err("refused").code,
        "BAD_REQUEST"
    );
}

fn status(command: &Command) -> Value {
    serde_json::to_value(respond(command)).expect("encodes")
}

#[test]
fn respond_reports_mining_and_reuse() {
    assert_eq!(
        status(&Command::Mining(lawful().to_string()))["status"],
        "PASS"
    );
    let broken = edited(|r| r["answer"]["operad_candidates"][0]["arity"] = json!(4));
    let fail = status(&Command::Mining(broken.to_string()));
    assert_eq!(fail["status"], "FAIL");
    assert_eq!(
        fail["result"]["errors"],
        json!(["MINED_ARITY_MISMATCH:sum"])
    );
    assert_eq!(fail["result"]["candidates"][0]["licensed_as"], json!(null));
    assert_eq!(
        status(&Command::Mining("{}".to_owned()))["refusal"]["code"],
        "BAD_REQUEST"
    );
    let request = json!({"mined": [candidate("m")], "emitted": [candidate("e")]});
    assert_eq!(
        status(&Command::Reuse(request.to_string())),
        json!({"status": "PASS", "result": {"reused": ["e"]}})
    );
}

#[test]
fn the_command_screens_a_mining_file_and_the_shipped_example() {
    let directory = std::env::temp_dir().join(format!("pfp_operad_mining_{}", std::process::id()));
    std::fs::create_dir_all(&directory).expect("scratch directory");
    let bad = directory.join("bad.json");
    let broken = edited(|r| r["answer"]["failure_triggers"][0] = json!("off by 1"));
    std::fs::write(&bad, broken.to_string()).expect("written");
    let pairs = directory.join("pairs.json");
    let request = json!({"mined": [candidate("m")], "emitted": [candidate("e")]});
    std::fs::write(&pairs, request.to_string()).expect("written");
    let run = |args: &[&str]| {
        let output = Process::new(env!("CARGO_BIN_EXE_pfp_operad"))
            .args(args)
            .output()
            .expect("the command runs");
        let line: Value = serde_json::from_slice(&output.stdout).unwrap_or(Value::Null);
        (output.status.code(), line)
    };
    let example = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/mining.json");
    let (code, line) = run(&["mining", example.to_str().expect("utf-8 path")]);
    assert_eq!((code, &line["status"]), (Some(0), &json!("PASS")));
    let (code, line) = run(&["mining", bad.to_str().expect("utf-8 path")]);
    assert_eq!((code, &line["status"]), (Some(1), &json!("FAIL")));
    let (code, line) = run(&["reuse", pairs.to_str().expect("utf-8 path")]);
    assert_eq!((code, &line["result"]["reused"]), (Some(0), &json!(["e"])));
    assert_eq!(run(&["mining"]).0, Some(2));
    assert_eq!(run(&["reuse"]).0, Some(2));
    std::fs::remove_dir_all(&directory).expect("scratch removed");
}
