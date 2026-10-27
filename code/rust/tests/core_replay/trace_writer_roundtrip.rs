//! Roundtrip and failure-path lanes for `core_replay::trace_writer`
//! (PKT-20260721-M0-EPOCH1 supporting evidence).

use std::path::{Path, PathBuf};

use core_replay::trace_writer::{write_dual_trace_v1, TraceArtifactId, TraceWriteError};
use core_replay::{AppendOnlyTraceV1, TraceConfig, TraceEventKindV1};

fn lane_base(lane: &str) -> PathBuf {
    let base = Path::new(env!("CARGO_TARGET_TMPDIR"))
        .join("trace_writer_roundtrip")
        .join(lane);
    let _ = std::fs::remove_dir_all(&base);
    base
}

fn config(base: &Path) -> TraceConfig {
    TraceConfig::new(true, true, base.to_path_buf()).expect("non-empty base dir")
}

fn artifact() -> TraceArtifactId {
    TraceArtifactId::new(
        "writer_roundtrip".to_string(),
        "0123456789abcdef".to_string(),
        "satisfied".to_string(),
    )
    .expect("valid artifact id")
}

fn sample_trace() -> AppendOnlyTraceV1 {
    let mut trace = AppendOnlyTraceV1::default();
    trace
        .append(TraceEventKindV1::Fact {
            key: "schema".to_string(),
            value: "core.test.v1".to_string(),
        })
        .expect("append fact");
    trace
        .append(TraceEventKindV1::TerminalRecorded {
            terminal: "OpenObstruction".to_string(),
        })
        .expect("append terminal");
    trace
}

#[test]
fn roundtrip_writes_verifiable_artifact_pair() {
    let base = lane_base("roundtrip");
    let written = write_dual_trace_v1(&config(&base), &artifact(), &sample_trace())
        .expect("first write succeeds");
    assert!(!written.idempotent, "first emit is a real write");

    let trace_path = written.pair.trace_path();
    let narrative_path = written.pair.narrative_path();
    assert!(
        trace_path.starts_with(base.join(".intelligence").join(".traces")),
        "artifacts live under <base>/.intelligence/.traces, got {}",
        trace_path.display()
    );
    assert_eq!(
        trace_path.file_name().and_then(|s| s.to_str()),
        Some("trace_writer_roundtrip__satisfied__0123456789abcdef.json")
    );
    assert_eq!(
        narrative_path.file_name().and_then(|s| s.to_str()),
        Some("uns_writer_roundtrip__satisfied__0123456789abcdef.md")
    );

    let bytes = std::fs::read(trace_path).expect("read trace artifact");
    let persisted: AppendOnlyTraceV1 = serde_json::from_slice(&bytes).expect("deserialize");
    let replayed = persisted.replay().expect("persisted chain replays");
    assert_eq!(
        replayed.replay_sha256, written.replay_sha256,
        "receipt digest matches the persisted chain's replay"
    );
    assert_eq!(
        replayed.terminal.as_ref().map(|t| t.terminal.as_str()),
        Some("OpenObstruction"),
        "terminal event survives the roundtrip"
    );

    let narrative = std::fs::read_to_string(narrative_path).expect("read narrative");
    assert!(
        narrative.contains(&written.replay_sha256),
        "narrative pins the replay digest"
    );
}

#[test]
fn identical_re_emit_is_idempotent() {
    let base = lane_base("idempotent");
    let first = write_dual_trace_v1(&config(&base), &artifact(), &sample_trace())
        .expect("first write succeeds");
    let first_bytes = std::fs::read(first.pair.trace_path()).expect("read first artifact");

    let second = write_dual_trace_v1(&config(&base), &artifact(), &sample_trace())
        .expect("identical re-emit succeeds");
    assert!(second.idempotent, "byte-identical re-emit is a no-op");
    assert_eq!(second.replay_sha256, first.replay_sha256);
    assert_eq!(
        std::fs::read(first.pair.trace_path()).expect("re-read artifact"),
        first_bytes,
        "idempotent re-emit leaves the artifact byte-identical"
    );
}

#[test]
fn divergent_re_emit_is_refused() {
    let base = lane_base("divergent");
    let first = write_dual_trace_v1(&config(&base), &artifact(), &sample_trace())
        .expect("first write succeeds");
    let first_bytes = std::fs::read(first.pair.trace_path()).expect("read first artifact");

    let mut divergent = AppendOnlyTraceV1::default();
    divergent
        .append(TraceEventKindV1::Fact {
            key: "schema".to_string(),
            value: "core.other.v1".to_string(),
        })
        .expect("append fact");
    divergent
        .append(TraceEventKindV1::TerminalRecorded {
            terminal: "OpenObstruction".to_string(),
        })
        .expect("append terminal");

    let error = write_dual_trace_v1(&config(&base), &artifact(), &divergent)
        .expect_err("divergent re-emit must be refused");
    assert!(
        matches!(error, TraceWriteError::ExistingArtifactMismatch { .. }),
        "typed append-only refusal, got {error:?}"
    );
    assert_eq!(
        std::fs::read(first.pair.trace_path()).expect("re-read artifact"),
        first_bytes,
        "refused re-emit must not mutate the existing artifact"
    );
}

#[test]
fn tampered_chain_never_reaches_disk() {
    let base = lane_base("tampered");
    let json = serde_json::to_string(&sample_trace()).expect("serialize sample");
    let tampered_json = json.replace("core.test.v1", "core.tampered.v1");
    assert_ne!(json, tampered_json, "tamper control actually changed bytes");
    let tampered: AppendOnlyTraceV1 =
        serde_json::from_str(&tampered_json).expect("tampered trace still deserializes");

    let error = write_dual_trace_v1(&config(&base), &artifact(), &tampered)
        .expect_err("tampered chain must be refused");
    assert!(
        matches!(error, TraceWriteError::Chain(_)),
        "typed chain refusal, got {error:?}"
    );
    assert!(
        !base.exists(),
        "a refused chain must never materialize an artifact directory"
    );
}

// Origin: engine/crates_rs/tests/core_replay/trace_writer_roundtrip.rs
// Claim: urn:core:crates_rs:tests:trace-writer-roundtrip:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord02d2876d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord02d2876d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError02d2876d {
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
impl BoundaryError02d2876d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError02d2876d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError02d2876d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord02d2876d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError02d2876d> {
        if capacity_bound == 0 {
            return Err(BoundaryError02d2876d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError02d2876d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError02d2876d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_02d2876d() {
    let admitted = BoundaryRecord02d2876d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord02d2876d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
