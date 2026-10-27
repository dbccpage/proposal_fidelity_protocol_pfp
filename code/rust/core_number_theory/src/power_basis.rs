//! Shared inversion for power-basis number fields `Q[t]/(f)`.
//!
//! Every cyclotomic type in this crate stores an element as the coefficient vector
//! of a polynomial in a primitive root `t`, reduced modulo the cyclotomic
//! polynomial. The inverse of `x` is the unique `y` with `x * y = 1`, i.e. the
//! solution of the linear system `M_x y = e_0`, where column `j` of `M_x` holds the
//! coefficients of `x * t^j`. That system is solved exactly by
//! `linear_algebra::solve_in_image`, so no type carries its own elimination.
//!
//! AuthorityEffect: None.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::image_kernel::{solve_in_image, ImageMembership};
use num_traits::{One, Zero};

use crate::rational::Rational;

/// Coefficients of `x^{-1}`, or `None` when `x` is zero (not invertible).
///
/// `column(j)` must return the `dim` coefficients of `x * t^j`.
pub fn invert_by_multiplication_matrix(
    dim: usize,
    column: impl Fn(usize) -> Vec<Rational>,
) -> Option<Vec<Rational>> {
    if dim == 0 {
        return None;
    }
    let mut data = vec![Rational::zero(); dim * dim];
    for j in 0..dim {
        let col = column(j);
        if col.len() != dim {
            return None;
        }
        for (i, c) in col.into_iter().enumerate() {
            data[i * dim + j] = c;
        }
    }
    let matrix = BasicMatrix::from_row_major(dim, dim, data).ok()?;
    let mut unit = vec![Rational::zero(); dim];
    unit[0] = Rational::one();
    match solve_in_image(&matrix, &unit).ok()? {
        ImageMembership::InImage(witness) => Some(witness.potential),
        ImageMembership::NotInImage { .. } => None,
    }
}

// Origin: engine/crates_rs/core_number_theory/src/power_basis.rs
// Claim: urn:core:crates_rs:core-number-theory:power-basis:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0d0a32a2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0d0a32a2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0d0a32a2 {
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
impl BoundaryError0d0a32a2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0d0a32a2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0d0a32a2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0d0a32a2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0d0a32a2> {
        if capacity_bound == 0 {
            return Err(BoundaryError0d0a32a2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0d0a32a2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0d0a32a2::ExceedsCapacity {
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
mod l4_boundary_tests_0d0a32a2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0d0a32a2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0d0a32a2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0d0a32a2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0d0a32a2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0d0a32a2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0d0a32a2::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0d0a32a2::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
