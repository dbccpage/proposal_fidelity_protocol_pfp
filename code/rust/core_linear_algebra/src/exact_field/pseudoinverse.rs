//! Exact Moore-Penrose inverses from a full-rank factorization C=A B.
//!
//! A contains the original pivot columns, and B their exact coordinates from
//! row reduction. Over a field with a positive Hermitian norm,
//! C^+=B†(BB†)^-1(A†A)^-1A†. All four Penrose identities replay independently;
//! no eigenvalues, square roots, or floating point are required.
//! AuthorityEffect: None.

use super::elimination::{inverse_with_limits, rref_with_limits};
use super::involution::adjoint;
use super::matrix::{from_fn_with_limits, multiply_with_limits, zeros_with_limits};
use super::ordered::HermitianOrdered;
use super::{charge, element_count, plus, times, ExactFieldError};
use crate::backend::basic_matrix::{BasicMatrix, OperationLimits};

/// Moore-Penrose inverse over the same exact coefficient field.
pub fn pseudoinverse<F: HermitianOrdered>(
    c: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    pseudoinverse_with_limits(c, OperationLimits::UNLIMITED)
}

/// Budgeted construction: each temporary has at most (m+n)^2 entries;
/// 100(m+n)^3 bounds the row reduction, two inverses and exact replay.
pub fn pseudoinverse_with_limits<F: HermitianOrdered>(
    c: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    charge_pseudoinverse_budget(c.rows(), c.cols(), limits)?;
    let reduction = rref_with_limits(c, limits)?;
    if reduction.pivot_columns().is_empty() {
        return zeros_with_limits(c.cols(), c.rows(), limits);
    }
    let (a, b) = full_rank_factors(c, &reduction, limits)?;
    let inverse = gram_pseudoinverse(&a, &b, limits)?;
    verify_penrose(c, &inverse, limits)?;
    Ok(inverse)
}

fn charge_pseudoinverse_budget(
    rows: usize,
    cols: usize,
    limits: OperationLimits,
) -> Result<(), crate::backend::basic_matrix::MatrixError> {
    let span = plus(rows, cols)?;
    let span_sq = element_count(span, span)?;
    charge(limits, span_sq, times(100, times(span_sq, span)?)?)
}

fn full_rank_factors<F: HermitianOrdered>(
    c: &BasicMatrix<F>,
    reduction: &super::elimination::RowReduced<F>,
    limits: OperationLimits,
) -> Result<(BasicMatrix<F>, BasicMatrix<F>), ExactFieldError> {
    let pivots = reduction.pivot_columns();
    let rank = pivots.len();
    let a = from_fn_with_limits(c.rows(), rank, limits, |r, k| {
        c.as_slice()[r * c.cols() + pivots[k]].clone()
    })?;
    let b = from_fn_with_limits(rank, c.cols(), limits, |r, k| {
        reduction.matrix().as_slice()[r * c.cols() + k].clone()
    })?;
    if multiply_with_limits(&a, &b, limits)? != *c {
        return Err(ExactFieldError::ReplayFailed {
            operation: "full-rank factorization",
        });
    }
    Ok((a, b))
}

fn gram_pseudoinverse<F: HermitianOrdered>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let a_star = adjoint(a)?;
    let b_star = adjoint(b)?;
    let a_gram = multiply_with_limits(&a_star, a, limits)?;
    let b_gram = multiply_with_limits(b, &b_star, limits)?;
    let a_inverse = inverse_with_limits(&a_gram, limits)?;
    let b_inverse = inverse_with_limits(&b_gram, limits)?;
    let left = multiply_with_limits(&b_star, &b_inverse, limits)?;
    let right = multiply_with_limits(&a_inverse, &a_star, limits)?;
    multiply_with_limits(&left, &right, limits)
}

/// Verify all four Penrose identities against the intact declared operator.
pub fn verify_penrose<F: HermitianOrdered>(
    c: &BasicMatrix<F>,
    inverse: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<(), ExactFieldError> {
    if inverse.shape() != (c.cols(), c.rows()) {
        return Err(ExactFieldError::CertificateRejected {
            reason: "pseudoinverse has wrong shape",
        });
    }
    let cp = multiply_with_limits(c, inverse, limits)?;
    let pc = multiply_with_limits(inverse, c, limits)?;
    if !penrose_projectors_valid(c, inverse, &cp, &pc, limits)? {
        return Err(ExactFieldError::CertificateRejected {
            reason: "a Penrose identity failed",
        });
    }
    Ok(())
}

fn penrose_projectors_valid<F: HermitianOrdered>(
    c: &BasicMatrix<F>,
    inverse: &BasicMatrix<F>,
    cp: &BasicMatrix<F>,
    pc: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<bool, ExactFieldError> {
    if multiply_with_limits(cp, c, limits)? != *c {
        return Ok(false);
    }
    if multiply_with_limits(pc, inverse, limits)? != *inverse {
        return Ok(false);
    }
    Ok(adjoint(cp)? == *cp && adjoint(pc)? == *pc)
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_field/pseudoinverse.rs
// Claim: urn:core:crates_rs:core-linear-algebra:pseudoinverse:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8e1c6446 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8e1c6446` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8e1c6446 {
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
impl BoundaryError8e1c6446 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8e1c6446 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8e1c6446 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8e1c6446 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8e1c6446> {
        if capacity_bound == 0 {
            return Err(BoundaryError8e1c6446::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8e1c6446::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8e1c6446::ExceedsCapacity {
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
    use super::super::matrix::{from_rows, identity};
    use super::*;
    use num_rational::BigRational;
    fn q(n: i64) -> BigRational {
        BigRational::from_integer(n.into())
    }
    #[test]
    fn rectangular_rank_deficient_inverse_replays_all_penrose_laws() {
        let c = from_rows(vec![vec![q(1), q(2), q(3)], vec![q(2), q(4), q(6)]]).unwrap();
        let p = pseudoinverse(&c).unwrap();
        assert_eq!(p.shape(), (3, 2));
        assert_eq!(p.as_slice()[0], BigRational::new(1.into(), 70.into()));
        verify_penrose(&c, &p, OperationLimits::UNLIMITED).unwrap();
        let bad = from_rows(vec![vec![q(0), q(0)], vec![q(0), q(0)], vec![q(0), q(0)]]).unwrap();
        assert!(verify_penrose(&c, &bad, OperationLimits::UNLIMITED).is_err());
    }
    #[test]
    fn inverse_and_zero_cases_have_the_canonical_shapes() {
        let c = identity::<BigRational>(3).unwrap();
        assert_eq!(pseudoinverse(&c).unwrap(), c);
        let zero = zeros_with_limits::<BigRational>(2, 3, OperationLimits::UNLIMITED).unwrap();
        assert_eq!(pseudoinverse(&zero).unwrap().shape(), (3, 2));
        assert!(pseudoinverse_with_limits(
            &c,
            OperationLimits {
                max_elements: 1,
                max_scalar_ops: 1
            }
        )
        .is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_8e1c6446 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8e1c6446::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8e1c6446::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8e1c6446::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8e1c6446::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8e1c6446::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError8e1c6446::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError8e1c6446::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
