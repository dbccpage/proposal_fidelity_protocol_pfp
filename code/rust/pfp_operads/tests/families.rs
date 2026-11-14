//! The family protocol: what the host asks next, what it refuses, and the report of a verdict.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-tests:v1

use pfp_operads::datum::Datum;
use pfp_operads::families::{
    certified, judge, judge_in, list, next, next_in, no_reply, refused, require, typed_refusal,
    Checks, Family, Run, Stop, Verdict, CERTIFIED, CERTIFIED_CODE, FAMILIES, MALFORMED,
    NO_PREDICATE, NO_REPLY, REFUSED, TYPED_REFUSAL,
};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const PROMPT: &str = "WF7 Typed refusal. Solve it.\n{\"A\":[[1,1],[1,-1]],\"b\":[3,1]}";

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

fn task() -> Value {
    json!({"statement": "Solve it.", "A": [[1, 1], [1, -1]], "b": [3, 1]})
}

fn request(replies: Value) -> String {
    json!({"workflow": "WF7", "task": task(), "replies": replies}).to_string()
}

fn passed(outcome: Outcome) -> Value {
    match outcome {
        Outcome::Pass { result } => result,
        other => panic!("expected PASS, got {other:?}"),
    }
}

fn failed(outcome: Outcome) -> Value {
    match outcome {
        Outcome::Fail { result } => result,
        other => panic!("expected FAIL, got {other:?}"),
    }
}

fn refusal(outcome: Outcome) -> (&'static str, String) {
    match outcome {
        Outcome::Refused { refusal } => (refusal.code, refusal.message),
        other => panic!("expected REFUSED, got {other:?}"),
    }
}

#[test]
fn the_host_lists_its_families_in_workflow_order() {
    assert_eq!(
        passed(list()),
        json!({"families": [
            {"workflow": "WF7", "name": "Typed refusal", "host_check": "typed_refusal_rank_test"},
            {"workflow": "WF9", "name": "Bounded check-and-repair",
             "host_check": "xor_cycle_minimal_repair"},
            {"workflow": "WF10", "name": "Local-to-global obstruction certificate",
             "host_check": "cochain_gluing_or_cycle_obstruction"},
            {"workflow": "WF11", "name": "Dual-certificate synthesis",
             "host_check": "lp_dual_and_farkas_certificate"},
            {"workflow": "WF13", "name": "Exact-domain capsule battery",
             "host_check": "per_domain_registered_checker"},
            {"workflow": "WF20", "name": "Derivation loop with lift grants",
             "host_check": "structural_lift_grant_loop"},
            {"workflow": "WF24", "name": "Pinned-token operational scratchpad",
             "host_check": "dual_holonomy_checkers"},
            {"workflow": "WF25", "name": "Hierarchical decimation",
             "host_check": "cycle_residual_preserving_decimation"},
            {"workflow": "WF26", "name": "Multi-round antibody dialogue",
             "host_check": "epitope_antibody_exact_oracle"},
            {"workflow": "WF27", "name": "Hinted retraction with a stationary-loop detector",
             "host_check": "xor_residual_gate_stationary_loop"},
            {"workflow": "WF30", "name": "Constraint-forcing anti-recitation",
             "host_check": "comparator_network_zero_one_principle"},
            {"workflow": "WF31", "name": "Multi-agent tournament with held-out cross-validation",
             "host_check": "exact_held_out_referee"},
            {"workflow": "WF32", "name": "Claim-scoped receipt",
             "host_check": "per_claim_independent_checkers"},
            {"workflow": "WF33", "name": "Recursive re-entry with shared fuel",
             "host_check": "shared_fuel_parent_bound_reentry"},
            {"workflow": "WF38", "name": "Diagnostic-trace proposal selection",
             "host_check": "host_recomputed_defect_ranking"},
            {"workflow": "WF40", "name": "Restart boundary after exhausted repair",
             "host_check": "cochain_trichotomy_boundary"},
            {"workflow": "WF45", "name": "Finite terminal selector and plenitude test",
             "host_check": "finite_survivor_set_verifier"},
            {"workflow": "WF46", "name": "Boundary sufficiency and gluing diagnostic",
             "host_check": "glued_trace_global_evaluator"},
            {"workflow": "WF47", "name": "Resumable bounded frontier search",
             "host_check": "sign_gauge_checkpoint_chain"},
        ]})
    );
    assert_eq!(FAMILIES.len(), 19);
}

