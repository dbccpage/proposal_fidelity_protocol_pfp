//! The immune domain the families share: thymic screening, the two-signal disposition and the
//! support an antibody needs.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-immune-tests:v1
//!
//! The digests in the tests were computed by Python's `signal1_digest` over the same matches.

use std::collections::BTreeSet;

use pfp_operads::families::immune::{
    custody, decide, screen, signal1, signal1_digest, support, Danger, Decision, Disposition, Fate,
    Match, Observation, Rule, DANGER_KINDS, FORBIDDEN_OBSERVERS, HOST_OBSERVERS, MATCHER,
    SUPPORT_BUDGET, SUPPORT_NEEDED,
};
use pfp_operads::families::pattern::compile;

fn rule(id: &str, pattern: &str) -> Rule {
    Rule {
        id: id.to_owned(),
        epitope: "WRONG_VALUE".to_owned(),
        pattern: pattern.to_owned(),
    }
}

fn found(epitope: &str, text: &str, offset: usize) -> Match {
    Match {
        detector: "d".to_owned(),
        epitope: epitope.to_owned(),
        text: text.to_owned(),
        offset,
    }
}

fn fates(rules: &[Rule], panel: &[&str]) -> Vec<bool> {
    screen(rules, panel)
        .expect("readable patterns")
        .iter()
        .map(|fate| matches!(fate, Fate::Admitted(_)))
        .collect()
}

#[test]
fn the_thymus_kills_a_rule_that_matches_the_panel_and_a_pattern_it_refuses() {
    let rules = [
        rule("quiet", "zzz"),
        rule("self_reactive", "coefficients"),
        rule("unbounded", "a+"),
        rule("on_the_second_text", "clean"),
    ];
    let panel = ["{\"coefficients\": [1, -3, 2]}", "clean"];
    assert_eq!(fates(&rules, &panel), [true, false, false, false]);
}

#[test]
fn the_thymus_matches_without_regard_to_case_on_any_panel_text() {
    let panel = ["no", "the second text is CLEAN"];
    assert_eq!(fates(&[rule("r", "clean")], &panel), [false]);
    assert_eq!(fates(&[rule("r", "clean")], &["no", "never"]), [true]);
    assert_eq!(fates(&[rule("r", "clean")], &[]), [true]);
}

#[test]
fn the_thymus_returns_one_fate_per_rule_in_order() {
    let rules = [rule("a", "x"), rule("b", "y+"), rule("c", "z")];
    assert_eq!(fates(&rules, &["y"]), [true, false, true]);
    assert!(screen(&[], &["x"]).expect("nothing to read").is_empty());
}

#[test]
fn a_pattern_the_host_does_not_read_is_named_with_its_rule() {
    let rules = [rule("fine", "x"), rule("anchored", "^x")];
    let error = screen(&rules, &["y"]).expect_err("an anchor is not read");
    assert!(error.contains("rule anchored"), "{error}");
    assert!(error.contains("anchor"), "{error}");
    assert!(error.contains("does not read"), "{error}");
}

#[test]
fn a_rule_matches_with_its_own_id_and_epitope_where_it_first_hits() {
    let one = rule("r1", "-6, ?8");
    let compiled = compile(&one.pattern).expect("a safe pattern");
    let hit = signal1("é [1, -6, 8]", &one, &compiled).expect("a match");
    assert_eq!(
        hit,
        Match {
            detector: "r1".to_owned(),
            epitope: "WRONG_VALUE".to_owned(),
            text: "-6, 8".to_owned(),
            offset: 6,
        }
    );
    assert_eq!(signal1("[1, 6, 8]", &one, &compiled), None);
}

#[test]
fn a_danger_carries_the_digest_of_what_the_observer_saw() {
    let seen = Danger::observed(
        "MALFORMED_PAYLOAD",
        "host.contract_check",
        "{\"coefficients\": [1, -3]}",
    );
    assert_eq!(seen.kind, "MALFORMED_PAYLOAD");
    assert_eq!(seen.observer, "host.contract_check");
    assert_eq!(
        seen.digest,
        "sha256:bb6a758ccb5e98efd39916f448209e5d337c3c0a77e685c9e1d2d9e5a71b2b67"
    );
    assert!(seen.spans.is_empty());
}

