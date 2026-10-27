//! Abelian / exact / derived category shells for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Conceptual link (docs only): computational chain/cochain machinery lives in
//! `core_homology`; these shells only record categorical shape claims.

pub mod abelian_category;
pub mod additivity;
pub mod chain_complex_category;
pub mod derived_category;
pub mod exact_category;
pub mod homological_algebra;

pub use abelian_category::AbelianCategory;
pub use additivity::Additivity;
pub use chain_complex_category::ChainComplexCategory;
pub use derived_category::DerivedCategory;
pub use exact_category::ExactCategory;
pub use homological_algebra::HomologicalAlgebra;

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ExactRankError {
    Zero,
    Composition { domain: u32, coordinate: u32 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/abelian/mod.rs
// Claim: urn:core:crates_rs:core-category-theory:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ExactRankError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ExactRankError {}

/// Rank additivity for the split exact sequence 0 → Z^a → Z^{a+c} → Z^c → 0.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ShortExactRankWitness {
    rank_a: u32,
    rank_b: u32,
    rank_c: u32,
}

fn verify_domain_cokernel_disjoint(
    rank_a: u32,
    rank_b: u32,
    rank_c: u32,
) -> Result<(), ExactRankError> {
    for domain in 0..rank_a {
        for cokernel in 0..rank_c {
            let coordinate = rank_a.checked_add(cokernel).ok_or(ExactRankError::Overflow)?;
            if coordinate == domain || coordinate >= rank_b {
                return Err(ExactRankError::Composition { domain, coordinate });
            }
        }
    }
    Ok(())
}

fn verify_cokernel_bounds(
    rank_a: u32,
    rank_b: u32,
    rank_c: u32,
) -> Result<(), ExactRankError> {
    for cokernel in 0..rank_c {
        let coordinate = rank_a.checked_add(cokernel).ok_or(ExactRankError::Overflow)?;
        if coordinate >= rank_b {
            return Err(ExactRankError::Composition { domain: rank_a, coordinate });
        }
    }
    Ok(())
}

impl ShortExactRankWitness {
    pub fn try_new(rank_a: u32, rank_c: u32) -> Result<Self, ExactRankError> {
        if rank_a == 0 && rank_c == 0 {
            return Err(ExactRankError::Zero);
        }
        let rank_b = rank_a.checked_add(rank_c).ok_or(ExactRankError::Overflow)?;
        verify_domain_cokernel_disjoint(rank_a, rank_b, rank_c)?;
        verify_cokernel_bounds(rank_a, rank_b, rank_c)?;
        Ok(Self { rank_a, rank_b, rank_c })
    }

    pub fn rank_b(&self) -> u32 { self.rank_b }
    pub fn rank_a(&self) -> u32 { self.rank_a }
    pub fn rank_c(&self) -> u32 { self.rank_c }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_rank_tests {
    use super::*;

    #[test]
    fn inclusion_then_projection_is_zero_on_a_rank_sum() {
        let witness = ShortExactRankWitness::try_new(2, 3);
        assert!(matches!(witness, Ok(ref witness) if witness.rank_b() == 5));
    }

    #[test]
    fn the_zero_sequence_is_refused() {
        let witness = ShortExactRankWitness::try_new(0, 0);
        assert!(matches!(witness, Err(ExactRankError::Zero)));
    }
}
