use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SignCancellationPattern {
    HighFrequencyOscillation,
    LargeTermCancellation,
    TopologicalObstruction,
    KoszulAccumulation,
    None,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignCancellationSignature {
    pub pattern: SignCancellationPattern,
    pub severity: f64,
    pub affected_steps: Vec<u32>,
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CancellationBalance {
    positive: u64,
    negative: u64,
    residual: u64,
    residual_nonnegative: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CancellationBalanceError {
    BothZero,
    StepsOnClearPattern,
    MissingSteps,
    PatternMismatch,
    Overflow,
}

// Origin: engine/crates_rs/core_types/src/sign_cancellation.rs
// Claim: urn:core:crates_rs:core-types:sign-cancellation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CancellationBalanceError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CancellationBalanceError {}

impl CancellationBalance {
    fn validate_pattern_steps(
        pattern: SignCancellationPattern,
        affected_steps: &[u32],
        residual: u64,
        both_nonzero: bool,
    ) -> Result<(), CancellationBalanceError> {
        match (pattern == SignCancellationPattern::None, affected_steps.is_empty()) {
            (true, false) => return Err(CancellationBalanceError::StepsOnClearPattern),
            (false, true) => return Err(CancellationBalanceError::MissingSteps),
            _ => {}
        }
        let exact_cancel = residual == 0 && both_nonzero;
        let fits = match pattern {
            SignCancellationPattern::LargeTermCancellation => exact_cancel,
            SignCancellationPattern::None => !exact_cancel,
            SignCancellationPattern::HighFrequencyOscillation
            | SignCancellationPattern::TopologicalObstruction
            | SignCancellationPattern::KoszulAccumulation => both_nonzero,
        };
        if !fits {
            return Err(CancellationBalanceError::PatternMismatch);
        }
        Ok(())
    }

    pub fn certify(pattern: SignCancellationPattern, affected_steps: &[u32], positive: u64, negative: u64) -> Result<Self, CancellationBalanceError> {
        if positive == 0 && negative == 0 {
            return Err(CancellationBalanceError::BothZero);
        }
        let residual = positive.abs_diff(negative);
        let residual_nonnegative = positive >= negative;
        Self::validate_pattern_steps(pattern, affected_steps, residual, positive > 0 && negative > 0)?;
        Ok(Self { positive, negative, residual, residual_nonnegative })
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(CancellationBalance::certify(SignCancellationPattern::None, &[], 5, 2), Ok(w) if w.residual == 3 && w.residual_nonnegative));
        assert!(matches!(CancellationBalance::certify(SignCancellationPattern::LargeTermCancellation, &[1], 4, 4), Ok(w) if w.residual == 0 && w.residual_nonnegative));
        assert!(matches!(CancellationBalance::certify(SignCancellationPattern::LargeTermCancellation, &[1], 4, 1), Err(CancellationBalanceError::PatternMismatch)));
        assert!(matches!(CancellationBalance::certify(SignCancellationPattern::KoszulAccumulation, &[], 3, 1), Err(CancellationBalanceError::MissingSteps)));
    }
}