#[test]
fn the_digest_of_matches_is_python_s_and_ignores_order() {
    assert_eq!(
        signal1_digest(&[found("WRONG_VALUE", "-6, 8", 3)]),
        "sha256:e170dc8612cd5d484b5ad313ee538ffdd7413bbc0378cb82a5efecd11e037b4c"
    );
    let sorted = [
        found("B", "x", 1),
        found("A", "yy", 0),
        found("A", "y", 5),
        found("A", "y", 2),
    ];
    let digest = "sha256:d2a04589e5056d268c85e66fce03f496c87f6add11af78e025c22d48eb95d038";
    assert_eq!(signal1_digest(&sorted), digest);
    let mut reversed = sorted.to_vec();
    reversed.reverse();
    assert_eq!(signal1_digest(&reversed), digest);
    assert_eq!(
        signal1_digest(&[]),
        "sha256:4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
    );
}

#[test]
fn the_digest_keeps_every_printable_ascii_character_as_it_is() {
    assert_eq!(
        signal1_digest(&[found("E", "a~b", 1)]),
        "sha256:92675a1cc523f92d6cb24f6b8671c3c1230c7632816b55744a59354d9e0b56a7"
    );
}

#[test]
fn the_digest_writes_text_as_ascii_json() {
    assert_eq!(
        signal1_digest(&[found("E", "é€😀", 0)]),
        "sha256:43573ed4ef308df740ff279e0a6736f2c6911b4efa45bad11d7fba8ff3ac9211"
    );
    assert_eq!(
        signal1_digest(&[found("E", "a\"b\\c\nd\te\r\u{8}\u{c}\u{1}\u{7f}", 7)]),
        "sha256:5d30c9d940a288f11d271c3c3f4ebd1d0903fe19e57647df61da8db35ef5305a"
    );
}

#[test]
fn the_registered_names_and_limits_are_the_ones_the_dossiers_use() {
    assert_eq!(
        HOST_OBSERVERS,
        [
            "host.ast_parse",
            "host.contract_check",
            "host.public_smoke",
            "host.transition_table"
        ]
    );
    assert_eq!(
        FORBIDDEN_OBSERVERS,
        ["MODEL", "LLM", "AGENT", "DETECTOR", "MATCHER"]
    );
    assert_eq!(
        DANGER_KINDS,
        [
            "REPLAY_FAILURE",
            "PROTECTED_FIELD_VIOLATION",
            "MANIFEST_CONTAMINATION",
            "MALFORMED_PAYLOAD"
        ]
    );
    assert_eq!(MATCHER, "regex");
    assert_eq!(SUPPORT_BUDGET, 32);
    assert_eq!(SUPPORT_NEEDED, 3);
}

fn danger(kind: &str, observer: &str) -> Danger {
    Danger::observed(kind, observer, "evidence")
}

fn hold(code: Option<&'static str>) -> Decision {
    Decision {
        disposition: Disposition::Hold,
        code,
    }
}

fn host() -> Danger {
    danger("MALFORMED_PAYLOAD", "host.contract_check")
}

#[test]
fn the_table_gives_each_disposition() {
    let one = [found("E", "x", 0)];
    let admit =
        |matches: &[Match], danger: Option<&Danger>| decide(matches, danger, &HOST_OBSERVERS);
    assert_eq!(
        admit(&[], None),
        Decision {
            disposition: Disposition::Pass,
            code: None
        }
    );
    assert_eq!(
        admit(&one, None),
        Decision {
            disposition: Disposition::Diagnostic,
            code: None
        }
    );
    assert_eq!(admit(&[], Some(&host())), hold(None));
    assert_eq!(admit(&one, Some(&host())), hold(None));
}

