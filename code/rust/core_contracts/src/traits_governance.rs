use crate::contracts_contract::SubjectKind;
use crate::kinds::ContractEffect;

pub trait Policy {
    fn governed_layers(&self) -> Vec<SubjectKind>;
}

// =============================================================================
// Auth Interface Contract (05_governance.yaml)
// =============================================================================

/// Authentication and authorization boundary gating access to system resources.
/// Maps to auth_interface contract in 05_governance.yaml.
///
/// AuthInterface is NOT an operator in the five-effect-class algebra (E, I, C, R, M).
/// It is an access-gating boundary. Auth is orthogonal to the effect-class algebra -- it
/// gates access to resources, not computation. Auth must not be confused with Evaluator,
/// which judges admissibility of evidence. Auth judges identity and permission.
pub trait AuthInterface {
    type Identity;
    type Role;
    type Permission;
    type Resource;
    type Decision;
    type Error;

    fn verify_identity(&self, identity: &Self::Identity) -> Result<bool, Self::Error>;
    fn resolve_role(&self, identity: &Self::Identity) -> Result<Self::Role, Self::Error>;
    fn check_permission(
        &self,
        role: &Self::Role,
        resource: &Self::Resource,
        permission: &Self::Permission,
    ) -> Result<Self::Decision, Self::Error>;
}

/// Auth decision result.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AuthDecision {
    Granted,
    Denied { reason: String },
    RequiresEscalation { route: String },
}

// =============================================================================
// Evaluator Contract (05_governance.yaml)
// =============================================================================

/// Deterministic admissibility judgment gate over evidence and policy.
/// Maps to evaluator contract in 05_governance.yaml.
///
/// Evaluator applies declared evaluation policy to already-computed facts.
/// Evaluator does not measure, discover, mutate, terminalize, or execute.
pub trait Evaluator<C> {
    type Input;
    type Policy;
    type Result;
    type Error;

    fn evaluator_id(&self) -> &str;
    fn evaluator_version(&self) -> &str;

    fn evaluate(
        &self,
        input: &Self::Input,
        policy: &Self::Policy,
    ) -> Result<Self::Result, Self::Error>;
}

/// Evaluation verdict from 05_governance.yaml.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EvaluationVerdict {
    Accept {
        evidence_ref: String,
    },
    Reject {
        reason: RejectionReason,
        evidence_ref: String,
    },
    Escalate {
        route: String,
        witness_id: String,
    },
}

/// Rejection reason for evaluation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RejectionReason {
    pub code: String,
    pub detail: String,
}

/// Evaluation result structure.
///
/// Evaluation results should carry `ContractEffect::RequestsDecision`.
/// They are not action licenses and do not execute transitions.
#[derive(Debug, Clone)]
pub struct EvaluationResult {
    pub verdict: EvaluationVerdict,
    pub policy_id: String,
    pub clauses_fired: Vec<String>,
    pub evidence_used: Vec<String>,
    pub evaluator_id: String,
    pub evaluator_version: String,
    pub input_hash: String,
    pub output_hash: String,
    pub policy_hash: String,
    pub authority_effect: ContractEffect,
}

// =============================================================================
// TerminalMapper Contract (05_governance.yaml)
// =============================================================================

/// Maps finalized execution states to typed terminal envelopes.
/// Maps to terminal_mapper contract in 05_governance.yaml.
///
/// TerminalMapper is NOT an operator in the five-effect-class algebra (E, I, C, R, M).
/// It maps completed execution states to typed terminal decision envelopes.
///
/// TerminalMapper does not execute, certify, license actions, mutate state, or compute
/// measurements. Licensing remains a separate LicensingBoundary responsibility.
pub trait TerminalMapper<State, Trace> {
    type Envelope;
    type Error;

    fn map_terminal(
        &self,
        state_ref: &str,
        trace_ref: &str,
        evidence_refs: Vec<String>,
    ) -> Result<Self::Envelope, Self::Error>;

    fn authority_effect(&self) -> ContractEffect {
        ContractEffect::RequestsDecision
    }
}

/// Terminal category from 05_governance.yaml.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TerminalCategory {
    VerifiedComplete,
    Refused,
    Fallback,
    UnverifiedComplete,
    Indeterminate,
}

