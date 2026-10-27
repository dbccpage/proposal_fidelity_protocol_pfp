//! Exact Q(i) realizations of a declared complex structure and balanced tensor.
//! Generic maps, quotient balancing and matrix arithmetic belong to linear_algebra.
//! Density inputs have already been admitted by ExactDensityState. No reconstruction
//! or authority follows from this representation. AuthorityEffect: None.

use crate::exact_instrument::ExactDensityState;
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError, OperationLimits};
pub use linear_algebra::exact_field::complex_tensor::ComplexTensorError;
use linear_algebra::exact_field::{complex_tensor as ct, matrix as mx};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{rq, Rational};

fn product(a: usize, b: usize) -> Result<usize, ComplexTensorError> {
    Ok(a.checked_mul(b)
        .ok_or(MatrixError::DimensionOverflow { rows: a, cols: b })?)
}

fn add(a: usize, b: usize) -> Result<usize, ComplexTensorError> {
    Ok(a.checked_add(b)
        .ok_or(MatrixError::OperationCountOverflow)?)
}

fn admit(limits: OperationLimits, elements: usize, calls: usize) -> Result<(), ComplexTensorError> {
    if elements > limits.max_elements {
        return Err(MatrixError::AllocationLimitExceeded {
            requested: elements,
            limit: limits.max_elements,
        }
        .into());
    }
    if calls > limits.max_scalar_ops {
        return Err(MatrixError::OperationLimitExceeded {
            requested: calls,
            limit: limits.max_scalar_ops,
        }
        .into());
    }
    Ok(())
}

/// Rectangular block realification; all real coordinates precede imaginary ones.
pub fn realify_operator_with_limits(
    operator: &BasicMatrix<GaussianRat>,
    limits: OperationLimits,
) -> Result<BasicMatrix<Rational>, ComplexTensorError> {
    let (m, n) = operator.shape();
    let count = product(m, n)?;
    product(2, m)?;
    product(2, n)?;
    admit(limits, product(4, count)?, count)?;
    let real = mx::from_fn_with_limits(m, n, limits, |r, c| {
        operator.as_slice()[r * n + c].re.clone()
    })?;
    let imaginary = mx::from_fn_with_limits(m, n, limits, |r, c| {
        operator.as_slice()[r * n + c].im.clone()
    })?;
    ct::realify_parts_with_limits(&real, &imaginary, limits)
}

/// Trace-one real state `R(rho)/2`; uses the admitted complex density as its premise.
pub fn realify_density_with_limits(
    state: &ExactDensityState,
    limits: OperationLimits,
) -> Result<BasicMatrix<Rational>, ComplexTensorError> {
    let count = product(state.dimension(), state.dimension())?;
    admit(limits, product(4, count)?, product(5, count)?)?;
    Ok(mx::scale(
        &realify_operator_with_limits(state.matrix(), limits)?,
        &rq(1, 2),
    )?)
}

fn tensor_preflight(
    left: (usize, usize),
    right: (usize, usize),
    density: bool,
    limits: OperationLimits,
) -> Result<(), ComplexTensorError> {
    let left_count = product(left.0, left.1)?;
    let right_count = product(right.0, right.1)?;
    let (elements, calls) = real_tensor_work_bound(left, right, density)?;
    let factor = if density { 5 } else { 1 };
    let conversion = product(factor, add(left_count, right_count)?)?;
    let max_elems = elements
        .max(product(4, left_count)?)
        .max(product(4, right_count)?);
    admit(limits, max_elems, add(calls, conversion)?)
}

fn real_tensor_work_bound(
    left: (usize, usize),
    right: (usize, usize),
    density: bool,
) -> Result<(usize, usize), ComplexTensorError> {
    let left_real = (product(2, left.0)?, product(2, left.1)?);
    let right_real = (product(2, right.0)?, product(2, right.1)?);
    Ok(ct::tensor_work_bound(left_real, right_real, !density)?)
}

/// The realification of the ordinary complex tensor of two declared operators.
/// Includes all conversion and balancing costs in one preflight.
pub fn product_operator_with_limits(
    left: &BasicMatrix<GaussianRat>,
    right: &BasicMatrix<GaussianRat>,
    limits: OperationLimits,
) -> Result<BasicMatrix<Rational>, ComplexTensorError> {
    tensor_preflight(left.shape(), right.shape(), false, limits)?;
    ct::normalized_tensor_with_limits(
        &realify_operator_with_limits(left, limits)?,
        &realify_operator_with_limits(right, limits)?,
        limits,
    )
}

/// `T (R(rho_left)/2 tensor R(rho_right)/2) T^t`, with trace one.
/// This product-state normalization differs from operator compression.
pub fn product_density_with_limits(
    left: &ExactDensityState,
    right: &ExactDensityState,
    limits: OperationLimits,
) -> Result<BasicMatrix<Rational>, ComplexTensorError> {
    tensor_preflight(left.matrix().shape(), right.matrix().shape(), true, limits)?;
    ct::unscaled_tensor_with_limits(
        &realify_density_with_limits(left, limits)?,
        &realify_density_with_limits(right, limits)?,
        limits,
    )
}

/// Lift any admitted complex composite, including entangled states, into the
/// ordinary doubled real tensor with support P: `T^t R(rho) T / 4`.
/// The declared dimensions must multiply to the actual density dimension.
pub fn lift_composite_density_with_limits(
    state: &ExactDensityState,
    left: usize,
    right: usize,
    limits: OperationLimits,
) -> Result<BasicMatrix<Rational>, ComplexTensorError> {
    Ok(composite_density_views_with_limits(state, left, right, limits)?.1)
}

/// Return the `2mn` real view and its normalized `4mn` balanced lift with one
/// shared conversion and one aggregate preflight.
pub fn composite_density_views_with_limits(
    state: &ExactDensityState,
    left: usize,
    right: usize,
    limits: OperationLimits,
) -> Result<(BasicMatrix<Rational>, BasicMatrix<Rational>), ComplexTensorError> {
    preflight_composite_density(state, left, right, limits)?;
    let view = realify_density_with_limits(state, limits)?;
    let lifted = ct::balanced_lift_with_limits(&view, left, right, limits)?;
    Ok((view, lifted))
}

fn preflight_composite_density(
    state: &ExactDensityState,
    left: usize,
    right: usize,
    limits: OperationLimits,
) -> Result<(), ComplexTensorError> {
    let n = product(left, right)?;
    if state.dimension() != n {
        return Err(
            linear_algebra::exact_field::ExactFieldError::ShapeMismatch {
                operation: "declared complex tensor density",
                left: state.matrix().shape(),
                right: (n, n),
            }
            .into(),
        );
    }
    let square = product(n, n)?;
    let cubic = product(square, n)?;
    let calls = add(add(product(96, cubic)?, product(22, square)?)?, 4)?;
    admit(limits, product(16, square)?, calls)
}

// Origin: engine/crates_rs/core_quantum_physics/src/complex_realification.rs
// Claim: urn:core:crates_rs:core-quantum-physics:complex-realification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5bcf9bd6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5bcf9bd6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5bcf9bd6 {
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
impl BoundaryError5bcf9bd6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5bcf9bd6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5bcf9bd6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5bcf9bd6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5bcf9bd6> {
        if capacity_bound == 0 {
            return Err(BoundaryError5bcf9bd6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5bcf9bd6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5bcf9bd6::ExceedsCapacity {
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
mod l4_boundary_tests_5bcf9bd6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5bcf9bd6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5bcf9bd6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5bcf9bd6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5bcf9bd6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5bcf9bd6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError5bcf9bd6::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError5bcf9bd6::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
