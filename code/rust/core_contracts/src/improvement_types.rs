//! Canonical improvement / maintenance contract types (V1).
//!
//! All fields that carry hashes are lowercase hex SHA-256 (64 chars).
//! No floating-point fields are permitted on any type in this module.

use core_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};

// ── Schema tags ─────────────────────────────────────────────────────────────

pub const MAINTENANCE_POLICY_SCHEMA_V1: &str = "core.improvement.maintenance_policy.v1";
pub const IMPROVEMENT_RUN_SCHEMA_V1: &str = "core.improvement.run.v1";
pub const SOURCE_ARTIFACT_SCHEMA_V1: &str = "core.improvement.source_artifact.v1";
pub const SOURCE_SPAN_SCHEMA_V1: &str = "core.improvement.source_span.v1";
pub const IMPROVEMENT_FINDING_SCHEMA_V1: &str = "core.improvement.finding.v1";
pub const RUN_LEARNING_RECEIPT_SCHEMA_V1: &str = "core.improvement.run_learning_receipt.v1";
pub const OPERATOR_IMPROVEMENT_CANDIDATE_SCHEMA_V1: &str =
    "core.improvement.operator_candidate.v1";
pub const IMPROVEMENT_EVALUATION_SCHEMA_V1: &str = "core.improvement.evaluation.v1";
pub const PROPOSAL_BUNDLE_SCHEMA_V1: &str = "core.improvement.proposal_bundle.v1";
pub const ADVERSARY_HANDOFF_SCHEMA_V1: &str = "core.improvement.adversary_handoff.v1";
pub const MAINTENANCE_TERMINAL_SCHEMA_V1: &str = "core.improvement.maintenance_terminal.v1";

// ── Enums ───────────────────────────────────────────────────────────────────

/// Host-visible maintenance terminal for one watched invocation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MaintenanceTerminalV1 {
    NoSignal,
    NoCandidate,
    BlockedAtAdversary,
    RefusedEvidence,
    RefusedProtectedSurface,
    InfrastructureFailure,
}

impl MaintenanceTerminalV1 {
    pub const SCHEMA: &'static str = MAINTENANCE_TERMINAL_SCHEMA_V1;

    /// V1 never renders PromotionReady; candidate-bearing runs stop at adversary.
    pub fn may_render_promotion_ready(self) -> bool {
        false
    }
}

/// Finding severity. Used for deterministic candidate selection ordering.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum FindingSeverityV1 {
    Info = 0,
    Low = 1,
    Medium = 2,
    High = 3,
    /// Immediate refuse — never candidate-eligible in the same run.
    HardSafety = 4,
}

/// Proposed routing target based on reference-skill roles.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProposedRouteV1 {
    /// Correction patterns → autoskill adapter.
    Autoskill,
    /// Learner defects → improve-autoskill.
    ImproveAutoskill,
    /// Cross-surface drift → symmetry-hunter.
    SymmetryHunter,
    /// Inventory / quality → review-skills / review-agents.
    ReviewSkills,
    ReviewAgents,
    /// No model route; host-only disposition.
    HostOnly,
    /// Hard safety refuse route.
    Refuse,
}

/// Source role claimed by signed policy for a watched surface.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SourceRoleV1 {
    /// Immutable reference evidence under `.claude/skills/**`.
    ImmutableReference,
    /// Optional read-only adapter under `.agents/**`.
    OptionalReadOnlyAdapter,
    /// Ordinary repository surface (subject to ordinary write rules).
    Ordinary,
    /// Protected surface — never an admitted self-edit target.
    Protected,
}

// ── Policy ──────────────────────────────────────────────────────────────────

