//! The host entry points and the `pfp_operad` command: typed requests in, one typed outcome out.
//!
//! AuthorityEffect: None.

use std::path::PathBuf;
use std::process::Command as Process;

use pfp_operads::host::{check, laws, respond, Command, Disposition, Outcome};
use serde_json::{json, Value};

fn sum_request() -> Value {
    json!({
        "colour_type": "prompt_colour",
        "operations": [
            {"id": "sum", "sources": ["RationalValue", "RationalValue"], "target": "TargetResult",
             "body": "sum", "variant": "Symmetric", "cost": 1},
            {"id": "explain", "sources": ["TargetResult"], "target": "RawTextSpan"}
        ],
        "ddc_moves": [
            {"id": "m1", "op": "C"},
            {"id": "m2", "op": "Λ", "operad_id": "sum"},
            {"id": "m3", "op": "T", "operad_id": "sum"}
        ],
        "checks": [{"operation": "sum", "inputs": [17, 21], "expected": 38}]
    })
}

fn codes(request: &Value) -> Vec<&'static str> {
    check(&request.to_string())
        .unwrap()
        .findings
        .iter()
        .map(|found| found.code)
        .collect()
}

fn dispositions(request: &Value) -> Vec<(String, Disposition)> {
    let report = check(&request.to_string()).unwrap();
    report
        .operations
        .into_iter()
        .map(|status| (status.id, status.disposition))
        .collect()
}

#[test]
fn a_candidate_with_a_body_and_a_passing_host_check_is_verified() {
    let report = check(&sum_request().to_string()).unwrap();
    assert!(report.accepted && report.findings.is_empty());
    assert_eq!(report.ddc_trace, "CΛT");
    assert_eq!(
        dispositions(&sum_request()),
        vec![
            ("sum".to_owned(), Disposition::HostVerified),
            ("explain".to_owned(), Disposition::UnverifiedCandidate)
        ]
    );
    let mut unchecked = sum_request();
    unchecked["checks"] = json!([]);
    assert_eq!(
        dispositions(&unchecked)[0].1,
        Disposition::UnverifiedCandidate
    );
    let mut bodiless = sum_request();
    bodiless["operations"][0]
        .as_object_mut()
        .unwrap()
        .remove("body");
    assert_eq!(codes(&bodiless), vec!["NO_BODY"]);
}

#[test]
fn a_wrong_answer_or_a_colour_outside_the_canon_is_refused() {
    let mut wrong = sum_request();
    wrong["checks"][0]["expected"] = json!(39);
    assert_eq!(codes(&wrong), vec!["CHECK_FAILED"]);
    assert_eq!(dispositions(&wrong)[0].1, Disposition::Refused);
    assert_eq!(dispositions(&wrong)[1].1, Disposition::UnverifiedCandidate);
    assert!(!check(&wrong.to_string()).unwrap().accepted);

    let mut shape = sum_request();
    shape["checks"][0]["inputs"] = json!([17, [21]]);
    assert_eq!(codes(&shape), vec!["VALUE_SHAPE"]);

    let mut foreign = sum_request();
    foreign["operations"][0]["sources"] = json!(["Integer", "Integer"]);
    assert_eq!(
        codes(&foreign),
        vec![
            "UNKNOWN_COLOUR",
            "UNKNOWN_OPERATION",
            "UNKNOWN_OPERATION",
            "UNKNOWN_OPERATION"
        ]
    );
    assert_eq!(dispositions(&foreign)[0].1, Disposition::Refused);

    let mut family = sum_request();
    family["colour_type"] = json!("severity");
    assert_eq!(codes(&family)[0], "UNKNOWN_COLOUR_TYPE");
}

