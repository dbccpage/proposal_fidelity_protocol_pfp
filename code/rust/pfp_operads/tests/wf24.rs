//! WF24, pinned-token scratchpad: the loop's holonomy folded two ways, against echoed tokens,
//! shown partial products, and the claimed holonomy and flatness.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf24-tests:v1

use pfp_operads::families::wf24::{FAMILY, MAX_LOOP, MAX_POINTS};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

/// A loop whose holonomy is the swap of points 0 and 2: `e1`, then `e2`, then `e1` undone.
fn twisted() -> Value {
    json!({"statement": "Fold the loop.", "n": 3,
           "links": {"e1": [1, 2, 0], "e2": [1, 0, 2]},
           "loop": ["e1+", "e2+", "e1-"]})
}

fn twisted_reply() -> Value {
    json!({"tokens": ["e1+", "e2+", "e1-"],
           "scratchpad": [[1, 2, 0], [0, 2, 1], [2, 1, 0]],
           "holonomy": [2, 1, 0], "flat": false})
}

fn flat() -> Value {
    json!({"n": 3, "links": {"e1": [1, 2, 0]}, "loop": ["e1+", "e1-"]})
}

fn flat_reply() -> Value {
    json!({"tokens": ["e1+", "e1-"], "scratchpad": [[1, 2, 0], [0, 1, 2]],
           "holonomy": [0, 1, 2], "flat": true})
}

fn with(mut reply: Value, key: &str, value: Value) -> Value {
    reply[key] = value;
    reply
}

/// The report of the run with this one reply, and whether the host passed it.
fn run(task: Value, content: Value) -> (bool, Value) {
    let request = json!({"workflow": "WF24", "task": task, "replies": [{"content": content}]});
    match judge(&request.to_string()) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn turn(task: Value) -> Outcome {
    next(&json!({"workflow": "WF24", "task": task}).to_string())
}

fn bad_task(task: Value) -> String {
    match turn(task) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

fn accepted(task: Value) {
    match turn(task) {
        Outcome::Pass { result } => assert_eq!(result["ask"]["stage"], "solve"),
        other => panic!("expected a turn, got {other:?}"),
    }
}

fn malformed(task: Value, content: Value) -> String {
    let (passed, report) = run(task, content);
    assert!(!passed);
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    assert_eq!(report["predicates"], json!([]));
    report["detail"]["reason"]
        .as_str()
        .expect("reason")
        .to_owned()
}

/// The names of the predicates that failed, in the order recorded.
fn failed(report: &Value) -> Vec<String> {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .filter(|row| row["passed"] == false)
        .map(|row| row["name"].as_str().expect("name").to_owned())
        .collect()
}

fn evidence(report: &Value, name: &str) -> String {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .find(|row| row["name"] == name)
        .unwrap_or_else(|| panic!("no predicate {name}"))["evidence_sha256"]
        .as_str()
        .expect("evidence")
        .to_owned()
}

#[test]
fn the_family_is_registered_under_its_names_and_limits() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF24",
            "Pinned-token operational scratchpad",
            "dual_holonomy_checkers"
        )
    );
    assert_eq!((MAX_POINTS, MAX_LOOP), (64, 4096));
}

