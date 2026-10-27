pub mod cycle_aware;
pub mod engine_invariants;
pub mod engine_stream;
pub mod licensed_commit;
pub mod everett;
pub mod multipath_iterator;
pub mod obstruction_branch_search;
pub mod obstruction_metrics;
pub mod obstruction_runtime;
pub mod operator_algebra_engine;
// prompt_intake_engine: not a default engines module (archive/host; see Cargo.toml).
pub mod quantum;

// Exact invariant envelope.
// Origin: engine/crates_rs/engines/src/lib.rs
// Claim: urn:core:engines:candidate-accounting:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AccountedSearch {
    proposed: u64,
    accounted: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AccountError {
    Range,
    Overflow,
    Unaccounted { proposed: u64, accounted: u64 },
}

// Origin: engine/crates_rs/engines/src/lib.rs
// Claim: urn:core:crates_rs:engines:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for AccountError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for AccountError {}

impl AccountedSearch {
    pub fn proposed(&self) -> u64 { self.proposed }
    pub fn accounted(&self) -> u64 { self.accounted }

    // The audit type exists only where engine_invariants is compiled in.
    #[cfg(any(debug_assertions, feature = "strict_invariants"))]
    pub fn try_from_audit(audit: &engine_invariants::EvaluationAudit) -> Result<Self, AccountError> {
        let proposed = u64::try_from(audit.proposed).map_err(|_| AccountError::Range)?;
        let evaluated = u64::try_from(audit.evaluated).map_err(|_| AccountError::Range)?;
        let duplicate = u64::try_from(audit.duplicate_pruned).map_err(|_| AccountError::Range)?;
        let budget = u64::try_from(audit.budget_pruned).map_err(|_| AccountError::Range)?;
        let seen = u64::try_from(audit.already_seen_pruned).map_err(|_| AccountError::Range)?;
        let accounted = evaluated
            .checked_add(duplicate)
            .and_then(|n| n.checked_add(budget))
            .and_then(|n| n.checked_add(seen))
            .ok_or(AccountError::Overflow)?;
        if accounted != proposed {
            return Err(AccountError::Unaccounted { proposed, accounted });
        }
        Ok(Self { proposed, accounted })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod accounted_search_tests {
    use super::*;

    #[test]
    fn every_proposal_is_evaluated_or_pruned() {
        let audit = engine_invariants::EvaluationAudit {
            proposed: 5,
            evaluated: 2,
            duplicate_pruned: 1,
            budget_pruned: 1,
            already_seen_pruned: 1,
        };
        let accounted = AccountedSearch::try_from_audit(&audit);
        assert!(matches!(accounted, Ok(ref row) if row.proposed() == 5 && row.accounted() == 5));
    }

    #[test]
    fn a_missing_prune_is_unaccounted() {
        let audit = engine_invariants::EvaluationAudit {
            proposed: 5,
            evaluated: 2,
            duplicate_pruned: 1,
            budget_pruned: 0,
            already_seen_pruned: 1,
        };
        assert!(matches!(
            AccountedSearch::try_from_audit(&audit),
            Err(AccountError::Unaccounted { proposed: 5, accounted: 4 })
        ));
    }
}
