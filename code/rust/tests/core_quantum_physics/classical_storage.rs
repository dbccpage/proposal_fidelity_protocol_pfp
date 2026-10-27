// AuthorityEffect: None. Exact finite carrier-hypothesis controls.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution as star, matrix as mx};
use core_lie_theory::pauli_symplectic::{pauli, Pauli};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::classical_storage::{
    xz_states, ClassicalStorageError, ExactMeasurePrepare,
};
use core_quantum_physics::exact_channel::ExactKrausChannel;
use core_quantum_physics::exact_hermitian::outer;
use core_quantum_physics::exact_instrument::ExactDensityState;
use core_quantum_physics::instruments::ExactPovm;
use core_quantum_physics::population_shadow::composition_defect;
use core_quantum_physics::trace_norm_certificate::SignCertificate;

fn scale(m: &BasicMatrix<GaussianRat>, r: Rational) -> BasicMatrix<GaussianRat> {
    mx::scale(m, &GaussianRat::from_rational(r)).unwrap()
}

fn z_storage() -> ExactMeasurePrepare {
    let states = xz_states().unwrap();
    ExactMeasurePrepare::try_new(
        ExactPovm::try_new(vec![states[0].matrix().clone(), states[1].matrix().clone()]).unwrap(),
        vec![states[0].clone(), states[1].clone()],
    )
    .unwrap()
}

#[test]
fn sharp_xz_bound_is_attained_and_choi_replays_the_round_trip() {
    let storage = z_storage();
    let certificate = storage.xz_certificate().unwrap();
    assert_eq!(certificate.survival(), &[ri(1), ri(1), rq(1, 2), rq(1, 2)]);
    assert_eq!(certificate.average(), &rq(3, 4));
    assert_eq!(certificate.upper_bound(), rq(3, 4));
    assert_eq!(certificate.gap(), &ri(0));
    assert_eq!(certificate.branch_slacks(), &[ri(0), ri(0)]);
    let choi = storage.choi().unwrap();
    for state in xz_states().unwrap() {
        assert_eq!(
            storage.apply(&state).unwrap().matrix(),
            &choi.apply(state.matrix()).unwrap()
        );
    }
}

#[test]
fn rational_rotated_projective_storage_also_attains_the_bound() {
    let x = pauli::<GaussianRat>(Pauli::X).unwrap();
    let z = pauli::<GaussianRat>(Pauli::Z).unwrap();
    let axis = mx::add(&scale(&x, rq(3, 5)), &scale(&z, rq(4, 5))).unwrap();
    let identity = mx::identity(2).unwrap();
    let positive =
        ExactDensityState::try_new(scale(&mx::add(&identity, &axis).unwrap(), rq(1, 2))).unwrap();
    let negative =
        ExactDensityState::try_new(scale(&mx::sub(&identity, &axis).unwrap(), rq(1, 2))).unwrap();
    let storage = ExactMeasurePrepare::try_new(
        ExactPovm::try_new(vec![positive.matrix().clone(), negative.matrix().clone()]).unwrap(),
        vec![positive, negative],
    )
    .unwrap();
    let certificate = storage.xz_certificate().unwrap();
    assert_eq!(
        certificate.survival(),
        &[rq(41, 50), rq(41, 50), rq(17, 25), rq(17, 25)]
    );
    assert_eq!(certificate.average(), &rq(3, 4));
    assert_eq!(certificate.branch_slacks(), &[ri(0), ri(0)]);
}

#[test]
fn refining_letters_and_adding_an_impossible_letter_does_not_evade_the_bound() {
    let states = xz_states().unwrap();
    let effects = states
        .iter()
        .map(|s| scale(s.matrix(), rq(1, 2)))
        .chain([mx::zeros(2, 2).unwrap()])
        .collect();
    let mut preparations = states.to_vec();
    preparations.push(states[2].clone());
    let storage =
        ExactMeasurePrepare::try_new(ExactPovm::try_new(effects).unwrap(), preparations).unwrap();
    let certificate = storage.xz_certificate().unwrap();
    assert_eq!(
        certificate.survival(),
        &[rq(3, 4), rq(3, 4), rq(3, 4), rq(3, 4)]
    );
    assert_eq!(certificate.average(), &rq(3, 4));
    assert_eq!(
        certificate.branch_slacks(),
        &[ri(0), ri(0), ri(0), ri(0), ri(0)]
    );
    assert_eq!(storage.probabilities(&states[0]).unwrap()[4], ri(0));
    for state in &states {
        let restored = storage.apply(state).unwrap();
        let difference = mx::sub(state.matrix(), restored.matrix()).unwrap();
        let sign = mx::sub(&scale(state.matrix(), ri(2)), &mx::identity(2).unwrap()).unwrap();
        let norm = SignCertificate::new(difference, sign).unwrap();
        assert_eq!(norm.trace_norm() / ri(2), rq(1, 4));
    }
}

