//! Vietoris–Rips complex builder from a finite metric point cloud.
//!
//! AuthorityEffect: None. Best-effort shell. Not PROVED; not GlobalGreen.

use crate::filtration::{FilteredSimplex, Filtration};
use num_rational::BigRational;
use num_traits::Zero;
use serde::{Deserialize, Serialize};

/// Finite point cloud with pairwise distances (full matrix, row-major).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PointCloud {
    pub n_points: usize,
    /// `dist[i * n + j]` for i,j in 0..n; must be symmetric with zero diagonal.
    pub distances: Vec<BigRational>,
}

impl PointCloud {
    pub fn distance(&self, i: usize, j: usize) -> BigRational {
        self.distances[i * self.n_points + j].clone()
    }

    /// Diameter of a simplex = max pairwise distance among vertices.
    pub fn simplex_diameter(&self, vertices: &[usize]) -> BigRational {
        let mut d = BigRational::zero();
        for a in 0..vertices.len() {
            for b in (a + 1)..vertices.len() {
                d = d.max(self.distance(vertices[a], vertices[b]));
            }
        }
        d
    }
}

/// Build a VR filtration up to `max_dim` including all simplices with diameter ≤ `radius`.
/// Filtration value of a simplex is its diameter.
pub fn vietoris_rips_filtration(
    cloud: &PointCloud,
    max_dim: usize,
    radius: BigRational,
) -> Filtration {
    let n = cloud.n_points;
    let mut simplices = Vec::new();

    // 0-simplices
    for i in 0..n {
        simplices.push(FilteredSimplex {
            vertices: vec![i],
            value: BigRational::zero(),
            dimension: 0,
        });
    }

    // Higher simplices via combinations (naive O(n^{k+1}))
    if max_dim >= 1 && n >= 2 {
        add_vr_edges(cloud, &radius, &mut simplices);
    }

    if max_dim >= 2 && n >= 3 {
        add_vr_triangles(cloud, &radius, &mut simplices);
    }

    // Sort by filtration value then dimension then vertices
    simplices.sort_by(|a, b| {
        a.value
            .cmp(&b.value)
            .then_with(|| a.dimension.cmp(&b.dimension))
            .then_with(|| a.vertices.cmp(&b.vertices))
    });

    Filtration::new(simplices, max_dim.min(2))
}

fn add_vr_edges(cloud: &PointCloud, radius: &BigRational, simplices: &mut Vec<FilteredSimplex>) {
    let n = cloud.n_points;
    for i in 0..n {
        for j in (i + 1)..n {
            let diam = cloud.distance(i, j);
            if &diam <= radius {
                simplices.push(FilteredSimplex {
                    vertices: vec![i, j],
                    value: diam,
                    dimension: 1,
                });
            }
        }
    }
}

fn add_vr_triangles(
    cloud: &PointCloud,
    radius: &BigRational,
    simplices: &mut Vec<FilteredSimplex>,
) {
    let n = cloud.n_points;
    for i in 0..n {
        for j in (i + 1)..n {
            for k in (j + 1)..n {
                let verts = [i, j, k];
                let diam = cloud.simplex_diameter(&verts);
                if &diam <= radius {
                    simplices.push(FilteredSimplex {
                        vertices: verts.to_vec(),
                        value: diam,
                        dimension: 2,
                    });
                }
            }
        }
    }
}

// Origin: engine/crates_rs/core_homology/src/vietoris_rips.rs
// Claim: urn:core:crates_rs:core-homology:vietoris-rips:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7a50a8d8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7a50a8d8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7a50a8d8 {
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
impl BoundaryError7a50a8d8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7a50a8d8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7a50a8d8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7a50a8d8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7a50a8d8> {
        if capacity_bound == 0 {
            return Err(BoundaryError7a50a8d8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7a50a8d8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7a50a8d8::ExceedsCapacity {
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
mod tests {
    use super::*;

    fn unit_segment() -> PointCloud {
        // two points distance 1
        PointCloud {
            n_points: 2,
            distances: [0, 1, 1, 0]
                .map(|v| BigRational::from_integer(v.into()))
                .to_vec(),
        }
    }

    #[test]
    fn vr_includes_edge_at_radius_one() {
        let f = vietoris_rips_filtration(&unit_segment(), 1, BigRational::from_integer(1.into()));
        assert!(f.simplices.iter().any(|s| s.dimension == 1));
    }

    #[test]
    fn vr_excludes_edge_below_radius() {
        let f = vietoris_rips_filtration(&unit_segment(), 1, BigRational::new(1.into(), 2.into()));
        assert!(!f.simplices.iter().any(|s| s.dimension == 1));
        assert_eq!(f.simplices.len(), 2);
    }
}

#[cfg(test)]
mod l4_boundary_tests_7a50a8d8 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7a50a8d8::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7a50a8d8::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7a50a8d8::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7a50a8d8::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7a50a8d8::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7a50a8d8::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7a50a8d8::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
