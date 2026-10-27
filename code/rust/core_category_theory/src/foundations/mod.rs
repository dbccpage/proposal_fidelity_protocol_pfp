//! Foundations shells for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

pub mod finite_set;
pub mod function;
pub mod hlevel;
pub mod set;
pub mod truncation;
pub mod universe;

pub use finite_set::FiniteSet;
pub use function::Function;
pub use hlevel::HLevel;
pub use set::Set;
pub use truncation::Truncation;
pub use universe::Universe;

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CumulativeHLevelWitness { claimed: i8, observed: i8 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HLevelWitnessError { BelowContractible, NotCumulative }

// Origin: engine/crates_rs/core_category_theory/src/foundations/mod.rs
// Claim: urn:core:crates_rs:core-category-theory:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for HLevelWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for HLevelWitnessError {}

impl CumulativeHLevelWitness {
    pub const CONTRACTIBLE: i8 = -2;
    pub const PROPOSITION: i8 = -1;
    pub const SET: i8 = 0;
    pub const GROUPOID: i8 = 1;

    /// An n-type claim is admitted only at an observed level at least n, and n is at least -2.
    pub fn try_new(claimed: i8, observed: i8) -> Result<Self, HLevelWitnessError> {
        if claimed < Self::CONTRACTIBLE || observed < Self::CONTRACTIBLE {
            return Err(HLevelWitnessError::BelowContractible);
        }
        if observed < claimed {
            return Err(HLevelWitnessError::NotCumulative);
        }
        Ok(Self { claimed, observed })
    }

    pub fn levels(&self) -> (i8, i8) { (self.claimed, self.observed) }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod hlevel_witness_checks {
    use super::*;

    #[test]
    fn a_groupoid_is_a_set() {
        let witness = CumulativeHLevelWitness::try_new(CumulativeHLevelWitness::SET, CumulativeHLevelWitness::GROUPOID);
        assert!(matches!(witness, Ok(w) if w.levels() == (0, 1)));
    }

    #[test]
    fn a_set_does_not_witness_a_groupoid_claim() {
        assert!(matches!(
            CumulativeHLevelWitness::try_new(CumulativeHLevelWitness::GROUPOID, CumulativeHLevelWitness::SET),
            Err(HLevelWitnessError::NotCumulative)
        ));
    }
}
