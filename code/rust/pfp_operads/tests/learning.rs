//! Ledger records the host writes itself: a witnessed failure and a scored trial.

use std::process::Command as Process;

use pfp_operads::host::{respond, Command};
use pfp_operads::learning::{trial, witness, HOST_REFUSAL, WRONG_RESULT};
use pfp_operads::ledger::{Ledger, Record, Status};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

/// A witness request written as text, so the case and the answer reach the host as given.
fn seen(values: &str, answer: &str, rest: &str) -> String {
    format!(
        r#"{{"id":"f1","workflow":"WF1","run":"run-7","checker":"integer_sum_v1","case":{{"values":{values}}},"answer":{answer}{rest}}}"#
    )
}

fn failure(values: &str, answer: &str, rest: &str) -> Value {
    let witnessed = witness(&seen(values, answer, rest)).expect("witnessed");
    serde_json::to_value(witnessed.record).expect("encodes")
}

fn sha256(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

#[test]
fn a_rejected_answer_becomes_a_failure_record_bound_to_what_was_seen() {
    let evidence = sha256(
        "pfp.operads.failure-evidence.v1\ninteger_sum_v1\n{\"values\":[17,25,-4]}\n{\"total\":46}\n",
    );
    assert_eq!(
        failure("[17,25,-4]", r#"{"total":46}"#, ""),
        json!({
            "kind": "failure",
            "id": "f1",
            "workflow": "WF1",
            "run": "run-7",
            "failure_class": "CounterfeitExactness",
            "ddc_trace": "M",
            "evidence_sha256": evidence
        })
    );
    assert_eq!((WRONG_RESULT, HOST_REFUSAL), ("CounterfeitExactness", "M"));
}

#[test]
fn the_evidence_hash_separates_checker_case_and_answer() {
    let hash = |values: &str, answer: &str| {
        failure(values, answer, "")["evidence_sha256"]
            .as_str()
            .expect("a hash")
            .to_owned()
    };
    let base = hash("[1,2]", r#"{"total":4}"#);
    assert_eq!(base, hash("[1,2]", r#"{"total":4}"#));
    assert_ne!(base, hash("[1,2]", r#"{"total":5}"#));
    assert_ne!(base, hash("[2,1]", r#"{"total":4}"#));
    // The parts are kept apart: moving a character from the case to the answer changes the hash.
    assert_eq!(
        base,
        sha256(
            "pfp.operads.failure-evidence.v1\ninteger_sum_v1\n{\"values\":[1,2]}\n{\"total\":4}\n"
        )
    );
}

#[test]
fn the_hosts_refusal_closes_the_replys_own_ddc_word() {
    let record = failure("[1,2]", "null", r#","reply_trace":"CRΛ""#);
    assert_eq!(record["ddc_trace"], "CRΛM");
    // The ledger, not this builder, decides whether the word is lawful.
    let record: Record =
        serde_json::from_value(failure("[1,2]", "null", r#","reply_trace":"CX""#)).expect("typed");
    assert_eq!(
        Ledger::new().append(record).expect_err("refused").code,
        "BAD_DDC_TRACE"
    );
}

#[test]
fn a_correct_answer_cannot_be_recorded_as_a_failure() {
    let code = |text: String| witness(&text).expect_err("refused").code;
    assert_eq!(
        code(seen("[17,25,-4]", r#"{"total":38}"#, "")),
        "NOT_A_FAILURE"
    );
    assert_eq!(code(seen("[1,2.5]", r#"{"total":3}"#, "")), "BAD_CASE");
    assert_eq!(
        code(seen("[1,2]", r#"{"total":4}"#, "").replace("integer_sum_v1", "by_eye")),
        "UNKNOWN_CHECKER"
    );
    assert_eq!(
        code(seen(
            "[1,2]",
            r#"{"total":4}"#,
            r#","failure_class":"ToyPromotion""#
        )),
        "BAD_REQUEST"
    );
    assert_eq!(code("{}".to_owned()), "BAD_REQUEST");
}

fn scored(cases: Value) -> Value {
    let request = json!({"candidate": "a1", "checker": "integer_sum_v1", "cases": cases});
    serde_json::to_value(trial(&request.to_string()).expect("scored")).expect("encodes")
}

fn held_out(id: &str, baseline: Value, treated: Value) -> Value {
    json!({"id": id, "case": {"values": [9, -2]}, "baseline": baseline, "treated": treated})
}

#[test]
fn a_trial_is_scored_by_the_judge_case_by_case() {
    let right = json!({"total": 7});
    let wrong = json!({"total": 11});
    let report = scored(json!([
        held_out("h1", wrong.clone(), right.clone()),
        held_out("h2", wrong.clone(), wrong.clone()),
        held_out("h3", right.clone(), right.clone()),
        held_out("h4", right.clone(), wrong.clone()),
        held_out("h5", right.clone(), Value::Null)
    ]));
    assert_eq!(
        report["record"],
        json!({
            "kind": "trial",
            "candidate": "a1",
            "held_out": ["h1", "h2", "h3", "h4", "h5"],
            "baseline_correct": 3,
            "treated_correct": 2,
            "clean_panel_hits": 2
        })
    );
    assert_eq!(
        report["cases"],
        json!([
            {"id": "h1", "baseline": false, "treated": true},
            {"id": "h2", "baseline": false, "treated": false},
            {"id": "h3", "baseline": true, "treated": true},
            {"id": "h4", "baseline": true, "treated": false},
            {"id": "h5", "baseline": true, "treated": false}
        ])
    );
    assert_eq!(
        scored(json!([]))["record"],
        json!({
            "kind": "trial", "candidate": "a1", "held_out": [],
            "baseline_correct": 0, "treated_correct": 0, "clean_panel_hits": 0
        })
    );
}

#[test]
fn a_trial_the_judge_cannot_score_is_refused() {
    let code = |request: Value| trial(&request.to_string()).expect_err("refused").code;
    let case = held_out("h1", json!({"total": 7}), json!({"total": 7}));
    let request = |checker: &str, cases: Value| json!({"candidate": "a1", "checker": checker, "cases": cases});
    assert_eq!(
        code(request("by_eye", json!([case.clone()]))),
        "UNKNOWN_CHECKER"
    );
    let mut broken = case.clone();
    broken["case"] = json!({"values": ["nine"]});
    assert_eq!(code(request("integer_sum_v1", json!([broken]))), "BAD_CASE");
    let mut open = case.clone();
    open["correct"] = json!(true);
    assert_eq!(
        code(request("integer_sum_v1", json!([open]))),
        "BAD_REQUEST"
    );
    let mut counted = request("integer_sum_v1", json!([case]));
    counted["treated_correct"] = json!(1);
    assert_eq!(code(counted), "BAD_REQUEST");
}

fn record(value: &Value) -> Record {
    serde_json::from_value(value.clone()).expect("a ledger record")
}

#[test]
fn the_ledger_admits_a_rule_only_on_records_the_host_wrote() {
    let mut ledger = Ledger::new();
    ledger
        .append(record(&failure("[9,-2]", r#"{"total":11}"#, "")))
        .expect("a witnessed failure");
    let rule: Record = record(&json!({
        "kind": "candidate", "id": "a1", "capability_kind": "antibody",
        "constraint": "Keep the sign of every value.", "derived_from": ["f1"]
    }));
    ledger.append(rule).expect("a candidate");
    let right = json!({"total": 7});
    let wrong = json!({"total": 11});
    // No gain: the ledger rejects the rule and refuses its admission.
    let flat = scored(json!([held_out("h1", wrong.clone(), wrong.clone())]));
    let seq = ledger.append(record(&flat["record"])).expect("a trial").seq;
    assert_eq!(ledger.status("a1"), Some(Status::Rejected));
    let admission =
        |trial: u64| record(&json!({"kind": "admission", "candidate": "a1", "trial": trial}));
    assert_eq!(
        ledger.append(admission(seq)).expect_err("refused").code,
        "NOT_EARNED"
    );
    // A later trial that gains and breaks nothing earns it.
    let won = scored(json!([
        held_out("h2", wrong, right.clone()),
        held_out("h3", right.clone(), right)
    ]));
    let seq = ledger.append(record(&won["record"])).expect("a trial").seq;
    ledger.append(admission(seq)).expect("earned");
    assert_eq!(ledger.admitted().len(), 1);
    // A trial on the failure the rule came from is not held out.
    let reused = scored(json!([held_out("f1", json!(null), json!({"total": 7}))]));
    assert_eq!(
        ledger
            .append(record(&reused["record"]))
            .expect_err("refused")
            .code,
        "SPLIT_OVERLAP"
    );
}

fn status(command: &Command) -> Value {
    serde_json::to_value(respond(command)).expect("encodes")
}

#[test]
fn respond_and_the_command_write_records_and_refuse_what_is_not_a_failure() {
    let wrong = seen("[1,2]", r#"{"total":4}"#, "");
    let right = seen("[1,2]", r#"{"total":3}"#, "");
    let pass = status(&Command::Witness(wrong.clone()));
    assert_eq!(pass["status"], "PASS");
    assert_eq!(pass["result"]["record"]["kind"], "failure");
    let refused = status(&Command::Witness(right.clone()));
    assert_eq!(refused["refusal"]["code"], "NOT_A_FAILURE");
    let trial_request =
        json!({"candidate": "a1", "checker": "integer_sum_v1", "cases": []}).to_string();
    let scored = status(&Command::Trial(trial_request.clone()));
    assert_eq!(scored["status"], "PASS");
    assert_eq!(scored["result"]["record"]["kind"], "trial");

    let directory =
        std::env::temp_dir().join(format!("pfp_operad_learning_{}", std::process::id()));
    std::fs::create_dir_all(&directory).expect("scratch directory");
    let run = |command: &str, name: &str, text: &str| {
        let path = directory.join(name);
        std::fs::write(&path, text).expect("written");
        let output = Process::new(env!("CARGO_BIN_EXE_pfp_operad"))
            .args([command, path.to_str().expect("utf-8 path")])
            .output()
            .expect("the command runs");
        let line: Value = serde_json::from_slice(&output.stdout).unwrap_or(Value::Null);
        (output.status.code(), line["status"].clone())
    };
    assert_eq!(
        run("witness", "wrong.json", &wrong),
        (Some(0), json!("PASS"))
    );
    assert_eq!(
        run("witness", "right.json", &right),
        (Some(1), json!("REFUSED"))
    );
    assert_eq!(
        run("trial", "trial.json", &trial_request),
        (Some(0), json!("PASS"))
    );
    assert_eq!(run("trial", "bad.json", "{}"), (Some(1), json!("REFUSED")));
    std::fs::remove_dir_all(&directory).expect("scratch removed");
}

#[test]
fn the_shipped_examples_give_a_failure_and_a_winning_trial() {
    let example = |name: &str| {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("examples")
            .join(name);
        std::fs::read_to_string(path).expect("example")
    };
    let witnessed = witness(&example("witness.json")).expect("witnessed");
    assert!(matches!(witnessed.record, Record::Failure { .. }));
    let report =
        serde_json::to_value(trial(&example("trial.json")).expect("scored")).expect("encodes");
    assert_eq!(report["record"]["baseline_correct"], 1);
    assert_eq!(report["record"]["treated_correct"], 3);
    assert_eq!(report["record"]["clean_panel_hits"], 0);
}
