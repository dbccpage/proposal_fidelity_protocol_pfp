use super::*;

fn presentation() -> Presentation {
    Presentation {
        signature: vec!["a".into(), "b".into(), "c".into()],
        rules: vec![
            Rule {
                name: "r1".into(),
                lhs: "ab".into(),
                rhs: "c".into(),
            },
            Rule {
                name: "r2".into(),
                lhs: "bc".into(),
                rhs: "a".into(),
            },
        ],
    }
}

fn joined_claim() -> CriticalPeakClaim {
    CriticalPeakClaim {
        source: "abc".into(),
        left: ReductionPath {
            steps: vec![ReductionStep {
                rule: "r1".into(),
                position: 0,
            }],
            endpoint: "cc".into(),
        },
        right: ReductionPath {
            steps: vec![ReductionStep {
                rule: "r2".into(),
                position: 1,
            }],
            endpoint: "cc".into(),
        },
        join: Some("cc".into()),
        steps_inspected: 2,
        step_budget: 100,
    }
}

#[test]
fn a_claim_without_a_presentation_produces_obligations() {
    // Acceptance criterion 13.
    let empty = Presentation {
        signature: vec![],
        rules: vec![],
    };
    let verdict = evaluate_peak(&empty, &joined_claim());
    assert_eq!(verdict.token(), "NEEDS_EVIDENCE");
    match verdict {
        PeakVerdict::NeedsEvidence { obligations } => {
            assert!(obligations
                .iter()
                .any(|o| o.contains("explicit rewrite presentation")));
        }
        other => panic!("expected obligations, got {other:?}"),
    }
}

#[test]
fn a_complete_but_forged_joined_claim_is_refused() {
    let verdict = evaluate_peak(&presentation(), &joined_claim());
    assert_eq!(verdict.token(), "NEEDS_EVIDENCE");
}

#[test]
fn a_genuine_joined_claim_is_accepted_as_joined_only() {
    let presentation = Presentation {
        signature: vec!["a".into()],
        rules: vec![Rule {
            name: "shrink".into(),
            lhs: "aa".into(),
            rhs: "a".into(),
        }],
    };
    let claim = CriticalPeakClaim {
        source: "aaa".into(),
        left: ReductionPath {
            steps: vec![ReductionStep {
                rule: "shrink".into(),
                position: 0,
            }],
            endpoint: "aa".into(),
        },
        right: ReductionPath {
            steps: vec![ReductionStep {
                rule: "shrink".into(),
                position: 1,
            }],
            endpoint: "aa".into(),
        },
        join: Some("aa".into()),
        steps_inspected: 2,
        step_budget: 100,
    };

    assert_eq!(
        evaluate_peak(&presentation, &claim),
        PeakVerdict::Joined { join: "aa".into() }
    );
}

/// Mirror of `joined_claim`, forged on the other branch.
///
/// `r1` rewrites `ab -> c`, so `abc` reduces to `cc`; this declares `aa`.
/// The right branch is honest -- `r2` really does yield `aa`.
fn left_forged_claim() -> CriticalPeakClaim {
    CriticalPeakClaim {
        source: "abc".into(),
        left: ReductionPath {
            steps: vec![ReductionStep {
                rule: "r1".into(),
                position: 0,
            }],
            endpoint: "aa".into(),
        },
        right: ReductionPath {
            steps: vec![ReductionStep {
                rule: "r2".into(),
                position: 1,
            }],
            endpoint: "aa".into(),
        },
        join: Some("aa".into()),
        steps_inspected: 2,
        step_budget: 100,
    }
}

// WP-1 acceptance A. Both tests below fail against a checker that resolves
// a step by name and compares producer-authored endpoint strings, because
// such a checker never asks what the rule actually produces.
//
// WP-1 acceptance B is why there are two of them, forged on opposite
// branches. The shipped fixture is forged only on the right, so an
// applicator wired down the left path alone would still pass it. One test
// per branch means no one-sided implementation survives.

