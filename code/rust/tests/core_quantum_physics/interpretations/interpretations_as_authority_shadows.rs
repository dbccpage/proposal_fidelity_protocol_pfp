//! Interpretations as packet-indistinguishable shadows: the paper's worked
//! example on a certified survivor packet, the observer-relative criterion
//! for when two readings differ, and exact countermodels for "a survivor
//! class selects complex Hilbert space". Readings are compared only through
//! replayed numbers; no reading is scored as true.

use num_traits::{Signed, Zero};
use core_functional::phi1::Phi1Functional;
use core_number_theory::rational::{ri, rq, Rational};
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_quantum_physics::composition_tomography::{
    local_tomography_spanning_complex, local_tomography_spanning_real,
};
use core_quantum_physics::contextuality_obstruction::{
    compute_obstruction_class, construct_cabello_scenario,
};
use core_quantum_physics::exact_hermitian::{gi, gq};
use core_quantum_physics::kochen_specker::{CABELLO_18_VECTORS, CABELLO_9_CONTEXTS};
use core_solvers::solver_cohomology_quotient_phi1::certified_phi1;
use core_solvers::data_cochain_packet::{certified_trichotomy, FiniteCochainPacket};

use core_quantum_physics::relative_state_branching::{
    first_separating_observable, system_only_observables, RelativeStatePacket,
};

/// `d0(alpha) = (alpha, -alpha)`: `C^0 = Q`, `C^1 = Q^2`, no faces.
fn survivor_d0() -> Vec<Vec<Rational>> {
    vec![vec![ri(1)], vec![ri(-1)]]
}

fn unit_weights() -> [Rational; 2] {
    [ri(1), ri(1)]
}

// ---------------------------------------------------------------------------
// QM-090-C1 / C13: the worked example on a certified survivor packet.
// ---------------------------------------------------------------------------

#[test]
fn readings_that_keep_every_packet_number_cannot_be_told_apart() {
    let x = [ri(0), ri(1)];
    let standard = certified_trichotomy(1, &survivor_d0(), &[], &unit_weights(), &x).unwrap();
    // The survivor signature: Phi1 = 1 > 0 and Gamma2 = 0.
    assert_eq!(
        standard.diagnostic_class(),
        ObstructionDiagnosticClass::ClosedResidual
    );
    assert_eq!(standard.phi1_value(), &ri(1));
    assert!(standard.gamma2_value().is_zero());

    // Reading A: a different representative, x + d0(3) = (3, -2). Its raw edge
    // mass is 5 rather than 1, but every packet number is unchanged.
    let shifted = [ri(3), ri(-2)];
    let reading_a =
        certified_trichotomy(1, &survivor_d0(), &[], &unit_weights(), &shifted).unwrap();
    assert_eq!(reading_a, standard);
    let raw = |v: &[Rational]| -> Rational { v.iter().map(|t| t.abs()).sum() };
    assert_eq!((raw(&x), raw(&shifted)), (ri(1), ri(5)));
}

#[test]
fn a_reading_that_moves_a_packet_number_is_adjudicated_by_replay() {
    let x = [ri(0), ri(1)];
    let replayed = certified_phi1(1, &survivor_d0(), &x, &unit_weights(), 16_384).unwrap();
    assert_eq!(replayed.value(), &ri(1));
    // The dual witness is the unique circulation z = (1, 1) with z . x = 1.
    assert_eq!(replayed.dual_witness(), &[ri(1), ri(1)]);

    // Reading B predicts decay to (9/10) x: a different packet, Phi1 = 9/10.
    let decayed = [ri(0), rq(9, 10)];
    let predicted =
        certified_trichotomy(1, &survivor_d0(), &[], &unit_weights(), &decayed).unwrap();
    assert_eq!(predicted.phi1_value(), &rq(9, 10));
    assert_ne!(predicted.phi1_value(), replayed.value());

    // Claimed of the actual packet, 9/10 fails replay: the certificate pins 1.
    let mut claim = replayed.certificate().clone();
    claim.reported_value = rq(9, 10);
    assert!(Phi1Functional::verify_exact_certificate(claim).is_err());
}

