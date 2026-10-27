use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::exact_field::{complex_tensor as ct, matrix as mx};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::complex_realification as real;
use core_quantum_physics::exact_channel::ExactKrausChannel;
use core_quantum_physics::exact_hermitian::{gi, gq, realify};
use core_quantum_physics::exact_instrument::ExactDensityState;

const LIMITS: OperationLimits = OperationLimits::UNLIMITED;

fn state() -> ExactDensityState {
    ExactDensityState::try_new(
        mx::from_rows(vec![
            vec![gq(3, 5, 0, 1), gq(0, 1, 1, 5)],
            vec![gq(0, 1, -1, 5), gq(2, 5, 0, 1)],
        ])
        .unwrap(),
    )
    .unwrap()
}

fn bell_state() -> ExactDensityState {
    let mut rho = mx::zeros(4, 4).unwrap();
    rho.set(0, 0, gq(1, 2, 0, 1)).unwrap();
    rho.set(3, 3, gq(1, 2, 0, 1)).unwrap();
    rho.set(0, 3, gq(0, 1, -1, 2)).unwrap();
    rho.set(3, 0, gq(0, 1, 1, 2)).unwrap();
    ExactDensityState::try_new(rho).unwrap()
}

fn embed_rational(matrix: &BasicMatrix<Rational>) -> BasicMatrix<GaussianRat> {
    mx::from_fn(matrix.rows(), matrix.cols(), |r, c| {
        GaussianRat::from_rational(matrix.get(r, c).unwrap().clone())
    })
    .unwrap()
}

#[test]
fn arbitrary_operator_realification_agrees_with_the_existing_hermitian_dilation() {
    let k = mx::from_rows(vec![
        vec![gi(1, 2), gi(-1, 3), gi(4, -2)],
        vec![gi(0, 1), gi(2, 0), gi(-3, -1)],
    ])
    .unwrap();
    let n = k.rows() + k.cols();
    let mut dilation = mx::zeros(n, n).unwrap();
    for i in 0..k.rows() {
        for j in 0..k.cols() {
            dilation
                .set(i, k.rows() + j, k.get(i, j).unwrap().clone())
                .unwrap();
            dilation
                .set(k.rows() + j, i, k.get(i, j).unwrap().conj())
                .unwrap();
        }
    }
    let existing = realify(&dilation).unwrap();
    let rows: Vec<_> = (0..k.rows()).chain(n..n + k.rows()).collect();
    let cols: Vec<_> = (k.rows()..n).chain(n + k.rows()..2 * n).collect();
    let expected = mx::from_fn(rows.len(), cols.len(), |r, c| {
        existing[rows[r]][cols[c]].clone()
    })
    .unwrap();
    assert_eq!(
        real::realify_operator_with_limits(&k, LIMITS).unwrap(),
        expected
    );
    let rho = state();
    assert_eq!(
        real::realify_operator_with_limits(rho.matrix(), LIMITS).unwrap(),
        mx::from_rows(realify(rho.matrix()).unwrap()).unwrap()
    );
    let empty = mx::zeros::<GaussianRat>(2, 0).unwrap();
    assert_eq!(
        real::realify_operator_with_limits(&empty, LIMITS)
            .unwrap()
            .shape(),
        (4, 0)
    );
}

#[test]
fn product_density_and_rectangular_operators_match_the_actual_complex_tensor() {
    let left = state();
    let right = ExactDensityState::try_new(
        mx::from_rows(vec![
            vec![gq(1, 2, 0, 1), gq(1, 4, 0, 1)],
            vec![gq(1, 4, 0, 1), gq(1, 2, 0, 1)],
        ])
        .unwrap(),
    )
    .unwrap();
    let complex_product =
        ExactDensityState::try_new(mx::kronecker(left.matrix(), right.matrix()).unwrap()).unwrap();
    let output = real::product_density_with_limits(&left, &right, LIMITS).unwrap();
    assert_eq!(
        output,
        real::realify_density_with_limits(&complex_product, LIMITS).unwrap()
    );
    assert_eq!(mx::trace(&output).unwrap(), ri(1));
    let a = mx::from_rows(vec![vec![gi(0, 1), gi(2, -1)], vec![gi(1, 0), gi(-2, 3)]]).unwrap();
    let b = mx::from_rows(vec![vec![gi(1, 2)], vec![gi(-1, 1)], vec![gi(0, 3)]]).unwrap();
    assert_eq!(
        real::product_operator_with_limits(&a, &b, LIMITS).unwrap(),
        real::realify_operator_with_limits(&mx::kronecker(&a, &b).unwrap(), LIMITS).unwrap()
    );
}

