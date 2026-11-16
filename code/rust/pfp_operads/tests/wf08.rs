//! WF8, staged sealed packets: the stages and their prompts, the five predicates of each
//! packet in the order the host records them, the hash chain, and the two checks after the last
//! stage.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf08-tests:v1

use pfp_operads::families::wf08::{FAMILY, QUESTION, STAGES};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

const FENCED: &str = "<<Q>>Solve A x = b for x with A = [[2, 1], [1, 3]], b = [3, 5].<</Q>>";

fn task() -> Value {
    json!({
        "statement": format!("{FENCED} Work in three sealed stages."),
        "A": [[2, 1], [1, 3]],
        "b": [3, 5],
    })
}

/// The payloads an honest run seals: the reduced `[A | b]`, the solution, the residual.
fn payloads() -> Vec<Value> {
    vec![
        json!([[1, 0, "4/5"], [0, 1, "7/5"]]),
        json!(["4/5", "7/5"]),
        json!([0, 0]),
    ]
}

/// Packets for these payloads, each sealed into the chain that starts at the task.
fn packets(task: &Value, payloads: Vec<Value>, carry: &str) -> Vec<Value> {
    let mut head = sha(&task.to_string());
    let mut out = Vec::new();
    for (stage, payload) in STAGES.iter().zip(payloads) {
        let seal = sha(&format!("{head}{payload}"));
        out.push(json!({
            "stage": stage, "carry": carry, "payload": payload, "prev": head, "seal": seal,
        }));
        head = seal;
    }
    out
}

fn honest() -> Vec<Value> {
    packets(&task(), payloads(), FENCED)
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
    json!({"workflow": "WF8", "task": task, "replies": replies}).to_string()
}

fn all(replies: Vec<Value>) -> Vec<Option<Value>> {
    replies.into_iter().map(Some).collect()
}

/// The report of a finished run, and whether the host passed it.
fn run_task(task: &Value, replies: Vec<Option<Value>>) -> (bool, Value) {
    match judge(&request(task, &replies)) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn run(replies: Vec<Value>) -> (bool, Value) {
    run_task(&task(), all(replies))
}

/// The next question of a run that is not finished.
fn ask(replies: Vec<Value>) -> Value {
    match next(&request(&task(), &all(replies))) {
        Outcome::Pass { result } => result["ask"].clone(),
        other => panic!("expected a turn, got {other:?}"),
    }
}

fn bad_task(task: Value) -> String {
    match next(&request(&task, &[])) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

/// The reason of a run refused because a reply could not be read, with the predicates recorded
/// before that.
fn malformed(mut replies: Vec<Value>, at: usize) -> (String, Vec<(String, bool)>) {
    replies.truncate(at + 1);
    let (passed, report) = run(replies);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    let reason = report["detail"]["reason"].as_str().expect("a reason");
    (reason.to_owned(), owned(outcomes(&report)))
}

fn owned(rows: Vec<(&str, bool)>) -> Vec<(String, bool)> {
    rows.into_iter()
        .map(|(name, held)| (name.to_owned(), held))
        .collect()
}

/// The predicates of a report as name and outcome, in the order they were recorded.
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

/// A run that stops at the reply with index `at`, refused under this code: the report, after
/// checking the code and the verdict.
fn refused(mut replies: Vec<Value>, at: usize, code: &str) -> Value {
    replies.truncate(at + 1);
    let (passed, report) = run(replies);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], code);
    report
}

#[test]
fn the_registry_names_the_family() {
    assert_eq!(FAMILY.workflow, "WF8");
    assert_eq!(FAMILY.name, "Staged sealed packets");
    assert_eq!(FAMILY.host_check, "stage_seal_chain_recompute");
    assert_eq!(STAGES, ["eliminate", "solve", "residual"]);
    assert_eq!(QUESTION.begin, "<<Q>>");
    assert_eq!(QUESTION.end, "<</Q>>");
    assert_eq!(QUESTION.name, "question");
}

