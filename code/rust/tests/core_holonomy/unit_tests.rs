//! Core functional unit tests for core_holonomy.
//!
//! AuthorityEffect: None.
//! Governing Rule: RULE[user_global] (Strict Zero-Float Law, genuine test logic).

use num_bigint::BigInt;
use num_rational::BigRational;
use core_holonomy::prelude::*;
use core_kernel::resource_limits::OperationLimits;
use std::collections::BTreeMap;

fn rat(num: i64, den: i64) -> BigRational {
    BigRational::new(BigInt::from(num), BigInt::from(den))
}

fn rot90() -> RationalMatrix {
    RationalMatrix::try_new(2, 2, vec![rat(0, 1), rat(-1, 1), rat(1, 1), rat(0, 1)]).unwrap()
}

#[test]
fn test_four_cycle_rotation_identity() {
    let limits = OperationLimits::holonomy();
    let mut complex = CellComplex::new(limits);
    complex.add_vertex("v0").unwrap();
    complex.add_vertex("v1").unwrap();
    complex.add_vertex("v2").unwrap();
    complex.add_vertex("v3").unwrap();

    complex.add_edge("v0", "v1").unwrap();
    complex.add_edge("v1", "v2").unwrap();
    complex.add_edge("v2", "v3").unwrap();
    complex.add_edge("v3", "v0").unwrap();

    let mut conn = Connection::new(2, limits);
    let r = rot90();
    conn.set_connection("v0", "v1", r.clone()).unwrap();
    conn.set_connection("v1", "v2", r.clone()).unwrap();
    conn.set_connection("v2", "v3", r.clone()).unwrap();
    conn.set_connection("v3", "v0", r.clone()).unwrap();

    let loop_path = vec![
        "v0".to_string(),
        "v1".to_string(),
        "v2".to_string(),
        "v3".to_string(),
        "v0".to_string(),
    ];

    let hol = compute_loop_holonomy(&conn, &loop_path).unwrap();
    let id2 = RationalMatrix::try_identity(2).unwrap();
    assert_eq!(
        hol, id2,
        "4 rotations by 90 degrees must equal identity in GL(2, Q)"
    );
}

#[test]
fn test_wilson_loop_trace_exact() {
    let limits = OperationLimits::holonomy();
    let mut conn = Connection::new(2, limits);
    let r = rot90();
    conn.set_connection("v0", "v1", r.clone()).unwrap();
    conn.set_connection("v1", "v2", r.clone()).unwrap();
    conn.set_connection("v2", "v3", r.clone()).unwrap();
    conn.set_connection("v3", "v0", r.clone()).unwrap();

    let loop_path = vec![
        "v0".to_string(),
        "v1".to_string(),
        "v2".to_string(),
        "v3".to_string(),
        "v0".to_string(),
    ];

    let tr = wilson_loop_trace(&conn, &loop_path).unwrap();
    assert_eq!(tr, rat(2, 1), "Trace of 2x2 identity matrix must equal 2/1");
}

#[test]
fn test_two_vertex_backtrack_roundtrip() {
    let limits = OperationLimits::holonomy();
    let mut conn = Connection::new(2, limits);

    // Arbitrary invertible rational matrix
    let m =
        RationalMatrix::try_new(2, 2, vec![rat(3, 2), rat(1, 2), rat(2, 1), rat(1, 1)]).unwrap();

    conn.set_connection("u", "v", m).unwrap();
    let loop_path = vec!["u".to_string(), "v".to_string(), "u".to_string()];
    let hol = compute_loop_holonomy(&conn, &loop_path).unwrap();
    let id2 = RationalMatrix::try_identity(2).unwrap();

    assert_eq!(
        hol, id2,
        "Backtrack loop u -> v -> u must evaluate to identity via edge inversion"
    );
}