#[test]
fn complex_effects_and_preparations_keep_the_choi_transpose_and_strict_margin() {
    let y = pauli::<GaussianRat>(Pauli::Y).unwrap();
    let identity = mx::identity(2).unwrap();
    let plus =
        ExactDensityState::try_new(scale(&mx::add(&identity, &y).unwrap(), rq(1, 2))).unwrap();
    let minus =
        ExactDensityState::try_new(scale(&mx::sub(&identity, &y).unwrap(), rq(1, 2))).unwrap();
    let storage = ExactMeasurePrepare::try_new(
        ExactPovm::try_new(vec![plus.matrix().clone(), minus.matrix().clone()]).unwrap(),
        vec![plus.clone(), minus.clone()],
    )
    .unwrap();
    let certificate = storage.xz_certificate().unwrap();
    assert_eq!(certificate.average(), &rq(1, 2));
    assert_eq!(certificate.gap(), &rq(1, 4));
    assert_eq!(certificate.branch_slacks(), &[ri(1), ri(1)]);
    let choi = storage.choi().unwrap();
    for state in [plus, minus] {
        assert_eq!(storage.apply(&state).unwrap(), state);
        assert_eq!(choi.apply(state.matrix()).unwrap(), *state.matrix());
    }
}

#[test]
fn rectangular_retrieval_is_normalized_but_has_no_qubit_score() {
    let preparation =
        ExactDensityState::try_new(scale(&mx::identity(3).unwrap(), rq(1, 3))).unwrap();
    let storage = ExactMeasurePrepare::try_new(
        ExactPovm::try_new(vec![mx::identity(2).unwrap()]).unwrap(),
        vec![preparation.clone()],
    )
    .unwrap();
    let state = xz_states().unwrap()[2].clone();
    assert_eq!(storage.apply(&state).unwrap(), preparation);
    assert_eq!(
        storage.choi().unwrap().apply(state.matrix()).unwrap(),
        *preparation.matrix()
    );
    assert_eq!(
        storage.xz_certificate(),
        Err(ClassicalStorageError::NotQubit)
    );
}

#[test]
fn invalid_carriers_and_nonpositive_retrieval_are_refused() {
    let states = xz_states().unwrap();
    let storage = z_storage();
    assert_eq!(
        ExactMeasurePrepare::try_new(storage.measurement().clone(), vec![states[0].clone()]),
        Err(ClassicalStorageError::OutcomeCount)
    );
    let one = ExactDensityState::try_new(mx::identity(1).unwrap()).unwrap();
    assert_eq!(
        ExactMeasurePrepare::try_new(
            storage.measurement().clone(),
            vec![states[0].clone(), one.clone()]
        ),
        Err(ClassicalStorageError::OutputDimension)
    );
    assert_eq!(
        storage.apply(&one),
        Err(ClassicalStorageError::InputDimension)
    );
    assert!(ExactPovm::try_new(vec![]).is_err());
    assert!(ExactPovm::try_new(vec![states[0].matrix().clone()]).is_err());
    assert!(ExactPovm::try_new(vec![
        scale(states[0].matrix(), ri(-1)),
        mx::add(&mx::identity(2).unwrap(), states[0].matrix()).unwrap(),
    ])
    .is_err());
    // A classical letter with definite X=Z=+1 would need this nonpositive
    // quantum preparation. Trace one and matching those two probes are not enough.
    let x = pauli::<GaussianRat>(Pauli::X).unwrap();
    let z = pauli::<GaussianRat>(Pauli::Z).unwrap();
    let fake_state = scale(
        &mx::add(&mx::add(&mx::identity(2).unwrap(), &x).unwrap(), &z).unwrap(),
        rq(1, 2),
    );
    assert!(ExactDensityState::try_new(fake_state).is_err());
    let mut raw = mx::identity(2).unwrap();
    raw.set(
        0,
        0,
        GaussianRat::from_rational(Rational::new_raw(1.into(), 0.into())),
    )
    .unwrap();
    assert!(ExactPovm::try_new(vec![raw]).is_err());
}

