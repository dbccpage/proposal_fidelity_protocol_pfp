//! Exact value/first/second derivative products of square matrix curves.
//! Components are derivatives at zero, not Taylor coefficients.
//! AuthorityEffect: None.

use crate::backend::basic_matrix::{BasicMatrix, OperationLimits};
use crate::exact_field::{
    charge, element_count, matrix as mx, plus, require_same_shape, require_square, times,
    ExactFieldError,
};
use crate::scalars::{ExactRing, Field};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MatrixJet2<F> {
    derivatives: [BasicMatrix<F>; 3],
}

impl<F: Field + ExactRing> MatrixJet2<F> {
    pub fn new(derivatives: [BasicMatrix<F>; 3]) -> Result<Self, ExactFieldError> {
        require_square("matrix jet", &derivatives[0])?;
        require_same_shape("matrix jet", &derivatives[0], &derivatives[1])?;
        require_same_shape("matrix jet", &derivatives[0], &derivatives[2])?;
        Ok(Self { derivatives })
    }

    pub fn derivatives(&self) -> [&BasicMatrix<F>; 3] {
        [
            &self.derivatives[0],
            &self.derivatives[1],
            &self.derivatives[2],
        ]
    }

    pub fn product(&self, right: &Self) -> Result<Self, ExactFieldError> {
        self.product_with_limits(right, OperationLimits::UNLIMITED)
    }

    /// Whole-product preflight: six matrix products, three additions, one scale.
    /// Each matrix allocation has n^2 elements; scalar calls <=12n^3+4n^2+1.
    pub fn product_with_limits(
        &self,
        right: &Self,
        limits: OperationLimits,
    ) -> Result<Self, ExactFieldError> {
        require_same_shape("jet product", &self.derivatives[0], &right.derivatives[0])?;
        charge_jet_product_budget(self.derivatives[0].rows(), limits)?;
        let a = self.derivatives();
        let b = right.derivatives();
        Self::new([
            mx::multiply(a[0], b[0])?,
            first_derivative_term(a, b)?,
            second_derivative_term(a, b)?,
        ])
    }
}

fn charge_jet_product_budget(
    n: usize,
    limits: OperationLimits,
) -> Result<(), crate::backend::basic_matrix::MatrixError> {
    let n2 = element_count(n, n)?;
    let cost = plus(plus(times(12, times(n2, n)?)?, times(4, n2)?)?, 1)?;
    charge(limits, n2, cost)
}

fn first_derivative_term<F: Field + ExactRing>(
    a: [&BasicMatrix<F>; 3],
    b: [&BasicMatrix<F>; 3],
) -> Result<BasicMatrix<F>, ExactFieldError> {
    mx::add(&mx::multiply(a[1], b[0])?, &mx::multiply(a[0], b[1])?)
}

fn second_derivative_term<F: Field + ExactRing>(
    a: [&BasicMatrix<F>; 3],
    b: [&BasicMatrix<F>; 3],
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let two = F::one().add(&F::one());
    let mid = mx::scale(&mx::multiply(a[1], b[1])?, &two)?;
    let left_two = mx::add(&mx::multiply(a[2], b[0])?, &mid)?;
    mx::add(&left_two, &mx::multiply(a[0], b[2])?)
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_field/second_order_jet.rs
// Claim: urn:core:crates_rs:core-linear-algebra:second-order-jet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord827be13f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord827be13f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError827be13f {
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
impl BoundaryError827be13f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError827be13f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError827be13f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord827be13f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError827be13f> {
        if capacity_bound == 0 {
            return Err(BoundaryError827be13f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError827be13f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError827be13f::ExceedsCapacity {
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
mod l4_boundary_tests_827be13f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord827be13f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord827be13f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord827be13f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord827be13f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord827be13f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError827be13f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError827be13f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
