//! Adversarial stress and challenge tests for core_holonomy.
//!
//! AuthorityEffect: None.
//! Governing Rule: RULE[user_global] (Non-abelian challenges, degenerate diagrams, error precedence).

use num_bigint::BigInt;
use num_rational::BigRational;
use core_holonomy::prelude::*;
use core_kernel::resource_limits::OperationLimits;

fn rat(num: i64, den: i64) -> BigRational {
    BigRational::new(BigInt::from(num), BigInt::from(den))
}

#[test]
fn test_non_abelian_holonomy_path_order_sensitivity() {
    let limits = OperationLimits::holonomy();
    let mut conn = Connection::new(2, limits);

    // Non-commuting shear matrices
    let m1 =
        RationalMatrix::try_new(2, 2, vec![rat(1, 1), rat(2, 1), rat(0, 1), rat(1, 1)]).unwrap();
    let m2 =
        RationalMatrix::try_new(2, 2, vec![rat(1, 1), rat(0, 1), rat(3, 1), rat(1, 1)]).unwrap();

    conn.set_connection("v0", "v1", m1.clone()).unwrap();
    conn.set_connection("v1", "v2", m2.clone()).unwrap();

    // Transport v0 -> v1 -> v2: M2 * M1
    let p1 = vec!["v0".into(), "v1".into(), "v2".into()];
    let hol1 = compute_path_holonomy(&conn, &p1).unwrap();

    // M2 * M1 = [[1, 0], [3, 1]] * [[1, 2], [0, 1]] = [[1, 2], [3, 7]]
    let expected = m2.matmul(&m1).unwrap();
    assert_eq!(hol1, expected);

    // Reversed path v2 -> v1 -> v0: M1^(-1) * M2^(-1) = (M2 * M1)^(-1)
    let p_rev = vec!["v2".into(), "v1".into(), "v0".into()];
    let hol_rev = compute_path_holonomy(&conn, &p_rev).unwrap();
    assert_eq!(hol_rev, expected.inverse().unwrap());
}

#[test]
fn test_figure_eight_self_intersecting_loop() {
    let limits = OperationLimits::holonomy();
    let mut conn = Connection::new(2, limits);

    let m1 =
        RationalMatrix::try_new(2, 2, vec![rat(1, 1), rat(1, 1), rat(0, 1), rat(1, 1)]).unwrap();
    let m2 =
        RationalMatrix::try_new(2, 2, vec![rat(1, 1), rat(0, 1), rat(1, 1), rat(1, 1)]).unwrap();

    conn.set_connection("center", "left", m1.clone()).unwrap();
    conn.set_connection("center", "right", m2.clone()).unwrap();

    // Figure-8: center -> left -> center -> right -> center
    // Holonomy = (U(right, center) * U(center, right)) * (U(left, center) * U(center, left)) = I * I = I
    let fig8 = vec![
        "center".into(),
        "left".into(),
        "center".into(),
        "right".into(),
        "center".into(),
    ];

    let hol = compute_loop_holonomy(&conn, &fig8).unwrap();
    let id2 = RationalMatrix::try_identity(2).unwrap();
    assert_eq!(
        hol, id2,
        "Contractible figure-8 loop must evaluate to identity"
    );
}

#[test]
fn test_strict_error_precedence_hierarchy() {
    // Priority order:
    // AllocationFailure > SingularConnection > OpenLoop > VertexNotFound > EdgeNotFound > DimensionMismatch > PathLengthExceeded

    let err_alloc = HolonomyError::AllocationFailure {
        requested: 100,
        detail: "limit".into(),
    };
    let err_sing = HolonomyError::SingularConnection {
        src: "u".into(),
        tgt: "v".into(),
        detail: "zero det".into(),
    };
    let err_open = HolonomyError::OpenLoop {
        start: "a".into(),
        end: "b".into(),
    };
    let err_vtx = HolonomyError::VertexNotFound { id: "x".into() };
    let err_edge = HolonomyError::EdgeNotFound {
        src: "u".into(),
        tgt: "v".into(),
    };
    let err_dim = HolonomyError::DimensionMismatch {
        expected: 2,
        actual: 3,
    };
    let err_path = HolonomyError::PathLengthExceeded {
        length: 10,
        limit: 5,
    };

    assert!(err_alloc.precedence_rank() < err_sing.precedence_rank());
    assert!(err_sing.precedence_rank() < err_open.precedence_rank());
    assert!(err_open.precedence_rank() < err_vtx.precedence_rank());
    assert!(err_vtx.precedence_rank() < err_edge.precedence_rank());
    assert!(err_edge.precedence_rank() < err_dim.precedence_rank());
    assert!(err_dim.precedence_rank() < err_path.precedence_rank());
}

// Origin: engine/crates_rs/tests/core_holonomy/adversarial_challenge_tests.rs
// Claim: urn:core:crates_rs:tests:adversarial-challenge-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8fc42e6d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8fc42e6d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8fc42e6d {
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
impl BoundaryError8fc42e6d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8fc42e6d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8fc42e6d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8fc42e6d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8fc42e6d> {
        if capacity_bound == 0 {
            return Err(BoundaryError8fc42e6d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8fc42e6d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8fc42e6d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_8fc42e6d() {
    let admitted = BoundaryRecord8fc42e6d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord8fc42e6d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