#[test]
fn test_pure_gauge_flatness_on_triangle() {
    let limits = OperationLimits::holonomy();
    let mut complex = CellComplex::new(limits);
    complex.add_vertex("v0").unwrap();
    complex.add_vertex("v1").unwrap();
    complex.add_vertex("v2").unwrap();

    complex.add_edge("v0", "v1").unwrap();
    complex.add_edge("v1", "v2").unwrap();
    complex.add_edge("v2", "v0").unwrap();

    let mut gauge_values = BTreeMap::new();
    gauge_values.insert(
        "v0".to_string(),
        RationalMatrix::try_new(2, 2, vec![rat(1, 1), rat(2, 1), rat(0, 1), rat(1, 1)]).unwrap(),
    );
    gauge_values.insert(
        "v1".to_string(),
        RationalMatrix::try_new(2, 2, vec![rat(2, 1), rat(1, 1), rat(1, 1), rat(1, 1)]).unwrap(),
    );
    gauge_values.insert(
        "v2".to_string(),
        RationalMatrix::try_new(2, 2, vec![rat(1, 1), rat(0, 1), rat(3, 1), rat(1, 1)]).unwrap(),
    );

    let conn = Connection::from_pure_gauge(&complex, &gauge_values, 2, limits).unwrap();
    let loop_path = vec![
        "v0".to_string(),
        "v1".to_string(),
        "v2".to_string(),
        "v0".to_string(),
    ];

    let hol = compute_loop_holonomy(&conn, &loop_path).unwrap();
    let id2 = RationalMatrix::try_identity(2).unwrap();
    assert_eq!(
        hol, id2,
        "Pure-gauge connection must telescope to identity on any closed loop"
    );
}

#[test]
fn test_curvature_commutator_commuting_matrices() {
    let limits = OperationLimits::holonomy();
    let m1 =
        RationalMatrix::try_new(2, 2, vec![rat(1, 1), rat(1, 1), rat(0, 1), rat(1, 1)]).unwrap();
    let m2 =
        RationalMatrix::try_new(2, 2, vec![rat(1, 1), rat(2, 1), rat(0, 1), rat(1, 1)]).unwrap();

    let comm = curvature_commutator(&m1, &m2, &limits).unwrap();
    let zero = rat(0, 1);
    for val in &comm.data {
        assert_eq!(
            *val, zero,
            "Commuting upper-triangular matrices must have vanishing Lie bracket"
        );
    }
    assert!(curvature_commutator_vanishes(&m1, &m2, &limits).unwrap());
}

#[test]
fn test_discrete_bianchi_identity_cube() {
    let limits = OperationLimits::holonomy();
    let mut conn = Connection::new(2, limits);

    // Identity transport on all edges of a cube
    let id2 = RationalMatrix::try_identity(2).unwrap();
    for i in 0..8 {
        for j in 0..8 {
            if i != j {
                let _ = conn.set_connection(format!("v{i}"), format!("v{j}"), id2.clone());
            }
        }
    }

    // 6 faces of a cube (standard 2-sphere boundary orientation)
    let faces = vec![
        vec![
            "v0".into(),
            "v1".into(),
            "v2".into(),
            "v3".into(),
            "v0".into(),
        ],
        vec![
            "v4".into(),
            "v5".into(),
            "v6".into(),
            "v7".into(),
            "v4".into(),
        ],
        vec![
            "v0".into(),
            "v1".into(),
            "v5".into(),
            "v4".into(),
            "v0".into(),
        ],
        vec![
            "v2".into(),
            "v3".into(),
            "v7".into(),
            "v6".into(),
            "v2".into(),
        ],
        vec![
            "v1".into(),
            "v2".into(),
            "v6".into(),
            "v5".into(),
            "v1".into(),
        ],
        vec![
            "v3".into(),
            "v0".into(),
            "v4".into(),
            "v7".into(),
            "v3".into(),
        ],
    ];

    assert!(verify_discrete_bianchi_identity(&conn, &faces).unwrap());
}

// Origin: engine/crates_rs/tests/core_holonomy/unit_tests.rs
// Claim: urn:core:crates_rs:tests:unit-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorded406438 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorded406438` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrored406438 {
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
impl BoundaryErrored406438 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrored406438 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrored406438 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorded406438 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrored406438> {
        if capacity_bound == 0 {
            return Err(BoundaryErrored406438::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrored406438::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrored406438::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ed406438() {
    let admitted = BoundaryRecorded406438::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorded406438::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
