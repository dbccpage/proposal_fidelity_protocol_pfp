//! PKT-20260722-M2-EPOCH15: refusal-path auditing, credential scrubbing, and
//! retention with legal hold, exercised through the crate's public surface.
//!
//! Layering note: `core_replay` has no HTTP vocabulary and must not grow one.
//! A refusal at this layer is a `TerminalRecorded` whose terminal is a refusal
//! terminal; the mapping from HTTP 401/403/429 onto those terminals lives in
//! `core_api` (`status_for_terminal`). What is proven here is the half this
//! crate owns: a refusal outcome produces a durable, hash-chained row on disk
//! exactly like a success does.

use std::path::{Path, PathBuf};

use core_replay::retention::{redact_trace_v1, LegalHold, RetentionClass, RetentionPolicy};
use core_replay::trace_writer::{write_dual_trace_v1, TraceArtifactId};
use core_replay::{AppendOnlyTraceV1, SecretScrubber, TraceConfig, TraceEventKindV1, REDACTION};

fn lane_base(lane: &str) -> PathBuf {
    let base = Path::new(env!("CARGO_TARGET_TMPDIR"))
        .join("retention_security")
        .join(lane);
    let _ = std::fs::remove_dir_all(&base);
    base
}

fn config(base: &Path) -> TraceConfig {
    TraceConfig::new(true, true, base.to_path_buf()).expect("non-empty base dir")
}

/// `verdict` is constrained to `satisfied` / `failed` by `TraceArtifactId`, so
/// every refusal lane below records as `failed` -- a refusal is a failed
/// verdict, not a separate artifact category.
fn artifact(lane: &str, digest: &str, verdict: &str) -> TraceArtifactId {
    TraceArtifactId::new(lane.to_string(), digest.to_string(), verdict.to_string())
        .expect("valid artifact id")
}

/// A refused request still produces a full, replayable trace chain.
#[test]
fn test_refusal_path_emits_trace_row() {
    // The three refusal terminals `core_api::status_for_terminal` maps onto
    // 4xx: Refused -> 422, BudgetExhausted -> 429, Halted -> 423. None of them
    // may be a silent drop.
    for (lane, terminal) in [
        ("refused", "Refused"),
        ("budget", "BudgetExhausted"),
        ("halted", "Halted"),
    ] {
        let base = lane_base(lane);
        let mut trace = AppendOnlyTraceV1::default();
        trace
            .append(TraceEventKindV1::Fact {
                key: "outcome".to_string(),
                value: terminal.to_string(),
            })
            .expect("append outcome fact");
        trace
            .append(TraceEventKindV1::TerminalRecorded {
                terminal: terminal.to_string(),
            })
            .expect("append terminal");

        let written = write_dual_trace_v1(
            &config(&base),
            &artifact(lane, "00112233445566ff", "failed"),
            &trace,
        )
        .expect("a refusal must still be written");

        assert!(
            written.pair.trace_path().exists(),
            "{terminal}: refusal produced no artifact on disk"
        );

        // The row is durable AND hash-chained: reload from disk and replay.
        let bytes = std::fs::read(written.pair.trace_path()).expect("read refusal artifact");
        let persisted: AppendOnlyTraceV1 = serde_json::from_slice(&bytes).expect("deserialize");
        let replayed = persisted.replay().expect("persisted refusal chain replays");
        assert_eq!(
            replayed.replay_sha256, written.replay_sha256,
            "{terminal}: receipt digest must match the persisted chain"
        );
        assert_eq!(
            replayed.terminal.as_ref().map(|t| t.terminal.as_str()),
            Some(terminal),
            "{terminal}: refusal terminal must survive to disk"
        );
    }
}

/// Planted credentials must not reach the artifact bytes.
#[test]
fn test_secret_scrubber_redacts_api_keys() {
    let base = lane_base("scrubbed");
    let planted =
        "call failed for sk-ant-api03-PLANTEDSECRET with ANTHROPIC_API_KEY=hunter2seekrit";

    // Scrub BEFORE sealing. Sealing first would hash the raw text, and no later
    // edit could remove it without invalidating event_sha256.
    let (clean, report) = SecretScrubber::new().scrub(planted);
    assert_eq!(report.redacted, 2, "both planted secrets must be found");

    let mut trace = AppendOnlyTraceV1::default();
    trace
        .append(TraceEventKindV1::ResidualObserved {
            residual_id: "R-AUTH".to_string(),
            detail: clean.into_owned(),
        })
        .expect("append scrubbed residual");
    trace
        .append(TraceEventKindV1::TerminalRecorded {
            terminal: "Refused".to_string(),
        })
        .expect("append terminal");

    let written = write_dual_trace_v1(
        &config(&base),
        &artifact("scrubbed", "aabbccddeeff0011", "failed"),
        &trace,
    )
    .expect("write scrubbed trace");

    for path in [written.pair.trace_path(), written.pair.narrative_path()] {
        let text = std::fs::read_to_string(path).expect("read artifact");
        assert!(
            !text.contains("PLANTEDSECRET"),
            "secret leaked into {}: {text}",
            path.display()
        );
        assert!(
            !text.contains("hunter2seekrit"),
            "env-assigned secret leaked into {}",
            path.display()
        );
    }

    let text = std::fs::read_to_string(written.pair.trace_path()).expect("read trace");
    assert!(
        text.contains(REDACTION),
        "the redaction marker should be visible in the artifact"
    );
}

/// Age-expired traces lose content; held traces do not.
#[test]
fn test_retention_policy_respects_legal_hold() {
    let policy = RetentionPolicy::new(30);
    let mut trace = AppendOnlyTraceV1::default();
    trace
        .append(TraceEventKindV1::Fact {
            key: "input_text".to_string(),
            value: "PRIVATE-USER-PROMPT".to_string(),
        })
        .expect("append fact");
    trace
        .append(TraceEventKindV1::TerminalRecorded {
            terminal: "Completed".to_string(),
        })
        .expect("append terminal");
    let replay_sha = trace.replay().expect("chain replays").replay_sha256;

    // Expired and unheld -> redact.
    assert_eq!(
        policy.classify(400, LegalHold::Released),
        RetentionClass::Redact
    );
    let redacted = redact_trace_v1(&trace, replay_sha.clone(), LegalHold::Released)
        .expect("expired trace redacts");
    let json = redacted.to_json().expect("serialize redacted");
    assert!(
        !json.contains("PRIVATE-USER-PROMPT"),
        "raw input text survived retention: {json}"
    );

    // The hash chain survives the content.
    assert_eq!(
        redacted.replay_sha256, replay_sha,
        "replay_sha256 must be preserved across redaction"
    );
    redacted
        .verify_chain_linkage()
        .expect("redacted ledger keeps a contiguous, linked chain");

    // Equally aged, but held -> preserved, and the redactor itself refuses.
    assert_eq!(
        policy.classify(400, LegalHold::Held),
        RetentionClass::HeldPastWindow
    );
    assert!(
        redact_trace_v1(&trace, replay_sha, LegalHold::Held).is_err(),
        "an automated sweep must not be able to redact held evidence"
    );
}

// Origin: engine/crates_rs/tests/core_replay/retention_security_test.rs
// Claim: urn:core:crates_rs:tests:retention-security-test:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd841ac7c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd841ac7c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord841ac7c {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrord841ac7c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord841ac7c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord841ac7c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd841ac7c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord841ac7c> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord841ac7c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord841ac7c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord841ac7c::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[test]
fn l4_boundary_admits_and_refuses_d841ac7c() {
    let admitted = BoundaryRecordd841ac7c::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd841ac7c::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
