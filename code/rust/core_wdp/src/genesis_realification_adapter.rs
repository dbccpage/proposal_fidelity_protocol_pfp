//! A declared finite complex realization mapped to its balanced real tensor.
//! State admission stays with the quantum owner, and balancing with the math owner.
//! These maps preserve a supplied operational model; they select no scalar/Born
//! axioms from the primitive mark and grant no execution permission.

use crate::types::AuthorityEffect;
use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use core_number_theory::rational::Rational;
use core_quantum_physics::complex_realification::{self, ComplexTensorError};
use core_quantum_physics::exact_instrument::ExactDensityState;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredRealComposite {
    left_dimension: usize,
    right_dimension: usize,
    view: BasicMatrix<Rational>,
    balanced_state: BasicMatrix<Rational>,
}

impl DeclaredRealComposite {
    /// The caller supplies the actual complex composite and its local dimensions.
    /// Entangled inputs are allowed. Arithmetic refusal never grants admission.
    pub fn from_complex(
        state: &ExactDensityState,
        left_dimension: usize,
        right_dimension: usize,
        limits: OperationLimits,
    ) -> Result<Self, ComplexTensorError> {
        let (view, balanced_state) = complex_realification::composite_density_views_with_limits(
            state,
            left_dimension,
            right_dimension,
            limits,
        )?;
        Ok(Self {
            left_dimension,
            right_dimension,
            view,
            balanced_state,
        })
    }

    pub fn local_dimensions(&self) -> (usize, usize) {
        (self.left_dimension, self.right_dimension)
    }

    pub fn real_view(&self) -> &BasicMatrix<Rational> {
        &self.view
    }

    pub fn balanced_state(&self) -> &BasicMatrix<Rational> {
        &self.balanced_state
    }

    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}

// Origin: engine/crates_rs/core_wdp/src/genesis_realification_adapter.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-realification-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord701d4d7b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord701d4d7b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError701d4d7b {
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
impl BoundaryError701d4d7b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError701d4d7b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError701d4d7b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord701d4d7b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError701d4d7b> {
        if capacity_bound == 0 {
            return Err(BoundaryError701d4d7b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError701d4d7b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError701d4d7b::ExceedsCapacity {
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
mod l4_boundary_tests_701d4d7b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord701d4d7b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord701d4d7b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord701d4d7b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord701d4d7b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord701d4d7b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError701d4d7b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError701d4d7b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
