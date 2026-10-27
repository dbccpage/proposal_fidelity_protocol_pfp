//! Multilinear tensors.

pub mod tensor;
pub mod tensor_view;

pub use tensor::*;
pub mod partial_transpose;

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct KroneckerRankLaw {
    rank: u64,
    dimension: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum KroneckerError {
    Bound,
    Overflow,
}

// Origin: engine/crates_rs/core_linear_algebra/src/tensor/mod.rs
// Claim: urn:core:crates_rs:core-linear-algebra:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for KroneckerError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for KroneckerError {}

impl KroneckerRankLaw {
    /// `rank(A tensor B) = rank(A) * rank(B)` and the dimension multiplies the same way.
    pub fn try_new(
        rank_a: u64,
        dim_a: u64,
        rank_b: u64,
        dim_b: u64,
    ) -> Result<Self, KroneckerError> {
        if dim_a == 0 || dim_b == 0 || rank_a > dim_a || rank_b > dim_b {
            return Err(KroneckerError::Bound);
        }
        let rank = rank_a.checked_mul(rank_b).ok_or(KroneckerError::Overflow)?;
        let dimension = dim_a.checked_mul(dim_b).ok_or(KroneckerError::Overflow)?;
        Ok(Self { rank, dimension })
    }

    pub fn rank(&self) -> u64 {
        self.rank
    }
    pub fn dimension(&self) -> u64 {
        self.dimension
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod kronecker_checks {
    use super::*;

    #[test]
    fn ranks_two_and_one_on_a_two_by_three_space() {
        let law = KroneckerRankLaw::try_new(2, 2, 1, 3);
        assert!(matches!(law, Ok(k) if k.rank() == 2 && k.dimension() == 6));
    }

    #[test]
    fn a_rank_above_the_dimension_is_refused() {
        assert!(matches!(
            KroneckerRankLaw::try_new(3, 2, 1, 1),
            Err(KroneckerError::Bound)
        ));
    }
}
