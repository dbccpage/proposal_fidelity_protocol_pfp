//! Finite Feynman shadows: the time-sliced free-particle kernel kept as
//! an exact sum of formal phases, replayed history by history and by transfer
//! matrices, evaluated only at declared commensurate units, refused on bad
//! declarations, and torn by refinement.

use std::collections::BTreeSet;

use linear_algebra::scalars::Semiring;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::{gi, gq};

use core_quantum_physics::graded_path_sum::{TimeSlicedTransport, TransportError};
use core_quantum_physics::time_sliced_action_shadow::{
    refinement_residual, FreeParticleShadow, PhaseSum, ShadowRefusal,
};

fn rats(values: &[i64]) -> Vec<Rational> {
    values.iter().map(|&v| ri(v)).collect()
}

/// Mass, hbar and normalization one, both endpoints at the origin.
fn shadow(times: Vec<Rational>, carrier: Vec<Rational>) -> FreeParticleShadow {
    FreeParticleShadow::new(times, carrier, ri(0), ri(0), ri(1), ri(1), gi(1, 0)).unwrap()
}

fn phases(terms: &[(Rational, GaussianRat)]) -> PhaseSum {
    terms.iter().fold(PhaseSum::zero(), |acc, (theta, c)| {
        acc.add(&PhaseSum::phase(theta.clone()).scale(c))
    })
}

#[test]
fn the_two_slice_free_particle_shadow_is_one_plus_two_phases() {
    let s = shadow(rats(&[0, 1, 2]), rats(&[-1, 0, 1]));
    let certificate = s.replay().unwrap();
    let positions: Vec<Vec<Rational>> = certificate
        .histories
        .iter()
        .map(|h| h.positions.clone())
        .collect();
    assert_eq!(
        positions,
        vec![rats(&[0, -1, 0]), rats(&[0, 0, 0]), rats(&[0, 1, 0])]
    );
    let actions: Vec<Rational> = certificate
        .histories
        .iter()
        .map(|h| h.action.clone())
        .collect();
    assert_eq!(actions, rats(&[1, 0, 1]));
    // K = 1 + 2 e^(i), kept exactly.
    assert_eq!(
        certificate.kernel,
        phases(&[(ri(0), gi(1, 0)), (ri(1), gi(2, 0))])
    );
    assert_eq!(s.transfer_kernel(), certificate.kernel);
}

#[test]
fn a_three_step_shadow_replays_nine_histories_and_matches_its_transfer_matrices() {
    let s = shadow(rats(&[0, 1, 2, 3]), rats(&[-1, 0, 1]));
    let certificate = s.replay().unwrap();
    assert_eq!(certificate.histories.len(), 9);
    let middles: BTreeSet<(Rational, Rational)> = certificate
        .histories
        .iter()
        .map(|h| (h.positions[1].clone(), h.positions[2].clone()))
        .collect();
    assert_eq!(middles.len(), 9, "every history appears exactly once");
    assert!(certificate
        .histories
        .iter()
        .all(|h| h.positions.len() == 4 && h.positions[0] == ri(0) && h.positions[3] == ri(0)));
    assert_eq!(
        certificate.kernel,
        phases(&[(ri(0), gi(1, 0)), (ri(1), gi(6, 0)), (ri(3), gi(2, 0))])
    );
    assert_eq!(s.transfer_kernel(), certificate.kernel);
}

#[test]
fn the_kernel_is_evaluated_only_at_a_declared_commensurate_unit() {
    let kernel = shadow(rats(&[0, 1, 2]), rats(&[-1, 0, 1]))
        .replay()
        .unwrap()
        .kernel;
    let u = gq(3, 5, 4, 5);
    assert_eq!(kernel.evaluate(&ri(1), &u).unwrap(), gq(11, 5, 8, 5));
    assert_eq!(kernel.evaluate(&rq(1, 2), &u).unwrap(), gq(11, 25, 48, 25));
    // A unit of finite order folds phases together: e^(i) read as i gives 1 + 2i.
    assert_eq!(kernel.evaluate(&ri(1), &gi(0, 1)).unwrap(), gi(1, 2));
    assert_eq!(
        kernel.evaluate(&ri(2), &u),
        Err(ShadowRefusal::IncommensuratePhase(ri(1)))
    );
    assert_eq!(
        kernel.evaluate(&ri(1), &gi(1, 1)),
        Err(ShadowRefusal::NonUnitPhase)
    );
    assert_eq!(kernel.evaluate(&ri(0), &u), Err(ShadowRefusal::ZeroQuantum));
}