#[test]
fn a_run_with_no_reply_is_told_what_to_ask() {
    assert_eq!(
        passed(next(&request(json!([])))),
        json!({
            "workflow": "WF7",
            "ask": {"stage": "solve", "prompt": PROMPT, "prompt_sha256": sha(PROMPT)},
            "asked": [],
        })
    );
}

#[test]
fn a_run_with_every_reply_has_nothing_left_to_ask() {
    assert_eq!(
        passed(next(&request(json!([{"content": {"answer": [2, 1]}}])))),
        json!({
            "workflow": "WF7",
            "ask": null,
            "asked": [{"stage": "solve", "prompt_sha256": sha(PROMPT)}],
        })
    );
    assert_eq!(passed(next(&request(json!([null]))))["ask"], Value::Null);
}

#[test]
fn a_certified_run_reports_its_predicates_and_passes() {
    let witness = r#"{"n":2,"rank_A":2,"rank_Ab":2,"status":"unique"}"#;
    assert_eq!(
        passed(judge(&request(json!([{"content": {"answer": [2, 1]}}])))),
        json!({
            "workflow": "WF7",
            "verdict": "HOST_CERTIFIED",
            "code": "CERTIFIED",
            "detail": {"witness": {"n": 2, "rank_A": 2, "rank_Ab": 2, "status": "unique"}},
            "predicates": [{
                "name": "answer_equals_unique_solution",
                "passed": true,
                "evidence_sha256": sha(witness),
            }],
            "every_predicate_passed": true,
            "uncertified_obligations": [],
            "asked": [{"stage": "solve", "prompt_sha256": sha(PROMPT)}],
        })
    );
}

#[test]
fn a_typed_refusal_passes_and_a_refused_verdict_fails() {
    let singular = json!({"workflow": "WF7", "task": {"A": [[1, 1], [2, 2]], "b": [3, 7]},
        "replies": [{"content": {"refusal": "UNRESOLVED_INCONSISTENT"}}]});
    let report = passed(judge(&singular.to_string()));
    assert_eq!(report["verdict"], TYPED_REFUSAL);
    assert_eq!(report["every_predicate_passed"], true);
    let wrong = failed(judge(&request(json!([{"content": {"answer": [1, 2]}}]))));
    assert_eq!(wrong["verdict"], REFUSED);
    assert_eq!(wrong["code"], "ANSWER_EQUALS_UNIQUE_SOLUTION");
    assert_eq!(wrong["every_predicate_passed"], false);
    assert_eq!(
        wrong["detail"]["failed"],
        json!(["answer_equals_unique_solution"])
    );
    assert_eq!(wrong["predicates"][0]["passed"], false);
}

#[test]
fn a_missing_reply_is_a_refused_verdict_with_no_predicate() {
    let report = failed(judge(&request(json!([null]))));
    assert_eq!(report["verdict"], REFUSED);
    assert_eq!(report["code"], NO_REPLY);
    assert_eq!(report["detail"], json!({}));
    assert_eq!(report["predicates"], json!([]));
    assert_eq!(report["every_predicate_passed"], false);
    assert_eq!(report["asked"][0]["stage"], "solve");
}

#[test]
fn a_reply_that_cannot_be_read_is_a_malformed_candidate() {
    for content in [json!(null), json!([1]), json!("x"), json!({"answer": "ab"})] {
        let report = failed(judge(&request(json!([{ "content": content }]))));
        assert_eq!(report["verdict"], REFUSED);
        assert_eq!(report["code"], MALFORMED);
        assert_eq!(report["predicates"], json!([]));
    }
    let report = failed(judge(&request(json!([{"content": 5}]))));
    assert_eq!(
        report["detail"],
        json!({"reason": "the reply must be an object"})
    );
}

#[test]
fn a_verdict_is_refused_while_a_step_waits_for_its_reply() {
    assert_eq!(
        refusal(judge(&request(json!([])))),
        (
            "REPLIES_INCOMPLETE",
            "stage solve has no reply yet".to_owned()
        )
    );
}

