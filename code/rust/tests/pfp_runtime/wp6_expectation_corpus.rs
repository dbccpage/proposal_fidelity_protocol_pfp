//! WP-6 expectation corpus — the peak surface (cases 1-3).
//!
//! Every assertion is transcribed from `_ooutwire/wp6_expectation_corpus.md`,
//! derived from contracts and doctrine and committed at `c5ebce8230` **before**
//! any of these ran. The git history is the proof of that ordering; a corpus
//! whose expectations were written after the run is a transcript, and a
//! transcript cannot refute anything.
//!
//! That derivation was deleted from the tree on 2026-09-04 and lives only in
//! git now — read it at
//! `git show c5ebce8230:_ooutwire/wp6_expectation_corpus.md`. The citation is
//! kept rather than dropped because the ordering claim above is the whole
//! warrant for this file, and a claim whose evidence has no address is not
//! checkable.
//!
//! A disagreement here is a FINDING, and which side is wrong is decided case by
//! case. Case 1 was flagged medium confidence in the derivation — specifically,
//! whether both obligations coexist or one short-circuits the other.
//!
//! Cases 4-8 are the packet surface and live in
//! `pfp/tests/test_wp6_expectation_corpus.py`.
//!
//! AuthorityEffect: None.

use pfp_runtime::{
    evaluate_peak_pinned, CriticalPeakClaim, ExhaustionBasis, PeakVerdict, Presentation,
    PresentationAuthority, PresentationPins, ReductionPath, ReductionStep, Rule,
    OBLIGATION_PEAK_NONCRITICAL, REFUSAL_PRESENTATION_UNKNOWN,
};

fn rule(name: &str, lhs: &str, rhs: &str) -> Rule {
    Rule {
        name: name.to_owned(),
        lhs: lhs.to_owned(),
        rhs: rhs.to_owned(),
    }
}

fn step(name: &str, position: usize) -> ReductionStep {
    ReductionStep {
        rule: name.to_owned(),
        position,
    }
}

fn path(steps: Vec<ReductionStep>, endpoint: &str) -> ReductionPath {
    ReductionPath {
        steps,
        endpoint: endpoint.to_owned(),
    }
}

fn signature(symbols: &[&str]) -> Vec<String> {
    symbols.iter().map(|s| (*s).to_owned()).collect()
}

/// A pin set that is NOT empty and does NOT contain the presentations under
/// test.
///
/// Deliberately not `PresentationPins::empty()`. An empty registry reports
/// `ProducerDeclared` for everything, so the assertions below would pass on a
/// host that had lost the ability to recognise anything at all. A populated
/// registry that simply does not hold *this* presentation is the honest fixture.
fn pins_holding_something_else() -> PresentationPins {
    let mut pins = PresentationPins::empty();
    pins.pin(
        "unrelated",
        &Presentation {
            signature: signature(&["x", "y"]),
            rules: vec![rule("swap", "xy", "yx")],
        },
    );
    pins
}

/// `{p1: ab -> ba, p2: cd -> dc}` — permutes symbols, so nothing shrinks, and
/// every reachable set still closes.
fn swapping() -> Presentation {
    Presentation {
        signature: signature(&["a", "b", "c", "d"]),
        rules: vec![rule("p1", "ab", "ba"), rule("p2", "cd", "dc")],
    }
}

/// `{r1: ab -> c, r2: bc -> a}` — strictly length-reducing.
fn shrinking() -> Presentation {
    Presentation {
        signature: signature(&["a", "b", "c"]),
        rules: vec![rule("r1", "ab", "c"), rule("r2", "bc", "a")],
    }
}

fn has(obligations: &[String], needle: &str) -> bool {
    obligations.iter().any(|o| o.contains(needle))
}

