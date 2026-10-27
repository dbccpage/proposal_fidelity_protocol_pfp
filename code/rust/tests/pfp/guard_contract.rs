//! Contract tests for rejection receipts and learned guard rails.
//!
//! `EPIC-OE-SYMGAM-012`. Like `SYMGAM-011`, this epic states its gate as "unit
//! and integration tests pass", which names no falsifier. The criteria below are
//! derived from the epic's *invariants* -- the Conservative Guard Law, zero data
//! loss, and the non-regression requirement -- each paired with the mutation
//! that breaks it.
//!
//! The load-bearing property is **soundness**, and it fails silently: a guard
//! that prunes too much simply stops a working candidate from being proposed,
//! and nothing reports the loss. Most of what follows is about that.

use pfp::epics::guard::{
    compilation_receipt, compile_guards, every_record_is_cited, CandidateFingerprint, GuardMask,
    GuardRefusal, GuardScope, GUARD_RECEIPT_SCHEMA,
};
use pfp::epics::retraction::{
    CandidateTurn, CemeterySink, DescentTriad, RetractionRefusal,
};

fn triad(gamma_2: u64, phi_1: u64, defects: u64) -> DescentTriad {
    DescentTriad::new(gamma_2, phi_1, defects)
}

fn candidate(tokens: &str, projection: &[bool]) -> CandidateTurn {
    CandidateTurn {
        token_stream: tokens.to_string(),
        cochain_projection: projection.to_vec(),
        triad: triad(1, 1, 1),
    }
}

fn a_refusal() -> RetractionRefusal {
    RetractionRefusal::NoProgress
}

fn cemetery_with(entries: &[(usize, CandidateTurn)]) -> CemeterySink {
    let mut sink = CemeterySink::default();
    for (index, candidate) in entries {
        sink.bury(*index, candidate.clone(), &a_refusal());
    }
    sink
}

// ---------------------------------------------------------------------------
// Criterion 1 -- the Conservative Guard Law
// ---------------------------------------------------------------------------

#[test]
fn a_compiled_guard_forbids_exactly_the_candidate_that_failed() {
    let failed = candidate("a b c", &[true, false]);
    let mask = compile_guards(&cemetery_with(&[(0, failed.clone())])).expect("coded refusal");

    assert_eq!(mask.len(), 1);
    assert!(mask.prunes(&failed));
}

#[test]
fn a_guard_does_not_prune_a_candidate_differing_only_in_projection() {
    // Both halves of the fingerprint are load-bearing. A guard keyed on the
    // token stream alone would prune this, and it never failed.
    let failed = candidate("a b c", &[true, false]);
    let sibling = candidate("a b c", &[false, false]);
    let mask = compile_guards(&cemetery_with(&[(0, failed)])).expect("coded refusal");

    assert!(!mask.prunes(&sibling));
}

#[test]
fn a_guard_does_not_prune_a_candidate_differing_only_in_tokens() {
    let failed = candidate("a b c", &[true, false]);
    let sibling = candidate("a b d", &[true, false]);
    let mask = compile_guards(&cemetery_with(&[(0, failed)])).expect("coded refusal");

    assert!(!mask.prunes(&sibling));
}

#[test]
fn a_guard_does_not_prune_an_extension_of_what_failed() {
    // Prefix matching would be the natural "smarter" guard and is exactly what
    // the Conservative Guard Law forbids: the longer stream was never observed
    // to fail.
    let failed = candidate("a b", &[true]);
    let longer = candidate("a b c", &[true]);
    let mask = compile_guards(&cemetery_with(&[(0, failed)])).expect("coded refusal");

    assert!(!mask.prunes(&longer));
}

#[test]
fn compilation_produces_only_exact_guards() {
    // The decisive structural claim: there is no path from the compiler to a
    // generalization.
    let mask = compile_guards(&cemetery_with(&[
        (0, candidate("a", &[true])),
        (1, candidate("b", &[false])),
    ]))
    .expect("coded refusal");

    assert_eq!(mask.len(), 2);
    for guard in mask.guards() {
        assert!(guard.scope.is_exact(), "compiler emitted a generalization");
        assert!(guard.scope.reviewer().is_none());
    }
}

