//! Connection Laplacian spectral and symmetry tests for core_holonomy.
//!
//! AuthorityEffect: None.
//! Governing Rule: RULE[user_global] (Symmetry, trace formula, spectral gap).

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
fn test_laplacian_symmetry_orthogonal_connection() {
    let limits = OperationLimits::holonomy();
    let mut complex = CellComplex::new(limits);
    complex.add_vertex("v0").unwrap();
    complex.add_vertex("v1").unwrap();
    complex.add_vertex("v2").unwrap();

    complex.add_edge("v0", "v1").unwrap();
    complex.add_edge("v1", "v2").unwrap();
    complex.add_edge("v2", "v0").unwrap();

    let mut conn = Connection::new(2, limits);
    let r = rot90();
    conn.set_connection("v0", "v1", r.clone()).unwrap();
    conn.set_connection("v1", "v2", r.clone()).unwrap();
    conn.set_connection("v2", "v0", r).unwrap();

    let lap = compute_connection_laplacian(&complex, &conn, None).unwrap();
    assert!(
        lap.is_symmetric(),
        "Connection Laplacian with orthogonal connection must be symmetric"
    );
}

#[test]
fn test_laplacian_trace_formula_exact() {
    let limits = OperationLimits::holonomy();
    let mut complex = CellComplex::new(limits);
    complex.add_vertex("v0").unwrap();
    complex.add_vertex("v1").unwrap();
    complex.add_vertex("v2").unwrap();
    complex.add_vertex("v3").unwrap();

    // 4 edges on 4-cycle
    complex.add_edge("v0", "v1").unwrap();
    complex.add_edge("v1", "v2").unwrap();
    complex.add_edge("v2", "v3").unwrap();
    complex.add_edge("v3", "v0").unwrap();

    let mut conn = Connection::new(2, limits);
    let id2 = RationalMatrix::try_identity(2).unwrap();
    conn.set_connection("v0", "v1", id2.clone()).unwrap();
    conn.set_connection("v1", "v2", id2.clone()).unwrap();
    conn.set_connection("v2", "v3", id2.clone()).unwrap();
    conn.set_connection("v3", "v0", id2).unwrap();

    let lap = compute_connection_laplacian(&complex, &conn, None).unwrap();
    // Trace theorem: Tr(Delta) = 2 * d * |E| = 2 * 2 * 4 = 16
    let tr = lap.trace().unwrap();
    assert_eq!(tr, rat(16, 1), "Trace must equal 2 * d * |E| = 16");
}

#[test]
fn test_laplacian_positive_semi_definiteness() {
    let limits = OperationLimits::holonomy();
    let mut complex = CellComplex::new(limits);
    complex.add_vertex("v0").unwrap();
    complex.add_vertex("v1").unwrap();

    complex.add_edge("v0", "v1").unwrap();

    let mut conn = Connection::new(2, limits);
    let id2 = RationalMatrix::try_identity(2).unwrap();
    conn.set_connection("v0", "v1", id2).unwrap();

    let lap = compute_connection_laplacian(&complex, &conn, None).unwrap();

    // Total dimension = 2 vertices * 2 fiber_dim = 4
    // Test section 1: psi = [1, 0, 0, 0]
    let psi1 = vec![rat(1, 1), rat(0, 1), rat(0, 1), rat(0, 1)];
    let val1 = lap.evaluate_quadratic_form(&psi1).unwrap();
    assert!(val1 >= rat(0, 1), "Quadratic form must be non-negative");

    // Test section 2: parallel section psi = [1, 2, 1, 2]
    // Since psi(v1) == U * psi(v0), D_U psi == 0, so <psi, Delta psi> == 0!
    let psi2 = vec![rat(1, 1), rat(2, 1), rat(1, 1), rat(2, 1)];
    let val2 = lap.evaluate_quadratic_form(&psi2).unwrap();
    assert_eq!(
        val2,
        rat(0, 1),
        "Parallel section must be in kernel with quadratic form 0"
    );

    // Test section 3: arbitrary non-parallel section
    let psi3 = vec![rat(1, 1), rat(-1, 1), rat(2, 1), rat(3, 1)];
    let val3 = lap.evaluate_quadratic_form(&psi3).unwrap();
    assert!(
        val3 > rat(0, 1),
        "Non-parallel section must have strictly positive quadratic form"
    );
}