#[test]
fn ids_letters_and_references_are_checked() {
    let mut twice = sum_request();
    twice["operations"][1]["id"] = json!("sum");
    let found = codes(&twice);
    assert_eq!(found[0], "DUPLICATE_OPERATION");
    assert_eq!(
        dispositions(&twice),
        vec![("sum".to_owned(), Disposition::Refused)]
    );

    let mut moves = sum_request();
    moves["ddc_moves"] = json!([
        {"id": "m1", "op": "C"}, {"id": "m1", "op": "X"}, {"id": "sum", "op": "T", "operad_id": "ghost"}
    ]);
    let report = check(&moves.to_string()).unwrap();
    let found: Vec<_> = report
        .findings
        .iter()
        .map(|f| (f.code, f.scope, f.subject.as_str()))
        .collect();
    assert_eq!(
        found,
        vec![
            ("DUPLICATE_DDC_MOVE", "ddc_move", "m1"),
            ("UNKNOWN_DDC_LETTER", "ddc_move", "m1"),
            ("UNKNOWN_OPERATION", "ddc_move", "sum")
        ]
    );
    assert_eq!(report.ddc_trace, "CT");
    assert_eq!(
        report.operations[0].disposition,
        Disposition::HostVerified,
        "a move named like an operation does not blame it"
    );
    assert!(!report.accepted);

    let mut alias = sum_request();
    alias["ddc_moves"][1]["op"] = json!("Lambda");
    assert_eq!(codes(&alias), vec!["UNKNOWN_DDC_LETTER"]);
}

#[test]
fn requests_are_closed_and_typed() {
    let mut extra = sum_request();
    extra["note"] = json!("hello");
    assert_eq!(check(&extra.to_string()).unwrap_err().code, "BAD_REQUEST");
    let mut float = sum_request();
    float["checks"][0]["inputs"] = json!([17.5, 21]);
    assert_eq!(check(&float.to_string()).unwrap_err().code, "BAD_REQUEST");
    assert_eq!(check("not json").unwrap_err().code, "BAD_REQUEST");
    assert_eq!(
        laws(&sum_request().to_string()).unwrap_err().code,
        "BAD_REQUEST"
    );
}

fn laws_request(variant: &str) -> Value {
    json!({
        "colour_type": "prompt_colour",
        "operations": [
            {"id": "sub", "sources": ["RationalValue", "RationalValue"], "target": "RationalValue",
             "body": "difference", "variant": variant},
            {"id": "add", "sources": ["RationalValue", "RationalValue"], "target": "RationalValue",
             "body": "sum", "variant": "Symmetric"}
        ],
        "panel": {"RationalValue": [2, -3, 5]}
    })
}

#[test]
fn the_law_battery_runs_from_a_request() {
    let report = laws(&laws_request("Planar").to_string()).unwrap();
    assert!(report.holds());
    assert_eq!((report.unit, report.symmetry), (6, 1));
    assert_eq!(
        (report.sequential, report.parallel, report.composition),
        (32, 8, 8)
    );
    let lying = laws(&laws_request("Symmetric").to_string()).unwrap();
    assert_eq!(lying.violations.len(), 1);
    assert_eq!(lying.violations[0].operations, vec!["sub".to_owned()]);
    let mut unsampled = laws_request("Planar");
    unsampled["panel"] = json!({});
    assert_eq!(laws(&unsampled.to_string()).unwrap_err().code, "NO_SAMPLES");
    let mut foreign = laws_request("Planar");
    foreign["panel"] = json!({"Integer": [1]});
    assert_eq!(
        laws(&foreign.to_string()).unwrap_err().code,
        "UNKNOWN_COLOUR"
    );
    let mut untyped = laws_request("Planar");
    untyped["operations"][0]["target"] = json!("Integer");
    assert_eq!(
        laws(&untyped.to_string()).unwrap_err().code,
        "UNKNOWN_COLOUR"
    );
}

fn failure_record() -> String {
    json!({"kind": "failure", "id": "f1", "workflow": "WF2", "run": "r1", "failure_class": "FAKE_RECEIPT",
           "ddc_trace": "CM", "evidence_sha256": "a".repeat(64)})
    .to_string()
}

fn status(outcome: &Outcome) -> &'static str {
    match outcome {
        Outcome::Pass { .. } => "PASS",
        Outcome::Fail { .. } => "FAIL",
        Outcome::Refused { .. } => "REFUSED",
    }
}

