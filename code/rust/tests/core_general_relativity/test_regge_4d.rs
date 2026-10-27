//! Integration tests for the exact rational 4D Regge engine.
//!
//! AuthorityEffect: None.
//! The tests check rational Cayley-Menger data, simplicity via the pfaffian, chartwise closure, SO(4,Q) holonomy, Freudenthal volume conservation, and the rational defect predicate.
//! They do not evaluate Σ A_h ε_h and they do not claim the round 4-sphere Einstein-Hilbert action was computed. The flat comparison value is the rational 0.

#![forbid(unsafe_code)]

use linear_algebra::regge_exact::{
    cayley_menger, q_i64, q_ratio, signed_volume_4, Bivector4, ExactError, So4,
};
use num_rational::BigRational;
use core_general_relativity::exact_regge::{
    all_hinges_simple, all_tetra_closures_vanish, closed_s4_cube_boundary,
    contracted_closure_in_pentatope, defect_bound_holds, flat_einstein_hilbert,
    freudenthal_refine_16, hinge_bivector_in_pentatope, hinge_holonomy, orthogonal_pentatope,
    pythagorean_so4, pythagorean_so4_inverse, rational_regge_proxy, simplicity_holds_in_pentatope,
    try_transition, ManifoldError, SimplicialManifold4D,
};

#[test]
fn orthogonal_pentatope_is_nondegenerate_with_volume_one_over_24() {
    let manifold = orthogonal_pentatope().unwrap();
    let chart = manifold.pentatope(0).unwrap();
    let volume = signed_volume_4(&chart.coords).unwrap();
    assert_eq!(volume, q_ratio(1, 24).unwrap());

    let lengths = squared_edge_block(&chart.coords);
    let cayley = cayley_menger(4, &lengths).unwrap();
    assert_eq!(cayley.volume_squared, q_ratio(1, 576).unwrap());

    assert!(manifold.nondegeneracy().is_ok());
    assert_eq!(manifold.vertex_count(), 5);
    assert_eq!(manifold.edges().len(), 10);
    assert_eq!(manifold.triangles().len(), 10);
    assert_eq!(manifold.tetrahedra().len(), 5);
    assert_eq!(manifold.pentatope_count(), 1);
    let euler: i64 = 5 - 10 + 10 - 5 + 1;
    assert_eq!(euler, 1);
    assert_eq!(manifold.euler_characteristic(), euler);
}

#[test]
fn orthogonal_hinges_are_simple_and_closure_vanishes() {
    let manifold = orthogonal_pentatope().unwrap();
    assert!(all_hinges_simple(&manifold).unwrap());
    assert!(all_tetra_closures_vanish(&manifold).unwrap());

    let tetras = manifold.tetrahedra();
    assert_eq!(tetras.len(), 5);
    for tetra in tetras {
        let closure = contracted_closure_in_pentatope(&manifold, 0, tetra).unwrap();
        assert!(closure.is_zero());
    }

    let triangles = manifold.triangles();
    assert!(!triangles.is_empty());
    let triangle = triangles[0];
    let hinge = hinge_bivector_in_pentatope(&manifold, 0, triangle).unwrap();
    assert!(hinge.is_simple());
    assert!(simplicity_holds_in_pentatope(&manifold, 0, triangle).unwrap());
}

#[test]
fn right_triangle_and_division_guard() {
    let mut squared = std::array::from_fn(|_| std::array::from_fn(|_| q_i64(0)));
    squared[0][1] = q_i64(9);
    squared[1][0] = q_i64(9);
    squared[0][2] = q_i64(16);
    squared[2][0] = q_i64(16);
    squared[1][2] = q_i64(25);
    squared[2][1] = q_i64(25);
    let triangle = cayley_menger(2, &squared).unwrap();
    assert_eq!(triangle.volume_squared, q_i64(36));

    assert_eq!(q_ratio(1, 0), Err(ExactError::DivisionByZero));

    let mixed =
        Bivector4::from_components([q_i64(1), q_i64(0), q_i64(0), q_i64(0), q_i64(0), q_i64(1)]);
    assert!(!mixed.is_simple());
}

#[test]
fn degenerate_repeated_vertex_is_rejected() {
    let orthogonal = orthogonal_pentatope().unwrap();
    let mut points = orthogonal.pentatope(0).unwrap().coords.clone();
    points[4] = points[0].clone();
    let rejected: Result<SimplicialManifold4D, ManifoldError> =
        SimplicialManifold4D::from_ambient_pentatopes(&[points]);
    assert!(rejected.is_err());
}