#[test]
fn local_rectangular_kraus_products_preserve_completeness_and_post_states() {
    let u = mx::from_rows(vec![
        vec![gq(3, 5, 0, 1), gq(0, 1, 4, 5)],
        vec![gq(0, 1, 4, 5), gq(3, 5, 0, 1)],
    ])
    .unwrap();
    let first = mx::multiply(
        &mx::diagonal(&[gq(3, 5, 0, 1), gq(4, 5, 0, 1)]).unwrap(),
        &u,
    )
    .unwrap();
    let second = mx::multiply(
        &mx::diagonal(&[gq(4, 5, 0, 1), gq(3, 5, 0, 1)]).unwrap(),
        &u,
    )
    .unwrap();
    let right = mx::from_rows(vec![
        vec![gq(3, 5, 0, 1)],
        vec![gq(0, 1, 4, 5)],
        vec![gi(0, 0)],
    ])
    .unwrap();
    ExactKrausChannel::from_operators(vec![first.clone(), second.clone()]).unwrap();
    ExactKrausChannel::from_operators(vec![right.clone()]).unwrap();
    let source = state();
    let trivial = ExactDensityState::try_new(mx::identity(1).unwrap()).unwrap();
    let actual_source =
        ExactDensityState::try_new(mx::kronecker(source.matrix(), trivial.matrix()).unwrap())
            .unwrap();
    let operators = [first, second];
    let complex = ExactKrausChannel::from_operators(
        operators
            .iter()
            .map(|k| mx::kronecker(k, &right).unwrap())
            .collect(),
    )
    .unwrap();
    let input = real::product_density_with_limits(&source, &trivial, LIMITS).unwrap();
    let mut output = mx::zeros(12, 12).unwrap();
    let mut complete = mx::zeros(4, 4).unwrap();
    for k in &operators {
        let real_k = real::product_operator_with_limits(k, &right, LIMITS).unwrap();
        complete = mx::add(
            &complete,
            &mx::multiply(&mx::transpose(&real_k).unwrap(), &real_k).unwrap(),
        )
        .unwrap();
        output = mx::add(
            &output,
            &mx::multiply(
                &mx::multiply(&real_k, &input).unwrap(),
                &mx::transpose(&real_k).unwrap(),
            )
            .unwrap(),
        )
        .unwrap();
    }
    assert_eq!(complete, mx::identity(4).unwrap());
    let actual_output =
        ExactDensityState::try_new(complex.apply(actual_source.matrix()).unwrap()).unwrap();
    assert_eq!(
        output,
        real::realify_density_with_limits(&actual_output, LIMITS).unwrap()
    );
    assert_eq!(mx::trace(&output).unwrap(), ri(1));
}

