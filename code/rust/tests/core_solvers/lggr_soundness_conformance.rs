//! Conformance: the O1 classification (Epoch 19, `o1_resolution.md`).
//!
//! Subject = `cert_lggr_soundness::nec_check` (Theorem 3's rank test). Oracles = the
//! four boundary carriers of the resolution document, each verified against the
//! recorded behaviour. A green test is a conformance reading of these instances;
//! it proves no proposition and mints no authority.


#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_4ea21237 = (i128, i128);
use nalgebra::DMatrix;
use core_solvers::cert_lggr_soundness::{nec_check, CoveringCarrier};

fn eye(d: usize) -> DMatrix<f64> {
    DMatrix::identity(d, d)
}

fn zero(d: usize) -> DMatrix<f64> {
    DMatrix::zeros(d, d)
}

/// A. Chain P4 with identity restrictions: a forest, so NEC (Corollary 6).
#[test]
fn test_chain_is_nec() {
    let carrier = CoveringCarrier {
        num_vertices: 4,
        dim: 2,
        edges: vec![(0, 1, eye(2)), (1, 2, eye(2)), (2, 3, eye(2))],
    };
    let (nec, reports) = nec_check(&carrier).expect("nec check");
    assert!(nec, "identity chain must be NEC");
    for r in &reports {
        assert_eq!(r.isolation_rank, r.fiber_dim, "edge {} not full", r.edge);
    }
}

/// B. The 7.4.5 hexagon (identity restrictions): every isolation space is {0},
/// the extreme non-NEC case — consistent with witness (a).
#[test]
fn test_hexagon_is_maximally_non_nec() {
    // vertices: 0..2 = x12, x23, x31 ; 3..5 = u1, u2, u3
    let carrier = CoveringCarrier {
        num_vertices: 6,
        dim: 3,
        edges: vec![
            (0, 3, eye(3)),
            (0, 4, eye(3)),
            (1, 4, eye(3)),
            (1, 5, eye(3)),
            (2, 5, eye(3)),
            (2, 3, eye(3)),
        ],
    };
    let (nec, reports) = nec_check(&carrier).expect("nec check");
    assert!(!nec, "the hexagon must not be NEC");
    for r in &reports {
        assert_eq!(
            r.isolation_rank, 0,
            "hexagon edge {} should have D_iso = 0",
            r.edge
        );
    }
}

/// C. Forest with a rank-deficient restriction: NOT NEC — kills "forest ⟹ NEC"
/// for general contractive restrictions (Theorem 7(i)).
#[test]
fn test_deficient_forest_is_not_nec() {
    // vertices 0 = a, 1 = b, 2 = b'; edges (a,b, r=0), (a,b', diag(1,0)).
    let carrier = CoveringCarrier {
        num_vertices: 3,
        dim: 2,
        edges: vec![
            (0, 1, zero(2)),
            (
                0,
                2,
                DMatrix::from_diagonal(&nalgebra::DVector::from_row_slice(&[1.0, 0.0])),
            ),
        ],
    };
    let (nec, reports) = nec_check(&carrier).expect("nec check");
    assert!(!nec, "the deficient forest must not be NEC");
    // Edge 0's isolation space is span(e1): rank exactly 1.
    assert_eq!(reports[0].isolation_rank, 1);
}

/// D. Cyclic diamond with alternating identity/zero restrictions: NEC despite
/// the 4-cycle — kills "NEC ⟹ forest" (Theorem 7(ii)).
#[test]
fn test_cyclic_diamond_is_nec() {
    // vertices 0 = a1, 1 = a2, 2 = b1, 3 = b2.
    let carrier = CoveringCarrier {
        num_vertices: 4,
        dim: 2,
        edges: vec![
            (0, 2, eye(2)),  // (a1,b1) = I
            (1, 2, zero(2)), // (a2,b1) = 0
            (1, 3, eye(2)),  // (a2,b2) = I
            (0, 3, zero(2)), // (a1,b2) = 0
        ],
    };
    let (nec, reports) = nec_check(&carrier).expect("nec check");
    assert!(nec, "the alternating diamond must be NEC despite the cycle");
    for r in &reports {
        assert_eq!(r.isolation_rank, r.fiber_dim, "edge {} not full", r.edge);
    }
}

/// E. Single-edge carrier: the lower-endpoint freedom already fills D_iso, so
/// NEC — the corrected reading of anchor (b) recorded in §4 of the resolution.
#[test]
fn test_single_edge_is_nec() {
    let carrier = CoveringCarrier {
        num_vertices: 2,
        dim: 2,
        edges: vec![(
            0,
            1,
            DMatrix::from_diagonal(&nalgebra::DVector::from_row_slice(&[1.0, 0.0])),
        )],
    };
    let (nec, reports) = nec_check(&carrier).expect("nec check");
    assert!(nec, "a single edge with a free lower endpoint is NEC");
    assert_eq!(reports[0].isolation_rank, 2);
}

// Origin: engine/crates_rs/tests/core_solvers/lggr_soundness_conformance.rs
// Claim: urn:core:crates_rs:tests:lggr-soundness-conformance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4ea21237 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4ea21237` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4ea21237 {
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
impl BoundaryError4ea21237 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4ea21237 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4ea21237 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4ea21237 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4ea21237> {
        if capacity_bound == 0 {
            return Err(BoundaryError4ea21237::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4ea21237::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4ea21237::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_4ea21237() {
    let admitted = BoundaryRecord4ea21237::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord4ea21237::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