#[test]
fn more_replies_than_steps_are_refused() {
    let extra = request(json!([{"content": {"answer": [2, 1]}}, null]));
    let expected = (
        "BAD_REQUEST",
        "the run ends after 1 replies and 2 were sent".to_owned(),
    );
    assert_eq!(refusal(judge(&extra)), expected);
    assert_eq!(refusal(next(&extra)), expected);
}

#[test]
fn a_reply_is_null_or_an_object_with_the_one_key_content() {
    let message = "a reply is null or an object with the one key content".to_owned();
    for reply in [
        json!(5),
        json!([]),
        json!({}),
        json!({"contents": 1}),
        json!({"content": 1, "more": 2}),
        json!({"a": 1, "b": 2}),
    ] {
        assert_eq!(
            refusal(judge(&request(json!([reply])))),
            ("BAD_REQUEST", message.clone())
        );
    }
}

#[test]
fn a_request_that_is_not_the_request_shape_is_refused() {
    assert_eq!(refusal(next("{")).0, "BAD_REQUEST");
    assert_eq!(refusal(next("[]")).0, "BAD_REQUEST");
    let unknown = json!({"workflow": "WF7", "task": task(), "extra": 1}).to_string();
    let (code, message) = refusal(next(&unknown));
    assert_eq!(code, "BAD_REQUEST");
    assert!(message.contains("unknown field `extra`"), "{message}");
    let no_task = json!({"workflow": "WF7"}).to_string();
    assert!(refusal(judge(&no_task)).1.contains("missing field `task`"));
    let twice = r#"{"workflow":"WF7","task":{"A":[[1]],"A":[[1]],"b":[1]}}"#;
    assert_eq!(
        refusal(next(twice)),
        (
            "BAD_JSON",
            "the key A appears twice in one object".to_owned()
        )
    );
}

#[test]
fn a_family_this_host_does_not_check_is_refused_by_name() {
    let request = json!({"workflow": "WF8", "task": task()}).to_string();
    assert_eq!(
        refusal(next(&request)),
        (
            "UNKNOWN_WORKFLOW",
            "this host checks no family named WF8".to_owned()
        )
    );
    assert_eq!(refusal(judge(&request)).0, "UNKNOWN_WORKFLOW");
}

#[test]
fn a_task_or_sealed_part_of_the_wrong_kind_is_refused() {
    let list_task = json!({"workflow": "WF7", "task": [1]}).to_string();
    assert_eq!(
        refusal(next(&list_task)),
        ("BAD_TASK", "the task must be an object".to_owned())
    );
    let list_sealed = json!({"workflow": "WF7", "task": task(), "sealed": [1]}).to_string();
    assert_eq!(
        refusal(next(&list_sealed)),
        ("BAD_REQUEST", "sealed must be an object".to_owned())
    );
    let empty_sealed = json!({"workflow": "WF7", "task": task(), "sealed": {}}).to_string();
    assert_eq!(passed(next(&empty_sealed))["ask"]["stage"], "solve");
}

#[test]
fn a_task_the_family_cannot_read_is_refused_with_the_family_s_reason() {
    let request = json!({"workflow": "WF7", "task": {"A": [], "b": []}}).to_string();
    let expected = ("BAD_TASK", "A must be a nonempty list of rows".to_owned());
    assert_eq!(refusal(next(&request)), expected);
    assert_eq!(refusal(judge(&request)), expected);
}

#[test]
fn a_prompt_that_carries_a_sealed_value_is_never_handed_out() {
    let leaky = |replies: Value| {
        json!({
            "workflow": "WF7",
            "task": {"statement": "secret 98765", "A": [[1]], "b": [1]},
            "sealed": {"expected": 98765},
            "replies": replies,
        })
        .to_string()
    };
    let expected = (
        "SEALED_LEAK",
        "the prompt of stage solve contains a sealed value".to_owned(),
    );
    assert_eq!(refusal(next(&leaky(json!([])))), expected);
    assert_eq!(
        refusal(judge(&leaky(json!([{"content": {"answer": [1]}}])))),
        expected
    );
}

