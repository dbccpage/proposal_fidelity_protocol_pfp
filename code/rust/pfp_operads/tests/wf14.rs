//! WF14, immune failure classification: the seal on the self panel, the thymus, the two-signal
//! admission of each rule, and the antibody custody and ledger entries the verdict carries.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf14-tests:v1

use pfp_operads::datum::Datum;
use pfp_operads::families::wf14::FAMILY;
use pfp_operads::families::{judge, next};
use pfp_operads::host::Outcome;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn sha(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

fn canonical(value: &Value) -> String {
    Datum::parse(&value.to_string())
        .expect("a datum")
        .canonical()
}

/// A reply text the way Python writes one: `{"coefficients": [1, -3, 2]}`.
fn coefficients(parts: &[&str]) -> String {
    format!("{{\"coefficients\": [{}]}}", parts.join(", "))
}

fn panel() -> Value {
    json!([
        {"roots": [1, 2], "text": coefficients(&["1", "-3", "2"])},
        {"roots": [2, -2], "text": coefficients(&["1", "0", "-4"])},
        {"roots": ["1/2"], "text": coefficients(&["1", "\"-1/2\""])},
        {"roots": [3, 1, 0], "text": coefficients(&["1", "-4", "3", "0"])},
    ])
}

fn provenance(k: usize) -> Value {
    json!({"model": format!("m{k}"), "scaffold": format!("s{k}"), "precedent": format!("p{k}"), "lineage": format!("l{k}")})
}

/// Seven failures: three noncanonical, one nonmonic, one malformed, one sign flip, one clean.
fn failures() -> Value {
    json!([
        {"id": "f1", "roots": [2, 3], "text": coefficients(&["1", "\"-5/1\"", "6"]), "provenance": provenance(1)},
        {"id": "f2", "roots": [1, 4], "text": coefficients(&["1", "\"-5/1\"", "4"]), "provenance": provenance(2)},
        {"id": "f3", "roots": [0, 5], "text": coefficients(&["1", "\"-5/1\"", "0"]), "provenance": provenance(3)},
        {"id": "f4", "roots": [1, 3], "text": coefficients(&["2", "-8", "6"]), "provenance": provenance(4)},
        {"id": "f5", "roots": [1, 2], "text": "{'coefficients': [1, -3, 2]}", "provenance": provenance(5)},
        {"id": "f6", "roots": [1, 5], "text": coefficients(&["1", "6", "5"]), "provenance": provenance(6)},
        {"id": "f7", "roots": [2, 4], "text": coefficients(&["1", "-6", "8"]), "provenance": {"model": "self-report"}},
    ])
}

fn task_of(failures: &Value) -> Value {
    json!({
        "statement": "Propose detector rules for the observed failures.",
        "failures": failures,
        "self_panel_sha256": sha(&canonical(&panel())),
    })
}

fn task() -> Value {
    task_of(&failures())
}

fn sealed() -> Value {
    json!({"self_panel": panel()})
}

fn rule(id: &str, epitope: &str, pattern: &str) -> Value {
    json!({"rule_id": id, "target_epitope": epitope, "pattern": pattern})
}

fn good() -> Value {
    json!([
        rule("denominator_one", "RATIONAL_NONCANONICAL", "/1\""),
        rule("leading_two", "NONMONIC_LEADING_COEFFICIENT", "\\[2,"),
        rule("single_quotes", "MALFORMED_JSON", "\\{'"),
    ])
}

fn request(task: &Value, sealed: &Value, replies: &[Option<Value>]) -> String {
    let replies: Vec<Value> = replies
        .iter()
        .map(|reply| {
            reply
                .as_ref()
                .map_or(Value::Null, |content| json!({ "content": content }))
        })
        .collect();
    json!({"workflow": "WF14", "task": task, "sealed": sealed, "replies": replies}).to_string()
}

fn run_with(task: &Value, sealed: &Value, reply: Value) -> (bool, Value) {
    match judge(&request(task, sealed, &[Some(reply)])) {
        Outcome::Pass { result } => (true, result),
        Outcome::Fail { result } => (false, result),
        Outcome::Refused { refusal } => panic!("refused: {refusal}"),
    }
}

fn run(rules: &Value) -> (bool, Value) {
    run_with(&task(), &sealed(), json!({ "rules": rules }))
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

fn statuses(report: &Value) -> Value {
    report["detail"]["rules"].clone()
}

fn bad_task(task: &Value) -> String {
    match judge(&request(task, &sealed(), &[])) {
        Outcome::Refused { refusal } => {
            assert_eq!(refusal.code, "BAD_TASK");
            refusal.message
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

fn malformed(task: &Value, sealed: &Value, reply: Value) -> String {
    let (passed, report) = run_with(task, sealed, reply);
    assert!(!passed);
    assert_eq!(report["code"], "MALFORMED_CANDIDATE");
    report["detail"]["reason"]
        .as_str()
        .expect("a reason")
        .to_owned()
}

fn bad_rules(rules: &Value) -> String {
    malformed(&task(), &sealed(), json!({ "rules": rules }))
}

#[test]
fn the_registry_names_the_family() {
    assert_eq!(FAMILY.workflow, "WF14");
    assert_eq!(FAMILY.name, "Immune failure classification");
    assert_eq!(FAMILY.host_check, "thymus_two_signal_admission");
}

#[test]
fn rules_that_two_independent_signals_hold_are_admitted() {
    let (passed, report) = run(&good());
    assert!(passed);
    assert_eq!(report["verdict"], "HOST_CERTIFIED");
    assert_eq!(report["code"], "RULES_ADMITTED");
    assert_eq!(
        report["detail"],
        json!({
            "rules": {"denominator_one": "ADMITTED", "leading_two": "ADMITTED", "single_quotes": "ADMITTED"},
            "epitopes": {
                "CLEAN": 1, "MALFORMED_JSON": 1, "NONMONIC_LEADING_COEFFICIENT": 1,
                "RATIONAL_NONCANONICAL": 3, "SIGN_MISMATCH": 1,
            },
            "antibodies": {
                "MALFORMED_JSON": "Candidate", "NONMONIC_LEADING_COEFFICIENT": "Candidate",
                "RATIONAL_NONCANONICAL": "Provisional", "SIGN_MISMATCH": "Candidate",
            },
        })
    );
    assert_eq!(
        outcomes(&report),
        [
            ("self_panel_sealed", true),
            ("self_panel_clean", true),
            ("no_autoimmune_rule", true),
            ("every_rule_two_signal_admitted", true),
        ]
    );
}

#[test]
fn each_predicate_is_recorded_over_what_it_looked_at() {
    let (_, report) = run(&good());
    let digests: Vec<&str> = report["predicates"]
        .as_array()
        .expect("predicates")
        .iter()
        .map(|row| row["evidence_sha256"].as_str().expect("a digest"))
        .collect();
    let admitted = "{\"denominator_one\":\"ADMITTED\",\"leading_two\":\"ADMITTED\",\"single_quotes\":\"ADMITTED\"}";
    assert_eq!(
        digests,
        [
            sha(&format!("\"{}\"", sha(&canonical(&panel())))),
            sha("4"),
            sha(admitted),
            sha(admitted)
        ]
    );
}

#[test]
fn one_step_is_asked_and_it_leaves_the_sealed_panel_out() {
    let turn = match next(&request(&task(), &sealed(), &[])) {
        Outcome::Pass { result } => result,
        other => panic!("expected a turn, got {other:?}"),
    };
    assert_eq!(turn["workflow"], "WF14");
    assert_eq!(turn["ask"]["stage"], "rules");
    assert_eq!(turn["asked"], json!([]));
    let prompt = turn["ask"]["prompt"].as_str().expect("a prompt");
    assert!(prompt.starts_with(
        "WF14 Immune failure classification. Propose detector rules for the observed failures.\n"
    ));
    assert!(prompt.contains("self_panel_sha256"));
    assert!(prompt.contains("self-report"));
    assert_eq!(turn["ask"]["prompt_sha256"], sha(prompt));
    let done = match next(&request(
        &task(),
        &sealed(),
        &[Some(json!({"rules": good()}))],
    )) {
        Outcome::Pass { result } => result,
        other => panic!("expected a turn, got {other:?}"),
    };
    assert_eq!(done["ask"], Value::Null);
    assert_eq!(done["asked"][0]["stage"], "rules");
}

#[test]
fn a_prompt_with_a_sealed_panel_text_is_never_handed_out() {
    let mut panel = panel();
    panel[0]["text"] = json!("leaky panel text");
    let mut failures = failures();
    failures[0]["text"] = json!("a failure that quotes: leaky panel text");
    let task = task_of(&failures);
    let sealed = json!({ "self_panel": panel });
    match judge(&request(&task, &sealed, &[Some(json!({"rules": good()}))])) {
        Outcome::Refused { refusal } => assert_eq!(refusal.code, "SEALED_LEAK"),
        other => panic!("expected a refusal, got {other:?}"),
    }
}

#[test]
fn a_rule_that_matches_a_clean_panel_text_is_killed_and_the_run_is_refused() {
    let mut rules = good();
    rules
        .as_array_mut()
        .expect("rules")
        .push(rule("any_reply", "MALFORMED_JSON", "coefficients"));
    let (passed, report) = run(&rules);
    assert!(!passed);
    assert_eq!(report["verdict"], "REFUSED");
    assert_eq!(report["code"], "NO_AUTOIMMUNE_RULE");
    assert_eq!(
        statuses(&report),
        json!({
            "any_reply": "KILLED_BY_THYMUS", "denominator_one": "ADMITTED",
            "leading_two": "ADMITTED", "single_quotes": "ADMITTED",
        })
    );
    assert_eq!(
        report["detail"]["failed"],
        json!(["no_autoimmune_rule", "every_rule_two_signal_admitted"])
    );
    assert_eq!(report["every_predicate_passed"], false);
}

#[test]
fn a_pattern_outside_the_bounded_subset_is_killed_before_it_can_match() {
    for pattern in ["a+", "(ab|cd){1,3}", "\\1", "[", "a?", "(a)(b)\\2"] {
        let (_, report) = run(&json!([rule("r", "WRONG_VALUE", pattern)]));
        assert_eq!(
            statuses(&report),
            json!({"r": "KILLED_BY_THYMUS"}),
            "{pattern}"
        );
    }
}

#[test]
fn a_match_on_a_failure_that_is_clean_is_only_diagnostic() {
    let (_, report) = run(&json!([rule("minus_six", "WRONG_VALUE", "-6, 8")]));
    assert_eq!(report["code"], "EVERY_RULE_TWO_SIGNAL_ADMITTED");
    assert_eq!(statuses(&report), json!({"minus_six": "DIAGNOSTIC_ONLY"}));
}

#[test]
fn a_danger_whose_evidence_is_what_the_rule_matched_is_one_signal_not_two() {
    let echo = r#"[["WRONG_VALUE","WRONG_VALUE",3]]"#;
    let failures = json!([{"id": "echo", "roots": [1], "text": echo}]);
    let rules = json!([rule("echo", "WRONG_VALUE", "WRONG_VALUE")]);
    let (passed, report) = run_with(&task_of(&failures), &sealed(), json!({"rules": rules}));
    assert!(!passed);
    assert_eq!(report["code"], "EVERY_RULE_TWO_SIGNAL_ADMITTED");
    assert_eq!(statuses(&report), json!({"echo": "TWO_SIGNAL_COLLAPSE"}));
    let other = json!([{"id": "echo", "roots": [1], "text": format!("{echo} ")}]);
    let (passed, report) = run_with(&task_of(&other), &sealed(), json!({"rules": rules}));
    assert_eq!(statuses(&report), json!({"echo": "EPITOPE_MISMATCH"}));
    assert!(!passed);
}

#[test]
fn a_rule_that_names_the_wrong_epitope_is_a_mismatch() {
    let (_, report) = run(&json!([rule("denominator_one", "SIGN_MISMATCH", "/1\"")]));
    assert_eq!(
        statuses(&report),
        json!({"denominator_one": "EPITOPE_MISMATCH"})
    );
}

#[test]
fn a_rule_that_matches_no_failure_is_unmatched() {
    let (passed, report) = run(&json!([rule("nothing", "WRONG_VALUE", "not anywhere")]));
    assert!(!passed);
    assert_eq!(statuses(&report), json!({"nothing": "UNMATCHED"}));
}

#[test]
fn the_first_failure_a_rule_matches_that_does_not_hold_ends_its_check() {
    let mut failures = failures();
    failures.as_array_mut().expect("failures").insert(
        0,
        json!({"id": "g0", "roots": [9], "text": coefficients(&["1", "-9"])}),
    );
    let rules = json!([rule("both", "RATIONAL_NONCANONICAL", "(-9|-5/1)")]);
    let (passed, report) = run_with(&task_of(&failures), &sealed(), json!({"rules": rules}));
    assert!(!passed);
    assert_eq!(statuses(&report), json!({"both": "DIAGNOSTIC_ONLY"}));
    let (passed, report) = run(&rules);
    assert!(passed);
    assert_eq!(statuses(&report), json!({"both": "ADMITTED"}));
}

#[test]
fn a_forged_seal_ends_the_run_before_anything_is_admitted() {
    let mut forged = task();
    forged["self_panel_sha256"] = json!(sha("something else"));
    let (passed, report) = run_with(&forged, &sealed(), json!({"rules": good()}));
    assert!(!passed);
    assert_eq!(report["code"], "SELF_PANEL_SEAL_BROKEN");
    assert_eq!(report["detail"], json!({}));
    assert_eq!(outcomes(&report), [("self_panel_sealed", false)]);
}

#[test]
fn a_self_panel_with_a_text_that_is_not_clean_fails_its_predicate_but_the_run_goes_on() {
    let mut dirty = panel();
    dirty[1]["text"] = json!(coefficients(&["1", "0", "4"]));
    let mut task = task();
    task["self_panel_sha256"] = json!(sha(&canonical(&dirty)));
    let (passed, report) = run_with(
        &task,
        &json!({"self_panel": dirty}),
        json!({"rules": good()}),
    );
    assert!(!passed);
    assert_eq!(report["code"], "SELF_PANEL_CLEAN");
    assert_eq!(
        outcomes(&report),
        [
            ("self_panel_sealed", true),
            ("self_panel_clean", false),
            ("no_autoimmune_rule", true),
            ("every_rule_two_signal_admitted", true),
        ]
    );
    assert_eq!(report["detail"]["failed"], json!(["self_panel_clean"]));
}

#[test]
fn a_missing_reply_is_refused_as_such() {
    match judge(&request(&task(), &sealed(), &[None])) {
        Outcome::Fail { result } => {
            assert_eq!(result["code"], "NO_ADMISSIBLE_REPLY");
            assert_eq!(result["predicates"], json!([]));
        }
        other => panic!("expected a refusal, got {other:?}"),
    }
}

#[test]
fn a_reply_that_is_not_an_object_or_has_no_rules_is_malformed() {
    assert_eq!(
        malformed(&task(), &sealed(), json!([1])),
        "rules reply must be an object"
    );
    assert_eq!(
        malformed(&task(), &sealed(), json!({})),
        "rules must be a nonempty list"
    );
    for rules in [json!([]), json!("x"), json!({"a": 1}), Value::Null] {
        assert_eq!(bad_rules(&rules), "rules must be a nonempty list");
    }
}

#[test]
fn a_rule_needs_a_known_epitope_an_id_and_a_pattern() {
    let epitope = "rule needs a known target_epitope";
    assert_eq!(bad_rules(&json!([5])), epitope);
    assert_eq!(
        bad_rules(&json!([{"rule_id": "r", "pattern": "x"}])),
        epitope
    );
    assert_eq!(bad_rules(&json!([rule("r", "NOPE", "x")])), epitope);
    assert_eq!(
        bad_rules(&json!([{"rule_id": "r", "target_epitope": 5, "pattern": "x"}])),
        epitope
    );
    let id = "bad rule: rule_id must be a nonempty string";
    for bad in [
        json!(""),
        json!("  \t"),
        json!(true),
        json!(1.5),
        json!(null),
        json!(["a"]),
    ] {
        let spec = json!({"rule_id": bad, "target_epitope": "WRONG_VALUE", "pattern": "x"});
        assert_eq!(bad_rules(&json!([spec])), id);
    }
    assert_eq!(
        bad_rules(&json!([{"target_epitope": "WRONG_VALUE", "pattern": "x"}])),
        id
    );
    let pattern = "bad rule: match_pattern must be a nonempty string";
    for bad in [
        json!(""),
        json!(" \u{a0}"),
        json!(7),
        json!(null),
        json!(["a"]),
    ] {
        let spec = json!({"rule_id": "r", "target_epitope": "WRONG_VALUE", "pattern": bad});
        assert_eq!(bad_rules(&json!([spec])), pattern);
    }
    assert_eq!(
        bad_rules(&json!([{"rule_id": "r", "target_epitope": "WRONG_VALUE"}])),
        pattern
    );
    assert_eq!(
        bad_rules(&json!([
            rule("r", "NOPE", "x"),
            rule("", "WRONG_VALUE", "")
        ])),
        epitope
    );
    assert_eq!(
        bad_rules(&json!([
            rule("", "WRONG_VALUE", ""),
            rule("r", "NOPE", "x")
        ])),
        id
    );
}

#[test]
fn rule_ids_are_unique_and_an_integer_id_stands_for_its_digits() {
    let unique = "rule ids must be unique";
    assert_eq!(
        bad_rules(&json!([
            rule("a", "WRONG_VALUE", "x"),
            rule("a", "WRONG_VALUE", "y")
        ])),
        unique
    );
    let apart = json!([
        rule("a", "WRONG_VALUE", "x"),
        rule("b", "WRONG_VALUE", "y"),
        rule("a", "WRONG_VALUE", "z")
    ]);
    assert_eq!(bad_rules(&apart), unique);
    let numbered = json!([{"rule_id": 5, "target_epitope": "WRONG_VALUE", "pattern": "x"}, rule("5", "WRONG_VALUE", "y")]);
    assert_eq!(bad_rules(&numbered), unique);
    let (_, report) =
        run(&json!([{"rule_id": 5, "target_epitope": "WRONG_VALUE", "pattern": "nothing here"}]));
    assert_eq!(statuses(&report), json!({"5": "UNMATCHED"}));
}

#[test]
fn a_pattern_the_host_does_not_read_stops_the_run_and_names_the_rule() {
    let reason = bad_rules(&json!([
        rule("fine", "WRONG_VALUE", "x"),
        rule("anchored", "WRONG_VALUE", "^x")
    ]));
    assert_eq!(
        reason,
        "rule anchored: the pattern uses an anchor, which the host does not read"
    );
}

#[test]
fn the_statuses_are_listed_in_the_order_of_the_rule_ids() {
    let rules = json!([
        rule("b", "WRONG_VALUE", "nothing"),
        rule("a", "MALFORMED_JSON", "coefficients"),
        rule("c", "RATIONAL_NONCANONICAL", "/1\""),
    ]);
    let (_, report) = run(&rules);
    let keys: Vec<&String> = report["detail"]["rules"]
        .as_object()
        .expect("a map")
        .keys()
        .collect();
    assert_eq!(keys, ["a", "b", "c"]);
    assert_eq!(
        statuses(&report),
        json!({"a": "KILLED_BY_THYMUS", "b": "UNMATCHED", "c": "ADMITTED"})
    );
}

#[test]
fn a_task_names_its_failures_and_its_seal() {
    let mut task = task();
    task["failures"] = json!([]);
    assert_eq!(bad_task(&task), "failures must be a nonempty list");
    task["failures"] = json!("x");
    assert_eq!(bad_task(&task), "failures must be a nonempty list");
    task.as_object_mut().expect("task").remove("failures");
    assert_eq!(bad_task(&task), "failures must be a nonempty list");
    let mut task = self::task();
    task.as_object_mut()
        .expect("task")
        .remove("self_panel_sha256");
    assert_eq!(bad_task(&task), "self panel seal required");
    task["self_panel_sha256"] = json!(5);
    assert_eq!(bad_task(&task), "self panel seal required");
}

#[test]
fn a_failure_needs_its_text_and_exact_roots_and_may_name_an_id_and_its_provenance() {
    let broken = |entry: Value| bad_task(&task_of(&json!([entry])));
    assert_eq!(broken(json!({"roots": [1]})), "each entry needs its text");
    assert_eq!(
        broken(json!({"roots": [1], "text": 5})),
        "each entry needs its text"
    );
    let roots = "roots must be a list of exact rationals";
    assert_eq!(broken(json!({"text": "x"})), roots);
    assert_eq!(broken(json!({"roots": "1", "text": "x"})), roots);
    assert_eq!(broken(json!({"roots": [0.5], "text": "x"})), roots);
    assert_eq!(broken(json!({"roots": ["1/0"], "text": "x"})), roots);
    assert_eq!(broken(json!({"roots": ["1.5"], "text": "x"})), roots);
    assert_eq!(
        broken(json!({"roots": [1], "text": "x", "id": 5})),
        "a failure id must be text"
    );
    assert_eq!(
        broken(json!({"roots": [1], "text": "x", "provenance": []})),
        "provenance must be an object"
    );
    for name in ["model", "scaffold", "precedent", "lineage"] {
        assert_eq!(
            broken(json!({"roots": [1], "text": "x", "provenance": {name: 5}})),
            format!("provenance {name} must be text")
        );
    }
    assert_eq!(bad_task(&task_of(&json!([1]))), "each entry needs its text");
}

#[test]
fn roots_may_be_empty_and_may_be_fractions() {
    let failures = json!([
        {"roots": [], "text": coefficients(&["1"])},
        {"roots": ["1/2", "-3/4", 2], "text": coefficients(&["1", "\"-7/4\"", "\"-1/8\"", "\"3/4\""])},
    ]);
    let (_, report) = run_with(
        &task_of(&failures),
        &sealed(),
        json!({"rules": [rule("r", "WRONG_VALUE", "nothing")]}),
    );
    assert_eq!(
        report["detail"]["epitopes"],
        json!({"CLEAN": 1, "WRONG_VALUE": 1})
    );
}

#[test]
fn the_sealed_panel_is_a_nonempty_list_of_texts_with_roots_and_is_read_before_anything_is_asked() {
    let reason = |sealed: Value| {
        let (passed, report) = match judge(&request(&task(), &sealed, &[])) {
            Outcome::Fail { result } => (false, result),
            other => panic!("expected a refusal, got {other:?}"),
        };
        assert!(!passed);
        assert_eq!(report["code"], "MALFORMED_CANDIDATE");
        report["detail"]["reason"]
            .as_str()
            .expect("a reason")
            .to_owned()
    };
    assert_eq!(reason(json!({})), "self_panel must be a nonempty list");
    assert_eq!(
        reason(json!({"self_panel": []})),
        "self_panel must be a nonempty list"
    );
    assert_eq!(
        reason(json!({"self_panel": "x"})),
        "self_panel must be a nonempty list"
    );
    assert_eq!(
        reason(json!({"self_panel": [{"roots": [1]}]})),
        "each entry needs its text"
    );
    assert_eq!(
        reason(json!({"self_panel": [{"text": "x", "roots": ["a"]}]})),
        "roots must be a list of exact rationals"
    );
    match next(&request(&task(), &json!({}), &[])) {
        Outcome::Pass { result } => assert_eq!(result["ask"], Value::Null),
        other => panic!("expected a turn, got {other:?}"),
    }
}

#[test]
fn each_failure_is_sorted_into_its_epitope_by_the_monic_classifier() {
    let failures = json!([
        {"roots": [2], "text": "not json"},
        {"roots": [2], "text": coefficients(&["1", "-2"])},
        {"roots": [2], "text": coefficients(&["1", "2"])},
        {"roots": [2], "text": coefficients(&["2", "-4"])},
        {"roots": [2], "text": coefficients(&["1", "\"-2\""])},
        {"roots": [2], "text": coefficients(&["1", "-3"])},
        {"roots": [2], "text": coefficients(&["1", "\"1_0\""])},
    ]);
    let (_, report) = run_with(
        &task_of(&failures),
        &sealed(),
        json!({"rules": [rule("r", "WRONG_VALUE", "nothing")]}),
    );
    assert_eq!(
        report["detail"]["epitopes"],
        json!({
            "CLEAN": 1, "MALFORMED_JSON": 1, "NONMONIC_LEADING_COEFFICIENT": 1,
            "RATIONAL_NONCANONICAL": 2, "SIGN_MISMATCH": 1, "WRONG_VALUE": 1,
        })
    );
    assert_eq!(
        report["detail"]["antibodies"]
            .as_object()
            .expect("a map")
            .len(),
        5
    );
}

fn noncanonical(count: usize, shared: impl Fn(usize) -> Value) -> Value {
    Value::Array(
        (0..count)
            .map(|place| {
                json!({"id": format!("n{place}"), "roots": [1], "text": coefficients(&["1", "\"-1/1\""]), "provenance": shared(place)})
            })
            .collect(),
    )
}

fn custody(failures: &Value) -> Value {
    let (_, report) = run_with(
        &task_of(failures),
        &sealed(),
        json!({"rules": [rule("r", "WRONG_VALUE", "nothing")]}),
    );
    report["detail"]["antibodies"].clone()
}

#[test]
fn three_failures_that_share_no_provenance_make_an_epitope_provisional() {
    let independent = noncanonical(3, provenance);
    assert_eq!(
        custody(&independent),
        json!({"RATIONAL_NONCANONICAL": "Provisional"})
    );
    let two = noncanonical(2, provenance);
    assert_eq!(custody(&two), json!({"RATIONAL_NONCANONICAL": "Candidate"}));
    let same_model = noncanonical(3, |place| {
        let mut one = provenance(place);
        one["model"] = json!("m");
        one
    });
    assert_eq!(
        custody(&same_model),
        json!({"RATIONAL_NONCANONICAL": "Candidate"})
    );
    for key in ["scaffold", "precedent", "lineage"] {
        let shared = noncanonical(3, |place| {
            let mut one = provenance(place);
            one[key] = json!("same");
            one
        });
        assert_eq!(
            custody(&shared),
            json!({"RATIONAL_NONCANONICAL": "Candidate"}),
            "{key}"
        );
    }
}

#[test]
fn a_failure_without_provenance_or_an_id_still_counts_once_under_its_position() {
    let bare = Value::Array(
        (0..3)
            .map(|place| json!({"roots": [1], "text": coefficients(&["1", "\"-1/1\""]), "provenance": {"model": format!("m{place}")}}))
            .collect(),
    );
    assert_eq!(
        custody(&bare),
        json!({"RATIONAL_NONCANONICAL": "Provisional"})
    );
    let blank = Value::Array(
        (0..3)
            .map(|_| json!({"roots": [1], "text": coefficients(&["1", "\"-1/1\""])}))
            .collect(),
    );
    assert_eq!(
        custody(&blank),
        json!({"RATIONAL_NONCANONICAL": "Candidate"})
    );
    let text = coefficients(&["1", "\"-1/1\""]);
    let collides = json!([
        {"id": "1", "roots": [1], "text": text, "provenance": provenance(0)},
        {"roots": [1], "text": text, "provenance": provenance(1)},
        {"id": "x", "roots": [1], "text": text, "provenance": provenance(2)},
    ]);
    assert_eq!(
        custody(&collides),
        json!({"RATIONAL_NONCANONICAL": "Candidate"})
    );
    let repeated = Value::Array(
        (0..3)
            .map(|place| json!({"id": "same", "roots": [1], "text": coefficients(&["1", "\"-1/1\""]), "provenance": provenance(place)}))
            .collect(),
    );
    assert_eq!(
        custody(&repeated),
        json!({"RATIONAL_NONCANONICAL": "Candidate"})
    );
}

#[test]
fn a_clean_failure_is_not_an_observation() {
    let clean = Value::Array(
        (0..4)
            .map(|place| json!({"id": format!("c{place}"), "roots": [1], "text": coefficients(&["1", "-1"]), "provenance": provenance(place)}))
            .collect(),
    );
    assert_eq!(custody(&clean), json!({}));
}

fn ledger_task(path: Value) -> Value {
    let mut task = task();
    task["ledger_path"] = path;
    task
}

#[test]
fn rules_that_were_not_admitted_come_with_the_ledger_entries_to_write() {
    let rules = json!([
        rule("a_killed", "MALFORMED_JSON", "coefficients"),
        rule("b_unmatched", "WRONG_VALUE", "nothing"),
        rule("c_admitted", "RATIONAL_NONCANONICAL", "/1\""),
        rule("d_mismatch", "SIGN_MISMATCH", "/1\""),
        rule("e_clean", "WRONG_VALUE", "-6, 8"),
    ]);
    let (_, report) = run_with(
        &ledger_task(json!("/tmp/ledger.jsonl")),
        &sealed(),
        json!({ "rules": rules }),
    );
    let entry = |id: &str, class: &str, evidence: &str| {
        json!({
            "failure_id": id, "failure_class": class, "ddc_trace": "CRM",
            "evidence_sha256": sha(evidence),
        })
    };
    assert_eq!(
        report["detail"]["ledger_failures"],
        json!([
            entry(
                "thymus_kill:a_killed",
                "BoundaryLeakage",
                "KILLED_BY_THYMUS:a_killed"
            ),
            entry(
                "rule_rejected:b_unmatched",
                "StructuralNonFit",
                "UNMATCHED:b_unmatched"
            ),
            entry(
                "rule_rejected:d_mismatch",
                "StructuralNonFit",
                "EPITOPE_MISMATCH:d_mismatch"
            ),
            entry(
                "rule_rejected:e_clean",
                "StructuralNonFit",
                "DIAGNOSTIC_ONLY:e_clean"
            ),
        ])
    );
}

#[test]
fn a_ledger_is_named_only_by_a_nonempty_text_and_admitted_rules_leave_no_entry() {
    let kill = json!({"rules": [rule("k", "WRONG_VALUE", "coefficients")]});
    for path in [json!(null), json!(""), json!(5), json!(["a"])] {
        let (_, report) = run_with(&ledger_task(path), &sealed(), kill.clone());
        assert!(report["detail"].get("ledger_failures").is_none());
    }
    let (_, report) = run_with(&task(), &sealed(), kill);
    assert!(report["detail"].get("ledger_failures").is_none());
    let (passed, report) = run_with(
        &ledger_task(json!("/tmp/ledger.jsonl")),
        &sealed(),
        json!({"rules": good()}),
    );
    assert!(passed);
    assert_eq!(report["detail"]["ledger_failures"], json!([]));
}

#[test]
fn a_run_ends_with_the_one_reply_it_asked_for() {
    let replies = [
        Some(json!({"rules": good()})),
        Some(json!({"rules": good()})),
    ];
    match judge(&request(&task(), &sealed(), &replies)) {
        Outcome::Refused { refusal } => assert_eq!(refusal.code, "BAD_REQUEST"),
        other => panic!("expected a refusal, got {other:?}"),
    }
}

#[test]
fn an_alternation_python_reads_as_a_set_matches_like_the_set_and_a_group_is_a_group() {
    let rules = json!([
        rule("denominators", "RATIONAL_NONCANONICAL", "-5/(1|1)\""),
        rule("leading", "NONMONIC_LEADING_COEFFICIENT", "\\[(2|3),"),
    ]);
    let (passed, report) = run(&rules);
    assert!(passed);
    assert_eq!(
        statuses(&report),
        json!({"denominators": "ADMITTED", "leading": "ADMITTED"})
    );
}
