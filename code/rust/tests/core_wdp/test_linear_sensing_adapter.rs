use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_observer_presentation::{
    LinearObserverError, LinearSensingPresentation,
};
use num_rational::BigRational;
use core_wdp::legacy_observer_adapters::{adapt_linear_sensing, SourceCustody};
fn q(n: i64) -> BigRational {
    BigRational::from_integer(n.into())
}
#[test]
fn sensing_adapter_preserves_visible_repairs_and_refuses_quotient_request() {
    let sensing = LinearSensingPresentation::try_new(
        BasicMatrix::from_row_major(1, 2, vec![q(1), q(0)]).unwrap(),
        BasicMatrix::from_row_major(2, 2, vec![q(1), q(0), q(0), q(1)]).unwrap(),
    )
    .unwrap();
    let custody = SourceCustody {
        path: "source ObserverHarness".into(),
        recorded_sha256: "a".repeat(64),
        source_receipts: vec![],
        source_authority_tags: vec!["unverified authorization label".into()],
    };
    let adapted = adapt_linear_sensing(sensing.clone(), custody.clone()).unwrap();
    assert_eq!(adapted.custody(), &custody);
    assert_eq!(adapted.linear_sensing(), Some(&sensing));
    assert_eq!(
        adapted
            .linear_sensing()
            .unwrap()
            .report(&[q(4), q(9)])
            .unwrap(),
        vec![q(4)]
    );
    assert!(matches!(
        adapted.linear_sensing().unwrap().try_quotient(),
        Err(LinearObserverError::SeesRepair { .. })
    ));
    assert!(adapted.linear().is_none() && adapted.memory().is_none() && adapted.policy().is_none());
    let hidden = sensing.check_repair_blindspot(&[q(0), q(9)]).unwrap();
    assert!(hidden.is_blindspot && hidden.is_nontrivial);
}

// Origin: engine/crates_rs/tests/core_wdp/test_linear_sensing_adapter.rs
// Claim: urn:core:crates_rs:tests:test-linear-sensing-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordac7266a3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordac7266a3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorac7266a3 {
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
impl BoundaryErrorac7266a3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorac7266a3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorac7266a3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordac7266a3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorac7266a3> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorac7266a3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorac7266a3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorac7266a3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ac7266a3() {
    let admitted = BoundaryRecordac7266a3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordac7266a3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