#[test]
fn a_danger_from_an_observer_the_caller_does_not_admit_is_ignored() {
    let one = [found("E", "x", 0)];
    let model = danger("MALFORMED_PAYLOAD", "model");
    assert_eq!(
        decide(&one, Some(&model), &HOST_OBSERVERS),
        Decision {
            disposition: Disposition::Diagnostic,
            code: Some("TWO_SIGNAL_COLLAPSE")
        }
    );
    assert_eq!(
        decide(&[], Some(&model), &HOST_OBSERVERS),
        Decision {
            disposition: Disposition::Pass,
            code: Some("UNWITNESSED_DANGER_SIGNAL")
        }
    );
    assert_eq!(
        decide(&one, Some(&model), &["model"]),
        hold(Some("TWO_SIGNAL_COLLAPSE"))
    );
    assert_eq!(
        decide(&one, Some(&host()), &["other"]).code,
        Some("TWO_SIGNAL_COLLAPSE")
    );
    for admitted in HOST_OBSERVERS {
        assert_eq!(
            decide(
                &one,
                Some(&danger("MALFORMED_PAYLOAD", admitted)),
                &HOST_OBSERVERS
            ),
            hold(None)
        );
    }
}

#[test]
fn an_observer_is_compared_without_its_outer_space_and_case_and_nothing_more() {
    let one = [found("E", "x", 0)];
    let admit = |observer: &str| {
        decide(
            &one,
            Some(&danger("MALFORMED_PAYLOAD", observer)),
            &[observer],
        )
    };
    for observer in [
        " Model ",
        "\u{1c}LLM\u{1f}",
        "\tagent\n",
        " Detector",
        "MATCHER ",
        " Regex ",
    ] {
        assert_eq!(
            admit(observer),
            hold(Some("TWO_SIGNAL_COLLAPSE")),
            "{observer:?}"
        );
    }
    for observer in ["xmodelx", "xregexx", "xllmx", "models", "agents"] {
        assert_eq!(admit(observer), hold(None), "{observer:?}");
    }
}

#[test]
fn a_signal_two_that_is_not_independent_still_holds_and_names_why() {
    let one = [found("E", "x", 0)];
    let admit =
        |observer: &str, kind: &str| decide(&one, Some(&danger(kind, observer)), &[observer]);
    for observer in FORBIDDEN_OBSERVERS {
        assert_eq!(
            admit(observer, "MALFORMED_PAYLOAD"),
            hold(Some("TWO_SIGNAL_COLLAPSE")),
            "{observer}"
        );
        assert_eq!(
            admit(
                &format!("  {}\t", observer.to_lowercase()),
                "MALFORMED_PAYLOAD"
            ),
            hold(Some("TWO_SIGNAL_COLLAPSE"))
        );
    }
    assert_eq!(
        admit(MATCHER, "MALFORMED_PAYLOAD"),
        hold(Some("TWO_SIGNAL_COLLAPSE"))
    );
    assert_eq!(
        admit("Regex", "MALFORMED_PAYLOAD"),
        hold(Some("TWO_SIGNAL_COLLAPSE"))
    );
    assert_eq!(
        admit("", "MALFORMED_PAYLOAD"),
        hold(Some("UNWITNESSED_DANGER_SIGNAL"))
    );
    assert_eq!(
        admit(" \u{a0}\u{1c}", "MALFORMED_PAYLOAD"),
        hold(Some("UNWITNESSED_DANGER_SIGNAL"))
    );
    assert_eq!(
        admit("host.x", "MADE_UP"),
        hold(Some("UNREGISTERED_DANGER_KIND"))
    );
    assert_eq!(admit("host.x", ""), hold(Some("UNREGISTERED_DANGER_KIND")));
    for kind in DANGER_KINDS {
        assert_eq!(admit("host.x", kind), hold(None), "{kind}");
    }
}

#[test]
fn with_no_match_there_is_nothing_for_the_signal_to_collapse_into() {
    for observer in ["regex", "model", ""] {
        let seen = danger("MADE_UP", observer);
        assert_eq!(decide(&[], Some(&seen), &[observer]), hold(None));
    }
}

#[test]
fn a_danger_whose_evidence_is_the_digest_of_the_matches_is_the_same_signal() {
    let one = [found("E", "x", 0)];
    let mut copied = host();
    copied.digest = signal1_digest(&one);
    assert_eq!(
        decide(&one, Some(&copied), &HOST_OBSERVERS),
        hold(Some("TWO_SIGNAL_COLLAPSE"))
    );
    copied.digest = signal1_digest(&[found("E", "y", 0)]);
    assert_eq!(decide(&one, Some(&copied), &HOST_OBSERVERS), hold(None));
}

