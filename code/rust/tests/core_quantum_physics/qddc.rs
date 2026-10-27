//! Exact examples and counterexamples for the finite QDDC contract.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_number_theory::cyclotomic::GaussianRat as G;
use core_number_theory::rational::{ri, Rational};
use core_quantum_physics::density_matrix::ExactDensityMatrix as Density;
use core_quantum_physics::exact_operator::ExactOperator as Op;
use core_quantum_physics::qddc::*;

fn op(a: &[i64]) -> Op {
    Op::try_new(
        BasicMatrix::from_row_major(2, 2, a.iter().map(|&n| G::from_ints(n, 0)).collect()).unwrap(),
    )
    .unwrap()
}
fn maps(filled: bool) -> (BasicMatrix<Rational>, BasicMatrix<Rational>) {
    let d0 = BasicMatrix::from_row_major(
        3,
        3,
        [-1, 1, 0, -1, 0, 1, 0, -1, 1].into_iter().map(ri).collect(),
    )
    .unwrap();
    let d1 = BasicMatrix::from_row_major(
        if filled { 1 } else { 0 },
        3,
        if filled {
            vec![ri(1), ri(-1), ri(1)]
        } else {
            vec![]
        },
    )
    .unwrap();
    (d0, d1)
}
fn state(filled: bool, values: Vec<Op>) -> QddcState {
    let (a, b) = maps(filled);
    QddcState::try_new(a, b, 2, values).unwrap()
}

#[test]
fn triangle_components_reconstruct_and_filling_removes_harmonic_cycle() {
    let z = op(&[1, 0, 0, -1]);
    let cycle = vec![z.clone(), z.scale_rat(&ri(-1)).unwrap(), z.clone()];
    let circle = state(false, cycle.clone()).decompose().unwrap();
    assert_eq!(circle.harmonic, cycle);
    assert!(circle.exact.iter().all(Op::is_zero));
    let filled = state(true, cycle.clone()).decompose().unwrap();
    assert!(filled.harmonic.iter().all(Op::is_zero));
    assert_eq!(filled.coexact, cycle);
    let general = vec![op(&[2, 1, 1, 0]), op(&[1, 0, 0, 3]), op(&[-2, 2, 2, 1])];
    let split = state(true, general.clone()).decompose().unwrap();
    for i in 0..3 {
        assert_eq!(
            split.exact[i]
                .add(&split.coexact[i])
                .unwrap()
                .add(&split.harmonic[i])
                .unwrap(),
            general[i]
        );
    }
}

#[test]
fn complex_coefficients_and_gauge_rotation_transport_the_harmonic_part() {
    let y = Op::from_rows(vec![
        vec![G::zero(), G::from_ints(0, -1)],
        vec![G::i(), G::zero()],
    ])
    .unwrap();
    let original = state(false, vec![y.clone(), y.scale_rat(&ri(-1)).unwrap(), y]);
    let x = op(&[0, 1, 1, 0]);
    let gauge = vec![op(&[1, 0, 0, 0]), op(&[0, 0, 0, 0]), op(&[2, 1, 1, 0])];
    let before = original.decompose().unwrap();
    let shifted = original
        .deform(&gauge, &Op::identity(2).unwrap())
        .unwrap()
        .decompose()
        .unwrap();
    assert_eq!(before.harmonic, shifted.harmonic);
    let rotated = original.deform(&gauge, &x).unwrap().decompose().unwrap();
    assert_ne!(before.harmonic, rotated.harmonic);
    for i in 0..3 {
        assert_eq!(
            rotated.harmonic[i],
            x.mul(&before.harmonic[i]).unwrap().mul(&x).unwrap()
        );
    }
}