#[test]
fn a_right_endpoint_the_presentation_does_not_produce_is_refused() {
    // `r2` rewrites `bc -> a`, so `abc` reduces to `aa`. The claim says
    // `cc` on both branches, and `cc` is not what `r2` produces.
    //
    // The obligation is named rather than the token, because this claim
    // earns NEEDS_EVIDENCE two independent ways -- the replay mismatch
    // below, and separately the declared join matching only one endpoint.
    // Asserting the token alone stays green when right-branch replay is
    // removed, so it would not defend the thing this test exists for.
    assert_replay_mismatch_is_reported(evaluate_peak(&presentation(), &joined_claim()), "right");
}

#[test]
fn a_left_endpoint_the_presentation_does_not_produce_is_refused() {
    // The mirror. `r1` yields `cc` from `abc`; the claim says `aa`.
    assert_replay_mismatch_is_reported(
        evaluate_peak(&presentation(), &left_forged_claim()),
        "left",
    );
}

/// Assert the verdict refuses *because host replay contradicted the
/// declared endpoint on `side`, not for some other reason that happens to
/// share the token.
///
/// A branch-blind applicator is killed here and nowhere else.
fn assert_replay_mismatch_is_reported(verdict: PeakVerdict, side: &str) {
    let PeakVerdict::NeedsEvidence { obligations } = &verdict else {
        panic!("expected NEEDS_EVIDENCE naming a {side} replay mismatch, got {verdict:?}");
    };
    assert!(
        obligations.iter().any(|o| {
            o.starts_with(&format!("{side} path declares endpoint"))
                && o.contains("replay from the source produces")
        }),
        "no obligation reports that host replay of the {side} branch \
         contradicted its declared endpoint; obligations were {obligations:?}"
    );
}

/// A presentation with no termination witness: both rules grow the term.
fn growing_presentation() -> Presentation {
    Presentation {
        signature: vec!["a".into(), "b".into()],
        rules: vec![
            Rule {
                name: "g1".into(),
                lhs: "a".into(),
                rhs: "aa".into(),
            },
            Rule {
                name: "g2".into(),
                lhs: "b".into(),
                rhs: "bb".into(),
            },
        ],
    }
}

/// Length-*preserving*: no termination witness, yet the reachable set from
/// any term is finite.
///
/// This separates the two fences. With growing rules the budget stops an
/// unwitnessed decision on its own, so such a fixture cannot tell whether
/// the witness check does any work. Here the sets close easily, and the
/// only thing standing between the host and an exhaustive verdict is the
/// missing witness.
fn swapping_presentation() -> Presentation {
    Presentation {
        signature: vec!["a".into(), "b".into(), "c".into(), "d".into()],
        rules: vec![
            Rule {
                name: "p1".into(),
                lhs: "ab".into(),
                rhs: "ba".into(),
            },
            Rule {
                name: "p2".into(),
                lhs: "cd".into(),
                rhs: "dc".into(),
            },
        ],
    }
}

/// Length-reducing, and the two branches diverge before reconverging two
/// steps later at `z`.
fn reconverging_presentation() -> Presentation {
    Presentation {
        signature: vec!["a".into(), "b".into(), "e".into(), "z".into()],
        rules: vec![
            Rule {
                name: "s1".into(),
                lhs: "ab".into(),
                rhs: "e".into(),
            },
            Rule {
                name: "s2".into(),
                lhs: "ba".into(),
                rhs: "e".into(),
            },
            Rule {
                name: "s3".into(),
                lhs: "ea".into(),
                rhs: "z".into(),
            },
            Rule {
                name: "s4".into(),
                lhs: "ae".into(),
                rhs: "z".into(),
            },
        ],
    }
}

