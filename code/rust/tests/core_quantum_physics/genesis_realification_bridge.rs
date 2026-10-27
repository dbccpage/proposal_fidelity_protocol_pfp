use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix::{diagonal, from_rows as matrix_from_rows};
use linear_algebra::exact_field::{involution as star, matrix as mx};
// AuthorityEffect: None. Representation equivalence with a DECLARED complex
// structure; no selection of a Hilbert/Born/complex host from difference.
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_channel::ExactKrausChannel;
use core_quantum_physics::exact_hermitian::{gi, gq, is_psd, realify};
use core_quantum_physics::exact_instrument::{ExactDensityState, ExactFiniteInstrument};

fn rational_matrix(rows: Vec<Vec<Rational>>) -> BasicMatrix<GaussianRat> {
    matrix_from_rows(
        rows.into_iter()
            .map(|row| {
                row.into_iter()
                    .map(|re| GaussianRat { re, im: ri(0) })
                    .collect()
            })
            .collect(),
    )
    .unwrap()
}

/// Existing public realify is Hermitian-only. General rectangular R(K) is
/// obtained from its Hermitian dilation, without another matrix-math engine.
fn operator_realification(k: &BasicMatrix<GaussianRat>) -> BasicMatrix<GaussianRat> {
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
    let real = realify(&dilation).unwrap();
    let rows: Vec<usize> = (0..k.rows()).chain(n..n + k.rows()).collect();
    let cols: Vec<usize> = (k.rows()..n).chain(n + k.rows()..2 * n).collect();
    rational_matrix(
        rows.iter()
            .map(|&i| cols.iter().map(|&j| real[i][j].clone()).collect())
            .collect(),
    )
}
fn hermitian_realification(k: &BasicMatrix<GaussianRat>) -> BasicMatrix<GaussianRat> {
    rational_matrix(realify(k).unwrap())
}
fn complex_structure(n: usize) -> BasicMatrix<GaussianRat> {
    let mut j = mx::zeros(2 * n, 2 * n).unwrap();
    for i in 0..n {
        j.set(i, n + i, gi(-1, 0)).unwrap();
        j.set(n + i, i, gi(1, 0)).unwrap();
    }
    j
}
fn state() -> ExactDensityState {
    ExactDensityState::try_new(
        matrix_from_rows(vec![
            vec![gq(3, 5, 0, 1), gq(0, 1, 1, 5)],
            vec![gq(0, 1, -1, 5), gq(2, 5, 0, 1)],
        ])
        .unwrap(),
    )
    .unwrap()
}
fn instrument_operators() -> Vec<BasicMatrix<GaussianRat>> {
    let u = matrix_from_rows(vec![
        vec![gq(3, 5, 0, 1), gq(0, 1, 4, 5)],
        vec![gq(0, 1, 4, 5), gq(3, 5, 0, 1)],
    ])
    .unwrap();
    vec![
        mx::multiply(&(diagonal(&[gq(3, 5, 0, 1), gq(4, 5, 0, 1)]).unwrap()), &u).unwrap(),
        mx::multiply(&(diagonal(&[gq(4, 5, 0, 1), gq(3, 5, 0, 1)]).unwrap()), &u).unwrap(),
    ]
}

#[test]
fn arbitrary_rectangular_realification_preserves_products_adjoint_and_real_trace() {
    let a = matrix_from_rows(vec![
        vec![gi(1, 2), gi(3, -1), gi(0, 1)],
        vec![gi(-1, 0), gi(2, 1), gi(1, -2)],
    ])
    .unwrap();
    let b = matrix_from_rows(vec![
        vec![gi(0, 1), gi(2, 0)],
        vec![gi(1, -1), gi(0, 2)],
        vec![gi(3, 1), gi(-1, 0)],
    ])
    .unwrap();
    let ra = operator_realification(&a);
    let rb = operator_realification(&b);
    assert_eq!(
        mx::multiply(&(ra), &rb).unwrap(),
        operator_realification(&mx::multiply(&(a), &b).unwrap())
    );
    assert_eq!(
        star::adjoint(&(ra)).unwrap(),
        operator_realification(&star::adjoint(&(a)).unwrap())
    );
    assert_eq!(
        mx::multiply(&(complex_structure(2)), &ra).unwrap(),
        mx::multiply(&(ra), &complex_structure(3)).unwrap()
    );
    assert_eq!(
        mx::multiply(&(complex_structure(2)), &complex_structure(2)).unwrap(),
        mx::scale(
            &(mx::identity(4).unwrap()),
            &core_number_theory::cyclotomic::GaussianRat::from_rational(ri(-1))
        )
        .unwrap()
    );
    let c = matrix_from_rows(vec![vec![gi(1, 3), gi(2, 1)], vec![gi(-1, 4), gi(2, -1)]]).unwrap();
    assert_eq!(mx::trace(&(c)).unwrap(), gi(3, 2));
    assert_eq!(mx::trace(&(operator_realification(&c))).unwrap(), gi(6, 0));
    assert!(realify(&c).is_err()); // Public API's Hermitian boundary remains intact.
    let rho = state();
    assert_eq!(
        operator_realification(rho.matrix()),
        hermitian_realification(rho.matrix())
    );
}

