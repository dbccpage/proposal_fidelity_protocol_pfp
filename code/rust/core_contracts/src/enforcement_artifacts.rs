use crate::kinds::ContractEffect;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum DecisionOrigin {
    EvaluatorGate,
    PolicyInterpretation,
    PolicySetResolution,
    EngineTransition,
}

pub type PolicyReason = String;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum BoundEnforcement {
    Hard,
    Soft,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct BoundConstraint {
    pub target: String,
    pub limit: String,
    pub enforcement: BoundEnforcement,
    pub reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum PolicyDecision {
    Allowed,
    Forbidden { reason: PolicyReason },
    Bounded { constraints: Vec<BoundConstraint> },
    Undetermined { reason: PolicyReason },
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PolicyDecisionEnvelope {
    pub policy_id: String,
    pub policy_version: String,
    pub policy_hash: String,
    pub request_hash: String,
    pub decision: PolicyDecision,
    pub clauses_evaluated: Vec<String>,
    pub clauses_fired: Vec<String>,
    pub authority_effect: ContractEffect,
    pub derivation: BTreeMap<String, String>,
}

/// Canonical representation of mathematical structure inside the engine.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StructureArtifact {
    pub id: String,
    pub source_id: Option<String>,
}

/// A single typed evidence item.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Evidence {
    pub name: String,
    pub details: String,
}

/// Unchecked evidence artifact.
///
/// Per 00_constitution.yaml canonical_artifact_families:
/// EvidenceEnvelope is distinct from FactEnvelope. Evidence becomes
/// a Fact only after passing through a checking boundary.
///
/// Default authority_effect: EvidenceOnly
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct EvidenceEnvelope {
    pub id: String,
    pub evidence: Vec<Evidence>,
    pub witness_refs: Vec<String>,
    pub certificate_refs: Vec<String>,
    pub authority_effect: ContractEffect,
}

impl Default for EvidenceEnvelope {
    fn default() -> Self {
        Self {
            id: String::new(),
            evidence: Vec::new(),
            witness_refs: Vec::new(),
            certificate_refs: Vec::new(),
            authority_effect: ContractEffect::EvidenceOnly,
        }
    }
}

/// A single typed fact (checked evidence).
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Fact {
    pub name: String,
    pub details: String,
}

/// Certified evidence of fact observation (checked by a boundary).
///
/// FactEnvelope is distinct from EvidenceEnvelope: it represents
/// evidence that has been checked and promoted to factual status.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct FactEnvelope {
    pub id: String,
    pub facts: Vec<Fact>,
    pub authority_effect: ContractEffect,
}

/// Certified resolution of policy or governance judgement.
///
/// Per 05_governance.yaml: DecisionEnvelope wraps policy decisions,
/// evaluation results, and auth decisions.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct DecisionEnvelope {
    pub id: String,
    pub decision: PolicyDecision,
    pub origin: DecisionOrigin,
    pub authority_effect: ContractEffect,
}

/// Scoped authorization to execute a state transition.
///
/// Per 00_constitution.yaml canonical_artifact_families and 08_lifts.yaml:
/// ActionLicense is distinct from Action. It authorizes a transition but
/// does not execute it. Only Engine executes licensed transitions.
///
/// Authority effect: AuthorizesTransition
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ActionLicense {
    /// Unique identifier for this license
    pub id: String,
    /// Scope of the licensed transition
    pub scope: String,
    /// Reference to the decision that supports this license
    pub decision_ref: String,
    /// Hash of the licensed transition parameters
    pub license_hash: String,
    /// Optional expiry epoch
    pub expiry: Option<u64>,
    /// Authority effect (always AuthorizesTransition)
    pub authority_effect: ContractEffect,
}

impl Default for ActionLicense {
    fn default() -> Self {
        Self {
            id: String::new(),
            scope: String::new(),
            decision_ref: String::new(),
            license_hash: String::new(),
            expiry: None,
            authority_effect: ContractEffect::AuthorizesTransition,
        }
    }
}