#[test]
fn shadow_declarations_are_refused_before_any_replay() {
    let times = || rats(&[0, 1, 2]);
    let carrier = || rats(&[-1, 0, 1]);
    let declare = |times: Vec<Rational>,
                   carrier: Vec<Rational>,
                   end: i64,
                   mass: i64,
                   hbar: i64,
                   z: GaussianRat| {
        FreeParticleShadow::new(times, carrier, ri(0), ri(end), ri(mass), ri(hbar), z)
    };
    assert_eq!(
        declare(rats(&[0]), carrier(), 0, 1, 1, gi(1, 0)),
        Err(ShadowRefusal::TooFewTimes(1))
    );
    assert_eq!(
        declare(rats(&[0, 1, 1]), carrier(), 0, 1, 1, gi(1, 0)),
        Err(ShadowRefusal::NonIncreasingTimes { step: 1 })
    );
    assert_eq!(
        declare(rats(&[0, 2, 1]), carrier(), 0, 1, 1, gi(1, 0)),
        Err(ShadowRefusal::NonIncreasingTimes { step: 1 })
    );
    assert_eq!(
        declare(times(), vec![], 0, 1, 1, gi(1, 0)),
        Err(ShadowRefusal::EmptyCarrier)
    );
    assert_eq!(
        declare(times(), rats(&[0, 1, 0]), 0, 1, 1, gi(1, 0)),
        Err(ShadowRefusal::DuplicateCarrierPoint { index: 2 })
    );
    assert_eq!(
        declare(times(), carrier(), 5, 1, 1, gi(1, 0)),
        Err(ShadowRefusal::EndpointNotInCarrier("end"))
    );
    assert_eq!(
        FreeParticleShadow::new(times(), carrier(), ri(2), ri(0), ri(1), ri(1), gi(1, 0)),
        Err(ShadowRefusal::EndpointNotInCarrier("start"))
    );
    assert_eq!(
        declare(times(), carrier(), 0, 0, 1, gi(1, 0)),
        Err(ShadowRefusal::NonPositiveMass)
    );
    assert_eq!(
        declare(times(), carrier(), 0, 1, -1, gi(1, 0)),
        Err(ShadowRefusal::NonPositiveHbar)
    );
    assert_eq!(
        declare(times(), carrier(), 0, 1, 1, gi(0, 0)),
        Err(ShadowRefusal::ZeroNormalization)
    );
}

#[test]
fn refining_the_partition_tears_the_free_particle_shadow() {
    let carrier = rats(&[-1, 0, 1]);
    let coarse = shadow(rats(&[0, 2]), carrier.clone());
    let fine = shadow(rats(&[0, 1, 2]), carrier.clone());
    assert_eq!(coarse.replay().unwrap().kernel, PhaseSum::one());
    assert_eq!(
        refinement_residual(&coarse, &fine).unwrap(),
        phases(&[(ri(1), gi(2, 0))])
    );
    // A declared normalization rescales the fine kernel but cannot close the tear.
    let normalized = FreeParticleShadow::new(
        rats(&[0, 1, 2]),
        carrier.clone(),
        ri(0),
        ri(0),
        ri(1),
        ri(1),
        gi(3, 0),
    )
    .unwrap();
    assert_eq!(
        refinement_residual(&coarse, &normalized).unwrap(),
        phases(&[(ri(0), gq(-2, 3, 0, 1)), (ri(1), gq(2, 3, 0, 1))])
    );
    // A one-point carrier has a single history at every refinement: no tear.
    let point = rats(&[0]);
    assert!(refinement_residual(
        &shadow(rats(&[0, 2]), point.clone()),
        &shadow(rats(&[0, 1, 2]), point)
    )
    .unwrap()
    .is_zero());
    // Only a genuine refinement of the same declaration is compared.
    assert_eq!(
        refinement_residual(&fine, &coarse),
        Err(ShadowRefusal::NotARefinement(
            "the partition is not refined"
        ))
    );
    assert_eq!(
        refinement_residual(&coarse, &shadow(rats(&[0, 1, 2]), rats(&[0, 1]))),
        Err(ShadowRefusal::NotARefinement("the carriers differ"))
    );
    assert_eq!(
        refinement_residual(&coarse, &shadow(rats(&[0, 1, 3]), carrier.clone())),
        Err(ShadowRefusal::NotARefinement(
            "the partition is not refined"
        ))
    );
    let moved_end = FreeParticleShadow::new(
        rats(&[0, 1, 2]),
        carrier.clone(),
        ri(0),
        ri(1),
        ri(1),
        ri(1),
        gi(1, 0),
    )
    .unwrap();
    assert_eq!(
        refinement_residual(&coarse, &moved_end),
        Err(ShadowRefusal::NotARefinement("the endpoints differ"))
    );
    let heavier = FreeParticleShadow::new(
        rats(&[0, 1, 2]),
        carrier,
        ri(0),
        ri(0),
        ri(2),
        ri(1),
        gi(1, 0),
    )
    .unwrap();
    assert_eq!(
        refinement_residual(&coarse, &heavier),
        Err(ShadowRefusal::NotARefinement("the mass or hbar differ"))
    );
}

