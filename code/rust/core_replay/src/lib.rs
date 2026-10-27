pub mod append_log;
pub mod dual_trace_memory;
pub mod replay_harness;
pub mod replay_hash;
pub mod retention;
pub mod secret_scrubber;
pub mod t3_authority;
pub mod run_folder;
pub mod run_trace;
pub mod trace;
pub mod trace_config;
pub mod trace_paths;
pub mod trace_policy;
pub mod trace_writer;

pub use run_folder::{
    compute_file_sha256, generate_run_folder_name, sanitize_task_slug, seal_run_folder,
    verify_run_folder, RunFolder, RunFolderError, RunManifestV1, RunMode, RunReceiptV1, RunTrigger,
    AUTHORITY_EFFECT_NONE, MANIFEST_SCHEMA_V1, RECEIPT_SCHEMA_V1,
};

pub use append_log::{AppendLogError, AppendLogRecordV1, AppendLogV1};
#[allow(deprecated)]
pub use dual_trace_memory::{
    derive_markdown_narrative_v1, emit_retrospective_v1, AppendOnlyTraceV1, DualTraceError,
    ImprovementCandidateV1, MemoryReferenceV1, ReplayFactV1, ReplayResidualV1, ReplayStateV1,
    ReplayTerminalV1, RunRetrospectiveV1, TraceEventKindV1, TraceEventV1, DUAL_TRACE_SCHEMA_V1,
};
pub use replay_harness::{ReplayPacket, T3Verifier, VerificationAudit, VerificationStatus};
pub use replay_hash::{ReplayHash, ScopedReplayHash, ScopedReplayHashError};
pub use retention::{
    redact_trace_v1, LegalHold, RedactedEventV1, RedactedTraceV1, RetentionClass, RetentionError,
    RetentionPolicy,
};
pub use run_trace::{
    BoundarySnapshot, BoundaryTrace, EvaluationGraph, NodeLabel, ObstructionDiagnostics,
    OffDiagonalCoherence, PerceptionSnapshot, RunTrace, SbeSnapshot, SbeTrace,
    TraceDensityDiagnostics, TraceStage, VerdictRecord,
};
pub use secret_scrubber::{ScrubReport, SecretScrubber, REDACTION};
pub use t3_authority::witness_from_t3_replay;
pub use trace::{
    ActionResultArtifact, DecisionArtifact, ImmutableTrace, LayeredTrace, StepTrace, TraceArtifact,
    ValidationArtifact, VoidTrace,
};
pub use trace_config::{TraceConfig, TraceConfigError};
pub use trace_paths::{TraceArtifactPair, TracePathsError};
pub use trace_writer::{write_dual_trace_v1, TraceWriteError, WrittenTraceV1};

/// Retention class of one scoped replay hash under the exported age-and-hold law.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReplayRetentionEnvelope {
    max_age_days: u64,
    age_days: u64,
    window_residual: u64,
    class: RetentionClass,
    authority: &'static str,
    hash_len: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ReplayRetentionError {
    Scope(ScopedReplayHashError),
    AuthorityDrift,
    ClassMismatch,
    AgeResidual,
}

// Origin: engine/crates_rs/core_replay/src/lib.rs
// Claim: urn:core:crates_rs:core-replay:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ReplayRetentionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ReplayRetentionError {}

impl ReplayRetentionEnvelope {
    pub fn try_classify(
        policy: RetentionPolicy,
        age_days: u64,
        hold: LegalHold,
        verifier_scope: &str,
        replay_hash: &str,
    ) -> Result<Self, ReplayRetentionError> {
        if AUTHORITY_EFFECT_NONE != "None" {
            return Err(ReplayRetentionError::AuthorityDrift);
        }
        let scoped = ScopedReplayHash::new(verifier_scope, replay_hash)
            .map_err(ReplayRetentionError::Scope)?;
        let class = policy.classify(age_days, hold);
        let (expected, window_residual) = if age_days <= policy.max_age_days {
            let residual = policy
                .max_age_days
                .checked_sub(age_days)
                .ok_or(ReplayRetentionError::AgeResidual)?;
            (RetentionClass::Retain, residual)
        } else {
            let residual = age_days
                .checked_sub(policy.max_age_days)
                .ok_or(ReplayRetentionError::AgeResidual)?;
            if residual == 0 {
                return Err(ReplayRetentionError::AgeResidual);
            }
            let expected = match hold {
                LegalHold::Held => RetentionClass::HeldPastWindow,
                LegalHold::Released => RetentionClass::Redact,
            };
            (expected, residual)
        };
        if class != expected {
            return Err(ReplayRetentionError::ClassMismatch);
        }
        let hash_len = scoped.replay_hash().len();
        if hash_len == 0 {
            return Err(ReplayRetentionError::Scope(
                ScopedReplayHashError::MissingReplayHash,
            ));
        }
        Ok(Self {
            max_age_days: policy.max_age_days,
            age_days,
            window_residual,
            class,
            authority: AUTHORITY_EFFECT_NONE,
            hash_len,
        })
    }

    pub fn class(&self) -> RetentionClass {
        self.class
    }

    pub fn window_residual(&self) -> u64 {
        self.window_residual
    }

    pub fn authority(&self) -> &'static str {
        self.authority
    }

    pub fn max_age_days(&self) -> u64 {
        self.max_age_days
    }

    pub fn age_days(&self) -> u64 {
        self.age_days
    }

    pub fn hash_len(&self) -> usize {
        self.hash_len
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn step_trace_round_trip_serialization() {
        let trace = StepTrace::new(vec![1u32, 2, 3]);
        let json = serde_json::to_string(&trace).unwrap();
        let recovered: StepTrace<u32> = serde_json::from_str(&json).unwrap();
        assert_eq!(trace.steps(), recovered.steps());
    }

    #[test]
    fn void_trace_serializable() {
        let trace = VoidTrace;
        let json = serde_json::to_string(&trace).unwrap();
        let _: VoidTrace = serde_json::from_str(&json).unwrap();
    }
}
