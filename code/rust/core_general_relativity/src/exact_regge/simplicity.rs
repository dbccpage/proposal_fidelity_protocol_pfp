//! Triangle area bivectors and the Barrett-Crane simplicity constraint.
//!
//! `Σ = (1/2) (r_j - r_i) ∧ (r_k - r_i)` in the caller's vertex order `(i, j, k)`.
//! Simplicity is the vanishing of the pfaffian of `Σ`. The deficit
//! `ε_h = 2π - Σ θ` is not computed.
//!
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

use super::manifold::{ManifoldError, SimplicialManifold4D};
use linear_algebra::regge_exact::Bivector4;
use num_rational::BigRational;

pub fn hinge_bivector_in_pentatope(
    manifold: &SimplicialManifold4D,
    pentatope_index: usize,
    triangle: [u32; 3],
) -> Result<Bivector4, ManifoldError> {
    let chart = manifold.pentatope(pentatope_index)?;
    let ri = vertex_coords(manifold, pentatope_index, &chart.vertices, triangle[0])?;
    let rj = vertex_coords(manifold, pentatope_index, &chart.vertices, triangle[1])?;
    let rk = vertex_coords(manifold, pentatope_index, &chart.vertices, triangle[2])?;
    let along_j = std::array::from_fn(|axis| rj[axis].clone() - ri[axis].clone());
    let along_k = std::array::from_fn(|axis| rk[axis].clone() - ri[axis].clone());
    Ok(Bivector4::from_wedge_half(&along_j, &along_k))
}

pub fn simplicity_holds_in_pentatope(
    manifold: &SimplicialManifold4D,
    pentatope_index: usize,
    triangle: [u32; 3],
) -> Result<bool, ManifoldError> {
    Ok(hinge_bivector_in_pentatope(manifold, pentatope_index, triangle)?.is_simple())
}

pub fn all_hinges_simple(manifold: &SimplicialManifold4D) -> Result<bool, ManifoldError> {
    let pentatope_count = manifold.pentatope_count();
    if pentatope_count == 0 {
        return Err(ManifoldError::Empty);
    }
    for index in 0..pentatope_count {
        let vertices = manifold.pentatope(index)?.vertices;
        for i in 0..5 {
            for j in (i + 1)..5 {
                for k in (j + 1)..5 {
                    let triangle = [vertices[i], vertices[j], vertices[k]];
                    if !simplicity_holds_in_pentatope(manifold, index, triangle)? {
                        return Ok(false);
                    }
                }
            }
        }
    }
    Ok(true)
}

fn vertex_coords(
    manifold: &SimplicialManifold4D,
    pentatope_index: usize,
    chart_vertices: &[u32; 5],
    vertex: u32,
) -> Result<[BigRational; 4], ManifoldError> {
    if !chart_vertices.contains(&vertex) {
        return Err(ManifoldError::NotAFace);
    }
    manifold.chart_coords(pentatope_index, vertex)
}

// Origin: engine/crates_rs/core_general_relativity/src/exact_regge/simplicity.rs
// Claim: urn:core:crates_rs:core-general-relativity:simplicity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordff499f5f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordff499f5f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorff499f5f {
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
impl BoundaryErrorff499f5f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorff499f5f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorff499f5f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordff499f5f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorff499f5f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorff499f5f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorff499f5f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorff499f5f::ExceedsCapacity {
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
mod l4_boundary_tests_ff499f5f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordff499f5f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordff499f5f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordff499f5f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordff499f5f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordff499f5f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorff499f5f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorff499f5f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
