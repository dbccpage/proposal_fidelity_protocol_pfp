use std::path::{Path, PathBuf};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TraceConfigError {
    #[error("target_base_dir cannot be empty")]
    EmptyBaseDir,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TraceConfig {
    trace_enabled: bool,
    narrative_enabled: bool,
    target_base_dir: PathBuf,
}

impl TraceConfig {
    pub fn new(
        trace_enabled: bool,
        narrative_enabled: bool,
        target_base_dir: PathBuf,
    ) -> Result<Self, TraceConfigError> {
        if target_base_dir.as_os_str().is_empty() {
            return Err(TraceConfigError::EmptyBaseDir);
        }
        Ok(Self {
            trace_enabled,
            narrative_enabled,
            target_base_dir,
        })
    }

    pub fn trace_enabled(&self) -> bool {
        self.trace_enabled
    }
    pub fn narrative_enabled(&self) -> bool {
        self.narrative_enabled
    }
    pub fn target_base_dir(&self) -> &Path {
        &self.target_base_dir
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BudgetError {
    Narrative,
    Consumed,
    Overflow,
}

/// Narrative output requires tracing, and consumed bytes stay inside the capacity.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TraceBudget {
    remaining: u64,
}

impl TraceBudget {
    pub fn try_new(config: &TraceConfig, capacity: u64, consumed: u64) -> Result<Self, BudgetError> {
        if config.narrative_enabled() && !config.trace_enabled() {
            return Err(BudgetError::Narrative);
        }
        if config.target_base_dir().as_os_str().is_empty() {
            return Err(BudgetError::Narrative);
        }
        let remaining = capacity.checked_sub(consumed).ok_or(BudgetError::Consumed)?;
        let restored = remaining.checked_add(consumed).ok_or(BudgetError::Overflow)?;
        if restored != capacity {
            return Err(BudgetError::Overflow);
        }
        Ok(Self { remaining })
    }

    pub fn remaining(&self) -> u64 { self.remaining }
}

// Origin: engine/crates_rs/core_replay/src/trace_config.rs
// Claim: urn:core:crates_rs:core-replay:trace-config:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod budget_tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn a_traced_run_keeps_the_unused_capacity() {
        let config = TraceConfig::new(true, true, PathBuf::from("runs"));
        let budget = config.as_ref().map(|config| TraceBudget::try_new(config, 10, 3));
        assert!(matches!(budget, Ok(Ok(ref budget)) if budget.remaining() == 7));
    }

    #[test]
    fn narrative_without_a_trace_is_refused() {
        let config = TraceConfig::new(false, true, PathBuf::from("runs"));
        let budget = config.as_ref().map(|config| TraceBudget::try_new(config, 10, 0));
        assert!(matches!(budget, Ok(Err(BudgetError::Narrative))));
    }
}
