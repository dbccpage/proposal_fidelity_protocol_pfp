//! Candidates the host runs itself: a body from the closed list, the task's input, the judge's result.

use std::process::Command as Process;

use pfp_operads::host::{check, respond, Command};
use pfp_operads::running::{run, NONE_VERIFIED, REFUSED, VERIFIED};
use serde_json::{json, Value};

fn request(cases: Value, candidates: Value) -> String {
    json!({"checker": "integer_sum_v1", "cases": cases, "candidates": candidates}).to_string()
}

fn report(cases: Value, candidates: Value) -> Value {
    serde_json::to_value(run(&request(cases, candidates)).expect("ran")).expect("encodes")
}

fn candidate(id: &str, sources: &[&str], body: &str) -> Value {
    json!({"id": id, "sources": sources, "target": "Integer", "body": body})
}

/// The code each candidate was given, or `HOST_VERIFIED`.
fn outcomes(report: &Value) -> Vec<(String, String)> {
    report["candidates"]
        .as_array()
        .expect("rows")
        .iter()
        .map(|row| {
            let reason = row.get("code").unwrap_or(&row["disposition"]);
            (
                row["id"].as_str().expect("an id").to_owned(),
                reason.as_str().expect("text").to_owned(),
            )
        })
        .collect()
}

fn pair(id: &str, reason: &str) -> (String, String) {
    (id.to_owned(), reason.to_owned())
}

const THREE: [&str; 3] = ["Integer", "Integer", "Integer"];

#[test]
fn a_body_that_reproduces_the_judges_result_on_every_case_is_verified() {
    let found = report(
        json!([{"values": [17, 25, -4]}, {"values": [-9, 0, 9]}]),
        json!([
            candidate("list", &["IntegerList"], "sum_list"),
            candidate("each", &THREE, "sum")
        ]),
    );
    assert_eq!(
        found,
        json!({
            "accepted": true,
            "verdict": "CANDIDATE_VERIFIED",
            "verified": ["list", "each"],
            "candidates": [
                {"id": "list", "disposition": "HOST_VERIFIED"},
                {"id": "each", "disposition": "HOST_VERIFIED"}
            ]
        })
    );
    assert_eq!(
        (VERIFIED, REFUSED, NONE_VERIFIED),
        (
            "CANDIDATE_VERIFIED",
            "CANDIDATE_REFUSED",
            "NO_VERIFIED_CANDIDATE"
        )
    );
    // One value, one integer input; no values, no inputs.
    let single = report(
        json!([{"values": [7]}]),
        json!([candidate("one", &["Integer"], "sum")]),
    );
    assert_eq!(single["verified"], json!(["one"]));
    let empty = report(
        json!([{"values": []}]),
        json!([candidate("none", &[], "sum")]),
    );
    assert_eq!(empty["verified"], json!(["none"]));
}

#[test]
fn a_body_that_gives_another_result_is_refused() {
    let found = report(
        json!([{"values": [17, 25, -4]}]),
        json!([
            candidate("times", &THREE, "product"),
            candidate("list", &["IntegerList"], "sum_list"),
            {"id": "keep", "sources": ["IntegerList"], "target": "IntegerList", "body": "pack"}
        ]),
    );
    assert_eq!(found["accepted"], false);
    assert_eq!(found["verdict"], "CANDIDATE_REFUSED");
    assert_eq!(found["verified"], json!(["list"]));
    assert_eq!(
        found["candidates"][0],
        json!({
            "id": "times", "disposition": "REFUSED", "code": "RESULT_DIFFERS",
            "message": "case 0: the body gives -1700, not the judge's result"
        })
    );
    assert_eq!(
        found["candidates"][2]["message"],
        "case 0: the body gives [[17,25,-4]], not the judge's result"
    );
    let minus = report(
        json!([{"values": [9, 2]}]),
        json!([candidate("minus", &["Integer", "Integer"], "difference")]),
    );
    assert_eq!(outcomes(&minus), vec![pair("minus", "RESULT_DIFFERS")]);
}

#[test]
fn a_probe_case_exposes_a_body_that_agrees_by_coincidence() {
    let times = json!([candidate("times", &["Integer", "Integer"], "product")]);
    let alone = report(json!([{"values": [2, 2]}]), times.clone());
    assert_eq!(alone["verified"], json!(["times"]));
    let probed = report(json!([{"values": [2, 2]}, {"values": [3, 5]}]), times);
    assert_eq!(probed["verdict"], "CANDIDATE_REFUSED");
    assert_eq!(
        probed["candidates"][0]["message"],
        "case 1: the body gives 15, not the judge's result"
    );
    let same = json!([candidate("same", &["Integer"], "identity")]);
    assert_eq!(
        report(json!([{"values": [7]}]), same)["verified"],
        json!(["same"])
    );
}

