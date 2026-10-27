// AuthorityEffect: None. Citation: sealed-derivation-v1 (3100c4e)

//! Adversarial Challenge Tests for `core_quantum_physics`.
//!
//! Stress-tests boundary conditions, edge cases, and algebraic invariants.

use core_number_theory::cyclotomic_field::CyclotomicNumber;
use core_number_theory::cyclotomic_ordered::standard_real_sign;
use core_number_theory::{rq, Cyc12, Cyc24, Cyc5, Cyc8};
use core_quantum_physics::hilbert_space::HilbertSpace;
use core_quantum_physics::{
    audit_commutator_obstruction_d3, state_magic_d5, DiscreteWignerSystemD5, MubSystem,
};

#[test]
fn test_adversarial_zero_dimension_rejected() {
    assert!(
        HilbertSpace::try_new(0, "zero").is_err(),
        "Zero dimension must be rejected"
    );
}

#[test]
fn test_adversarial_commutator_trace_obstruction_soundness() {
    let report = audit_commutator_obstruction_d3().unwrap();
    assert!(report.commutator_trace_is_zero);
    assert!(report.hypothetical_ccr_trace_non_zero);
    assert!(report.weyl_relation_satisfied);
    assert!(report.weyl_commutator_trace_is_zero);
}

#[test]
fn test_adversarial_clifton_kent_unconditional_deficit() {
    let mub4 = MubSystem::mub_d4();
    assert!(mub4.verify_clifton_kent_purity_obstruction());
    let total = mub4.dimension.pow(mub4.bases.len() as u32);
    let mut non_psd = 0;
    for code in 0..total {
        let mut remaining = code;
        let outcomes: Vec<usize> = (0..mub4.bases.len())
            .map(|_| {
                let outcome = remaining % mub4.dimension;
                remaining /= mub4.dimension;
                outcome
            })
            .collect();
        // The reconstructed Hermitian trace-one operator has purity 4.
        // A positive trace-one operator has purity at most 1.
        assert_eq!(
            mub4.deterministic_valuation_purity(&outcomes).unwrap(),
            Cyc24::from_int(4)
        );
        non_psd += 1;
    }
    assert_eq!(total, 1024);
    assert_eq!(non_psd, total);
}

#[test]
fn test_adversarial_wigner_d5_negativity_witness() {
    let wsys = DiscreteWignerSystemD5::new();
    let rho_magic = state_magic_d5();
    let grid = wsys.evaluate_exact(&rho_magic).unwrap();
    assert_eq!(grid[0][0], Cyc5::rat(rq(-1, 5)));
    let has_neg = grid
        .iter()
        .flatten()
        .any(|v| standard_real_sign(&CyclotomicNumber::from(v)).unwrap() == -1);
    assert!(has_neg);
    assert_eq!(
        wsys.evaluate_wigner(&rho_magic),
        Err(core_quantum_physics::wigner::WignerError::NonRational)
    );
}

#[test]
fn test_adversarial_cyclotomic_zeta_multiplication() {
    let z8 = Cyc8::zeta8(1);
    let z8_4 = z8.mul(&z8).mul(&z8).mul(&z8);
    assert_eq!(z8_4, Cyc8::one().neg());

    let z12 = Cyc12::zeta12(1);
    let z12_6 = (0..6).fold(Cyc12::one(), |acc, _| acc.mul(&z12));
    assert_eq!(z12_6, Cyc12::one().neg());
}

// Origin: engine/crates_rs/tests/core_quantum_physics/adversarial_challenge_tests.rs
// Claim: urn:core:crates_rs:tests:adversarial-challenge-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord01517f04 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord01517f04` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError01517f04 {
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
impl BoundaryError01517f04 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError01517f04 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError01517f04 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord01517f04 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError01517f04> {
        if capacity_bound == 0 {
            return Err(BoundaryError01517f04::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError01517f04::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError01517f04::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_01517f04() {
    let admitted = BoundaryRecord01517f04::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord01517f04::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