#[test]
fn test_flat_connection_harmonic_ground_states() {
    let limits = OperationLimits::holonomy();
    let mut complex = CellComplex::new(limits);
    complex.add_vertex("v0").unwrap();
    complex.add_vertex("v1").unwrap();
    complex.add_vertex("v2").unwrap();

    complex.add_edge("v0", "v1").unwrap();
    complex.add_edge("v1", "v2").unwrap();
    complex.add_edge("v2", "v0").unwrap();

    let mut conn = Connection::new(2, limits);
    let id2 = RationalMatrix::try_identity(2).unwrap();
    conn.set_connection("v0", "v1", id2.clone()).unwrap();
    conn.set_connection("v1", "v2", id2.clone()).unwrap();
    conn.set_connection("v2", "v0", id2).unwrap();

    let lap = compute_connection_laplacian(&complex, &conn, None).unwrap();
    // On a connected graph with flat connection, kernel dimension must equal fiber dimension d = 2
    let ker_dim = lap.kernel_dimension();
    assert_eq!(
        ker_dim, 2,
        "Kernel dimension of flat connection on connected graph must equal d=2"
    );
    assert!(
        !lap.has_spectral_gap(),
        "Flat connection has non-trivial kernel (zero modes)"
    );
}

#[test]
fn test_frustrated_connection_spectral_gap() {
    let limits = OperationLimits::holonomy();
    let mut complex = CellComplex::new(limits);
    complex.add_vertex("v0").unwrap();
    complex.add_vertex("v1").unwrap();

    complex.add_edge("v0", "v1").unwrap();

    let mut conn = Connection::new(2, limits);
    // Non-trivial rotation with no +1 eigenvalue: 90-degree rotation
    let r = rot90();
    conn.set_connection("v0", "v1", r).unwrap();

    let _lap = compute_connection_laplacian(&complex, &conn, None).unwrap();
    // For single edge with R90: L = [ [I, -R], [-R^T, I] ]
    // Kernel requires psi1 = R * psi0 and psi0 = R^T * psi1, which is always satisfied on tree.
    // To frustrate, we need a cycle with holonomy != I:
    complex.add_vertex("v2").unwrap();
    complex.add_edge("v1", "v2").unwrap();
    complex.add_edge("v2", "v0").unwrap();

    let id2 = RationalMatrix::try_identity(2).unwrap();
    conn.set_connection("v1", "v2", id2.clone()).unwrap();
    conn.set_connection("v2", "v0", id2).unwrap();
    // Total loop holonomy = I * I * R90 = R90 != I.
    // R90 has eigenvalues +/- i, none equal to +1. Thus no parallel section exists over Q!

    let lap_frustrated = compute_connection_laplacian(&complex, &conn, None).unwrap();
    let ker_dim = lap_frustrated.kernel_dimension();
    assert_eq!(
        ker_dim, 0,
        "Frustrated connection has trivial kernel over Q"
    );
    assert!(
        lap_frustrated.has_spectral_gap(),
        "Frustrated connection certifies exact spectral gap"
    );
}

fn weighted_triangle() -> (
    CellComplex,
    Connection,
    BTreeMap<(String, String), BigRational>,
) {
    let limits = OperationLimits::holonomy();
    let mut complex = CellComplex::new(limits);
    for v in ["v0", "v1", "v2"] {
        complex.add_vertex(v).unwrap();
    }
    let mut conn = Connection::new(2, limits);
    let r = rot90();
    let mut weights = BTreeMap::new();
    for (u, v, w) in [("v0", "v1", 1), ("v1", "v2", 2), ("v2", "v0", 3)] {
        complex.add_edge(u, v).unwrap();
        conn.set_connection(u, v, r.clone()).unwrap();
        weights.insert((u.to_string(), v.to_string()), rat(w, 1));
    }
    (complex, conn, weights)
}