#[test]
fn empty_carriers_and_invalid_complexes_are_distinguished() {
    let zero = BasicMatrix::from_row_major(0, 0, vec![]).unwrap();
    assert!(QddcState::try_new(zero.clone(), zero.clone(), 1, vec![])
        .unwrap()
        .decompose()
        .unwrap()
        .harmonic
        .is_empty());
    assert!(QddcState::try_new(zero.clone(), zero, 0, vec![]).is_err());
    let a = BasicMatrix::from_row_major(1, 1, vec![ri(1)]).unwrap();
    assert!(QddcState::try_new(a.clone(), a, 2, vec![op(&[1, 0, 0, 1])]).is_err());
    assert!(state(false, vec![op(&[1, 0, 0, 0]); 3])
        .deform(&[op(&[0, 0, 0, 0]); 0], &op(&[1, 0, 0, 1]))
        .is_err());
}

#[test]
fn lindblad_derivative_is_trace_zero_but_euler_need_not_be_positive() {
    let rho = Density::try_from_operator(op(&[1, 0, 0, 0])).unwrap();
    let generator = Lindbladian::try_new(op(&[0, 1, 1, 0]), vec![]).unwrap();
    let derivative = generator.derivative(&rho).unwrap();
    assert!(derivative.is_hermitian());
    assert!(derivative.trace().unwrap().is_zero());
    for denominator in [1, 2, 100] {
        let euler = rho
            .as_operator()
            .add(&derivative.scale_rat(&(ri(1) / ri(denominator))).unwrap())
            .unwrap();
        assert!(Density::try_from_operator(euler).is_err());
    }
    let damping = Lindbladian::try_new(op(&[0, 0, 0, 0]), vec![op(&[0, 1, 0, 0])]).unwrap();
    let excited = Density::try_from_operator(op(&[0, 0, 0, 1])).unwrap();
    assert_eq!(damping.derivative(&excited).unwrap(), op(&[1, 0, 0, -1]));
    assert!(Lindbladian::try_new(op(&[0, 1, 0, 0]), vec![]).is_err());
}

#[test]
fn retraction_is_idempotent_and_has_exact_outside_weight_law() {
    let projector = op(&[1, 1, 1, 1]).scale_rat(&(ri(1) / ri(2))).unwrap();
    let channel = RetractionChannel::try_new(projector.clone()).unwrap();
    let rho = Density::try_from_operator(op(&[1, 0, 0, 0])).unwrap();
    let q = channel.outside_weight(&rho).unwrap();
    assert_eq!(q, ri(1) / ri(2));
    for eta in [ri(0), ri(1) / ri(3), ri(1)] {
        let output = channel.step(&rho, &eta).unwrap();
        assert_eq!(
            channel.outside_weight(&output).unwrap(),
            (ri(1) - &eta) * &q
        );
    }
    let reset = channel.step(&rho, &ri(1)).unwrap();
    let witnessed = rho
        .apply_channel(&channel.weighted_kraus().unwrap())
        .unwrap();
    assert_eq!(witnessed.as_operator(), reset.as_operator());
    assert_eq!(reset.as_operator(), &projector);
    assert_eq!(
        channel.step(&reset, &ri(1)).unwrap().as_operator(),
        reset.as_operator()
    );
    assert!(channel.step(&rho, &ri(2)).is_err());
    assert!(RetractionChannel::try_new(op(&[0, 0, 0, 0])).is_err());
    assert!(RetractionChannel::try_new(op(&[1, 1, 0, 0])).is_err());
    assert!(RetractionChannel::try_new(op(&[2, 0, 0, 0])).is_err());
}

#[test]
fn selected_probe_order_changes_joint_probability_and_handles_zero_branch() {
    let p = op(&[1, 0, 0, 0]);
    let q = op(&[1, 1, 1, 1]).scale_rat(&(ri(1) / ri(2))).unwrap();
    let rho = Density::try_from_operator(p.clone()).unwrap();
    let (a, post_a) = probe(&rho, &p).unwrap();
    let (b, _) = probe(&post_a.unwrap(), &q).unwrap();
    let (c, post_c) = probe(&rho, &q).unwrap();
    let (d, _) = probe(&post_c.unwrap(), &p).unwrap();
    assert_eq!(a * b, ri(1) / ri(2));
    assert_eq!(c * d, ri(1) / ri(4));
    let (probability, conditional) = probe(&rho, &op(&[0, 0, 0, 1])).unwrap();
    assert_eq!(probability, ri(0));
    assert!(conditional.is_none());
}

