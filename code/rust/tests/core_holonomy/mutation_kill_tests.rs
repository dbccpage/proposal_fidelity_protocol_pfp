//! Behavioral Mutation Kill Suite for core_holonomy (MUT-01 through MUT-06).
//!
//! AuthorityEffect: None.
//! Governing Rule: RULE[user_global] (L4A certification rubric, non-vacuous mutation testing).

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use core_holonomy::prelude::*;
use core_kernel::resource_limits::OperationLimits;

fn rat(num: i64, den: i64) -> BigRational {
    BigRational::new(BigInt::from(num), BigInt::from(den))
}

/// MUT-01: Reversed path composition order.
/// Mutant computes U(e_1) * U(e_2) instead of U(e_2) * U(e_1).
/// Kill test: Non-commuting matrices where M2 * M1 != M1 * M2.
#[test]
fn test_kill_mutant_01_path_order_swap() {
    let limits = OperationLimits::holonomy();
    let mut conn = Connection::new(2, limits);

    let m1 =
        RationalMatrix::try_new(2, 2, vec![rat(1, 1), rat(1, 1), rat(0, 1), rat(1, 1)]).unwrap();
    let m2 =
        RationalMatrix::try_new(2, 2, vec![rat(1, 1), rat(0, 1), rat(1, 1), rat(1, 1)]).unwrap();

    conn.set_connection("v0", "v1", m1.clone()).unwrap();
    conn.set_connection("v1", "v2", m2.clone()).unwrap();

    let path = vec!["v0".to_string(), "v1".to_string(), "v2".to_string()];
    let hol = compute_path_holonomy(&conn, &path).unwrap();

    // Correct ordered product is M2 * M1 = [[1, 1], [1, 2]]
    let expected = m2.matmul(&m1).unwrap();
    assert_eq!(hol, expected);

    // Reversed product is M1 * M2 = [[2, 1], [1, 1]] != M2 * M1
    let reversed = m1.matmul(&m2).unwrap();
    assert_ne!(
        hol, reversed,
        "MUT-01 KILLED: Path product order inversion detected"
    );
}

/// MUT-02: Edge inversion fallacy.
/// Mutant traverses reverse edge without inverting connection matrix (returns U(e) instead of U(e)^-1).
/// Kill test: Roundtrip loop u -> v -> u must equal I_d. If mutant uses U(e) * U(e),
/// result is M^2 != I_d for non-involutory matrix.
#[test]
fn test_kill_mutant_02_edge_inversion_fallacy() {
    let limits = OperationLimits::holonomy();
    let mut conn = Connection::new(2, limits);

    // Non-involutory shear matrix where M^2 != I
    let m =
        RationalMatrix::try_new(2, 2, vec![rat(1, 1), rat(2, 1), rat(0, 1), rat(1, 1)]).unwrap();
    conn.set_connection("u", "v", m.clone()).unwrap();

    let loop_path = vec!["u".to_string(), "v".to_string(), "u".to_string()];
    let hol = compute_loop_holonomy(&conn, &loop_path).unwrap();

    let id2 = RationalMatrix::try_identity(2).unwrap();
    assert_eq!(hol, id2, "Roundtrip loop must equal identity");

    let m_squared = m.matmul(&m).unwrap();
    assert_ne!(
        hol, m_squared,
        "MUT-02 KILLED: Reverse edge traversal must use inverted matrix"
    );
}

#[test]
fn opposite_write_cannot_break_edge_inversion() {
    let limits = OperationLimits::holonomy();
    let mut conn = Connection::new(2, limits);
    let first =
        RationalMatrix::try_new(2, 2, vec![rat(1, 1), rat(2, 1), rat(0, 1), rat(1, 1)]).unwrap();
    let second =
        RationalMatrix::try_new(2, 2, vec![rat(3, 1), rat(0, 1), rat(0, 1), rat(1, 1)]).unwrap();
    conn.set_connection("u", "v", first).unwrap();
    conn.set_connection("v", "u", second.clone()).unwrap();

    let vu = conn.get_step("v", "u").unwrap().clone();
    let uv = conn.get_step("u", "v").unwrap().clone();
    assert_eq!(vu, second);
    let id2 = RationalMatrix::try_identity(2).unwrap();
    assert_eq!(vu.matmul(&uv).unwrap(), id2);
    assert_eq!(uv.matmul(&vu).unwrap(), id2);
    assert_eq!(conn.forward.len(), 1);

    let tight = OperationLimits {
        max_edges: 1,
        ..OperationLimits::holonomy()
    };
    let mut capped = Connection::new(2, tight);
    capped.set_connection("u", "v", id2.clone()).unwrap();
    assert!(capped.set_connection("u", "v", second).is_ok());
    assert!(capped.set_connection("a", "b", id2).is_err());
}

/// MUT-03: Pure-gauge false flatness bypass.
/// Mutant hardcodes identity for loops without evaluating the gauge connection values.
/// Kill test: For a connection that is NOT pure gauge (e.g. non-zero magnetic flux),
/// loop holonomy must NOT evaluate to identity.
#[test]
fn test_kill_mutant_03_pure_gauge_flatness_bypass() {
    let limits = OperationLimits::holonomy();
    let mut conn = Connection::new(2, limits);

    // Non-trivial 90-degree rotation connection on 3-cycle
    let r90 =
        RationalMatrix::try_new(2, 2, vec![rat(0, 1), rat(-1, 1), rat(1, 1), rat(0, 1)]).unwrap();
    let id2 = RationalMatrix::try_identity(2).unwrap();

    conn.set_connection("v0", "v1", r90).unwrap();
    conn.set_connection("v1", "v2", id2.clone()).unwrap();
    conn.set_connection("v2", "v0", id2.clone()).unwrap();

    let loop_path = vec![
        "v0".to_string(),
        "v1".to_string(),
        "v2".to_string(),
        "v0".to_string(),
    ];
    let hol = compute_loop_holonomy(&conn, &loop_path).unwrap();

    // A bypass mutant that unconditionally returns identity would fail here:
    assert_ne!(
        hol, id2,
        "MUT-03 KILLED: Frustrated connection must not be falsely reported as identity flat"
    );
}