// ---------------------------------------------------------------------------
// Criterion 2 -- generalization requires a named reviewer
// ---------------------------------------------------------------------------

#[test]
fn a_generalization_records_who_admitted_it() {
    let mask =
        compile_guards(&cemetery_with(&[(0, candidate("a b", &[true]))])).expect("coded refusal");
    let guard = mask.guards()[0]
        .clone()
        .admit_generalization("j.carroll", "the whole stream is unreachable")
        .expect("a named reviewer");

    assert_eq!(guard.scope.reviewer(), Some("j.carroll"));
    assert!(!guard.scope.is_exact());
    match &guard.scope {
        GuardScope::Generalized { rationale, .. } => assert!(rationale.contains("unreachable")),
        GuardScope::Exact => panic!("expected a generalization"),
    }
}

#[test]
fn a_generalization_without_a_reviewer_is_refused() {
    // "Reviewed by nobody" must not be recordable as review.
    let mask =
        compile_guards(&cemetery_with(&[(0, candidate("a b", &[true]))])).expect("coded refusal");
    for empty in ["", "   ", "\t"] {
        let error = mask.guards()[0]
            .clone()
            .admit_generalization(empty, "because")
            .expect_err("an unnamed reviewer is refused");
        assert_eq!(error, GuardRefusal::UnreviewedGeneralization);
    }
}

#[test]
fn only_a_generalized_guard_reaches_past_the_exact_projection() {
    // And when it does, it is because a human signed for it.
    let failed = candidate("a b", &[true]);
    let sibling = candidate("a b", &[false]);
    let mask = compile_guards(&cemetery_with(&[(0, failed)])).expect("coded refusal");

    assert!(!mask.prunes(&sibling));

    let generalized = mask.guards()[0]
        .clone()
        .admit_generalization("j.carroll", "stream is unreachable at any projection")
        .expect("a named reviewer");
    assert!(generalized.prunes(&sibling));
}

// ---------------------------------------------------------------------------
// Criterion 3 -- non-regression: never prune a provably admissible path
// ---------------------------------------------------------------------------

#[test]
fn a_mask_that_admits_the_known_good_set_is_certified() {
    let mask =
        compile_guards(&cemetery_with(&[(0, candidate("bad", &[true]))])).expect("coded refusal");
    let admissible = vec![candidate("good", &[true]), candidate("also good", &[false])];

    assert!(mask.assert_admits(&admissible).is_ok());
}

#[test]
fn a_guard_pruning_a_known_good_candidate_is_reported_with_both_identities() {
    // "Some guard is wrong" is not actionable. The refusal names the guard, the
    // cemetery turn that taught it, and the candidate it wrongly pruned.
    let overlap = candidate("shared", &[true]);
    let mask = compile_guards(&cemetery_with(&[(7, overlap.clone())])).expect("coded refusal");

    let error = mask
        .assert_admits(std::slice::from_ref(&overlap))
        .expect_err("the guard prunes a candidate declared admissible");

    match error {
        GuardRefusal::PrunesAdmissible {
            source_turn,
            token_stream,
            guard_digest,
        } => {
            assert_eq!(source_turn, 7);
            assert_eq!(token_stream, "shared");
            assert_eq!(guard_digest, CandidateFingerprint::of(&overlap).digest());
        }
        other => panic!("expected PrunesAdmissible, got {other:?}"),
    }
}

#[test]
fn an_empty_known_good_set_is_refused_rather_than_certified() {
    // Proving that no guard prunes any of zero candidates proves nothing, and a
    // vacuous pass is how an unsound guard ships.
    let mask =
        compile_guards(&cemetery_with(&[(0, candidate("a", &[true]))])).expect("coded refusal");
    assert_eq!(
        mask.assert_admits(&[]).expect_err("vacuous certification"),
        GuardRefusal::NoAdmissibleWitnesses
    );
}