/// Signed maintenance configuration frozen into each run.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MaintenancePolicyV1 {
    pub schema: String,
    /// Content-addressed policy identity (hash of signed body excluding this field).
    pub policy_id: String,
    /// Signed source roles keyed by normalized relative path prefix.
    pub source_roles: Vec<SourceRoleBindingV1>,
    /// Path prefixes that may never become admitted write surfaces.
    pub protected_surfaces: Vec<String>,
    pub limits: MaintenanceLimitsV1,
    /// Detector version pins (name → version string).
    pub detector_versions: Vec<DetectorVersionPinV1>,
    /// Frozen evaluator epoch identity.
    pub evaluator_epoch: String,
    /// Optional `.agents` adapter configuration. Absence is valid.
    pub agents_adapter: Option<AgentsAdapterConfigV1>,
    /// Live model production disabled by default until an operator signs a provider.
    pub live_model_provider_id: Option<String>,
    /// Self-lane weight. V1 holds this at zero.
    pub self_lane_weight: u32,
    /// Encoding tag — must be `core.canonical_json.v1`.
    pub encoding: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceRoleBindingV1 {
    pub path_prefix: String,
    pub role: SourceRoleV1,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DetectorVersionPinV1 {
    pub detector_id: String,
    pub version: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MaintenanceLimitsV1 {
    pub max_candidates_per_run: u32,
    pub max_edited_files: u32,
    /// Maximum total candidate replacement bytes per run.
    pub max_candidate_bytes: u64,
    /// Maximum total captured source bytes per run.
    pub max_captured_source_bytes: u64,
}

impl Default for MaintenanceLimitsV1 {
    fn default() -> Self {
        Self {
            max_candidates_per_run: 1,
            max_edited_files: 4,
            max_candidate_bytes: 200 * 1024,
            max_captured_source_bytes: 2 * 1024 * 1024,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AgentsAdapterConfigV1 {
    /// Relative root of the optional adapter (typically `.agents`).
    pub root: String,
    /// Configured lifecycle/registry projection relative paths (read-only).
    pub projection_paths: Vec<String>,
}

impl MaintenancePolicyV1 {
    /// Default control-plane first-slice policy (unsigned body; host must sign).
    pub fn control_plane_defaults_v1() -> Self {
        Self {
            schema: MAINTENANCE_POLICY_SCHEMA_V1.to_owned(),
            policy_id: String::new(), // filled after hashing body
            source_roles: vec![
                SourceRoleBindingV1 {
                    path_prefix: ".claude/skills".to_owned(),
                    role: SourceRoleV1::ImmutableReference,
                },
                SourceRoleBindingV1 {
                    path_prefix: ".agents".to_owned(),
                    role: SourceRoleV1::OptionalReadOnlyAdapter,
                },
            ],
            protected_surfaces: default_protected_surfaces_v1(),
            limits: MaintenanceLimitsV1::default(),
            detector_versions: default_detector_versions_v1(),
            evaluator_epoch: "evaluator-epoch-held-v1".to_owned(),
            agents_adapter: Some(AgentsAdapterConfigV1 {
                root: ".agents".to_owned(),
                projection_paths: vec![
                    ".agents/skills/_shared/family_registry.md".to_owned(),
                    ".agents/skills/_shared/constraints.md".to_owned(),
                ],
            }),
            live_model_provider_id: None,
            self_lane_weight: 0,
            encoding: super::canonical_json::CORE_CANONICAL_JSON_V1.to_owned(),
        }
    }
}

/// First-slice watched skill family (rubrics/roles only; never executed).
pub const META_MAINTENANCE_SKILL_FAMILY_V1: &[&str] = &[
    "autoskill",
    "improve-autoskill",
    "symmetry-hunter",
    "review-skills",
    "review-agents",
];

pub fn default_protected_surfaces_v1() -> Vec<String> {
    vec![
        ".claude".to_owned(),
        ".agents".to_owned(),
        ".intelligence".to_owned(),
        "maintenance/.intelligence".to_owned(),
        "crates/core_corrigibility".to_owned(),
        "crates/core_safety_controller".to_owned(),
        "crates/core_governance/src/enforcement.rs".to_owned(),
        "crates/core_governance/src/improvement_quarantine.rs".to_owned(),
        "crates/core_maintenance".to_owned(),
        "crates/core_self_review".to_owned(),
        "halt".to_owned(),
        "off_switch".to_owned(),
        "policy_manifest".to_owned(),
        "authority_constructors".to_owned(),
        "evaluators".to_owned(),
        "active_operator".to_owned(),
    ]
}

pub fn default_detector_versions_v1() -> Vec<DetectorVersionPinV1> {
    const DETECTORS: &[&str] = &[
        "malformed_metadata",
        "broken_references",
        "duplicate_identities",
        "provider_projection_drift",
        "authority_collisions",
        "direct_mutation_instructions",
        "self_certification_instructions",
        "protected_surface_proposals",
        "agents_lifecycle_contradictions",
    ];
    DETECTORS
        .iter()
        .map(|id| DetectorVersionPinV1 {
            detector_id: (*id).to_owned(),
            version: format!("{id}@v1"),
        })
        .collect()
}

// ── Run identity ────────────────────────────────────────────────────────────

/// Frozen identity of one maintenance invocation attempt.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ImprovementRunV1 {
    pub schema: String,
    pub invocation_id: String,
    pub attempt_id: String,
    pub base_commit: String,
    pub task_journal_sha256: String,
    pub policy_id: String,
    pub policy_sha256: String,
    pub binary_id: String,
    pub binary_sha256: String,
    pub input_manifest_sha256: String,
    pub encoding: String,
}

// ── Source artifacts & spans ────────────────────────────────────────────────

/// Hash-bound source file captured at freeze time.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceArtifactV1 {
    pub schema: String,
    /// Normalized relative path (forward slashes, no traversal).
    pub path: String,
    /// SHA-256 of exact raw bytes (independent of JSON).
    pub content_sha256: String,
    /// Exact raw byte length.
    pub byte_len: u64,
    /// Exact raw bytes (may be non-UTF-8). Serialized as base64 for JSON safety.
    #[serde(with = "serde_bytes_b64")]
    pub raw_bytes: Vec<u8>,
}

/// Half-open byte-offset span into a frozen source artifact.
/// Line numbers are advisory only.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceSpanV1 {
    pub path: String,
    pub content_sha256: String,
    /// Inclusive start byte offset.
    pub start: u64,
    /// Exclusive end byte offset.
    pub end: u64,
    pub start_line: Option<u32>,
    pub end_line: Option<u32>,
}

impl SourceSpanV1 {
    pub const SCHEMA: &'static str = SOURCE_SPAN_SCHEMA_V1;

    pub fn validate_against(&self, artifact: &SourceArtifactV1) -> Result<(), SpanValidationError> {
        if self.path != artifact.path {
            return Err(SpanValidationError::PathMismatch);
        }
        if self.content_sha256 != artifact.content_sha256 {
            return Err(SpanValidationError::HashMismatch);
        }
        if self.start > self.end || self.end > artifact.byte_len {
            return Err(SpanValidationError::OffsetOutOfRange);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SpanValidationError {
    #[error("span path does not match artifact")]
    PathMismatch,
    #[error("span content hash does not match artifact")]
    HashMismatch,
    #[error("span offsets out of range")]
    OffsetOutOfRange,
}

// ── Findings ────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ImprovementFindingV1 {
    pub schema: String,
    pub finding_id: String,
    pub detector_id: String,
    pub detector_version: String,
    pub grounded_spans: Vec<SourceSpanV1>,
    /// Observed fact bound to spans (not inference).
    pub observed_fact: String,
    /// Separate inference layer; never substitutes for observed_fact.
    pub inference: String,
    pub severity: FindingSeverityV1,
    pub proposed_route: ProposedRouteV1,
}

// ── Learning receipt ────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RunLearningReceiptV1 {
    pub schema: String,
    pub run: ImprovementRunV1,
    /// Immutable task terminal string from the host journal (pass/fail/refuse/…).
    pub task_terminal: String,
    pub maintenance_terminal: MaintenanceTerminalV1,
    pub findings: Vec<ImprovementFindingV1>,
    pub skipped_stages: Vec<String>,
    pub errors: Vec<String>,
    /// Hash chain of prior receipt digests + this receipt body hash (excl. chain).
    pub hash_chain: Vec<String>,
    /// Always `AuthorityEffect::None`.
    pub authority_effect: AuthorityEffect,
}

// ── Candidate ───────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExactEditV1 {
    pub path: String,
    pub baseline_sha256: String,
    pub replacement_sha256: String,
    #[serde(with = "serde_bytes_b64")]
    pub baseline_bytes: Vec<u8>,
    #[serde(with = "serde_bytes_b64")]
    pub replacement_bytes: Vec<u8>,
    /// Create if absent, else replace. Never delete-only in V1.
    pub create_or_replace: bool,
}

/// Bounded operator improvement candidate. V1 ends at proposal bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OperatorImprovementCandidateV1 {
    pub schema: String,
    pub candidate_id: String,
    pub edits: Vec<ExactEditV1>,
    pub declared_write_surface: Vec<String>,
    pub rollback_sha256: String,
    pub source_finding_ids: Vec<String>,
    /// Always true.
    pub host_admission_required: bool,
    /// Always false — self-activation is forbidden.
    pub self_activation_requested: bool,
    pub authority_effect: AuthorityEffect,
}

// ── Evaluation ──────────────────────────────────────────────────────────────

/// Hard-gate result then named integer reliability metrics.
/// No scalar “improvement score.”
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ImprovementEvaluationV1 {
    pub schema: String,
    pub candidate_id: String,
    pub hard_gates: Vec<HardGateResultV1>,
    pub reliability_metrics: Vec<NamedIntegerMetricV1>,
    pub authority_effect: AuthorityEffect,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HardGateResultV1 {
    pub gate_id: String,
    pub passed: bool,
    pub detail: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NamedIntegerMetricV1 {
    pub name: String,
    pub value: i64,
}

// ── Proposal bundle & adversary handoff ─────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProposalBundleV1 {
    pub schema: String,
    pub run: ImprovementRunV1,
    pub receipt: RunLearningReceiptV1,
    pub input_artifacts: Vec<SourceArtifactV1>,
    pub findings: Vec<ImprovementFindingV1>,
    pub candidate: Option<OperatorImprovementCandidateV1>,
    pub evaluation: Option<ImprovementEvaluationV1>,
    pub nonclaims: Vec<String>,
    pub adversary_handoff: AdversaryHandoffV1,
    pub maintenance_terminal: MaintenanceTerminalV1,
    pub authority_effect: AuthorityEffect,
}

/// Independently consumable adversary packet. Distinct-provider I3_CROSS_MODEL
/// re-derives a receipt from this packet; same-provider review cannot satisfy it.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AdversaryHandoffV1 {
    pub schema: String,
    pub handoff_id: String,
    pub run_id: String,
    pub candidate_id: Option<String>,
    pub required_independence_class: String,
    pub producer_provider_id: Option<String>,
    /// Forbidden providers for the I3 evaluator (includes producer when set).
    pub forbidden_provider_ids: Vec<String>,
    pub bundle_content_sha256: String,
    pub findings_sha256: String,
    pub candidate_sha256: Option<String>,
    pub nonclaims: Vec<String>,
    pub authority_effect: AuthorityEffect,
}

impl AdversaryHandoffV1 {
    pub const REQUIRED_INDEPENDENCE_CLASS: &'static str = "I3_CROSS_MODEL";
}

// ── Pending / protocol records ──────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PendingMaintenanceRunV1 {
    pub schema: String,
    pub run: ImprovementRunV1,
    pub policy: MaintenancePolicyV1,
    pub input_manifest_sha256: String,
    pub frozen_at_unix_ms: u64,
    pub status: PendingStatusV1,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PendingStatusV1 {
    Pending,
    Finalized,
    RecoveredIncomplete,
}

pub const PENDING_RUN_SCHEMA_V1: &str = "core.improvement.pending_run.v1";

// ── base64 helpers for raw bytes in JSON ────────────────────────────────────

mod serde_bytes_b64 {
    use serde::{Deserialize, Deserializer, Serializer};

    pub fn serialize<S: Serializer>(bytes: &[u8], serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_str(&b64_encode(bytes))
    }

    pub fn deserialize<'de, D: Deserializer<'de>>(deserializer: D) -> Result<Vec<u8>, D::Error> {
        let s = String::deserialize(deserializer)?;
        b64_decode(&s).map_err(serde::de::Error::custom)
    }

    fn b64_encode(bytes: &[u8]) -> String {
        const T: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        let mut out = String::new();
        for chunk in bytes.chunks(3) {
            let b0 = chunk[0] as u32;
            let b1 = chunk.get(1).copied().unwrap_or(0) as u32;
            let b2 = chunk.get(2).copied().unwrap_or(0) as u32;
            let n = (b0 << 16) | (b1 << 8) | b2;
            out.push(T[((n >> 18) & 63) as usize] as char);
            out.push(T[((n >> 12) & 63) as usize] as char);
            out.push(if chunk.len() > 1 {
                T[((n >> 6) & 63) as usize] as char
            } else {
                '='
            });
            out.push(if chunk.len() > 2 {
                T[(n & 63) as usize] as char
            } else {
                '='
            });
        }
        out
    }

    fn b64_decode(s: &str) -> Result<Vec<u8>, String> {
        fn val(c: u8) -> Result<u8, String> {
            match c {
                b'A'..=b'Z' => Ok(c - b'A'),
                b'a'..=b'z' => Ok(c - b'a' + 26),
                b'0'..=b'9' => Ok(c - b'0' + 52),
                b'+' => Ok(62),
                b'/' => Ok(63),
                _ => Err(format!("invalid base64 byte {c}")),
            }
        }
        let bytes = s.as_bytes();
        if !bytes.len().is_multiple_of(4) {
            return Err("invalid base64 length".to_owned());
        }
        let mut out = Vec::with_capacity(bytes.len() / 4 * 3);
        for chunk in bytes.chunks(4) {
            let pad = chunk.iter().filter(|&&c| c == b'=').count();
            let n = ((val(chunk[0])? as u32) << 18)
                | ((val(chunk[1])? as u32) << 12)
                | ((if chunk[2] == b'=' {
                    0
                } else {
                    val(chunk[2])? as u32
                }) << 6)
                | (if chunk[3] == b'=' {
                    0
                } else {
                    val(chunk[3])? as u32
                });
            out.push(((n >> 16) & 0xFF) as u8);
            if pad < 2 {
                out.push(((n >> 8) & 0xFF) as u8);
            }
            if pad < 1 {
                out.push((n & 0xFF) as u8);
            }
        }
        Ok(out)
    }
}

// Origin: engine/crates_rs/core_contracts/src/improvement_types.rs
// Claim: urn:core:crates_rs:core-contracts:improvement-types:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::improvement::{dumps_canonical_v1, hash_raw_bytes};

    #[test]
    fn maintenance_terminal_never_promotes() {
        for t in [
            MaintenanceTerminalV1::NoSignal,
            MaintenanceTerminalV1::NoCandidate,
            MaintenanceTerminalV1::BlockedAtAdversary,
            MaintenanceTerminalV1::RefusedEvidence,
            MaintenanceTerminalV1::RefusedProtectedSurface,
            MaintenanceTerminalV1::InfrastructureFailure,
        ] {
            assert!(!t.may_render_promotion_ready());
        }
    }

    #[test]
    fn self_lane_weight_default_is_zero() {
        let p = MaintenancePolicyV1::control_plane_defaults_v1();
        assert_eq!(p.self_lane_weight, 0);
        assert!(p.live_model_provider_id.is_none());
        assert_eq!(p.limits.max_candidates_per_run, 1);
    }

    #[test]
    fn source_artifact_round_trips_raw_bytes_including_invalid_utf8() {
        let raw = b"\x80\xFFhello\r\n".to_vec();
        let art = SourceArtifactV1 {
            schema: SOURCE_ARTIFACT_SCHEMA_V1.to_owned(),
            path: "x.md".to_owned(),
            content_sha256: hash_raw_bytes(&raw),
            byte_len: raw.len() as u64,
            raw_bytes: raw.clone(),
        };
        let bytes = dumps_canonical_v1(&art).unwrap();
        let back: SourceArtifactV1 = serde_json::from_slice(&bytes).unwrap();
        assert_eq!(back.raw_bytes, raw);
        assert_eq!(back.content_sha256, art.content_sha256);
    }

    #[test]
    fn span_validates_against_artifact() {
        let raw = b"abcdef";
        let art = SourceArtifactV1 {
            schema: SOURCE_ARTIFACT_SCHEMA_V1.to_owned(),
            path: "a.md".to_owned(),
            content_sha256: hash_raw_bytes(raw),
            byte_len: 6,
            raw_bytes: raw.to_vec(),
        };
        let ok = SourceSpanV1 {
            path: "a.md".to_owned(),
            content_sha256: art.content_sha256.clone(),
            start: 1,
            end: 4,
            start_line: Some(1),
            end_line: Some(1),
        };
        assert!(ok.validate_against(&art).is_ok());
        let bad = SourceSpanV1 {
            path: "a.md".to_owned(),
            content_sha256: art.content_sha256.clone(),
            start: 0,
            end: 99,
            start_line: None,
            end_line: None,
        };
        assert_eq!(
            bad.validate_against(&art).unwrap_err(),
            SpanValidationError::OffsetOutOfRange
        );
    }
}
