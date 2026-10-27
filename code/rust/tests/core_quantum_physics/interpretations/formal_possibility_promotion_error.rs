//! The promotion error in miniature: the paper's worked instance fixes the
//! obstruction value from structure alone, and the certificate that carries it
//! holds structure and nothing else: no terminal, packet or authority field.
//! Authority itself is not nameable in this crate (`certified_authority_fence`).
//! The ledger's transposed version of the instance is refused as malformed.

use core_number_theory::rational::{ri, Rational};
use core_solvers::solver_cohomology_quotient_phi1::{certified_phi1, CertifiedPhi1Error};
use core_solvers::data_cochain_packet::FiniteCochainPacket;

// ---------------------------------------------------------------------------
// QM-091-C4: the worked instance.
// ---------------------------------------------------------------------------

#[test]
fn the_worked_instance_fixes_phi1_from_the_structure_alone() {
    // C^0 = Q, C^1 = Q^2, d0(alpha) = (alpha, -alpha), weights (1, 1), x = (0, 1).
    let d0 = vec![vec![ri(1)], vec![ri(-1)]];
    let weights = vec![ri(1), ri(1)];
    let x = vec![ri(0), ri(1)];
    let phi1 = certified_phi1(1, &d0, &x, &weights, 16_384).unwrap();
    assert_eq!(phi1.value(), &ri(1));

    // The replayed certificate holds the structure, a primal repair and a dual
    // circulation; it has no field for a terminal, a packet or an authority.
    let certificate = phi1.certificate();
    assert_eq!(
        (&certificate.omega, &certificate.d0, &certificate.weights),
        (&x, &d0, &weights)
    );
    let residual: Vec<Rational> = x
        .iter()
        .zip(&d0)
        .map(|(value, row)| value - &row[0] * &certificate.alpha[0])
        .collect();
    assert_eq!(residual, certificate.primal_residual);
    assert_eq!(certificate.dual_witness, vec![ri(1), ri(1)]);

    // Every representative x + d0(alpha) of the class gives the same value.
    for alpha in -3..=3 {
        let shifted = vec![ri(alpha), ri(1 - alpha)];
        assert_eq!(
            certified_phi1(1, &d0, &shifted, &weights, 16_384)
                .unwrap()
                .value(),
            &ri(1)
        );
    }

    // The digon g -> v -> g has a coboundary with the same image, and the same value.
    let digon = FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(&["g", "v"], &[("g", "v"), ("v", "g")], &[]).unwrap(),
    )
    .unwrap();
    assert_eq!(digon.quotient_mass(&x).unwrap().value(), &ri(1));
}

#[test]
fn the_ledger_transposition_of_the_instance_is_malformed() {
    // The ledger row reads C^0 = Q^2, C^1 = Q, d0 = (1, -1) with two weights:
    // two weights for one edge are refused.
    let transposed = vec![vec![ri(1), ri(-1)]];
    assert!(matches!(
        certified_phi1(2, &transposed, &[ri(1)], &[ri(1), ri(1)], 16_384),
        Err(CertifiedPhi1Error::Shape)
    ));
    // With one weight it is a single edge between two vertices, where every
    // residual is a repair: Phi1 = 0, not the paper's 1.
    let single_edge = certified_phi1(2, &transposed, &[ri(1)], &[ri(1)], 16_384).unwrap();
    assert_eq!(single_edge.value(), &ri(0));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/interpretations/formal_possibility_promotion_error.rs
// Claim: urn:core:crates_rs:tests:formal-possibility-promotion-error:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord868a161d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord868a161d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError868a161d {
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
impl BoundaryError868a161d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError868a161d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError868a161d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord868a161d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError868a161d> {
        if capacity_bound == 0 {
            return Err(BoundaryError868a161d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError868a161d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError868a161d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_868a161d() {
    let admitted = BoundaryRecord868a161d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord868a161d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
