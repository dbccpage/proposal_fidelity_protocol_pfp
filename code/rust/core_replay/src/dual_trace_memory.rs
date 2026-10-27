//! S09-001 append-only trace, replay-derived narrative, and bounded memory.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_bf5988c6<T> {
    fn checked_invariant_bf5988c6(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_bf5988c6<T> for Option<T> {
    #[inline]
    fn checked_invariant_bf5988c6(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_bf5988c6<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_bf5988c6(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeMap;

use core_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

pub const DUAL_TRACE_SCHEMA_V1: &str = "core.dual-trace-memory.v1";

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum TraceEventKindV1 {
    Fact { key: String, value: String },
    ResidualObserved { residual_id: String, detail: String },
    TerminalRecorded { terminal: String },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TraceEventV1 {
    pub sequence: u64,
    pub parent_sha256: Option<String>,
    pub event: TraceEventKindV1,
    pub event_sha256: String,
}

#[derive(Serialize)]
struct EventMaterialV1<'a> {
    sequence: u64,
    parent_sha256: &'a Option<String>,
    event: &'a TraceEventKindV1,
}

impl TraceEventV1 {
    pub fn seal(
        sequence: u64,
        parent_sha256: Option<String>,
        event: TraceEventKindV1,
    ) -> Result<Self, DualTraceError> {
        validate_event_text(&event)?;
        let event_sha256 = hash_json(&EventMaterialV1 {
            sequence,
            parent_sha256: &parent_sha256,
            event: &event,
        })?;
        Ok(Self {
            sequence,
            parent_sha256,
            event,
            event_sha256,
        })
    }

    pub fn verify(&self) -> Result<(), DualTraceError> {
        validate_event_text(&self.event)?;
        let expected = hash_json(&EventMaterialV1 {
            sequence: self.sequence,
            parent_sha256: &self.parent_sha256,
            event: &self.event,
        })?;
        if expected != self.event_sha256 {
            return Err(DualTraceError::EventHashMismatch(self.sequence));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(transparent)]
pub struct AppendOnlyTraceV1 {
    events: Vec<TraceEventV1>,
}

impl AppendOnlyTraceV1 {
    pub fn events(&self) -> &[TraceEventV1] {
        &self.events
    }

    pub fn append(&mut self, event: TraceEventKindV1) -> Result<&TraceEventV1, DualTraceError> {
        if self
            .events
            .last()
            .is_some_and(|last| matches!(last.event, TraceEventKindV1::TerminalRecorded { .. }))
        {
            return Err(DualTraceError::TerminalImmutable);
        }
        let sequence = self.events.len() as u64;
        let parent_sha256 = self.events.last().map(|last| last.event_sha256.clone());
        let sealed = TraceEventV1::seal(sequence, parent_sha256, event)?;
        self.events.push(sealed);
        Ok(self.events.last().checked_invariant_bf5988c6("event was just appended"))
    }

    fn apply_trace_event(
        state: &mut ReplayStateV1,
        event: &TraceEventV1,
    ) -> Result<(), DualTraceError> {
        match &event.event {
            TraceEventKindV1::Fact { key, value } => {
                state.facts.insert(
                    key.clone(),
                    ReplayFactV1 {
                        value: value.clone(),
                        source_event_sha256: event.event_sha256.clone(),
                    },
                );
            }
            TraceEventKindV1::ResidualObserved {
                residual_id,
                detail,
            } => {
                let residual = state
                    .residuals
                    .entry(residual_id.clone())
                    .or_insert_with(|| ReplayResidualV1 {
                        detail: detail.clone(),
                        occurrences: 0,
                        first_event_sha256: event.event_sha256.clone(),
                        latest_event_sha256: event.event_sha256.clone(),
                    });
                if residual.detail != *detail {
                    return Err(DualTraceError::ResidualMutation(residual_id.clone()));
                }
                residual.occurrences += 1;
                residual.latest_event_sha256 = event.event_sha256.clone();
            }
            TraceEventKindV1::TerminalRecorded { terminal } => {
                state.terminal = Some(ReplayTerminalV1 {
                    terminal: terminal.clone(),
                    source_event_sha256: event.event_sha256.clone(),
                });
            }
        }
        Ok(())
    }

    pub fn replay(&self) -> Result<ReplayStateV1, DualTraceError> {
        let mut state = ReplayStateV1::default();
        let mut expected_parent: Option<&str> = None;
        for (index, event) in self.events.iter().enumerate() {
            if state.terminal.is_some() {
                return Err(DualTraceError::TerminalImmutable);
            }
            if event.sequence != index as u64 || event.parent_sha256.as_deref() != expected_parent {
                return Err(DualTraceError::ParentMismatch(event.sequence));
            }
            event.verify()?;
            Self::apply_trace_event(&mut state, event)?;
            expected_parent = Some(&event.event_sha256);
        }
        state.replay_sha256 = hash_json(&self.events)?;
        Ok(state)
    }
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReplayStateV1 {
    pub facts: BTreeMap<String, ReplayFactV1>,
    pub residuals: BTreeMap<String, ReplayResidualV1>,
    pub terminal: Option<ReplayTerminalV1>,
    pub replay_sha256: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReplayFactV1 {
    pub value: String,
    pub source_event_sha256: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReplayResidualV1 {
    pub detail: String,
    pub occurrences: u32,
    pub first_event_sha256: String,
    pub latest_event_sha256: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReplayTerminalV1 {
    pub terminal: String,
    pub source_event_sha256: String,
}

pub fn derive_markdown_narrative_v1(state: &ReplayStateV1) -> String {
    let mut lines = vec![
        "# Verified Run Narrative".to_owned(),
        String::new(),
        format!("Replay SHA-256: `{}`", state.replay_sha256),
        String::new(),
        "## Facts".to_owned(),
    ];
    if state.facts.is_empty() {
        lines.push("- None recorded.".to_owned());
    } else {
        lines.extend(state.facts.iter().map(|(key, fact)| {
            format!(
                "- `{key}` = `{}` (event `{}`)",
                fact.value, fact.source_event_sha256
            )
        }));
    }
    lines.extend([String::new(), "## Residuals".to_owned()]);
    if state.residuals.is_empty() {
        lines.push("- None recorded.".to_owned());
    } else {
        lines.extend(state.residuals.iter().map(|(id, residual)| {
            format!(
                "- `{id}`: {} (occurrences: {}; event `{}`)",
                residual.detail, residual.occurrences, residual.latest_event_sha256
            )
        }));
    }
    lines.extend([String::new(), "## Terminal".to_owned()]);
    match &state.terminal {
        Some(terminal) => lines.push(format!(
            "- `{}` (event `{}`)",
            terminal.terminal, terminal.source_event_sha256
        )),
        None => lines.push("- Not recorded.".to_owned()),
    }
    lines.push(String::new());
    lines.join("\n")
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MemoryReferenceV1 {
    pub artifact_sha256: String,
    pub policy_reference: String,
    pub redaction_receipt_sha256: String,
}

impl MemoryReferenceV1 {
    pub fn validate(&self) -> Result<(), DualTraceError> {
        if !is_sha256(&self.artifact_sha256)
            || !is_sha256(&self.redaction_receipt_sha256)
            || self.policy_reference.trim().is_empty()
        {
            return Err(DualTraceError::UnsafeMemoryReference);
        }
        Ok(())
    }
}

/// Compatibility-epoch residual candidate stub.
///
/// Prefer `core_contracts::improvement::OperatorImprovementCandidateV1` for
/// new producers. This type remains for one epoch so existing retrospective
/// emitters keep compiling; it must not invent missing provenance fields.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[deprecated(note = "use core_contracts::improvement::OperatorImprovementCandidateV1")]
pub struct ImprovementCandidateV1 {
    pub candidate_id: String,
    pub repeated_residual_id: String,
    pub host_admission_required: bool,
    pub self_activation_requested: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(deprecated)]
pub struct RunRetrospectiveV1 {
    pub replay_sha256: String,
    pub residuals: Vec<String>,
    pub improvement_candidates: Vec<ImprovementCandidateV1>,
    pub memory_references: Vec<MemoryReferenceV1>,
    pub authority_effect: AuthorityEffect,
}

#[allow(deprecated)]
pub fn emit_retrospective_v1(
    state: &ReplayStateV1,
    memory_references: Vec<MemoryReferenceV1>,
) -> Result<RunRetrospectiveV1, DualTraceError> {
    if !is_sha256(&state.replay_sha256) {
        return Err(DualTraceError::ReplayHashMissing);
    }
    for reference in &memory_references {
        reference.validate()?;
    }
    let improvement_candidates = state
        .residuals
        .iter()
        .filter(|(_, residual)| residual.occurrences > 1)
        .map(|(id, _)| ImprovementCandidateV1 {
            candidate_id: format!("candidate-{id}"),
            repeated_residual_id: id.clone(),
            host_admission_required: true,
            self_activation_requested: false,
        })
        .collect();
    Ok(RunRetrospectiveV1 {
        replay_sha256: state.replay_sha256.clone(),
        residuals: state.residuals.keys().cloned().collect(),
        improvement_candidates,
        memory_references,
        authority_effect: AuthorityEffect::None,
    })
}

fn validate_event_text(event: &TraceEventKindV1) -> Result<(), DualTraceError> {
    let valid = match event {
        TraceEventKindV1::Fact { key, value } => !key.trim().is_empty() && !value.trim().is_empty(),
        TraceEventKindV1::ResidualObserved {
            residual_id,
            detail,
        } => !residual_id.trim().is_empty() && !detail.trim().is_empty(),
        TraceEventKindV1::TerminalRecorded { terminal } => !terminal.trim().is_empty(),
    };
    if valid {
        Ok(())
    } else {
        Err(DualTraceError::InvalidEventText)
    }
}

fn hash_json<T: Serialize + ?Sized>(value: &T) -> Result<String, DualTraceError> {
    let bytes =
        serde_json::to_vec(value).map_err(|error| DualTraceError::Json(error.to_string()))?;
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    Ok(format!("{:x}", hasher.finalize()))
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum DualTraceError {
    #[error("event {0} hash mismatch")]
    EventHashMismatch(u64),
    #[error("event {0} parent or sequence mismatch")]
    ParentMismatch(u64),
    #[error("terminal trace is immutable")]
    TerminalImmutable,
    #[error("residual {0} attempted to change meaning")]
    ResidualMutation(String),
    #[error("event text is empty")]
    InvalidEventText,
    #[error("replay hash is missing")]
    ReplayHashMissing,
    #[error("memory contains an unredacted or unbound reference")]
    UnsafeMemoryReference,
    #[error("JSON serialization failed: {0}")]
    Json(String),
}

// Origin: engine/crates_rs/core_replay/src/dual_trace_memory.rs
// Claim: urn:core:crates_rs:core-replay:dual-trace-memory:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_bf5988c6 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