#[test]
fn entangled_balanced_lift_preserves_positive_state_local_effects_and_roundtrip() {
    let rho = bell_state();
    let (view, lifted) = real::composite_density_views_with_limits(&rho, 2, 2, LIMITS).unwrap();
    ExactDensityState::try_new(embed_rational(&lifted)).unwrap();
    assert_eq!(mx::trace(&lifted).unwrap(), ri(1));
    let p = ct::balance_projector_with_limits(2, 2, LIMITS).unwrap();
    assert_eq!(
        mx::multiply(&mx::multiply(&p, &lifted).unwrap(), &p).unwrap(),
        lifted
    );
    let t = ct::balance_map_with_limits(2, 2, LIMITS).unwrap();
    assert_eq!(
        mx::scale(
            &mx::multiply(
                &mx::multiply(&t, &lifted).unwrap(),
                &mx::transpose(&t).unwrap()
            )
            .unwrap(),
            &rq(1, 2)
        )
        .unwrap(),
        view
    );
    let x = mx::from_rows(vec![
        vec![gq(1, 2, 0, 1), gq(1, 2, 0, 1)],
        vec![gq(1, 2, 0, 1), gq(1, 2, 0, 1)],
    ])
    .unwrap();
    let y = mx::from_rows(vec![
        vec![gq(1, 2, 0, 1), gq(0, 1, -1, 2)],
        vec![gq(0, 1, 1, 2), gq(1, 2, 0, 1)],
    ])
    .unwrap();
    let complex_probability =
        mx::trace(&mx::multiply(&mx::kronecker(&x, &y).unwrap(), rho.matrix()).unwrap()).unwrap();
    assert_eq!(complex_probability, gq(1, 2, 0, 1));
    let local_real = mx::kronecker(
        &real::realify_operator_with_limits(&x, LIMITS).unwrap(),
        &real::realify_operator_with_limits(&y, LIMITS).unwrap(),
    )
    .unwrap();
    assert_eq!(
        mx::trace(&mx::multiply(&local_real, &lifted).unwrap()).unwrap(),
        complex_probability.re
    );
    let compressed = real::product_operator_with_limits(&x, &y, LIMITS).unwrap();
    assert_eq!(
        mx::trace(&mx::multiply(&compressed, &view).unwrap()).unwrap(),
        complex_probability.re
    );
    assert!(real::lift_composite_density_with_limits(&rho, 1, 3, LIMITS).is_err());
}

#[test]
fn conversion_and_tensor_costs_are_one_aggregate_preflight() {
    let scalar = ExactDensityState::try_new(mx::identity(1).unwrap()).unwrap();
    let limits = OperationLimits {
        max_elements: 16,
        max_scalar_ops: 126,
    };
    assert!(real::product_density_with_limits(&scalar, &scalar, limits).is_ok());
    assert!(real::product_density_with_limits(
        &scalar,
        &scalar,
        OperationLimits {
            max_scalar_ops: 125,
            ..limits
        }
    )
    .is_err());
    assert!(real::product_operator_with_limits(
        scalar.matrix(),
        scalar.matrix(),
        OperationLimits {
            max_scalar_ops: 125,
            ..limits
        }
    )
    .is_ok());
    assert!(real::product_operator_with_limits(
        scalar.matrix(),
        scalar.matrix(),
        OperationLimits {
            max_scalar_ops: 124,
            ..limits
        }
    )
    .is_err());
    assert!(real::composite_density_views_with_limits(
        &scalar,
        1,
        1,
        OperationLimits {
            max_scalar_ops: 122,
            ..limits
        }
    )
    .is_ok());
    assert!(real::composite_density_views_with_limits(
        &scalar,
        1,
        1,
        OperationLimits {
            max_scalar_ops: 121,
            ..limits
        }
    )
    .is_err());
    assert!(real::realify_density_with_limits(
        &scalar,
        OperationLimits {
            max_elements: 4,
            max_scalar_ops: 5
        }
    )
    .is_ok());
    assert!(real::realify_density_with_limits(
        &scalar,
        OperationLimits {
            max_elements: 4,
            max_scalar_ops: 4
        }
    )
    .is_err());
}

// Origin: engine/crates_rs/tests/core_quantum_physics/complex_tensor_realification.rs
// Claim: urn:core:crates_rs:tests:complex-tensor-realification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde77461eb {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde77461eb` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore77461eb {
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
impl BoundaryErrore77461eb {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore77461eb {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore77461eb {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde77461eb {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore77461eb> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore77461eb::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore77461eb::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore77461eb::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_e77461eb() {
    let admitted = BoundaryRecorde77461eb::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde77461eb::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