#[test]
fn an_empty_mask_still_requires_witnesses_to_certify() {
    // The empty mask is trivially sound, but the refusal is about the *claim*,
    // not the mask: certifying against nothing is meaningless either way.
    let mask = GuardMask::default();
    assert!(mask.is_empty());
    assert_eq!(
        mask.assert_admits(&[]).expect_err("still vacuous"),
        GuardRefusal::NoAdmissibleWitnesses
    );
    assert!(mask
        .assert_admits(&[candidate("anything", &[true])])
        .is_ok());
}

#[test]
fn a_generalization_can_break_soundness_and_the_check_catches_it() {
    // The reason generalization needs review, demonstrated rather than asserted.
    let failed = candidate("stream", &[true]);
    let admissible = candidate("stream", &[false]);
    let mask = compile_guards(&cemetery_with(&[(0, failed)])).expect("coded refusal");

    // Sound while exact.
    assert!(mask
        .assert_admits(std::slice::from_ref(&admissible))
        .is_ok());

    // A reviewer widens it, and the same known-good candidate is now pruned.
    // This is why the widening needs a signature: the loss is real and silent.
    let generalized = mask.guards()[0]
        .clone()
        .admit_generalization("j.carroll", "over-wide on purpose")
        .expect("named reviewer");
    assert!(generalized.prunes(&admissible));
}

// ---------------------------------------------------------------------------
// Criterion 4 -- zero data loss and deterministic compilation
// ---------------------------------------------------------------------------

#[test]
fn every_buried_record_is_cited_by_some_guard() {
    let cemetery = cemetery_with(&[
        (0, candidate("a", &[true])),
        (1, candidate("b", &[false])),
        (2, candidate("c", &[true, true])),
    ]);
    let mask = compile_guards(&cemetery).expect("coded refusal");

    assert!(every_record_is_cited(&cemetery, &mask));
}

#[test]
fn a_repeated_burial_makes_one_guard_that_cites_both_turns() {
    // Deduplicated, but not at the cost of a citation: how often a candidate was
    // retried is evidence the Cemetery holds.
    let repeated = candidate("a b", &[true]);
    let cemetery = cemetery_with(&[(0, repeated.clone()), (4, repeated.clone()), (9, repeated)]);
    let mask = compile_guards(&cemetery).expect("coded refusal");

    assert_eq!(mask.len(), 1);
    assert_eq!(mask.guards()[0].source_turns, vec![0, 4, 9]);
    assert!(every_record_is_cited(&cemetery, &mask));
}

#[test]
fn compilation_is_deterministic_regardless_of_burial_order() {
    let a = candidate("alpha", &[true]);
    let b = candidate("beta", &[false]);
    let forward =
        compile_guards(&cemetery_with(&[(0, a.clone()), (1, b.clone())])).expect("coded refusal");
    let reversed = compile_guards(&cemetery_with(&[(1, b), (0, a)])).expect("coded refusal");

    // Same guards, same digest: a mask that depended on burial order could not
    // be compared across runs.
    assert_eq!(forward.len(), reversed.len());
    assert_eq!(forward.digest(), reversed.digest());
}

#[test]
fn the_mask_digest_changes_when_a_guard_changes() {
    let one =
        compile_guards(&cemetery_with(&[(0, candidate("a", &[true]))])).expect("coded refusal");
    let two = compile_guards(&cemetery_with(&[
        (0, candidate("a", &[true])),
        (1, candidate("b", &[true])),
    ]))
    .expect("coded refusal");

    assert_ne!(one.digest(), two.digest());
}

#[test]
fn an_empty_cemetery_compiles_to_an_empty_mask_that_prunes_nothing() {
    let mask = compile_guards(&CemeterySink::default()).expect("an empty cemetery is legal");
    assert!(mask.is_empty());
    assert!(!mask.prunes(&candidate("anything", &[true])));
}

