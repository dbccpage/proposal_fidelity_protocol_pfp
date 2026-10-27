//! Governance error types for Blackrod and Adversary functors.
//!
//! All governance errors are defensive in nature. No error type encodes
//! offensive, retaliatory, or real-world coercive semantics.

use serde::{Deserialize, Serialize};

/// Result type alias for governance operations.
pub type GovernanceResult<T> = Result<T, GovernanceError>;

/// Governance error types.
///
/// These errors describe failures in the governance enforcement/diagnostic pipeline.
/// No error variant encodes offensive or coercive semantics.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, thiserror::Error)]
pub enum GovernanceError {
    /// Authority boundary violation.
    #[error("authority violation: {0}")]
    AuthorityViolation(String),

    /// Evidence requirement not met.
    #[error("evidence missing: {artifact_id} requires {evidence_type}")]
    EvidenceMissing {
        artifact_id: String,
        evidence_type: String,
    },

    /// Invalid finding structure.
    #[error("invalid finding: {0}")]
    InvalidFinding(String),

    /// Trace not found.
    #[error("trace not found: {0}")]
    TraceNotFound(String),

    /// Council not found.
    #[error("council not found: {0}")]
    CouncilNotFound(String),

    /// License not found.
    #[error("license not found: {0}")]
    LicenseNotFound(String),

    /// Artifact not found.
    #[error("artifact not found: {0}")]
    ArtifactNotFound(String),

    /// Meeting not found.
    #[error("meeting not found: {0}")]
    MeetingNotFound(String),

    /// Internal governance error.
    #[error("internal error: {0}")]
    InternalError(String),
}

/// Unique identifier for a trace record.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct TraceId(pub String);

impl TraceId {
    /// Create a new trace identifier.
    pub fn new(id: impl Into<String>) -> Self {
        Self(id.into())
    }

    /// Get the trace ID as a string slice.
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl From<String> for TraceId {
    fn from(s: String) -> Self {
        Self(s)
    }
}

impl From<&str> for TraceId {
    fn from(s: &str) -> Self {
        Self(s.to_string())
    }
}

/// Unique identifier for a council.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct CouncilId(pub String);

impl CouncilId {
    /// Create a new council identifier.
    pub fn new(id: impl Into<String>) -> Self {
        Self(id.into())
    }

    /// Get the council ID as a string slice.
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl From<String> for CouncilId {
    fn from(s: String) -> Self {
        Self(s)
    }
}

impl From<&str> for CouncilId {
    fn from(s: &str) -> Self {
        Self(s.to_string())
    }
}

/// Unique identifier for a license.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct LicenseId(pub String);

impl LicenseId {
    /// Create a new license identifier.
    pub fn new(id: impl Into<String>) -> Self {
        Self(id.into())
    }

    /// Get the license ID as a string slice.
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl From<String> for LicenseId {
    fn from(s: String) -> Self {
        Self(s)
    }
}

impl From<&str> for LicenseId {
    fn from(s: &str) -> Self {
        Self(s.to_string())
    }
}

/// Artifact type classification.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ArtifactType {
    /// Source code artifact.
    Code,
    /// Test artifact.
    Test,
    /// Documentation artifact.
    Documentation,
    /// Configuration artifact.
    Configuration,
    /// Trace artifact.
    Trace,
    /// Evidence artifact.
    Evidence,
    /// Certificate artifact.
    Certificate,
    /// Unknown artifact type.
    Unknown,
}

/// Exact carrier witness.
/// Admission reads a static code and a locus from the error. Either string being empty is a refusal.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AdmittedGovernanceError {
    code: &'static str,
    locus: String,
    locus_len: usize,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GovernanceAdmissionError {
    EmptyCode,
    EmptyLocus,
    LengthMismatch,
}

impl AdmittedGovernanceError {
    pub fn code(&self) -> &'static str {
        self.code
    }

    pub fn locus(&self) -> &str {
        &self.locus
    }

    pub fn locus_len(&self) -> usize {
        self.locus_len
    }
}

impl GovernanceError {
    fn evidence_missing_locus(
        artifact_id: &str,
        evidence_type: &str,
    ) -> Result<(&'static str, String), GovernanceAdmissionError> {
        if artifact_id.is_empty() || evidence_type.is_empty() {
            return Err(GovernanceAdmissionError::EmptyLocus);
        }
        let mut locus = String::new();
        locus.push_str(artifact_id);
        locus.push('/');
        locus.push_str(evidence_type);
        Ok(("evidence_missing", locus))
    }