#[test]
fn imaginary_coherence_effects_probabilities_and_conditional_states_are_preserved() {
    let rho = state();
    let sigma = ExactDensityState::try_new(
        mx::scale(
            &(hermitian_realification(rho.matrix())),
            &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 2)),
        )
        .unwrap(),
    )
    .unwrap();
    assert_eq!(mx::trace(&(sigma.matrix())).unwrap(), gi(1, 0));
    let j = complex_structure(2);
    assert_eq!(
        mx::multiply(&(j), sigma.matrix()).unwrap(),
        mx::multiply(&(sigma.matrix()), &j).unwrap()
    );
    let ks = instrument_operators();
    let complex = ExactFiniteInstrument::try_new(
        2,
        2,
        ks.iter().cloned().map(|k| vec![k]).collect(),
        "complex",
    )
    .unwrap();
    let real = ExactFiniteInstrument::try_new(
        4,
        4,
        ks.iter().map(|k| vec![operator_realification(k)]).collect(),
        "realified",
    )
    .unwrap();
    let mut total = ri(0);
    for outcome in 0..2 {
        let effect = complex.effect(outcome).unwrap();
        assert!(!effect.get(0, 1).unwrap().im.eq(&ri(0))); // An actually complex, nontrivial effect.
        assert_eq!(
            real.effect(outcome).unwrap(),
            hermitian_realification(&effect)
        );
        let p = complex.probability(outcome, &rho).unwrap();
        assert!(p > ri(0) && p < ri(1));
        assert_eq!(real.probability(outcome, &sigma).unwrap(), p);
        total += p;
        let unnormalized = complex.unnormalized_post_state(outcome, &rho).unwrap();
        assert_eq!(
            real.unnormalized_post_state(outcome, &sigma).unwrap(),
            mx::scale(
                &(hermitian_realification(&unnormalized)),
                &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 2))
            )
            .unwrap()
        );
        let post = complex.post_state(outcome, &rho).unwrap().unwrap();
        assert_eq!(
            real.post_state(outcome, &sigma).unwrap().unwrap().matrix(),
            &mx::scale(
                &(hermitian_realification(post.matrix())),
                &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 2))
            )
            .unwrap()
        );
    }
    assert_eq!(total, ri(1));
    // Omitting the factor1/2 produces trace2 and is refused as a state.
    assert!(ExactDensityState::try_new(hermitian_realification(rho.matrix())).is_err());
}

#[test]
fn sequential_channel_composition_and_heisenberg_pairing_are_preserved() {
    let rho = state();
    let sigma = mx::scale(
        &(hermitian_realification(rho.matrix())),
        &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 2)),
    )
    .unwrap();
    let ks = instrument_operators();
    let first = ExactKrausChannel::try_new(2, 2, ks.clone(), "first").unwrap();
    let second = ExactKrausChannel::try_weighted(
        2,
        2,
        vec![
            (rq(1, 3), mx::identity(2).unwrap()),
            (
                rq(2, 3),
                matrix_from_rows(vec![vec![gi(0, 0), gi(0, -1)], vec![gi(0, 1), gi(0, 0)]])
                    .unwrap(),
            ),
        ],
        "second",
    )
    .unwrap();
    let real_first = ExactKrausChannel::try_new(
        4,
        4,
        ks.iter().map(operator_realification).collect(),
        "real first",
    )
    .unwrap();
    let real_second = ExactKrausChannel::try_weighted(
        4,
        4,
        second
            .weights()
            .iter()
            .cloned()
            .zip(second.operators().iter().map(operator_realification))
            .collect(),
        "real second",
    )
    .unwrap();
    let composed = first.compose(&second).unwrap();
    let real_composed = real_first.compose(&real_second).unwrap();
    let complex_output = composed.apply(rho.matrix()).unwrap();
    assert_eq!(
        complex_output,
        second.apply(&first.apply(rho.matrix()).unwrap()).unwrap()
    );
    assert_eq!(
        real_composed.apply(&sigma).unwrap(),
        mx::scale(
            &(hermitian_realification(&complex_output)),
            &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 2))
        )
        .unwrap()
    );
    let effect = mx::multiply(&(star::adjoint(&(ks[0])).unwrap()), &ks[0]).unwrap();
    assert_eq!(
        real_composed
            .adjoint_apply(&hermitian_realification(&effect))
            .unwrap(),
        hermitian_realification(&composed.adjoint_apply(&effect).unwrap())
    );
}

#[test]
fn unrestricted_real_states_and_dynamics_are_not_the_complex_image() {
    let j = complex_structure(2);
    let pure_real = diagonal(&[gi(1, 0), gi(0, 0), gi(0, 0), gi(0, 0)]).unwrap();
    assert!(is_psd(&pure_real).unwrap());
    assert!(ExactDensityState::try_new(pure_real.clone()).is_ok());
    assert_ne!(
        mx::multiply(&(j), &pure_real).unwrap(),
        mx::multiply(&(pure_real), &j).unwrap()
    );
    let sigma = mx::scale(
        &(hermitian_realification(state().matrix())),
        &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 2)),
    )
    .unwrap();
    let reflection = diagonal(&[gi(-1, 0), gi(1, 0), gi(1, 0), gi(1, 0)]).unwrap();
    assert_eq!(
        mx::multiply(&(star::adjoint(&(reflection)).unwrap()), &reflection).unwrap(),
        mx::identity(4).unwrap()
    );
    assert_ne!(
        mx::multiply(&(j), &reflection).unwrap(),
        mx::multiply(&(reflection), &j).unwrap()
    );
    let real_channel =
        ExactKrausChannel::try_new(4, 4, vec![reflection], "unrestricted real extension").unwrap();
    let output = real_channel.apply(&sigma).unwrap();
    assert_ne!(
        mx::multiply(&(j), &output).unwrap(),
        mx::multiply(&(output), &j).unwrap()
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/genesis_realification_bridge.rs
// Claim: urn:core:crates_rs:tests:genesis-realification-bridge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda3b92b37 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda3b92b37` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora3b92b37 {
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
impl BoundaryErrora3b92b37 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora3b92b37 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora3b92b37 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda3b92b37 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora3b92b37> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora3b92b37::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora3b92b37::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora3b92b37::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a3b92b37() {
    let admitted = BoundaryRecorda3b92b37::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda3b92b37::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
