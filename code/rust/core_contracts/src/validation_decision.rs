use serde::{Deserialize, Serialize};

/// Validation decision result.
///
/// Note: This enum represents the *decision* outcome of a validation run.
/// For the ValidationStatus used in ValidationReport artifacts (per 05_governance.yaml),
/// see [`ValidationStatus`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ValidationDecision {
    Valid,
    Invalid,
    DomainError,
}

/// Validation status for validation reports.
///
/// Per 05_governance.yaml validator contract:
/// - Valid: Target satisfies all declared invariants
/// - Invalid: Target violates one or more declared invariants
/// - Indeterminate: Validation could not determine status (e.g., timeout, missing data)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ValidationStatus {
    Valid,
    Invalid,
    DomainError,
    Indeterminate,
}

impl From<ValidationDecision> for ValidationStatus {
    fn from(decision: ValidationDecision) -> Self {
        match decision {
            ValidationDecision::Valid => Self::Valid,
            ValidationDecision::Invalid => Self::Invalid,
            ValidationDecision::DomainError => Self::DomainError,
        }
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_contracts/src/validation/decision.rs
// Claim: urn:core:contracts:validation:obligation-tally:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObligationTally {
    checked: u64,
    failed: u64,
    domain_fault: bool,
    status: ValidationStatus,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ObligationTallyError {
    FailedExceedsChecked { failed: u64, checked: u64 },
}

// Origin: engine/crates_rs/core_contracts/src/validation_decision.rs
// Claim: urn:core:crates_rs:core-contracts:validation-decision:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ObligationTallyError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ObligationTallyError {}

impl ObligationTally {
    pub fn try_new(checked: u64, failed: u64, domain_fault: bool) -> Result<Self, ObligationTallyError> {
        if failed > checked {
            return Err(ObligationTallyError::FailedExceedsChecked { failed, checked });
        }
        let status = if domain_fault {
            ValidationStatus::DomainError
        } else if failed > 0 {
            ValidationStatus::Invalid
        } else if checked > 0 {
            ValidationStatus::Valid
        } else {
            ValidationStatus::Indeterminate
        };
        Ok(Self {
            checked,
            failed,
            domain_fault,
            status,
        })
    }

    pub fn status(&self) -> ValidationStatus {
        self.status
    }

    pub fn checked(&self) -> u64 {
        self.checked
    }

    pub fn failed(&self) -> u64 {
        self.failed
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod obligation_tally_tests {
    use super::*;

    #[test]
    fn classifies_the_four_statuses() {
        let valid = ObligationTally::try_new(4, 0, false);
        let invalid = ObligationTally::try_new(4, 1, false);
        let indeterminate = ObligationTally::try_new(0, 0, false);
        let fault = ObligationTally::try_new(2, 2, true);
        assert!(matches!(valid, Ok(ref row) if row.status() == ValidationStatus::Valid && row.checked() == 4));
        assert!(matches!(invalid, Ok(ref row) if row.status() == ValidationStatus::Invalid && row.failed() == 1));
        assert!(matches!(indeterminate, Ok(ref row) if row.status() == ValidationStatus::Indeterminate));
        assert!(matches!(fault, Ok(ref row) if row.status() == ValidationStatus::DomainError));
    }

    #[test]
    fn refuses_more_failures_than_checks() {
        let wrong = ObligationTally::try_new(2, 3, false);
        assert!(matches!(
            wrong,
            Err(ObligationTallyError::FailedExceedsChecked { failed: 3, checked: 2 })
        ));
    }
}