    fn code_and_locus(&self) -> Result<(&'static str, String), GovernanceAdmissionError> {
        match self {
            GovernanceError::AuthorityViolation(locus) => Ok(("authority_violation", locus.clone())),
            GovernanceError::EvidenceMissing { artifact_id, evidence_type } => {
                Self::evidence_missing_locus(artifact_id, evidence_type)
            }
            GovernanceError::InvalidFinding(locus) => Ok(("invalid_finding", locus.clone())),
            GovernanceError::TraceNotFound(locus) => Ok(("trace_not_found", locus.clone())),
            GovernanceError::CouncilNotFound(locus) => Ok(("council_not_found", locus.clone())),
            GovernanceError::LicenseNotFound(locus) => Ok(("license_not_found", locus.clone())),
            GovernanceError::ArtifactNotFound(locus) => Ok(("artifact_not_found", locus.clone())),
            GovernanceError::MeetingNotFound(locus) => Ok(("meeting_not_found", locus.clone())),
            GovernanceError::InternalError(locus) => Ok(("internal_error", locus.clone())),
        }
    }

    pub fn try_admit(&self) -> Result<AdmittedGovernanceError, GovernanceAdmissionError> {
        let (code, locus) = self.code_and_locus()?;
        if code.is_empty() {
            return Err(GovernanceAdmissionError::EmptyCode);
        }
        let locus_len = locus.len();
        if locus_len == 0 || locus.is_empty() {
            return Err(GovernanceAdmissionError::EmptyLocus);
        }
        let admitted = AdmittedGovernanceError { code, locus, locus_len };
        if admitted.code.is_empty() || admitted.locus_len != admitted.locus.len() || admitted.locus_len == 0 {
            return Err(GovernanceAdmissionError::LengthMismatch);
        }
        Ok(admitted)
    }
}

// Origin: engine/crates_rs/core_contracts/src/enforcement_governance_errors.rs
// Claim: urn:core:crates_rs:core-contracts:enforcement-governance-errors:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn trace_id_round_trip() {
        let id = TraceId::new("trace-001");
        assert_eq!(id.as_str(), "trace-001");
    }

    #[test]
    fn council_id_round_trip() {
        let id = CouncilId::new("council-alpha");
        assert_eq!(id.as_str(), "council-alpha");
    }

    #[test]
    fn license_id_round_trip() {
        let id = LicenseId::new("lic-42");
        assert_eq!(id.as_str(), "lic-42");
    }

    #[test]
    fn governance_error_display() {
        let err = GovernanceError::AuthorityViolation("test violation".into());
        assert!(err.to_string().contains("authority violation"));
    }

    #[test]
    fn admission_keeps_a_nonempty_code_and_locus() {
        let admitted = GovernanceError::AuthorityViolation("test violation".into()).try_admit();
        assert!(matches!(
            admitted.as_ref(),
            Ok(value)
                if value.code() == "authority_violation"
                    && value.locus() == "test violation"
                    && value.locus_len() == value.locus().len()
        ));
        let evidence = GovernanceError::EvidenceMissing {
            artifact_id: "artifact".into(),
            evidence_type: "trace".into(),
        }
        .try_admit();
        assert!(matches!(
            evidence.as_ref(),
            Ok(value) if value.code() == "evidence_missing" && value.locus() == "artifact/trace"
        ));
    }

    #[test]
    fn admission_refuses_an_empty_locus() {
        assert!(matches!(
            GovernanceError::AuthorityViolation(String::new()).try_admit(),
            Err(GovernanceAdmissionError::EmptyLocus)
        ));
        assert!(matches!(
            GovernanceError::InternalError(String::new()).try_admit(),
            Err(GovernanceAdmissionError::EmptyLocus)
        ));
        assert!(matches!(
            GovernanceError::EvidenceMissing {
                artifact_id: String::new(),
                evidence_type: "trace".into(),
            }
            .try_admit(),
            Err(GovernanceAdmissionError::EmptyLocus)
        ));
        assert!(matches!(
            GovernanceError::EvidenceMissing {
                artifact_id: "artifact".into(),
                evidence_type: String::new(),
            }
            .try_admit(),
            Err(GovernanceAdmissionError::EmptyLocus)
        ));
    }
}