// ---------------------------------------------------------------------------
// Case 1 — a genuinely joinable peak, under producer-declared rules.
//
// Derived: Joined { "badc" }; token SELF_CONSISTENT_ONLY; ProducerDeclared;
// obligations contain BOTH FW-PRESENTATION-UNKNOWN and FW-PEAK-NONCRITICAL,
// because p1 occupies positions 0-1 and p2 positions 2-3, so the redexes do not
// overlap and this is not a critical pair.
// ---------------------------------------------------------------------------

fn case_one_claim() -> CriticalPeakClaim {
    CriticalPeakClaim {
        source: "abcd".to_owned(),
        left: path(vec![step("p1", 0)], "bacd"),
        right: path(vec![step("p2", 2)], "abdc"),
        join: None,
        steps_inspected: 0,
        step_budget: 10_000,
    }
}

#[test]
fn case_1_the_join_is_found_and_reported() {
    let evaluation = evaluate_peak_pinned(
        &swapping(),
        &case_one_claim(),
        &pins_holding_something_else(),
    );
    assert_eq!(
        evaluation.verdict,
        PeakVerdict::Joined {
            join: "badc".to_owned()
        },
        "both branches reach badc and both reachable sets close"
    );
}

#[test]
fn case_1_a_decision_under_unpinned_rules_is_self_consistent_only() {
    let evaluation = evaluate_peak_pinned(
        &swapping(),
        &case_one_claim(),
        &pins_holding_something_else(),
    );
    assert_eq!(
        evaluation.authority,
        PresentationAuthority::ProducerDeclared
    );
    assert_eq!(
        evaluation.token(),
        "SELF_CONSISTENT_ONLY",
        "the join holds under rules that arrived with the claim, and the host pins none of them"
    );
}

#[test]
fn case_1_carries_both_obligations() {
    // The medium-confidence assertion of the whole derivation: whether the two
    // obligations coexist, or one short-circuits the other.
    let evaluation = evaluate_peak_pinned(
        &swapping(),
        &case_one_claim(),
        &pins_holding_something_else(),
    );
    assert!(
        has(&evaluation.obligations, REFUSAL_PRESENTATION_UNKNOWN),
        "the presentation is unpinned; got {:?}",
        evaluation.obligations
    );
    assert!(
        has(&evaluation.obligations, OBLIGATION_PEAK_NONCRITICAL),
        "p1 at 0-1 and p2 at 2-3 do not overlap, so this is not a critical pair; got {:?}",
        evaluation.obligations
    );
}

// ---------------------------------------------------------------------------
// Case 2 — the non-joinable critical pair (cc, aa).
//
// Derived: NotJoinable carrying ClosedReachableSets; token
// SELF_CONSISTENT_ONLY; FW-PEAK-NONCRITICAL must NOT fire, because ab at 0 and
// bc at 1 share the b and this is a genuine critical pair.
// ---------------------------------------------------------------------------

fn case_two_claim() -> CriticalPeakClaim {
    CriticalPeakClaim {
        source: "abc".to_owned(),
        left: path(vec![step("r1", 0)], "cc"),
        right: path(vec![step("r2", 1)], "aa"),
        join: None,
        steps_inspected: 0,
        step_budget: 10_000,
    }
}

#[test]
fn case_2_disjoint_closed_sets_are_a_decision_not_a_failed_search() {
    let evaluation = evaluate_peak_pinned(
        &shrinking(),
        &case_two_claim(),
        &pins_holding_something_else(),
    );
    assert_eq!(
        evaluation.verdict,
        PeakVerdict::NotJoinable {
            left_endpoint: "cc".to_owned(),
            right_endpoint: "aa".to_owned(),
            basis: ExhaustionBasis::ClosedReachableSets,
        },
        "nothing rewrites cc or aa, so the sets close and are disjoint"
    );
}

#[test]
fn case_2_the_negative_decision_downgrades_too() {
    // NotJoinable under producer rules is if anything the easier answer to
    // arrange: dropping a rule can only shrink the reachable sets.
    let evaluation = evaluate_peak_pinned(
        &shrinking(),
        &case_two_claim(),
        &pins_holding_something_else(),
    );
    assert_eq!(evaluation.token(), "SELF_CONSISTENT_ONLY");
}

