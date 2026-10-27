use serde::{Deserialize, Serialize};

pub use super::authority::{AuthorityEffect, AuthorityLevel};

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct RowId(String);

impl RowId {
    pub fn new(value: impl Into<String>) -> Result<Self, DomainTypeError> {
        let value = value.into();
        if value.trim().is_empty() {
            return Err(DomainTypeError::Empty("row_id"));
        }
        if !value
            .chars()
            .all(|ch| ch.is_ascii_alphanumeric() || matches!(ch, '_' | '.' | ':' | '-'))
        {
            return Err(DomainTypeError::InvalidFormat("row_id"));
        }
        Ok(Self(value))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PolicyId(String);

impl PolicyId {
    pub fn new(value: impl Into<String>) -> Result<Self, DomainTypeError> {
        let value = value.into();
        if value.trim().is_empty() {
            return Err(DomainTypeError::Empty("policy_id"));
        }
        if !value
            .chars()
            .all(|ch| ch.is_ascii_alphanumeric() || matches!(ch, '_' | '.' | ':' | '-'))
        {
            return Err(DomainTypeError::InvalidFormat("policy_id"));
        }
        Ok(Self(value))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct EvidenceRef(String);

impl EvidenceRef {
    pub fn new(value: impl Into<String>) -> Result<Self, DomainTypeError> {
        let value = value.into();
        if value.trim().is_empty() {
            return Err(DomainTypeError::Empty("evidence_ref"));
        }
        Ok(Self(value))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Hash256(String);

impl Hash256 {
    pub fn new(value: impl Into<String>) -> Result<Self, DomainTypeError> {
        let value = value.into();
        if value.len() != 64 || !value.chars().all(|ch| ch.is_ascii_hexdigit()) {
            return Err(DomainTypeError::InvalidFormat("hash256"));
        }
        Ok(Self(value))
    }

    pub fn from_hex_unchecked(value: impl Into<String>) -> Self {
        Self(value.into())
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum DatasetSplit {
    Train,
    Test,
    Unknown,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Sector {
    Bit,
    Cipher,
    Unit,
    Numeral,
    Gravity,
    Symbol,
    Unknown,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PacketFamily {
    Bit,
    Cipher,
    Unit,
    Numeral,
    Gravity,
    Symbol,
    Unknown,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum SolverFamily {
    BitwiseExpr8,
    Bitwise,
    Bit,
    CipherSubstitution,
    Cipher,
    UnitConversion,
    Unit,
    GravityNewton,
    Gravity,
    NumeralBase,
    Numeral,
    RationalReplay,
    Rational,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum SolverEvidenceClass {
    ExactProof,
    UniqueOutput,
    InfeasibleRefusal,
    HeuristicOutput,
    Unknown,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EvaluationVerdict {
    Accept,
    Reject,
    Escalate,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EvaluationReason {
    AcceptedExactRule,
    AcceptedUniqueOutput,
    ExactProofRequiresReplay,
    ReplayFailed,
    EvidenceRequiresDerivedAnswer,
    EvidenceNonUniqueOutput,
    NonExactEvidenceUnsupported,
    SolverInfeasible,
    SolverFailed,
    UnsupportedSolverOutput,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ReplayFailureCode {
    MissingOrInvalidRuleWitness,
    NoExamplesFound,
    ParsingFailed,
    InductionFailed,
    RuleMismatch,
    MissingVerifier,
    StrictComparisonMismatch,
    ExecutionError,
    NoExamples,
    NonFiniteNumber,
    TransportCoherenceFailure,
    DecimalPolicyMismatch,
    RationalNormalizationMismatch,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ClauseCode {
    ExactProofVerified,
    UniqueOutputVerified,
    ExactProofRequiresReplay,
    ReplayFailedReject,
    EvidenceRequiresDerivedAnswer,
    EvidenceNonUnique,
    NonExactEvidenceUnsupported,
    InfeasibleTerminal,
    FailedEscalate,
    UnsupportedOutputType,
    CertifiedReplayTerminalized,
    FallbackTerminalized,
    RefusalTerminalized,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DomainTypeError {
    Empty(&'static str),
    InvalidFormat(&'static str),
}

// Origin: engine/crates_rs/core_types/src/domain_types.rs
// Claim: urn:core:crates_rs:core-types:domain-types:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DomainTypeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DomainTypeError {}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EvaluatorFacts {
    pub phi: f64,
    pub gamma: f64,
    pub refusal_signal: f64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PolicyContext {
    pub request_id: String,
    pub sector: Sector,
    pub user_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PolicyRequest {
    pub context: PolicyContext,
    pub facts: EvaluatorFacts,
    pub requested_at: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MetricPolicyRequest {
    pub request_id: String,
    pub phi: f64,
    pub gamma: f64,
    pub refusal_signal: f64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PolicyMetric {
    Phi,
    Gamma,
    RefusalSignal,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ConstraintKind {
    Hard,
    Soft,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BoundConstraint {
    pub metric: PolicyMetric,
    pub upper_bound: Option<f64>,
    pub lower_bound: Option<f64>,
    pub kind: ConstraintKind,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PolicyDecisionKind {
    Allowed,
    Bounded,
    Forbidden,
    Undetermined,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PolicyDecision {
    pub kind: PolicyDecisionKind,
    pub reason_code: String,
    pub fired_rules: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PolicyDecisionEnvelope {
    pub policy_id: String,
    pub decision: PolicyDecision,
    pub context_hash: String,
    pub evaluated_at: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PolicySet {
    pub set_id: String,
    pub policy_ids: Vec<String>,
    pub resolution_strategy: PolicyResolutionStrategy,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PolicyResolutionStrategy {
    Strict,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ReplayMethod {
    PolicyReplay,
    FullChainReplay,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ResolvedPolicyDecisionEnvelope {
    pub set_id: String,
    pub final_decision: PolicyDecision,
    pub envelopes: Vec<PolicyDecisionEnvelope>,
    pub resolved_at: String,
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{Hash256, PolicyId, RowId};

    #[test]
    fn ids_reject_empty_and_bad_characters() {
        assert!(RowId::new("").is_err());
        assert!(RowId::new("row 1").is_err());
        assert!(RowId::new("row_1:ok").is_ok());
        assert!(PolicyId::new("core.v1").is_ok());
    }

    #[test]
    fn hash256_requires_64_hex_characters() {
        assert!(Hash256::new("abc").is_err());
        assert!(Hash256::new("g".repeat(64)).is_err());
        assert!(Hash256::new("a".repeat(64)).is_ok());
    }
}