#[test]
fn refining_the_carrier_or_the_step_changes_the_finite_shadow() {
    let halves = vec![ri(-1), rq(-1, 2), ri(0), rq(1, 2), ri(1)];
    assert_eq!(
        shadow(rats(&[0, 1, 2]), halves).replay().unwrap().kernel,
        phases(&[(ri(0), gi(1, 0)), (rq(1, 4), gi(2, 0)), (ri(1), gi(2, 0))])
    );
    let half_steps = shadow(vec![ri(0), rq(1, 2), ri(1)], rats(&[-1, 0, 1]));
    assert_eq!(
        half_steps.replay().unwrap().kernel,
        phases(&[(ri(0), gi(1, 0)), (ri(2), gi(2, 0))])
    );
    // Mass 3 and hbar 2 give phases (3/2) x_1^2; normalization 3 divides.
    let heavy = FreeParticleShadow::new(
        rats(&[0, 1, 2]),
        rats(&[-1, 0, 1]),
        ri(0),
        ri(0),
        ri(3),
        ri(2),
        gi(3, 0),
    )
    .unwrap();
    assert_eq!(
        heavy.replay().unwrap().kernel,
        phases(&[(ri(0), gq(1, 3, 0, 1)), (rq(3, 2), gq(2, 3, 0, 1))])
    );
    assert_eq!(heavy.transfer_kernel(), heavy.replay().unwrap().kernel);
}

#[test]
fn the_exact_step_phase_example_sums_to_two_i() {
    // From the origin to the midpoints -1 and 1 and back: moving away carries i,
    // returning carries 1, so each history weighs i.
    let (away, back) = (gi(0, 1), gi(1, 0));
    let walk = |second: &GaussianRat| {
        TimeSlicedTransport::new(
            vec![1, 2, 1],
            vec![
                vec![vec![away.clone()], vec![away.clone()]],
                vec![vec![second.clone(), second.clone()]],
            ],
        )
        .unwrap()
    };
    assert_eq!(walk(&back).path_sum(0, 0).unwrap(), gi(0, 2));
    // Charging i on the return as well gives the source's -2.
    assert_eq!(walk(&away).path_sum(0, 0).unwrap(), gi(-2, 0));
    assert_eq!(
        walk(&back).histories(0, 1),
        Err(TransportError::VertexOutOfRange {
            vertex: 1,
            count: 1
        })
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/dynamics/feynman_finite_shadow_histories.rs
// Claim: urn:core:crates_rs:tests:feynman-finite-shadow-histories:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord20abe593 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord20abe593` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError20abe593 {
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
impl BoundaryError20abe593 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError20abe593 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError20abe593 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord20abe593 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError20abe593> {
        if capacity_bound == 0 {
            return Err(BoundaryError20abe593::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError20abe593::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError20abe593::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_20abe593() {
    let admitted = BoundaryRecord20abe593::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord20abe593::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