#[test]
fn respond_reports_pass_fail_and_refused() {
    assert_eq!(
        status(&respond(&Command::Check(sum_request().to_string()))),
        "PASS"
    );
    assert_eq!(
        status(&respond(&Command::Laws(laws_request("Planar").to_string()))),
        "PASS"
    );
    let failed = respond(&Command::Laws(laws_request("Symmetric").to_string()));
    assert_eq!(status(&failed), "FAIL");
    let wire = serde_json::to_value(&failed).unwrap();
    assert_eq!(wire["status"], "FAIL");
    assert_eq!(wire["result"]["violations"][0]["law"], "symmetry");
    let mut wrong = sum_request();
    wrong["checks"][0]["expected"] = json!(0);
    assert_eq!(status(&respond(&Command::Check(wrong.to_string()))), "FAIL");
    let refused = serde_json::to_value(respond(&Command::Check("{}".to_owned()))).unwrap();
    assert_eq!(
        (
            refused["status"].as_str(),
            refused["refusal"]["code"].as_str()
        ),
        (Some("REFUSED"), Some("BAD_REQUEST"))
    );
}

#[test]
fn the_ledger_is_reachable_through_respond() {
    let Outcome::Pass { result: entry } = respond(&Command::LedgerAppend {
        ledger: String::new(),
        record: failure_record(),
    }) else {
        panic!("a lawful first record must be appended");
    };
    assert_eq!(entry["seq"], 0);
    let text = format!("{entry}\n");
    let Outcome::Pass { result } = respond(&Command::LedgerVerify(text.clone())) else {
        panic!("the appended line must verify");
    };
    assert_eq!(result, json!({"entries": 1}));
    let Outcome::Pass { result } = respond(&Command::LedgerAdmitted(text.clone())) else {
        panic!("an intact ledger must list its rules");
    };
    assert_eq!(result, json!([]));
    let again = respond(&Command::LedgerAppend {
        ledger: text.clone(),
        record: failure_record(),
    });
    assert_eq!(status(&again), "REFUSED");
    let unknown = respond(&Command::LedgerAppend {
        ledger: text.clone(),
        record: "{\"kind\":\"wish\"}".to_owned(),
    });
    assert_eq!(status(&unknown), "REFUSED");
    assert_eq!(
        status(&respond(&Command::LedgerVerify(text.replace("WF2", "WF3")))),
        "REFUSED"
    );
    assert_eq!(
        status(&respond(&Command::LedgerAdmitted("garbage".to_owned()))),
        "REFUSED"
    );
}

fn scratch(name: &str) -> PathBuf {
    let folder = std::env::temp_dir().join(format!("pfp_operad_{}_{name}", std::process::id()));
    let _ = std::fs::remove_dir_all(&folder);
    std::fs::create_dir_all(&folder).unwrap();
    folder
}

fn run(args: &[&str]) -> (i32, Value, String) {
    let output = Process::new(env!("CARGO_BIN_EXE_pfp_operad"))
        .args(args)
        .output()
        .unwrap();
    let stdout = serde_json::from_slice(&output.stdout).unwrap_or(Value::Null);
    (
        output.status.code().unwrap(),
        stdout,
        String::from_utf8_lossy(&output.stderr).into_owned(),
    )
}

#[test]
fn the_command_exits_0_1_or_2_and_prints_one_outcome() {
    let folder = scratch("exit");
    let path = |name: &str| folder.join(name).to_string_lossy().into_owned();
    std::fs::write(path("check.json"), sum_request().to_string()).unwrap();
    std::fs::write(path("laws.json"), laws_request("Planar").to_string()).unwrap();
    std::fs::write(path("lying.json"), laws_request("Symmetric").to_string()).unwrap();
    let (code, out, _) = run(&["check", &path("check.json")]);
    assert_eq!((code, out["status"].as_str()), (0, Some("PASS")));
    assert_eq!(
        out["result"]["operations"][0]["disposition"],
        "HOST_VERIFIED"
    );
    assert_eq!(run(&["laws", &path("laws.json")]).0, 0);
    let (code, out, _) = run(&["laws", &path("lying.json")]);
    assert_eq!((code, out["status"].as_str()), (1, Some("FAIL")));
    let (code, out, _) = run(&["check", &path("laws.json")]);
    assert_eq!((code, out["status"].as_str()), (1, Some("REFUSED")));
    let (code, out, err) = run(&["check", &path("missing.json")]);
    assert_eq!((code, out), (2, Value::Null));
    assert!(err.contains("cannot read"));
    for bad in [
        &[][..],
        &["laws"][..],
        &["ledger", "burn", "x"][..],
        &["check", "a", "b"][..],
    ] {
        let (code, _, err) = run(bad);
        assert_eq!(code, 2);
        assert!(err.contains("usage: pfp_operad"));
    }
    std::fs::remove_dir_all(folder).unwrap();
}

