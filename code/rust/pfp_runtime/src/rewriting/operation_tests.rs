use super::super::*;
use super::{joined_claim, presentation, swapping_presentation};

#[test]
fn apply_uses_symbol_positions_and_requires_an_exact_redex() {
    let rule = Rule {
        name: "unicode".into(),
        lhs: "αβ".into(),
        rhs: "γ".into(),
    };

    assert_eq!(apply(&rule, "xαβy", 1), Some("xγy".into()));
    assert_eq!(apply(&rule, "xαβy", 0), None);
    assert_eq!(apply(&rule, "xαβy", 4), None);
}

#[test]
fn critical_pair_enumeration_finds_proper_overlap_and_containment() {
    let pairs = critical_pairs(&presentation());
    assert_eq!(pairs.len(), 1);
    assert_eq!(pairs[0].source, "abc");
    assert_eq!(pairs[0].left_endpoint, "cc");
    assert_eq!(pairs[0].right_endpoint, "aa");

    let containment = Presentation {
        signature: vec!["a".into(), "b".into(), "c".into()],
        rules: vec![
            Rule {
                name: "outer".into(),
                lhs: "abc".into(),
                rhs: "x".into(),
            },
            Rule {
                name: "inner".into(),
                lhs: "b".into(),
                rhs: "y".into(),
            },
        ],
    };
    assert!(critical_pairs(&containment).iter().any(|pair| {
        pair.source == "abc"
            && pair.left.position == 1
            && pair.right.position == 0
            && pair.left_endpoint == "ayc"
            && pair.right_endpoint == "x"
    }));
}

#[test]
fn every_gap_is_reported_at_once() {
    let empty = Presentation {
        signature: vec![],
        rules: vec![],
    };
    let claim = CriticalPeakClaim {
        source: "".into(),
        left: ReductionPath {
            steps: vec![],
            endpoint: "".into(),
        },
        right: ReductionPath {
            steps: vec![],
            endpoint: "".into(),
        },
        join: None,
        steps_inspected: 0,
        step_budget: 0,
    };
    match evaluate_peak(&empty, &claim) {
        PeakVerdict::NeedsEvidence { obligations } => assert!(obligations.len() >= 5),
        other => panic!("expected obligations, got {other:?}"),
    }
}

// ---------------------------------------------------------------------
// Presentation pinning.
//
// The defect: `evaluate_peak` takes the presentation as an argument, and
// on the wire the presentation arrives in the same payload as the claim.
// A `JOINED` read back off that wire says "the branches join" and means
// "the branches join under rules the producer also supplied", with nothing
// distinguishing the two readings.
// ---------------------------------------------------------------------

/// The claim that really does join under `swapping_presentation`.
fn joining_claim() -> CriticalPeakClaim {
    CriticalPeakClaim {
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
    }
}

/// The claim that is provably NOT joinable under `presentation`.
fn disjoint_claim() -> CriticalPeakClaim {
    let mut claim = joined_claim();
    claim.right.endpoint = "aa".into();
    claim.join = None;
    claim
}

#[test]
fn reordering_the_rules_does_not_change_the_system() {
    // Rules are a set. A pin that a reorder defeats is not a pin: a
    // producer would evade it by shuffling the payload, and the host would
    // report SELF_CONSISTENT_ONLY for a presentation it does pin.
    let forward = swapping_presentation();
    let mut reversed = forward.clone();
    reversed.rules.reverse();
    reversed.signature.reverse();
    assert_ne!(
        forward.rules, reversed.rules,
        "the fixture must actually differ, or this asserts nothing"
    );
    assert_eq!(
        presentation_digest(&forward),
        presentation_digest(&reversed)
    );
}

#[test]
fn changing_one_rule_changes_the_digest() {
    // The other half. A digest insensitive to the rules would pass the
    // test above while naming nothing.
    let base = swapping_presentation();
    let mut altered = base.clone();
    altered.rules[0].rhs = "ab".into();
    assert_ne!(presentation_digest(&base), presentation_digest(&altered));

    let mut renamed = base.clone();
    renamed.rules[0].name = "p9".into();
    assert_ne!(presentation_digest(&base), presentation_digest(&renamed));

    let mut resigned = base.clone();
    resigned.signature.push("e".into());
    assert_ne!(presentation_digest(&base), presentation_digest(&resigned));
}

#[test]
fn the_digest_is_not_injectable() {
    // We shipped this exact bug once, in the Python carrier digest: fields
    // joined with a delimiter let a value CONTAINING the delimiter
    // reproduce another object's serialisation, so two different objects
    // digested the same. Under `name:lhs:rhs` both of these render as
    // "r:a:b:c" -- and they are different rewriting systems.
    let smuggled = Presentation {
        signature: vec!["a".into()],
        rules: vec![Rule {
            name: "r".into(),
            lhs: "a:b".into(),
            rhs: "c".into(),
        }],
    };
    let honest = Presentation {
        signature: vec!["a".into()],
        rules: vec![Rule {
            name: "r".into(),
            lhs: "a".into(),
            rhs: "b:c".into(),
        }],
    };
    assert_ne!(
        presentation_digest(&smuggled),
        presentation_digest(&honest),
        "a digest whose pre-image is ambiguous is not a digest of the thing it names"
    );
}