#[test]
fn an_honest_run_is_certified_with_every_predicate_in_order() {
    let replies = honest();
    let (passed, report) = run(replies.clone());
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "SEALED_PIPELINE");
    assert_eq!(
        report["detail"],
        json!({"stages": 3, "head": replies[2]["seal"]})
    );
    let mut names = Vec::new();
    for stage in STAGES {
        for predicate in [
            "stage_named",
            "fence_intact",
            "chain_linked",
            "seal_matches",
            "recomputed",
        ] {
            names.push((format!("{stage}:{predicate}"), true));
        }
    }
    names.push(("answer_is_unique_solution".to_owned(), true));
    names.push(("final_residual_zero".to_owned(), true));
    assert_eq!(owned(outcomes(&report)), names);
    assert_eq!(report["every_predicate_passed"], true);
    let digests: Vec<&str> = report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| row["evidence_sha256"].as_str().expect("a digest"))
        .collect();
    for (stage, packet) in replies.iter().enumerate() {
        for digest in &digests[stage * 5..stage * 5 + 5] {
            assert_eq!(*digest, sha(&packet.to_string()), "stage {stage}");
        }
    }
    assert_eq!(digests[15..], [sha("null"), sha("null")]);
    let asked: Vec<&str> = report["asked"]
        .as_array()
        .expect("asked")
        .iter()
        .map(|row| row["stage"].as_str().expect("a stage"))
        .collect();
    assert_eq!(asked, ["stage:eliminate", "stage:solve", "stage:residual"]);
}

#[test]
fn each_stage_is_asked_with_the_packet_before_it() {
    let replies = honest();
    let rest = r#"{"A":[[2,1],[1,3]],"b":[3,5]}"#;
    let first = format!("WF8 Staged sealed packets. {FENCED} Work in three sealed stages.\n{rest}");
    let opening = ask(vec![]);
    let prompt = format!("{first}\nStage eliminate.");
    assert_eq!(opening["stage"], "stage:eliminate");
    assert_eq!(opening["prompt"], prompt);
    assert_eq!(opening["prompt_sha256"], sha(&prompt));
    let second = ask(vec![replies[0].clone()]);
    let prompt = format!(
        "{first}\nStage solve.\nPrevious sealed packet: {}",
        replies[0]
    );
    assert_eq!(second["stage"], "stage:solve");
    assert_eq!(second["prompt"], prompt);
    let third = ask(vec![replies[0].clone(), replies[1].clone()]);
    let prompt = format!(
        "{first}\nStage residual.\nPrevious sealed packet: {}",
        replies[1]
    );
    assert_eq!(third["stage"], "stage:residual");
    assert_eq!(third["prompt"], prompt);
}

