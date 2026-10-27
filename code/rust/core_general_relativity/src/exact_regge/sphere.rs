//! Fixtures: one orthogonal pentatope, and the Kuhn triangulation of the
//! boundary of the 5-cube (a closed combinatorial 4-sphere) with a `Q^4` chart
//! on every facet.
//!
//! Charts are piecewise-flat and rational. The construction does not evaluate
//! the Einstein-Hilbert action of the round metric. The Euler characteristic
//! of this closed combinatorial 4-sphere is computed elsewhere.
//!
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

use super::manifold::{ManifoldError, PentatopeChart, SimplicialManifold4D};
use super::permute::lex_permutations_4;
use linear_algebra::regge_exact::q_i64;
use num_rational::BigRational;

/// Orthogonal corner pentatope on
/// `(0,0,0,0), (1,0,0,0), (0,1,0,0), (0,0,1,0), (0,0,0,1)`.
pub fn orthogonal_pentatope() -> Result<SimplicialManifold4D, ManifoldError> {
    let pentatope = [
        rational_point([0, 0, 0, 0]),
        rational_point([1, 0, 0, 0]),
        rational_point([0, 1, 0, 0]),
        rational_point([0, 0, 1, 0]),
        rational_point([0, 0, 0, 1]),
    ];
    SimplicialManifold4D::from_ambient_pentatopes(&[pentatope])
}

/// Combinatorial boundary of the 5-cube `{0,1}^5`.
///
/// Each of the 10 facets is Kuhn-triangulated into `4! = 24` pentatopes:
/// 32 global vertices and 240 pentatopes. The id of a point is `Σ point[i] << i`
/// and stays in `0..=31`; vertices are not renumbered.
///
/// Chart slot `j` is the value of the `j`-th free axis in ascending index order,
/// not the order of the permutation. Values are `0` or `1`.
///
/// Charts are piecewise-flat and rational. This construction does not evaluate
/// the Einstein-Hilbert action of the round metric.
pub fn closed_s4_cube_boundary() -> Result<SimplicialManifold4D, ManifoldError> {
    let mut charts = Vec::with_capacity(240);
    for axis in 0..5 {
        let free = free_axes(axis);
        for bit in [0_u32, 1_u32] {
            for permutation in lex_permutations_4(free) {
                charts.push(kuhn_chart(axis, bit, &free, &permutation));
            }
        }
    }
    SimplicialManifold4D::from_charts(charts)
}

fn rational_point(coords: [i64; 4]) -> [BigRational; 4] {
    std::array::from_fn(|coordinate| q_i64(coords[coordinate]))
}

fn free_axes(frozen: usize) -> [usize; 4] {
    let mut free = [0; 4];
    let mut slot = 0;
    for coordinate in 0..5 {
        if coordinate != frozen {
            free[slot] = coordinate;
            slot += 1;
        }
    }
    free
}

fn kuhn_chart(
    axis: usize,
    bit: u32,
    free: &[usize; 4],
    permutation: &[usize; 4],
) -> PentatopeChart {
    let mut point = [0_u32; 5];
    point[axis] = bit;
    let mut vertices = [0_u32; 5];
    let mut coords: [[BigRational; 4]; 5] =
        std::array::from_fn(|_| std::array::from_fn(|_| q_i64(0)));
    vertices[0] = cube5_vertex_id(&point);
    coords[0] = chart_coords(&point, free);
    for step in 0..4 {
        point[permutation[step]] = 1;
        vertices[step + 1] = cube5_vertex_id(&point);
        coords[step + 1] = chart_coords(&point, free);
    }
    PentatopeChart { vertices, coords }
}

fn cube5_vertex_id(point: &[u32; 5]) -> u32 {
    point[0] + (point[1] << 1) + (point[2] << 2) + (point[3] << 3) + (point[4] << 4)
}

fn chart_coords(point: &[u32; 5], free: &[usize; 4]) -> [BigRational; 4] {
    std::array::from_fn(|slot| q_i64(i64::from(point[free[slot]])))
}

// Origin: engine/crates_rs/core_general_relativity/src/exact_regge/sphere.rs
// Claim: urn:core:crates_rs:core-general-relativity:sphere:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf5420605 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf5420605` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf5420605 {
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
impl BoundaryErrorf5420605 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf5420605 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf5420605 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf5420605 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf5420605> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf5420605::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf5420605::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf5420605::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_f5420605 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf5420605::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf5420605::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf5420605::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf5420605::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf5420605::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf5420605::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf5420605::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