#[test]
fn a_match_inside_the_evidence_is_the_same_token() {
    let overlapping = |offset: usize, text: &str, spans: Vec<(usize, usize)>| {
        let mut seen = host();
        seen.spans = spans;
        decide(&[found("E", text, offset)], Some(&seen), &HOST_OBSERVERS)
    };
    let collapse = hold(Some("TWO_SIGNAL_COLLAPSE"));
    assert_eq!(overlapping(5, "abc", vec![(7, 9)]), collapse);
    assert_eq!(overlapping(5, "abc", vec![(2, 6)]), collapse);
    assert_eq!(overlapping(5, "abc", vec![(5, 6)]), collapse);
    assert_eq!(overlapping(5, "abc", vec![(7, 8)]), collapse);
    assert_eq!(overlapping(5, "abc", vec![(8, 9)]), hold(None));
    assert_eq!(overlapping(5, "abc", vec![(0, 5)]), hold(None));
    assert_eq!(
        overlapping(5, "abc", vec![(0, 2), (9, 12), (3, 6)]),
        collapse
    );
    assert_eq!(overlapping(5, "é€", vec![(6, 7)]), collapse);
    assert_eq!(overlapping(5, "é€", vec![(7, 8)]), hold(None));
    assert_eq!(overlapping(5, "", vec![(5, 6)]), collapse);
    assert_eq!(overlapping(5, "", vec![(6, 7)]), hold(None));
    assert_eq!(overlapping(5, "abc", vec![]), hold(None));
}

#[test]
fn the_dispositions_are_named_as_the_dossiers_name_them() {
    assert_eq!(Disposition::Pass.name(), "PASS");
    assert_eq!(Disposition::Diagnostic.name(), "DIAGNOSTIC_OR_NORMALIZE");
    assert_eq!(Disposition::Hold.name(), "HOLD_OR_REPAIR");
}

fn seen(id: &str, keys: [&str; 4]) -> Observation {
    Observation {
        occurrence: id.to_owned(),
        keys: keys.map(str::to_owned),
    }
}

#[test]
fn three_observations_that_share_nothing_make_an_antibody_provisional() {
    let one = seen("a", ["m1", "s1", "p1", "l1"]);
    let two = seen("b", ["m2", "s2", "p2", "l2"]);
    let three = seen("c", ["m3", "s3", "p3", "l3"]);
    assert_eq!(support(&[one.clone(), two.clone(), three.clone()]), Some(3));
    assert_eq!(custody(&[one.clone(), two.clone(), three]), "Provisional");
    assert_eq!(support(&[one.clone(), two.clone()]), Some(2));
    assert_eq!(custody(&[one, two]), "Candidate");
    assert_eq!((SUPPORT_NEEDED, SUPPORT_BUDGET), (3, 32));
}

#[test]
fn no_observation_supports_nothing() {
    assert_eq!(support(&[]), Some(0));
    assert_eq!(custody(&[]), "Candidate");
}

#[test]
fn a_shared_key_in_any_of_the_four_places_is_a_conflict() {
    for place in 0..4 {
        let mut left = ["a1", "b1", "c1", "d1"];
        let mut right = ["a2", "b2", "c2", "d2"];
        left[place] = "same";
        right[place] = "same";
        assert_eq!(
            support(&[seen("x", left), seen("y", right)]),
            Some(1),
            "place {place}"
        );
    }
}

#[test]
fn an_empty_key_conflicts_with_nothing_and_keys_in_different_places_do_not_meet() {
    let blank = seen("x", ["", "", "", ""]);
    let other = seen("y", ["", "", "", "z"]);
    assert_eq!(support(&[blank, other]), Some(2));
    let crossed = [
        seen("x", ["a", "b", "c", "d"]),
        seen("y", ["b", "a", "d", "c"]),
    ];
    assert_eq!(support(&crossed), Some(2));
}

