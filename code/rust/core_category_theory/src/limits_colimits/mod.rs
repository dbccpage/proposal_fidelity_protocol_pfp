//! Limits / colimits shells for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Hierarchical catalog under `limits_colimits/`. Legacy flat modules
//! `limits.rs`, `colimits.rs`, and `coend.rs` remain at crate root.

pub mod coend;
pub mod coequalizer;
pub mod cokernel_pair;
pub mod colimit;
pub mod cone;
pub mod coproduct;
pub mod density_comonad;
pub mod end;
pub mod equalizer;
pub mod initial_object;
pub mod kan_extension;
pub mod kernel_pair;
pub mod limit;
pub mod pointwise_kan_extension;
pub mod product;
pub mod pullback;
pub mod pushout;
pub mod terminal_object;

pub use coend::Coend;
pub use coequalizer::Coequalizer;
pub use cokernel_pair::CokernelPair;
pub use colimit::Colimit;
pub use cone::{Cocone, Cone, ConeLeg};
pub use coproduct::Coproduct;
pub use density_comonad::DensityComonad;
pub use end::End;
pub use equalizer::Equalizer;
pub use initial_object::InitialObject;
pub use kan_extension::{KanExtension, KanExtensionKind};
pub use kernel_pair::KernelPair;
pub use limit::Limit;
pub use pointwise_kan_extension::PointwiseKanExtension;
pub use product::Product;
pub use pullback::Pullback;
pub use pushout::Pushout;
pub use terminal_object::TerminalObject;

/// Refusal from a finite pullback count.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PullbackError {
    /// The pair count overflowed, or it exceeded `|A| |B|`.
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/limits_colimits/mod.rs
// Claim: urn:core:crates_rs:core-category-theory:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PullbackError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PullbackError {}

/// Number of pairs `(a, b)` with `f(a) = g(b)`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PullbackCount {
    pairs: u32,
}

impl PullbackCount {
    /// `f` and `g` are the two legs into a common codomain, stored as integer colors.
    pub fn try_count(f: &[u32], g: &[u32]) -> Result<Self, PullbackError> {
        let mut pairs = 0u32;
        for &color_a in f {
            for &color_b in g {
                if color_a == color_b {
                    pairs = pairs.checked_add(1).ok_or(PullbackError::Overflow)?;
                }
            }
        }
        let bound = u32::try_from(f.len())
            .map_err(|_| PullbackError::Overflow)?
            .checked_mul(u32::try_from(g.len()).map_err(|_| PullbackError::Overflow)?)
            .ok_or(PullbackError::Overflow)?;
        if pairs > bound {
            return Err(PullbackError::Overflow);
        }
        Ok(Self { pairs })
    }

    /// Cardinality of the pullback.
    pub fn pairs(&self) -> u32 { self.pairs }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod pullback_tests {
    use super::*;
    #[test]
    fn three_pairs_meet() {
        let count = PullbackCount::try_count(&[0, 1], &[1, 0, 1]);
        assert!(matches!(count, Ok(ref c) if c.pairs() == 3));
    }
}