#[test]
fn a_sealed_value_that_is_not_in_the_prompt_changes_nothing() {
    let request = json!({"workflow": "WF7", "task": task(), "sealed": {"expected": 98765},
        "replies": [{"content": {"answer": [2, 1]}}]});
    assert_eq!(passed(judge(&request.to_string()))["verdict"], CERTIFIED);
}

#[test]
fn the_default_prompt_is_the_family_the_statement_and_the_rest_of_the_task() {
    let prompt = |task: Value| {
        passed(next(&json!({"workflow": "WF7", "task": task}).to_string()))["ask"]["prompt"]
            .as_str()
            .expect("a prompt")
            .to_owned()
    };
    assert_eq!(
        prompt(json!({"b": [1], "A": [[2]]})),
        "WF7 Typed refusal. \n{\"A\":[[2]],\"b\":[1]}"
    );
    assert_eq!(
        prompt(json!({"b": [1], "statement": 7, "A": [[2]], "note": "n"})),
        "WF7 Typed refusal. 7\n{\"A\":[[2]],\"b\":[1],\"note\":\"n\"}"
    );
    assert_eq!(
        prompt(json!({"b": [1], "statement": "line\n\"two\"", "A": [[2]]})),
        "WF7 Typed refusal. line\n\"two\"\n{\"A\":[[2]],\"b\":[1]}"
    );
}

#[test]
fn a_predicate_is_recorded_once_under_its_name() {
    let mut checks = Checks::default();
    assert!(!checks.certified());
    assert!(checks.record("first", true, &Datum::from(1usize)));
    assert!(checks.certified());
    assert!(!checks.record("second", false, &Datum::Null));
    assert!(!checks.certified());
    let verdict = checks.judge(CERTIFIED_CODE, Datum::map([("kept", Datum::Bool(true))]));
    assert_eq!(verdict.verdict, REFUSED);
    assert_eq!(verdict.code, "SECOND");
    assert_eq!(
        verdict.detail.canonical(),
        r#"{"failed":["second"],"kept":true}"#
    );
}

#[test]
fn a_name_recorded_twice_is_kept_as_a_failed_predicate() {
    let mut checks = Checks::default();
    assert!(checks.record("same", true, &Datum::Null));
    assert!(!checks.record("same", true, &Datum::Null));
    assert!(!checks.certified());
    let verdict = checks.judge("OK", Datum::map([]));
    assert_eq!(verdict.code, "REPEATED:SAME");
    assert_eq!(
        verdict.detail.canonical(),
        r#"{"failed":["repeated:same"]}"#
    );
}

#[test]
fn the_first_failed_predicate_names_the_refusal() {
    let mut checks = Checks::default();
    checks.record("good", true, &Datum::Null);
    checks.record("bad_one", false, &Datum::Null);
    checks.record("bad_two", false, &Datum::Null);
    let verdict = checks.judge("OK", Datum::text("not a map"));
    assert_eq!(verdict.code, "BAD_ONE");
    assert_eq!(
        verdict.detail.canonical(),
        r#"{"failed":["bad_one","bad_two"]}"#
    );
}