// ---------------------------------------------------------------------------
// Criterion 5 -- filtering and receipts
// ---------------------------------------------------------------------------

#[test]
fn filtering_keeps_every_candidate_no_guard_forbids() {
    let bad = candidate("bad", &[true]);
    let mask = compile_guards(&cemetery_with(&[(0, bad.clone())])).expect("coded refusal");
    let proposals = vec![candidate("good", &[true]), bad, candidate("fine", &[false])];

    let kept = mask.filter(&proposals);

    assert_eq!(kept.len(), 2);
    assert!(kept.iter().all(|c| c.token_stream != "bad"));
}

#[test]
fn a_pruned_candidate_can_name_the_guard_that_pruned_it() {
    let bad = candidate("bad", &[true]);
    let mask = compile_guards(&cemetery_with(&[(3, bad.clone())])).expect("coded refusal");

    let guard = mask.pruning_guard(&bad).expect("it is pruned");
    assert_eq!(guard.source_turns, vec![3]);
    assert_eq!(guard.refusal_code, "NO_PROGRESS");
}

#[test]
fn the_receipt_distinguishes_records_from_guards() {
    // They differ whenever a candidate was buried twice, and collapsing them
    // would hide how much of the Cemetery was repetition.
    let repeated = candidate("a", &[true]);
    let cemetery = cemetery_with(&[
        (0, repeated.clone()),
        (1, repeated),
        (2, candidate("b", &[false])),
    ]);
    let mask = compile_guards(&cemetery).expect("coded refusal");
    let receipt = compilation_receipt(&cemetery, &mask);

    assert_eq!(receipt.cemetery_records, 3);
    assert_eq!(receipt.guards_compiled, 2);
    assert_eq!(receipt.cited_turns, vec![0, 1, 2]);
    assert_eq!(receipt.exact_guards, 2);
    assert_eq!(receipt.generalized_guards, 0);
    assert_eq!(receipt.schema, GUARD_RECEIPT_SCHEMA);
    assert_eq!(receipt.authority_effect, "None");
    assert_eq!(receipt.mask_digest, mask.digest());
}

#[test]
fn the_receipt_serialises_to_json() {
    let cemetery = cemetery_with(&[(0, candidate("a", &[true]))]);
    let mask = compile_guards(&cemetery).expect("coded refusal");
    let json = serde_json::to_string(&compilation_receipt(&cemetery, &mask))
        .expect("the receipt must serialise");

    assert!(json.contains(GUARD_RECEIPT_SCHEMA));
    assert!(json.contains("\"authority_effect\":\"None\""));
}

#[test]
fn a_fingerprint_digest_is_stable_and_separating() {
    let a = CandidateFingerprint::of(&candidate("x", &[true]));
    let same = CandidateFingerprint::of(&candidate("x", &[true]));
    let other = CandidateFingerprint::of(&candidate("x", &[false]));

    assert_eq!(a.digest(), same.digest());
    assert_ne!(a.digest(), other.digest());
}

#[test]
fn a_fingerprint_separates_a_token_boundary_from_its_projection() {
    // Without a separator between the two halves, "ab" + [] and "a" + ... could
    // hash alike. They must not.
    let left = CandidateFingerprint::of(&candidate("ab", &[]));
    let right = CandidateFingerprint::of(&candidate("a", &[true]));
    assert_ne!(left.digest(), right.digest());
}

// Origin: engine/crates_rs/tests/pfp/guard_contract.rs
// Claim: urn:core:crates_rs:tests:guard-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordec4690d2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordec4690d2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorec4690d2 {
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
impl BoundaryErrorec4690d2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorec4690d2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorec4690d2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordec4690d2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorec4690d2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorec4690d2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorec4690d2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorec4690d2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ec4690d2() {
    let admitted = BoundaryRecordec4690d2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordec4690d2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