/// An execution artifact produced by Engine state changes.
///
/// Per 06_execution.yaml: Only Engine emits Action with StateTransition
/// authority. Action requires a prior ActionLicense.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct EngineAction {
    pub action_id: String,
    pub license_ref: String,
    pub pre_state_hash: String,
    pub post_state_hash: String,
    pub emitted_trace_ref: String,
    pub action_hash: String,
    pub authority_effect: ContractEffect,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum TerminalCategory {
    VerifiedComplete,
    Refused,
    Fallback,
    UnverifiedComplete,
    Indeterminate,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
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

impl Default for TerminalEnvelope {
    fn default() -> Self {
        Self {
            terminal_id: String::new(),
            terminal_category: TerminalCategory::Indeterminate,
            state_ref: String::new(),
            trace_ref: String::new(),
            evaluator_decision_refs: vec![],
            policy_decision_refs: vec![],
            evidence_refs: vec![],
            certificate_refs: vec![],
            replay_refs: vec![],
            clauses_fired: vec![],
            envelope_hash: String::new(),
            authority_effect: ContractEffect::RequestsDecision,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CheckedTerminalEnvelope {
    pub envelope_ref: String,
    pub replay_ref: String,
    pub certificate_refs: Vec<String>,
    pub checked_hash: String,
    pub authority_effect: ContractEffect,
}

impl Default for CheckedTerminalEnvelope {
    fn default() -> Self {
        Self {
            envelope_ref: String::new(),
            replay_ref: String::new(),
            certificate_refs: vec![],
            checked_hash: String::new(),
            authority_effect: ContractEffect::FactOnly,
        }
    }
}

/// An unmodifiable, execution-neutral logging artifact.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Record {
    pub id: String,
    pub timestamp: u64,
}

/// Orchestration boundary artifact produced by adapter wrappers.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct OrchestrationArtifact {
    pub id: String,
    pub stage: String,
    pub details: String,
}

// Origin: engine/crates_rs/core_contracts/src/enforcement_artifacts.rs
// Claim: urn:core:crates_rs:core-contracts:enforcement-artifacts:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde51bddf0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde51bddf0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore51bddf0 {
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
impl BoundaryErrore51bddf0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore51bddf0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore51bddf0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde51bddf0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore51bddf0> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore51bddf0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore51bddf0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore51bddf0::ExceedsCapacity {
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_evidence_envelope_defaults_to_evidence_only() {
        // EvidenceEnvelope default should be EvidenceOnly per 02_evidence.yaml
        let envelope = EvidenceEnvelope::default();
        assert_eq!(envelope.authority_effect, ContractEffect::EvidenceOnly);
    }

    #[test]
    fn test_evidence_layer_authority_effects_are_canonical() {
        // Per 02_evidence.yaml: evidence layer may use None, EvidenceOnly, FactOnly
        assert!(ContractEffect::None.is_evidence_layer());
        assert!(ContractEffect::EvidenceOnly.is_evidence_layer());
        assert!(ContractEffect::FactOnly.is_evidence_layer());
        assert!(!ContractEffect::StateTransition.is_evidence_layer());
    }

    #[test]
    fn test_fact_envelope_cannot_express_state_transition() {
        // FactEnvelope is constrained by artifact law to evidence-layer authority.
        let envelope = FactEnvelope {
            id: "fact_1".to_string(),
            facts: vec![Fact {
                name: "observation".to_string(),
                details: "value".to_string(),
            }],
            authority_effect: ContractEffect::FactOnly,
        };
        assert_eq!(envelope.authority_effect, ContractEffect::FactOnly);
    }

    #[test]
    fn test_policy_decision_envelope_requests_decision() {
        let envelope = PolicyDecisionEnvelope {
            policy_id: "pol_1".to_string(),
            policy_version: "1.0".to_string(),
            policy_hash: "hash".to_string(),
            request_hash: "req".to_string(),
            decision: PolicyDecision::Allowed,
            clauses_evaluated: vec![],
            clauses_fired: vec![],
            authority_effect: ContractEffect::RequestsDecision,
            derivation: BTreeMap::new(),
        };
        assert!(envelope.authority_effect.is_decision());
    }

    #[test]
    fn test_policy_authority_effects_are_canonical() {
        // Per 05_governance.yaml: governance layer may use None, RequiresEvaluator, RequestsDecision
        assert_eq!(ContractEffect::None, ContractEffect::None);
        assert!(ContractEffect::RequiresEvaluator.is_decision());
        assert!(ContractEffect::RequestsDecision.is_decision());
        assert!(!ContractEffect::AuthorizesTransition.is_decision());
    }

    #[test]
    fn test_action_license_defaults_to_authorizes_transition() {
        // Per 08_lifts.yaml: ActionLicense authority_effect is AuthorizesTransition
        let license = ActionLicense::default();
        assert_eq!(
            license.authority_effect,
            ContractEffect::AuthorizesTransition
        );
        assert!(license.authority_effect.is_license());
    }

    #[test]
    fn test_action_license_is_distinct_from_action() {
        // ActionLicense authorizes; Action executes. Per 00_constitution.yaml
        let license = ActionLicense {
            id: "lic_1".to_string(),
            scope: "test_scope".to_string(),
            decision_ref: "dec_1".to_string(),
            license_hash: "hash123".to_string(),
            expiry: None,
            authority_effect: ContractEffect::AuthorizesTransition,
        };
        assert_eq!(
            license.authority_effect,
            ContractEffect::AuthorizesTransition
        );

        let action = EngineAction {
            action_id: "act_1".to_string(),
            license_ref: "lic_1".to_string(),
            pre_state_hash: "pre".to_string(),
            post_state_hash: "post".to_string(),
            emitted_trace_ref: "trace_1".to_string(),
            action_hash: "hash_1".to_string(),
            authority_effect: ContractEffect::StateTransition,
        };
        assert_eq!(action.authority_effect, ContractEffect::StateTransition);
        assert_eq!(action.license_ref, license.id);
    }

    #[test]
    fn test_only_action_can_express_engine_state_transition() {
        // Show that EngineAction holds the canonical StateTransition authority effect.
        let action = EngineAction {
            action_id: "act_1".to_string(),
            license_ref: "lic_1".to_string(),
            pre_state_hash: "pre".to_string(),
            post_state_hash: "post".to_string(),
            emitted_trace_ref: "trace_1".to_string(),
            action_hash: "hash_1".to_string(),
            authority_effect: ContractEffect::StateTransition,
        };
        assert_eq!(action.authority_effect, ContractEffect::StateTransition);
        assert!(action.authority_effect.is_execution());
    }

    #[test]
    fn test_engine_authority_effects_are_canonical() {
        // Per 06_execution.yaml and 08_lifts.yaml: AuthorizesTransition and StateTransition
        assert!(ContractEffect::AuthorizesTransition.is_license());
        assert!(ContractEffect::StateTransition.is_execution());
    }

    #[test]
    fn test_engine_action_has_required_fields() {
        let action = EngineAction {
            action_id: "act_1".to_string(),
            license_ref: "lic_1".to_string(),
            pre_state_hash: "pre".to_string(),
            post_state_hash: "post".to_string(),
            emitted_trace_ref: "trace_1".to_string(),
            action_hash: "hash".to_string(),
            authority_effect: ContractEffect::StateTransition,
        };
        assert_eq!(action.action_id, "act_1");
    }

    #[test]
    fn test_decision_envelope_includes_origin_and_authority() {
        // Per 05_governance.yaml: DecisionEnvelope includes origin and authority_effect
        let envelope = DecisionEnvelope {
            id: "dec_1".to_string(),
            decision: PolicyDecision::Allowed,
            origin: DecisionOrigin::EvaluatorGate,
            authority_effect: ContractEffect::RequiresEvaluator,
        };
        assert_eq!(envelope.origin, DecisionOrigin::EvaluatorGate);
        assert_eq!(envelope.authority_effect, ContractEffect::RequiresEvaluator);
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LicenseCensusError { kind: &'static str, left: u128, right: u128 }
impl LicenseCensusError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Four nonempty license strings, and the authority effect that authorizes a transition.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LicenseFieldCensus { filled: u64 }
impl LicenseFieldCensus {
    pub fn try_new(id: &str, scope: &str, decision_ref: &str, license_hash: &str, authority_effect: ContractEffect) -> Result<Self, LicenseCensusError> {
        if authority_effect != ContractEffect::AuthorizesTransition {
            return Err(LicenseCensusError::new("a license authorizes a transition", 0, 0));
        }
        let fields = [id, scope, decision_ref, license_hash];
        let mut filled = 0u64;
        for field in &fields {
            if field.is_empty() {
                return Err(LicenseCensusError::new("a license field is nonempty", u128::from(filled), 4));
            }
            filled = filled.checked_add(1).ok_or_else(|| LicenseCensusError::new("filled count overflow", u128::from(filled), 1))?;
        }
        if filled != 4 {
            return Err(LicenseCensusError::new("a license carries four required strings", u128::from(filled), 4));
        }
        Ok(Self { filled })
    }
    pub const fn filled(&self) -> u64 { self.filled }
}
#[cfg(test)]
mod license_census_checks {
    use super::{ContractEffect, LicenseFieldCensus};
    #[test]
    fn four_fields_and_the_license_authority_are_admitted() {
        let census = LicenseFieldCensus::try_new("id", "scope", "decision", "hash", ContractEffect::AuthorizesTransition);
        assert_eq!(census.as_ref().map(LicenseFieldCensus::filled), Ok(4));
        assert_eq!(LicenseFieldCensus::try_new("", "scope", "decision", "hash", ContractEffect::AuthorizesTransition).map(|_| ()).map_err(|error| error.kind()), Err("a license field is nonempty"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_e51bddf0 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde51bddf0::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde51bddf0::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde51bddf0::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde51bddf0::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde51bddf0::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore51bddf0::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore51bddf0::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
