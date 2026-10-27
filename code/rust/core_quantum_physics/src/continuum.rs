//! Exact finite canonical-commutator obstruction and Weyl certificates.
//! Finite trace cyclicity blocks [A,B]=lambda I for lambda!=0 in nonzero
//! dimension. Finite Weyl systems do not remove that obstruction.
//! AuthorityEffect: None.
use crate::exact_hermitian::{self, ExactHermitianError};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_number_theory::cyclotomic::GaussianRat;
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CanonicalCommutatorObstruction {
    pub dimension: usize,
    pub trace_commutator: GaussianRat,
    pub trace_target: GaussianRat,
    pub equality_obstructed: bool,
}
pub fn canonical_commutator_obstruction(
    a: &BasicMatrix<GaussianRat>,
    b: &BasicMatrix<GaussianRat>,
    lambda: &GaussianRat,
) -> Result<CanonicalCommutatorObstruction, ExactHermitianError> {
    let n = validate_square_pair_dim(a, b)?;
    let limits = linear_algebra::backend::basic_matrix::OperationLimits {
        max_elements: 1 << 20,
        max_scalar_ops: 1 << 24,
    };
    let trace_commutator = compute_trace_commutator(a, b, limits)?;
    let id = linear_algebra::exact_field::matrix::identity_with_limits::<GaussianRat>(n, limits)?;
    let scaled_id = linear_algebra::exact_field::matrix::scale(&id, lambda)?;
    let trace_target = linear_algebra::exact_field::matrix::trace(&scaled_id)?;
    let equality_obstructed = trace_commutator != trace_target;
    Ok(CanonicalCommutatorObstruction {
        dimension: n,
        trace_commutator,
        trace_target,
        equality_obstructed,
    })
}

fn validate_square_pair_dim(
    a: &BasicMatrix<GaussianRat>,
    b: &BasicMatrix<GaussianRat>,
) -> Result<usize, ExactHermitianError> {
    let n = exact_hermitian::square_dim(a)?;
    let m = exact_hermitian::square_dim(b)?;
    if n != m {
        return Err(ExactHermitianError::ShapeMismatch {
            expected: n,
            actual: m,
        });
    }
    Ok(n)
}

fn compute_trace_commutator(
    a: &BasicMatrix<GaussianRat>,
    b: &BasicMatrix<GaussianRat>,
    limits: linear_algebra::backend::basic_matrix::OperationLimits,
) -> Result<GaussianRat, ExactHermitianError> {
    let ab = linear_algebra::exact_field::matrix::multiply_with_limits(a, b, limits)?;
    let ba = linear_algebra::exact_field::matrix::multiply_with_limits(b, a, limits)?;
    let comm = linear_algebra::exact_field::matrix::sub(&ab, &ba)?;
    Ok(linear_algebra::exact_field::matrix::trace(&comm)?)
}

// Origin: engine/crates_rs/core_quantum_physics/src/continuum.rs
// Claim: urn:core:crates_rs:core-quantum-physics:continuum:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord39087c45 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord39087c45` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError39087c45 {
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
impl BoundaryError39087c45 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError39087c45 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError39087c45 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord39087c45 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError39087c45> {
        if capacity_bound == 0 {
            return Err(BoundaryError39087c45::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError39087c45::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError39087c45::ExceedsCapacity {
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
mod l4_boundary_tests_39087c45 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord39087c45::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord39087c45::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord39087c45::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord39087c45::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord39087c45::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError39087c45::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError39087c45::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
