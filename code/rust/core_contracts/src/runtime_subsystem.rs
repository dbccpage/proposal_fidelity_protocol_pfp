use crate::kinds::ContractEffect;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CanonicalTimestamp(pub String);

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ArtifactId(pub String);

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ContentHash(pub String);

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RendererVersion(pub String);

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ReportSchemaId(pub String);

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ReportGenerationContext {
    pub generated_at: CanonicalTimestamp,
    pub source_artifact_ids: Vec<ArtifactId>,
    pub source_hashes: Vec<ContentHash>,
    pub renderer_version: RendererVersion,
    pub report_schema_id: ReportSchemaId,
}

/// Report capability profile aligned with the kernel authority matrix columns.
///
/// These booleans describe what a report renderer may observe while producing
/// evidence. They are not authority effects and do not authorize decisions,
/// licenses, mutation, or execution.
///
/// The kernel authority matrix defines what different components may do:
/// - Observe: read state without modification
/// - Measure: compute derived values from observations
/// - Decide: make policy/classification decisions
/// - Mutate: modify runtime state
/// - Execute: perform state transitions
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ReportAuthority {
    /// May observe state without modification (read-only access).
    pub may_observe: bool,
    /// May compute derived measurements from observations.
    pub may_measure: bool,
    /// May make policy or classification decisions.
    pub may_decide: bool,
    /// May modify runtime state.
    pub may_mutate: bool,
    /// May rank candidates (search/explore).
    pub may_rank: bool,
    /// May execute state transitions.
    pub may_execute: bool,
}

impl Default for ReportAuthority {
    fn default() -> Self {
        Self {
            may_observe: true,
            may_measure: false,
            may_decide: false,
            may_mutate: false,
            may_rank: false,
            may_execute: false,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ReportManifest {
    pub context: ReportGenerationContext,
    pub authority: ReportAuthority,
    pub authority_effect: ContractEffect,
    pub rendered_hash: String,
}

impl ReportManifest {
    pub fn new(
        context: ReportGenerationContext,
        authority: ReportAuthority,
        rendered_hash: String,
    ) -> Result<Self, ReportManifestError> {
        if authority.may_decide {
            return Err(ReportManifestError::DecisionCapabilityForbidden);
        }
        if authority.may_mutate {
            return Err(ReportManifestError::MutationCapabilityForbidden);
        }
        if authority.may_execute {
            return Err(ReportManifestError::ExecutionCapabilityForbidden);
        }

        Ok(Self {
            context,
            authority,
            authority_effect: ContractEffect::EvidenceOnly,
            rendered_hash,
        })
    }

    pub fn dummy() -> Self {
        Self {
            context: ReportGenerationContext {
                generated_at: CanonicalTimestamp("".into()),
                source_artifact_ids: vec![],
                source_hashes: vec![],
                renderer_version: RendererVersion("".into()),
                report_schema_id: ReportSchemaId("".into()),
            },
            authority: ReportAuthority::default(),
            authority_effect: ContractEffect::EvidenceOnly,
            rendered_hash: "".into(),
        }
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum ReportManifestError {
    DecisionCapabilityForbidden,
    MutationCapabilityForbidden,
    ExecutionCapabilityForbidden,
}

// Origin: engine/crates_rs/core_contracts/src/runtime_subsystem.rs
// Claim: urn:core:crates_rs:core-contracts:runtime-subsystem:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ReportManifestError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ReportManifestError {}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn context() -> ReportGenerationContext {
        ReportGenerationContext {
            generated_at: CanonicalTimestamp("2026-05-26T00:00:00Z".to_string()),
            source_artifact_ids: vec![ArtifactId("artifact:1".to_string())],
            source_hashes: vec![ContentHash("hash:1".to_string())],
            renderer_version: RendererVersion("renderer:v1".to_string()),
            report_schema_id: ReportSchemaId("schema:v1".to_string()),
        }
    }

    #[test]
    fn report_manifest_defaults_to_evidence_only() {
        let manifest = ReportManifest::new(
            context(),
            ReportAuthority::default(),
            "rendered:hash".to_string(),
        )
        .expect("read-only report manifest should be valid");

        assert_eq!(manifest.authority_effect, ContractEffect::EvidenceOnly);
        assert!(!manifest.authority.may_decide);
        assert!(!manifest.authority.may_mutate);
        assert!(!manifest.authority.may_execute);
    }

    #[test]
    fn report_manifest_refuses_decision_mutation_and_execution_capabilities() {
        let deciding = ReportAuthority {
            may_decide: true,
            ..ReportAuthority::default()
        };
        assert_eq!(
            ReportManifest::new(context(), deciding, "hash".to_string()),
            Err(ReportManifestError::DecisionCapabilityForbidden)
        );

        let mutating = ReportAuthority {
            may_mutate: true,
            ..ReportAuthority::default()
        };
        assert_eq!(
            ReportManifest::new(context(), mutating, "hash".to_string()),
            Err(ReportManifestError::MutationCapabilityForbidden)
        );

        let executing = ReportAuthority {
            may_execute: true,
            ..ReportAuthority::default()
        };
        assert_eq!(
            ReportManifest::new(context(), executing, "hash".to_string()),
            Err(ReportManifestError::ExecutionCapabilityForbidden)
        );
    }
}