#[test]
fn an_unjoined_peak_without_a_termination_witness_stays_bounded() {
    // The fence that has not moved. `g1` and `g2` grow the term, so no
    // witness exists, the reachable sets are infinite, and a search that
    // found nothing found nothing. Bounded is the only honest answer.
    assert!(!is_length_reducing(&growing_presentation()));

    let claim = CriticalPeakClaim {
        source: "ab".into(),
        left: ReductionPath {
            steps: vec![ReductionStep {
                rule: "g1".into(),
                position: 0,
            }],
            endpoint: "aab".into(),
        },
        right: ReductionPath {
            steps: vec![ReductionStep {
                rule: "g2".into(),
                position: 1,
            }],
            endpoint: "abb".into(),
        },
        join: None,
        steps_inspected: 100,
        step_budget: 100,
    };

    let verdict = evaluate_peak(&growing_presentation(), &claim);
    assert_eq!(
        verdict.token(),
        "BOUNDED_WITH_UNJOINED_PEAK",
        "without a termination witness no exhaustive verdict is available; got {verdict:?}"
    );
}

#[test]
fn a_bounded_verdict_reports_host_work_not_producer_testimony() {
    // The laundering this fix closes. The verdict used to copy
    // claim.steps_inspected verbatim, so a host verdict reported a number
    // the host never derived. Here the producer declares 999 -- inside its
    // own budget, so no consistency obligation fires -- and the host
    // declines after exhausting its own search budget. The verdict must
    // report that work, not 999.
    let claim = CriticalPeakClaim {
        source: "ab".into(),
        left: ReductionPath {
            steps: vec![ReductionStep {
                rule: "g1".into(),
                position: 0,
            }],
            endpoint: "aab".into(),
        },
        right: ReductionPath {
            steps: vec![ReductionStep {
                rule: "g2".into(),
                position: 1,
            }],
            endpoint: "abb".into(),
        },
        join: None,
        steps_inspected: 999,
        step_budget: 10_000,
    };

    let verdict = evaluate_peak(&growing_presentation(), &claim);
    match verdict {
        PeakVerdict::BoundedWithUnjoinedPeak {
            host_expansions,
            step_budget,
        } => {
            assert_ne!(
                host_expansions, claim.steps_inspected,
                "the verdict is echoing the producer's declared figure"
            );
            assert!(
                host_expansions > 0,
                "the host searched until the budget ran out and must report it"
            );
            assert_eq!(step_budget, 10_000);
        }
        other => panic!("expected a bounded verdict, got {other:?}"),
    }
}

#[test]
fn a_bounded_verdict_counts_the_work_the_host_actually_did() {
    // The other direction: where the host DOES spend budget before
    // declining, the figure it reports is its own count, not zero and not
    // the producer's.
    let mut claim = joined_claim();
    claim.right.endpoint = "aa".into();
    claim.join = None;
    claim.step_budget = 1;
    claim.steps_inspected = 0;

    match evaluate_peak(&presentation(), &claim) {
        PeakVerdict::BoundedWithUnjoinedPeak {
            host_expansions, ..
        } => assert_eq!(
            host_expansions, claim.step_budget,
            "the budget is one cap over both branches, not a fresh allowance per side"
        ),
        other => panic!("expected a bounded verdict, got {other:?}"),
    }
}

#[test]
fn a_claim_that_outspends_its_own_budget_is_refused() {
    // steps_inspected no longer reaches any verdict, but it is still
    // checked against the producer's own declared budget: a claim
    // reporting more work than it declared is internally inconsistent, and
    // that is decidable without believing either number.
    let mut claim = joined_claim();
    claim.steps_inspected = 101;
    claim.step_budget = 100;

    let verdict = evaluate_peak(&presentation(), &claim);
    let PeakVerdict::NeedsEvidence { obligations } = &verdict else {
        panic!("expected obligations, got {verdict:?}");
    };
    assert!(
        obligations
            .iter()
            .any(|o| o.contains("101") && o.contains("100")),
        "no obligation reports the inconsistency; obligations were {obligations:?}"
    );
}

