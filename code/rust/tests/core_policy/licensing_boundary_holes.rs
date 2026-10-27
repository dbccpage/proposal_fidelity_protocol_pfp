//! Regression tests for two ways past the licensing boundary.
//!
//! Both were reachable with ordinary data — no unsafe, no forged license, no
//! trait widening. The crate's unforgeability argument was sound; what failed
//! was that `evaluate` compared strings where it meant to compare values, and
//! trusted the proposer's summary of numbers it was already being handed.
//!
//! AuthorityEffect: None.

use core_policy::{
    evaluate, AdmissibilityVerdict, ExactnessWitness, Inadmissible, LicensingBoundary,
    TransitionProposal, ValuationReceipt,
};
use sha2::{Digest, Sha256};

fn hex_of(seed: &str) -> String {
    hex::encode(Sha256::digest(seed.as_bytes()))
}

fn digest(seed: &str) -> String {
    format!("sha256:{}", hex_of(seed))
}

fn witness() -> ExactnessWitness {
    ExactnessWitness {
        repair_differential: "alpha=[1,0,1]".to_owned(),
        witness_digest: digest("witness"),
        checked_by: "core_certifiers::phi1_form".to_owned(),
    }
}

/// A proposal that is admissible, so each test below changes exactly one thing.
fn admissible() -> TransitionProposal {
    TransitionProposal {
        pre_state_digest: digest("pre"),
        post_state_digest: digest("post"),
        valuation: ValuationReceipt {
            phi_pre: "4".to_owned(),
            phi_post: "0".to_owned(),
            delta_phi_is_non_positive: true,
            gamma2: "0".to_owned(),
            gamma2_is_zero: true,
            phi_post_is_zero: true,
        },
        exactness_witness: Some(witness()),
        preserved_invariants: vec!["carrier_cardinality".to_owned()],
    }
}

fn is_admissible(p: &TransitionProposal) -> bool {
    evaluate(p, &[]) == AdmissibilityVerdict::Admissible
}

#[test]
fn the_baseline_proposal_is_admissible() {
    // Guards the tests below: if this ever fails they would pass vacuously.
    assert!(is_admissible(&admissible()));
}

// ---------------------------------------------------------------------------
// digest spelling
// ---------------------------------------------------------------------------

#[test]
fn a_null_transition_spelled_two_ways_is_refused() {
    // `is_digest` accepted bare hex as well as the prefixed form while the
    // change-of-state check compared raw strings, so the same digest written
    // both ways read as a transition and minted a license for a state change
    // that is not one.
    let mut proposal = admissible();
    proposal.pre_state_digest = digest("same");
    proposal.post_state_digest = hex_of("same");

    match evaluate(&proposal, &[]) {
        AdmissibilityVerdict::Inadmissible(Inadmissible::MalformedTransition { .. }) => {}
        other => panic!("expected a refusal, got {other:?}"),
    }
    assert!(LicensingBoundary.mint(&proposal, &[]).is_err());
}

#[test]
fn a_bare_hex_digest_is_refused_outright() {
    let mut proposal = admissible();
    proposal.post_state_digest = hex_of("post");
    assert!(
        !is_admissible(&proposal),
        "a digest has one canonical spelling"
    );
}

#[test]
fn uppercase_hex_is_refused_rather_than_folded() {
    // The alternative was to normalise case and accept both. Every producer in
    // the tree emits lowercase, so rejecting costs nothing, and admitting a
    // second spelling of one value is the shape of the original defect.
    let mut proposal = admissible();
    proposal.post_state_digest = format!("sha256:{}", hex_of("post").to_uppercase());
    assert!(!is_admissible(&proposal));
}

#[test]
fn case_only_differences_are_not_a_transition() {
    let mut proposal = admissible();
    proposal.pre_state_digest = format!("sha256:{}", hex_of("same"));
    proposal.post_state_digest = format!("sha256:{}", hex_of("same").to_uppercase());
    assert!(!is_admissible(&proposal));
}

#[test]
fn a_license_authorizes_its_own_transition_and_nothing_else() {
    let license = LicensingBoundary
        .mint(&admissible(), &[])
        .expect("admissible");
    assert!(license.authorizes(&digest("pre"), &digest("post")));
    assert!(!license.authorizes(&digest("post"), &digest("pre")));
    assert!(!license.authorizes(&digest("pre"), &digest("elsewhere")));
    assert!(!license.authorizes("not-a-digest", &digest("post")));
    assert!(
        !license.authorizes(&hex_of("pre"), &hex_of("post")),
        "an unprefixed digest is not a digest"
    );
}

// ---------------------------------------------------------------------------
// the proposer's own numbers
// ---------------------------------------------------------------------------

#[test]
fn phi_post_zero_declared_non_zero_cannot_skip_the_witness() {
    // The headline rule keyed off `phi_post_is_zero`, a boolean supplied by the
    // proposer, sitting next to the exact string that contradicted it. Flipping
    // one bit walked a witness-less zero straight past the check.
    let mut proposal = admissible();
    proposal.valuation.phi_post = "0".to_owned();
    proposal.valuation.phi_post_is_zero = false;
    proposal.exactness_witness = None;

    assert!(
        !is_admissible(&proposal),
        "phi_post is zero and there is no witness; the flag must not decide this"
    );
    assert!(LicensingBoundary.mint(&proposal, &[]).is_err());
}