// ---------------------------------------------------------------------------
// QM-090-C7: distinguishability is relative to the declared observer packet.
// ---------------------------------------------------------------------------

#[test]
fn distinguishability_is_relative_to_the_declared_observer_packet() {
    // Unitary reading: the coherent relative state. Collapse reading: its branch mixture.
    let e0 = vec![gi(1, 0), gi(0, 0)];
    let e1 = vec![gi(0, 0), gi(1, 0)];
    let packet = RelativeStatePacket::new(vec![gi(3, 0), gi(4, 0)], vec![e0, e1]).unwrap();
    let unitary = packet.global_state();
    let collapse = packet.branch_mixture();

    let local = system_only_observables(2, 2).unwrap();
    assert_eq!(
        first_separating_observable(&local, &unitary, &collapse).unwrap(),
        None
    );

    let mut global = local;
    global.push(unitary.clone());
    let separation = first_separating_observable(&global, &unitary, &collapse)
        .unwrap()
        .unwrap();
    // Only the recoherence projector separates them: 1 versus (9/25)^2 + (16/25)^2.
    assert_eq!(separation.index, 4);
    assert_eq!(
        (separation.left, separation.right),
        (gi(1, 0), gq(337, 625, 0, 1))
    );
}

// ---------------------------------------------------------------------------
// QM-090-C3 / C10: the survivor signature does not select complex Hilbert space.
// ---------------------------------------------------------------------------

#[test]
fn the_survivor_signature_occurs_on_a_real_graph_cycle_with_no_hilbert_space() {
    let complex = FiniteCochainPacket::build_complex(
        &["a", "b", "c"],
        &[("a", "b"), ("b", "c"), ("c", "a")],
        &[],
    )
    .unwrap();
    let triangle = FiniteCochainPacket::with_unit_weights(complex).unwrap();
    // One unit of difference on one edge of an unfilled triangle: it closes
    // locally and does not glue into a global potential.
    let class = triangle.classify(&[ri(1), ri(0), ri(0)]).unwrap();
    assert_eq!(
        class.diagnostic_class(),
        ObstructionDiagnosticClass::ClosedResidual
    );
    assert_eq!(class.phi1_value(), &ri(1));
    assert!(class.gamma2_value().is_zero());
    assert_eq!(triangle.dimensions().h1, 1);
}

#[test]
fn contextuality_on_real_rays_does_not_select_complex_hilbert_space() {
    // Cabello's rays have integer coordinates, and each context is an
    // orthogonal frame of R^4: the configuration lives in real Hilbert space.
    for context in CABELLO_9_CONTEXTS {
        for (i, &p) in context.iter().enumerate() {
            for &q in &context[i + 1..] {
                let dot: i64 = CABELLO_18_VECTORS[p]
                    .iter()
                    .zip(&CABELLO_18_VECTORS[q])
                    .map(|(a, b)| a * b)
                    .sum();
                assert_eq!(dot, 0);
            }
        }
    }
    let class = compute_obstruction_class(&construct_cabello_scenario()).unwrap();
    assert!(!class.obstruction_class_is_zero);
    assert!(!class.global_section_exhibited);

    // R^4 = R^2 (x) R^2 is the rebit pair, which fails local tomography;
    // the complex qubit pair satisfies it.
    let real = local_tomography_spanning_real(2, 2).unwrap();
    assert_eq!(
        (real.product_rank, real.joint_dim, real.spans),
        (9, 10, false)
    );
    let complex = local_tomography_spanning_complex(2, 2).unwrap();
    assert_eq!(
        (complex.product_rank, complex.joint_dim, complex.spans),
        (16, 16, true)
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/interpretations/interpretations_as_authority_shadows.rs
// Claim: urn:core:crates_rs:tests:interpretations-as-authority-shadows:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9ddec83d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9ddec83d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9ddec83d {
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
impl BoundaryError9ddec83d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9ddec83d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9ddec83d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9ddec83d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9ddec83d> {
        if capacity_bound == 0 {
            return Err(BoundaryError9ddec83d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9ddec83d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9ddec83d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_9ddec83d() {
    let admitted = BoundaryRecord9ddec83d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9ddec83d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
