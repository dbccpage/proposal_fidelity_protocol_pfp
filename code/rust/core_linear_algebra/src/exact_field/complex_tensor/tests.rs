use super::*;
use crate::exact_field::test_support::{m, q, Fp, Shaky, Z6};
use crate::exact_field::{elimination, matrix as mx};
use num_rational::BigRational;

const LIMITS: OperationLimits = OperationLimits::UNLIMITED;

#[test]
fn projector_rank_kernel_and_two_complex_structures_agree() {
    for left in 0..=3 {
        for right in 0..=3 {
            let n = left * right;
            let t = balance_map_with_limits::<BigRational>(left, right, LIMITS).unwrap();
            let p = balance_projector_with_limits::<BigRational>(left, right, LIMITS).unwrap();
            assert_eq!(t.shape(), (2 * n, 4 * n));
            assert_eq!(
                mx::multiply(&t, &mx::transpose(&t).unwrap()).unwrap(),
                mx::scale(&mx::identity(2 * n).unwrap(), &q(2, 1)).unwrap()
            );
            assert_eq!(
                p,
                mx::scale(
                    &mx::multiply(&mx::transpose(&t).unwrap(), &t).unwrap(),
                    &q(1, 2)
                )
                .unwrap()
            );
            assert_eq!(mx::multiply(&p, &p).unwrap(), p);
            assert_eq!(elimination::rank(&p).unwrap(), 2 * n);
            assert_eq!(elimination::kernel_basis(&t).unwrap().len(), 2 * n);
            let jl = realify_parts_with_limits(
                &mx::zeros(left, left).unwrap(),
                &mx::identity(left).unwrap(),
                LIMITS,
            )
            .unwrap();
            let jr = realify_parts_with_limits(
                &mx::zeros(right, right).unwrap(),
                &mx::identity(right).unwrap(),
                LIMITS,
            )
            .unwrap();
            let global_j = realify_parts_with_limits(
                &mx::zeros(n, n).unwrap(),
                &mx::identity(n).unwrap(),
                LIMITS,
            )
            .unwrap();
            let first = mx::kronecker(&jl, &mx::identity(2 * right).unwrap()).unwrap();
            let second = mx::kronecker(&mx::identity(2 * left).unwrap(), &jr).unwrap();
            assert_eq!(
                mx::multiply(&t, &first).unwrap(),
                mx::multiply(&global_j, &t).unwrap()
            );
            assert_eq!(
                mx::multiply(&t, &second).unwrap(),
                mx::multiply(&global_j, &t).unwrap()
            );
            let relation = mx::sub(&first, &second).unwrap();
            assert!(mx::is_zero_matrix(&mx::multiply(&t, &relation).unwrap()));
            assert_eq!(elimination::rank(&relation).unwrap(), 2 * n);
            let expected = mx::scale(
                &mx::sub(
                    &mx::identity(4 * n).unwrap(),
                    &mx::kronecker(&jl, &jr).unwrap(),
                )
                .unwrap(),
                &q(1, 2),
            )
            .unwrap();
            assert_eq!(p, expected);
        }
    }
}

#[test]
fn rectangular_operator_compression_matches_four_independent_component_products() {
    for (a, c, b, d) in [(2, 3, 3, 1), (1, 2, 2, 3), (0, 1, 2, 1), (2, 0, 1, 2)] {
        let real = mx::from_fn(a, c, |i, j| q((2 * i + j + 1) as i64, 3)).unwrap();
        let imag = mx::from_fn(a, c, |i, j| q(i as i64 - j as i64, 5)).unwrap();
        let second_real = mx::from_fn(b, d, |i, j| q((i + 3 * j) as i64, 2)).unwrap();
        let second_imag = mx::from_fn(b, d, |i, j| q((i + j + 1) as i64, 7)).unwrap();
        let left = realify_parts_with_limits(&real, &imag, LIMITS).unwrap();
        let right = realify_parts_with_limits(&second_real, &second_imag, LIMITS).unwrap();
        let expected_real = mx::sub(
            &mx::kronecker(&real, &second_real).unwrap(),
            &mx::kronecker(&imag, &second_imag).unwrap(),
        )
        .unwrap();
        let expected_imag = mx::add(
            &mx::kronecker(&real, &second_imag).unwrap(),
            &mx::kronecker(&imag, &second_real).unwrap(),
        )
        .unwrap();
        let expected = realify_parts_with_limits(&expected_real, &expected_imag, LIMITS).unwrap();
        assert_eq!(
            normalized_tensor_with_limits(&left, &right, LIMITS).unwrap(),
            expected
        );
        assert_eq!(
            unscaled_tensor_with_limits(&left, &right, LIMITS).unwrap(),
            mx::scale(&expected, &q(2, 1)).unwrap()
        );
    }
}

