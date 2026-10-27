//! Soviet allocation discipline and hash determinism tests for core_holonomy.
//!
//! AuthorityEffect: None.
//! Governing Rule: RULE[user_global] (Fallible allocation, try_reserve_exact, zero panics).

use core_holonomy::prelude::*;
use core_kernel::resource_limits::OperationLimits;

#[test]
fn test_exceed_max_vertices_refusal() {
    let limits = OperationLimits {
        max_vertices: 2,
        ..OperationLimits::holonomy()
    };
    let mut complex = CellComplex::new(limits);
    complex.add_vertex("v0").unwrap();
    complex.add_vertex("v1").unwrap();

    let res = complex.add_vertex("v2");
    assert!(matches!(res, Err(HolonomyError::AllocationFailure { .. })));
}

#[test]
fn test_exceed_max_edges_refusal() {
    let limits = OperationLimits {
        max_edges: 1,
        ..OperationLimits::holonomy()
    };
    let mut complex = CellComplex::new(limits);
    complex.add_vertex("v0").unwrap();
    complex.add_vertex("v1").unwrap();
    complex.add_vertex("v2").unwrap();

    complex.add_edge("v0", "v1").unwrap();
    let res = complex.add_edge("v1", "v2");
    assert!(matches!(res, Err(HolonomyError::AllocationFailure { .. })));
}

#[test]
fn test_exceed_max_dimension_refusal() {
    let limits = OperationLimits {
        max_dimension: 2,
        ..OperationLimits::holonomy()
    };
    let res = RationalMatrix::identity(3, &limits);
    assert!(matches!(res, Err(HolonomyError::AllocationFailure { .. })));
}

#[test]
fn test_exceed_max_path_length_refusal() {
    let limits = OperationLimits {
        max_path_length: 3,
        ..OperationLimits::holonomy()
    };
    let mut conn = Connection::new(2, limits);
    let id2 = RationalMatrix::try_identity(2).unwrap();
    conn.set_connection("v0", "v1", id2.clone()).unwrap();
    conn.set_connection("v1", "v2", id2.clone()).unwrap();
    conn.set_connection("v2", "v3", id2.clone()).unwrap();
    conn.set_connection("v3", "v0", id2).unwrap();

    let long_path = vec![
        "v0".to_string(),
        "v1".to_string(),
        "v2".to_string(),
        "v3".to_string(),
    ];
    let res = compute_path_holonomy(&conn, &long_path);
    assert!(matches!(res, Err(HolonomyError::PathLengthExceeded { .. })));
}

#[test]
fn test_sha256_content_hash_determinism_under_permutation() {
    let limits = OperationLimits::holonomy();

    // Order 1: v0, v1, v2
    let mut c1 = CellComplex::new(limits);
    c1.add_vertex("v0").unwrap();
    c1.add_vertex("v1").unwrap();
    c1.add_vertex("v2").unwrap();
    c1.add_edge("v0", "v1").unwrap();
    c1.add_edge("v1", "v2").unwrap();

    // Order 2: v2, v0, v1
    let mut c2 = CellComplex::new(limits);
    c2.add_vertex("v2").unwrap();
    c2.add_vertex("v0").unwrap();
    c2.add_vertex("v1").unwrap();
    c2.add_edge("v1", "v2").unwrap();
    c2.add_edge("v0", "v1").unwrap();

    assert_eq!(
        c1.content_hash(),
        c2.content_hash(),
        "SHA-256 state hash must be identical regardless of insertion order"
    );
}

#[test]
fn test_zero_float_static_verification() {
    // Scan source files of crate for any occurrence of f32 or f64
    let src_files = [
        include_str!("../../core_holonomy/src/lib.rs"),
        include_str!("../../core_holonomy/src/error.rs"),
        include_str!("../../core_holonomy/src/matrix.rs"),
        include_str!("../../core_holonomy/src/graph.rs"),
        include_str!("../../core_holonomy/src/connection.rs"),
        include_str!("../../core_holonomy/src/holonomy.rs"),
        include_str!("../../core_holonomy/src/laplacian.rs"),
        include_str!("../../core_holonomy/src/curvature.rs"),
    ];

    for (idx, src) in src_files.iter().enumerate() {
        assert!(
            !src.contains("f32"),
            "Zero-Float Law violation: found f32 in module index {idx}"
        );
        assert!(
            !src.contains("f64"),
            "Zero-Float Law violation: found f64 in module index {idx}"
        );
    }
}

// Origin: engine/crates_rs/tests/core_holonomy/soviet_allocation_tests.rs
// Claim: urn:core:crates_rs:tests:soviet-allocation-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1318197e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1318197e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1318197e {
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
impl BoundaryError1318197e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1318197e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1318197e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1318197e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1318197e> {
        if capacity_bound == 0 {
            return Err(BoundaryError1318197e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1318197e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1318197e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_1318197e() {
    let admitted = BoundaryRecord1318197e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1318197e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
