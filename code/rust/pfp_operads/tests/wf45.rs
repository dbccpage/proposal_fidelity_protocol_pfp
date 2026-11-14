//! WF45, finite terminal selector: the terminal the survivor set gives, the survivor when there
//! is one, the whole declared family, and the twin that shows acceptance is relative to it.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf45-tests:v1

use pfp_operads::families::wf45::{
    ACCEPTED, FAMILY, REFUSED_TERMINAL, REFUTED, TERMINALS, TWIN, UNDERDETERMINED_TERMINAL,
};
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

/// a = 1 + 2x, b = 1 + x^2, c = 1 + x + x^2.
fn family() -> Value {
    json!({"a": [1, 2], "b": [1, 0, 1], "c": [1, 1, 1]})
}

/// Two observations that keep `a` and `c`.
fn under() -> Value {
    json!({"statement": "Pick the candidate the evidence selects.", "family": family(),
           "evidence": [{"x": 0, "y": 1}, {"x": 1, "y": 3, "tol": "1/10"}]})
}

/// A third observation that drops `c`: a(2) = 5 is within 1/5 of 49/10, and c(2) = 7 is not.
fn unique() -> Value {
    json!({"family": family(),
           "evidence": [{"x": 0, "y": 1}, {"x": 1, "y": 3, "tol": "1/10"}, {"x": 2, "y": "49/10", "tol": "1/5"}]})
}

fn refuted() -> Value {
    json!({"family": family(), "evidence": [{"x": 0, "y": 5}]})
}

fn reply(terminal: &str, selected: Value) -> Value {
    json!({"terminal": terminal, "selected": selected, "family_considered": ["a", "b", "c"]})
}

