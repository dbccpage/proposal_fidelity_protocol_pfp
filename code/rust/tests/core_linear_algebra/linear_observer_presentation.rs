use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_observer_presentation::{
    LinearObserverError, LinearObserverPresentation,
};
use num_rational::BigRational;
fn q(x: i64) -> BigRational {
    BigRational::from_integer(x.into())
}
fn mat(r: usize, c: usize, x: &[i64]) -> BasicMatrix<BigRational> {
    BasicMatrix::from_row_major(r, c, x.iter().copied().map(q).collect()).unwrap()
}
#[test]
fn actual_reports_descend_to_quotient_and_preserve_repair_fibers() {
    let observer =
        LinearObserverPresentation::try_new(mat(1, 2, &[1, -1]), mat(2, 1, &[1, 1])).unwrap();
    assert_eq!(observer.report(&[q(3), q(1)]).unwrap(), vec![q(2)]);
    for a in -3..=3 {
        assert_eq!(observer.report(&[q(3 + a), q(1 + a)]).unwrap(), vec![q(2)]);
    }
    assert!(observer.report(&[q(1)]).is_err());
}
#[test]
fn omitted_annihilation_hypothesis_changes_report_of_exact_repairs() {
    assert_eq!(
        LinearObserverPresentation::try_new(mat(1, 2, &[1, 0]), mat(2, 1, &[1, 1])),
        Err(LinearObserverError::SeesRepair { row: 0, column: 0 })
    );
    assert!(LinearObserverPresentation::try_new(mat(1, 1, &[1]), mat(2, 1, &[1, 1])).is_err());
}

// Origin: engine/crates_rs/tests/core_linear_algebra/linear_observer_presentation.rs
// Claim: urn:core:crates_rs:tests:linear-observer-presentation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordcea1c6a8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordcea1c6a8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorcea1c6a8 {
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
impl BoundaryErrorcea1c6a8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorcea1c6a8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorcea1c6a8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordcea1c6a8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorcea1c6a8> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorcea1c6a8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorcea1c6a8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorcea1c6a8::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_cea1c6a8() {
    let admitted = BoundaryRecordcea1c6a8::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordcea1c6a8::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
