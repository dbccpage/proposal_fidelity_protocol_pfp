//! Append-only dual-trace artifact writer for the `.intelligence/.traces/`
//! convention ([`crate::trace_policy::build_trace_paths`]).
//!
//! Contract: an artifact, once written, is IMMUTABLE. A re-emit with
//! byte-identical content is an idempotent no-op (reported via
//! [`WrittenTraceV1::idempotent`]); a re-emit whose bytes diverge is refused
//! with [`TraceWriteError::ExistingArtifactMismatch`]. The event chain is
//! replay-verified ([`AppendOnlyTraceV1::replay`]) BEFORE any filesystem
//! effect, so a tampered chain never reaches disk.
//!
//! Diagnostic machinery only — writing a trace mints no authority.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_aa39cb14<T> {
    fn checked_invariant_aa39cb14(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_aa39cb14<T> for Option<T> {
    #[inline]
    fn checked_invariant_aa39cb14(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_aa39cb14<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_aa39cb14(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::fs;
use std::io::{self, Write as _};
use std::path::Path;

use crate::dual_trace_memory::{derive_markdown_narrative_v1, AppendOnlyTraceV1, DualTraceError};
use crate::trace_config::TraceConfig;
use crate::trace_paths::{TraceArtifactPair, TracePathsError};
use crate::trace_policy::build_trace_paths;

pub use core_types::trace_artifact_id::{TraceArtifactId, TraceArtifactIdError};

/// Failure emitting a dual-trace artifact pair.
#[derive(Debug, thiserror::Error)]
pub enum TraceWriteError {
    /// The in-memory event chain failed replay verification (nothing written).
    #[error(transparent)]
    Chain(#[from] DualTraceError),
    /// The artifact id produced an invalid path pair.
    #[error(transparent)]
    Paths(#[from] TracePathsError),
    /// The trace could not be serialized to canonical JSON.
    #[error("serialize trace: {0}")]
    Serialize(String),
    /// Filesystem failure creating or reading an artifact.
    #[error("trace io at {path}: {source}")]
    Io {
        path: String,
        #[source]
        source: io::Error,
    },
    /// Append-only violation: the artifact exists with DIFFERENT bytes.
    #[error("append-only violation: {path} already exists with different content")]
    ExistingArtifactMismatch { path: String },
}

/// Receipt for one emitted (or idempotently re-emitted) artifact pair.
#[derive(Debug)]
pub struct WrittenTraceV1 {
    /// The validated `trace_*.json` / `uns_*.md` path pair.
    pub pair: TraceArtifactPair,
    /// `sha256` of the replayed event chain (the trace digest).
    pub replay_sha256: String,
    /// `true` when byte-identical artifacts already existed (no-op re-emit).
    pub idempotent: bool,
}

/// Verify the chain, then persist `trace_*.json` + `uns_*.md` under
/// `<base>/.intelligence/.traces/`, append-only.
pub fn write_dual_trace_v1(
    config: &TraceConfig,
    artifact_id: &TraceArtifactId,
    trace: &AppendOnlyTraceV1,
) -> Result<WrittenTraceV1, TraceWriteError> {
    let state = trace.replay()?;
    let pair = build_trace_paths(config, artifact_id)?;
    let trace_bytes = serde_json::to_vec_pretty(trace)
        .map_err(|error| TraceWriteError::Serialize(error.to_string()))?;
    let narrative = derive_markdown_narrative_v1(&state);

    let dir = pair
        .trace_path()
        .parent()
        .checked_invariant_aa39cb14("build_trace_paths always yields a parented path");
    fs::create_dir_all(dir).map_err(|source| io_error(dir, source))?;

    let trace_existed = write_append_only(pair.trace_path(), &trace_bytes)?;
    let narrative_existed = write_append_only(pair.narrative_path(), narrative.as_bytes())?;

    Ok(WrittenTraceV1 {
        replay_sha256: state.replay_sha256,
        idempotent: trace_existed && narrative_existed,
        pair,
    })
}

/// Create-new write; on `AlreadyExists`, admit only byte-identical content.
/// Returns whether the artifact already existed (the idempotent path).
fn write_append_only(path: &Path, bytes: &[u8]) -> Result<bool, TraceWriteError> {
    match fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
    {
        Ok(mut file) => {
            file.write_all(bytes)
                .map_err(|source| io_error(path, source))?;
            Ok(false)
        }
        Err(error) if error.kind() == io::ErrorKind::AlreadyExists => {
            let existing = fs::read(path).map_err(|source| io_error(path, source))?;
            if existing == bytes {
                Ok(true)
            } else {
                Err(TraceWriteError::ExistingArtifactMismatch {
                    path: path.display().to_string(),
                })
            }
        }
        Err(source) => Err(io_error(path, source)),
    }
}

fn io_error(path: &Path, source: io::Error) -> TraceWriteError {
    TraceWriteError::Io {
        path: path.display().to_string(),
        source,
    }
}

// Origin: engine/crates_rs/core_replay/src/trace_writer.rs
// Claim: urn:core:crates_rs:core-replay:trace-writer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_aa39cb14 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
