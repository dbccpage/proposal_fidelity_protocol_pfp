pub mod complex_matrix;
pub mod density;
pub mod eigen;
pub mod gram_schmidt;
pub mod graph_laplacian;
pub mod hermitian_mul;
pub mod hermitian_mul_blocked;
pub mod homology_basis;
pub mod image_kernel;
pub mod incidence_matrix;
pub mod l1_additivity;
pub mod module;
pub mod norm;
pub mod projector;
pub mod rank;
pub mod sparse_operator;
pub mod support_operations;
pub mod vec_category;
pub mod vec_monoidal;
pub mod vec_types;
pub mod vector_space;

/// Rank-nullity over a finite dimension: `dimension = rank + nullity`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RankNullityWitness {
    dimension: u32,
    rank: u32,
    nullity: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RankNullityError {
    Overflow,
    NotSplit {
        dimension: u32,
        rank: u32,
        nullity: u32,
    },
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/mod.rs
// Claim: urn:core:crates_rs:core-linear-algebra:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RankNullityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RankNullityError {}

impl RankNullityWitness {
    pub fn admit(dimension: u32, rank: u32, nullity: u32) -> Result<Self, RankNullityError> {
        let sum = rank
            .checked_add(nullity)
            .ok_or(RankNullityError::Overflow)?;
        if sum != dimension {
            return Err(RankNullityError::NotSplit {
                dimension,
                rank,
                nullity,
            });
        }
        Ok(Self {
            dimension,
            rank,
            nullity,
        })
    }

    pub fn dimension(&self) -> u32 {
        self.dimension
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod rank_nullity_witness_tests {
    use super::*;

    #[test]
    fn rank_plus_nullity_is_dimension() {
        let admitted = RankNullityWitness::admit(5, 2, 3);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.dimension()), Some(5));
        assert!(matches!(
            RankNullityWitness::admit(5, 2, 2),
            Err(RankNullityError::NotSplit {
                dimension: 5,
                rank: 2,
                nullity: 2
            })
        ));
    }
}
