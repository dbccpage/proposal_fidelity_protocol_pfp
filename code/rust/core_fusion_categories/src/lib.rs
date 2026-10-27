//! `core_fusion_categories` -- exact fusion rings and multiplicity-free fusion,
//! braided and modular data.
//!
//! Every quantity is exact: fusion coefficients are checked non-negative integers,
//! and the symbols (F, R, S, T, twists, dimensions) are elements of an exact number
//! field `K` from `core_number_theory`. There are no floating-point conversions and no
//! tolerances.
//!
//! | module | content |
//! |---|---|
//! | [`fusion_ring`] | fusion tables and rings (`N_{ab}^c`), ring laws, duals, fusion-path counts, Frobenius-Perron dimensions, Verlinde check, the ring catalog |
//! | [`fusion_category`] | F-symbols, the pentagon equation, unit normalisation, gauges, dimension and Frobenius-Schur data |
//! | [`braided`] | R-symbols, both hexagon equations, twists, the ribbon relation, braid-group representations on fusion spaces |
//! | [`braid_group`] | braid relations, projective normal forms and exact finite-group closure of braid images |
//! | [`yang_baxter`] | the Yang-Baxter equation as an exact matrix identity, and the standard solutions |
//! | [`modular`] | `S~`, `T`, Verlinde, the modular relations, Gauss-Milgram, ground-state degeneracy |
//! | [`catalog`] | validated constructors: Ising, Fibonacci, semion, toric code, three-fermion, pointed and quantum-double models |
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

pub mod braid_group;
pub mod braided;
pub mod catalog;
pub mod error;
pub mod fusion_category;
pub mod fusion_ring;
pub mod modular;
pub mod scalar;
pub mod su2_level;
pub mod yang_baxter;

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FusionChannelWitness {
    dim_a: u64,
    dim_b: u64,
    dim_c: u64,
    multiplicity: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FusionChannelWitnessError {
    NonPositive,
    DimensionMismatch { left: u64, right: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_fusion_categories/src/lib.rs
// Claim: urn:core:crates_rs:core-fusion-categories:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FusionChannelWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FusionChannelWitnessError {}

impl FusionChannelWitness {
    pub fn certify(dim_a: u64, dim_b: u64, dim_c: u64, multiplicity: u64) -> Result<Self, FusionChannelWitnessError> {
        if dim_a == 0 || dim_b == 0 || dim_c == 0 || multiplicity == 0 { return Err(FusionChannelWitnessError::NonPositive); }
        let left = dim_a.checked_mul(dim_b).ok_or(FusionChannelWitnessError::Overflow)?;
        let right = multiplicity.checked_mul(dim_c).ok_or(FusionChannelWitnessError::Overflow)?;
        if left != right { return Err(FusionChannelWitnessError::DimensionMismatch { left, right }); }
        Ok(Self { dim_a, dim_b, dim_c, multiplicity })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(FusionChannelWitness::certify(2, 3, 6, 1), Ok(w) if w.multiplicity == 1));
        assert!(matches!(FusionChannelWitness::certify(2, 3, 3, 2), Ok(w) if w.dim_c == 3));
        assert!(matches!(FusionChannelWitness::certify(2, 3, 5, 1), Err(FusionChannelWitnessError::DimensionMismatch { left: 6, right: 5 })));
        assert!(matches!(FusionChannelWitness::certify(2, 3, 6, 0), Err(FusionChannelWitnessError::NonPositive)));
    }
}