#[test]
fn a_packet_may_carry_more_than_its_five_fields() {
    let mut replies = honest();
    replies[0]["note"] = json!("kept");
    let (passed, _) = run(replies.clone());
    assert!(passed);
    let second = ask(vec![replies[0].clone()]);
    let prompt = second["prompt"].as_str().expect("a prompt");
    assert!(prompt.ends_with(&format!("Previous sealed packet: {}", replies[0])));
    assert!(prompt.contains(r#""note":"kept""#));
}

#[test]
fn the_same_rationals_written_another_way_are_the_same_payload() {
    let task = task();
    let again = vec![
        json!([["1", "0/3", "8/10"], [0, "1", "14/10"]]),
        json!(["8/10", "14/10"]),
        json!(["0", "0/1"]),
    ];
    let (passed, report) = run_task(&task, all(packets(&task, again, FENCED)));
    assert!(passed, "{report}");
}

#[test]
fn an_overdetermined_system_has_a_row_of_zeros_and_a_residual_per_row() {
    let task = json!({
        "statement": format!("{FENCED} Three equations."),
        "A": [[1, 0], [0, 1], [1, 1]],
        "b": [1, 2, 3],
    });
    let sealed = packets(
        &task,
        vec![
            json!([[1, 0, 1], [0, 1, 2], [0, 0, 0]]),
            json!([1, 2]),
            json!([0, 0, 0]),
        ],
        FENCED,
    );
    let (passed, report) = run_task(&task, all(sealed));
    assert!(passed, "{report}");
}

#[test]
fn the_carry_may_hold_more_than_the_question() {
    let carry = format!("Notes first. {FENCED} And notes after.");
    let (passed, _) = run(packets(&task(), payloads(), &carry));
    assert!(passed);
}

#[test]
fn a_packet_edited_after_it_was_sealed_breaks_its_seal() {
    let mut replies = honest();
    replies[1]["payload"] = json!(["1", "1/3"]);
    let report = refused(replies, 1, "SEAL_MISMATCH");
    assert_eq!(
        report["detail"],
        json!({"stage": "solve", "sealed_stages": 1})
    );
    let rows = outcomes(&report);
    assert!(rows.contains(&("solve:chain_linked", true)));
    assert!(rows.contains(&("solve:seal_matches", false)));
    assert!(rows.contains(&("solve:recomputed", false)));
    assert!(!rows.iter().any(|(name, _)| name.starts_with("residual")));
}

#[test]
fn a_broken_chain_link_is_found_before_the_seal() {
    let mut replies = honest();
    let first_link = replies[0]["prev"].clone();
    replies[1]["prev"] = first_link;
    let report = refused(replies, 1, "CHAIN_BROKEN");
    assert_eq!(
        report["detail"],
        json!({"stage": "solve", "sealed_stages": 1})
    );
    let rows = outcomes(&report);
    assert!(rows.contains(&("solve:chain_linked", false)));
    assert!(rows.contains(&("solve:seal_matches", true)));
}

#[test]
fn a_packet_that_drops_the_question_is_refused_for_its_fence() {
    for carry in [
        json!("Solve A x = b."),
        json!(""),
        json!(7),
        json!(null),
        json!(format!("{FENCED} {FENCED}")),
    ] {
        let mut replies = honest();
        replies[1]["carry"] = carry.clone();
        let report = refused(replies, 1, "FENCE_VIOLATED");
        assert_eq!(
            report["detail"],
            json!({"stage": "solve", "sealed_stages": 1})
        );
        assert!(
            outcomes(&report).contains(&("solve:fence_intact", false)),
            "{carry}"
        );
    }
}

#[test]
fn a_packet_must_name_its_stage() {
    for stage in [json!("solve"), json!(null), json!(3)] {
        let mut replies = honest();
        replies[0]["stage"] = stage;
        let report = refused(replies, 0, "STAGE_MISNAMED");
        assert_eq!(
            report["detail"],
            json!({"stage": "eliminate", "sealed_stages": 0})
        );
        assert!(outcomes(&report).contains(&("eliminate:stage_named", false)));
    }
}

#[test]
fn a_stage_that_is_sealed_but_wrong_is_refused_for_its_payload() {
    let wrong = vec![payloads()[0].clone(), json!(["1", "1/3"]), json!([0, 0])];
    let report = refused(
        packets(&task(), wrong, FENCED),
        1,
        "STAGE_RECOMPUTE_MISMATCH",
    );
    assert_eq!(
        report["detail"],
        json!({"stage": "solve", "sealed_stages": 1})
    );
    let rows = outcomes(&report);
    assert!(rows.contains(&("solve:seal_matches", true)));
    assert!(rows.contains(&("solve:recomputed", false)));
}

#[test]
fn a_payload_of_another_shape_is_not_the_recomputed_one() {
    for payload in [
        json!({"rows": [[1, 0, "4/5"], [0, 1, "7/5"]]}),
        json!([1, 0, "4/5", 0, 1, "7/5"]),
        json!([]),
    ] {
        let mut sealed = payloads();
        sealed[0] = payload;
        refused(
            packets(&task(), sealed, FENCED),
            0,
            "STAGE_RECOMPUTE_MISMATCH",
        );
    }
}

#[test]
fn every_predicate_of_a_packet_is_recorded_even_after_one_fails() {
    let mut replies = honest();
    replies[0]["stage"] = json!("wrong");
    replies[0]["carry"] = json!("");
    replies[0]["prev"] = json!("0");
    replies[0]["seal"] = json!("0");
    replies[0]["payload"] = json!([]);
    let report = refused(replies, 0, "STAGE_MISNAMED");
    assert_eq!(
        owned(outcomes(&report)),
        owned(vec![
            ("eliminate:stage_named", false),
            ("eliminate:fence_intact", false),
            ("eliminate:chain_linked", false),
            ("eliminate:seal_matches", false),
            ("eliminate:recomputed", false),
        ])
    );
}

#[test]
fn the_first_failure_names_the_refusal() {
    let mut replies = honest();
    replies[0]["carry"] = json!("");
    replies[0]["seal"] = json!("0");
    refused(replies, 0, "FENCE_VIOLATED");
}

#[test]
fn a_stage_with_no_packet_is_refused_as_missing() {
    let replies = honest();
    let (passed, report) = run_task(&task(), vec![None]);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "STAGE_MISSING");
    assert_eq!(report["detail"], json!({"stage": "eliminate"}));
    assert_eq!(
        owned(outcomes(&report)),
        owned(vec![("eliminate:packet_received", false)])
    );
    let (passed, report) = run_task(&task(), vec![Some(replies[0].clone()), None]);
    assert!(!passed);
    assert_eq!(report["code"], "STAGE_MISSING");
    assert_eq!(report["detail"], json!({"stage": "solve"}));
    let rows = owned(outcomes(&report));
    assert_eq!(rows.len(), 6);
    assert_eq!(rows[5], ("solve:packet_received".to_owned(), false));
    let (passed, report) = run_task(
        &task(),
        vec![Some(replies[0].clone()), Some(replies[1].clone()), None],
    );
    assert!(!passed);
    assert_eq!(report["detail"], json!({"stage": "residual"}));
}

#[test]
fn a_reply_that_is_not_a_packet_is_malformed() {
    for field in ["stage", "carry", "payload", "prev", "seal"] {
        let mut replies = honest();
        replies[0].as_object_mut().expect("an object").remove(field);
        let (reason, rows) = malformed(replies, 0);
        assert_eq!(reason, "packet fields missing", "{field}");
        assert!(rows.is_empty());
    }
    let mut replies = honest();
    replies[0] = json!("not a packet");
    let (reason, _) = malformed(replies, 0);
    assert_eq!(reason, "packet fields missing");
}

#[test]
fn a_payload_that_is_not_exact_is_malformed_before_any_predicate_of_its_stage() {
    for payload in [
        json!([[1, 0, 0.5], [0, 1, 1]]),
        json!(null),
        json!(true),
        json!("seven"),
        json!([[1, 0, "1/0"]]),
        json!([{"k": 1.5}]),
    ] {
        let mut replies = honest();
        replies[0]["payload"] = payload.clone();
        let (reason, rows) = malformed(replies, 0);
        assert_eq!(reason, "payload must be exact rationals", "{payload}");
        assert!(rows.is_empty(), "{payload}");
    }
    let mut replies = honest();
    replies[1]["payload"] = json!(["4/5", 1.5]);
    let (_, rows) = malformed(replies, 1);
    assert_eq!(rows.len(), 5);
}

#[test]
fn a_task_the_host_cannot_stage_is_a_bad_task() {
    let mut cases = Vec::new();
    let mut many = task();
    many["A"] = json!([[1, 1]]);
    many["b"] = json!([2]);
    cases.push((many, "unique solution"));
    let mut none = task();
    none["A"] = json!([[1, 1], [1, 1]]);
    none["b"] = json!([1, 2]);
    cases.push((none, "unique solution"));
    let mut ragged = task();
    ragged["A"] = json!([[2, 1], [1]]);
    cases.push((ragged, "rectangular"));
    let mut statement = task();
    statement
        .as_object_mut()
        .expect("an object")
        .remove("statement");
    cases.push((statement, "statement must be text"));
    cases.push((
        json!({"statement": 5, "A": [[1]], "b": [1]}),
        "statement must be text",
    ));
    cases.push((
        json!({"statement": "no fence", "A": [[1]], "b": [1]}),
        "FENCE_MARKERS_NOT_UNIQUE",
    ));
    cases.push((
        json!({"statement": "<<Q>>a<</Q>> <<Q>>b<</Q>>", "A": [[1]], "b": [1]}),
        "FENCE_MARKERS_NOT_UNIQUE",
    ));
    for (case, expected) in cases {
        let message = bad_task(case);
        assert!(message.contains(expected), "{message}");
    }
}

#[test]
fn a_single_unknown_is_a_staged_run_too() {
    let task = json!({"statement": "<<Q>>x = 3?<</Q>>", "A": [[2]], "b": [6]});
    let sealed = packets(
        &task,
        vec![json!([[1, 3]]), json!([3]), json!([0])],
        "<<Q>>x = 3?<</Q>>",
    );
    let (passed, report) = run_task(&task, all(sealed));
    assert!(passed, "{report}");
}