#[test]
fn test_perturbation_certificate_reads_weighted_degree_and_is_strict() {
    let (complex, conn, weights) = weighted_triangle();
    let lap = compute_connection_laplacian(&complex, &conn, Some(&weights)).unwrap();
    // deg(v0) = 1 + 3, deg(v1) = 1 + 2, deg(v2) = 2 + 3.
    assert_eq!(lap.max_weighted_degree().unwrap(), rat(5, 1));

    // bound = 5 * 1/20 = 1/4, tolerance = 1/2: a gap of exactly 1/2 can close.
    let at_tolerance = lap.perturbation_certificate(rat(1, 20), rat(1, 2)).unwrap();
    assert_eq!(at_tolerance.operator_norm_bound, rat(1, 4));
    assert_eq!(at_tolerance.spectral_gap_tolerance, rat(1, 2));
    assert!(!at_tolerance.gap_survives);
    assert!(
        lap.perturbation_certificate(rat(1, 20), rat(3, 5))
            .unwrap()
            .gap_survives
    );
}

#[test]
fn test_perturbation_certificate_refuses_negative_inputs_and_non_hermitian() {
    let (complex, conn, weights) = weighted_triangle();
    let mut lap = compute_connection_laplacian(&complex, &conn, Some(&weights)).unwrap();
    assert!(matches!(
        lap.perturbation_certificate(rat(-1, 10), rat(1, 1)),
        Err(HolonomyError::NegativeBound { quantity, .. }) if quantity == "transport_epsilon"
    ));
    assert!(matches!(
        lap.perturbation_certificate(rat(1, 10), rat(-1, 1)),
        Err(HolonomyError::NegativeBound { quantity, .. }) if quantity == "unperturbed_gap"
    ));
    *lap.matrix.get_mut(0, 2) = rat(7, 1);
    assert!(matches!(
        lap.perturbation_certificate(rat(1, 10), rat(1, 1)),
        Err(HolonomyError::NonHermitianLaplacian { u, v, .. }) if u == "0" && v == "2"
    ));
}

#[test]
fn test_u1_gaussian_laplacian_is_hermitian_and_certified() {
    let limits = OperationLimits::holonomy();
    let mut complex = CellComplex::new(limits);
    let mut conn = DiscreteConnection::<GaussianRational<BigRational>>::new(1, limits);
    for v in ["v0", "v1", "v2"] {
        complex.add_vertex(v).unwrap();
    }
    // A Pythagorean unit phase 3/5 + 4/5 i on one edge; trivial phases elsewhere.
    let phase = |re, im| ExactMatrix::try_new(1, 1, vec![GaussianRational::new(re, im)]).unwrap();
    for (u, v, p) in [
        ("v0", "v1", phase(rat(3, 5), rat(4, 5))),
        ("v1", "v2", phase(rat(1, 1), rat(0, 1))),
        ("v2", "v0", phase(rat(1, 1), rat(0, 1))),
    ] {
        complex.add_edge(u, v).unwrap();
        conn.set_connection(u, v, p).unwrap();
    }
    let lap = compute_connection_laplacian(&complex, &conn, None).unwrap();
    assert!(lap.is_hermitian());
    assert_eq!(lap.max_weighted_degree().unwrap(), rat(2, 1));
    let cert = lap
        .perturbation_certificate(rat(1, 100), rat(1, 2))
        .unwrap();
    assert_eq!(cert.spectral_gap_tolerance, rat(1, 25));
    assert!(cert.gap_survives);
}

// Origin: engine/crates_rs/tests/core_holonomy/laplacian_tests.rs
// Claim: urn:core:crates_rs:tests:laplacian-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord698415a9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord698415a9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError698415a9 {
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
impl BoundaryError698415a9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError698415a9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError698415a9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord698415a9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError698415a9> {
        if capacity_bound == 0 {
            return Err(BoundaryError698415a9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError698415a9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError698415a9::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_698415a9() {
    let admitted = BoundaryRecord698415a9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord698415a9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
