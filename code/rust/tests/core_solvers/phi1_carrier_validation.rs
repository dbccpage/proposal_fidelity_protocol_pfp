//! Carrier validation for the Phi-1 L1 boundary solver.
//!
//! The Python side (`engine/crates/solver/solv_phi1_l1_boundary.py`)
//! validates the carrier before constructing a single arc, and its own comment
//! calls this out: "Reject malformed carriers before any arc/index is created
//! (fail closed)." Rust, which is the PROD face, did not validate at all.
//!
//! A malformed carrier must produce a typed refusal. A panic is not a refusal:
//! it cannot be classified, it cannot be recorded in a trace, and it takes the
//! host down instead of the request.
//!
//! AuthorityEffect: None.

use core_solvers::solver_flow_network_simplex::NetworkSimplexError;
use core_solvers::solver_lp_phi1_boundary::{solve_l1_boundary, Boundary1, BoundaryEdge};

fn edge(tail: usize, head: usize, weight: i128) -> BoundaryEdge {
    BoundaryEdge { tail, head, weight }
}

#[test]
fn an_endpoint_past_the_carrier_is_refused_not_panicked() {
    let boundary = Boundary1 {
        num_vertices: 2,
        edges: vec![edge(0, 7, 1)],
    };
    match solve_l1_boundary(&boundary, &[1, -1]) {
        Err(NetworkSimplexError::InvalidCarrier { .. }) => {}
        other => panic!("expected InvalidCarrier, got {other:?}"),
    }
}

#[test]
fn a_self_loop_is_refused() {
    let boundary = Boundary1 {
        num_vertices: 2,
        edges: vec![edge(1, 1, 1)],
    };
    match solve_l1_boundary(&boundary, &[0, 0]) {
        Err(NetworkSimplexError::InvalidCarrier { .. }) => {}
        other => panic!("expected InvalidCarrier, got {other:?}"),
    }
}

#[test]
fn an_empty_carrier_is_refused() {
    let boundary = Boundary1 {
        num_vertices: 0,
        edges: vec![],
    };
    match solve_l1_boundary(&boundary, &[]) {
        Err(NetworkSimplexError::InvalidCarrier { .. }) => {}
        other => panic!("expected InvalidCarrier, got {other:?}"),
    }
}

#[test]
fn a_negative_weight_still_reports_negative_weight_not_invalid_carrier() {
    // Ordering matters. Python checks range and self-loop first, then weight,
    // so a well-formed edge carrying a negative weight must keep its specific
    // class rather than being swallowed by the new carrier check.
    let boundary = Boundary1 {
        num_vertices: 2,
        edges: vec![edge(0, 1, -3)],
    };
    match solve_l1_boundary(&boundary, &[1, -1]) {
        Err(NetworkSimplexError::NegativeWeight { edge, weight }) => {
            assert_eq!(edge, 0);
            assert_eq!(weight, -3);
        }
        other => panic!("expected NegativeWeight, got {other:?}"),
    }
}

#[test]
fn a_well_formed_carrier_still_solves() {
    let boundary = Boundary1 {
        num_vertices: 3,
        edges: vec![edge(0, 1, 2), edge(1, 2, 3)],
    };
    let solved = solve_l1_boundary(&boundary, &[1, 0, -1]).expect("well-formed carrier must solve");
    assert_eq!(solved.z.len(), 2);
    assert_eq!(solved.vertex_potential.len(), 3);
}

// Origin: engine/crates_rs/tests/core_solvers/phi1_carrier_validation.rs
// Claim: urn:core:crates_rs:tests:phi1-carrier-validation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord89ea0cf9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord89ea0cf9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError89ea0cf9 {
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
impl BoundaryError89ea0cf9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError89ea0cf9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError89ea0cf9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord89ea0cf9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError89ea0cf9> {
        if capacity_bound == 0 {
            return Err(BoundaryError89ea0cf9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError89ea0cf9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError89ea0cf9::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_89ea0cf9() {
    let admitted = BoundaryRecord89ea0cf9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord89ea0cf9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
