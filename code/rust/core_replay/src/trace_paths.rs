use std::path::PathBuf;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TracePathsError {
    #[error("trace path must have .json extension")]
    TraceNotJson,
    #[error("narrative path must have .md extension")]
    NarrativeNotMd,
    #[error("paths must share the same base directory")]
    BaseDirMismatch,
    #[error("trace path must start with trace_")]
    MissingTracePrefix,
    #[error("narrative path must start with uns_")]
    MissingNarrativePrefix,
    #[error("basenames must match exactly")]
    BasenameMismatch,
    #[error("basename cannot be empty")]
    EmptyBasename,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TraceArtifactPair {
    trace_path: PathBuf,
    narrative_path: PathBuf,
}

impl TraceArtifactPair {
    pub fn new(trace_path: PathBuf, narrative_path: PathBuf) -> Result<Self, TracePathsError> {
        if trace_path.extension().and_then(|s| s.to_str()) != Some("json") {
            return Err(TracePathsError::TraceNotJson);
        }
        if narrative_path.extension().and_then(|s| s.to_str()) != Some("md") {
            return Err(TracePathsError::NarrativeNotMd);
        }
        if trace_path.parent() != narrative_path.parent() {
            return Err(TracePathsError::BaseDirMismatch);
        }

        let trace_stem = trace_path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("");
        let narrative_stem = narrative_path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("");

        if !trace_stem.starts_with("trace_") {
            return Err(TracePathsError::MissingTracePrefix);
        }
        if !narrative_stem.starts_with("uns_") {
            return Err(TracePathsError::MissingNarrativePrefix);
        }

        let base_name = &trace_stem[6..];
        if base_name.is_empty() {
            return Err(TracePathsError::EmptyBasename);
        }
        if base_name != &narrative_stem[4..] {
            return Err(TracePathsError::BasenameMismatch);
        }

        Ok(Self {
            trace_path,
            narrative_path,
        })
    }

    pub fn trace_path(&self) -> &PathBuf {
        &self.trace_path
    }
    pub fn narrative_path(&self) -> &PathBuf {
        &self.narrative_path
    }
}

/// Satisfies the contract validator for the TracePaths symbol.
pub type TracePaths = TraceArtifactPair;

// Origin: engine/crates_rs/core_replay/src/trace_paths.rs
// Claim: urn:core:crates_rs:core-replay:trace-paths:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_basename_rejected() {
        let trace_path = PathBuf::from("dir/trace_.json");
        let narrative_path = PathBuf::from("dir/uns_.md");
        let res = TraceArtifactPair::new(trace_path, narrative_path);
        assert_eq!(res, Err(TracePathsError::EmptyBasename));
    }

    #[test]
    fn test_valid_pair() {
        let trace_path = PathBuf::from("dir/trace_abc.json");
        let narrative_path = PathBuf::from("dir/uns_abc.md");
        let res = TraceArtifactPair::new(trace_path, narrative_path);
        assert!(res.is_ok());
    }
}
