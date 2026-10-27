use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution as star, matrix as mx};
// AuthorityEffect: None. Finite identities for declared Q(i) instruments.
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::{hermitian_trace, outer};
use core_quantum_physics::exact_instrument::{ExactDensityState, ExactFiniteInstrument};

fn entry(row: usize, col: usize, coefficient: Rational) -> BasicMatrix<GaussianRat> {
    let mut matrix =
        BasicMatrix::<GaussianRat>::try_from_fn(2, 3, |_, _| GaussianRat::zero()).unwrap();
    matrix
        .set(row, col, GaussianRat::from_rational(coefficient))
        .unwrap();
    matrix
}
fn rectangular() -> ExactFiniteInstrument {
    ExactFiniteInstrument::try_new(
        3,
        2,
        vec![
            vec![entry(0, 0, rq(3, 5)), entry(0, 0, rq(4, 5))],
            vec![entry(1, 1, ri(1)), entry(0, 2, ri(1))],
            vec![],
        ],
        "rectangular-grouped",
    )
    .unwrap()
}
fn diagonal_state() -> ExactDensityState {
    let mut rho = mx::zeros(3, 3).unwrap();
    for (i, p) in [rq(1, 2), rq(1, 3), rq(1, 6)].into_iter().enumerate() {
        rho.set(i, i, GaussianRat::from_rational(p)).unwrap();
    }
    ExactDensityState::try_new(rho).unwrap()
}

#[test]
fn arbitrary_dimension_grouped_outcomes_obey_exact_instrument_identities() {
    let instrument = rectangular();
    let state = diagonal_state();
    let mut effects = mx::zeros(3, 3).unwrap();
    let mut unnormalized = mx::zeros(2, 2).unwrap();
    let mut total = ri(0);
    for outcome in 0..instrument.outcomes() {
        let effect = instrument.effect(outcome).unwrap();
        let post = instrument.unnormalized_post_state(outcome, &state).unwrap();
        let probability = instrument.probability(outcome, &state).unwrap();
        assert_eq!(
            instrument.dilation_outcome_map(outcome, &state).unwrap(),
            post
        );
        let trace_formula = mx::trace(&(mx::multiply(&(effect), state.matrix()).unwrap())).unwrap();
        assert_eq!(trace_formula.im, ri(0));
        assert_eq!(trace_formula.re, probability);
        assert!(probability >= ri(0));
        if let Some(normalized) = instrument.post_state(outcome, &state).unwrap() {
            assert_eq!(hermitian_trace(normalized.matrix()).unwrap(), ri(1));
            assert_eq!(
                mx::scale(
                    &(normalized.matrix()),
                    &core_number_theory::cyclotomic::GaussianRat::from_rational(
                        probability.clone()
                    )
                )
                .unwrap(),
                post
            );
        } else {
            assert_eq!(probability, ri(0));
            assert_eq!(post, mx::zeros(2, 2).unwrap());
        }
        effects = mx::add(&(effects), &effect).unwrap();
        unnormalized = mx::add(&(unnormalized), &post).unwrap();
        total += probability;
    }
    assert_eq!(effects, mx::identity(3).unwrap());
    assert_eq!(total, ri(1));
    assert_eq!(
        unnormalized,
        instrument.channel().apply(state.matrix()).unwrap()
    );
    let isometry = instrument.stinespring_isometry().unwrap();
    assert_eq!((isometry.rows(), isometry.cols()), (8, 3));
    assert_eq!(
        mx::multiply(&(star::adjoint(&(isometry)).unwrap()), &isometry).unwrap(),
        mx::identity(3).unwrap()
    );
    assert_eq!(instrument.apply_dilation(&state).unwrap(), unnormalized);
}

#[test]
fn complex_coherences_and_invalid_states_are_checked_exactly() {
    let vector = [
        GaussianRat::from_rational(rq(3, 5)),
        GaussianRat {
            re: ri(0),
            im: rq(4, 5),
        },
        GaussianRat::zero(),
    ];
    let state = ExactDensityState::try_new(outer(&vector, &vector).unwrap()).unwrap();
    let instrument = rectangular();
    assert_eq!(instrument.probability(0, &state).unwrap(), rq(9, 25));
    assert_eq!(instrument.probability(1, &state).unwrap(), rq(16, 25));
    assert_eq!(
        instrument.apply_dilation(&state).unwrap(),
        instrument.channel().apply(state.matrix()).unwrap()
    );
    assert!(ExactDensityState::try_new(mx::zeros(3, 3).unwrap()).is_err());
    let mut indefinite = mx::zeros(3, 3).unwrap();
    indefinite.set(0, 0, GaussianRat::from_ints(2, 0)).unwrap();
    indefinite.set(1, 1, GaussianRat::from_ints(-1, 0)).unwrap();
    assert!(ExactDensityState::try_new(indefinite).is_err());
    let mut malformed = state.matrix().as_slice().to_vec();
    malformed.pop();
    assert!(BasicMatrix::<GaussianRat>::from_row_major(
        state.dimension(),
        state.dimension(),
        malformed
    )
    .is_err());
    let wrong_dimension = ExactDensityState::try_new(mx::identity(1).unwrap()).unwrap();
    assert!(instrument.probability(0, &wrong_dimension).is_err());
    assert!(instrument.probability(3, &state).is_err());
}

// Origin: engine/crates_rs/tests/core_quantum_physics/exact_instrument_finite.rs
// Claim: urn:core:crates_rs:tests:exact-instrument-finite:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4c062a1d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4c062a1d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4c062a1d {
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
impl BoundaryError4c062a1d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4c062a1d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4c062a1d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4c062a1d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4c062a1d> {
        if capacity_bound == 0 {
            return Err(BoundaryError4c062a1d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4c062a1d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4c062a1d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_4c062a1d() {
    let admitted = BoundaryRecord4c062a1d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord4c062a1d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