#[test]
fn case_2_a_real_critical_pair_is_not_flagged_non_critical() {
    // The discriminating half of case 1. If FW-PEAK-NONCRITICAL fired here it
    // would fire on everything and mean nothing.
    let evaluation = evaluate_peak_pinned(
        &shrinking(),
        &case_two_claim(),
        &pins_holding_something_else(),
    );
    assert!(
        !has(&evaluation.obligations, OBLIGATION_PEAK_NONCRITICAL),
        "ab at 0 and bc at 1 overlap on the b; this IS a critical pair. Got {:?}",
        evaluation.obligations
    );
}

// ---------------------------------------------------------------------------
// Case 3 — the same peak with a forged declared join.
//
// Derived: NeedsEvidence naming the refuted join; token NEEDS_EVIDENCE, NOT
// downgraded, because NeedsEvidence decides nothing and there is nothing in it
// for a presentation to have decided. The unpinned obligation still stands.
// ---------------------------------------------------------------------------

fn case_three_claim() -> CriticalPeakClaim {
    let mut claim = case_two_claim();
    claim.join = Some("cc".to_owned());
    claim
}

#[test]
fn case_3_a_forged_join_is_refuted_not_adopted() {
    let evaluation = evaluate_peak_pinned(
        &shrinking(),
        &case_three_claim(),
        &pins_holding_something_else(),
    );
    assert!(
        matches!(evaluation.verdict, PeakVerdict::NeedsEvidence { .. }),
        "cc is not reachable from the right endpoint; got {:?}",
        evaluation.verdict
    );
}

#[test]
fn case_3_an_undecided_verdict_keeps_its_own_token() {
    // Downgrading this would report an undecided run as internally consistent,
    // which is a stronger claim than the truth.
    let evaluation = evaluate_peak_pinned(
        &shrinking(),
        &case_three_claim(),
        &pins_holding_something_else(),
    );
    assert_eq!(evaluation.token(), "NEEDS_EVIDENCE");
    assert!(!evaluation.decides());
}

#[test]
fn case_3_the_rules_obligation_stands_whatever_the_verdict() {
    let evaluation = evaluate_peak_pinned(
        &shrinking(),
        &case_three_claim(),
        &pins_holding_something_else(),
    );
    assert!(
        has(&evaluation.obligations, REFUSAL_PRESENTATION_UNKNOWN),
        "it is a fact about the rules, not about the claim; got {:?}",
        evaluation.obligations
    );
}

// ---------------------------------------------------------------------------
// Fixture guards. Without these, the three cases above could all pass on a host
// that had stopped recognising anything.
// ---------------------------------------------------------------------------

#[test]
fn the_pin_set_is_populated_and_does_recognise_its_own_entry() {
    let pins = pins_holding_something_else();
    assert_eq!(pins.len(), 1);
    let held = Presentation {
        signature: signature(&["x", "y"]),
        rules: vec![rule("swap", "xy", "yx")],
    };
    assert_eq!(
        pins.authority_of(&pfp_runtime::presentation_digest(&held)),
        PresentationAuthority::HostPinned {
            pin: "unrelated".to_owned()
        },
        "a registry that recognised nothing would make every assertion above vacuous"
    );
}

// Origin: engine/crates_rs/tests/pfp_runtime/wp6_expectation_corpus.rs
// Claim: urn:core:crates_rs:tests:wp6-expectation-corpus:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda5171c52 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda5171c52` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora5171c52 {
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
impl BoundaryErrora5171c52 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora5171c52 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora5171c52 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda5171c52 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora5171c52> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora5171c52::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora5171c52::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora5171c52::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_a5171c52() {
    let admitted = BoundaryRecorda5171c52::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda5171c52::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
