//! The integer sum judge: the host's exact sum against the total a reply states.

use std::process::Command as Process;

use pfp_operads::host::{respond, Command};
use pfp_operads::judge::{judge, Verdict, INTEGER_SUM};
use serde_json::{json, Value};

/// A request written as text, so every digit and space reaches the judge as given.
fn request(values: &str, answer: &str) -> String {
    format!(r#"{{"checker":"integer_sum_v1","case":{{"values":{values}}},"answer":{answer}}}"#)
}

fn accepted(values: &str, answer: &str) -> bool {
    judge(&request(values, answer)).expect("judged").accepted
}

#[test]
fn the_exact_sum_is_accepted_and_any_other_total_is_not() {
    assert_eq!(INTEGER_SUM, "integer_sum_v1");
    assert_eq!(
        judge(&request("[17,25,-4]", r#"{"total":38}"#)),
        Ok(Verdict {
            accepted: true,
            reason: "Exact integer sum agrees."
        })
    );
    assert_eq!(
        judge(&request("[17,25,-4]", r#"{"total":39}"#)),
        Ok(Verdict {
            accepted: false,
            reason: "Incorrect integer sum."
        })
    );
    assert!(!accepted("[17,25,-4]", r#"{"total":-38}"#));
    assert!(accepted("[-5,2]", r#"{"total":-3}"#));
    assert!(accepted("[5,-5]", r#"{"total":0}"#));
    assert!(accepted("[5,-5]", r#"{"total":-0}"#));
    assert!(accepted("[7]", r#"{ "total" : 7 }"#));
    assert!(accepted("[]", r#"{"total":0}"#));
}

#[test]
fn only_an_object_holding_one_integer_total_can_be_accepted() {
    for answer in [
        r#"{"total":38.0}"#,
        r#"{"total":3.8e1}"#,
        r#"{"total":38e0}"#,
        r#"{"total":"38"}"#,
        r#"{"total":true}"#,
        r#"{"total":null}"#,
        r#"{"total":[38]}"#,
        r#"{"total":38,"note":"checked"}"#,
        r#"{"sum":38}"#,
        r#"{}"#,
        "38",
        "[38]",
        "null",
        r#""38""#,
    ] {
        assert!(!accepted("[17,25,-4]", answer), "{answer} was accepted");
    }
}

#[test]
fn integers_are_unbounded_and_exact() {
    let huge = "1".to_owned() + &"0".repeat(100);
    let values = format!("[{huge},{huge},-1,9223372036854775807,18446744073709551615]");
    let total = "2".to_owned() + &"0".repeat(80) + "27670116110564327421";
    assert!(accepted(&values, &format!(r#"{{"total":{total}}}"#)));
    let off_by_one = "2".to_owned() + &"0".repeat(80) + "27670116110564327422";
    assert!(!accepted(&values, &format!(r#"{{"total":{off_by_one}}}"#)));
    assert!(accepted(&format!("[-{huge},{huge}]"), r#"{"total":0}"#));
}

#[test]
fn a_case_may_carry_more_than_its_values() {
    let text = r#"{"checker":"integer_sum_v1","case":{"values":[1,2],"attachment":{"values":[9]}},"answer":{"total":3}}"#;
    assert!(judge(text).expect("judged").accepted);
}

#[test]
fn a_case_the_judge_cannot_sum_is_refused_not_judged() {
    let code = |text: &str| judge(text).expect_err("refused").code;
    assert_eq!(code(&request("[1,2.5]", r#"{"total":3}"#)), "BAD_CASE");
    assert_eq!(code(&request("[1,1e2]", r#"{"total":101}"#)), "BAD_CASE");
    assert_eq!(code(&request(r#"[1,"2"]"#, r#"{"total":3}"#)), "BAD_CASE");
    assert_eq!(code(&request("7", r#"{"total":7}"#)), "BAD_CASE");
    assert_eq!(
        code(r#"{"checker":"integer_sum_v1","case":{},"answer":{"total":0}}"#),
        "BAD_CASE"
    );
    let message = judge(&request("[1,2.5]", r#"{"total":3}"#))
        .expect_err("refused")
        .message;
    assert_eq!(message, "2.5 is not an integer");
}

#[test]
fn an_unknown_checker_or_an_open_request_is_refused() {
    let unknown = r#"{"checker":"schema_only","case":{"values":[1]},"answer":{"total":1}}"#;
    let refusal = judge(unknown).expect_err("refused");
    assert_eq!(refusal.code, "UNKNOWN_CHECKER");
    assert_eq!(refusal.message, "no judge is registered for schema_only");
    let open =
        r#"{"checker":"integer_sum_v1","case":{"values":[1]},"answer":{"total":1},"hint":1}"#;
    assert_eq!(judge(open).expect_err("refused").code, "BAD_REQUEST");
    assert_eq!(judge("[]").expect_err("refused").code, "BAD_REQUEST");
}

#[test]
fn respond_and_the_command_report_pass_fail_and_refused() {
    let status =
        |text: String| serde_json::to_value(respond(&Command::Judge(text))).expect("encodes");
    let pass = status(request("[17,25,-4]", r#"{"total":38}"#));
    assert_eq!(
        pass,
        json!({"status": "PASS", "result": {"accepted": true, "reason": "Exact integer sum agrees."}})
    );
    let fail = status(request("[17,25,-4]", r#"{"total":0}"#));
    assert_eq!(
        fail,
        json!({"status": "FAIL", "result": {"accepted": false, "reason": "Incorrect integer sum."}})
    );
    assert_eq!(status("{}".to_owned())["status"], "REFUSED");

    let directory = std::env::temp_dir().join(format!("pfp_operad_judge_{}", std::process::id()));
    std::fs::create_dir_all(&directory).expect("scratch directory");
    let run = |name: &str, text: String| {
        let path = directory.join(name);
        std::fs::write(&path, text).expect("written");
        let output = Process::new(env!("CARGO_BIN_EXE_pfp_operad"))
            .args(["judge", path.to_str().expect("utf-8 path")])
            .output()
            .expect("the command runs");
        let line: Value = serde_json::from_slice(&output.stdout).unwrap_or(Value::Null);
        (output.status.code(), line["status"].clone())
    };
    assert_eq!(
        run("right.json", request("[1,2]", r#"{"total":3}"#)),
        (Some(0), json!("PASS"))
    );
    assert_eq!(
        run("wrong.json", request("[1,2]", r#"{"total":4}"#)),
        (Some(1), json!("FAIL"))
    );
    assert_eq!(
        run("refused.json", request("[1,2.0]", r#"{"total":3}"#)),
        (Some(1), json!("REFUSED"))
    );
    std::fs::remove_dir_all(&directory).expect("scratch removed");
}

#[test]
fn the_shipped_example_is_accepted() {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/judge.json");
    let verdict = judge(&std::fs::read_to_string(path).expect("example")).expect("judged");
    assert!(verdict.accepted);
}