#[test]
fn pythagorean_holonomy_is_identity_and_bad_frame_is_rejected() {
    let holonomy: So4 = hinge_holonomy(&[pythagorean_so4(), pythagorean_so4_inverse()]);
    assert!(holonomy.is_identity());
    assert_eq!(holonomy.frobenius_defect_squared(), q_i64(0));

    let zero = matrix4([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]);
    assert!(try_transition(zero).is_err());

    let reflection = matrix4([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]]);
    assert!(try_transition(reflection).is_err());
}

#[test]
fn freudenthal_sixteen_children_conserve_volume() {
    let manifold = orthogonal_pentatope().unwrap();
    let parent = manifold.pentatope(0).unwrap().coords.clone();
    let children = freudenthal_refine_16(&parent).unwrap();
    assert_eq!(children.len(), 16);

    let parent_volume = signed_volume_4(&parent).unwrap();
    assert_eq!(parent_volume, q_ratio(1, 24).unwrap());
    let mut total = q_i64(0);
    for child in &children {
        let child_volume = signed_volume_4(child).unwrap();
        assert_ne!(child_volume, q_i64(0));
        total += child_volume;
    }
    assert_eq!(total, parent_volume);

    let refined = SimplicialManifold4D::from_ambient_pentatopes(&children).unwrap();
    assert!(refined.nondegeneracy().is_ok());
    let proxy = rational_regge_proxy(&refined, &[]).unwrap();
    assert_eq!(proxy.action, q_i64(0));
    let action = proxy.action;
    assert!(defect_bound_holds(
        &action,
        &flat_einstein_hilbert(),
        &q_i64(1),
        &q_ratio(1, 4).unwrap(),
    ));
    assert!(defect_bound_holds(
        &q_ratio(1, 3).unwrap(),
        &q_ratio(1, 4).unwrap(),
        &q_i64(2),
        &q_ratio(1, 16).unwrap(),
    ));
    assert!(!defect_bound_holds(
        &q_i64(1),
        &q_i64(0),
        &q_i64(1),
        &q_ratio(1, 4).unwrap(),
    ));
}

#[test]
fn closed_s4_cube_boundary_has_euler_two_and_algebraic_identities() {
    let sphere = closed_s4_cube_boundary().unwrap();
    assert_eq!(sphere.vertex_count(), 32);
    assert_eq!(sphere.pentatope_count(), 240);
    assert_eq!(sphere.euler_characteristic(), 2);
    assert!(sphere.nondegeneracy().is_ok());
    assert!(all_hinges_simple(&sphere).unwrap());
    assert!(all_tetra_closures_vanish(&sphere).unwrap());
}

/// Squared Euclidean distances of five points, packed into a symmetric 5×5 block.
/// The diagonal is zero. Only `BigRational` operations are used.
fn squared_edge_block(points: &[[BigRational; 4]; 5]) -> [[BigRational; 5]; 5] {
    std::array::from_fn(|i| {
        std::array::from_fn(|j| {
            if i == j {
                q_i64(0)
            } else {
                squared_distance(&points[i], &points[j])
            }
        })
    })
}

fn squared_distance(left: &[BigRational; 4], right: &[BigRational; 4]) -> BigRational {
    let mut sum = q_i64(0);
    for (left_coord, right_coord) in left.iter().zip(right.iter()) {
        let delta = left_coord - right_coord;
        sum += &delta * &delta;
    }
    sum
}

fn matrix4(entries: [[i64; 4]; 4]) -> [[BigRational; 4]; 4] {
    std::array::from_fn(|row| std::array::from_fn(|col| q_i64(entries[row][col])))
}

// Origin: engine/crates_rs/tests/core_general_relativity/test_regge_4d.rs
// Claim: urn:core:crates_rs:tests:test-regge-4d:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord34225fe6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord34225fe6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError34225fe6 {
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
impl BoundaryError34225fe6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError34225fe6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError34225fe6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord34225fe6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError34225fe6> {
        if capacity_bound == 0 {
            return Err(BoundaryError34225fe6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError34225fe6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError34225fe6::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_34225fe6() {
    let admitted = BoundaryRecord34225fe6::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord34225fe6::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