#[test]
fn identical_endpoints_join_without_any_length_reduction() {
    // Joinability at zero further steps is a string comparison. Demanding
    // a witness first declined to answer a question already answered, and
    // reported "no join found" over two identical strings.
    assert!(!is_length_reducing(&swapping_presentation()));

    let claim = CriticalPeakClaim {
        source: "abcd".into(),
        left: ReductionPath {
            steps: vec![ReductionStep {
                rule: "p1".into(),
                position: 0,
            }],
            endpoint: "bacd".into(),
        },
        right: ReductionPath {
            steps: vec![ReductionStep {
                rule: "p1".into(),
                position: 0,
            }],
            endpoint: "bacd".into(),
        },
        join: None,
        steps_inspected: 0,
        step_budget: 1_000,
    };

    // Same rule at the same position on both sides is not a divergence, so
    // build the divergence out of two distinct steps that land together.
    let mut divergent = claim.clone();
    divergent.right.steps = vec![ReductionStep {
        rule: "p2".into(),
        position: 2,
    }];
    divergent.right.endpoint = "abdc".into();

    // Sanity: that pair really does differ, so it exercises the general
    // path rather than the identical-endpoint short circuit -- and the
    // general path now decides it, because both sets close.
    assert_eq!(
        evaluate_peak(&swapping_presentation(), &divergent).token(),
        "JOINED"
    );

    // And the identical-endpoint case is decided, witness or no witness.
    let mut same = claim.clone();
    same.right.steps = vec![ReductionStep {
        rule: "p2".into(),
        position: 2,
    }];
    same.right.endpoint = "bacd".into();
    // p2 on "abcd" gives "abdc", not "bacd", so the declared endpoint is
    // refused before joinability is even considered -- which is correct.
    assert_eq!(
        evaluate_peak(&swapping_presentation(), &same).token(),
        "NEEDS_EVIDENCE"
    );
}

/// Two common reducts, where the nearest and the lexicographically least
/// are DIFFERENT terms. Every other fixture has a single common reduct, so
/// none of them can tell the two selection rules apart.
///
/// `abcd` splits to `mcd` and `abn`; both reach `mn` in one more step and
/// `a` in two. So `mn` costs 1+1 and `a` costs 2+2, while byte order puts
/// `a` first.
fn two_join_candidates_presentation() -> Presentation {
    Presentation {
        signature: vec![
            "a".into(),
            "b".into(),
            "c".into(),
            "d".into(),
            "m".into(),
            "n".into(),
        ],
        rules: vec![
            Rule {
                name: "rA".into(),
                lhs: "ab".into(),
                rhs: "m".into(),
            },
            Rule {
                name: "rB".into(),
                lhs: "cd".into(),
                rhs: "n".into(),
            },
            Rule {
                name: "rC".into(),
                lhs: "mn".into(),
                rhs: "a".into(),
            },
        ],
    }
}

fn two_join_candidates_claim() -> CriticalPeakClaim {
    CriticalPeakClaim {
        source: "abcd".into(),
        left: ReductionPath {
            steps: vec![ReductionStep {
                rule: "rA".into(),
                position: 0,
            }],
            endpoint: "mcd".into(),
        },
        right: ReductionPath {
            steps: vec![ReductionStep {
                rule: "rB".into(),
                position: 2,
            }],
            endpoint: "abn".into(),
        },
        join: None,
        steps_inspected: 0,
        step_budget: 10_000,
    }
}

#[test]
fn the_reported_join_is_the_nearest_not_the_lexicographically_first() {
    // The defect: taking the first element of a BTreeSet intersection
    // reported whichever term sorted first in byte order -- neither the
    // nearest join nor a normal form, just the container's iteration
    // order, chosen by nobody.
    //
    // Here byte order says "a" and distance says "mn". A reader checking
    // the witness has to redo two steps per branch for "a" and one for
    // "mn", and only one of those is the reason the peak converges.
    let verdict = evaluate_peak(
        &two_join_candidates_presentation(),
        &two_join_candidates_claim(),
    );
    assert_eq!(
        verdict,
        PeakVerdict::Joined { join: "mn".into() },
        "expected the nearest common reduct; \"a\" is the lexicographically \
         first one and is twice as far from both endpoints"
    );
}

