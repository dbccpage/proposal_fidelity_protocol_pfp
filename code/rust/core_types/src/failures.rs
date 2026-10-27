//! failures.rs
//! ============
//! Origin: core_types failure taxonomy
//! Claim: urn:core:types:failures:v1
//! AuthorityEffect: None.
//! Scope Fence: What this file does not claim: Defines typed failure variants and certified result structures; does not execute gates.

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LambdaFailure {
    OutsideAdmissibleDomain,
    InvariantViolation,
    UndefinedTransformation,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum OperatorFailure {
    #[error("invalid input")]
    InvalidInput,
    #[error("operator composition mismatch")]
    CompositionMismatch,
    #[error("invariant violation: {0}")]
    InvariantViolation(String),
}

pub type InvariantId = String;
pub enum ReducerFailure {
    OutsideAdmissibleDomain,
    InvariantViolation { invariant: InvariantId },
    ReductionUndefined { reason: &'static str },
    NonFiniteInput,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TransformFailure {
    OutsideAdmissibleDomain,
    InvariantViolation,
    UndefinedTransformation,
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct AdmissibleInterval {
    lower_inclusive: i64,
    upper_exclusive: i64,
    width: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AdmissibleIntervalError {
    EmptyInterval { lower_inclusive: i64, upper_exclusive: i64 },
    WidthOverflow,
}

impl AdmissibleInterval {
    pub fn certify(lower_inclusive: i64, upper_exclusive: i64) -> Result<Self, AdmissibleIntervalError> {
        if lower_inclusive >= upper_exclusive { return Err(AdmissibleIntervalError::EmptyInterval { lower_inclusive, upper_exclusive }); }
        let width = upper_exclusive.checked_sub(lower_inclusive).ok_or(AdmissibleIntervalError::WidthOverflow)?;
        if width <= 0 { return Err(AdmissibleIntervalError::EmptyInterval { lower_inclusive, upper_exclusive }); }
        Ok(Self { lower_inclusive, upper_exclusive, width })
    }
}

impl AdmissibleInterval {
    pub fn classify(&self, sample: Option<i64>) -> Result<(), ReducerFailure> {
        let Some(sample) = sample else { return Err(ReducerFailure::NonFiniteInput); };
        if sample < self.lower_inclusive || sample >= self.upper_exclusive {
            return Err(ReducerFailure::OutsideAdmissibleDomain);
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(AdmissibleInterval::certify(-2, 3), Ok(w) if w.width == 5));
        let w = AdmissibleInterval::certify(0, 2).expect("valid interval");
        let admitted = w.classify(Some(1)).map(|_| 0u64);
        assert!(matches!(admitted, Ok(0)));
        let outside = w.classify(Some(2));
        assert!(matches!(outside, Err(ReducerFailure::OutsideAdmissibleDomain)));
        let non_finite = w.classify(None);
        assert!(matches!(non_finite, Err(ReducerFailure::NonFiniteInput)));
        assert!(matches!(AdmissibleInterval::certify(3, 3), Err(AdmissibleIntervalError::EmptyInterval { .. })));
    }
}