#[test]
fn the_command_appends_only_lawful_records_to_the_ledger_file() {
    let folder = scratch("ledger");
    let path = |name: &str| folder.join(name).to_string_lossy().into_owned();
    let ledger = path("failures.jsonl");
    std::fs::write(path("failure.json"), failure_record()).unwrap();
    let (code, out, _) = run(&["ledger", "append", &ledger, &path("failure.json")]);
    assert_eq!((code, out["result"]["seq"].as_u64()), (0, Some(0)));
    let (code, out, _) = run(&["ledger", "append", &ledger, &path("failure.json")]);
    assert_eq!(
        (code, out["refusal"]["code"].as_str()),
        (1, Some("DUPLICATE_ID"))
    );
    assert_eq!(std::fs::read_to_string(&ledger).unwrap().lines().count(), 1);
    let rule = json!({"kind": "candidate", "id": "a1", "capability_kind": "anti_skill",
                      "constraint": "Never cite a receipt you did not compute.", "derived_from": ["f1"]});
    let trial = json!({"kind": "trial", "candidate": "a1", "held_out": ["h1", "h2"],
                       "baseline_correct": 0, "treated_correct": 2, "clean_panel_hits": 0});
    let admit = json!({"kind": "admission", "candidate": "a1", "trial": 2});
    for (name, record) in [
        ("rule.json", rule),
        ("trial.json", trial),
        ("admit.json", admit),
    ] {
        std::fs::write(path(name), record.to_string()).unwrap();
        assert_eq!(run(&["ledger", "append", &ledger, &path(name)]).0, 0);
    }
    let (code, out, _) = run(&["ledger", "verify", &ledger]);
    assert_eq!((code, out["result"]["entries"].as_u64()), (0, Some(4)));
    let (code, out, _) = run(&["ledger", "admitted", &ledger]);
    assert_eq!(code, 0);
    assert_eq!(
        out["result"],
        json!([{"id": "a1", "capability_kind": "anti_skill",
                                      "constraint": "Never cite a receipt you did not compute."}])
    );
    let tampered = std::fs::read_to_string(&ledger)
        .unwrap()
        .replace("Never cite", "Always cite");
    std::fs::write(&ledger, tampered).unwrap();
    let (code, out, _) = run(&["ledger", "verify", &ledger]);
    assert_eq!(
        (code, out["refusal"]["code"].as_str()),
        (1, Some("CHAIN_BROKEN"))
    );
    assert_eq!(run(&["ledger", "verify", &path("absent.jsonl")]).0, 2);
    assert_eq!(
        run(&["ledger", "append", &ledger, &path("absent.json")]).0,
        2
    );
    std::fs::remove_dir_all(folder).unwrap();
}

#[test]
fn defaults_are_planar_and_the_declared_cost_is_used() {
    let mut defaulted = laws_request("Planar");
    defaulted["operations"][0]
        .as_object_mut()
        .unwrap()
        .remove("variant");
    let report = laws(&defaulted.to_string()).unwrap();
    assert!(report.holds());
    assert_eq!(report.symmetry, 1);
    let mut dear = laws_request("Planar");
    dear["operations"] = json!([
        {"id": "dear", "sources": ["RationalValue"], "target": "RationalValue", "cost": u64::MAX}
    ]);
    assert_eq!(laws(&dear.to_string()).unwrap_err().code, "OVERFLOW");
}

#[test]
fn neither_copy_of_a_duplicated_operation_stays_typed() {
    let mut twice = sum_request();
    twice["operations"][1]["id"] = json!("sum");
    let unknown = "UNKNOWN_OPERATION";
    assert_eq!(
        codes(&twice),
        vec!["DUPLICATE_OPERATION", unknown, unknown, unknown]
    );
}

#[test]
fn the_shipped_examples_pass() {
    let example = |name: &str| {
        let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("examples")
            .join(name);
        std::fs::read_to_string(path).unwrap()
    };
    assert_eq!(
        status(&respond(&Command::Check(example("check.json")))),
        "PASS"
    );
    assert_eq!(
        status(&respond(&Command::Laws(example("laws.json")))),
        "PASS"
    );
    let append = Command::LedgerAppend {
        ledger: String::new(),
        record: example("failure.json"),
    };
    assert_eq!(status(&respond(&append)), "PASS");
}