#[test]
fn the_verdict_does_not_depend_on_whether_the_producer_testified() {
    // The defect: a declared join short-circuited the decision entirely
    // when it equalled both endpoints, so the SAME peak returned a
    // different payload according to whether a `join` field was present.
    // The producer's testimony was selecting the host's answer.
    //
    // Here the producer declares "a" -- a genuine common reduct, but the
    // far one. The host must report its own nearest, "mn", and must report
    // exactly what it reports when nothing is declared at all.
    let presentation = two_join_candidates_presentation();

    let silent = evaluate_peak(&presentation, &two_join_candidates_claim());

    let mut testified = two_join_candidates_claim();
    testified.join = Some("a".into());
    let spoken = evaluate_peak(&presentation, &testified);

    assert_eq!(
        silent, spoken,
        "the host's verdict changed because the producer spoke"
    );
    assert_eq!(spoken, PeakVerdict::Joined { join: "mn".into() });
}

#[test]
fn a_true_but_distant_declared_join_is_accepted_not_refused() {
    // The old check compared the declared join against the two endpoints,
    // so a join two steps down from both -- a perfectly true claim -- was
    // refused for not equalling either. Reachability is the right test.
    let mut claim = two_join_candidates_claim();
    claim.join = Some("a".into());
    assert_eq!(
        evaluate_peak(&two_join_candidates_presentation(), &claim).token(),
        "JOINED",
        "\"a\" is reachable from both endpoints, so declaring it is a true claim"
    );
}

#[test]
fn an_unverifiable_declaration_does_not_ride_out_on_a_verdict() {
    // Where the host cannot check the declaration -- here because the
    // budget closes neither reachable set -- a verdict reached without it
    // must not be reported as though the declaration were confirmed.
    assert!(!is_length_reducing(&swapping_presentation()));

    let claim = CriticalPeakClaim {
        source: "abcd".into(),
        left: ReductionPath {
            steps: vec![ReductionStep {
                rule: "p1".into(),
                position: 0,
            }],
            endpoint: "bacd".into(),
        },
        right: ReductionPath {
            steps: vec![ReductionStep {
                rule: "p2".into(),
                position: 2,
            }],
            endpoint: "abdc".into(),
        },
        join: Some("badc".into()),
        steps_inspected: 0,
        // Too small to close either set, so the declaration is unchecked.
        step_budget: 1,
    };

    assert_eq!(
        evaluate_peak(&swapping_presentation(), &claim).token(),
        "BOUNDED_WITH_UNJOINED_PEAK",
        "an unchecked declaration must not be treated as established"
    );
}

/// Genuinely NON-TERMINATING, with a finite reachable set.
///
/// `swapping_presentation` was doing this job and could not: `ab -> ba`
/// and `cd -> dc` each move a letter rightwards past another, so the count
/// of inversions strictly decreases and the system terminates. It separates
/// closure from `is_length_reducing` -- the syntactic test -- but NOT from
/// termination itself, which is the property the redesign actually dropped.
///
/// These two rules cycle forever (`ab -> ba -> ab -> ...`), so no
/// termination order exists at all, while the reachable set is confined to
/// permutations of a fixed multiset and closes immediately.
fn cycling_presentation() -> Presentation {
    Presentation {
        signature: vec!["a".into(), "b".into()],
        rules: vec![
            Rule {
                name: "q1".into(),
                lhs: "ab".into(),
                rhs: "ba".into(),
            },
            Rule {
                name: "q2".into(),
                lhs: "ba".into(),
                rhs: "ab".into(),
            },
        ],
    }
}

