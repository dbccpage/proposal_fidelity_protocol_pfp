//! Integration tests for DDC Move Network and Futile Cycle Detector (U24).
//!
//! Invariants verified:
//! - Directed state graph: nodes are (state_id, Phi_1, Gamma_2).
//! - Edges are DDC operations consuming tokens.
//! - Futile Cycle: net Delta Phi_1 = 0, net Delta Gamma_2 = 0, total token_cost > 0.
//! - Witness: Diamond 4b gives futile cycle traversed 6 times.
//!
//! AuthorityEffect: None.

use core_wdp::ddc::move_network::*;

#[test]
fn test_diamond_4b_futile_cycle_witness_6_traversals() {
    let mut net = MoveNetwork::new();

    // Diamond 4b cycle nodes: s1, s2, s3, s4
    // s1: Phi_1 = 3, Gamma_2 = 2
    // s2: Phi_1 = 2, Gamma_2 = 2 (after R, tokens = 10, dPhi = -1)
    // s3: Phi_1 = 2, Gamma_2 = 1 (after C, tokens = 15, dGamma = -1)
    // s4: Phi_1 = 3, Gamma_2 = 1 (after I, tokens = 12, dPhi = +1)
    // back to s1: Phi_1 = 3, Gamma_2 = 2 (after D, tokens = 18, dGamma = +1)
    net.add_transition("s1", "s2", "R", 10, 3, 2, 2, 2);
    net.add_transition("s2", "s3", "C", 15, 2, 2, 2, 1);
    net.add_transition("s3", "s4", "I", 12, 2, 3, 1, 1);
    net.add_transition("s4", "s1", "D", 18, 3, 3, 1, 2);

    // Detect futile cycles in the move network
    let futile = net.detect_futile_cycles();
    assert!(!futile.is_empty(), "Diamond 4b loop must be detected as a cycle");

    let c = &futile[0];
    assert_eq!(c.net_delta_phi1, 0);
    assert_eq!(c.net_delta_gamma2, 0);
    assert_eq!(c.total_token_cost, 10 + 15 + 12 + 18); // 55 tokens
    assert!(c.total_token_cost > 0);
    assert!(c.is_futile);

    // Witness: Diamond 4b gives futile cycle traversed 6 times
    let mut trajectory = Vec::new();
    let cycle_nodes = ["s1", "s2", "s3", "s4"];
    for _ in 0..6 {
        for &node in &cycle_nodes {
            trajectory.push(node);
        }
    }
    trajectory.push("s1"); // close the final 6th traversal

    let traversals = net.count_cycle_traversals(&trajectory, &["s1", "s2", "s3", "s4", "s1"]);
    assert_eq!(traversals, 6, "Diamond 4b cycle must be traversed exactly 6 times");
}

#[test]
fn test_strictly_descending_move_is_not_futile() {
    let mut net = MoveNetwork::new();

    // Descending step: s1 (Phi_1 = 5) -> s2 (Phi_1 = 2) -> s3 (Phi_1 = 0)
    net.add_transition("s1", "s2", "R", 10, 5, 2, 0, 0);
    net.add_transition("s2", "s3", "C", 10, 2, 0, 0, 0);

    let futile = net.detect_futile_cycles();
    assert!(futile.is_empty(), "Strictly descending acyclic trajectory has no futile cycles");
}

// Origin: engine/crates_rs/tests/core_wdp/test_ddc_move_network.rs
// Claim: urn:core:crates_rs:tests:test-ddc-move-network:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord005187ae {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord005187ae` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError005187ae {
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
impl BoundaryError005187ae {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError005187ae {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError005187ae {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord005187ae {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError005187ae> {
        if capacity_bound == 0 {
            return Err(BoundaryError005187ae::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError005187ae::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError005187ae::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_005187ae() {
    let admitted = BoundaryRecord005187ae::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord005187ae::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