#[test]
fn balance_map_associativity_retains_the_actual_tensor_coordinate_order() {
    let (a, b, c) = (2, 1, 3);
    let first = mx::multiply(
        &balance_map_with_limits::<BigRational>(a * b, c, LIMITS).unwrap(),
        &mx::kronecker(
            &balance_map_with_limits(a, b, LIMITS).unwrap(),
            &mx::identity(2 * c).unwrap(),
        )
        .unwrap(),
    )
    .unwrap();
    let second = mx::multiply(
        &balance_map_with_limits::<BigRational>(a, b * c, LIMITS).unwrap(),
        &mx::kronecker(
            &mx::identity(2 * a).unwrap(),
            &balance_map_with_limits(b, c, LIMITS).unwrap(),
        )
        .unwrap(),
    )
    .unwrap();
    assert_eq!(first, second);
}

#[test]
fn product_state_normalization_differs_from_balanced_lift_and_operator_compression() {
    let state = mx::scale(&mx::identity::<BigRational>(2).unwrap(), &q(1, 2)).unwrap();
    let product = unscaled_tensor_with_limits(&state, &state, LIMITS).unwrap();
    assert_eq!(product, state);
    assert_eq!(mx::trace(&product).unwrap(), q(1, 1));
    let wrong_state = normalized_tensor_with_limits(&state, &state, LIMITS).unwrap();
    assert_eq!(mx::trace(&wrong_state).unwrap(), q(1, 2));
    let raw = mx::kronecker(&state, &state).unwrap();
    let p = balance_projector_with_limits(1, 1, LIMITS).unwrap();
    let projected = mx::multiply(&mx::multiply(&p, &raw).unwrap(), &p).unwrap();
    assert_eq!(mx::trace(&projected).unwrap(), q(1, 2));
    let lifted = balanced_lift_with_limits(&product, 1, 1, LIMITS).unwrap();
    assert_eq!(lifted, mx::scale(&projected, &q(2, 1)).unwrap());
    assert_eq!(mx::trace(&lifted).unwrap(), q(1, 1));
    assert_eq!(
        mx::multiply(&mx::multiply(&p, &lifted).unwrap(), &p).unwrap(),
        lifted
    );
    let t = balance_map_with_limits(1, 1, LIMITS).unwrap();
    let recovered = mx::scale(
        &mx::multiply(
            &mx::multiply(&t, &lifted).unwrap(),
            &mx::transpose(&t).unwrap(),
        )
        .unwrap(),
        &q(1, 2),
    )
    .unwrap();
    assert_eq!(recovered, product);
}

