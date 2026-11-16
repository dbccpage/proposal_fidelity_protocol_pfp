//! WF42, reasoning-trace validation: how a step is read, the obstruction the host finds, and
//! the correction or the potential and conclusion a reply must give.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf42-tests:v1

use pfp_operads::families::wf42::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

fn task() -> Value {
    json!({"statement": "Reason in steps of the form 'u - v = k', then state the conclusion."})
}

fn chain() -> Value {
    json!(["s1: b - a = 1", "s2: c - b = 1"])
}

fn cycle() -> Value {
    json!(["s1: b - a = 1", "s2: c - b = 0", "s3: a - c = 0"])
}

fn potential() -> Value {
    json!({"a": 0, "b": 1, "c": 2})
}

fn consistent(trace: Value, potential: Value, conclusion: &str) -> Value {
    json!({
        "trace": trace,
        "status": "CONSISTENT",
        "potential": potential,
        "conclusion": conclusion,
    })
}

fn obstructed(trace: Value, correction: Value) -> Value {
    json!({"trace": trace, "status": "OBSTRUCTED", "correction": correction})
}

fn request(replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF42", "task": task(), "replies": replies}).to_string()
}

fn run(reply: &Value) -> (bool, Value) {
    match judge(&request(&[Some(reply.clone())])) {
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

fn malformed(reply: &Value) -> String {
    let (passed, report) = run(reply);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    report["detail"]["reason"]
        .as_str()
        .expect("a reason")
        .to_owned()
}

#[test]
fn the_registry_names_the_family() {
    assert_eq!(FAMILY.workflow, "WF42");
    assert_eq!(FAMILY.name, "Reasoning-trace validation");
    assert_eq!(FAMILY.host_check, "rational_lp_primal_dual_check");
}

#[test]
fn a_consistent_trace_with_its_potential_and_conclusion_is_certified() {
    let (passed, report) = run(&consistent(chain(), potential(), "c - a = 2"));
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "TRACE_VALID");
    assert_eq!(report["detail"], json!({"Phi": 0, "dual": [0, 0]}));
    assert_eq!(
        outcomes(&report),
        [
            ("status_matches_obstruction", true),
            ("potential_explains_steps", true),
            ("conclusion_forced_by_steps", true),
            ("conclusion_matches_steps", true),
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
        [
            sha(r#"{"Phi":0,"dual":[0,0]}"#),
            sha("[0,1,2]"),
            sha(r#"["c","a"]"#),
            sha(r#"["c","a",2]"#),
        ]
    );
    assert_eq!(report["asked"].as_array().expect("asked").len(), 1);
    assert_eq!(report["asked"][0]["stage"], "solve");
}

#[test]
fn the_prompt_is_the_family_prompt_for_the_task() {
    let Outcome::Pass { result } = next(&request(&[])) else {
        panic!("expected a turn");
    };
    assert_eq!(result["ask"]["stage"], "solve");
    let prompt = result["ask"]["prompt"].as_str().expect("a prompt");
    assert!(prompt.starts_with("WF42 Reasoning-trace validation. Reason in steps of the form"));
}

#[test]
fn an_obstructed_trace_with_a_minimal_correction_is_a_typed_refusal() {
    let (passed, report) = run(&obstructed(cycle(), json!([1, 0, 0])));
    assert!(passed);
    assert_eq!(report["verdict"], "TYPED_REFUSAL");
    assert_eq!(report["code"], "TRACE_OBSTRUCTED");
    assert_eq!(report["detail"], json!({"Phi": 1, "dual": [1, 1, 1]}));
    assert_eq!(
        outcomes(&report),
        [
            ("status_matches_obstruction", true),
            ("correction_closes_cycles", true),
            ("primal_equals_dual", true),
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
        [
            sha(r#"{"Phi":1,"dual":[1,1,1]}"#),
            sha("[1,0,0]"),
            sha(r#"{"Phi":1,"dual":[1,1,1]}"#),
        ]
    );
}

#[test]
fn any_minimal_correction_that_closes_the_cycle_will_do() {
    for correction in [json!([1, 0, 0]), json!([0, 1, 0]), json!([0, 0, 1])] {
        let (_, report) = run(&obstructed(cycle(), correction.clone()));
        assert_eq!(report["code"], "TRACE_OBSTRUCTED", "{correction}");
    }
}

#[test]
fn a_correction_is_sized_by_adding_up_its_entries() {
    let double = json!(["s1: b - a = 2", "s2: c - b = 0", "s3: a - c = 0"]);
    for correction in [json!([2, 0, 0]), json!([1, 1, 0]), json!([1, 0, 1])] {
        let (passed, report) = run(&obstructed(double.clone(), correction.clone()));
        assert!(passed, "{correction}");
        assert_eq!(report["code"], "TRACE_OBSTRUCTED", "{correction}");
        assert_eq!(report["detail"], json!({"Phi": 2, "dual": [1, 1, 1]}));
    }
    let (_, report) = run(&obstructed(double, json!([1, 0, 0])));
    assert_eq!(report["code"], "CORRECTION_CLOSES_CYCLES");
}

#[test]
fn a_correction_that_is_too_large_is_refused_by_its_size() {
    let (passed, report) = run(&obstructed(cycle(), json!([2, -1, 0])));
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "PRIMAL_EQUALS_DUAL");
    assert_eq!(
        report["detail"],
        json!({"Phi": 1, "dual": [1, 1, 1], "failed": ["primal_equals_dual"]})
    );
    assert_eq!(
        outcomes(&report),
        [
            ("status_matches_obstruction", true),
            ("correction_closes_cycles", true),
            ("primal_equals_dual", false),
        ]
    );
}

#[test]
fn a_correction_that_leaves_the_cycle_open_is_refused_by_its_cycle() {
    let (_, report) = run(&obstructed(cycle(), json!([-1, 0, 0])));
    assert_eq!(report["code"], "CORRECTION_CLOSES_CYCLES");
    assert_eq!(
        outcomes(&report),
        [
            ("status_matches_obstruction", true),
            ("correction_closes_cycles", false),
            ("primal_equals_dual", true),
        ]
    );
    let (_, report) = run(&obstructed(cycle(), json!([0, 0, 0])));
    assert_eq!(report["code"], "CORRECTION_CLOSES_CYCLES");
    assert_eq!(
        report["detail"]["failed"],
        json!(["correction_closes_cycles", "primal_equals_dual"])
    );
}

#[test]
fn an_obstruction_the_status_hides_is_refused_with_its_circulation() {
    let hidden = consistent(cycle(), potential(), "c - a = 1");
    let (passed, report) = run(&hidden);
    assert!(!passed);
    assert_eq!(report["code"], "HIDDEN_OBSTRUCTION");
    assert_eq!(report["detail"], json!({"Phi": 1, "dual": [1, 1, 1]}));
    assert_eq!(outcomes(&report), [("status_matches_obstruction", false)]);
}

#[test]
fn an_obstruction_claimed_where_there_is_none_is_refused() {
    let (passed, report) = run(&obstructed(chain(), json!([0, 0])));
    assert!(!passed);
    assert_eq!(report["code"], "FALSE_OBSTRUCTION");
    assert_eq!(report["detail"], json!({"Phi": 0, "dual": [0, 0]}));
    assert_eq!(outcomes(&report), [("status_matches_obstruction", false)]);
}

#[test]
fn a_potential_that_does_not_explain_the_steps_is_refused() {
    let reply = consistent(chain(), json!({"a": 0, "b": 1, "c": 3}), "c - a = 2");
    let (passed, report) = run(&reply);
    assert!(!passed);
    assert_eq!(report["code"], "POTENTIAL_EXPLAINS_STEPS");
    assert_eq!(
        report["detail"],
        json!({
            "Phi": 0,
            "dual": [0, 0],
            "failed": ["potential_explains_steps", "conclusion_matches_steps"],
        })
    );
    let reply = consistent(chain(), json!({"a": 5, "b": 6, "c": 7}), "c - a = 2");
    let (passed, _) = run(&reply);
    assert!(passed, "a shifted potential explains the same steps");
}

#[test]
fn a_conclusion_the_steps_contradict_is_refused() {
    let (passed, report) = run(&consistent(chain(), potential(), "c - a = 3"));
    assert!(!passed);
    assert_eq!(report["code"], "CONCLUSION_MATCHES_STEPS");
    assert_eq!(
        outcomes(&report),
        [
            ("status_matches_obstruction", true),
            ("potential_explains_steps", true),
            ("conclusion_forced_by_steps", true),
            ("conclusion_matches_steps", false),
        ]
    );
}

#[test]
fn a_conclusion_is_read_from_the_second_name_to_the_first() {
    let cases = [
        ("a - c = -2", true),
        ("b - a = 1", true),
        ("a - b = 1", false),
        ("c - a = -2", false),
    ];
    for (conclusion, holds) in cases {
        let (passed, report) = run(&consistent(chain(), potential(), conclusion));
        assert_eq!(passed, holds, "{conclusion}");
        if !holds {
            assert_eq!(report["code"], "CONCLUSION_MATCHES_STEPS", "{conclusion}");
        }
    }
}

#[test]
fn a_conclusion_joining_names_the_steps_do_not_join_is_not_forced() {
    let steps = json!(["b - a = 1", "d - c = 1"]);
    let held = json!({"a": 0, "b": 1, "c": 0, "d": 1});
    let (passed, report) = run(&consistent(steps.clone(), held.clone(), "c - a = 0"));
    assert!(!passed);
    assert_eq!(report["code"], "CONCLUSION_FORCED_BY_STEPS");
    assert_eq!(
        report["detail"]["failed"],
        json!(["conclusion_forced_by_steps", "conclusion_matches_steps"])
    );
    let (passed, _) = run(&consistent(steps, held, "b - a = 1"));
    assert!(passed);
}

#[test]
fn a_conclusion_naming_a_new_vertex_is_not_forced() {
    for conclusion in ["z - a = 0", "a - z = 0", "z - y = 0"] {
        let (passed, report) = run(&consistent(chain(), potential(), conclusion));
        assert!(!passed, "{conclusion}");
        assert_eq!(report["code"], "CONCLUSION_FORCED_BY_STEPS", "{conclusion}");
    }
}

#[test]
fn a_conclusion_about_one_name_says_it_differs_from_itself_by_zero() {
    let (passed, _) = run(&consistent(chain(), potential(), "a - a = 0"));
    assert!(passed);
    let (passed, report) = run(&consistent(chain(), potential(), "a - a = 1"));
    assert!(!passed);
    assert_eq!(report["code"], "CONCLUSION_MATCHES_STEPS");
}

#[test]
fn the_extra_entries_of_a_potential_and_a_reply_are_ignored() {
    let mut reply = consistent(
        chain(),
        json!({"a": 0, "b": 1, "c": 2, "zz": "anything"}),
        "c - a = 2",
    );
    reply["note"] = json!("ignored");
    reply["correction"] = json!("ignored");
    let (passed, report) = run(&reply);
    assert!(passed, "{report}");
}

#[test]
fn an_obstructed_reply_needs_no_potential_or_conclusion() {
    let (passed, report) = run(&obstructed(cycle(), json!([1, 0, 0])));
    assert!(passed, "{report}");
}

#[test]
fn the_first_of_several_best_circulations_is_reported() {
    let steps = json!(["b - a = 1", "a - b = 0", "a - b = 0"]);
    let (passed, report) = run(&obstructed(steps, json!([1, 0, 0])));
    assert!(passed);
    assert_eq!(report["detail"], json!({"Phi": 1, "dual": [1, 0, 1]}));
}

#[test]
fn parallel_steps_that_disagree_are_an_obstruction() {
    let steps = json!(["b - a = 1", "b - a = 2"]);
    let (passed, report) = run(&obstructed(steps, json!([0, 1])));
    assert!(passed);
    assert_eq!(report["detail"], json!({"Phi": 1, "dual": [-1, 1]}));
    let steps = json!(["b - a = 2", "b - a = 1"]);
    let (_, report) = run(&obstructed(steps, json!([1, 0])));
    assert_eq!(report["detail"], json!({"Phi": 1, "dual": [1, -1]}));
}

#[test]
fn parallel_steps_that_agree_are_consistent() {
    let steps = json!(["b - a = 2", "b - a = 2"]);
    let held = json!({"a": 0, "b": 2});
    let (passed, report) = run(&consistent(steps, held, "b - a = 2"));
    assert!(passed, "{report}");
    assert_eq!(report["detail"], json!({"Phi": 0, "dual": [0, 0]}));
}

#[test]
fn a_step_that_names_one_vertex_twice_is_a_loop() {
    let (passed, report) = run(&obstructed(json!(["a - a = 2"]), json!([2])));
    assert!(passed);
    assert_eq!(report["detail"], json!({"Phi": 2, "dual": [1]}));
    let (passed, report) = run(&obstructed(json!(["a - a = -3"]), json!([-3])));
    assert!(passed);
    assert_eq!(report["detail"], json!({"Phi": 3, "dual": [-1]}));
    let held = json!({"a": 7});
    let (passed, _) = run(&consistent(json!(["a - a = 0"]), held, "a - a = 0"));
    assert!(passed);
}

#[test]
fn an_obstruction_in_one_part_of_the_trace_is_found() {
    let steps = json!(["b - a = 1", "c - b = 0", "a - c = 0", "e - d = 4"]);
    let (passed, report) = run(&obstructed(steps, json!([1, 0, 0, 0])));
    assert!(passed);
    assert_eq!(report["detail"], json!({"Phi": 1, "dual": [1, 1, 1, 0]}));
}

#[test]
fn the_steps_may_hold_integers_of_any_size() {
    let steps = json!(["b - a = 99999999999999999999", "a - b = 0"]);
    let text = request(&[Some(obstructed(steps, json!([1, 0])))])
        .replace("[1,0]", "[99999999999999999999,0]");
    let Outcome::Pass { result } = judge(&text) else {
        panic!("expected a typed refusal");
    };
    assert_eq!(result["code"], "TRACE_OBSTRUCTED");
    assert_eq!(result["detail"]["Phi"], json!("99999999999999999999"));
}

#[test]
fn a_trace_of_eight_steps_is_read_and_one_of_nine_is_not() {
    let names = ["a", "b", "c", "d", "e", "f", "g", "h", "i"];
    let steps: Vec<String> = names
        .windows(2)
        .map(|pair| format!("{} - {} = 1", pair[1], pair[0]))
        .collect();
    assert_eq!(steps.len(), 8);
    let held: serde_json::Map<String, Value> = names
        .iter()
        .enumerate()
        .map(|(place, name)| ((*name).to_owned(), json!(place)))
        .collect();
    let reply = consistent(json!(steps), Value::Object(held.clone()), "i - a = 8");
    let (passed, report) = run(&reply);
    assert!(passed, "{report}");
    assert_eq!(report["detail"]["dual"], json!([0, 0, 0, 0, 0, 0, 0, 0]));
    let mut longer = steps;
    longer.push("j - i = 1".to_owned());
    let reply = consistent(json!(longer), Value::Object(held), "i - a = 8");
    assert_eq!(malformed(&reply), "trace graphs are limited to 8 claims");
}

#[test]
fn a_trace_of_no_steps_has_nothing_to_conclude_from() {
    let (passed, report) = run(&consistent(json!([]), json!({}), "a - a = 0"));
    assert!(!passed);
    assert_eq!(report["code"], "CONCLUSION_FORCED_BY_STEPS");
    assert_eq!(report["detail"]["Phi"], 0);
    assert_eq!(report["detail"]["dual"], json!([]));
    let (_, report) = run(&obstructed(json!([]), json!([])));
    assert_eq!(report["code"], "FALSE_OBSTRUCTION");
}

#[test]
fn a_step_is_a_pair_of_lowercase_names_and_a_whole_number() {
    let readable = [
        "b - a = 1",
        "b-a=1",
        "  s1:   b - a = 1  ",
        "b - a = 1\n",
        "lbl_9: bb_2 - a3 = -0",
        "b \t- \t a = 00",
    ];
    for step in readable {
        let reply = json!({"trace": [step], "status": "OBSTRUCTED", "correction": [0]});
        let (_, report) = run(&reply);
        assert_eq!(report["code"], "FALSE_OBSTRUCTION", "{step:?}");
    }
    let unreadable = [
        "B - a = 1",
        "b - A = 1",
        "1 - a = 1",
        "_b - a = 1",
        "b - a = +1",
        "b - a = 1.0",
        "b - a = ",
        "b - a",
        "b - a = one",
        "b - a - c = 1",
        "b exceeds a by one",
        "s 1: b - a = 1",
        "s1 b - a = 1",
        ": b - a = 1",
        "b - a = 1 and more",
        "",
    ];
    for step in unreadable {
        let reply = json!({"trace": [step], "status": "CONSISTENT"});
        let reason = malformed(&reply);
        assert_eq!(
            reason,
            format!("extractor cannot parse step {step:?}"),
            "{step:?}"
        );
    }
}

#[test]
fn a_step_that_is_not_text_stops_the_run() {
    for step in [
        json!(1),
        json!(null),
        json!(["b - a = 1"]),
        json!({"step": "b - a = 1"}),
    ] {
        let reply = json!({"trace": [step], "status": "CONSISTENT"});
        assert_eq!(malformed(&reply), "trace steps must be strings", "{reply}");
    }
}

#[test]
fn the_reply_must_be_an_object_with_a_trace_and_a_status() {
    assert_eq!(malformed(&json!("a - b = 1")), "trace list required");
    assert_eq!(malformed(&json!([chain()])), "trace list required");
    assert_eq!(
        malformed(&json!({"status": "CONSISTENT"})),
        "trace list required"
    );
    for trace in [json!("b - a = 1"), json!(null), json!({"s1": "b - a = 1"})] {
        let reply = json!({"trace": trace, "status": "CONSISTENT"});
        assert_eq!(malformed(&reply), "trace list required", "{reply}");
    }
    let wrong = [
        json!({"trace": []}),
        json!({"trace": [], "status": "consistent"}),
        json!({"trace": [], "status": "OBSTRUCTED "}),
        json!({"trace": [], "status": true}),
        json!({"trace": [], "status": ["CONSISTENT"]}),
        json!({"trace": [], "status": "VALID"}),
    ];
    for reply in wrong {
        assert_eq!(
            malformed(&reply),
            "status must be CONSISTENT or OBSTRUCTED",
            "{reply}"
        );
    }
}

#[test]
fn the_trace_is_checked_before_the_status_and_the_status_before_the_steps() {
    let reply = json!({"trace": ["not a step"], "status": "maybe"});
    assert_eq!(malformed(&reply), "status must be CONSISTENT or OBSTRUCTED");
    let reply = json!({"trace": "not a list", "status": "maybe"});
    assert_eq!(malformed(&reply), "trace list required");
}

#[test]
fn a_correction_must_be_one_exact_integer_for_each_step() {
    let cases = [
        (json!(null), "correction must be a list of exact integers"),
        (
            json!("1,0,0"),
            "correction must be a list of exact integers",
        ),
        (
            json!({"0": 1}),
            "correction must be a list of exact integers",
        ),
        (
            json!([1, 0, 0.5]),
            "correction must be a list of exact integers",
        ),
        (
            json!([1, 0, "0"]),
            "correction must be a list of exact integers",
        ),
        (
            json!([1, 0, true]),
            "correction must be a list of exact integers",
        ),
        (
            json!([1, 0, null]),
            "correction must be a list of exact integers",
        ),
        (json!([1, 0]), "one correction per step"),
        (json!([1, 0, 0, 0]), "one correction per step"),
        (json!([]), "one correction per step"),
    ];
    for (correction, reason) in cases {
        let reply = obstructed(cycle(), correction.clone());
        assert_eq!(malformed(&reply), reason, "{correction}");
    }
    let mut missing = obstructed(cycle(), json!([1, 0, 0]));
    missing
        .as_object_mut()
        .expect("object")
        .remove("correction");
    assert_eq!(
        malformed(&missing),
        "correction must be a list of exact integers"
    );
}

#[test]
fn a_potential_must_give_an_exact_integer_for_every_name() {
    let cases = [
        (json!({"a": 0, "b": 1}), "potential must be an exact int"),
        (
            json!({"a": 0, "b": 1, "c": 2.0}),
            "potential must be an exact int",
        ),
        (
            json!({"a": 0, "b": "1", "c": 2}),
            "potential must be an exact int",
        ),
        (
            json!({"a": 0, "b": 1, "c": null}),
            "potential must be an exact int",
        ),
        (
            json!({"a": 0, "b": 1, "c": true}),
            "potential must be an exact int",
        ),
        (
            json!({"a": 0, "b": 1, "c": [2]}),
            "potential must be an exact int",
        ),
        (json!({}), "potential must be an exact int"),
        (json!([0, 1, 2]), "potential object required"),
        (json!("a=0"), "potential object required"),
        (json!(null), "potential object required"),
    ];
    for (given, reason) in cases {
        let reply = consistent(chain(), given.clone(), "c - a = 2");
        assert_eq!(malformed(&reply), reason, "{given}");
    }
    let mut missing = consistent(chain(), potential(), "c - a = 2");
    missing.as_object_mut().expect("object").remove("potential");
    assert_eq!(malformed(&missing), "potential object required");
}

#[test]
fn a_conclusion_must_be_a_readable_step() {
    for conclusion in [
        json!("c is two above a"),
        json!(2),
        json!(null),
        json!(["c - a = 2"]),
    ] {
        let mut reply = consistent(chain(), potential(), "c - a = 2");
        reply["conclusion"] = conclusion.clone();
        let reason = malformed(&reply);
        assert!(
            reason == "trace steps must be strings"
                || reason.starts_with("extractor cannot parse step"),
            "{conclusion}: {reason}"
        );
    }
    let mut missing = consistent(chain(), potential(), "c - a = 2");
    missing
        .as_object_mut()
        .expect("object")
        .remove("conclusion");
    assert_eq!(malformed(&missing), "trace steps must be strings");
}

#[test]
fn the_potential_is_read_before_the_conclusion() {
    let mut reply = consistent(chain(), json!({"a": 0}), "not a step");
    assert_eq!(malformed(&reply), "potential must be an exact int");
    reply["potential"] = potential();
    assert_eq!(
        malformed(&reply),
        "extractor cannot parse step \"not a step\""
    );
}

#[test]
fn a_missing_reply_stops_the_run() {
    let Outcome::Fail { result } = judge(&request(&[None])) else {
        panic!("expected a refused run");
    };
    assert_eq!(result["verdict"], "REFUSED");
    assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
    assert_eq!(result["predicates"], json!([]));
}

#[test]
fn a_second_reply_is_not_accepted() {
    let both = [
        Some(consistent(chain(), potential(), "c - a = 2")),
        Some(consistent(chain(), potential(), "c - a = 2")),
    ];
    match judge(&request(&both)) {
        Outcome::Refused { refusal } => assert_eq!(refusal.code, "BAD_REQUEST"),
        other => panic!("expected a refusal, got {other:?}"),
    }
}