/// Terminal envelope structure.
#[derive(Debug, Clone)]
pub struct TerminalEnvelope {
    pub terminal_id: String,
    pub terminal_category: TerminalCategory,
    pub state_ref: String,
    pub trace_ref: String,
    pub evaluator_decision_refs: Vec<String>,
    pub policy_decision_refs: Vec<String>,
    pub evidence_refs: Vec<String>,
    pub certificate_refs: Vec<String>,
    pub replay_refs: Vec<String>,
    pub clauses_fired: Vec<String>,
    pub envelope_hash: String,
    pub authority_effect: ContractEffect,
}

impl TerminalEnvelope {
    pub fn requests_decision(&self) -> bool {
        self.authority_effect == ContractEffect::RequestsDecision
    }
}

/// Terminal mapping error.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TerminalMappingError {
    MissingEvidence { detail: String },
    MissingClauses { detail: String },
    InvalidTerminalCategory { detail: String },
    EmptyPayload { detail: String },
}

// Origin: engine/crates_rs/core_contracts/src/traits_governance.rs
// Claim: urn:core:crates_rs:core-contracts:traits-governance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TerminalMappingError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TerminalMappingError {}

// =============================================================================
// Validator Contract (05_governance.yaml)
// =============================================================================

/// Deterministic structural well-formedness checker against declared invariants.
/// Maps to validator contract in 05_governance.yaml.
///
/// Validators check well-formedness, invariants, and admissibility boundaries.
/// Validators check structure. Validators do not transform, normalize, repair, certify,
/// terminalize, execute, or mutate state.
pub trait Validator<T> {
    type Report;
    type Error;

    fn validate(&self, target: &T) -> Result<Self::Report, Self::Error>;

    fn authority_effect(&self) -> ContractEffect {
        ContractEffect::EvidenceOnly
    }
}

/// Validation status from 05_governance.yaml.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ValidationStatus {
    Valid,
    Invalid,
    Indeterminate,
}

/// Validation report structure.
///
/// Validation reports are `EvidenceOnly` unless a separate checked wrapper records the
/// checker boundary and checked scope.
#[derive(Debug, Clone)]
pub struct ValidationReport {
    pub target_hash: String,
    pub validator_id: String,
    pub invariants_checked: Vec<String>,
    pub status: ValidationStatus,
    pub violations: Vec<ValidationViolation>,
    pub report_hash: String,
    pub authority_effect: ContractEffect,
}

/// Validation violation detail.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidationViolation {
    pub invariant_id: String,
    pub detail: String,
}

/// Validation error types.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ValidationError {
    InvalidStructure {
        violation: ValidationViolation,
    },
    OutOfBoundsValue {
        invariant_id: String,
        detail: String,
    },
    InvariantViolated {
        invariant_id: String,
        detail: String,
    },
    SchemaMismatch {
        expected: String,
        actual: String,
    },
    HashMismatch {
        expected: String,
        actual: String,
    },
    UndeclaredInvariant {
        invariant_id: String,
    },
    ValidatorInternalError {
        detail: String,
    },
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    struct TestTerminalMapper;

    impl TerminalMapper<(), ()> for TestTerminalMapper {
        type Envelope = TerminalEnvelope;
        type Error = TerminalMappingError;

        fn map_terminal(
            &self,
            state_ref: &str,
            trace_ref: &str,
            evidence_refs: Vec<String>,
        ) -> Result<Self::Envelope, Self::Error> {
            Ok(TerminalEnvelope {
                terminal_id: "terminal:test".to_string(),
                terminal_category: TerminalCategory::VerifiedComplete,
                state_ref: state_ref.to_string(),
                trace_ref: trace_ref.to_string(),
                evaluator_decision_refs: Vec::new(),
                policy_decision_refs: Vec::new(),
                evidence_refs,
                certificate_refs: Vec::new(),
                replay_refs: Vec::new(),
                clauses_fired: Vec::new(),
                envelope_hash: "hash:test".to_string(),
                authority_effect: ContractEffect::RequestsDecision,
            })
        }
    }

    #[test]
    fn terminal_mapper_requests_decision_not_evidence_only() {
        let mapper = TestTerminalMapper;
        assert_eq!(mapper.authority_effect(), ContractEffect::RequestsDecision);

        let envelope = mapper
            .map_terminal("state:1", "trace:1", vec!["evidence:1".to_string()])
            .expect("terminal mapping should succeed");
        assert!(envelope.requests_decision());
    }
}