#[test]
fn a_candidate_the_host_cannot_run_stays_unverified() {
    let cases = json!([{"values": [17, 25, -4]}]);
    let bare = json!({"id": "bare", "sources": ["IntegerList"], "target": "Integer"});
    let two = candidate("two", &["Integer", "Integer"], "sum");
    let found = report(cases.clone(), json!([bare.clone(), two.clone()]));
    assert_eq!(
        found,
        json!({
            "accepted": false,
            "verdict": "NO_VERIFIED_CANDIDATE",
            "verified": [],
            "candidates": [
                {"id": "bare", "disposition": "UNVERIFIED_CANDIDATE", "code": "NO_BODY",
                 "message": "the candidate names no body, so there is nothing to run"},
                {"id": "two", "disposition": "UNVERIFIED_CANDIDATE", "code": "DOES_NOT_FIT_CASE",
                 "message": "case 0: the candidate's inputs do not take the case's values"}
            ]
        })
    );
    // An unverified candidate does not block a verified one.
    let list = candidate("list", &["IntegerList"], "sum_list");
    let mixed = report(cases.clone(), json!([bare, list, two]));
    assert_eq!(
        (mixed["accepted"].clone(), mixed["verified"].clone()),
        (json!(true), json!(["list"]))
    );
    assert_eq!(report(cases, json!([]))["verdict"], "NO_VERIFIED_CANDIDATE");
    // A list is not one integer, and one integer each is not a list.
    let list_as_integer = report(
        json!([{"values": [7]}]),
        json!([candidate("x", &["IntegerList", "IntegerList"], "sum")]),
    );
    assert_eq!(
        outcomes(&list_as_integer),
        vec![pair("x", "DOES_NOT_FIT_CASE")]
    );
}

#[test]
fn a_wrong_result_on_one_case_outweighs_a_case_that_does_not_fit() {
    let cases = json!([{"values": [1, 2, 3]}, {"values": [3, 5]}, {"values": [4]}]);
    let found = report(
        cases,
        json!([
            candidate("times", &["Integer", "Integer"], "product"),
            candidate("plus", &["Integer", "Integer"], "sum")
        ]),
    );
    assert_eq!(
        found["candidates"],
        json!([
            {"id": "times", "disposition": "REFUSED", "code": "RESULT_DIFFERS",
             "message": "case 1: the body gives 15, not the judge's result"},
            {"id": "plus", "disposition": "UNVERIFIED_CANDIDATE", "code": "DOES_NOT_FIT_CASE",
             "message": "case 0: the candidate's inputs do not take the case's values"}
        ])
    );
    assert_eq!(found["verdict"], "CANDIDATE_REFUSED");
}

#[test]
fn an_ill_typed_candidate_is_refused_with_the_code_of_its_fault() {
    let found = report(
        json!([{"values": [17, 25, -4]}]),
        json!([
            {"id": "foreign", "sources": ["RationalValue"], "target": "Integer", "body": "sum"},
            candidate("three-way", &THREE, "difference"),
            {"id": "recolour", "sources": ["IntegerList"], "target": "Integer", "body": "identity"},
            candidate(" ", &["IntegerList"], "sum_list"),
            candidate("twice", &["IntegerList"], "sum_list"),
            candidate("twice", &["IntegerList"], "sum_list"),
            candidate("shape", &["IntegerList"], "sum"),
            candidate("list", &["IntegerList"], "sum_list")
        ]),
    );
    assert_eq!(
        outcomes(&found),
        vec![
            pair("foreign", "UNKNOWN_COLOUR"),
            pair("three-way", "ARITY"),
            pair("recolour", "COLOUR_MISMATCH"),
            pair(" ", "BAD_NAME"),
            pair("twice", "DUPLICATE_OPERATION"),
            pair("twice", "DUPLICATE_OPERATION"),
            pair("shape", "VALUE_SHAPE"),
            pair("list", "HOST_VERIFIED")
        ]
    );
    for row in found["candidates"].as_array().expect("rows").iter().take(7) {
        assert_eq!(row["disposition"], "REFUSED", "{row}");
    }
    assert_eq!(
        found["candidates"][6]["message"],
        "case 0: expected an integer, got a list"
    );
    assert_eq!(found["candidates"][4]["message"], "the id is used twice");
    assert_eq!(found["verdict"], "CANDIDATE_REFUSED");
    assert_eq!(found["verified"], json!(["list"]));
}

#[test]
fn a_body_that_overflows_is_refused_while_the_judge_stays_exact() {
    let found = report(
        json!([{"values": [9223372036854775807i64, 1]}]),
        json!([candidate("list", &["IntegerList"], "sum_list")]),
    );
    assert_eq!(outcomes(&found), vec![pair("list", "OVERFLOW")]);
    assert_eq!(found["candidates"][0]["disposition"], "REFUSED");
}

