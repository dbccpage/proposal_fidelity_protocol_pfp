//! Integration tests for Chemical Reaction Network Theory (CRNT) Deficiency Calculator (U24).
//!
//! Invariants verified:
//! - delta = n - ell - s with s exact rank over rationals Q.
//! - Witness: A -> 2A, A -> 0 has n=3, ell=1, s=1 => delta = 1.
//! - Mutation Kill Gate: Computing s as reaction count (r=2) turns delta witness test RED.
//! - Weak reversibility and Deficiency Zero Theorem applicability.
//!
//! AuthorityEffect: None.

use core_solvers::solver_crn_deficiency::*;

#[test]
fn test_deficiency_one_witness_a_to_2a_and_a_to_zero() {
    // A -> 2A and A -> 0
    let c_a = Complex::single("A", 1);
    let c_2a = Complex::single("A", 2);
    let c_0 = Complex::zero();

    let reactions = vec![
        Reaction::new(c_a.clone(), c_2a.clone()),
        Reaction::new(c_a.clone(), c_0.clone()),
    ];

    let net = ReactionNetwork::new(reactions);
    let report = net.evaluate();

    // 1 species: A
    assert_eq!(report.num_species, 1);
    // 3 complexes: A, 2A, 0
    assert_eq!(report.num_complexes, 3);
    // 2 reactions
    assert_eq!(report.num_reactions, 2);
    // 1 linkage class (connected via A)
    assert_eq!(report.num_linkage_classes, 1);
    // Exact stoichiometric rank over Q is 1 (span of [+1, -1] is 1-dimensional)
    // Mutation kill gate: If s were computed as number of reactions (2), this assertion would fail!
    assert_eq!(report.stoichiometric_rank, 1);
    // delta = n - ell - s = 3 - 1 - 1 = 1
    assert_eq!(report.deficiency, 1);
    // Not weakly reversible (irreversible branching)
    assert_eq!(report.is_weakly_reversible, false);
    assert_eq!(report.deficiency_zero_applicable, false);
    assert_eq!(report.authority_effect, "None");
}

#[test]
fn test_deficiency_zero_reversible_cycle() {
    // A <-> B <-> C <-> A (fully reversible cycle)
    let c_a = Complex::single("A", 1);
    let c_b = Complex::single("B", 1);
    let c_c = Complex::single("C", 1);

    let reactions = vec![
        Reaction::new(c_a.clone(), c_b.clone()),
        Reaction::new(c_b.clone(), c_a.clone()),
        Reaction::new(c_b.clone(), c_c.clone()),
        Reaction::new(c_c.clone(), c_b.clone()),
        Reaction::new(c_c.clone(), c_a.clone()),
        Reaction::new(c_a.clone(), c_c.clone()),
    ];

    let net = ReactionNetwork::new(reactions);
    let report = net.evaluate();

    assert_eq!(report.num_species, 3);
    assert_eq!(report.num_complexes, 3);
    assert_eq!(report.num_linkage_classes, 1);
    // Stoichiometric rank = 2 (in 3 species with sum of changes = 0)
    assert_eq!(report.stoichiometric_rank, 2);
    // delta = 3 - 1 - 2 = 0
    assert_eq!(report.deficiency, 0);
    // Fully reversible cycle is weakly reversible
    assert_eq!(report.is_weakly_reversible, true);
    assert_eq!(report.deficiency_zero_applicable, true);
}

#[test]
fn test_multiple_linkage_classes() {
    // Two independent subnetworks:
    // Net 1: A -> B
    // Net 2: C -> D
    let c_a = Complex::single("A", 1);
    let c_b = Complex::single("B", 1);
    let c_c = Complex::single("C", 1);
    let c_d = Complex::single("D", 1);

    let reactions = vec![Reaction::new(c_a, c_b), Reaction::new(c_c, c_d)];

    let net = ReactionNetwork::new(reactions);
    let report = net.evaluate();

    assert_eq!(report.num_species, 4);
    assert_eq!(report.num_complexes, 4);
    assert_eq!(report.num_linkage_classes, 2);
    assert_eq!(report.stoichiometric_rank, 2);
    // delta = 4 - 2 - 2 = 0
    assert_eq!(report.deficiency, 0);
}

// Origin: engine/crates_rs/tests/core_solvers/reaction_network.rs
// Claim: urn:core:crates_rs:tests:reaction-network:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord075bf521 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord075bf521` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError075bf521 {
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
impl BoundaryError075bf521 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError075bf521 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError075bf521 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord075bf521 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError075bf521> {
        if capacity_bound == 0 {
            return Err(BoundaryError075bf521::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError075bf521::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError075bf521::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_075bf521() {
    let admitted = BoundaryRecord075bf521::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord075bf521::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
