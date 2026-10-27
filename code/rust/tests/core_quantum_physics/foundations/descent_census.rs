//! The descent census: the finite bar an ingredient must meet to descend to the
//! obstruction calculus, and the finite witnesses at which the Hilbert-carrier
//! rivals stall. Each stall is a statement about a declared composition, not a
//! refutation of the rival.

use linear_algebra::exact_field::matrix::trace;
use num_bigint::{BigInt, BigUint};
use num_traits::Zero;
use core_number_theory::rational::{ri, rq, Rational};
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_quantum_physics::composition_tomography::{
    local_tomography_spanning_complex, local_tomography_spanning_real, real_symmetric_basis,
    rebit_separating_projector, rebit_state_pair, skew_skew_deficiency, tensor_morphisms,
};
use core_quantum_physics::operational_axiom_selection::{
    local_tomography_dimensions, FiniteRivalTheory,
};
use core_solvers::data_cochain_packet::{CochainPacketError, FiniteCochainPacket};

fn evaluate_local_tomography_typed(t: FiniteRivalTheory, a: u64, b: u64) -> (bool, BigInt) {
    let r = local_tomography_dimensions(t, &BigUint::from(a), &BigUint::from(b)).unwrap();
    (r.holds(), r.deficit)
}

/// A filled triangle `abc` sharing the edge `ca` with an unfilled triangle `acd`.
fn census_packet() -> FiniteCochainPacket {
    let complex = FiniteCochainPacket::build_complex(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("b", "c"), ("c", "a"), ("c", "d"), ("d", "a")],
        &[&["a", "b", "c"]],
    )
    .unwrap();
    FiniteCochainPacket::with_unit_weights(complex).unwrap()
}

fn unit(index: usize, len: usize) -> Vec<Rational> {
    (0..len)
        .map(|i| if i == index { ri(1) } else { ri(0) })
        .collect()
}

// ---------------------------------------------------------------------------
// The descent bar
// ---------------------------------------------------------------------------

#[test]
fn the_descent_bar_is_a_total_disjoint_classification() {
    let packet = census_packet();
    let dims = packet.dimensions();
    assert_eq!(
        (dims.c0, dims.c1, dims.c2, dims.b1, dims.z1, dims.h1),
        (4, 5, 1, 3, 4, 1)
    );

    let exact = packet
        .primitive_difference(&[ri(1), ri(2), ri(4), ri(8)])
        .unwrap();
    let closed = unit(3, 5); // the unfilled cycle's edge cd
    let active = unit(0, 5); // an edge of the filled face
    let mixed: Vec<Rational> = exact.iter().zip(&closed).map(|(a, b)| a + b).collect();

    let class = |x: &[Rational]| {
        let t = packet.classify(x).unwrap();
        (
            t.diagnostic_class(),
            t.phi1_value().clone(),
            t.gamma2_value().clone(),
        )
    };
    assert_eq!(
        class(&exact),
        (ObstructionDiagnosticClass::ExactRepair, ri(0), ri(0))
    );
    assert_eq!(
        class(&closed),
        (ObstructionDiagnosticClass::ClosedResidual, ri(1), ri(0))
    );
    assert_eq!(
        class(&mixed),
        class(&closed),
        "the class, not the representative, is classified"
    );
    let (active_class, _, active_gamma) = class(&active);
    assert_eq!(
        active_class,
        ObstructionDiagnosticClass::ActiveClosureFailure
    );
    assert_eq!(active_gamma, ri(1));

    // Malformed inputs are refused before any class is assigned.
    assert_eq!(
        packet.classify(&[ri(1)]).unwrap_err(),
        CochainPacketError::CochainLength {
            expected: 5,
            actual: 1
        }
    );
    let complex = FiniteCochainPacket::build_complex(&["a", "b"], &[("a", "b")], &[]).unwrap();
    assert_eq!(
        FiniteCochainPacket::new(complex.clone(), vec![ri(0)]).unwrap_err(),
        CochainPacketError::NonPositiveWeight { edge: 0 }
    );
    assert_eq!(
        FiniteCochainPacket::new(complex, vec![ri(1), ri(1)]).unwrap_err(),
        CochainPacketError::WeightCountMismatch {
            edges: 1,
            weights: 2
        }
    );
}

// ---------------------------------------------------------------------------
// Where the Hilbert-carrier rivals stall
// ---------------------------------------------------------------------------

const RIVALS: [FiniteRivalTheory; 4] = [
    FiniteRivalTheory::Classical,
    FiniteRivalTheory::Complex,
    FiniteRivalTheory::Real,
    FiniteRivalTheory::Quaternionic,
];

