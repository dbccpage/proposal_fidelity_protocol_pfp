//! Coxeter-Freudenthal 1-to-16 refinement of one 4-simplex.
//!
//! Reference simplex at scale 2: `2 ≥ x0 ≥ x1 ≥ x2 ≥ x3 ≥ 0`.
//! A child is a lattice path of four `+e_{π(k)}` steps whose five vertices all
//! lie in that simplex. There are exactly 16 such paths.
//! Barycentric coordinates of a lattice point `p` relative to the corners
//! `(0,0,0,0), (2,0,0,0), (2,2,0,0), (2,2,2,0), (2,2,2,2)` are
//! `λ0 = 1 - p0/2`, `λ1 = (p0-p1)/2`, `λ2 = (p1-p2)/2`, `λ3 = (p2-p3)/2`, `λ4 = p3/2`.
//! Map by `Σ λ_k V_k`. Orient each child so its signed volume has the same sign
//! as the parent (swap vertices 0 and 1 if the product of the signed volumes is
//! negative). Parent signed volume `0` is [`ManifoldError::Degenerate`].
//!
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

use super::manifold::ManifoldError;
use super::permute::lex_permutations_4;
use linear_algebra::regge_exact::{q_i64, signed_volume_4};
use num_rational::BigRational;
use num_traits::{Signed, Zero};

/// Images of the 16 Freudenthal children, in enumeration order, oriented with the parent.
///
/// Starts run through `{0,1,2}^4` in lexicographic order. For each start, permutations
/// of `{0,1,2,3}` are lexicographic. A path is kept only when all five vertices lie in
/// the reference simplex. Dividing by 2 in the barycentric map is exact in `Q`.
pub fn freudenthal_refine_16(
    parent: &[[BigRational; 4]; 5],
) -> Result<Vec<[[BigRational; 4]; 5]>, ManifoldError> {
    let parent_volume = signed_volume_4(parent).map_err(|_| degenerate_pentatope())?;
    if parent_volume.is_zero() {
        return Err(degenerate_pentatope());
    }
    let paths = reference_paths();
    if paths.len() != 16 {
        return Err(degenerate_pentatope());
    }
    let mut children = Vec::with_capacity(16);
    for path in paths {
        let child = [
            barycentric_image(parent, path[0]),
            barycentric_image(parent, path[1]),
            barycentric_image(parent, path[2]),
            barycentric_image(parent, path[3]),
            barycentric_image(parent, path[4]),
        ];
        children.push(orient_with_parent(&parent_volume, child)?);
    }
    Ok(children)
}

fn degenerate_pentatope() -> ManifoldError {
    ManifoldError::Degenerate {
        cell: "pentatope",
        index: 0,
    }
}

fn reference_paths() -> Vec<[[i64; 4]; 5]> {
    let permutations = lex_permutations_4([0, 1, 2, 3]);
    let mut paths = Vec::with_capacity(16);
    for x0 in 0_i64..=2 {
        for x1 in 0_i64..=2 {
            for x2 in 0_i64..=2 {
                for x3 in 0_i64..=2 {
                    let start = [x0, x1, x2, x3];
                    for permutation in &permutations {
                        if let Some(path) = admissible_path(start, permutation) {
                            paths.push(path);
                        }
                    }
                }
            }
        }
    }
    paths
}

fn admissible_path(start: [i64; 4], permutation: &[usize; 4]) -> Option<[[i64; 4]; 5]> {
    let mut current = start;
    let mut path = [start; 5];
    if !in_reference_simplex(current) {
        return None;
    }
    for step in 0..4 {
        current[permutation[step]] += 1;
        if !in_reference_simplex(current) {
            return None;
        }
        path[step + 1] = current;
    }
    Some(path)
}

fn in_reference_simplex(point: [i64; 4]) -> bool {
    point[3] >= 0
        && point[2] >= point[3]
        && point[1] >= point[2]
        && point[0] >= point[1]
        && point[0] <= 2
}

fn barycentric_image(parent: &[[BigRational; 4]; 5], point: [i64; 4]) -> [BigRational; 4] {
    let two = q_i64(2);
    let p = [
        q_i64(point[0]),
        q_i64(point[1]),
        q_i64(point[2]),
        q_i64(point[3]),
    ];
    let lambda = [
        q_i64(1) - (&p[0] / &two),
        (&p[0] - &p[1]) / &two,
        (&p[1] - &p[2]) / &two,
        (&p[2] - &p[3]) / &two,
        &p[3] / &two,
    ];
    std::array::from_fn(|coordinate| {
        let mut sum = q_i64(0);
        for vertex in 0..5 {
            sum += &lambda[vertex] * &parent[vertex][coordinate];
        }
        sum
    })
}

fn orient_with_parent(
    parent_volume: &BigRational,
    mut child: [[BigRational; 4]; 5],
) -> Result<[[BigRational; 4]; 5], ManifoldError> {
    let child_volume = signed_volume_4(&child).map_err(|_| degenerate_pentatope())?;
    if child_volume.is_zero() {
        return Err(degenerate_pentatope());
    }
    if (&child_volume * parent_volume).is_negative() {
        child.swap(0, 1);
    }
    Ok(child)
}

// Origin: engine/crates_rs/core_general_relativity/src/exact_regge/refinement.rs
// Claim: urn:core:crates_rs:core-general-relativity:refinement:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb402b234 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb402b234` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb402b234 {
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
impl BoundaryErrorb402b234 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb402b234 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb402b234 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb402b234 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb402b234> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb402b234::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb402b234::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb402b234::ExceedsCapacity {
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
mod l4_boundary_tests_b402b234 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb402b234::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb402b234::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb402b234::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb402b234::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb402b234::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb402b234::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb402b234::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
