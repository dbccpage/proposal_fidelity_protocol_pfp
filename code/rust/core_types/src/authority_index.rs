//! Authority index records.
//!
//! This module records the coordinates that an authority claim would have to
//! bind to: terminal, evidence ceiling, verifier scope, replay hash, and role
//! boundary. It is deliberately non-authority data. It has no constructor for
//! [`crate::authority::CertifiedAuthority`] and no terminalization method.

use crate::authority::{AuthorityTerminal, DescentWitness};
use crate::ceiling::EvidenceCeiling;
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum AuthorityIndexError {
    #[error("missing verifier scope")]
    MissingVerifierScope,
    #[error("missing replay hash")]
    MissingReplayHash,
    #[error("missing role boundary")]
    MissingRoleBoundary,
    #[error("descent witness terminal does not match authority index terminal")]
    WitnessTerminalMismatch,
    #[error("descent witness replay hash does not match authority index replay hash")]
    WitnessReplayHashMismatch,
}

/// Non-authority coordinates for a terminal descent claim.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(try_from = "RawAuthorityIndexRecord")]
pub struct AuthorityIndexRecord {
    terminal: AuthorityTerminal,
    evidence_ceiling: EvidenceCeiling,
    verifier_scope: String,
    replay_hash: String,
    role_boundary: String,
}

#[derive(Deserialize)]
struct RawAuthorityIndexRecord {
    terminal: AuthorityTerminal,
    evidence_ceiling: EvidenceCeiling,
    verifier_scope: String,
    replay_hash: String,
    role_boundary: String,
}

impl TryFrom<RawAuthorityIndexRecord> for AuthorityIndexRecord {
    type Error = AuthorityIndexError;

    fn try_from(raw: RawAuthorityIndexRecord) -> Result<Self, Self::Error> {
        AuthorityIndexRecord::new(
            raw.terminal,
            raw.evidence_ceiling,
            raw.verifier_scope,
            raw.replay_hash,
            raw.role_boundary,
        )
    }
}

impl AuthorityIndexRecord {
    pub fn new(
        terminal: AuthorityTerminal,
        evidence_ceiling: EvidenceCeiling,
        verifier_scope: impl Into<String>,
        replay_hash: impl Into<String>,
        role_boundary: impl Into<String>,
    ) -> Result<Self, AuthorityIndexError> {
        let verifier_scope = verifier_scope.into();
        if verifier_scope.trim().is_empty() {
            return Err(AuthorityIndexError::MissingVerifierScope);
        }
        let replay_hash = replay_hash.into();
        if replay_hash.trim().is_empty() {
            return Err(AuthorityIndexError::MissingReplayHash);
        }
        let role_boundary = role_boundary.into();
        if role_boundary.trim().is_empty() {
            return Err(AuthorityIndexError::MissingRoleBoundary);
        }
        Ok(Self {
            terminal,
            evidence_ceiling,
            verifier_scope,
            replay_hash,
            role_boundary,
        })
    }

    pub fn terminal(&self) -> AuthorityTerminal {
        self.terminal
    }

    pub fn evidence_ceiling(&self) -> EvidenceCeiling {
        self.evidence_ceiling
    }

    pub fn verifier_scope(&self) -> &str {
        &self.verifier_scope
    }

    pub fn replay_hash(&self) -> &str {
        &self.replay_hash
    }

    pub fn role_boundary(&self) -> &str {
        &self.role_boundary
    }

    /// Shape-check that a witness is bound to this index. This does not certify
    /// authority; it only prevents cross-terminal or cross-replay reuse at the
    /// index layer.
    pub fn check_witness_binding(
        &self,
        witness: &DescentWitness,
    ) -> Result<(), AuthorityIndexError> {
        if witness.terminal() != self.terminal {
            return Err(AuthorityIndexError::WitnessTerminalMismatch);
        }
        if witness.replay_hash() != self.replay_hash {
            return Err(AuthorityIndexError::WitnessReplayHashMismatch);
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_types/src/authority_index.rs
// Claim: urn:core:crates_rs:core-types:authority-index:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::authority::{AuthorityTerminal, DescentWitness};

    #[test]
    fn complete_authority_index_record_constructs() {
        let record = AuthorityIndexRecord::new(
            AuthorityTerminal::ExactRuleDerived,
            EvidenceCeiling::BoundaryChecked,
            "t3-primal-dual-v1",
            "replay:abc",
            "role:terminalizer",
        )
        .expect("complete index");

        assert_eq!(record.terminal(), AuthorityTerminal::ExactRuleDerived);
        assert_eq!(record.evidence_ceiling(), EvidenceCeiling::BoundaryChecked);
        assert_eq!(record.verifier_scope(), "t3-primal-dual-v1");
        assert_eq!(record.replay_hash(), "replay:abc");
        assert_eq!(record.role_boundary(), "role:terminalizer");
    }

    #[test]
    fn missing_verifier_scope_is_refused() {
        assert_eq!(
            AuthorityIndexRecord::new(
                AuthorityTerminal::ExactRuleDerived,
                EvidenceCeiling::BoundaryChecked,
                " ",
                "replay:abc",
                "role:terminalizer",
            )
            .unwrap_err(),
            AuthorityIndexError::MissingVerifierScope
        );
    }

    #[test]
    fn witness_binding_rejects_cross_replay_reuse() {
        let record = AuthorityIndexRecord::new(
            AuthorityTerminal::ExactRuleDerived,
            EvidenceCeiling::BoundaryChecked,
            "t3-primal-dual-v1",
            "replay:abc",
            "role:terminalizer",
        )
        .expect("complete index");
        let witness = DescentWitness::from_verified_replay(
            AuthorityTerminal::ExactRuleDerived,
            "descent:1",
            "replay:other",
        )
        .expect("witness shape");

        assert_eq!(
            record.check_witness_binding(&witness).unwrap_err(),
            AuthorityIndexError::WitnessReplayHashMismatch
        );
    }

    #[test]
    fn deserialization_rejects_invalid_records() {
        let bad_scope = r#"{"terminal":"ExactRuleDerived","evidence_ceiling":"BoundaryChecked","verifier_scope":"   ","replay_hash":"replay:abc","role_boundary":"role:terminalizer"}"#;
        let res: Result<AuthorityIndexRecord, _> = serde_json::from_str(bad_scope);
        assert!(res.is_err());

        let bad_hash = r#"{"terminal":"ExactRuleDerived","evidence_ceiling":"BoundaryChecked","verifier_scope":"t3-primal-dual-v1","replay_hash":"   ","role_boundary":"role:terminalizer"}"#;
        let res: Result<AuthorityIndexRecord, _> = serde_json::from_str(bad_hash);
        assert!(res.is_err());

        let bad_role = r#"{"terminal":"ExactRuleDerived","evidence_ceiling":"BoundaryChecked","verifier_scope":"t3-primal-dual-v1","replay_hash":"replay:abc","role_boundary":"   "}"#;
        let res: Result<AuthorityIndexRecord, _> = serde_json::from_str(bad_role);
        assert!(res.is_err());
    }
}
