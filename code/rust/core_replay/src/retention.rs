//! Retention: age out trace CONTENT while keeping the hash ledger auditable.
//!
//! # Why redaction cannot be an in-place edit
//!
//! [`TraceEventV1::event_sha256`] is taken over the event content, and
//! [`AppendOnlyTraceV1::replay`] recomputes it per event. So scrubbing the
//! payload of a sealed event and leaving it in the same structure produces a
//! chain that fails its own verification: there is no edit that removes the
//! text and still satisfies `verify()`. That is arithmetic, not policy.
//!
//! Retention therefore produces a DIFFERENT artifact, [`RedactedTraceV1`],
//! rather than mutating the trace. What survives redaction is the part that
//! never depended on the content being present:
//!
//! * every recorded `event_sha256` and `parent_sha256`, verbatim;
//! * the run's `replay_sha256`;
//! * therefore the LINKAGE invariant -- each event's recorded parent equals the
//!   previous event's recorded hash -- which [`RedactedTraceV1::verify_chain_linkage`]
//!   still checks with no content at all.
//!
//! What does NOT survive is the ability to re-derive those hashes. A redacted
//! trace proves *that* a chain of given digests existed and was contiguous; it
//! cannot prove what those digests were taken over. Claiming otherwise would be
//! claiming to hash data we deliberately destroyed. Callers must not describe a
//! redacted artifact as replay-verified.
//!
//! Records under [`LegalHold`] are never redacted regardless of age.

use serde::{Deserialize, Serialize};

use crate::dual_trace_memory::{AppendOnlyTraceV1, TraceEventKindV1};
use crate::secret_scrubber::REDACTION;

pub const REDACTED_TRACE_SCHEMA_V1: &str = "core.redacted-trace.v1";

/// Preservation order that outranks any retention window.
///
/// Deliberately a separate type from a `bool` flag: clearing a hold is an
/// operator act, and the packet's non-goals forbid an automated routine from
/// removing one. Nothing in this module constructs [`LegalHold::Released`] --
/// a caller must state it explicitly.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum LegalHold {
    /// Preserve un-redacted regardless of age.
    Held,
    /// No hold; the retention window governs.
    Released,
}

/// What retention says to do with one artifact.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RetentionClass {
    /// Inside the window: keep content as-is.
    Retain,
    /// Past the window: content must be redacted.
    Redact,
    /// Past the window but preserved by a legal hold.
    HeldPastWindow,
}

/// Age-based retention window.
///
/// The decision takes an explicit age rather than reading a clock, so the
/// policy is a pure function: tests are hermetic and two nodes classifying the
/// same artifact cannot disagree because their clocks differ.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct RetentionPolicy {
    /// Days of raw content retention. `0` means redact at the first sweep.
    pub max_age_days: u64,
}

impl RetentionPolicy {
    pub const fn new(max_age_days: u64) -> Self {
        Self { max_age_days }
    }

    /// Classify one artifact. A hold always wins over an expired window.
    pub const fn classify(&self, age_days: u64, hold: LegalHold) -> RetentionClass {
        if age_days <= self.max_age_days {
            return RetentionClass::Retain;
        }
        match hold {
            LegalHold::Held => RetentionClass::HeldPastWindow,
            LegalHold::Released => RetentionClass::Redact,
        }
    }
}

/// One event reduced to its hash coordinates.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RedactedEventV1 {
    pub sequence: u64,
    pub parent_sha256: Option<String>,
    /// The ORIGINAL digest, carried verbatim. Not recomputable from this struct.
    pub event_sha256: String,
    /// Discriminant of the event that was here, kept because it carries no
    /// user text and makes a redacted ledger legible.
    pub kind: &'static str,
    /// Fixed marker; never the original text.
    pub content: &'static str,
}

/// A trace whose content has been aged out, retaining the hash ledger.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RedactedTraceV1 {
    pub schema: &'static str,
    /// The run digest recorded before redaction.
    pub replay_sha256: String,
    pub events: Vec<RedactedEventV1>,
}

/// Why a redacted chain is not internally consistent.
#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum RetentionError {
    #[error("redacted chain: event {0} is out of sequence")]
    SequenceGap(u64),
    #[error("redacted chain: event {0} does not link to its recorded parent")]
    ParentMismatch(u64),
    #[error("refused to redact an artifact under legal hold")]
    UnderLegalHold,
}

/// Reduce `trace` to its hash ledger, destroying event content.
///
/// `replay_sha256` is the digest the caller recorded when the trace was
/// written; it is carried through rather than recomputed, because after this
/// call the material it was taken over no longer exists.
///
/// Refuses outright when `hold` is [`LegalHold::Held`] -- an automated sweep
/// must not be able to redact held evidence by passing the wrong age.
pub fn redact_trace_v1(
    trace: &AppendOnlyTraceV1,
    replay_sha256: impl Into<String>,
    hold: LegalHold,
) -> Result<RedactedTraceV1, RetentionError> {
    if hold == LegalHold::Held {
        return Err(RetentionError::UnderLegalHold);
    }
    let events = trace
        .events()
        .iter()
        .map(|event| RedactedEventV1 {
            sequence: event.sequence,
            parent_sha256: event.parent_sha256.clone(),
            event_sha256: event.event_sha256.clone(),
            kind: match event.event {
                TraceEventKindV1::Fact { .. } => "fact",
                TraceEventKindV1::ResidualObserved { .. } => "residual_observed",
                TraceEventKindV1::TerminalRecorded { .. } => "terminal_recorded",
            },
            content: REDACTION,
        })
        .collect();

    Ok(RedactedTraceV1 {
        schema: REDACTED_TRACE_SCHEMA_V1,
        replay_sha256: replay_sha256.into(),
        events,
    })
}