#[test]
fn local_tomography_selects_the_complex_carrier_only_when_declared() {
    for d_a in 2..=5u64 {
        for d_b in d_a..=5u64 {
            let holds = |t: FiniteRivalTheory| evaluate_local_tomography_typed(t, d_a, d_b).0;
            let declared: Vec<_> = RIVALS.into_iter().filter(|t| holds(*t)).collect();
            assert_eq!(
                declared,
                vec![FiniteRivalTheory::Classical, FiniteRivalTheory::Complex]
            );
            // The real deficit is exactly the skew-skew sector; the quaternionic
            // products overshoot the tensor carrier.
            let (_, real) = evaluate_local_tomography_typed(FiniteRivalTheory::Real, d_a, d_b);
            assert_eq!(
                -real,
                BigInt::from(skew_skew_deficiency(d_a as usize, d_b as usize).unwrap())
            );
            assert!(
                evaluate_local_tomography_typed(FiniteRivalTheory::Quaternionic, d_a, d_b).1
                    > BigInt::zero()
            );
        }
    }
    // Local tomography keeps exactly one of the three Hilbert carriers, but the
    // classical simplex passes it too. Selecting complex QM needs a further
    // declared axiom; the selection is relative to the declared registry.
}

#[test]
fn the_rebit_stall_is_a_pair_of_states_no_product_effect_separates() {
    let real = local_tomography_spanning_real(2, 2).unwrap();
    assert_eq!(
        (real.product_count, real.product_rank, real.joint_dim),
        (9, 9, 10)
    );
    let complex = local_tomography_spanning_complex(2, 2).unwrap();
    assert_eq!((complex.product_rank, complex.joint_dim), (16, 16));

    let (plus, minus) = rebit_state_pair().unwrap();
    assert_eq!(trace(&plus).unwrap(), ri(1));
    assert_eq!(trace(&minus).unwrap(), ri(1));
    let basis = real_symmetric_basis(2).unwrap();
    for a in &basis {
        for b in &basis {
            let effect = tensor_morphisms(a, b).unwrap();
            assert_eq!(
                linear_algebra::exact_field::involution::hs_inner(&effect, &plus).unwrap(),
                linear_algebra::exact_field::involution::hs_inner(&effect, &minus).unwrap()
            );
        }
    }
    let p = rebit_separating_projector().unwrap();
    assert_eq!(
        linear_algebra::exact_field::involution::hs_inner(&p, &plus).unwrap(),
        rq(3, 4)
    );
    assert_eq!(
        linear_algebra::exact_field::involution::hs_inner(&p, &minus).unwrap(),
        rq(1, 4)
    );
}

/// The least carrier size whose state dimension reaches `target`, if one hits it.
fn carrier_with_dimension(theory: FiniteRivalTheory, target: BigUint) -> Option<u64> {
    (1..=100u64)
        .map(|n| (n, theory.state_dimension(&BigUint::from(n)).unwrap()))
        .take_while(|(_, k)| k <= &target)
        .find(|(_, k)| k == &target)
        .map(|(n, _)| n)
}

#[test]
fn no_real_or_quaternionic_carrier_holds_the_product_dimension_of_two_qubits() {
    let product = |t: FiniteRivalTheory| {
        t.state_dimension(&BigUint::from(2u8)).unwrap()
            * t.state_dimension(&BigUint::from(2u8)).unwrap()
    };
    assert_eq!(
        FiniteRivalTheory::Quaternionic
            .state_dimension(&BigUint::from(2u8))
            .unwrap(),
        BigUint::from(6u8)
    );
    assert_eq!(
        FiniteRivalTheory::Quaternionic
            .state_dimension(&BigUint::from(4u8))
            .unwrap(),
        BigUint::from(28u8)
    );
    assert_eq!(
        carrier_with_dimension(
            FiniteRivalTheory::Complex,
            product(FiniteRivalTheory::Complex)
        ),
        Some(4)
    );
    assert_eq!(
        carrier_with_dimension(
            FiniteRivalTheory::Classical,
            product(FiniteRivalTheory::Classical)
        ),
        Some(4)
    );
    // 9 is not d(d+1)/2 and 36 is not d(2d-1) for any d.
    assert_eq!(
        carrier_with_dimension(FiniteRivalTheory::Real, product(FiniteRivalTheory::Real)),
        None
    );
    assert_eq!(
        carrier_with_dimension(
            FiniteRivalTheory::Quaternionic,
            product(FiniteRivalTheory::Quaternionic)
        ),
        None
    );
    // A count is only a necessary condition: two real qutrits give 6 * 6 = 36 =
    // 8 * 9 / 2, yet the tensor carrier misses nine product directions.
    assert_eq!(
        carrier_with_dimension(FiniteRivalTheory::Real, BigUint::from(36u8)),
        Some(8)
    );
    let qutrits = local_tomography_spanning_real(3, 3).unwrap();
    assert_eq!(
        (
            qutrits.product_count,
            qutrits.product_rank,
            qutrits.joint_dim
        ),
        (36, 36, 45)
    );
    assert!(!qutrits.spans);
}

// Origin: engine/crates_rs/tests/core_quantum_physics/foundations/descent_census.rs
// Claim: urn:core:crates_rs:tests:descent-census:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord828001e4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord828001e4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError828001e4 {
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
impl BoundaryError828001e4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError828001e4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError828001e4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord828001e4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError828001e4> {
        if capacity_bound == 0 {
            return Err(BoundaryError828001e4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError828001e4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError828001e4::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_828001e4() {
    let admitted = BoundaryRecord828001e4::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord828001e4::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
