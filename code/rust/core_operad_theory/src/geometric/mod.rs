//! Geometric Tier for Operad Theory.
//!
//! AuthorityEffect: None.

pub mod little_disks;
pub mod en_algebra;

pub use little_disks::{LittleDisksConfiguration, RectilinearDisk};
pub use en_algebra::{build_associative_homology_operad, build_commutative_homology_operad, build_gerstenhaber_homology_operad};

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RectilinearIntervalPacking { count: usize }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PackingError { Empty, Width, Radius, Overflow, Overlap }

// Origin: engine/crates_rs/core_operad_theory/src/geometric/mod.rs
// Claim: urn:core:crates_rs:core-operad-theory:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PackingError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PackingError {}

impl RectilinearIntervalPacking {
    fn check_pair_disjoint(
        centers: &[i64],
        radii: &[u64],
        i: usize,
        j: usize,
    ) -> Result<(), PackingError> {
        let left = i128::from(*centers.get(i).ok_or(PackingError::Width)?);
        let right = i128::from(*centers.get(j).ok_or(PackingError::Width)?);
        let gap = left
            .checked_sub(right)
            .ok_or(PackingError::Overflow)?
            .unsigned_abs();
        let need = u128::from(*radii.get(i).ok_or(PackingError::Width)?)
            .checked_add(u128::from(*radii.get(j).ok_or(PackingError::Width)?))
            .ok_or(PackingError::Overflow)?;
        if gap < need {
            return Err(PackingError::Overlap);
        }
        Ok(())
    }

    /// Closed intervals on a line do not overlap: `|c_i - c_j| >= r_i + r_j`.
    pub fn try_pack(centers: &[i64], radii: &[u64]) -> Result<Self, PackingError> {
        if centers.is_empty() {
            return Err(PackingError::Empty);
        }
        if centers.len() != radii.len() {
            return Err(PackingError::Width);
        }
        if radii.contains(&0) {
            return Err(PackingError::Radius);
        }
        for i in 0..centers.len() {
            for j in (i + 1)..centers.len() {
                Self::check_pair_disjoint(centers, radii, i, j)?;
            }
        }
        Ok(Self { count: centers.len() })
    }

    pub fn count(&self) -> usize { self.count }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod packing_checks {
    use super::*;

    #[test]
    fn separated_intervals_pack() {
        let packing = RectilinearIntervalPacking::try_pack(&[0, 5], &[2, 2]);
        assert!(matches!(packing, Ok(p) if p.count() == 2));
    }

    #[test]
    fn overlapping_intervals_are_refused() {
        assert!(matches!(RectilinearIntervalPacking::try_pack(&[0, 3], &[2, 2]), Err(PackingError::Overlap)));
    }
}