impl RedactedTraceV1 {
    /// Check the linkage invariant that survives content destruction: events
    /// are contiguous from 0 and each records the previous event's digest as
    /// its parent.
    ///
    /// This is NOT replay verification. It cannot detect a digest that was
    /// altered together with its child's parent field, because without the
    /// content there is nothing to recompute against. It detects truncation,
    /// reordering, and splicing -- which is what a retention ledger is for.
    pub fn verify_chain_linkage(&self) -> Result<(), RetentionError> {
        let mut expected_parent: Option<&str> = None;
        for (index, event) in self.events.iter().enumerate() {
            if event.sequence != index as u64 {
                return Err(RetentionError::SequenceGap(event.sequence));
            }
            if event.parent_sha256.as_deref() != expected_parent {
                return Err(RetentionError::ParentMismatch(event.sequence));
            }
            expected_parent = Some(&event.event_sha256);
        }
        Ok(())
    }

    /// Serialized form contains no event content by construction.
    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(self)
    }
}

// Origin: engine/crates_rs/core_replay/src/retention.rs
// Claim: urn:core:crates_rs:core-replay:retention:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_trace() -> AppendOnlyTraceV1 {
        let mut trace = AppendOnlyTraceV1::default();
        trace
            .append(TraceEventKindV1::Fact {
                key: "input_text".into(),
                value: "the users private prompt".into(),
            })
            .expect("fact appends");
        trace
            .append(TraceEventKindV1::ResidualObserved {
                residual_id: "R1".into(),
                detail: "another private detail".into(),
            })
            .expect("residual appends");
        trace
            .append(TraceEventKindV1::TerminalRecorded {
                terminal: "Refused".into(),
            })
            .expect("terminal appends");
        trace
    }

    #[test]
    fn inside_the_window_content_is_retained() {
        let policy = RetentionPolicy::new(30);
        assert_eq!(
            policy.classify(29, LegalHold::Released),
            RetentionClass::Retain
        );
        assert_eq!(
            policy.classify(30, LegalHold::Released),
            RetentionClass::Retain,
            "the boundary day is still inside the window"
        );
    }

    #[test]
    fn past_the_window_content_is_redacted() {
        let policy = RetentionPolicy::new(30);
        assert_eq!(
            policy.classify(31, LegalHold::Released),
            RetentionClass::Redact
        );
    }

    #[test]
    fn test_retention_policy_respects_legal_hold() {
        let policy = RetentionPolicy::new(30);
        assert_eq!(
            policy.classify(9_999, LegalHold::Held),
            RetentionClass::HeldPastWindow,
            "a hold outranks any window"
        );
        // And the redactor itself refuses, so a wrong age cannot destroy held evidence.
        let trace = sample_trace();
        assert_eq!(
            redact_trace_v1(&trace, "deadbeef", LegalHold::Held),
            Err(RetentionError::UnderLegalHold)
        );
    }

    #[test]
    fn redaction_destroys_content_but_keeps_digests() {
        let trace = sample_trace();
        let replay_sha = trace.replay().expect("chain replays").replay_sha256;
        let redacted =
            redact_trace_v1(&trace, replay_sha.clone(), LegalHold::Released).expect("redacts");

        let json = redacted.to_json().expect("serializes");
        assert!(!json.contains("the users private prompt"), "{json}");
        assert!(!json.contains("another private detail"), "{json}");

        assert_eq!(redacted.replay_sha256, replay_sha);
        for (original, kept) in trace.events().iter().zip(&redacted.events) {
            assert_eq!(original.event_sha256, kept.event_sha256);
            assert_eq!(original.parent_sha256, kept.parent_sha256);
        }
    }

    #[test]
    fn redacted_chain_linkage_still_verifies() {
        let trace = sample_trace();
        let replay_sha = trace.replay().expect("chain replays").replay_sha256;
        let redacted = redact_trace_v1(&trace, replay_sha, LegalHold::Released).expect("redacts");
        assert_eq!(redacted.verify_chain_linkage(), Ok(()));
    }

    #[test]
    fn splicing_a_redacted_chain_is_detected() {
        let trace = sample_trace();
        let replay_sha = trace.replay().expect("chain replays").replay_sha256;
        let mut redacted =
            redact_trace_v1(&trace, replay_sha, LegalHold::Released).expect("redacts");

        redacted.events.remove(1); // drop the middle event
        assert!(
            matches!(
                redacted.verify_chain_linkage(),
                Err(RetentionError::SequenceGap(_) | RetentionError::ParentMismatch(_))
            ),
            "a truncated ledger must not pass linkage verification"
        );
    }

    #[test]
    fn terminal_kind_survives_so_a_redacted_ledger_stays_legible() {
        let trace = sample_trace();
        let replay_sha = trace.replay().expect("chain replays").replay_sha256;
        let redacted = redact_trace_v1(&trace, replay_sha, LegalHold::Released).expect("redacts");
        assert_eq!(redacted.events[0].kind, "fact");
        assert_eq!(redacted.events[2].kind, "terminal_recorded");
        assert!(redacted.events.iter().all(|e| e.content == REDACTION));
    }
}
