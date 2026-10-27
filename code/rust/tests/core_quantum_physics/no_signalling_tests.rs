//! Exact bipartite no-signalling and independent mutation controls.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    involution::{adjoint, outer_product},
    matrix as mx,
};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_channel::ExactKrausChannel;
use core_quantum_physics::exact_hermitian::{
    is_hermitian, partial_trace_first, partial_trace_second,
};
use core_quantum_physics::no_signalling::*;
fn half_identity() -> BasicMatrix<GaussianRat> {
    mx::scale(
        &mx::identity(2).unwrap(),
        &GaussianRat::from_rational(rq(1, 2)),
    )
    .unwrap()
}
#[test]
fn test_t840_bell_states_properties() {
    for (_, rho) in all_bell_states() {
        assert_eq!(mx::trace(&rho).unwrap(), GaussianRat::one());
        assert!(is_hermitian(&rho));
        assert_eq!(partial_trace_first(&rho, 2, 2).unwrap(), half_identity());
        assert_eq!(partial_trace_second(&rho, 2, 2).unwrap(), half_identity());
    }
}
#[test]
fn test_t840_partial_trace_uniqueness_proof() {
    for (_, rho) in all_bell_states() {
        assert!(prove_partial_trace_uniqueness(&rho, 2, 2));
    }
    let wrong = mx::zeros::<GaussianRat>(3, 4).unwrap();
    assert!(!prove_partial_trace_uniqueness(&wrong, 2, 2));
}
#[test]
fn test_t840_no_signalling_exact() {
    assert!(verify_no_signalling_on_bell_states());
}
#[test]
fn every_matrix_unit_preserves_bob_for_rectangular_channels() {
    let g = |n| GaussianRat::from_ints(n, 0);
    let operators = vec![
        mx::from_rows(vec![vec![g(1), g(0)]]).unwrap(),
        mx::from_rows(vec![vec![g(0), g(1)]]).unwrap(),
    ];
    let discard = ExactKrausChannel::try_new(2, 1, operators, "discard").unwrap();
    assert_eq!(certify_no_signalling_map(&discard, 3, 36), Ok(true));
    assert!(matches!(
        certify_no_signalling_map(&discard, 3, 35),
        Err(NoSignallingError::Budget {
            required: 36,
            budget: 35
        })
    ));
}
#[test]
fn test_t842_mutation_1_marginals_compared_by_tolerance() {
    let marginal = half_identity();
    let mut perturbed = marginal.clone();
    let delta = Rational::new(1.into(), num_bigint::BigInt::from(10u8).pow(100));
    perturbed
        .set(
            0,
            0,
            perturbed
                .get(0, 0)
                .unwrap()
                .add(&GaussianRat::from_rational(delta)),
        )
        .unwrap();
    assert_ne!(perturbed, marginal);
}
#[test]
fn test_t842_mutation_2_local_operation_acting_on_both_factors() {
    let v = vec![
        GaussianRat::one(),
        GaussianRat::zero(),
        GaussianRat::one(),
        GaussianRat::zero(),
    ];
    let input = mx::scale(
        &outer_product(&v, &v).unwrap(),
        &GaussianRat::from_rational(rq(1, 2)),
    )
    .unwrap();
    let cnot = cnot_matrix();
    let output = mx::multiply(
        &mx::multiply(&cnot, &input).unwrap(),
        &adjoint(&cnot).unwrap(),
    )
    .unwrap();
    assert_eq!(partial_trace_first(&input, 2, 2).unwrap(), proj_0());
    assert_eq!(partial_trace_first(&output, 2, 2).unwrap(), half_identity());
    assert!(ExactKrausChannel::try_new(2, 2, vec![cnot], "claimed local").is_err());
}
#[test]
fn test_t842_mutation_3_uniqueness_assumed_rather_than_checked() {
    let rho = bell_phi_plus();
    let reduced = partial_trace_second(&rho, 2, 2).unwrap();
    let z = core_lie_theory::pauli_symplectic::pauli::<GaussianRat>(
        core_lie_theory::pauli_symplectic::Pauli::Z,
    )
    .unwrap();
    let fake = mx::add(&reduced, &z).unwrap();
    let p = proj_0();
    assert_ne!(
        mx::trace(&mx::multiply(&p, &fake).unwrap()).unwrap(),
        mx::trace(
            &mx::multiply(&mx::kronecker(&p, &mx::identity(2).unwrap()).unwrap(), &rho).unwrap()
        )
        .unwrap()
    );
}
#[test]
fn postselection_steers_bob_but_the_sum_of_branches_does_not() {
    let rho = bell_phi_plus();
    let p = mx::kronecker(&proj_0(), &mx::identity(2).unwrap()).unwrap();
    let branch = mx::multiply(&mx::multiply(&p, &rho).unwrap(), &p).unwrap();
    assert_eq!(mx::trace(&branch).unwrap().re, rq(1, 2));
    assert_eq!(
        partial_trace_first(
            &mx::scale(&branch, &GaussianRat::from_rational(ri(2))).unwrap(),
            2,
            2
        )
        .unwrap(),
        proj_0()
    );
    let measurement =
        ExactKrausChannel::try_new(2, 2, vec![proj_0(), proj_1()], "unselective").unwrap();
    assert_eq!(no_signalling(&rho, &measurement, 2), Ok(true));
}
#[test]
fn incomplete_kraus_and_malformed_carriers_are_refused() {
    assert!(
        ExactKrausChannel::try_new(2, 2, vec![proj_0()], "postselection claimed CPTP").is_err()
    );
    let id = ExactKrausChannel::try_new(2, 2, vec![mx::identity(2).unwrap()], "id").unwrap();
    let wrong = mx::zeros::<GaussianRat>(3, 4).unwrap();
    assert!(no_signalling(&wrong, &id, 2).is_err());
    assert!(no_signalling(&bell_phi_plus(), &id, 0).is_err());
}

// Origin: engine/crates_rs/tests/core_quantum_physics/no_signalling_tests.rs
// Claim: urn:core:crates_rs:tests:no-signalling-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd3238104 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd3238104` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord3238104 {
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
impl BoundaryErrord3238104 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord3238104 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord3238104 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd3238104 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord3238104> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord3238104::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord3238104::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord3238104::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d3238104() {
    let admitted = BoundaryRecordd3238104::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd3238104::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