#[test]
fn a_non_terminating_presentation_is_still_decided_when_it_closes() {
    // The claim the whole redesign rests on, and the only test that can
    // defend it: closure decides joinability where NO termination argument
    // exists, not merely where the cheap syntactic one fails.
    //
    // q1 and q2 invert each other, so the rewrite relation has an infinite
    // chain and the system is not terminating under any order. Its
    // reachable set is nonetheless {abab, baab, abba, baba, bbaa, aabb, ...}
    // -- permutations of a fixed multiset -- so the frontier empties and
    // the sets are complete.
    assert!(!is_length_reducing(&cycling_presentation()));

    let reached = reachable(&cycling_presentation(), "ab", 10_000);
    let terms = reached
        .terms
        .expect("a cycling system still closes: the reachable set is finite");
    assert!(
        terms.contains_key("ab") && terms.contains_key("ba"),
        "the cycle is real and both terms are reachable: {terms:?}"
    );

    let claim = CriticalPeakClaim {
        source: "abab".into(),
        left: ReductionPath {
            steps: vec![ReductionStep {
                rule: "q1".into(),
                position: 0,
            }],
            endpoint: "baab".into(),
        },
        right: ReductionPath {
            steps: vec![ReductionStep {
                rule: "q1".into(),
                position: 2,
            }],
            endpoint: "abba".into(),
        },
        join: None,
        steps_inspected: 0,
        step_budget: 10_000,
    };

    let verdict = evaluate_peak(&cycling_presentation(), &claim);
    assert_ne!(
        verdict.token(),
        "BOUNDED_WITH_UNJOINED_PEAK",
        "a non-terminating system whose sets close must still be decided; \
         refusing here is the behaviour the termination gate had and the \
         reason it was removed. got {verdict:?}"
    );
}

#[test]
fn an_unbounded_budget_still_terminates_the_search() {
    // saturating_add caps `expansions` at u64::MAX, so a strict `>`
    // comparison against a budget of u64::MAX can never fire and the guard
    // is silently disarmed. The budget is producer-supplied, so that value
    // is reachable from the wire.
    let reached = reachable(&presentation(), "abc", u64::MAX);
    assert!(
        reached.terms.is_some(),
        "the closure completed rather than spinning"
    );
}

#[test]
fn the_budget_is_charged_only_for_viable_redex_positions() {
    // The bound used to run to `width` inclusive, charging for positions
    // where the left-hand side could not fit and for rules longer than the
    // term. The decline threshold was therefore set by a loop bound rather
    // than by the search, and the field's own documentation -- "rewrite
    // steps inspected" -- did not describe what was counted.
    //
    // Presentation {aa -> a}, term "aa": exactly one viable position (0).
    // Its reduct "a" is shorter than the rule, so it admits none.
    let presentation = Presentation {
        signature: vec!["a".into()],
        rules: vec![Rule {
            name: "r1".into(),
            lhs: "aa".into(),
            rhs: "a".into(),
        }],
    };

    let reached = reachable(&presentation, "aa", 1_000);
    assert_eq!(
        reached.terms.map(|t| t.len()),
        Some(2),
        "the closure is {{aa, a}}"
    );
    assert_eq!(
        reached.expansions, 1,
        "one viable probe on \"aa\" and none on \"a\"; the old bound charged 5"
    );
}

#[test]
fn a_rule_longer_than_the_term_costs_nothing() {
    let presentation = Presentation {
        signature: vec!["a".into(), "b".into()],
        rules: vec![Rule {
            name: "wide".into(),
            lhs: "abab".into(),
            rhs: "a".into(),
        }],
    };
    let reached = reachable(&presentation, "ab", 1_000);
    assert_eq!(
        reached.expansions, 0,
        "no position in \"ab\" can hold \"abab\""
    );
    assert_eq!(reached.terms.map(|t| t.len()), Some(1));
}

