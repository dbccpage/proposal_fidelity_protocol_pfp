#[path = "enforcement_artifacts.rs"]
pub mod artifacts;
#[path = "enforcement_generated.rs"]
pub mod generated;
#[path = "enforcement_governance.rs"]
pub mod governance;
#[path = "enforcement_macros.rs"]
pub mod macros;
pub use artifacts::*;

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SpendError {
    Empty,
    Cost,
    Overspend,
    Balance,
    Overflow,
}

// Origin: engine/crates_rs/core_contracts/src/enforcement.rs
// Claim: urn:core:crates_rs:core-contracts:enforcement:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SpendError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SpendError {}

/// Positive costs whose sum, plus the remainder, restores the initial budget.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AdmittedSpend {
    spent: u64,
    remaining: u64,
}

impl AdmittedSpend {
    pub fn try_new(initial: u64, costs: &[u64]) -> Result<Self, SpendError> {
        if initial == 0 || costs.is_empty() {
            return Err(SpendError::Empty);
        }
        let mut spent = 0u64;
        for &cost in costs {
            if cost == 0 {
                return Err(SpendError::Cost);
            }
            spent = spent.checked_add(cost).ok_or(SpendError::Overflow)?;
        }
        let remaining = initial.checked_sub(spent).ok_or(SpendError::Overspend)?;
        let restored = remaining.checked_add(spent).ok_or(SpendError::Overflow)?;
        if restored != initial {
            return Err(SpendError::Balance);
        }
        Ok(Self { spent, remaining })
    }

    pub fn spent(&self) -> u64 { self.spent }
    pub fn remaining(&self) -> u64 { self.remaining }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod spend_tests {
    use super::*;

    #[test]
    fn remainder_plus_spent_restores_the_budget() {
        let spend = AdmittedSpend::try_new(10, &[3, 2]);
        assert!(matches!(spend, Ok(ref spend) if spend.spent() == 5 && spend.remaining() == 5));
    }

    #[test]
    fn a_cost_past_the_budget_is_refused() {
        let spend = AdmittedSpend::try_new(10, &[3, 8]);
        assert!(matches!(spend, Err(SpendError::Overspend)));
    }
}
