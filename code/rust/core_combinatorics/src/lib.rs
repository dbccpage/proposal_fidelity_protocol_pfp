//! Exact finite combinatorics with budgets checked before enumeration.
//! Depends on nothing in the workspace.
//!
//! AuthorityEffect: None.

/// Mandatory authority effect declaration.
pub const AUTHORITY_EFFECT: &str = "AuthorityEffect: None";

pub mod cartesian_words;
pub mod enumeration;
pub mod finite_geometry;
pub mod mub_configurations;
pub mod weyl_systems;

pub mod color_constraints;

pub mod partitions;

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EnumerationBudget {
    limit: u64,
    consumed: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EnumerationBudgetError {
    ZeroLimit,
    Exhausted { consumed: u64, limit: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_combinatorics/src/lib.rs
// Claim: urn:core:crates_rs:core-combinatorics:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for EnumerationBudgetError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for EnumerationBudgetError {}

impl EnumerationBudget {
    pub fn certify(limit: u64) -> Result<Self, EnumerationBudgetError> {
        if limit == 0 { return Err(EnumerationBudgetError::ZeroLimit); }
        Ok(Self { limit, consumed: 0 })
    }
}

impl EnumerationBudget {
    pub fn consume(self, count: u64) -> Result<Self, EnumerationBudgetError> {
        let consumed = self.consumed.checked_add(count).ok_or(EnumerationBudgetError::Overflow)?;
        if consumed > self.limit { return Err(EnumerationBudgetError::Exhausted { consumed, limit: self.limit }); }
        Ok(Self { limit: self.limit, consumed })
    }

    pub fn remaining(&self) -> Result<u64, EnumerationBudgetError> {
        self.limit.checked_sub(self.consumed).ok_or(EnumerationBudgetError::Overflow)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        let step = EnumerationBudget::certify(4).and_then(|budget| budget.consume(3));
        assert!(matches!(step, Ok(ref budget) if budget.consumed == 3));
        let left = step.and_then(|budget| budget.remaining());
        assert!(matches!(left, Ok(1)));
        assert!(matches!(EnumerationBudget::certify(2).and_then(|budget| budget.consume(3)), Err(EnumerationBudgetError::Exhausted { .. })));
        assert!(matches!(EnumerationBudget::certify(0), Err(EnumerationBudgetError::ZeroLimit)));
    }
}
