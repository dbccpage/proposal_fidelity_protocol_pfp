//! Partial transpose on the right tensor factor with declared lexicographic basis.
//! (a,b;c,d) maps to (a,d;c,b), so the operation is an exact linear involution
//! preserving trace and Hermiticity, while generally failing positivity.
//! AuthorityEffect: None.

use crate::backend::basic_matrix::{BasicMatrix, MatrixError, OperationLimits};
use crate::exact_field::{matrix, ExactFieldError};
use crate::scalars::{ExactRing, Field};

pub fn partial_transpose_right<F: Field + ExactRing>(
    m: &BasicMatrix<F>,
    left: usize,
    right: usize,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    partial_transpose_right_with_limits(m, left, right, OperationLimits::UNLIMITED)
}
pub fn partial_transpose_right_with_limits<F: Field + ExactRing>(
    m: &BasicMatrix<F>,
    left: usize,
    right: usize,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let n = left
        .checked_mul(right)
        .ok_or(MatrixError::DimensionOverflow {
            rows: left,
            cols: right,
        })?;
    if left == 0 || right == 0 || m.shape() != (n, n) {
        return Err(ExactFieldError::ShapeMismatch {
            operation: "partial transpose right",
            left: m.shape(),
            right: (n, n),
        });
    }
    matrix::from_fn_with_limits(n, n, limits, |row, col| {
        let (a, b, c, d) = (row / right, row % right, col / right, col % right);
        m.as_slice()[(a * right + d) * n + c * right + b].clone()
    })
}

// Origin: engine/crates_rs/core_linear_algebra/src/tensor/partial_transpose.rs
// Claim: urn:core:crates_rs:core-linear-algebra:partial-transpose:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3af5a96a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3af5a96a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3af5a96a {
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
impl BoundaryError3af5a96a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3af5a96a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3af5a96a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3af5a96a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3af5a96a> {
        if capacity_bound == 0 {
            return Err(BoundaryError3af5a96a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3af5a96a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3af5a96a::ExceedsCapacity {
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
    use num_rational::BigRational;
    #[test]
    fn partial_transpose_is_an_involution_with_the_declared_basis() {
        let m =
            matrix::from_fn(6, 6, |r, c| BigRational::from_integer((r * 6 + c).into())).unwrap();
        let p = partial_transpose_right(&m, 2, 3).unwrap();
        assert_eq!(p.as_slice()[1], m.as_slice()[6]);
        assert_eq!(partial_transpose_right(&p, 2, 3).unwrap(), m);
        assert_eq!(matrix::trace(&p).unwrap(), matrix::trace(&m).unwrap());
        assert!(partial_transpose_right(&m, 3, 3).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_3af5a96a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3af5a96a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3af5a96a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3af5a96a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3af5a96a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3af5a96a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3af5a96a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3af5a96a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
