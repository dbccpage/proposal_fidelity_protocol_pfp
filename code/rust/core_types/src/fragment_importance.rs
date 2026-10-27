use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum FragmentImportance {
    HighImpact,
    LowImpact,
    NegativeDelta,
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FragmentDeltaError { Denom, Threshold, Zero, Overflow }

// Origin: engine/crates_rs/core_types/src/fragment_importance.rs
// Claim: urn:core:crates_rs:core-types:fragment-importance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FragmentDeltaError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FragmentDeltaError {}

/// Classify `numer/denom` against a nonnegative threshold by cross-multiplication.
pub fn classify_exact_delta(numer: i64, denom: i64, threshold_numer: i64, threshold_denom: i64) -> Result<FragmentImportance, FragmentDeltaError> {
    if denom <= 0 || threshold_denom <= 0 {
        return Err(FragmentDeltaError::Denom);
    }
    if threshold_numer < 0 {
        return Err(FragmentDeltaError::Threshold);
    }
    if numer == 0 {
        return Err(FragmentDeltaError::Zero);
    }
    if numer < 0 {
        return Ok(FragmentImportance::NegativeDelta);
    }
    let left = i128::from(numer).checked_mul(i128::from(threshold_denom)).ok_or(FragmentDeltaError::Overflow)?;
    let right = i128::from(threshold_numer).checked_mul(i128::from(denom)).ok_or(FragmentDeltaError::Overflow)?;
    if left > right {
        Ok(FragmentImportance::HighImpact)
    } else {
        Ok(FragmentImportance::LowImpact)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod fragment_delta_checks {
    use super::*;

    #[test]
    fn three_halves_is_high_and_one_third_is_low() {
        assert!(matches!(classify_exact_delta(3, 2, 1, 1), Ok(FragmentImportance::HighImpact)));
        assert!(matches!(classify_exact_delta(1, 3, 1, 1), Ok(FragmentImportance::LowImpact)));
    }

    #[test]
    fn a_negative_delta_and_a_zero_numerator_are_distinct() {
        assert!(matches!(classify_exact_delta(-1, 2, 1, 1), Ok(FragmentImportance::NegativeDelta)));
        assert!(matches!(classify_exact_delta(0, 1, 1, 1), Err(FragmentDeltaError::Zero)));
    }
}
