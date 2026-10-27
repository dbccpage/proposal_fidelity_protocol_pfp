#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TraceArtifactIdError {
    #[error("test_name must be non-empty")]
    EmptyTestName,
    #[error("run id must be non-empty")]
    EmptyRunId,
    #[error("verdict must be satisfied or failed")]
    InvalidVerdict,
    #[error("filename separator is ambiguous")]
    AmbiguousSeparator,
    #[error("filename does not round-trip")]
    RoundTrip,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TraceArtifactId {
    test_name: String,
    run_id_short: String,
    verdict: String,
}

impl TraceArtifactId {
    pub fn new(
        test_name: String,
        run_id_short: String,
        verdict: String,
    ) -> Result<Self, TraceArtifactIdError> {
        if test_name.is_empty() {
            return Err(TraceArtifactIdError::EmptyTestName);
        }
        if run_id_short.is_empty() {
            return Err(TraceArtifactIdError::EmptyRunId);
        }
        if verdict != "satisfied" && verdict != "failed" {
            return Err(TraceArtifactIdError::InvalidVerdict);
        }

        Ok(Self {
            test_name,
            run_id_short,
            verdict,
        })
    }

    pub fn test_name(&self) -> &str {
        &self.test_name
    }
    pub fn run_id_short(&self) -> &str {
        &self.run_id_short
    }
    pub fn verdict(&self) -> &str {
        &self.verdict
    }

    pub fn filename_base(&self) -> String {
        format!(
            "{}__{}__{}",
            self.test_name, self.verdict, self.run_id_short
        )
    }

    /// Split `{test}__{verdict}__{run}` back into the three private fields.
    pub fn parse_filename_base(text: &str) -> Result<Self, TraceArtifactIdError> {
        let mut parts = text.split("__");
        let Some(test_name) = parts.next() else {
            return Err(TraceArtifactIdError::AmbiguousSeparator);
        };
        let Some(verdict) = parts.next() else {
            return Err(TraceArtifactIdError::AmbiguousSeparator);
        };
        let Some(run_id_short) = parts.next() else {
            return Err(TraceArtifactIdError::AmbiguousSeparator);
        };
        if parts.next().is_some() || text.matches("__").count() != 2 {
            return Err(TraceArtifactIdError::AmbiguousSeparator);
        }
        Self::new(test_name.to_owned(), run_id_short.to_owned(), verdict.to_owned())
    }

    /// A filename whose parts contain no separator parses back to the same id.
    pub fn round_trip(&self) -> Result<Self, TraceArtifactIdError> {
        if self.test_name.contains("__")
            || self.run_id_short.contains("__")
            || self.verdict.contains("__")
        {
            return Err(TraceArtifactIdError::AmbiguousSeparator);
        }
        let parsed = Self::parse_filename_base(&self.filename_base())?;
        if parsed.test_name != self.test_name
            || parsed.run_id_short != self.run_id_short
            || parsed.verdict != self.verdict
        {
            return Err(TraceArtifactIdError::RoundTrip);
        }
        Ok(parsed)
    }
}

// Origin: engine/crates_rs/core_types/src/trace_artifact_id.rs
// Claim: urn:core:crates_rs:core-types:trace-artifact-id:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod round_trip_tests {
    use super::*;

    fn taken(result: Result<TraceArtifactId, TraceArtifactIdError>) -> TraceArtifactId {
        result.map_or_else(|_| loop { assert!(false); }, |value| value)
    }

    #[test]
    fn filename_base_parses_back_to_the_three_fields() {
        let id = taken(TraceArtifactId::new(
            "trace-law".to_owned(),
            "run-4".to_owned(),
            "satisfied".to_owned(),
        ));
        let parsed = taken(id.round_trip());
        assert_eq!(parsed.filename_base(), "trace-law__satisfied__run-4");
        assert_eq!(parsed.verdict(), "satisfied");
    }

    #[test]
    fn a_third_separator_is_refused() {
        assert!(matches!(
            TraceArtifactId::parse_filename_base("a__satisfied__b__c"),
            Err(TraceArtifactIdError::AmbiguousSeparator)
        ));
    }
}
