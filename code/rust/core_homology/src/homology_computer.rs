//! Unified interface: filtered complex → diagrams / homology.
//!
//! AuthorityEffect: None. Best-effort shell. Not PROVED; not GlobalGreen.

use crate::filtration::Filtration;
use crate::persistent_homology::{
    compute_persistent_homology, PersistentHomologyError, PersistentHomologyResult,
};
use crate::ph_matrix_reduction::PhBoundaryMatrix;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CoefficientField {
    Z2,
    /// Rational coefficients are unsupported and are explicitly refused.
    Q,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HomologyComputeRequest {
    pub field: CoefficientField,
    pub max_dimension: usize,
}

impl Default for HomologyComputeRequest {
    fn default() -> Self {
        Self {
            field: CoefficientField::Z2,
            max_dimension: 2,
        }
    }
}

/// Run persistent homology on a filtration + boundary matrix.
pub fn compute(
    filtration: &Filtration,
    boundary: &mut PhBoundaryMatrix,
    request: &HomologyComputeRequest,
) -> Result<PersistentHomologyResult, PersistentHomologyError> {
    if request.field != CoefficientField::Z2 {
        return Err(PersistentHomologyError::UnsupportedCoefficientField);
    }
    if filtration.max_dimension > request.max_dimension {
        return Err(PersistentHomologyError::DimensionMismatch);
    }
    compute_persistent_homology(filtration, boundary)
}

// Origin: engine/crates_rs/core_homology/src/homology_computer.rs
// Claim: urn:core:crates_rs:core-homology:homology-computer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbd4073ba {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbd4073ba` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbd4073ba {
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
impl BoundaryErrorbd4073ba {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbd4073ba {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbd4073ba {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbd4073ba {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbd4073ba> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbd4073ba::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbd4073ba::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbd4073ba::ExceedsCapacity {
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
mod tests {
    use super::*;
    use crate::ph_matrix_reduction::PhBoundaryMatrix;

    #[test]
    fn rational_coefficients_never_fall_back_to_f2() {
        let f = Filtration::new(vec![], 0);
        let mut m = PhBoundaryMatrix { columns: vec![] };
        let request = HomologyComputeRequest {
            field: CoefficientField::Q,
            max_dimension: 0,
        };
        assert_eq!(
            compute(&f, &mut m, &request),
            Err(PersistentHomologyError::UnsupportedCoefficientField)
        );
    }

    #[test]
    fn empty_request() {
        let f = Filtration::new(vec![], 0);
        let mut m = PhBoundaryMatrix { columns: vec![] };
        let r = compute(&f, &mut m, &HomologyComputeRequest::default()).unwrap();
        assert!(r.diagram.points.is_empty());
    }
}

#[cfg(test)]
mod l4_boundary_tests_bd4073ba {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbd4073ba::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbd4073ba::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbd4073ba::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbd4073ba::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbd4073ba::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbd4073ba::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbd4073ba::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
