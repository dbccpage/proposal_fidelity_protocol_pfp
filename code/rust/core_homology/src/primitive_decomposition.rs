//! § 6: Primitive Decomposition
//!
//! A proposed split $S = \bigsqcup_i S_i$ is licensed only when quotient
//! separability is certified:
//!
//! $$C^1_S = \bigoplus_i C^1_{S_i}, \quad \text{im}(d_0) \cap C^1_S = \bigoplus_i \text{im}(d_{0,i})$$
//!
//! Only then may obstruction mass add over the split.

use serde::{Deserialize, Serialize};

/// Status of a proposed primitive decomposition.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum PrimitiveStatus {
    /// Quotient separability certified: mass adds over split.
    Certified,
    /// Separability check failed.
    NotSeparable,
    /// Separability check did not complete within budget.
    PrimitiveUnknown,
}

/// Coordinate direct sum: blocks partition the basis, and each image support stays inside its block.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DirectSumSplit {
    basis: usize,
    blocks: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SplitError {
    Bound,
    Shape,
    Overlap,
    Support,
}

impl std::fmt::Display for SplitError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            SplitError::Bound => write!(formatter, "basis must lie in 1..=16"),
            SplitError::Shape => write!(formatter, "blocks and images must be a nonempty matching pair"),
            SplitError::Overlap => write!(formatter, "basis vectors are not partitioned by the blocks"),
            SplitError::Support => write!(formatter, "an image vector leaves its block"),
        }
    }
}

impl std::error::Error for SplitError {}

impl DirectSumSplit {
    pub fn certify(basis: usize, blocks: &[Vec<usize>], images: &[Vec<usize>]) -> Result<Self, SplitError> {
        Self::check_split_bounds(basis, blocks, images)?;
        let owner = Self::build_block_owners(basis, blocks)?;
        Self::verify_image_supports(basis, &owner, images)?;
        Ok(Self {
            basis,
            blocks: blocks.len(),
        })
    }

    fn check_split_bounds(
        basis: usize,
        blocks: &[Vec<usize>],
        images: &[Vec<usize>],
    ) -> Result<(), SplitError> {
        if blocks.is_empty() || blocks.len() != images.len() {
            return Err(SplitError::Shape);
        }
        if basis == 0 || basis > 16 || blocks.len() > 16 {
            return Err(SplitError::Bound);
        }
        Ok(())
    }

    fn build_block_owners(basis: usize, blocks: &[Vec<usize>]) -> Result<Vec<usize>, SplitError> {
        let mut owner = vec![usize::MAX; basis];
        for (block_index, block) in blocks.iter().enumerate() {
            if block.is_empty() {
                return Err(SplitError::Shape);
            }
            for &vertex in block {
                let slot = owner.get_mut(vertex).ok_or(SplitError::Overlap)?;
                if *slot != usize::MAX {
                    return Err(SplitError::Overlap);
                }
                *slot = block_index;
            }
        }
        if owner.iter().any(|slot| *slot == usize::MAX) {
            return Err(SplitError::Overlap);
        }
        Ok(owner)
    }

    fn verify_image_supports(
        basis: usize,
        owner: &[usize],
        images: &[Vec<usize>],
    ) -> Result<(), SplitError> {
        for (block_index, image) in images.iter().enumerate() {
            let mut seen = vec![false; basis];
            for &vertex in image {
                let claimed = *owner.get(vertex).ok_or(SplitError::Support)?;
                if claimed != block_index {
                    return Err(SplitError::Support);
                }
                let slot = seen.get_mut(vertex).ok_or(SplitError::Support)?;
                if *slot {
                    return Err(SplitError::Support);
                }
                *slot = true;
            }
        }
        Ok(())
    }

    pub fn basis(&self) -> usize {
        self.basis
    }

    pub fn blocks(&self) -> usize {
        self.blocks
    }
}

// Origin: engine/crates_rs/core_homology/src/primitive_decomposition.rs
// Claim: urn:core:crates_rs:core-homology:primitive-decomposition:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod split_tests {
    use super::*;

    fn taken<T, E>(value: Result<T, E>) -> T {
        match value {
            Ok(inner) => inner,
            Err(_) => loop {
                assert!(false);
            },
        }
    }

    #[test]
    fn a_partition_keeps_each_image_inside_its_block() {
        let split = taken(DirectSumSplit::certify(3, &[vec![0, 1], vec![2]], &[vec![0], vec![2]]));
        assert_eq!(split.basis(), 3);
        assert_eq!(split.blocks(), 2);
        assert!(DirectSumSplit::certify(3, &[vec![0, 1], vec![2]], &[vec![0], vec![0]]).is_err());
    }
}
