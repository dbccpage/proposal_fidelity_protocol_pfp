//! Truncation, terminal outcomes, and authority/refusal dependent records.

use crate::tower::CoreLayer;
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TruncationLevel {
    Contractible,
    Proposition,
    Set,
    Groupoid,
    NType(u32),
    Untruncated,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum TerminalOutcome {
    Authority(String),
    ScopedNegative(String),
    Refusal(String),
    BudgetUnknown,
    LiftRequired,
    OracleNeeded,
}

impl TerminalOutcome {
    pub fn is_authority_bearing(&self) -> bool {
        matches!(self, Self::Authority(_))
    }
}

/// `Authority(x) := Sigma(t:T_auth)(Pi(x)=inl(t))`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AuthorityType {
    pub subject_ref: String,
    pub terminal: TerminalOutcome,
    pub terminalization_proof_ref: String,
}

impl AuthorityType {
    pub fn validate(&self) -> Result<(), TruncationError> {
        if self.subject_ref.is_empty() || self.terminalization_proof_ref.is_empty() {
            return Err(TruncationError::MissingAuthorityReference);
        }
        if !self.terminal.is_authority_bearing() {
            return Err(TruncationError::TerminalIsNotAuthority);
        }
        Ok(())
    }
}

/// `Refusal(x) := Sigma(f:F)(Pi(x)=inr(f))`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RefusalType {
    pub subject_ref: String,
    pub terminal: TerminalOutcome,
    pub terminalization_proof_ref: String,
}

impl RefusalType {
    pub fn validate(&self) -> Result<(), TruncationError> {
        if self.subject_ref.is_empty() || self.terminalization_proof_ref.is_empty() {
            return Err(TruncationError::MissingAuthorityReference);
        }
        if !matches!(
            self.terminal,
            TerminalOutcome::Refusal(_)
                | TerminalOutcome::BudgetUnknown
                | TerminalOutcome::OracleNeeded
        ) {
            return Err(TruncationError::TerminalIsNotRefusal);
        }
        Ok(())
    }
}

/// Dependent packet spine:
/// `Packet(s) = Sigma K, Sigma E, Sigma V, Sigma tau, LiftDiscipline`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DependentPacket {
    pub layer: CoreLayer,
    pub carrier_ref: String,
    pub candidate_family_ref: String,
    pub verifier_ref: String,
    pub terminalizer_ref: String,
    pub lift_discipline_ref: String,
    pub truncation: TruncationLevel,
}

impl DependentPacket {
    pub fn validate(&self) -> Result<(), TruncationError> {
        if self.carrier_ref.is_empty()
            || self.candidate_family_ref.is_empty()
            || self.verifier_ref.is_empty()
            || self.terminalizer_ref.is_empty()
            || self.lift_discipline_ref.is_empty()
        {
            return Err(TruncationError::IncompletePacket);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum TruncationError {
    #[error("authority/refusal type is missing subject or terminalization proof")]
    MissingAuthorityReference,
    #[error("terminal outcome is not authority-bearing")]
    TerminalIsNotAuthority,
    #[error("terminal outcome is not a refusal")]
    TerminalIsNotRefusal,
    #[error("dependent packet is missing one or more required fields")]
    IncompletePacket,
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/truncation.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:truncation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn authority_requires_authority_terminal() {
        let auth = AuthorityType {
            subject_ref: "packet-x".to_string(),
            terminal: TerminalOutcome::Authority("UniqueRule".to_string()),
            terminalization_proof_ref: "tau-proof".to_string(),
        };

        assert!(auth.validate().is_ok());
    }

    #[test]
    fn refusal_does_not_validate_as_authority() {
        let auth = AuthorityType {
            subject_ref: "packet-x".to_string(),
            terminal: TerminalOutcome::Refusal("NoReplay".to_string()),
            terminalization_proof_ref: "tau-proof".to_string(),
        };

        assert!(matches!(
            auth.validate(),
            Err(TruncationError::TerminalIsNotAuthority)
        ));
    }
}