#[test]
fn nothing_recorded_certifies_nothing() {
    let verdict = Checks::default().judge("OK", Datum::map([]));
    assert_eq!(verdict.verdict, REFUSED);
    assert_eq!(verdict.code, NO_PREDICATE);
    assert_eq!(verdict.detail.canonical(), r#"{"failed":[]}"#);
}

#[test]
fn every_predicate_passing_certifies_under_the_family_s_code() {
    let mut checks = Checks::default();
    checks.record("a", true, &Datum::Null);
    checks.record("b", true, &Datum::Null);
    let detail = Datum::map([("n", Datum::from(2usize))]);
    assert_eq!(
        checks.judge("DONE", detail.clone()),
        certified("DONE", detail)
    );
}

#[test]
fn the_verdict_builders_set_the_kind_and_keep_the_code_and_detail() {
    let detail = Datum::map([("k", Datum::from(1usize))]);
    let built = certified("A", detail.clone());
    assert_eq!(
        (built.verdict, built.code.as_str(), &built.detail),
        (CERTIFIED, "A", &detail)
    );
    let built = typed_refusal("B", detail.clone());
    assert_eq!(
        (built.verdict, built.code.as_str(), &built.detail),
        (TYPED_REFUSAL, "B", &detail)
    );
    let built = refused("C", detail.clone());
    assert_eq!(
        (built.verdict, built.code.as_str(), &built.detail),
        (REFUSED, "C", &detail)
    );
    assert_eq!(no_reply(), refused(NO_REPLY, Datum::map([])));
    assert_eq!(
        (CERTIFIED, TYPED_REFUSAL, REFUSED),
        ("HOST_CERTIFIED", "TYPED_REFUSAL", "REFUSED")
    );
    assert_eq!(
        (CERTIFIED_CODE, NO_REPLY, MALFORMED, NO_PREDICATE),
        (
            "CERTIFIED",
            "NO_ADMISSIBLE_REPLY",
            "MALFORMED_CANDIDATE",
            "NO_HOST_PREDICATE"
        )
    );
}

#[test]
fn require_stops_the_walk_with_its_reason_only_when_the_condition_fails() {
    assert_eq!(require(true, "unused"), Ok(()));
    assert_eq!(
        require(false, "why"),
        Err(Stop::Malformed("why".to_owned()))
    );
}

fn cli(args: &[&str]) -> (Option<i32>, Value) {
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_pfp_operad"))
        .args(args)
        .output()
        .expect("the command runs");
    (
        output.status.code(),
        serde_json::from_slice(&output.stdout).unwrap_or(Value::Null),
    )
}

#[test]
fn the_command_line_runs_the_three_family_commands() {
    let directory = std::env::temp_dir().join(format!("pfp_operad_family_{}", std::process::id()));
    std::fs::create_dir_all(&directory).expect("scratch directory");
    let file = |name: &str, text: String| {
        let path = directory.join(name);
        std::fs::write(&path, text).expect("written");
        path.to_str().expect("utf-8 path").to_owned()
    };
    let (code, listed) = cli(&["family", "list"]);
    assert_eq!(code, Some(0));
    assert_eq!(listed, json!({"status": "PASS", "result": passed(list())}));

    let waiting = file("waiting.json", request(json!([])));
    let (code, turn) = cli(&["family", "next", &waiting]);
    assert_eq!(code, Some(0));
    assert_eq!(turn["status"], "PASS");
    assert_eq!(turn["result"]["ask"]["stage"], "solve");
    let (code, early) = cli(&["family", "judge", &waiting]);
    assert_eq!(code, Some(1));
    assert_eq!(early["status"], "REFUSED");
    assert_eq!(early["refusal"]["code"], "REPLIES_INCOMPLETE");

    let right = file(
        "right.json",
        request(json!([{"content": {"answer": [2, 1]}}])),
    );
    let (code, report) = cli(&["family", "judge", &right]);
    assert_eq!(code, Some(0));
    assert_eq!(report["status"], "PASS");
    assert_eq!(report["result"]["verdict"], "HOST_CERTIFIED");
    let (code, turn) = cli(&["family", "next", &right]);
    assert_eq!(code, Some(0));
    assert_eq!(turn["result"]["ask"], Value::Null);

    let wrong = file(
        "wrong.json",
        request(json!([{"content": {"answer": [1, 2]}}])),
    );
    let (code, report) = cli(&["family", "judge", &wrong]);
    assert_eq!(code, Some(1));
    assert_eq!(report["status"], "FAIL");
    assert_eq!(report["result"]["verdict"], "REFUSED");

    let absent = directory.join("absent.json");
    let absent = absent.to_str().expect("utf-8 path");
    for args in [
        vec!["family"],
        vec!["family", "next"],
        vec!["family", "judge"],
        vec!["family", "list", &right],
        vec!["family", "grade", &right],
        vec!["family", "next", absent],
        vec!["family", "judge", absent],
    ] {
        assert_eq!(cli(&args), (Some(2), Value::Null), "{args:?}");
    }
    std::fs::remove_dir_all(&directory).expect("scratch removed");
}

#[test]
fn the_shipped_examples_ask_one_step_and_certify_its_answer() {
    let example = |name: &str| {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("examples")
            .join(name);
        std::fs::read_to_string(path).expect("example")
    };
    assert_eq!(
        passed(next(&example("family_next.json")))["ask"]["stage"],
        "solve"
    );
    assert_eq!(
        passed(judge(&example("family_judge.json")))["verdict"],
        CERTIFIED
    );
}

fn any_task(_task: &Datum, _sealed: &Datum) -> Result<(), String> {
    Ok(())
}

/// A walk that does what its reply says, so a test can make a family misbehave.
fn obedient(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let Some(reply) = run.ask("say", "Say what to do.".to_owned())? else {
        return Ok(no_reply());
    };
    for name in reply.get("pass").and_then(Datum::as_list).unwrap_or(&[]) {
        checks.record(name.as_text().unwrap_or("unnamed"), true, &Datum::Null);
    }
    for name in reply.get("fail").and_then(Datum::as_list).unwrap_or(&[]) {
        checks.record(name.as_text().unwrap_or("unnamed"), false, &Datum::Null);
    }
    let detail = Datum::map([("note", Datum::from("kept"))]);
    let verdict = match reply.get("claim").and_then(Datum::as_text) {
        Some("certified") => certified("DONE", detail),
        Some("typed_refusal") => typed_refusal("WHY", detail),
        _ => refused("NO", detail),
    };
    let owed = reply.get("owe").and_then(Datum::as_list).unwrap_or(&[]);
    Ok(verdict.owing(
        owed.iter()
            .filter_map(Datum::as_text)
            .map(str::to_owned)
            .collect(),
    ))
}

/// A walk that asks about one part of its task, with the family's default prompt for that part.
fn partwise(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let part = run.task.get("part").unwrap_or(&Datum::Null);
    let prompt = run.prompt_for(part);
    run.ask("part", prompt)?;
    Ok(checks.judge("DONE", Datum::map([])))
}

static PARTWISE: Family = Family {
    workflow: "WF00",
    name: "Partwise",
    host_check: "none",
    validate: any_task,
    walk: partwise,
};

static OBEDIENT: Family = Family {
    workflow: "WF0",
    name: "Obedient",
    host_check: "none",
    validate: any_task,
    walk: obedient,
};

fn told(reply: Value) -> Outcome {
    let request = json!({"workflow": "WF0", "task": {}, "replies": [{"content": reply}]});
    judge_in(&[&OBEDIENT], &request.to_string())
}

#[test]
fn a_walk_cannot_certify_without_a_recorded_predicate() {
    for claim in ["certified", "typed_refusal"] {
        let report = failed(told(json!({ "claim": claim })));
        assert_eq!(report["verdict"], "REFUSED");
        assert_eq!(report["code"], "NO_HOST_PREDICATE");
        assert_eq!(report["every_predicate_passed"], false);
        assert_eq!(report["detail"]["failed"], json!([]));
        assert_eq!(report["detail"]["claimed_detail"], json!({"note": "kept"}));
    }
    let report = failed(told(json!({"claim": "certified"})));
    assert_eq!(
        report["detail"],
        json!({"claimed_verdict": "HOST_CERTIFIED", "claimed_code": "DONE",
               "claimed_detail": {"note": "kept"}, "failed": []})
    );
}

#[test]
fn a_walk_cannot_certify_past_a_failed_predicate() {
    let report = failed(told(
        json!({"claim": "certified", "pass": ["first"], "fail": ["second", "third"]}),
    ));
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "SECOND");
    assert_eq!(report["detail"]["failed"], json!(["second", "third"]));
    assert_eq!(report["detail"]["claimed_verdict"], "HOST_CERTIFIED");
    let report = failed(told(json!({"claim": "typed_refusal", "fail": ["only"]})));
    assert_eq!(report["code"], "ONLY");
    assert_eq!(report["detail"]["claimed_verdict"], "TYPED_REFUSAL");
    assert_eq!(report["detail"]["claimed_code"], "WHY");
}

