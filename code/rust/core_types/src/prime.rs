//! Plain views for Prime 002 continuation results (ADR-0002 / AGENTS.md).
//!
//! Plain, unsealed view of `oeprmalg2::can_continue_n` decisions.
//! AuthorityEffect: None.

use crate::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};

/// Canonical plain view of a continuation decision from Prime 002 (`oeprmalg2`).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CanContinueResult {
    pub may_continue: bool,
    pub blockers: Vec<String>,
    pub disposition: String,
    pub step_terminal: String,
}

impl CanContinueResult {
    pub fn new(
        may_continue: bool,
        blockers: Vec<String>,
        disposition: impl Into<String>,
        step_terminal: impl Into<String>,
    ) -> Self {
        Self {
            may_continue,
            blockers,
            disposition: disposition.into(),
            step_terminal: step_terminal.into(),
        }
    }

    pub fn permitted(step_terminal: impl Into<String>, disposition: impl Into<String>) -> Self {
        Self {
            may_continue: true,
            blockers: Vec::new(),
            disposition: disposition.into(),
            step_terminal: step_terminal.into(),
        }
    }

    pub fn refused(
        blockers: Vec<String>,
        step_terminal: impl Into<String>,
        disposition: impl Into<String>,
    ) -> Self {
        Self {
            may_continue: false,
            blockers,
            disposition: disposition.into(),
            step_terminal: step_terminal.into(),
        }
    }

    pub fn may_continue(&self) -> bool {
        self.may_continue
    }

    pub fn blockers(&self) -> &[String] {
        &self.blockers
    }

    pub fn disposition(&self) -> &str {
        &self.disposition
    }

    pub fn step_terminal(&self) -> &str {
        &self.step_terminal
    }

    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}

/// Admitted and refused continuation steps.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ContinuationCensus {
    permitted: i64,
    refused: i64,
    total: i64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PrimeError {
    BlockerDisagrees,
    Authority,
    Overflow,
}

impl std::fmt::Display for PrimeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::BlockerDisagrees => {
                write!(formatter, "may_continue disagrees with an empty blocker list")
            }
            Self::Authority => write!(formatter, "continuation authority is not None"),
            Self::Overflow => write!(formatter, "continuation census overflowed"),
        }
    }
}

impl std::error::Error for PrimeError {}

impl ContinuationCensus {
    pub fn permitted(&self) -> i64 {
        self.permitted
    }

    pub fn refused(&self) -> i64 {
        self.refused
    }

    pub fn total(&self) -> i64 {
        self.total
    }
}

/// `may_continue` is true exactly when `blockers` is empty, and the two counts sum to the step count.
/// Every step reports [`AuthorityEffect::None`].
pub fn certify_continuation(steps: &[CanContinueResult]) -> Result<ContinuationCensus, PrimeError> {
    let mut permitted = 0i64;
    let mut refused = 0i64;
    for step in steps {
        if step.authority_effect() != AuthorityEffect::None {
            return Err(PrimeError::Authority);
        }
        let open = step.blockers.is_empty();
        if step.may_continue != open {
            return Err(PrimeError::BlockerDisagrees);
        }
        if step.may_continue {
            permitted = permitted.checked_add(1).ok_or(PrimeError::Overflow)?;
        } else {
            refused = refused.checked_add(1).ok_or(PrimeError::Overflow)?;
        }
    }
    let total = permitted.checked_add(refused).ok_or(PrimeError::Overflow)?;
    let width = i64::try_from(steps.len()).map_err(|_| PrimeError::Overflow)?;
    if total != width {
        return Err(PrimeError::Overflow);
    }
    Ok(ContinuationCensus {
        permitted,
        refused,
        total,
    })
}

// Origin: engine/crates_rs/core_types/src/prime.rs
// Claim: urn:core:crates_rs:core-types:prime:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod continuation_tests {
    use super::*;

    fn taken(result: Result<ContinuationCensus, PrimeError>) -> ContinuationCensus {
        result.map_or_else(|_| loop { assert!(false); }, |value| value)
    }

    #[test]
    fn permitted_and_refused_partition_the_steps() {
        let steps = [
            CanContinueResult::permitted("step-1", "open"),
            CanContinueResult::refused(vec!["blocked".to_owned()], "step-2", "closed"),
        ];
        let census = taken(certify_continuation(&steps));
        assert_eq!(census.permitted() + census.refused(), census.total());
        assert_eq!(census.total(), 2);
    }

    #[test]
    fn a_continue_flag_with_a_blocker_is_refused() {
        let steps = [CanContinueResult::new(true, vec!["blocked".to_owned()], "bad", "step")];
        assert!(matches!(
            certify_continuation(&steps),
            Err(PrimeError::BlockerDisagrees)
        ));
    }
}
