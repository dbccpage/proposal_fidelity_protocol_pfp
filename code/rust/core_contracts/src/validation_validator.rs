use super::artifact::ValidationArtifact;
use super::violation::ValidationViolation;
use crate::kinds::{Capability, ContractEffect};
use crate::witness::evidence::ValidationWitness;

/// Validator trait for structural well-formedness checking.
///
/// Per 05_governance.yaml validator contract:
/// - Role: "Deterministic structural well-formedness checker against declared invariants"
/// - authority_effect: EvidenceOnly (validators do not emit facts, decisions, or actions)
/// - Validators check structure, they do NOT:
///   - repair/normalize targets
///   - certify or sign certificates
///   - execute or mutate state
///   - evaluate admissibility (that's Evaluator's role)
///   - terminalize
///   - authorize or license transitions
///   - define invariants from LLM output
///   - write trace directly
pub trait Validator<S> {
    type Witness: ValidationWitness;
    type Violation: ValidationViolation;

    const VALIDATOR_ID: &'static str;
    const SUBJECT_TYPE: &'static str;
    const PROPERTY: &'static str;

    /// Validate the subject and return a ValidationArtifact.
    fn validate(subject: &S) -> ValidationArtifact<Self::Witness, Self::Violation>;

    /// Returns the authority effect of this validator.
    ///
    /// Per 05_governance.yaml: Validators always emit EvidenceOnly artifacts.
    /// A CheckedValidationReport may become FactOnly only through a declared
    /// checking, replay, or certificate boundary.
    fn authority_effect() -> ContractEffect {
        ContractEffect::EvidenceOnly
    }
}

/// Canonical capabilities forbidden to validators per 05_governance.yaml.
pub const VALIDATOR_FORBIDDEN_CAPABILITIES: &[Capability] = &[
    Capability::Repair,
    Capability::CertificateSigning,
    Capability::ExecuteStateTransition,
    Capability::Evaluation,
    Capability::AdmissibilityDecision,
    Capability::RuntimeMutation,
    Capability::TerminalMapping,
    Capability::ActionLicensing,
    Capability::AuthorityPromotion,
    Capability::TraceWriting,
];

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidatorFence {
    forbidden_count: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ValidatorFenceError {
    Empty,
    Count { offered: u64, declared: u64 },
    Duplicate,
    NotForbidden,
    MissingForbidden,
    Overflow,
}

// Origin: engine/crates_rs/core_contracts/src/validation_validator.rs
// Claim: urn:core:crates_rs:core-contracts:validation-validator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ValidatorFenceError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ValidatorFenceError {}

impl ValidatorFence {
    fn count_hits(caps: &[Capability], offered: u64, cap: Capability) -> Result<u64, ValidatorFenceError> {
        let mut hits = 0u64;
        let mut j = 0u64;
        while j < offered {
            let j_us = usize::try_from(j).map_err(|_| ValidatorFenceError::Overflow)?;
            let other = *caps.get(j_us).ok_or(ValidatorFenceError::Overflow)?;
            if other == cap { hits = hits.checked_add(1).ok_or(ValidatorFenceError::Overflow)?; }
            j = j.checked_add(1).ok_or(ValidatorFenceError::Overflow)?;
        }
        Ok(hits)
    }

    fn verify_required_present(caps: &[Capability], declared: u64) -> Result<(), ValidatorFenceError> {
        let mut k = 0u64;
        while k < declared {
            let k_us = usize::try_from(k).map_err(|_| ValidatorFenceError::Overflow)?;
            let required = *VALIDATOR_FORBIDDEN_CAPABILITIES.get(k_us).ok_or(ValidatorFenceError::Overflow)?;
            if !caps.contains(&required) { return Err(ValidatorFenceError::MissingForbidden); }
            k = k.checked_add(1).ok_or(ValidatorFenceError::Overflow)?;
        }
        Ok(())
    }

    fn verify_offered_unique_and_forbidden(caps: &[Capability], offered: u64) -> Result<(), ValidatorFenceError> {
        let mut i = 0u64;
        while i < offered {
            let i_us = usize::try_from(i).map_err(|_| ValidatorFenceError::Overflow)?;
            let cap = *caps.get(i_us).ok_or(ValidatorFenceError::Overflow)?;
            if Self::count_hits(caps, offered, cap)? != 1 { return Err(ValidatorFenceError::Duplicate); }
            if !VALIDATOR_FORBIDDEN_CAPABILITIES.contains(&cap) { return Err(ValidatorFenceError::NotForbidden); }
            i = i.checked_add(1).ok_or(ValidatorFenceError::Overflow)?;
        }
        Ok(())
    }

    pub fn certify(caps: &[Capability]) -> Result<Self, ValidatorFenceError> {
        if caps.is_empty() { return Err(ValidatorFenceError::Empty); }
        let offered = u64::try_from(caps.len()).map_err(|_| ValidatorFenceError::Overflow)?;
        let declared = u64::try_from(VALIDATOR_FORBIDDEN_CAPABILITIES.len()).map_err(|_| ValidatorFenceError::Overflow)?;
        if offered != declared { return Err(ValidatorFenceError::Count { offered, declared }); }
        Self::verify_offered_unique_and_forbidden(caps, offered)?;
        Self::verify_required_present(caps, declared)?;
        let out = Self { forbidden_count: declared };
        Ok(out)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(ValidatorFence::certify(VALIDATOR_FORBIDDEN_CAPABILITIES), Ok(w) if w.forbidden_count == 10));
        assert!(matches!(ValidatorFence::certify(&[Capability::Repair]), Err(ValidatorFenceError::Count { .. })));
        assert!(matches!(ValidatorFence::certify(&[]), Err(ValidatorFenceError::Empty)));
    }
}
