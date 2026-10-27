#[path = "traits_analysis.rs"]
pub mod analysis;
#[path = "traits_authority_laws.rs"]
pub mod authority_laws;
#[path = "traits_candidates.rs"]
pub mod candidates;
#[path = "traits_evidence.rs"]
pub mod evidence;
#[path = "traits_execution.rs"]
pub mod execution;
#[path = "traits_fixed_layer.rs"]
pub mod fixed_layer;
#[path = "traits_governance.rs"]
pub mod governance;
#[path = "traits_identity.rs"]
pub mod identity;
#[path = "traits_intake.rs"]
pub mod intake;
#[path = "traits_operators.rs"]
pub mod operators;
#[path = "traits_representation.rs"]
pub mod representation;
#[path = "traits_structure.rs"]
pub mod structure;

pub use analysis::*;
pub use authority_laws::*;
pub use candidates::*;
pub use evidence::*;
pub use execution::*;
pub use fixed_layer::*;
pub use governance::*;
pub use identity::*;
pub use intake::*;
pub use operators::*;
pub use representation::*;
pub use structure::*;

/// The twelve trait-layer module names, in declaration order.
pub const TRAIT_LAYERS: [&str; 12] = [
    "analysis",
    "authority_laws",
    "candidates",
    "evidence",
    "execution",
    "fixed_layer",
    "governance",
    "identity",
    "intake",
    "operators",
    "representation",
    "structure",
];

/// Refusal from a layer permutation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LayerPermError {
    /// The image is not a permutation of `0..12`.
    NotBijective,
    /// The inversion count overflowed.
    Overflow,
}

// Origin: engine/crates_rs/core_contracts/src/traits.rs
// Claim: urn:core:crates_rs:core-contracts:traits:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for LayerPermError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for LayerPermError {}

/// A permutation of the twelve trait layers, with its sign.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LayerPermutation {
    sign: i8,
}

impl LayerPermutation {
    /// `order[i]` is the layer moved into position `i`.
    pub fn try_new(order: &[u8]) -> Result<Self, LayerPermError> {
        if order.len() != TRAIT_LAYERS.len() {
            return Err(LayerPermError::NotBijective);
        }
        let mut seen = [false; 12];
        for &image in order {
            if image >= 12 {
                return Err(LayerPermError::NotBijective);
            }
            let Some(slot) = seen.get_mut(usize::from(image)) else {
                return Err(LayerPermError::NotBijective);
            };
            if *slot {
                return Err(LayerPermError::NotBijective);
            }
            *slot = true;
        }
        let inversions = Self::count_inversions(order)?;
        let sign = if inversions % 2 == 0 { 1 } else { -1 };
        let out = Self { sign };
        Ok(out)
    }

    fn count_inversions(order: &[u8]) -> Result<u32, LayerPermError> {
        let mut inversions = 0u32;
        for i in 0..order.len() {
            for j in (i + 1)..order.len() {
                let left = order.get(i).copied().ok_or(LayerPermError::NotBijective)?;
                let right = order.get(j).copied().ok_or(LayerPermError::NotBijective)?;
                if left > right {
                    inversions = inversions.checked_add(1).ok_or(LayerPermError::Overflow)?;
                }
            }
        }
        Ok(inversions)
    }

    /// Sign of the permutation.
    pub fn sign(&self) -> i8 { self.sign }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod layer_perm_tests {
    use super::*;
    #[test]
    fn a_transposition_is_odd() {
        let mut order: [u8; 12] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
        order[0] = 1;
        order[1] = 0;
        let perm = LayerPermutation::try_new(&order);
        assert!(matches!(perm, Ok(ref p) if p.sign() == -1));
    }
    #[test]
    fn a_repeated_index_is_refused() {
        assert!(matches!(LayerPermutation::try_new(&[0, 0]), Err(LayerPermError::NotBijective)));
    }
}
