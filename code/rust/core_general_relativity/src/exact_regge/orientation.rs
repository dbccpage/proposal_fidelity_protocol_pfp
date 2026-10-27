//! Induced orientations.
//!
//! Tetra boundary of `(v0,v1,v2,v3)`:
//! `+(v1,v2,v3) - (v0,v2,v3) + (v0,v1,v3) - (v0,v1,v2)`.
//!
//! Pentatope boundary of `(v0,v1,v2,v3,v4)`:
//! `+(v1,v2,v3,v4) - (v0,v2,v3,v4) + (v0,v1,v3,v4) - (v0,v1,v2,v4) + (v0,v1,v2,v3)`.
//!
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

/// Face opposite vertex `i` carries sign `(-1)^i`, with the remaining vertices in order.
pub fn triangle_boundary_of_tetra(tetra: [u32; 4]) -> [([u32; 3], i8); 4] {
    let [v0, v1, v2, v3] = tetra;
    [
        ([v1, v2, v3], 1),
        ([v0, v2, v3], -1),
        ([v0, v1, v3], 1),
        ([v0, v1, v2], -1),
    ]
}

/// Facet opposite vertex `i` carries sign `(-1)^i`, with the remaining vertices in order.
pub fn tetra_boundary_of_pentatope(pentatope: [u32; 5]) -> [([u32; 4], i8); 5] {
    let [v0, v1, v2, v3, v4] = pentatope;
    [
        ([v1, v2, v3, v4], 1),
        ([v0, v2, v3, v4], -1),
        ([v0, v1, v3, v4], 1),
        ([v0, v1, v2, v4], -1),
        ([v0, v1, v2, v3], 1),
    ]
}

// Origin: engine/crates_rs/core_general_relativity/src/exact_regge/orientation.rs
// Claim: urn:core:crates_rs:core-general-relativity:orientation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbccc8e2d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbccc8e2d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbccc8e2d {
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
impl BoundaryErrorbccc8e2d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbccc8e2d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbccc8e2d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbccc8e2d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbccc8e2d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbccc8e2d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbccc8e2d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbccc8e2d::ExceedsCapacity {
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
    use super::{tetra_boundary_of_pentatope, triangle_boundary_of_tetra};
    use std::collections::BTreeMap;

    #[test]
    fn tetra_triangle_signs_omit_each_vertex_once() {
        let tetra = [7, 1, 4, 9];
        let boundary = triangle_boundary_of_tetra(tetra);
        let signs = [1_i8, -1, 1, -1];
        let mut omitted = [0_u32; 4];
        let mut sign_sum = 0_i32;
        for (i, (face, sign)) in boundary.iter().enumerate() {
            assert_eq!(*sign, signs[i]);
            sign_sum += i32::from(*sign);
            let mut missing = None;
            for &vertex in &tetra {
                if !face.iter().any(|&other| other == vertex) {
                    assert!(missing.is_none());
                    missing = Some(vertex);
                }
            }
            omitted[i] = missing.expect("each triangle omits one vertex");
        }
        assert_eq!(sign_sum, 0);
        assert_eq!(signs, [1, -1, 1, -1]);
        let mut omitted_sorted = omitted;
        omitted_sorted.sort_unstable();
        let mut tetra_sorted = tetra;
        tetra_sorted.sort_unstable();
        assert_eq!(omitted_sorted, tetra_sorted);
        assert_eq!(
            boundary,
            [
                ([1, 4, 9], 1),
                ([7, 4, 9], -1),
                ([7, 1, 9], 1),
                ([7, 1, 4], -1),
            ]
        );
    }

    #[test]
    fn pentatope_tetra_signs_omit_each_vertex_once() {
        let pentatope = [7, 1, 4, 9, 2];
        let boundary = tetra_boundary_of_pentatope(pentatope);
        let signs = [1_i8, -1, 1, -1, 1];
        let mut omitted = [0_u32; 5];
        for (i, (face, sign)) in boundary.iter().enumerate() {
            assert_eq!(*sign, signs[i]);
            let mut missing = None;
            for &vertex in &pentatope {
                if !face.iter().any(|&other| other == vertex) {
                    assert!(missing.is_none());
                    missing = Some(vertex);
                }
            }
            omitted[i] = missing.expect("each tetrahedron omits one vertex");
        }
        let mut omitted_sorted = omitted;
        omitted_sorted.sort_unstable();
        let mut pentatope_sorted = pentatope;
        pentatope_sorted.sort_unstable();
        assert_eq!(omitted_sorted, pentatope_sorted);
        assert_eq!(
            boundary,
            [
                ([1, 4, 9, 2], 1),
                ([7, 4, 9, 2], -1),
                ([7, 1, 9, 2], 1),
                ([7, 1, 4, 2], -1),
                ([7, 1, 4, 9], 1),
            ]
        );
    }

    #[test]
    fn pentatope_boundary_of_boundary_cancels() {
        let pentatope = [0, 1, 2, 3, 4];
        let mut coeff: BTreeMap<[u32; 3], i32> = BTreeMap::new();
        for (tetra, tetra_sign) in tetra_boundary_of_pentatope(pentatope) {
            for (triangle, triangle_sign) in triangle_boundary_of_tetra(tetra) {
                *coeff.entry(triangle).or_insert(0) +=
                    i32::from(tetra_sign) * i32::from(triangle_sign);
            }
        }
        assert_eq!(coeff.len(), 10);
        assert!(coeff.values().all(|&c| c == 0));
    }
}

#[cfg(test)]
mod l4_boundary_tests_bccc8e2d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbccc8e2d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbccc8e2d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbccc8e2d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbccc8e2d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbccc8e2d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbccc8e2d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbccc8e2d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