#[test]
fn a_walk_s_verdict_stands_when_every_recorded_predicate_passed() {
    let report = passed(told(json!({"claim": "certified", "pass": ["a", "b"]})));
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "DONE");
    assert_eq!(report["detail"], json!({"note": "kept"}));
    assert_eq!(report["every_predicate_passed"], true);
    let report = passed(told(json!({"claim": "typed_refusal", "pass": ["a"]})));
    assert_eq!(report["verdict"], "TYPED_REFUSAL");
    assert_eq!(report["code"], "WHY");
    assert_eq!(report["detail"], json!({"note": "kept"}));
    // The flag reports the predicates, not the verdict: a walk may refuse past passed predicates.
    let report = failed(told(json!({"pass": ["a"]})));
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "NO");
    assert_eq!(report["every_predicate_passed"], true);
}

#[test]
fn a_walk_s_own_refusal_is_kept_as_it_is() {
    for reply in [json!({}), json!({"pass": ["a"]}), json!({"fail": ["a"]})] {
        let report = failed(told(reply));
        assert_eq!(report["verdict"], "REFUSED");
        assert_eq!(report["code"], "NO");
        assert_eq!(report["detail"], json!({"note": "kept"}));
    }
}

#[test]
fn a_registry_checks_only_its_own_families() {
    let own = json!({"workflow": "WF0", "task": {}}).to_string();
    let turn = passed(next_in(&[&OBEDIENT], &own));
    assert_eq!(turn["workflow"], "WF0");
    assert_eq!(turn["ask"]["stage"], "say");
    assert_eq!(turn["ask"]["prompt"], "Say what to do.");
    assert_eq!(refusal(next(&own)).0, "UNKNOWN_WORKFLOW");
    assert_eq!(refusal(judge(&own)).0, "UNKNOWN_WORKFLOW");
    let shipped = request(json!([]));
    assert_eq!(
        refusal(next_in(&[&OBEDIENT], &shipped)),
        (
            "UNKNOWN_WORKFLOW",
            "this host checks no family named WF7".to_owned()
        )
    );
    assert_eq!(
        refusal(judge_in(&[&OBEDIENT], &shipped)).0,
        "UNKNOWN_WORKFLOW"
    );
    assert_eq!(passed(next_in(FAMILIES, &shipped)), passed(next(&shipped)));
}

