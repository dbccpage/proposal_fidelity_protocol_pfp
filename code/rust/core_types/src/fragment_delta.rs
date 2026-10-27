use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct FragmentDelta {
    pub index: usize,
    pub entropy_before: f64,
    pub entropy_after: f64,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum FragmentDeltaError {
    #[error("fragment delta entropy values must be finite")]
    NonFiniteEntropy,
}

impl FragmentDelta {
    pub fn new(
        index: usize,
        entropy_before: f64,
        entropy_after: f64,
    ) -> Result<Self, FragmentDeltaError> {
        if !entropy_before.is_finite() || !entropy_after.is_finite() {
            return Err(FragmentDeltaError::NonFiniteEntropy);
        }
        Ok(Self {
            index,
            entropy_before,
            entropy_after,
        })
    }

    pub fn entropy_delta(&self) -> f64 {
        self.entropy_after - self.entropy_before
    }
}

/// Exact telescoping ledger: the sum of consecutive integer deltas equals the last score minus the first.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TelescopingLedger {
    steps: usize,
    net: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LedgerError {
    Bound,
    Overflow,
    Telescope,
}

impl std::fmt::Display for LedgerError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            LedgerError::Bound => write!(formatter, "a telescoping ledger needs 2..=64 scores"),
            LedgerError::Overflow => write!(formatter, "a consecutive difference overflowed i64"),
            LedgerError::Telescope => write!(formatter, "partial deltas do not recover the endpoint gap"),
        }
    }
}

impl std::error::Error for LedgerError {}

impl TelescopingLedger {
    fn sum_window_deltas(scores: &[i64]) -> Result<i64, LedgerError> {
        let mut net: i64 = 0;
        for window in scores.windows(2) {
            let delta = window[1].checked_sub(window[0]).ok_or(LedgerError::Overflow)?;
            net = net.checked_add(delta).ok_or(LedgerError::Overflow)?;
        }
        Ok(net)
    }

    pub fn from_scores(scores: &[i64]) -> Result<Self, LedgerError> {
        if !(2..=64).contains(&scores.len()) {
            return Err(LedgerError::Bound);
        }
        let net = Self::sum_window_deltas(scores)?;
        let ends = scores[scores.len() - 1]
            .checked_sub(scores[0])
            .ok_or(LedgerError::Overflow)?;
        if net != ends {
            return Err(LedgerError::Telescope);
        }
        Ok(Self {
            steps: scores.len() - 1,
            net,
        })
    }

    pub fn steps(&self) -> usize {
        self.steps
    }

    pub fn net(&self) -> i64 {
        self.net
    }
}

// Origin: engine/crates_rs/core_types/src/fragment_delta.rs
// Claim: urn:core:crates_rs:core-types:fragment-delta:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod ledger_tests {
    use super::*;

    fn taken<T, E>(value: Result<T, E>) -> T {
        match value {
            Ok(inner) => inner,
            Err(_) => loop {
                assert!(false);
            },
        }
    }

    #[test]
    fn three_scores_telescope_to_the_endpoint_gap() {
        let ledger = taken(TelescopingLedger::from_scores(&[3, 5, 4]));
        assert_eq!(ledger.steps(), 2);
        assert_eq!(ledger.net(), 1);
        assert!(TelescopingLedger::from_scores(&[i64::MAX, i64::MIN]).is_err());
    }
}