#[test]
fn a_request_the_host_cannot_run_is_refused() {
    let code = |text: String| run(&text).expect_err("refused").code;
    let list = json!([candidate("list", &["IntegerList"], "sum_list")]);
    assert_eq!(code(request(json!([]), list.clone())), "NO_CASES");
    let huge = r#"{"checker":"integer_sum_v1","cases":[{"values":[1]},{"values":[9223372036854775808]}],"candidates":[]}"#;
    let refusal = run(huge).expect_err("refused");
    assert_eq!(refusal.code, "CASE_OUT_OF_RANGE");
    assert_eq!(
        refusal.message,
        "a candidate is run on 64-bit integers and a case value does not fit"
    );
    let lowest = r#"{"checker":"integer_sum_v1","cases":[{"values":[-9223372036854775808]}],"candidates":[]}"#;
    assert!(run(lowest).is_ok());
    assert_eq!(
        code(request(json!([{"values": [1.5]}]), list.clone())),
        "BAD_CASE"
    );
    assert_eq!(
        code(request(json!([{"values": [1]}]), list.clone()).replace("integer_sum_v1", "by_eye")),
        "UNKNOWN_CHECKER"
    );
    // The caller cannot hand the host an expected value, a verdict or an unlisted body.
    let mut told =
        json!({"checker": "integer_sum_v1", "cases": [{"values": [1]}], "candidates": list});
    told["expected"] = json!(1);
    assert_eq!(code(told.to_string()), "BAD_REQUEST");
    let average = json!([candidate("mean", &["IntegerList"], "average")]);
    assert_eq!(
        code(request(json!([{"values": [1]}]), average)),
        "BAD_REQUEST"
    );
    let marked = json!([{"id": "a", "sources": ["IntegerList"], "target": "Integer",
                         "body": "sum_list", "disposition": "HOST_VERIFIED"}]);
    assert_eq!(
        code(request(json!([{"values": [1]}]), marked)),
        "BAD_REQUEST"
    );
    assert_eq!(code("[]".to_owned()), "BAD_REQUEST");
}

#[test]
fn task_value_colours_type_operations_for_every_host_command() {
    let typed = json!({
        "colour_type": "task_value_colour",
        "operations": [{"id": "add", "sources": ["IntegerList"], "target": "Integer", "body": "sum_list"}],
        "checks": [{"operation": "add", "inputs": [[4, 5]], "expected": 9}]
    });
    assert!(check(&typed.to_string()).expect("checked").accepted);
}

#[test]
fn respond_and_the_command_report_pass_fail_and_refused() {
    let cases = json!([{"values": [17, 25, -4]}]);
    let right = request(
        cases.clone(),
        json!([candidate("list", &["IntegerList"], "sum_list")]),
    );
    let wrong = request(
        cases.clone(),
        json!([candidate("times", &THREE, "product")]),
    );
    let none = request(cases, json!([]));
    let status = |text: &str| {
        serde_json::to_value(respond(&Command::Run(text.to_owned()))).expect("encodes")
    };
    assert_eq!(status(&right)["status"], "PASS");
    assert_eq!(status(&right)["result"]["verdict"], "CANDIDATE_VERIFIED");
    assert_eq!(status(&wrong)["status"], "FAIL");
    assert_eq!(status(&wrong)["result"]["verdict"], "CANDIDATE_REFUSED");
    assert_eq!(status(&none)["status"], "FAIL");
    assert_eq!(status("{}")["refusal"]["code"], "BAD_REQUEST");

    let directory = std::env::temp_dir().join(format!("pfp_operad_running_{}", std::process::id()));
    std::fs::create_dir_all(&directory).expect("scratch directory");
    let command = |name: &str, text: &str| {
        let path = directory.join(name);
        std::fs::write(&path, text).expect("written");
        let output = Process::new(env!("CARGO_BIN_EXE_pfp_operad"))
            .args(["run", path.to_str().expect("utf-8 path")])
            .output()
            .expect("the command runs");
        let line: Value = serde_json::from_slice(&output.stdout).unwrap_or(Value::Null);
        (output.status.code(), line["status"].clone())
    };
    assert_eq!(command("right.json", &right), (Some(0), json!("PASS")));
    assert_eq!(command("wrong.json", &wrong), (Some(1), json!("FAIL")));
    assert_eq!(command("open.json", "{}"), (Some(1), json!("REFUSED")));
    std::fs::remove_dir_all(&directory).expect("scratch removed");
}

#[test]
fn the_shipped_example_verifies_its_candidate() {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/run.json");
    let found = run(&std::fs::read_to_string(path).expect("example")).expect("ran");
    assert!(found.accepted);
    assert_eq!(found.verified, vec!["add-the-list".to_owned()]);
}