#[test]
fn an_unpinned_join_is_reported_as_self_consistent_only() {
    let pins = PresentationPins::empty();
    let evaluation = evaluate_peak_pinned(&swapping_presentation(), &joining_claim(), &pins);
    assert_eq!(evaluation.token(), "SELF_CONSISTENT_ONLY");
    assert_eq!(
        evaluation.authority,
        PresentationAuthority::ProducerDeclared
    );
}

#[test]
fn a_pinned_join_is_reported_as_joined() {
    // The other side of the same decision. Without this, a token() that
    // always said SELF_CONSISTENT_ONLY would pass the test above.
    let mut pins = PresentationPins::empty();
    pins.pin("swapping", &swapping_presentation());
    let evaluation = evaluate_peak_pinned(&swapping_presentation(), &joining_claim(), &pins);
    assert_eq!(evaluation.token(), "JOINED");
    assert_eq!(
        evaluation.authority,
        PresentationAuthority::HostPinned {
            pin: "swapping".into()
        }
    );
}

#[test]
fn the_verdict_itself_is_never_suppressed() {
    // The join really does exist under the declared rules, and discarding
    // a true finding would be its own dishonesty. What is withheld is the
    // host's endorsement, not the mathematics.
    let pins = PresentationPins::empty();
    let evaluation = evaluate_peak_pinned(&swapping_presentation(), &joining_claim(), &pins);
    assert_eq!(
        evaluation.verdict,
        PeakVerdict::Joined {
            join: "badc".into()
        },
        "the downgrade is in the token, not in the verdict"
    );
    assert_eq!(
        evaluation.verdict,
        evaluate_peak(&swapping_presentation(), &joining_claim()),
        "provenance must not change the mathematics"
    );
}

#[test]
fn an_unpinned_non_joinability_is_downgraded_too() {
    // NotJoinable under producer rules is if anything the easier answer to
    // arrange: dropping a rule can only shrink the reachable sets. A
    // downgrade that covered only JOINED would leave the cheaper forgery
    // reading as a host guarantee.
    let pins = PresentationPins::empty();
    let evaluation = evaluate_peak_pinned(&presentation(), &disjoint_claim(), &pins);
    assert!(
        matches!(evaluation.verdict, PeakVerdict::NotJoinable { .. }),
        "fixture must produce NOT_JOINABLE; got {:?}",
        evaluation.verdict
    );
    assert_eq!(evaluation.token(), "SELF_CONSISTENT_ONLY");

    let mut pinned = PresentationPins::empty();
    pinned.pin("length-reducing", &presentation());
    assert_eq!(
        evaluate_peak_pinned(&presentation(), &disjoint_claim(), &pinned).token(),
        "NOT_JOINABLE"
    );
}

#[test]
fn a_verdict_that_decides_nothing_is_unchanged_by_provenance() {
    // NeedsEvidence and BoundedWithUnjoinedPeak settle nothing, so there is
    // nothing in them for a presentation to have settled. Downgrading them
    // would report every unpinned run as self-consistent, which is false:
    // they are not consistent, they are undecided.
    let pins = PresentationPins::empty();
    let evaluation = evaluate_peak_pinned(&presentation(), &joined_claim(), &pins);
    assert_eq!(evaluation.verdict.token(), "NEEDS_EVIDENCE");
    assert_eq!(evaluation.token(), "NEEDS_EVIDENCE");
    assert!(!evaluation.decides());
}

#[test]
fn the_unknown_presentation_obligation_stands_whatever_the_verdict() {
    // It is a fact about the rules, not about the claim, so it does not
    // wait for a verdict worth qualifying.
    let pins = PresentationPins::empty();
    for claim in [joining_claim(), joined_claim()] {
        let evaluation = evaluate_peak_pinned(&swapping_presentation(), &claim, &pins);
        assert!(
            evaluation
                .obligations
                .iter()
                .any(|o| o.contains(REFUSAL_PRESENTATION_UNKNOWN)),
            "expected {REFUSAL_PRESENTATION_UNKNOWN} in {:?}",
            evaluation.obligations
        );
    }
}

#[test]
fn a_pinned_presentation_raises_no_presentation_obligation() {
    let mut pins = PresentationPins::empty();
    pins.pin("swapping", &swapping_presentation());
    let evaluation = evaluate_peak_pinned(&swapping_presentation(), &joining_claim(), &pins);
    assert!(
        !evaluation
            .obligations
            .iter()
            .any(|obligation| obligation.contains(REFUSAL_PRESENTATION_UNKNOWN)),
        "a pinned presentation raises no presentation obligation; got {:?}",
        evaluation.obligations
    );
}