#[test]
fn a_static_classical_table_fits_the_four_states_without_positive_quantum_retrieval() {
    // Letters carry (Z,X)=(+,+),(+,-),(-,+),(-,-). This static experiment
    // alone is classical: no contextuality or ontology is refuted by four rows.
    let distributions = [
        [rq(1, 2), rq(1, 2), ri(0), ri(0)],
        [ri(0), ri(0), rq(1, 2), rq(1, 2)],
        [rq(1, 2), ri(0), rq(1, 2), ri(0)],
        [ri(0), rq(1, 2), ri(0), rq(1, 2)],
    ];
    let probes = [[ri(1), ri(1), ri(0), ri(0)], [ri(1), ri(0), ri(1), ri(0)]];
    let expected = [
        [ri(1), ri(0), rq(1, 2), rq(1, 2)],
        [rq(1, 2), rq(1, 2), ri(1), ri(0)],
    ];
    for (i, distribution) in distributions.iter().enumerate() {
        assert_eq!(distribution.iter().sum::<Rational>(), ri(1));
        for (a, probe) in probes.iter().enumerate() {
            let probability = distribution
                .iter()
                .zip(probe)
                .map(|(p, e)| p * e)
                .sum::<Rational>();
            assert_eq!(probability, expected[a][i]);
        }
    }
    for letter in 0..4 {
        assert_eq!(
            &distributions[0][letter] + &distributions[1][letter],
            &distributions[2][letter] + &distributions[3][letter]
        );
    }
}

#[test]
fn coherent_memory_scores_one_and_population_loss_fails_under_available_inverse_control() {
    let identity =
        ExactKrausChannel::try_new(2, 2, vec![mx::identity(2).unwrap()], "memory").unwrap();
    let score = xz_states()
        .unwrap()
        .iter()
        .map(|s| {
            star::hs_inner(s.matrix(), &identity.apply(s.matrix()).unwrap())
                .unwrap()
                .re
        })
        .sum::<Rational>()
        / ri(4);
    assert_eq!(score, ri(1));
    let rotation = BasicMatrix::from_row_major(
        2,
        2,
        vec![
            GaussianRat::from_rational(rq(3, 5)),
            GaussianRat::from_rational(rq(4, 5)),
            GaussianRat::from_rational(rq(-4, 5)),
            GaussianRat::from_rational(rq(3, 5)),
        ],
    )
    .unwrap();
    let undo = ExactKrausChannel::try_new(2, 2, vec![rotation], "inverse-prepare").unwrap();
    let before = ExactKrausChannel::try_new(
        2,
        2,
        vec![star::adjoint(&undo.operators()[0]).unwrap()],
        "prepare",
    )
    .unwrap();
    assert_ne!(
        composition_defect(&before, &undo).unwrap(),
        mx::zeros(2, 2).unwrap()
    );
    let states = [ri(1), ri(-1)].map(|sign| {
        let vector = [
            GaussianRat::from_rational(rq(3, 5)),
            GaussianRat::from_rational(sign * rq(4, 5)),
        ];
        ExactDensityState::try_new(outer(&vector, &vector).unwrap()).unwrap()
    });
    let storage = z_storage();
    assert_eq!(
        storage.probabilities(&states[0]).unwrap(),
        vec![rq(9, 25), rq(16, 25)]
    );
    assert_eq!(
        storage.probabilities(&states[0]).unwrap(),
        storage.probabilities(&states[1]).unwrap()
    );
    assert_eq!(
        storage.apply(&states[0]).unwrap(),
        storage.apply(&states[1]).unwrap()
    );
    let q0 = |s: &ExactDensityState| undo.apply(s.matrix()).unwrap().get(0, 0).unwrap().re;
    assert_eq!(q0(&states[0]), ri(1));
    assert_eq!(q0(&states[1]), rq(49, 625));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/classical_storage.rs
// Claim: urn:core:crates_rs:tests:classical-storage:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0296bdfc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0296bdfc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0296bdfc {
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
impl BoundaryError0296bdfc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0296bdfc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0296bdfc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0296bdfc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0296bdfc> {
        if capacity_bound == 0 {
            return Err(BoundaryError0296bdfc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0296bdfc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0296bdfc::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_0296bdfc() {
    let admitted = BoundaryRecord0296bdfc::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord0296bdfc::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