#[test]
fn a_repeated_occurrence_or_a_repeated_set_of_keys_adds_no_support() {
    let keys = ["m1", "s1", "p1", "l1"];
    let other = ["m2", "s2", "p2", "l2"];
    assert_eq!(support(&[seen("x", keys), seen("x", other)]), Some(1));
    assert_eq!(support(&[seen("x", keys), seen("y", keys)]), Some(1));
    assert_eq!(support(&[seen("", other), seen("", keys)]), Some(2));
    let blank = ["", "", "", ""];
    assert_eq!(support(&[seen("x", blank), seen("y", blank)]), Some(1));
}

#[test]
fn the_repeated_occurrence_is_dropped_before_its_keys_are_looked_at() {
    let first = seen("x", ["m1", "", "", ""]);
    let repeat = seen("x", ["m2", "", "", ""]);
    let third = seen("y", ["m2", "", "", ""]);
    assert_eq!(support(&[first, repeat, third]), Some(2));
}

#[test]
fn a_chain_of_conflicts_has_the_independent_set_a_greedy_pick_misses() {
    let a = seen("a", ["m1", "s1", "", ""]);
    let b = seen("b", ["m1", "s2", "", ""]);
    let c = seen("c", ["m3", "s2", "", ""]);
    let d = seen("d", ["m3", "s4", "", ""]);
    assert_eq!(support(&[a, b, c, d]), Some(2));
}

#[test]
fn more_observations_than_the_budget_have_no_exact_support() {
    let many = |count: usize| -> Vec<Observation> {
        (0..count)
            .map(|place| seen(&format!("o{place}"), [&format!("m{place}"), "", "", ""]))
            .collect()
    };
    assert_eq!(support(&many(SUPPORT_BUDGET)), Some(SUPPORT_BUDGET));
    assert_eq!(support(&many(SUPPORT_BUDGET + 1)), None);
    assert_eq!(custody(&many(SUPPORT_BUDGET + 1)), "Candidate");
    let mut repeated = many(SUPPORT_BUDGET);
    repeated.extend(many(SUPPORT_BUDGET));
    assert_eq!(support(&repeated), Some(SUPPORT_BUDGET));
}

/// The size of the largest set of observations none of which conflicts, by trying every set.
fn by_trying_every_set(nodes: &[Observation]) -> usize {
    let conflict = |left: &Observation, right: &Observation| {
        left.keys
            .iter()
            .zip(&right.keys)
            .any(|(one, other)| !one.is_empty() && one == other)
    };
    (0u32..1 << nodes.len())
        .filter(|chosen| {
            let picked: Vec<&Observation> = (0..nodes.len())
                .filter(|place| chosen >> place & 1 == 1)
                .map(|place| &nodes[place])
                .collect();
            picked
                .iter()
                .enumerate()
                .all(|(at, one)| picked[at + 1..].iter().all(|other| !conflict(one, other)))
        })
        .map(u32::count_ones)
        .max()
        .map_or(0, |best| best as usize)
}

#[test]
fn the_support_is_the_largest_independent_set_on_random_observations() {
    let mut state: u64 = 0x9e37_79b9_7f4a_7c15;
    let mut next = |bound: u64| {
        state = state
            .wrapping_mul(6_364_136_223_846_793_005)
            .wrapping_add(1_442_695_040_888_963_407);
        (state >> 33) % bound
    };
    let alphabet = ["", "a", "b", "c", "d"];
    for round in 0..300 {
        let count = 1 + next(11) as usize;
        let mut nodes: Vec<Observation> = Vec::new();
        let mut keys_seen: BTreeSet<[String; 4]> = BTreeSet::new();
        for place in 0..count {
            let keys = [(); 4].map(|()| alphabet[next(alphabet.len() as u64) as usize].to_owned());
            if keys_seen.insert(keys.clone()) {
                nodes.push(Observation {
                    occurrence: format!("o{place}"),
                    keys,
                });
            }
        }
        assert_eq!(
            support(&nodes),
            Some(by_trying_every_set(&nodes)),
            "round {round}: {nodes:?}"
        );
    }
}