#[test]
fn both_candidates_really_are_common_reducts() {
    // Guards the fixture itself. If "a" stopped being reachable from both
    // endpoints, the test above would pass for the wrong reason -- there
    // would be nothing for the selection rule to choose BETWEEN.
    let presentation = two_join_candidates_presentation();
    for endpoint in ["mcd", "abn"] {
        let reached = reachable(&presentation, endpoint, 10_000);
        let terms = reached.terms.expect("the closure fits the budget");
        assert_eq!(
            terms.get("mn"),
            Some(&1),
            "{endpoint} should reach mn in one step"
        );
        assert_eq!(
            terms.get("a"),
            Some(&2),
            "{endpoint} should reach a in two steps"
        );
    }
}

#[test]
fn a_closed_search_space_is_a_licence_to_decide() {
    // This test previously asserted the opposite, and the assertion was
    // wrong. `p1` and `p2` only permute symbols, so nothing shrinks and the
    // old termination gate refused any exhaustive verdict here.
    //
    // But closure, not termination, is what deciding ONE PAIR needs. Both
    // reachable sets close well inside the budget, and two closed sets
    // settle joinability by intersection whatever the rules do to length.
    // The gate was refusing an answer it could soundly give.
    assert!(!is_length_reducing(&swapping_presentation()));

    let claim = CriticalPeakClaim {
        source: "abcd".into(),
        left: ReductionPath {
            steps: vec![ReductionStep {
                rule: "p1".into(),
                position: 0,
            }],
            endpoint: "bacd".into(),
        },
        right: ReductionPath {
            steps: vec![ReductionStep {
                rule: "p2".into(),
                position: 2,
            }],
            endpoint: "abdc".into(),
        },
        join: None,
        steps_inspected: 0,
        step_budget: 10_000,
    };

    let verdict = evaluate_peak(&swapping_presentation(), &claim);
    assert_eq!(
        verdict,
        PeakVerdict::Joined {
            join: "badc".into()
        },
        "both sets close, so the peak is decided; got {verdict:?}"
    );
}

#[test]
fn a_terminating_presentation_decides_non_joinability() {
    // The fixture that shipped asserting JOINED. With rules that strictly
    // shrink the term, both reachable sets close, and they are disjoint:
    // nothing rewrites "cc" or "aa". That is a decision, not a failed
    // search, so it is reported as such and carries its witness.
    let mut claim = joined_claim();
    claim.right.endpoint = "aa".into();
    claim.join = None;

    let verdict = evaluate_peak(&presentation(), &claim);
    assert_eq!(
        verdict,
        PeakVerdict::NotJoinable {
            left_endpoint: "cc".into(),
            right_endpoint: "aa".into(),
            basis: ExhaustionBasis::ClosedReachableSets,
        },
        "cc and aa have disjoint reachable sets under a length-reducing \
         presentation; got {verdict:?}"
    );
}

#[test]
fn an_exhausted_budget_declines_to_decide() {
    // A witness alone is not enough. If the budget cannot close both
    // reachable sets, the host has a partial exploration and must not
    // report NOT_JOINABLE from it.
    let mut claim = joined_claim();
    claim.right.endpoint = "aa".into();
    claim.join = None;
    claim.step_budget = 1;
    // The fixture declared 2 steps inspected against a budget of 1, which
    // is an internally inconsistent claim and now earns its own obligation.
    // Keep the budget the thing under test.
    claim.steps_inspected = 1;

    let verdict = evaluate_peak(&presentation(), &claim);
    assert_eq!(
        verdict.token(),
        "BOUNDED_WITH_UNJOINED_PEAK",
        "a budget too small to close the reachable sets must not yield an \
         exhaustive verdict; got {verdict:?}"
    );
}

#[test]
fn the_host_finds_a_join_the_producer_did_not_declare() {
    // "aba" splits to "ea" and "ae", which are different terms, and both
    // reduce to "z" one step later. The producer declared no join; the
    // host decides there is one.
    let claim = CriticalPeakClaim {
        source: "aba".into(),
        left: ReductionPath {
            steps: vec![ReductionStep {
                rule: "s1".into(),
                position: 0,
            }],
            endpoint: "ea".into(),
        },
        right: ReductionPath {
            steps: vec![ReductionStep {
                rule: "s2".into(),
                position: 1,
            }],
            endpoint: "ae".into(),
        },
        join: None,
        steps_inspected: 0,
        step_budget: 1000,
    };

    let verdict = evaluate_peak(&reconverging_presentation(), &claim);
    assert_eq!(
        verdict,
        PeakVerdict::Joined { join: "z".into() },
        "ea and ae both reduce to z, so the peak joins; got {verdict:?}"
    );
}