#[test]
fn a_verdict_names_what_no_predicate_covers() {
    let report = passed(told(
        json!({"claim": "certified", "pass": ["a"], "owe": ["the rest", "and more"]}),
    ));
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["every_predicate_passed"], true);
    assert_eq!(
        report["uncertified_obligations"],
        json!(["the rest", "and more"])
    );
    let report = failed(told(json!({"claim": "certified", "owe": ["still owed"]})));
    assert_eq!(report["code"], "NO_HOST_PREDICATE");
    assert_eq!(report["uncertified_obligations"], json!(["still owed"]));
    let report = failed(told(json!({"owe": ["on a refusal"]})));
    assert_eq!(report["uncertified_obligations"], json!(["on a refusal"]));
    assert_eq!(
        certified("A", Datum::Null).obligations,
        Vec::<String>::new()
    );
    assert_eq!(typed_refusal("A", Datum::Null).obligations.len(), 0);
    assert_eq!(refused("A", Datum::Null).obligations.len(), 0);
    assert_eq!(
        refused("A", Datum::Null)
            .owing(vec!["x".to_owned()])
            .obligations,
        vec!["x".to_owned()]
    );
}

#[test]
fn the_default_prompt_can_be_written_for_a_part_of_the_task() {
    let prompt = |task: Value| {
        let request = json!({"workflow": "WF00", "task": task}).to_string();
        passed(next_in(&[&PARTWISE], &request))["ask"]["prompt"]
            .as_str()
            .expect("a prompt")
            .to_owned()
    };
    assert_eq!(
        prompt(json!({"statement": "whole", "part": {"statement": "this part", "k": [2, 1]}})),
        "WF00 Partwise. this part\n{\"k\":[2,1]}"
    );
    assert_eq!(
        prompt(json!({"statement": "whole", "part": {"z": 1, "a": 2}})),
        "WF00 Partwise. \n{\"a\":2,\"z\":1}"
    );
    assert_eq!(
        prompt(json!({"statement": "whole", "part": [3, 4]})),
        "WF00 Partwise. \n[3,4]"
    );
    assert_eq!(prompt(json!({})), "WF00 Partwise. \nnull");
}