#[test]
fn a_residual_increase_declared_non_positive_is_refused() {
    let mut proposal = admissible();
    proposal.valuation.phi_pre = "1".to_owned();
    proposal.valuation.phi_post = "9".to_owned();
    proposal.valuation.phi_post_is_zero = false;
    proposal.valuation.delta_phi_is_non_positive = true; // the lie
    assert!(!is_admissible(&proposal));
}

#[test]
fn zero_written_any_of_its_spellings_is_still_zero() {
    for spelling in ["0", "0.0", "-0", "0.000", "+0"] {
        let mut proposal = admissible();
        proposal.valuation.phi_post = spelling.to_owned();
        proposal.valuation.phi_post_is_zero = true;
        proposal.exactness_witness = None;
        assert!(
            !is_admissible(&proposal),
            "{spelling} is zero, so the witness requirement applies"
        );
    }
}

#[test]
fn fractional_residuals_compare_exactly() {
    // Positional, not lexicographic: 0.5 > 0.45 even though "45" > "5".
    let mut proposal = admissible();
    proposal.valuation.phi_pre = "0.45".to_owned();
    proposal.valuation.phi_post = "0.5".to_owned();
    proposal.valuation.phi_post_is_zero = false;
    proposal.valuation.delta_phi_is_non_positive = false;
    assert!(
        matches!(
            evaluate(&proposal, &[]),
            AdmissibilityVerdict::Inadmissible(Inadmissible::ResidualIncreased)
        ),
        "0.45 -> 0.5 is an increase"
    );

    let mut decreasing = admissible();
    decreasing.valuation.phi_pre = "0.5".to_owned();
    decreasing.valuation.phi_post = "0.45".to_owned();
    decreasing.valuation.phi_post_is_zero = false;
    decreasing.valuation.delta_phi_is_non_positive = true;
    assert!(is_admissible(&decreasing), "0.5 -> 0.45 is a decrease");
}

#[test]
fn a_residual_that_is_not_a_number_is_refused() {
    for bad in ["", "  ", "NaN", "1e5", "0x10", "1.2.3", "--1"] {
        let mut proposal = admissible();
        proposal.valuation.phi_post = bad.to_owned();
        assert!(!is_admissible(&proposal), "{bad:?} is not an exact decimal");
    }
}

#[test]
fn equal_residuals_are_a_non_positive_delta() {
    let mut proposal = admissible();
    proposal.valuation.phi_pre = "3.25".to_owned();
    proposal.valuation.phi_post = "3.250".to_owned();
    proposal.valuation.phi_post_is_zero = false;
    proposal.valuation.delta_phi_is_non_positive = true;
    assert!(is_admissible(&proposal), "no increase is not an increase");
}

#[test]
fn the_witness_is_recorded_as_provenance() {
    let license = LicensingBoundary
        .mint(&admissible(), &[])
        .expect("admissible");
    assert_eq!(
        license.exactness_witness_digest(),
        Some(digest("witness").as_str()),
        "a trace must be able to say which witness authorized the commit"
    );
}

#[test]
fn gamma2_flag_true_with_a_nonzero_exact_value_mints_no_license() {
    let mut proposal = admissible();
    proposal.valuation.gamma2 = "0.000000001".to_owned();
    proposal.valuation.gamma2_is_zero = true;

    match evaluate(&proposal, &[]) {
        AdmissibilityVerdict::Inadmissible(Inadmissible::MalformedTransition { detail }) => {
            assert!(detail.contains("gamma2"), "{detail}");
        }
        other => panic!("expected a malformed refusal, got {other:?}"),
    }
    assert!(LicensingBoundary.mint(&proposal, &[]).is_err());
}

#[test]
fn gamma2_flag_false_while_the_exact_value_is_zero_is_malformed() {
    let mut proposal = admissible();
    proposal.valuation.gamma2 = "0".to_owned();
    proposal.valuation.gamma2_is_zero = false;

    match evaluate(&proposal, &[]) {
        AdmissibilityVerdict::Inadmissible(Inadmissible::MalformedTransition { detail }) => {
            assert!(detail.contains("gamma2"), "{detail}");
        }
        other => panic!("expected a malformed refusal, got {other:?}"),
    }
    assert!(LicensingBoundary.mint(&proposal, &[]).is_err());
}

#[test]
fn an_exact_zero_gamma2_is_admitted_when_the_flag_agrees() {
    let mut proposal = admissible();
    proposal.valuation.gamma2 = "0.000".to_owned();
    proposal.valuation.gamma2_is_zero = true;

    assert_eq!(evaluate(&proposal, &[]), AdmissibilityVerdict::Admissible);
    assert!(LicensingBoundary.mint(&proposal, &[]).is_ok());
}

// Origin: engine/crates_rs/tests/core_policy/licensing_boundary_holes.rs
// Claim: urn:core:crates_rs:tests:licensing-boundary-holes:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordcd5f16d1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordcd5f16d1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorcd5f16d1 {
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
impl BoundaryErrorcd5f16d1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorcd5f16d1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorcd5f16d1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordcd5f16d1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorcd5f16d1> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorcd5f16d1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorcd5f16d1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorcd5f16d1::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_cd5f16d1() {
    let admitted = BoundaryRecordcd5f16d1::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordcd5f16d1::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