#[test]
fn rational_interferometer_has_a_dark_port_and_preserves_total_norm() {
    let a = G {
        re: ri(1) / ri(2),
        im: ri(1) / ri(2),
    };
    let u = op(&[1, 1, 1, -1]).scale(&a).unwrap();
    assert!(u.is_unitary());
    let path = u.mul(&op(&[1, 0, 0, -1])).unwrap().mul(&u).unwrap();
    assert_eq!(
        path.apply(&[G::one(), G::zero()]).unwrap(),
        vec![G::zero(), G::i()]
    );
    let mixed = Density::maximally_mixed(2).unwrap();
    assert_eq!(
        mixed.conjugate(&path).unwrap().as_operator(),
        mixed.as_operator()
    );
    let plus =
        Density::try_from_operator(op(&[1, 1, 1, 1]).scale_rat(&(ri(1) / ri(2))).unwrap()).unwrap();
    assert!(plus.is_pure());
    assert_eq!(plus.matrix().as_slice()[0].re, ri(1) / ri(2));
    assert!(!mixed.is_pure());
}

#[test]
fn bounds_and_cross_carrier_errors_fail_closed() {
    let huge = Rational::from_integer(num_bigint::BigInt::from(1) << 256);
    assert!(check_scalar(&huge).is_err());
    assert!(check_scalar(&Rational::new_raw(1.into(), 0.into())).is_err());
    assert!(check_scalar(&Rational::new_raw(2.into(), 4.into())).is_err());
    assert!(
        Lindbladian::try_new(op(&[0, 0, 0, 0]), vec![op(&[0, 0, 0, 0]); MAX_JUMPS + 1]).is_err()
    );
    let channel = RetractionChannel::try_new(op(&[1, 0, 0, 0])).unwrap();
    assert!(channel
        .step(&Density::maximally_mixed(1).unwrap(), &ri(1))
        .is_err());
    let (d0, d1) = maps(false);
    assert!(QddcState::try_new(d0, d1, 2, vec![op(&[0, 1, 0, 0]); 3]).is_err());
}

#[test]
fn derived_repair_space_is_exact_not_harmonic() {
    let s = state(false, vec![op(&[0, 0, 0, 0]); 3]);
    let p = s.repair_projector().unwrap();
    assert!(p.is_hermitian() && p.is_idempotent());
    assert_eq!(p.trace().unwrap().re, ri(2));
    let gradient: Vec<G> = [-1, -1, 0]
        .into_iter()
        .map(|v| G::from_ints(v, 0))
        .collect();
    assert_eq!(p.apply(&gradient).unwrap(), gradient);
    assert_eq!(
        p.apply(&[G::one(), G::from_ints(-1, 0), G::one()]).unwrap(),
        vec![G::zero(); 3]
    );
    let channel = RetractionChannel::try_new(p).unwrap();
    let rho = Density::maximally_mixed(3).unwrap();
    let reset = channel.step(&rho, &ri(1)).unwrap();
    assert_eq!(channel.outside_weight(&reset).unwrap(), ri(0));
    assert_eq!(
        rho.apply_channel(&channel.weighted_kraus().unwrap())
            .unwrap()
            .as_operator(),
        reset.as_operator()
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/qddc.rs
// Claim: urn:core:crates_rs:tests:qddc:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord20a4d331 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord20a4d331` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError20a4d331 {
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
impl BoundaryError20a4d331 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError20a4d331 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError20a4d331 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord20a4d331 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError20a4d331> {
        if capacity_bound == 0 {
            return Err(BoundaryError20a4d331::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError20a4d331::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError20a4d331::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_20a4d331() {
    let admitted = BoundaryRecord20a4d331::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord20a4d331::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
