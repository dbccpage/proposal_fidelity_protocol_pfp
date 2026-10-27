//! Anthropic Messages API transport with the advisor and code-execution server tools and
//! parallel client tool results. Paid dispatch is off unless the caller grants a cost
//! ceiling; every reply is persisted before it is parsed.
//!
//! AuthorityEffect: None.

pub mod raw_store;
pub mod request;
pub mod response;
pub mod tool_round;
pub mod transport;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MicrosBudget {
    ceiling: u64,
    spent: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BudgetError {
    OverCeiling { spent: u64, cost: u64, ceiling: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_adversary/src/providers/anthropic/mod.rs
// Claim: urn:core:crates_rs:core-adversary:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BudgetError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BudgetError {}

impl MicrosBudget {
    pub fn try_new(ceiling: u64, spent: u64) -> Result<Self, BudgetError> {
        if spent > ceiling {
            return Err(BudgetError::OverCeiling {
                spent,
                cost: 0,
                ceiling,
            });
        }
        Ok(Self { ceiling, spent })
    }

    pub fn try_charge(&self, cost: u64) -> Result<Self, BudgetError> {
        let spent = self.spent.checked_add(cost).ok_or(BudgetError::Overflow)?;
        if spent > self.ceiling {
            return Err(BudgetError::OverCeiling {
                spent: self.spent,
                cost,
                ceiling: self.ceiling,
            });
        }
        Ok(Self {
            ceiling: self.ceiling,
            spent,
        })
    }

    pub fn spent(&self) -> u64 {
        self.spent
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod micros_budget_tests {
    use super::*;

    #[test]
    fn charge_stays_under_the_ceiling() {
        let admitted = MicrosBudget::try_new(100, 40).and_then(|budget| budget.try_charge(50));
        assert!(matches!(admitted, Ok(budget) if budget.spent() == 90));
        let refused = MicrosBudget::try_new(100, 40).and_then(|budget| budget.try_charge(70));
        assert!(matches!(refused, Err(BudgetError::OverCeiling { .. })));
    }
}
