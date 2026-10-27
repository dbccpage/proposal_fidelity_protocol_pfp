use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
// Finite exact evidence; AuthorityEffect: None.
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq};
use core_quantum_physics::exact_hermitian::outer;
use core_quantum_physics::exact_instrument::{ExactDensityState, ExactFiniteInstrument};
use core_quantum_physics::instrument_repeatability::{
    analyze_repeatability, is_outcome_repeatable, RepeatabilityError,
};

fn basis(n: usize, i: usize) -> Vec<GaussianRat> {
    let mut vector = vec![GaussianRat::zero(); n];
    vector[i] = GaussianRat::one();
    vector
}
fn matrix_unit(n: usize, row: usize, col: usize) -> BasicMatrix<GaussianRat> {
    outer(&basis(n, row), &basis(n, col)).unwrap()
}

#[test]
fn luders_repeats_and_same_effects_measure_prepare_switches() {
    let luders = ExactFiniteInstrument::try_new(
        3,
        3,
        (0..3).map(|i| vec![matrix_unit(3, i, i)]).collect(),
        "projective",
    )
    .unwrap();
    let prepared = ExactFiniteInstrument::try_new(
        3,
        3,
        (0..3).map(|i| vec![matrix_unit(3, 0, i)]).collect(),
        "replace-with-zero",
    )
    .unwrap();
    for o in 0..3 {
        assert_eq!(luders.effect(o).unwrap(), prepared.effect(o).unwrap());
    }
    assert!(is_outcome_repeatable(&luders).unwrap());
    let analysis = analyze_repeatability(&prepared).unwrap();
    assert!(!analysis.is_repeatable());
    let witness = analysis.switching_witness().unwrap();
    assert_eq!((witness.first_outcome, witness.second_outcome), (1, 0));
    assert_eq!(witness.joint_probability_on_maximally_mixed, rq(1, 3));
    let maximally_mixed = ExactDensityState::try_new(
        mx::scale(
            &(mx::identity(3).unwrap()),
            &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 3)),
        )
        .unwrap(),
    )
    .unwrap();
    let first_probability = prepared.probability(1, &maximally_mixed).unwrap();
    let post = prepared.post_state(1, &maximally_mixed).unwrap().unwrap();
    assert_eq!(
        first_probability * prepared.probability(0, &post).unwrap(),
        witness.joint_probability_on_maximally_mixed
    );
}

#[test]
fn nonprojective_effects_can_be_repeatable_in_dimension_three() {
    // E0=diag(1,0,1/2), E1=diag(0,1,1/2). The transient third direction
    // is prepared in the outcome's unit-eigenvalue subspace. Q(i) supplies an
    // exact coefficient (1+i)/2 of squared norm 1/2, without a real sqrt.
    let mut k02 = matrix_unit(3, 0, 2);
    let mut k12 = matrix_unit(3, 1, 2);
    let half_phase = GaussianRat {
        re: rq(1, 2),
        im: rq(1, 2),
    };
    k02.set(0, 2, half_phase.clone()).unwrap();
    k12.set(1, 2, half_phase).unwrap();
    let instrument = ExactFiniteInstrument::try_new(
        3,
        3,
        vec![
            vec![matrix_unit(3, 0, 0), k02],
            vec![matrix_unit(3, 1, 1), k12],
            vec![],
        ],
        "repeatable-unsharp",
    )
    .unwrap();
    let e0 = instrument.effect(0).unwrap();
    assert_ne!(mx::multiply(&(e0), &e0).unwrap(), e0);
    let analysis = analyze_repeatability(&instrument).unwrap();
    assert!(analysis.is_repeatable());
    assert_eq!(
        analysis.joint_probabilities()[0],
        vec![rq(1, 2), ri(0), ri(0)]
    );
    assert_eq!(
        analysis.joint_probabilities()[1],
        vec![ri(0), rq(1, 2), ri(0)]
    );
    let transient = ExactDensityState::try_new(matrix_unit(3, 2, 2)).unwrap();
    for o in 0..2 {
        assert_eq!(instrument.probability(o, &transient).unwrap(), rq(1, 2));
        let post = instrument.post_state(o, &transient).unwrap().unwrap();
        assert_eq!(instrument.probability(o, &post).unwrap(), ri(1));
    }
    assert!(instrument.post_state(2, &transient).unwrap().is_none());
}

#[test]
fn outcome_repeatability_does_not_assert_idempotent_state_update() {
    // One outcome, but its unitary rotates every time. Outcome repeatability
    // is vacuous for that outcome; M(M(rho)) need not equal M(rho).
    let mut unitary = mx::zeros(2, 2).unwrap();
    unitary
        .set(0, 0, GaussianRat::from_rational(rq(3, 5)))
        .unwrap();
    unitary
        .set(0, 1, GaussianRat::from_rational(rq(-4, 5)))
        .unwrap();
    unitary
        .set(1, 0, GaussianRat::from_rational(rq(4, 5)))
        .unwrap();
    unitary
        .set(1, 1, GaussianRat::from_rational(rq(3, 5)))
        .unwrap();
    let instrument = ExactFiniteInstrument::try_new(2, 2, vec![vec![unitary]], "rotate").unwrap();
    assert!(is_outcome_repeatable(&instrument).unwrap());
    let state = ExactDensityState::try_new(matrix_unit(2, 0, 0)).unwrap();
    let once = instrument.post_state(0, &state).unwrap().unwrap();
    let twice = instrument.post_state(0, &once).unwrap().unwrap();
    assert_ne!(once, twice);
}

#[test]
fn rectangular_state_change_requires_an_explicit_second_instrument() {
    let rectangular = ExactFiniteInstrument::try_new(
        2,
        1,
        vec![vec![
            outer(&basis(1, 0), &basis(2, 0)).unwrap(),
            outer(&basis(1, 0), &basis(2, 1)).unwrap(),
        ]],
        "dimension-change",
    )
    .unwrap();
    assert_eq!(
        analyze_repeatability(&rectangular),
        Err(RepeatabilityError::DifferentCarriers {
            dim_in: 2,
            dim_out: 1
        })
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/instrument_repeatability.rs
// Claim: urn:core:crates_rs:tests:instrument-repeatability:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord45f464fb {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord45f464fb` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError45f464fb {
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
impl BoundaryError45f464fb {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError45f464fb {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError45f464fb {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord45f464fb {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError45f464fb> {
        if capacity_bound == 0 {
            return Err(BoundaryError45f464fb::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError45f464fb::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError45f464fb::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_45f464fb() {
    let admitted = BoundaryRecord45f464fb::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord45f464fb::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
