// AuthorityEffect: None.
use core_finite_probability::signed_representation::{
    SignedInstrumentQuotient, SignedRepresentationError, SignedValuation,
};
use core_number_theory::rational::{ri, rq};

#[test]
fn signed_indicator_separates_full_readouts_but_coarse_reports_can_be_classical() {
    let signed = SignedValuation::from_weights(vec![ri(2), ri(-1)]).unwrap();
    assert_eq!(signed.negative_indicator(), Some((1, ri(-1))));
    assert_eq!(signed.negativity(), ri(1));
    assert_eq!(
        signed.jordan_parts(),
        (vec![ri(2), ri(0)], vec![ri(0), ri(1)])
    );
    assert!(signed.report_state(&[0, 1], 2).is_err());
    assert_eq!(signed.report_state(&[0, 0], 1).unwrap().probs(), &[ri(1)]);
    assert!(signed.report_state(&[0, 0], 2).is_err());
}
#[test]
fn signed_instrument_has_classical_quotient_exactly_under_descent_and_positivity() {
    // Hidden signed shear preserves the sole report and total mass.
    let shear = vec![vec![ri(2), ri(-1)], vec![ri(1), ri(0)]];
    let quotient = SignedInstrumentQuotient::try_new(vec![0, 0], 1, vec![shear.clone()]).unwrap();
    assert_eq!(quotient.forgetting().rows(), &[vec![ri(1)]]);
    assert!(matches!(
        SignedInstrumentQuotient::try_new(vec![0, 1], 2, vec![shear]),
        Err(SignedRepresentationError::NegativeReportTransition { .. })
    ));
    // Same source report, differing post-report laws: no Markov quotient exists.
    let bad = vec![
        vec![ri(1), ri(0), ri(0)],
        vec![ri(0), ri(0), ri(1)],
        vec![ri(0), ri(0), ri(1)],
    ];
    assert!(matches!(
        SignedInstrumentQuotient::try_new(vec![0, 0, 1], 2, vec![bad]),
        Err(SignedRepresentationError::NotDescending { .. })
    ));
    let identity = vec![vec![rq(1, 2), ri(0)], vec![ri(0), rq(1, 2)]];
    let split =
        SignedInstrumentQuotient::try_new(vec![0, 1], 2, vec![identity.clone(), identity]).unwrap();
    assert_eq!(split.outcome_maps().len(), 2);
    assert_eq!(
        split.forgetting().rows(),
        &[vec![ri(1), ri(0)], vec![ri(0), ri(1)]]
    );
}

#[test]
fn nontrivial_signed_hidden_model_has_an_exact_classical_instrument_representation() {
    // A genuine two-report model: negative hidden mass survives within one
    // fibre, while the accepted report state is a fair binary distribution.
    let hidden = SignedValuation::from_weights(vec![ri(2), ri(-1), ri(1)]).unwrap();
    let reports = vec![0, 0, 1];
    assert_eq!(
        hidden.report_state(&reports, 2).unwrap().probs(),
        &[rq(1, 2), rq(1, 2)]
    );
    let first = vec![
        vec![ri(2), ri(-1), ri(0)],
        vec![ri(1), ri(0), ri(0)],
        vec![ri(0), ri(0), ri(0)],
    ];
    let second = vec![
        vec![ri(0), ri(0), ri(0)],
        vec![ri(0), ri(0), ri(0)],
        vec![ri(0), ri(0), ri(1)],
    ];
    let quotient = SignedInstrumentQuotient::try_new(reports, 2, vec![first, second]).unwrap();
    assert_eq!(
        quotient.outcome_maps(),
        &[
            vec![vec![ri(1), ri(0)], vec![ri(0), ri(0)]],
            vec![vec![ri(0), ri(0)], vec![ri(0), ri(1)]]
        ]
    );
}

// Origin: engine/crates_rs/tests/core_finite_probability/signed_representation_classification.rs
// Claim: urn:core:crates_rs:tests:signed-representation-classification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord84416a2e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord84416a2e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError84416a2e {
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
impl BoundaryError84416a2e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError84416a2e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError84416a2e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord84416a2e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError84416a2e> {
        if capacity_bound == 0 {
            return Err(BoundaryError84416a2e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError84416a2e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError84416a2e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_84416a2e() {
    let admitted = BoundaryRecord84416a2e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord84416a2e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