#[test]
fn length_reduction_requires_every_rule_to_shrink() {
    // One non-shrinking rule is enough to withdraw the witness from the
    // whole presentation, because termination is a property of the system.
    assert!(is_length_reducing(&presentation()));

    let mut mixed = presentation();
    mixed.rules.push(Rule {
        name: "grow".into(),
        lhs: "z".into(),
        rhs: "zz".into(),
    });
    assert!(!is_length_reducing(&mixed));

    // An empty presentation has nothing to witness.
    assert!(!is_length_reducing(&Presentation {
        signature: vec![],
        rules: vec![],
    }));
}

#[test]
fn a_path_citing_an_undeclared_rule_is_refused() {
    let mut claim = joined_claim();
    claim.left.steps = vec![ReductionStep {
        rule: "r99".into(),
        position: 0,
    }];
    match evaluate_peak(&presentation(), &claim) {
        PeakVerdict::NeedsEvidence { obligations } => {
            assert!(obligations.iter().any(|o| o.contains("r99")));
        }
        other => panic!("expected obligations, got {other:?}"),
    }
}

#[test]
fn two_identical_branches_are_not_a_divergence() {
    let mut claim = joined_claim();
    claim.right.steps = claim.left.steps.clone();
    match evaluate_peak(&presentation(), &claim) {
        PeakVerdict::NeedsEvidence { obligations } => {
            assert!(obligations.iter().any(|o| o.contains("not a divergence")));
        }
        other => panic!("expected obligations, got {other:?}"),
    }
}

#[test]
fn a_join_that_is_not_a_common_reduct_is_refused() {
    // The check is now reachability, not equality with the endpoints, which
    // is strictly stronger: a declared join two steps down from both is a
    // true claim the old comparison would have refused, and a term equal to
    // neither is refused for the reason that actually holds.
    let mut claim = joined_claim();
    claim.right.endpoint = "aa".into();
    claim.join = Some("elsewhere".into());
    match evaluate_peak(&presentation(), &claim) {
        PeakVerdict::NeedsEvidence { obligations } => {
            assert!(
                obligations
                    .iter()
                    .any(|o| o.contains("elsewhere")
                        && o.contains("not reachable from both endpoints")),
                "the obligation must name the declared term and the reason it \
                 fails; obligations were {obligations:?}"
            );
        }
        other => panic!("expected obligations, got {other:?}"),
    }
}

#[test]
fn a_missing_budget_is_an_obligation() {
    let mut claim = joined_claim();
    claim.step_budget = 0;
    match evaluate_peak(&presentation(), &claim) {
        PeakVerdict::NeedsEvidence { obligations } => {
            assert!(obligations
                .iter()
                .any(|o| o.contains("finite search budget")));
        }
        other => panic!("expected obligations, got {other:?}"),
    }
}

#[path = "operation_tests.rs"]
mod operations;

// Origin: engine/crates_rs/pfp_runtime/src/rewriting/tests.rs
// Claim: urn:core:crates_rs:pfp-runtime:tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddb7f5e70 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddb7f5e70` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordb7f5e70 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrordb7f5e70 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordb7f5e70 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordb7f5e70 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddb7f5e70 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordb7f5e70> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordb7f5e70::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordb7f5e70::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordb7f5e70::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod l4_boundary_tests_db7f5e70 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorddb7f5e70::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorddb7f5e70::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorddb7f5e70::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorddb7f5e70::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorddb7f5e70::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrordb7f5e70::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrordb7f5e70::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