#[test]
fn a_loop_folded_step_by_step_is_certified() {
    let (passed, report) = run(twisted(), twisted_reply());
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "CERTIFIED");
    assert_eq!(
        report["detail"],
        json!({"holonomy": [2, 1, 0], "flat": false, "first_bad_step": null})
    );
    assert_eq!(
        report["predicates"],
        json!([
            {"name": "tokens_pinned", "passed": true, "evidence_sha256": sha(r#"["e1+","e2+","e1-"]"#)},
            {"name": "scratchpad_steps_exact", "passed": true, "evidence_sha256": sha("null")},
            {"name": "dual_checkers_agree", "passed": true,
             "evidence_sha256": sha(r#"{"composed":[2,1,0],"matrices":[2,1,0]}"#)},
            {"name": "holonomy_matches", "passed": true, "evidence_sha256": sha("[2,1,0]")},
            {"name": "flatness_matches", "passed": true, "evidence_sha256": sha("false")},
        ])
    );
    assert_eq!(report["asked"].as_array().map(Vec::len), Some(1));
    assert_eq!(report["asked"][0]["stage"], "solve");
}

#[test]
fn a_loop_that_closes_is_certified_as_flat() {
    let (passed, report) = run(flat(), flat_reply());
    assert!(passed);
    assert_eq!(
        report["detail"],
        json!({"holonomy": [0, 1, 2], "flat": true, "first_bad_step": null})
    );
    assert_eq!(evidence(&report, "flatness_matches"), sha("true"));
}

#[test]
fn a_backward_token_is_the_inverse_of_its_link_not_the_link() {
    let task = json!({"n": 3, "links": {"e1": [1, 2, 0]}, "loop": ["e1-"]});
    let inverse =
        json!({"tokens": ["e1-"], "scratchpad": [[2, 0, 1]], "holonomy": [2, 0, 1], "flat": false});
    assert!(run(task.clone(), inverse).0);
    let forward =
        json!({"tokens": ["e1-"], "scratchpad": [[1, 2, 0]], "holonomy": [1, 2, 0], "flat": false});
    let (passed, report) = run(task, forward);
    assert!(!passed);
    assert_eq!(
        failed(&report),
        ["scratchpad_steps_exact", "holonomy_matches"]
    );
}

#[test]
fn links_are_applied_in_loop_order() {
    // e1 then e2 sends 0 to e2[e1[0]] = 0; e2 then e1 sends 0 to e1[e2[0]] = 2.
    let task = json!({"n": 3, "links": {"e1": [1, 2, 0], "e2": [1, 0, 2]}, "loop": ["e1+", "e2+"]});
    let in_order = json!({"tokens": ["e1+", "e2+"], "scratchpad": [[1, 2, 0], [0, 2, 1]],
                          "holonomy": [0, 2, 1], "flat": false});
    assert!(run(task.clone(), in_order).0);
    let reversed = json!({"tokens": ["e1+", "e2+"], "scratchpad": [[1, 2, 0], [2, 1, 0]],
                          "holonomy": [2, 1, 0], "flat": false});
    let (passed, report) = run(task, reversed);
    assert!(!passed);
    assert_eq!(report["detail"]["first_bad_step"], 1);
    assert_eq!(report["detail"]["holonomy"], json!([0, 2, 1]));
}

#[test]
fn tokens_that_are_not_the_loop_s_fail_alone() {
    for tokens in [
        json!(["e1+", "e2+"]),
        json!(["e1+", "e2+", "e1+"]),
        json!(["e2+", "e1+", "e1-"]),
        json!(["e1+", "e2+", "e1-", "e1+"]),
        json!([]),
    ] {
        let written = tokens.to_string();
        let (passed, report) = run(twisted(), with(twisted_reply(), "tokens", tokens));
        assert!(!passed);
        assert_eq!(report["verdict"], "REFUSED");
        assert_eq!(report["code"], "TOKENS_PINNED");
        assert_eq!(failed(&report), ["tokens_pinned"]);
        assert_eq!(evidence(&report, "tokens_pinned"), sha(&written));
        assert_eq!(
            report["detail"],
            json!({"holonomy": [2, 1, 0], "flat": false, "first_bad_step": null,
                   "failed": ["tokens_pinned"]})
        );
    }
}

#[test]
fn a_wrong_partial_product_fails_alone_and_is_located() {
    for (scratchpad, step) in [
        (json!([[0, 1, 2], [0, 2, 1], [2, 1, 0]]), 0),
        (json!([[1, 2, 0], [0, 1, 2], [2, 1, 0]]), 1),
        (json!([[1, 2, 0], [0, 2, 1], [0, 1, 2]]), 2),
        (json!([[1, 2, 0], [2, 1, 0], [0, 2, 1]]), 1),
    ] {
        let (passed, report) = run(twisted(), with(twisted_reply(), "scratchpad", scratchpad));
        assert!(!passed);
        assert_eq!(report["code"], "SCRATCHPAD_STEPS_EXACT");
        assert_eq!(failed(&report), ["scratchpad_steps_exact"]);
        assert_eq!(report["detail"]["first_bad_step"], step);
        assert_eq!(
            evidence(&report, "scratchpad_steps_exact"),
            sha(&step.to_string())
        );
    }
}

#[test]
fn a_scratchpad_of_the_wrong_length_fails_at_the_first_step_one_side_lacks() {
    for (scratchpad, step) in [
        (json!([]), 0),
        (json!([[1, 2, 0]]), 1),
        (json!([[1, 2, 0], [0, 2, 1]]), 2),
        (json!([[1, 2, 0], [0, 2, 1], [2, 1, 0], [2, 1, 0]]), 3),
        (json!([[1, 2, 0], [0, 1, 2], [2, 1, 0], [2, 1, 0]]), 1),
    ] {
        let (passed, report) = run(twisted(), with(twisted_reply(), "scratchpad", scratchpad));
        assert!(!passed);
        assert_eq!(failed(&report), ["scratchpad_steps_exact"]);
        assert_eq!(report["detail"]["first_bad_step"], step);
    }
}

#[test]
fn a_wrong_holonomy_fails_alone() {
    let (passed, report) = run(
        twisted(),
        with(twisted_reply(), "holonomy", json!([0, 1, 2])),
    );
    assert!(!passed);
    assert_eq!(report["code"], "HOLONOMY_MATCHES");
    assert_eq!(failed(&report), ["holonomy_matches"]);
    assert_eq!(evidence(&report, "holonomy_matches"), sha("[2,1,0]"));
    assert_eq!(report["detail"]["holonomy"], json!([2, 1, 0]));
}

#[test]
fn a_wrong_flatness_fails_alone() {
    let (passed, report) = run(twisted(), with(twisted_reply(), "flat", json!(true)));
    assert!(!passed);
    assert_eq!(report["code"], "FLATNESS_MATCHES");
    assert_eq!(failed(&report), ["flatness_matches"]);
    assert_eq!(evidence(&report, "flatness_matches"), sha("false"));

    let (passed, report) = run(flat(), with(flat_reply(), "flat", json!(false)));
    assert!(!passed);
    assert_eq!(failed(&report), ["flatness_matches"]);
    assert_eq!(report["detail"]["flat"], true);
}

#[test]
fn every_failure_is_reported_together() {
    let reply =
        json!({"tokens": ["e1+"], "scratchpad": [[0, 1, 2]], "holonomy": [0, 1, 2], "flat": true});
    let (passed, report) = run(twisted(), reply);
    assert!(!passed);
    assert_eq!(report["code"], "TOKENS_PINNED");
    assert_eq!(
        report["detail"]["failed"],
        json!([
            "tokens_pinned",
            "scratchpad_steps_exact",
            "holonomy_matches",
            "flatness_matches"
        ])
    );
    assert_eq!(report["detail"]["first_bad_step"], 0);
}

#[test]
fn a_reply_without_its_parts_is_malformed() {
    let parts = "tokens and scratchpad required";
    for (key, value) in [
        ("tokens", Value::Null),
        ("tokens", json!("e1+ e2+ e1-")),
        ("tokens", json!({"0": "e1+"})),
        ("scratchpad", Value::Null),
        ("scratchpad", json!("[1, 2, 0]")),
        ("scratchpad", json!({"0": [1, 2, 0]})),
    ] {
        assert_eq!(
            malformed(twisted(), with(twisted_reply(), key, value)),
            parts
        );
    }
    for key in ["tokens", "scratchpad"] {
        let mut reply = twisted_reply();
        reply.as_object_mut().expect("object").remove(key);
        assert_eq!(malformed(twisted(), reply), parts);
    }
    for value in [json!(0), json!("false"), Value::Null, json!([false])] {
        assert_eq!(
            malformed(twisted(), with(twisted_reply(), "flat", value)),
            "flat must be a bool"
        );
    }
    let mut reply = twisted_reply();
    reply.as_object_mut().expect("object").remove("flat");
    assert_eq!(malformed(twisted(), reply), "flat must be a bool");
}

#[test]
fn a_scratchpad_entry_or_holonomy_that_is_not_a_permutation_is_malformed() {
    for entry in [
        json!([1, 2]),
        json!([1, 2, 0, 3]),
        json!([1, 1, 0]),
        json!([1, 2, 3]),
        json!([1, 2, 0.0]),
        json!("120"),
    ] {
        let scratchpad = json!([entry, [0, 2, 1], [2, 1, 0]]);
        let (passed, report) = run(twisted(), with(twisted_reply(), "scratchpad", scratchpad));
        assert!(!passed);
        assert_eq!(report["code"], "MALFORMED_CANDIDATE");
        assert_eq!(
            report["detail"],
            json!({"reason": "every scratchpad entry must be a permutation of 3 points"})
        );
        assert_eq!(
            malformed(twisted(), with(twisted_reply(), "holonomy", entry)),
            "holonomy must be a permutation of 3 points"
        );
    }
    let mut reply = twisted_reply();
    reply.as_object_mut().expect("object").remove("holonomy");
    assert_eq!(
        malformed(twisted(), reply),
        "holonomy must be a permutation of 3 points"
    );
}

#[test]
fn the_reply_s_parts_are_read_in_a_fixed_order() {
    let nothing = json!({});
    assert_eq!(
        malformed(twisted(), nothing),
        "tokens and scratchpad required"
    );
    let no_flat = json!({"tokens": [], "scratchpad": [[9]], "holonomy": 1});
    assert_eq!(malformed(twisted(), no_flat), "flat must be a bool");
    let bad_pad = json!({"tokens": [], "scratchpad": [[9]], "holonomy": 1, "flat": true});
    assert_eq!(
        malformed(twisted(), bad_pad),
        "every scratchpad entry must be a permutation of 3 points"
    );
}

#[test]
fn the_number_of_points_is_an_exact_integer_within_the_limit() {
    let points = "n must be an exact integer from 1 to 64";
    let task = |n: Value| json!({"n": n, "links": {}, "loop": []});
    for n in [
        json!(0),
        json!(65),
        json!(-1),
        json!("3"),
        json!(3.0),
        Value::Null,
    ] {
        assert_eq!(bad_task(task(n)), points);
    }
    assert_eq!(bad_task(json!({"links": {}, "loop": []})), points);
    let identity: Vec<usize> = (0..64).collect();
    accepted(json!({"n": 64, "links": {"e1": identity}, "loop": ["e1+"]}));
    accepted(json!({"n": 1, "links": {"e1": [0]}, "loop": ["e1-"]}));
}

#[test]
fn every_link_is_a_permutation_of_the_task_s_points() {
    let task = |links: Value| json!({"n": 3, "links": links, "loop": ["e1+"]});
    for links in [json!([[1, 2, 0]]), json!("e1"), Value::Null] {
        assert_eq!(bad_task(task(links)), "links must be an object");
    }
    assert_eq!(
        bad_task(json!({"n": 3, "loop": ["e1+"]})),
        "links must be an object"
    );
    for link in [
        json!([1, 2]),
        json!([0, 0, 1]),
        json!([1, 2, 3]),
        json!("120"),
        json!([0, 1, 2, 3]),
    ] {
        assert_eq!(
            bad_task(task(json!({"e1": [1, 2, 0], "e2": link}))),
            "every link must be a permutation of 3 points"
        );
    }
}

#[test]
fn the_loop_has_between_one_and_the_limit_of_tokens() {
    let length = "loop must be a list of 1 to 4096 tokens";
    let task = |tokens: Value| json!({"n": 2, "links": {"e1": [1, 0]}, "loop": tokens});
    assert_eq!(bad_task(task(json!([]))), length);
    assert_eq!(bad_task(task(json!("e1+"))), length);
    assert_eq!(bad_task(task(Value::Null)), length);
    assert_eq!(bad_task(json!({"n": 2, "links": {"e1": [1, 0]}})), length);
    assert_eq!(bad_task(task(json!(vec!["e1+"; 4097]))), length);
    accepted(task(json!(vec!["e1+"; 4096])));
}

#[test]
fn a_loop_at_the_limit_is_folded_exactly() {
    // 4096 swaps of two points: an even number, so the loop closes.
    let tokens = vec!["e1+"; 4096];
    let scratchpad: Vec<Value> = (0..4096)
        .map(|step| {
            if step % 2 == 0 {
                json!([1, 0])
            } else {
                json!([0, 1])
            }
        })
        .collect();
    let task = json!({"n": 2, "links": {"e1": [1, 0]}, "loop": tokens});
    let reply =
        json!({"tokens": tokens, "scratchpad": scratchpad, "holonomy": [0, 1], "flat": true});
    let (passed, report) = run(task, reply);
    assert!(passed);
    assert_eq!(report["detail"]["holonomy"], json!([0, 1]));
}

#[test]
fn a_token_is_a_declared_link_with_a_direction() {
    let pinned = "loop tokens must be pinned eK+ / eK- on declared links";
    let task = |token: Value| {
        json!({"n": 2, "links": {"e1": [1, 0], "f1": [1, 0], "e": [1, 0], "e١": [1, 0],
                                                         "e1x": [1, 0], "1": [1, 0]},
                                     "loop": ["e1+", token]})
    };
    for token in [
        json!("e1"),
        json!("e2+"),
        json!("f1+"),
        json!("e+"),
        json!("e١+"),
        json!("e1x+"),
        json!("1+"),
        json!("+"),
        json!(""),
        json!("e1*"),
        json!(" e1+"),
        json!(1),
        json!(["e1+"]),
        Value::Null,
    ] {
        assert_eq!(bad_task(task(token)), pinned);
    }
    accepted(task(json!("e1-")));
    accepted(json!({"n": 2, "links": {"e10": [1, 0]}, "loop": ["e10+"]}));
}