/// The report of the run with this one reply, and whether the host passed it.
fn run(task: Value, content: Value) -> (bool, Value) {
    let request = json!({"workflow": "WF45", "task": task, "replies": [{"content": content}]});
    match judge(&request.to_string()) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn turn(task: Value) -> Outcome {
    next(&json!({"workflow": "WF45", "task": task}).to_string())
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

fn malformed(content: Value) -> String {
    let (passed, report) = run(unique(), content);
    assert!(!passed);
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    assert_eq!(report["predicates"], json!([]));
    report["detail"]["reason"]
        .as_str()
        .expect("reason")
        .to_owned()
}

fn names(report: &Value) -> Vec<String> {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| row["name"].as_str().expect("name").to_owned())
        .collect()
}

fn failed(report: &Value) -> Vec<String> {
    report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .filter(|row| row["passed"] == false)
        .map(|row| row["name"].as_str().expect("name").to_owned())
        .collect()
}

fn evidence_of(report: &Value, name: &str) -> String {
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

/// The survivors the host finds for a family under some evidence, and the truth it reports.
fn survivors(family: Value, evidence: Value) -> (Value, Value) {
    let ids: Vec<String> = family
        .as_object()
        .expect("family")
        .keys()
        .cloned()
        .collect();
    let content = json!({"terminal": "Refused", "family_considered": ids});
    let (_, report) = run(json!({"family": family, "evidence": evidence}), content);
    (
        report["detail"]["survivors"].clone(),
        report["detail"]["terminal"].clone(),
    )
}

#[test]
fn the_family_is_registered_under_its_names_and_terminals() {
    assert_eq!(
        (FAMILY.workflow, FAMILY.name, FAMILY.host_check),
        (
            "WF45",
            "Finite terminal selector and plenitude test",
            "finite_survivor_set_verifier"
        )
    );
    assert_eq!(
        (
            ACCEPTED,
            UNDERDETERMINED_TERMINAL,
            REFUTED,
            REFUSED_TERMINAL
        ),
        ("Accepted", "Underdetermined", "Refuted", "Refused")
    );
    assert_eq!(
        TERMINALS,
        ["Accepted", "Underdetermined", "Refuted", "Refused"]
    );
    assert_eq!(TWIN, "~twin");
}

#[test]
fn the_one_survivor_is_accepted_within_the_declared_family() {
    let (passed, report) = run(unique(), reply("Accepted", json!("a")));
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "ACCEPTED_WITHIN_FAMILY");
    assert_eq!(
        report["detail"],
        json!({"survivors": ["a"], "terminal": "Accepted"})
    );
    assert_eq!(
        report["predicates"],
        json!([
            {"name": "declared_family_kept", "passed": true, "evidence_sha256": sha(r#"["a","b","c"]"#)},
            {"name": "terminal_matches_survivor_set", "passed": true,
             "evidence_sha256": sha(r#"{"survivors":["a"],"terminal":"Accepted"}"#)},
            {"name": "selection_is_the_survivor", "passed": true, "evidence_sha256": sha(r#""a""#)},
            {"name": "plenitude_raises_survivor_count", "passed": true, "evidence_sha256": sha(r#"{"after":2,"before":1,"twin":["1/1","4/1","-3/1","1/1"]}"#)},
        ])
    );
    assert_eq!(report["uncertified_obligations"], json!([]));
    assert_eq!(report["asked"][0]["stage"], "solve");
    assert_eq!(report["asked"].as_array().map(Vec::len), Some(1));
}

#[test]
fn several_survivors_are_a_typed_refusal_not_a_selection() {
    let (passed, report) = run(under(), reply("Underdetermined", Value::Null));
    assert!(passed);
    assert_eq!(report["verdict"], "TYPED_REFUSAL");
    assert_eq!(report["code"], "UNRESOLVED_UNDERDETERMINED");
    assert_eq!(
        report["detail"],
        json!({"survivors": ["a", "c"], "terminal": "Underdetermined"})
    );
    assert_eq!(
        names(&report),
        [
            "declared_family_kept",
            "terminal_matches_survivor_set",
            "plenitude_raises_survivor_count"
        ]
    );
    assert_eq!(
        evidence_of(&report, "terminal_matches_survivor_set"),
        sha(r#"{"survivors":["a","c"],"terminal":"Underdetermined"}"#)
    );
    assert_eq!(
        evidence_of(&report, "plenitude_raises_survivor_count"),
        sha(r#"{"after":3,"before":2,"twin":["1/1","1/1","1/1"]}"#)
    );
    // Naming one of them changes nothing: the selection is only read when one survives.
    let (passed, report) = run(under(), reply("Underdetermined", json!("a")));
    assert!(passed);
    assert_eq!(report["code"], "UNRESOLVED_UNDERDETERMINED");
}

#[test]
fn no_survivor_is_a_typed_refusal_with_no_plenitude_test() {
    let (passed, report) = run(refuted(), reply("Refuted", Value::Null));
    assert!(passed);
    assert_eq!(report["verdict"], "TYPED_REFUSAL");
    assert_eq!(report["code"], "UNRESOLVED_INCONSISTENT");
    assert_eq!(
        report["detail"],
        json!({"survivors": [], "terminal": "Refuted"})
    );
    assert_eq!(
        names(&report),
        ["declared_family_kept", "terminal_matches_survivor_set"]
    );
}

#[test]
fn an_empty_family_or_no_evidence_is_refused_as_undeclared() {
    let no_evidence = json!({"family": family(), "evidence": []});
    let (passed, report) = run(no_evidence, reply("Refused", Value::Null));
    assert!(passed);
    assert_eq!(report["verdict"], "TYPED_REFUSAL");
    assert_eq!(report["code"], "REFUSED_UNDECLARED_FAMILY");
    assert_eq!(
        report["detail"],
        json!({"survivors": ["a", "b", "c"], "terminal": "Refused"})
    );
    assert_eq!(
        evidence_of(&report, "plenitude_raises_survivor_count"),
        sha(r#"{"after":4,"before":3,"twin":["2/1","2/1"]}"#)
    );

    let no_family = json!({"family": {}, "evidence": [{"x": 0, "y": 1}]});
    let content = json!({"terminal": "Refused", "family_considered": []});
    let (passed, report) = run(no_family.clone(), content);
    assert!(passed);
    assert_eq!(report["code"], "REFUSED_UNDECLARED_FAMILY");
    assert_eq!(
        report["detail"],
        json!({"survivors": [], "terminal": "Refused"})
    );
    let (passed, report) = run(
        no_family,
        json!({"terminal": "Refuted", "family_considered": []}),
    );
    assert!(!passed);
    assert_eq!(failed(&report), ["terminal_matches_survivor_set"]);

    // One candidate and no evidence is still refused, not accepted.
    let lone = json!({"family": {"a": [1]}, "evidence": []});
    let content = json!({"terminal": "Accepted", "selected": "a", "family_considered": ["a"]});
    let (passed, report) = run(lone, content);
    assert!(!passed);
    assert_eq!(report["detail"]["terminal"], "Refused");
    assert_eq!(failed(&report), ["terminal_matches_survivor_set"]);
}

#[test]
fn a_terminal_the_survivors_do_not_give_fails_alone() {
    for (task, truth, claims) in [
        (
            under(),
            "Underdetermined",
            ["Accepted", "Refuted", "Refused"],
        ),
        (
            refuted(),
            "Refuted",
            ["Accepted", "Underdetermined", "Refused"],
        ),
        (
            json!({"family": family(), "evidence": []}),
            "Refused",
            ["Accepted", "Underdetermined", "Refuted"],
        ),
    ] {
        for claim in claims {
            let (passed, report) = run(task.clone(), reply(claim, json!("a")));
            assert!(!passed, "{truth} claimed as {claim}");
            assert_eq!(report["verdict"], "REFUSED");
            assert_eq!(report["code"], "TERMINAL_MATCHES_SURVIVOR_SET");
            assert_eq!(failed(&report), ["terminal_matches_survivor_set"]);
            assert_eq!(report["detail"]["terminal"], truth);
            // The selection is read only when one candidate survives, whatever the reply claims.
            assert!(!names(&report).contains(&"selection_is_the_survivor".to_owned()));
            assert_eq!(
                report["detail"]["failed"],
                json!(["terminal_matches_survivor_set"])
            );
        }
    }
    for claim in ["Underdetermined", "Refuted", "Refused"] {
        let (passed, report) = run(unique(), reply(claim, json!("a")));
        assert!(!passed);
        assert_eq!(failed(&report), ["terminal_matches_survivor_set"]);
        assert_eq!(report["detail"]["survivors"], json!(["a"]));
        // The evidence is the terminal the survivors give, not the one the reply claimed.
        assert_eq!(
            evidence_of(&report, "terminal_matches_survivor_set"),
            sha(r#"{"survivors":["a"],"terminal":"Accepted"}"#)
        );
        assert_eq!(
            names(&report),
            [
                "declared_family_kept",
                "terminal_matches_survivor_set",
                "selection_is_the_survivor",
                "plenitude_raises_survivor_count"
            ]
        );
    }
}

#[test]
fn a_family_other_than_the_declared_one_fails_alone() {
    for considered in [
        json!(["a", "b"]),
        json!(["a"]),
        json!([]),
        json!(["a", "b", "c", "d"]),
        json!(["a", "a", "b", "c"]),
        json!(["a", "b", "C"]),
    ] {
        let content =
            json!({"terminal": "Accepted", "selected": "a", "family_considered": considered});
        let (passed, report) = run(unique(), content);
        assert!(!passed);
        assert_eq!(report["code"], "DECLARED_FAMILY_KEPT");
        assert_eq!(failed(&report), ["declared_family_kept"]);
    }
    let content =
        json!({"terminal": "Accepted", "selected": "a", "family_considered": ["c", "a", "b", "a"]});
    let (_, report) = run(unique(), content);
    assert_eq!(
        evidence_of(&report, "declared_family_kept"),
        sha(r#"["a","a","b","c"]"#)
    );
    let any_order =
        json!({"terminal": "Accepted", "selected": "a", "family_considered": ["c", "a", "b"]});
    assert!(run(unique(), any_order).0);
}

#[test]
fn deleting_a_competitor_to_force_acceptance_fails_twice() {
    let content = json!({"terminal": "Accepted", "selected": "a", "family_considered": ["a", "b"]});
    let (passed, report) = run(under(), content);
    assert!(!passed);
    assert_eq!(report["code"], "DECLARED_FAMILY_KEPT");
    assert_eq!(
        failed(&report),
        ["declared_family_kept", "terminal_matches_survivor_set"]
    );
}

#[test]
fn a_selection_that_is_not_the_survivor_fails_alone() {
    for selected in [
        json!("c"),
        json!("b"),
        json!("A"),
        Value::Null,
        json!(["a"]),
        json!("~twin"),
    ] {
        let (passed, report) = run(unique(), reply("Accepted", selected));
        assert!(!passed);
        assert_eq!(report["code"], "SELECTION_IS_THE_SURVIVOR");
        assert_eq!(failed(&report), ["selection_is_the_survivor"]);
    }
    let content = json!({"terminal": "Accepted", "family_considered": ["a", "b", "c"]});
    let (passed, report) = run(unique(), content);
    assert!(!passed);
    assert_eq!(failed(&report), ["selection_is_the_survivor"]);
}

#[test]
fn a_candidate_is_a_polynomial_with_its_constant_term_first() {
    // At x = 3: a = 1 + 2*3 = 7, b = 1 + 9 = 10, c = 1 + 3 + 9 = 13.
    for (y, survivor) in [(7, "a"), (10, "b"), (13, "c")] {
        assert_eq!(
            survivors(family(), json!([{"x": 3, "y": y}])),
            (json!([survivor]), json!("Accepted"))
        );
    }
    assert_eq!(
        survivors(family(), json!([{"x": 3, "y": 5}])),
        (json!([]), json!("Refuted"))
    );
    // Rational coefficients and points: 1/2 + (2/3)(3/4) = 1.
    assert_eq!(
        survivors(
            json!({"p": ["1/2", "2/3"], "q": ["1/2", "2/3", 1]}),
            json!([{"x": "3/4", "y": 1}])
        ),
        (json!(["p"]), json!("Accepted"))
    );
    // The empty polynomial is zero everywhere.
    assert_eq!(
        survivors(json!({"zero": [], "one": [1]}), json!([{"x": 9, "y": 0}])),
        (json!(["zero"]), json!("Accepted"))
    );
}

#[test]
fn an_observation_keeps_a_candidate_up_to_its_tolerance_and_no_further() {
    let five = json!({"p": [5]});
    for (y, tol, kept) in [
        ("49/10", json!("1/10"), true),
        ("51/10", json!("1/10"), true),
        ("49/10", json!("99/1000"), false),
        ("51/10", json!("99/1000"), false),
        ("5", json!(0), true),
        ("5", Value::Null, true),
        ("4999/1000", Value::Null, false),
        ("4999/1000", json!(0), false),
    ] {
        let mut seen = json!({"x": 0, "y": y});
        if !tol.is_null() {
            seen["tol"] = tol.clone();
        }
        let expected = if kept {
            (json!(["p"]), json!("Accepted"))
        } else {
            (json!([]), json!("Refuted"))
        };
        assert_eq!(
            survivors(five.clone(), json!([seen])),
            expected,
            "{y} {tol}"
        );
    }
}

#[test]
fn every_observation_must_keep_a_survivor() {
    // a and c agree at 0 and 1 and part at 2; b leaves at 1.
    assert_eq!(
        survivors(family(), json!([{"x": 0, "y": 1}])),
        (json!(["a", "b", "c"]), json!("Underdetermined"))
    );
    assert_eq!(
        survivors(family(), json!([{"x": 0, "y": 1}, {"x": 1, "y": 3}])),
        (json!(["a", "c"]), json!("Underdetermined"))
    );
    assert_eq!(
        survivors(
            family(),
            json!([{"x": 2, "y": 7}, {"x": 0, "y": 1}, {"x": 1, "y": 3}])
        ),
        (json!(["c"]), json!("Accepted"))
    );
    assert_eq!(
        survivors(family(), json!([{"x": 2, "y": 7}, {"x": 2, "y": 5}])),
        (json!([]), json!("Refuted"))
    );
}

#[test]
fn the_twin_is_the_first_survivor_plus_the_polynomial_that_vanishes_at_the_observed_points() {
    for (family, evidence, record) in [
        // The survivor is longer than the vanishing polynomial X - 1.
        (
            json!({"p": [1, 0, 0, 0, 0, 1]}),
            json!([{"x": 1, "y": 2}]),
            r#"{"after":2,"before":1,"twin":["0/1","1/1","0/1","0/1","0/1","1/1"]}"#,
        ),
        // The survivor is shorter than (X + 2)(X - 1/2)(X - 1) = X^3 + X^2/2 - 5X/2 + 1.
        (
            json!({"p": [3]}),
            json!([{"x": 1, "y": 3}, {"x": -2, "y": 3}, {"x": "1/2", "y": 3}]),
            r#"{"after":2,"before":1,"twin":["4/1","-5/2","1/2","1/1"]}"#,
        ),
        // A point seen twice is one root, not two.
        (
            json!({"p": [1, 2]}),
            json!([{"x": "1/2", "y": 2}, {"x": "1/2", "y": 2}]),
            r#"{"after":2,"before":1,"twin":["1/2","3/1"]}"#,
        ),
        // The twin is built on the first survivor in name order: k, not m.
        (
            json!({"m": [0, 1], "k": [0, 1, 0]}),
            json!([{"x": 5, "y": 5}]),
            r#"{"after":3,"before":2,"twin":["-5/1","2/1","0/1"]}"#,
        ),
        // (X - 4)(X - 7) = X^2 - 11X + 28 on the zero polynomial.
        (
            json!({"zero": []}),
            json!([{"x": 4, "y": 0}, {"x": 7, "y": 0}]),
            r#"{"after":2,"before":1,"twin":["28/1","-11/1","1/1"]}"#,
        ),
    ] {
        let ids: Vec<String> = family
            .as_object()
            .expect("family")
            .keys()
            .cloned()
            .collect();
        let terminal = if ids.len() == 1 {
            "Accepted"
        } else {
            "Underdetermined"
        };
        let content = json!({"terminal": terminal, "selected": ids[0], "family_considered": ids});
        let (passed, report) = run(json!({"family": family, "evidence": evidence}), content);
        assert!(passed, "{report}");
        assert_eq!(
            evidence_of(&report, "plenitude_raises_survivor_count"),
            sha(record)
        );
    }
}

#[test]
fn the_reply_names_a_terminal_and_the_family_it_considered() {
    let terminal = "terminal must be one of Accepted, Underdetermined, Refuted, Refused";
    for value in [
        json!("accepted"),
        json!("Accept"),
        json!(""),
        json!(0),
        Value::Null,
        json!(["Accepted"]),
    ] {
        assert_eq!(
            malformed(json!({"terminal": value, "family_considered": ["a", "b", "c"]})),
            terminal
        );
    }
    assert_eq!(
        malformed(json!({"family_considered": ["a", "b", "c"]})),
        terminal
    );
    assert_eq!(malformed(json!({})), terminal);
    let considered = "family_considered must list candidate ids";
    for value in [
        json!("a,b,c"),
        json!({"a": true}),
        Value::Null,
        json!(["a", 2]),
        json!([["a"]]),
    ] {
        assert_eq!(
            malformed(json!({"terminal": "Accepted", "family_considered": value})),
            considered
        );
    }
    assert_eq!(
        malformed(json!({"terminal": "Accepted", "selected": "a"})),
        considered
    );
}

#[test]
fn the_family_is_an_object_of_exact_coefficient_lists() {
    let object = "family must be an object";
    for value in [json!([[1, 2]]), json!("a"), Value::Null] {
        assert_eq!(bad_task(json!({"family": value, "evidence": []})), object);
    }
    assert_eq!(bad_task(json!({"evidence": []})), object);
    let exact = "every candidate must be a list of exact rationals";
    for candidate in [
        json!([1.5]),
        json!([1, "x"]),
        json!("1"),
        json!(1),
        json!([1, null]),
        json!({"0": 1}),
    ] {
        assert_eq!(
            bad_task(json!({"family": {"a": [1], "b": candidate}, "evidence": []})),
            exact
        );
    }
    assert_eq!(
        bad_task(json!({"family": {"a": [1], "~twin": [1]}, "evidence": []})),
        "the candidate name ~twin is kept for the host"
    );
    accepted(json!({"family": {"a": [1], "twin": ["-3/7"], "~twi": []}, "evidence": []}));
}

#[test]
fn the_evidence_is_a_list_of_exact_observations() {
    let list = "evidence must be a list";
    for value in [json!({"x": 0, "y": 1}), json!("none"), Value::Null] {
        assert_eq!(bad_task(json!({"family": {}, "evidence": value})), list);
    }
    assert_eq!(bad_task(json!({"family": {}})), list);
    let exact = "every observation needs exact rational x and y, and tol zero or more";
    for seen in [
        json!({"y": 1}),
        json!({"x": 0}),
        json!({"x": 0.5, "y": 1}),
        json!({"x": 0, "y": 1.0}),
        json!({"x": 0, "y": "one"}),
        json!({"x": 0, "y": 1, "tol": "-1/10"}),
        json!({"x": 0, "y": 1, "tol": -1}),
        json!({"x": 0, "y": 1, "tol": 0.1}),
        json!({"x": 0, "y": 1, "tol": null}),
        json!([0, 1]),
        json!("0,1"),
    ] {
        assert_eq!(
            bad_task(json!({"family": {}, "evidence": [{"x": 0, "y": 1}, seen]})),
            exact
        );
    }
    accepted(
        json!({"family": {}, "evidence": [{"x": "-1/2", "y": "7/3", "tol": 0}, {"x": 0, "y": 0, "tol": "1/1000"}]}),
    );
}
