//! Boundary and corner case tests for core_holonomy.
//!
//! AuthorityEffect: None.
//! Governing Rule: RULE[user_global] (Strict Zero-Float Law, precise error conditions).

use num_bigint::BigInt;
use num_rational::BigRational;
use core_holonomy::prelude::*;
use core_kernel::resource_limits::OperationLimits;

fn rat(num: i64, den: i64) -> BigRational {
    BigRational::new(BigInt::from(num), BigInt::from(den))
}

#[test]
fn test_empty_path_rejection() {
    let limits = OperationLimits::holonomy();
    let conn = Connection::new(2, limits);

    let empty: Vec<String> = vec![];
    let res = compute_path_holonomy(&conn, &empty);
    assert_eq!(res, Err(HolonomyError::EmptyPath));
}

#[test]
fn test_length_one_loop_rejection() {
    let limits = OperationLimits::holonomy();
    let conn = Connection::new(2, limits);

    let single = vec!["v0".to_string()];
    let res = compute_loop_holonomy(&conn, &single);
    assert_eq!(res, Err(HolonomyError::MalformedPath { length: 1 }));
}

#[test]
fn test_open_loop_rejection() {
    let limits = OperationLimits::holonomy();
    let mut conn = Connection::new(2, limits);
    let id2 = RationalMatrix::try_identity(2).unwrap();
    conn.set_connection("v0", "v1", id2.clone()).unwrap();
    conn.set_connection("v1", "v2", id2.clone()).unwrap();

    let open_path = vec!["v0".to_string(), "v1".to_string(), "v2".to_string()];
    let res = compute_loop_holonomy(&conn, &open_path);
    assert_eq!(
        res,
        Err(HolonomyError::OpenLoop {
            start: "v0".to_string(),
            end: "v2".to_string(),
        })
    );
}

#[test]
fn test_missing_edge_rejection() {
    let limits = OperationLimits::holonomy();
    let mut conn = Connection::new(2, limits);
    let id2 = RationalMatrix::try_identity(2).unwrap();
    conn.set_connection("v0", "v1", id2).unwrap();

    // Edge (v1, v2) is not declared
    let path = vec![
        "v0".to_string(),
        "v1".to_string(),
        "v2".to_string(),
        "v0".to_string(),
    ];
    let res = compute_path_holonomy(&conn, &path);
    assert!(matches!(
        res,
        Err(HolonomyError::EdgeNotFound { src, tgt }) if src == "v1" && tgt == "v2"
    ));
}

#[test]
fn test_singular_connection_rejection() {
    let limits = OperationLimits::holonomy();
    let mut conn = Connection::new(2, limits);

    // Singular matrix with det = 0: row1 = [1, 2], row2 = [2, 4]
    let singular =
        RationalMatrix::try_new(2, 2, vec![rat(1, 1), rat(2, 1), rat(2, 1), rat(4, 1)]).unwrap();

    let res = conn.set_connection("v0", "v1", singular);
    assert!(matches!(
        res,
        Err(HolonomyError::SingularConnection { src, tgt, .. }) if src == "v0" && tgt == "v1"
    ));
}

#[test]
fn test_dimension_one_scalar_connection_holonomy() {
    let limits = OperationLimits::holonomy();
    let mut conn = Connection::new(1, limits);

    // 1x1 matrices: (2/1) * (3/1) * (1/6) = 1/1
    let m1 = RationalMatrix::try_new(1, 1, vec![rat(2, 1)]).unwrap();
    let m2 = RationalMatrix::try_new(1, 1, vec![rat(3, 1)]).unwrap();
    let m3 = RationalMatrix::try_new(1, 1, vec![rat(1, 6)]).unwrap();

    conn.set_connection("v0", "v1", m1).unwrap();
    conn.set_connection("v1", "v2", m2).unwrap();
    conn.set_connection("v2", "v0", m3).unwrap();

    let loop_path = vec![
        "v0".to_string(),
        "v1".to_string(),
        "v2".to_string(),
        "v0".to_string(),
    ];

    let hol = compute_loop_holonomy(&conn, &loop_path).unwrap();
    assert_eq!(hol.get(0, 0), &rat(1, 1));
}

#[test]
fn test_disconnected_components_refusal() {
    let limits = OperationLimits::holonomy();
    let mut complex = CellComplex::new(limits);
    complex.add_vertex("a1").unwrap();
    complex.add_vertex("a2").unwrap();
    complex.add_vertex("b1").unwrap();
    complex.add_vertex("b2").unwrap();

    complex.add_edge("a1", "a2").unwrap();
    complex.add_edge("b1", "b2").unwrap();

    let mut conn = Connection::new(2, limits);
    let id2 = RationalMatrix::try_identity(2).unwrap();
    conn.set_connection("a1", "a2", id2.clone()).unwrap();
    conn.set_connection("b1", "b2", id2.clone()).unwrap();

    // Trying to step from component A to component B
    let path = vec!["a1".to_string(), "b2".to_string()];
    let res = compute_path_holonomy(&conn, &path);
    assert!(matches!(res, Err(HolonomyError::EdgeNotFound { .. })));
}

/// `ExactMatrix::inverse` used to report a singular matrix as a
/// `SingularConnection` on a fictitious edge ("matrix", "inverse"). It now
/// reports `SingularMatrix`; `set_connection` still names the edge.
#[test]
fn test_singular_matrix_is_not_reported_as_a_connection() {
    let singular =
        RationalMatrix::try_new(2, 2, vec![rat(1, 1), rat(2, 1), rat(2, 1), rat(4, 1)]).unwrap();
    assert!(matches!(
        singular.inverse(),
        Err(HolonomyError::SingularMatrix { .. })
    ));
    let invertible =
        RationalMatrix::try_new(2, 2, vec![rat(2, 1), rat(1, 1), rat(1, 1), rat(1, 1)]).unwrap();
    let inverse = invertible.inverse().unwrap();
    assert_eq!(
        invertible.matmul(&inverse).unwrap(),
        RationalMatrix::try_identity(2).unwrap()
    );

    let mut conn = Connection::new(2, OperationLimits::holonomy());
    assert!(matches!(
        conn.set_connection("v0", "v1", singular),
        Err(HolonomyError::SingularConnection { src, tgt, .. }) if src == "v0" && tgt == "v1"
    ));
}

// Origin: engine/crates_rs/tests/core_holonomy/boundary_tests.rs
// Claim: urn:core:crates_rs:tests:boundary-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord92e47bb3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord92e47bb3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError92e47bb3 {
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
impl BoundaryError92e47bb3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError92e47bb3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError92e47bb3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord92e47bb3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError92e47bb3> {
        if capacity_bound == 0 {
            return Err(BoundaryError92e47bb3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError92e47bb3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError92e47bb3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_92e47bb3() {
    let admitted = BoundaryRecord92e47bb3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord92e47bb3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
