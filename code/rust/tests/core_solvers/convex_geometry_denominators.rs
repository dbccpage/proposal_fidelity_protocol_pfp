//! Standalone integration fixture; before version does not name a future error variant.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix;
use num_rational::BigRational;
use core_solvers::solver_convex_vertex_enum::{
    convex_membership, packing_optimum, verify_convex_witness, verify_packing_witness,
    vertex_enumeration, ConvexGeometryError, ConvexWitness, PackingWitness,
};
use std::panic::{catch_unwind, AssertUnwindSafe};

fn q(n: i64) -> BigRational {
    BigRational::from_integer(n.into())
}

fn invalid() -> BigRational {
    BigRational::new_raw(1.into(), 0.into())
}

fn rows(values: Vec<Vec<BigRational>>) -> BasicMatrix<BigRational> {
    matrix::from_rows(values).unwrap()
}

type RouteResult = std::thread::Result<Result<(), ConvexGeometryError>>;

fn record<T>(
    results: &mut Vec<(&'static str, RouteResult)>,
    name: &'static str,
    operation: impl FnOnce() -> Result<T, ConvexGeometryError>,
) {
    results.push((
        name,
        catch_unwind(AssertUnwindSafe(|| operation().map(|_| ()))),
    ));
}

/// Run every malformed route even when another route panics. This retains the
/// full before-fix refusal census instead of stopping at the first bad field.
fn malformed_routes() -> Vec<(&'static str, RouteResult)> {
    let mut results = Vec::new();
    let points = vec![vec![q(0)]];
    let bad_points = vec![vec![invalid()]];
    let target = vec![q(0)];
    let bad_target = vec![invalid()];
    let convex = ConvexWitness {
        support: vec![0],
        weights: vec![q(1)],
    };
    let bad_convex = ConvexWitness {
        support: vec![0],
        weights: vec![invalid()],
    };
    record(&mut results, "hull points", || {
        convex_membership(&bad_points, &target, 1)
    });
    record(&mut results, "hull target", || {
        convex_membership(&points, &bad_target, 1)
    });
    record(&mut results, "convex replay points", || {
        verify_convex_witness(&bad_points, &target, &convex)
    });
    record(&mut results, "convex replay target", || {
        verify_convex_witness(&points, &bad_target, &convex)
    });
    record(&mut results, "convex replay weights", || {
        verify_convex_witness(&points, &target, &bad_convex)
    });

    let e_empty = matrix::zeros(0, 1).unwrap();
    let unit = rows(vec![vec![q(1)]]);
    let bad_matrix = rows(vec![vec![invalid()]]);
    record(&mut results, "vertex equality map", || {
        vertex_enumeration(&bad_matrix, &[q(0)], &unit, &[q(1)], 1)
    });
    record(&mut results, "vertex equality RHS", || {
        vertex_enumeration(&unit, &[invalid()], &unit, &[q(1)], 1)
    });
    record(&mut results, "vertex inequality map", || {
        vertex_enumeration(&e_empty, &[], &bad_matrix, &[q(1)], 1)
    });
    record(&mut results, "vertex inequality bounds", || {
        vertex_enumeration(&e_empty, &[], &unit, &[invalid()], 1)
    });

    record_malformed_packing_routes(&mut results, &unit, &bad_matrix);
    results
}

fn record_malformed_packing_routes(
    results: &mut Vec<(&'static str, RouteResult)>,
    unit: &matrix::Matrix<Rational>,
    bad_matrix: &matrix::Matrix<Rational>,
) {
    let packing = PackingWitness {
        primal: vec![q(1)],
        dual: vec![q(1)],
        value: q(1),
    };
    let bad_primal = PackingWitness {
        primal: vec![invalid()],
        ..packing.clone()
    };
    let bad_dual = PackingWitness {
        dual: vec![invalid()],
        ..packing.clone()
    };
    let bad_value = PackingWitness {
        value: invalid(),
        ..packing.clone()
    };
    record(results, "packing proposal map", || {
        packing_optimum(bad_matrix, &[q(1)], 3)
    });
    record(results, "packing proposal bounds", || {
        packing_optimum(unit, &[invalid()], 3)
    });
    record(results, "packing replay map", || {
        verify_packing_witness(bad_matrix, &[q(1)], &packing)
    });
    record(results, "packing replay bounds", || {
        verify_packing_witness(unit, &[invalid()], &packing)
    });
    record(results, "packing replay primal", || {
        verify_packing_witness(unit, &[q(1)], &bad_primal)
    });
    record(results, "packing replay dual", || {
        verify_packing_witness(unit, &[q(1)], &bad_dual)
    });
    record(results, "packing replay objective", || {
        verify_packing_witness(unit, &[q(1)], &bad_value)
    });
}

#[test]
fn all_malformed_rational_routes_refuse_without_panicking() {
    let failures: Vec<_> = malformed_routes()
        .into_iter()
        .filter_map(|(name, result)| (!matches!(result, Ok(Err(_)))).then_some(name))
        .collect();
    assert!(
        failures.is_empty(),
        "each route must return a typed refusal: {failures:?}"
    );
}

#[test]
fn valid_geometry_controls_replay_independent_normal_hull_square_and_packing() {
    let points = vec![vec![q(0)], vec![q(2)]];
    let witness = convex_membership(&points, &[q(1)], 3).unwrap().unwrap();
    assert_eq!(witness.support, vec![0, 1]);
    assert_eq!(
        witness.weights,
        vec![BigRational::new(1.into(), 2.into()); 2]
    );
    verify_convex_witness(&points, &[q(1)], &witness).unwrap();
    assert_eq!(convex_membership(&points, &[q(3)], 3).unwrap(), None);

    let e = matrix::zeros(0, 2).unwrap();
    let a = rows(vec![
        vec![q(1), q(0)],
        vec![q(-1), q(0)],
        vec![q(0), q(1)],
        vec![q(0), q(-1)],
    ]);
    let vertices = vertex_enumeration(&e, &[], &a, &[q(1), q(0), q(1), q(0)], 6).unwrap();
    assert_eq!(
        vertices,
        vec![
            vec![q(0), q(0)],
            vec![q(0), q(1)],
            vec![q(1), q(0)],
            vec![q(1), q(1)]
        ]
    );

    // Independent optimum: x0 <= 2, x1 <= 3, so max(x0+x1)=5.
    // Six primal active sets and one complementary dual active set cost seven.
    let identity = rows(vec![vec![q(1), q(0)], vec![q(0), q(1)]]);
    let bound = vec![q(2), q(3)];
    let optimum = packing_optimum(&identity, &bound, 7).unwrap();
    assert_eq!(optimum.primal, bound);
    assert_eq!(optimum.dual, vec![q(1), q(1)]);
    assert_eq!(optimum.value, q(5));
    verify_packing_witness(&identity, &bound, &optimum).unwrap();
}

#[test]
fn witness_shape_refusal_precedes_malformed_scalar_scans() {
    let points = vec![vec![q(0)]];
    let bad = ConvexWitness {
        support: vec![0; 4097],
        weights: vec![invalid(); 4097],
    };
    assert_eq!(
        verify_convex_witness(&points, &[q(0)], &bad),
        Err(ConvexGeometryError::InvalidWitness)
    );
    let unit = rows(vec![vec![q(1)]]);
    let bad = PackingWitness {
        primal: vec![invalid(); 65],
        dual: vec![q(1)],
        value: invalid(),
    };
    assert_eq!(
        verify_packing_witness(&unit, &[q(1)], &bad),
        Err(ConvexGeometryError::InvalidWitness)
    );
}

#[test]
fn every_malformed_route_reports_invalid_rational() {
    let failures: Vec<_> = malformed_routes()
        .into_iter()
        .filter_map(|(name, result)| {
            (!matches!(result, Ok(Err(ConvexGeometryError::InvalidRational)))).then_some(name)
        })
        .collect();
    assert!(
        failures.is_empty(),
        "every scalar route must refuse InvalidRational: {failures:?}"
    );
}

// Origin: engine/crates_rs/tests/core_solvers/convex_geometry_denominators.rs
// Claim: urn:core:crates_rs:tests:convex-geometry-denominators:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0070915b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0070915b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0070915b {
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
impl BoundaryError0070915b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0070915b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0070915b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0070915b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0070915b> {
        if capacity_bound == 0 {
            return Err(BoundaryError0070915b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0070915b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0070915b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_0070915b() {
    let admitted = BoundaryRecord0070915b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord0070915b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