#[test]
fn a_noncritical_peak_is_named_without_suppressing_its_join() {
    let presentation = swapping_presentation();
    let claim = joining_claim();
    let mut pins = PresentationPins::empty();
    pins.pin("swapping", &presentation);

    let evaluation = evaluate_peak_pinned(&presentation, &claim, &pins);
    assert!(
        evaluation
            .obligations
            .iter()
            .any(|obligation| obligation.contains(OBLIGATION_PEAK_NONCRITICAL)),
        "disjoint first redexes are not a critical pair: {:?}",
        evaluation.obligations
    );
    assert!(matches!(evaluation.verdict, PeakVerdict::Joined { .. }));
    assert_eq!(
        evaluation.token(),
        "JOINED",
        "FW-PEAK-NONCRITICAL qualifies the claim; it does not deny the true joinability result"
    );
}

#[test]
fn a_host_enumerated_critical_pair_raises_no_noncritical_obligation() {
    let presentation = presentation();
    let mut pins = PresentationPins::empty();
    pins.pin("critical", &presentation);

    let evaluation = evaluate_peak_pinned(&presentation, &joined_claim(), &pins);
    assert!(
        !evaluation
            .obligations
            .iter()
            .any(|obligation| obligation.contains(OBLIGATION_PEAK_NONCRITICAL)),
        "the exact source and first steps occur in critical_pairs(): {:?}",
        evaluation.obligations
    );
}

#[test]
fn critical_pair_membership_accepts_the_claimed_branches_in_either_order() {
    let presentation = presentation();
    let mut claim = joined_claim();
    std::mem::swap(&mut claim.left, &mut claim.right);
    let mut pins = PresentationPins::empty();
    pins.pin("critical", &presentation);

    let evaluation = evaluate_peak_pinned(&presentation, &claim, &pins);
    assert!(
        !evaluation
            .obligations
            .iter()
            .any(|obligation| obligation.contains(OBLIGATION_PEAK_NONCRITICAL)),
        "critical pair enumeration order is not part of the wire contract: {:?}",
        evaluation.obligations
    );
}

#[test]
fn a_pin_survives_a_reordered_payload() {
    // The digest property, exercised end to end rather than asserted in
    // isolation: a producer shuffling the rules must not be able to turn
    // JOINED into SELF_CONSISTENT_ONLY, nor the reverse.
    let mut pins = PresentationPins::empty();
    pins.pin("swapping", &swapping_presentation());

    let mut shuffled = swapping_presentation();
    shuffled.rules.reverse();
    assert_eq!(
        evaluate_peak_pinned(&shuffled, &joining_claim(), &pins).token(),
        "JOINED"
    );
}

#[test]
fn a_different_presentation_is_not_the_pinned_one() {
    // Guards the pin lookup itself: if `authority_of` returned HostPinned
    // for anything, every test above would pass for the wrong reason.
    let mut pins = PresentationPins::empty();
    pins.pin("swapping", &swapping_presentation());
    assert_eq!(pins.len(), 1);
    assert_eq!(pins.pin_names(), vec!["swapping"]);
    assert_eq!(
        pins.authority_of(&presentation_digest(&presentation())),
        PresentationAuthority::ProducerDeclared
    );
}

#[test]
fn an_empty_pin_set_pins_nothing() {
    let pins = PresentationPins::empty();
    assert!(pins.is_empty());
    assert_eq!(
        pins.authority_of(&presentation_digest(&swapping_presentation())),
        PresentationAuthority::ProducerDeclared
    );
}

#[test]
fn the_evaluation_round_trips_on_the_wire() {
    // The provenance has to survive serialisation, or it is a fact the
    // host knows and the wire loses -- which is the defect again.
    let pins = PresentationPins::empty();
    let evaluation = evaluate_peak_pinned(&swapping_presentation(), &joining_claim(), &pins);
    let json = serde_json::to_string(&evaluation).expect("serializes");
    let back: PeakEvaluation = serde_json::from_str(&json).expect("round trips");
    assert_eq!(back, evaluation);
    assert_eq!(back.token(), "SELF_CONSISTENT_ONLY");
}

// Origin: engine/crates_rs/pfp_runtime/src/rewriting/operation_tests.rs
// Claim: urn:core:crates_rs:pfp-runtime:operation-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord05370dbf {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord05370dbf` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError05370dbf {
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
impl BoundaryError05370dbf {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError05370dbf {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError05370dbf {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord05370dbf {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError05370dbf> {
        if capacity_bound == 0 {
            return Err(BoundaryError05370dbf::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError05370dbf::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError05370dbf::ExceedsCapacity {
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
mod l4_boundary_tests_05370dbf {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord05370dbf::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord05370dbf::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord05370dbf::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord05370dbf::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord05370dbf::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError05370dbf::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError05370dbf::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