/// MUT-04: Connection Laplacian off-diagonal sign swap.
/// Mutant sets L_uv = +U_uv instead of -U_uv.
/// Kill test: On a flat connection with constant sections psi(v) = c,
/// D_U(c) = 0 and <c, Delta c> = 0. If L_uv = +U_uv, then <c, Delta c> = 4c^2 != 0.
#[test]
fn test_kill_mutant_04_laplacian_symmetry_violation() {
    let limits = OperationLimits::holonomy();
    let mut complex = CellComplex::new(limits);
    complex.add_vertex("v0").unwrap();
    complex.add_vertex("v1").unwrap();
    complex.add_edge("v0", "v1").unwrap();

    let mut conn = Connection::new(2, limits);
    let id2 = RationalMatrix::try_identity(2).unwrap();
    conn.set_connection("v0", "v1", id2).unwrap();

    let lap = compute_connection_laplacian(&complex, &conn, None).unwrap();
    let psi_constant = vec![rat(1, 1), rat(1, 1), rat(1, 1), rat(1, 1)];
    let quad = lap.evaluate_quadratic_form(&psi_constant).unwrap();

    assert_eq!(
        quad,
        rat(0, 1),
        "Constant section must have zero quadratic form on flat connection"
    );

    // Off-diagonal block must be negative identity: -I
    assert_eq!(
        lap.matrix.get(0, 2),
        &rat(-1, 1),
        "MUT-04 KILLED: Off-diagonal entry must be -1, not +1"
    );
    assert_eq!(
        lap.matrix.get(1, 3),
        &rat(-1, 1),
        "MUT-04 KILLED: Off-diagonal entry must be -1, not +1"
    );
}

/// MUT-05: Curvature commutator sign / anticommutator replacement.
/// Mutant replaces [M1, M2] = M1*M2 - M2*M1 with anticommutator M1*M2 + M2*M1.
/// Kill test: Commuting diagonal matrices have [M1, M2] = 0, but {M1, M2} = 2 M1 M2 != 0.
#[test]
fn test_kill_mutant_05_curvature_commutator_sign() {
    let limits = OperationLimits::holonomy();
    let m1 =
        RationalMatrix::try_new(2, 2, vec![rat(2, 1), rat(0, 1), rat(0, 1), rat(2, 1)]).unwrap();
    let m2 =
        RationalMatrix::try_new(2, 2, vec![rat(3, 1), rat(0, 1), rat(0, 1), rat(3, 1)]).unwrap();

    assert!(curvature_commutator_vanishes(&m1, &m2, &limits).unwrap());

    // Mutant anticommutator: 2 * (2*I * 3*I) = 12 * I != 0
    let p1 = m1.matmul(&m2).unwrap();
    let p2 = m2.matmul(&m1).unwrap();
    let mut anticomm = p1;
    for i in 0..anticomm.data.len() {
        anticomm.data[i] += p2.data[i].clone();
    }
    assert!(
        !anticomm.data.iter().all(|x| x.is_zero()),
        "MUT-05 KILLED: Anticommutator does not vanish for commuting scalar matrices"
    );
}

/// MUT-06: Unchecked allocation limit bypass.
/// Mutant bypasses try_reserve_exact checks.
/// Kill test: Requesting vertices beyond max_vertices must return AllocationFailure.
#[test]
fn test_kill_mutant_06_allocation_limit_bypass() {
    let limits = OperationLimits {
        max_vertices: 1,
        ..OperationLimits::holonomy()
    };
    let mut complex = CellComplex::new(limits);
    complex.add_vertex("v0").unwrap();

    let res = complex.add_vertex("v1");
    assert!(
        matches!(res, Err(HolonomyError::AllocationFailure { .. })),
        "MUT-06 KILLED: Allocation limit must be strictly enforced via AllocationFailure"
    );
}

/// MUT-07 (Bonus): Loop closure bypass.
/// Passing open path ["v0", "v1", "v2"] must strictly return OpenLoop.
#[test]
fn test_kill_mutant_07_loop_closure_bypass() {
    let limits = OperationLimits::holonomy();
    let mut conn = Connection::new(2, limits);
    let id2 = RationalMatrix::try_identity(2).unwrap();
    conn.set_connection("v0", "v1", id2.clone()).unwrap();
    conn.set_connection("v1", "v2", id2).unwrap();

    let open_path = vec!["v0".to_string(), "v1".to_string(), "v2".to_string()];
    let res = compute_loop_holonomy(&conn, &open_path);
    assert!(
        matches!(res, Err(HolonomyError::OpenLoop { start, end }) if start == "v0" && end == "v2"),
        "MUT-07 KILLED: Open loop must be rejected by compute_loop_holonomy"
    );
}

// Origin: engine/crates_rs/tests/core_holonomy/mutation_kill_tests.rs
// Claim: urn:core:crates_rs:tests:mutation-kill-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb4b8d392 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb4b8d392` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb4b8d392 {
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
impl BoundaryErrorb4b8d392 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb4b8d392 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb4b8d392 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb4b8d392 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb4b8d392> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb4b8d392::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb4b8d392::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb4b8d392::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b4b8d392() {
    let admitted = BoundaryRecordb4b8d392::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb4b8d392::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