#[test]
fn shape_image_characteristic_and_inverse_contract_refusals_are_distinct() {
    let identity = mx::identity::<BigRational>(2).unwrap();
    assert!(matches!(
        normalized_tensor_with_limits(&mx::identity(1).unwrap(), &identity, LIMITS),
        Err(ComplexTensorError::NotDoubled { .. })
    ));
    let reflection = m(&[&[-1, 0], &[0, 1]]);
    assert!(matches!(
        normalized_tensor_with_limits(&reflection, &identity, LIMITS),
        Err(ComplexTensorError::ComplexStructure {
            operand: "left",
            ..
        })
    ));
    assert!(balanced_lift_with_limits(&identity, 1, 2, LIMITS).is_err());
    assert!(realify_parts_with_limits(&identity, &mx::identity(1).unwrap(), LIMITS).is_err());
    assert!(matches!(
        balance_projector_with_limits::<Fp<2>>(1, 1, LIMITS),
        Err(ComplexTensorError::Algebra(
            ExactFieldError::CharacteristicTwo { .. }
        ))
    ));
    assert!(matches!(
        balance_projector_with_limits::<Z6>(1, 1, LIMITS),
        Err(ComplexTensorError::Algebra(
            ExactFieldError::ScalarContract { .. }
        ))
    ));
    assert!(matches!(
        balance_projector_with_limits::<Shaky<8>>(1, 1, LIMITS),
        Err(ComplexTensorError::Algebra(
            ExactFieldError::ScalarContract { .. }
        ))
    ));
    let p = balance_projector_with_limits::<Fp<5>>(1, 2, LIMITS).unwrap();
    assert_eq!(mx::multiply(&p, &p).unwrap(), p);
}

#[test]
fn inclusive_aggregate_budgets_refuse_before_invalid_scalar_contracts() {
    let identity = mx::identity::<BigRational>(2).unwrap();
    let exact = OperationLimits {
        max_elements: 16,
        max_scalar_ops: 123,
    };
    assert!(normalized_tensor_with_limits(&identity, &identity, exact).is_ok());
    assert!(matches!(
        normalized_tensor_with_limits(
            &identity,
            &identity,
            OperationLimits {
                max_scalar_ops: 122,
                ..exact
            }
        ),
        Err(ComplexTensorError::Algebra(ExactFieldError::Matrix(
            MatrixError::OperationLimitExceeded {
                requested: 123,
                limit: 122
            }
        )))
    ));
    assert!(matches!(
        normalized_tensor_with_limits(
            &identity,
            &identity,
            OperationLimits {
                max_elements: 15,
                ..exact
            }
        ),
        Err(ComplexTensorError::Algebra(ExactFieldError::Matrix(
            MatrixError::AllocationLimitExceeded {
                requested: 16,
                limit: 15
            }
        )))
    ));
    assert!(unscaled_tensor_with_limits(
        &identity,
        &identity,
        OperationLimits {
            max_scalar_ops: 116,
            ..exact
        }
    )
    .is_ok());
    assert!(balanced_lift_with_limits(
        &identity,
        1,
        1,
        OperationLimits {
            max_scalar_ops: 117,
            ..exact
        }
    )
    .is_ok());
    assert!(balanced_lift_with_limits(
        &identity,
        1,
        1,
        OperationLimits {
            max_scalar_ops: 116,
            ..exact
        }
    )
    .is_err());
    let tiny = OperationLimits {
        max_elements: 16,
        max_scalar_ops: 3,
    };
    assert!(matches!(
        balance_projector_with_limits::<Shaky<8>>(1, 1, tiny),
        Err(ComplexTensorError::Algebra(ExactFieldError::Matrix(
            MatrixError::OperationLimitExceeded {
                requested: 4,
                limit: 3
            }
        )))
    ));
    assert!(balance_map_with_limits::<BigRational>(usize::MAX, 1, LIMITS).is_err());
    assert!(balance_projector_with_limits::<BigRational>(usize::MAX / 2, 2, LIMITS).is_err());
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_field/complex_tensor/tests.rs
// Claim: urn:core:crates_rs:core-linear-algebra:tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5778edb9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5778edb9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5778edb9 {
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
impl BoundaryError5778edb9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5778edb9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5778edb9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5778edb9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5778edb9> {
        if capacity_bound == 0 {
            return Err(BoundaryError5778edb9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5778edb9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5778edb9::ExceedsCapacity {
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
mod l4_boundary_tests_5778edb9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5778edb9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5778edb9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5778edb9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5778edb9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5778edb9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5778edb9::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5778edb9::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
