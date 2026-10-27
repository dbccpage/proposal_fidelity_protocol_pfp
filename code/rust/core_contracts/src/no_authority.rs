use core_types::authority::AuthorityEffect;

pub trait AuthorityTagged {
    fn authority_effect(&self) -> AuthorityEffect;
    fn artifact_id(&self) -> &str;
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AuthorityViolation {
    pub artifact_id: String,
    pub artifact_name: String,
    pub effect: AuthorityEffect,
}

pub struct NoAuthorityGuard;

impl NoAuthorityGuard {
    pub fn validate<T: AuthorityTagged>(
        artifact: &T,
        artifact_name: impl Into<String>,
    ) -> Result<(), AuthorityViolation> {
        let effect = artifact.authority_effect();
        if effect.is_none() {
            Ok(())
        } else {
            Err(AuthorityViolation {
                artifact_id: artifact.artifact_id().to_string(),
                artifact_name: artifact_name.into(),
                effect,
            })
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{AuthorityTagged, NoAuthorityGuard};
    use core_types::authority::{
        AuthorityEffect, AuthorityTerminal, CertifiedAuthority, DescentWitness, IsAuth,
    };
    use core_types::GuardEvidence;

    struct DiagnosticArtifact {
        id: String,
        authority_effect: AuthorityEffect,
    }

    impl AuthorityTagged for DiagnosticArtifact {
        fn authority_effect(&self) -> AuthorityEffect {
            self.authority_effect.clone()
        }

        fn artifact_id(&self) -> &str {
            &self.id
        }
    }

    #[test]
    fn no_authority_guard_accepts_none() {
        let artifact = DiagnosticArtifact {
            id: "probe:1".into(),
            authority_effect: AuthorityEffect::None,
        };
        assert!(NoAuthorityGuard::validate(&artifact, "probe").is_ok());
    }

    #[test]
    fn no_authority_guard_rejects_claimed_authority() {
        // There is no bare `AuthorityEffect::Certified`; to tag an artifact as
        // certified you must present the dependent pair (terminal + descent
        // witness). The guard still rejects any non-`None` effect.
        let terminal = AuthorityTerminal::ExactRuleDerived;
        let witness =
            DescentWitness::from_verified_replay(terminal, "descent:proposal-1", "blake3:cafe")
                .unwrap();
        let is_auth = IsAuth::decide(
            terminal,
            GuardEvidence::new_valid(["cand_01"], "K_carrier_01", "blake3:deadbeef"),
        )
        .unwrap();
        let certified = CertifiedAuthority::certify(terminal, witness, is_auth).unwrap();
        let artifact = DiagnosticArtifact {
            id: "proposal:1".into(),
            authority_effect: AuthorityEffect::Certified(certified),
        };
        let violation = NoAuthorityGuard::validate(&artifact, "proposal").unwrap_err();
        assert_eq!(violation.artifact_id, "proposal:1");
        assert!(violation.effect.is_certified());
    }
}

// --- exact carrier witness ---
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BatchError {
    Empty,
    Identifier,
    Violation(AuthorityViolation),
}

// Origin: engine/crates_rs/core_contracts/src/no_authority.rs
// Claim: urn:core:crates_rs:core-contracts:no-authority:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BatchError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BatchError {}

/// A batch of artifacts that all carry AuthorityEffect::None and distinct ids.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NoneOnlyItem {
    artifact_id: String,
}

impl NoneOnlyItem {
    pub fn try_new(artifact_id: impl Into<String>) -> Result<Self, BatchError> {
        let artifact_id = artifact_id.into();
        if artifact_id.is_empty() {
            return Err(BatchError::Identifier);
        }
        Ok(Self { artifact_id })
    }
}

impl AuthorityTagged for NoneOnlyItem {
    fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }

    fn artifact_id(&self) -> &str {
        &self.artifact_id
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NoAuthorityBatch {
    admitted: usize,
}

impl NoAuthorityBatch {
    pub fn try_from_items(items: &[NoneOnlyItem]) -> Result<Self, BatchError> {
        if items.is_empty() {
            return Err(BatchError::Empty);
        }
        let mut seen = BTreeSet::new();
        for item in items {
            if !seen.insert(item.artifact_id.clone()) {
                return Err(BatchError::Identifier);
            }
            NoAuthorityGuard::validate(item, "batch").map_err(BatchError::Violation)?;
        }
        Ok(Self { admitted: items.len() })
    }

    pub fn admitted(&self) -> usize { self.admitted }
}

#[cfg(test)]
mod batch_tests {
    use super::*;

    #[test]
    fn two_none_artifacts_are_admitted() {
        let first = NoneOnlyItem::try_new("probe:1");
        let second = NoneOnlyItem::try_new("probe:2");
        let batch = first.and_then(|first| second.map(|second| NoAuthorityBatch::try_from_items(&[first, second])));
        assert!(matches!(batch, Ok(Ok(ref batch)) if batch.admitted() == 2));
    }

    #[test]
    fn a_repeated_artifact_id_is_refused() {
        let first = NoneOnlyItem::try_new("probe:1");
        let second = NoneOnlyItem::try_new("probe:1");
        let batch = first.and_then(|first| second.map(|second| NoAuthorityBatch::try_from_items(&[first, second])));
        assert!(matches!(batch, Ok(Err(BatchError::Identifier))));
    }
}
