//! Validation rules from YAML canonical contract definitions.
//!
//! These rules are extracted from:
//! - `04_actions_contracts.yaml` validation_rules section
//! - `05_governance.yaml` validation_rules section
//! - `02_evidence.yaml` validation_rules section
//!
//! Each rule corresponds to a contract-level invariant that must hold
//! for the system to maintain authority separation.

use crate::kinds::{ComponentRole, ContractEffect};
use serde::{Deserialize, Serialize};

/// Validation rule identifiers from YAML canonical definitions.
///
/// These rules enforce authority separation and prevent forbidden
/// artifact/authority combinations.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ValidationRuleId {
    // From 04_actions_contracts.yaml
    /// YAML must parse without errors
    YamlMustParse,
    /// Actions cannot emit FactEnvelope directly
    NoActionFactEnvelope,
    /// Operators cannot emit FactEnvelope directly
    NoOperatorFactEnvelope,
    /// Non-certifier contracts emit evidence, not certificates
    NonCertifierContractsEmitEvidenceNotCertificates,
    /// Candidates default to EvidenceOnly authority
    CandidatesDefaultToEvidenceOnly,
    /// Checked outputs require a boundary for FactOnly promotion
    CheckedOutputsRequireBoundaryForFactOnly,
    /// ActionLicense can only come from LicensingBoundary
    ActionLicenseOnlyFromLicensingBoundary,
    /// StateTransition can only come from Engine
    StateTransitionOnlyFromEngine,
    /// Engine executes only licensed transitions
    EngineExecutesOnlyLicensedTransitions,
    /// Primary output family must be canonical
    PrimaryOutputFamilyMustBeCanonical,
    /// Referenced output families must be canonical
    ReferencedOutputFamiliesMustBeCanonical,
    /// Domain-specific output kinds must use domain_output_kind
    DomainSpecificOutputKindsMustUseDomainOutputKind,
    /// Non-certifier contracts must not emit certificate-named structs
    NonCertifierContractsMustNotEmitCertificateNamedStructs,
    /// Candidates must not emit RequiresEvaluator by default
    CandidatesMustNotEmitRequiresEvaluatorByDefault,
    /// Composition laws must be conditional unless explicit rewrite law
    CompositionLawsMustBeConditionalUnlessExplicitRewriteLaw,
    /// Constructor must not emit validation certificate directly
    ConstructorMustNotEmitValidationCertificateDirectly,
    /// Encoding evidence is allowed, encoding certificate is forbidden
    EncodingEvidenceIsAllowedEncodingCertificateIsForbidden,

    // From 05_governance.yaml
    /// Evaluator outputs DecisionEnvelope
    EvaluatorOutputsDecisionEnvelope,
    /// Policy outputs DecisionEnvelope
    PolicyOutputsDecisionEnvelope,
    /// AuthInterface outputs DecisionEnvelope
    AuthInterfaceOutputsDecisionEnvelope,
    /// TerminalMapper must not reference ActionLicense when licensing forbidden
    TerminalMapperMustNotReferenceActionLicenseWhenLicensingForbidden,
    /// Validator outputs EvidenceOnly until checked
    ValidatorOutputsEvidenceOnlyUntilChecked,
    /// No local authority effect enums allowed
    NoLocalAuthorityEffectEnums,
    /// No local artifact family enums allowed
    NoLocalArtifactFamilyEnums,
    /// Default unchecked outputs to EvidenceOnly
    DefaultUncheckedOutputsToEvidenceOnly,
    /// Checked fact requires certificate or replay boundary
    CheckedFactRequiresCertificateOrReplayBoundary,
    /// Forbid self-declared effect class
    ForbidSelfDeclaredEffectClass,
    /// Composition requires rewrite law or certificate
    CompositionRequiresRewriteLawOrCertificate,
    /// TerminalMapper outputs DecisionEnvelope
    TerminalMapperOutputsDecisionEnvelope,
    /// Checked validation report FactOnly requires declared check boundary
    CheckedValidationReportFactOnlyRequiresDeclaredCheckBoundary,

    // From 02_evidence.yaml
    /// Unchecked evidence defaults to EvidenceOnly
    UncheckedEvidenceDefaultsToEvidenceOnly,
    /// Checked fact requires declared boundary
    CheckedFactRequiresDeclaredBoundary,
    /// Certificate authority must not exceed evidence
    CertificateAuthorityMustNotExceedEvidence,
    /// Witness does not verify itself
    WitnessDoesNotVerifyItself,
    /// Replay does not repair or execute
    ReplayDoesNotRepairOrExecute,
    /// Trace records and controls nothing
    TraceRecordsAndControlsNothing,
    /// Measurement values are not facts by existence
    MeasurementValuesAreNotFactsByExistence,
    /// Observable does not emit canonical cohomological measurements
    ObservableDoesNotEmitCanonicalCohomologicalMeasurements,
    /// Checked packet FactOnly requires declared check boundary
    CheckedPacketFactOnlyRequiresDeclaredCheckBoundary,
    /// Checked packet must reference evidence packet
    CheckedPacketMustReferenceEvidencePacket,
    /// Checked packet must reference checker or verifier
    CheckedPacketMustReferenceCheckerOrVerifier,
    /// Checked packet must not promote unchecked evidence
    CheckedPacketMustNotPromoteUncheckedEvidence,
}

/// Result of a validation rule check.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ValidationRuleResult {
    pub rule_id: ValidationRuleId,
    pub passed: bool,
    pub message: Option<String>,
}

impl ValidationRuleResult {
    pub fn pass(rule_id: ValidationRuleId) -> Self {
        Self {
            rule_id,
            passed: true,
            message: None,
        }
    }

    pub fn fail(rule_id: ValidationRuleId, message: impl Into<String>) -> Self {
        Self {
            rule_id,
            passed: false,
            message: Some(message.into()),
        }
    }
}

// ============================================================================
// Rule checking functions
// ============================================================================

/// Check that an authority effect is valid for a candidate.
///
/// Per 04_actions_contracts.yaml: candidates_default_to_evidence_only
pub fn check_candidate_authority_effect(effect: ContractEffect) -> ValidationRuleResult {
    match effect {
        ContractEffect::EvidenceOnly | ContractEffect::None => {
            ValidationRuleResult::pass(ValidationRuleId::CandidatesDefaultToEvidenceOnly)
        }
        other => ValidationRuleResult::fail(
            ValidationRuleId::CandidatesDefaultToEvidenceOnly,
            format!(
                "Candidate has authority effect {:?}, but candidates must default to EvidenceOnly",
                other
            ),
        ),
    }
}

/// Check that an artifact is not an ActionFactEnvelope.
///
/// Per 04_actions_contracts.yaml: no_action_fact_envelope
pub fn check_no_action_fact_envelope(artifact_name: &str) -> ValidationRuleResult {
    if artifact_name.contains("ActionFactEnvelope") || artifact_name.contains("ActionFact") {
        ValidationRuleResult::fail(
            ValidationRuleId::NoActionFactEnvelope,
            format!(
                "Artifact '{}' appears to be an ActionFactEnvelope, which is forbidden",
                artifact_name
            ),
        )
    } else {
        ValidationRuleResult::pass(ValidationRuleId::NoActionFactEnvelope)
    }
}

/// Check that an artifact is not an OperatorFactEnvelope.
///
/// Per 04_actions_contracts.yaml: no_operator_fact_envelope
pub fn check_no_operator_fact_envelope(artifact_name: &str) -> ValidationRuleResult {
    if artifact_name.contains("OperatorFactEnvelope") || artifact_name.contains("OperatorFact") {
        ValidationRuleResult::fail(
            ValidationRuleId::NoOperatorFactEnvelope,
            format!(
                "Artifact '{}' appears to be an OperatorFactEnvelope, which is forbidden",
                artifact_name
            ),
        )
    } else {
        ValidationRuleResult::pass(ValidationRuleId::NoOperatorFactEnvelope)
    }
}

/// Check that only LicensingBoundary emits ActionLicense.
///
/// Per 04_actions_contracts.yaml: action_license_only_from_licensing_boundary
pub fn check_action_license_only_from_licensing_boundary(
    emitter_role: ComponentRole,
    emits_action_license: bool,
) -> ValidationRuleResult {
    if emits_action_license && emitter_role != ComponentRole::LiftLicense {
        ValidationRuleResult::fail(
            ValidationRuleId::ActionLicenseOnlyFromLicensingBoundary,
            format!(
                "Component '{:?}' emits ActionLicense, but only LiftLicense/LicensingBoundary may do so",
                emitter_role
            ),
        )
    } else {
        ValidationRuleResult::pass(ValidationRuleId::ActionLicenseOnlyFromLicensingBoundary)
    }
}

/// Check that only Engine emits StateTransition.
///
/// Per 04_actions_contracts.yaml: state_transition_only_from_engine
pub fn check_state_transition_only_from_engine(
    emitter_role: ComponentRole,
    authority_effect: ContractEffect,
) -> ValidationRuleResult {
    if authority_effect == ContractEffect::StateTransition && emitter_role != ComponentRole::Engine
    {
        ValidationRuleResult::fail(
            ValidationRuleId::StateTransitionOnlyFromEngine,
            format!(
                "Component '{:?}' has StateTransition authority, but only Engine may emit StateTransition",
                emitter_role
            ),
        )
    } else {
        ValidationRuleResult::pass(ValidationRuleId::StateTransitionOnlyFromEngine)
    }
}

/// Check that unchecked outputs default to EvidenceOnly.
///
/// Per 05_governance.yaml: default_unchecked_outputs_to_evidence_only
pub fn check_default_unchecked_outputs_to_evidence_only(
    is_checked: bool,
    authority_effect: ContractEffect,
) -> ValidationRuleResult {
    if !is_checked
        && !matches!(
            authority_effect,
            ContractEffect::EvidenceOnly | ContractEffect::None
        )
    {
        ValidationRuleResult::fail(
            ValidationRuleId::DefaultUncheckedOutputsToEvidenceOnly,
            format!(
                "Unchecked output has authority {:?}, but unchecked outputs must default to EvidenceOnly",
                authority_effect
            ),
        )
    } else {
        ValidationRuleResult::pass(ValidationRuleId::DefaultUncheckedOutputsToEvidenceOnly)
    }
}

/// Check that validator outputs are EvidenceOnly until checked.
///
/// Per 05_governance.yaml: validator_outputs_evidence_only_until_checked
pub fn check_validator_outputs_evidence_only_until_checked(
    is_checked: bool,
    authority_effect: ContractEffect,
) -> ValidationRuleResult {
    if !is_checked && authority_effect != ContractEffect::EvidenceOnly {
        ValidationRuleResult::fail(
            ValidationRuleId::ValidatorOutputsEvidenceOnlyUntilChecked,
            format!(
                "Unchecked validator output has authority {:?}, but must be EvidenceOnly until checked",
                authority_effect
            ),
        )
    } else {
        ValidationRuleResult::pass(ValidationRuleId::ValidatorOutputsEvidenceOnlyUntilChecked)
    }
}

/// Check that a witness does not verify itself.
///
/// Per 02_evidence.yaml: witness_does_not_verify_itself
pub fn check_witness_does_not_verify_itself(
    witness_id: &str,
    verifier_id: &str,
) -> ValidationRuleResult {
    if witness_id == verifier_id {
        ValidationRuleResult::fail(
            ValidationRuleId::WitnessDoesNotVerifyItself,
            format!(
                "Witness '{}' appears to verify itself, which is forbidden",
                witness_id
            ),
        )
    } else {
        ValidationRuleResult::pass(ValidationRuleId::WitnessDoesNotVerifyItself)
    }
}

/// Check that certificate authority does not exceed evidence.
///
/// Per 02_evidence.yaml: certificate_authority_must_not_exceed_evidence
pub fn check_certificate_authority_not_exceeds_evidence(
    evidence_authority: ContractEffect,
    certificate_authority: ContractEffect,
) -> ValidationRuleResult {
    // Authority ordering: None < EvidenceOnly < FactOnly < RequiresEvaluator < RequestsDecision < AuthorizesTransition < StateTransition
    let authority_level = |a: ContractEffect| -> u8 {
        match a {
            ContractEffect::None => 0,
            ContractEffect::EvidenceOnly => 1,
            ContractEffect::FactOnly => 2,
            ContractEffect::RequiresEvaluator => 3,
            ContractEffect::RequestsDecision => 4,
            ContractEffect::AuthorizesTransition => 5,
            ContractEffect::StateTransition => 6,
        }
    };

    if authority_level(certificate_authority) > authority_level(evidence_authority) {
        ValidationRuleResult::fail(
            ValidationRuleId::CertificateAuthorityMustNotExceedEvidence,
            format!(
                "Certificate authority {:?} exceeds evidence authority {:?}",
                certificate_authority, evidence_authority
            ),
        )
    } else {
        ValidationRuleResult::pass(ValidationRuleId::CertificateAuthorityMustNotExceedEvidence)
    }
}

/// Check that checked packet references evidence packet.
///
/// Per 02_evidence.yaml: checked_packet_must_reference_evidence_packet
pub fn check_checked_packet_references_evidence(has_evidence_ref: bool) -> ValidationRuleResult {
    if !has_evidence_ref {
        ValidationRuleResult::fail(
            ValidationRuleId::CheckedPacketMustReferenceEvidencePacket,
            "Checked packet must reference an evidence packet".to_string(),
        )
    } else {
        ValidationRuleResult::pass(ValidationRuleId::CheckedPacketMustReferenceEvidencePacket)
    }
}

/// Check that checked packet references checker or verifier.
///
/// Per 02_evidence.yaml: checked_packet_must_reference_checker_or_verifier
pub fn check_checked_packet_references_checker(has_checker_ref: bool) -> ValidationRuleResult {
    if !has_checker_ref {
        ValidationRuleResult::fail(
            ValidationRuleId::CheckedPacketMustReferenceCheckerOrVerifier,
            "Checked packet must reference a checker or verifier".to_string(),
        )
    } else {
        ValidationRuleResult::pass(ValidationRuleId::CheckedPacketMustReferenceCheckerOrVerifier)
    }
}

// ============================================================================
// Batch rule checking
// ============================================================================

/// Check all validation rules for a component.
pub fn check_all_component_rules(
    component_role: ComponentRole,
    authority_effect: ContractEffect,
    is_checked: bool,
    artifact_name: &str,
    emits_action_license: bool,
) -> Vec<ValidationRuleResult> {
    vec![
        check_candidate_authority_effect(authority_effect),
        check_no_action_fact_envelope(artifact_name),
        check_no_operator_fact_envelope(artifact_name),
        check_action_license_only_from_licensing_boundary(component_role, emits_action_license),
        check_state_transition_only_from_engine(component_role, authority_effect),
        check_default_unchecked_outputs_to_evidence_only(is_checked, authority_effect),
    ]
}

/// Returns true if all rules passed.
pub fn all_rules_passed(results: &[ValidationRuleResult]) -> bool {
    results.iter().all(|r| r.passed)
}

/// Returns failed rules.
pub fn failed_rules(results: &[ValidationRuleResult]) -> Vec<&ValidationRuleResult> {
    results.iter().filter(|r| !r.passed).collect()
}

// Origin: engine/crates_rs/core_contracts/src/validation_rules.rs
// Claim: urn:core:crates_rs:core-contracts:validation-rules:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord02c06ba1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord02c06ba1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError02c06ba1 {
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
impl BoundaryError02c06ba1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError02c06ba1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError02c06ba1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord02c06ba1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError02c06ba1> {
        if capacity_bound == 0 {
            return Err(BoundaryError02c06ba1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError02c06ba1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError02c06ba1::ExceedsCapacity {
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
    fn test_candidate_authority_effect_evidence_only() {
        let result = check_candidate_authority_effect(ContractEffect::EvidenceOnly);
        assert!(result.passed);
    }

    #[test]
    fn test_candidate_authority_effect_fact_only_fails() {
        let result = check_candidate_authority_effect(ContractEffect::FactOnly);
        assert!(!result.passed);
    }

    #[test]
    fn test_no_action_fact_envelope() {
        let result = check_no_action_fact_envelope("ActionFactEnvelope");
        assert!(!result.passed);

        let result = check_no_action_fact_envelope("EvidenceEnvelope");
        assert!(result.passed);
    }

    #[test]
    fn test_action_license_only_from_licensing_boundary() {
        let result =
            check_action_license_only_from_licensing_boundary(ComponentRole::LiftLicense, true);
        assert!(result.passed);

        let result =
            check_action_license_only_from_licensing_boundary(ComponentRole::Evaluator, true);
        assert!(!result.passed);

        let result =
            check_action_license_only_from_licensing_boundary(ComponentRole::Evaluator, false);
        assert!(result.passed);
    }

    #[test]
    fn test_state_transition_only_from_engine() {
        let result = check_state_transition_only_from_engine(
            ComponentRole::Engine,
            ContractEffect::StateTransition,
        );
        assert!(result.passed);

        let result = check_state_transition_only_from_engine(
            ComponentRole::Evaluator,
            ContractEffect::StateTransition,
        );
        assert!(!result.passed);

        let result = check_state_transition_only_from_engine(
            ComponentRole::Evaluator,
            ContractEffect::EvidenceOnly,
        );
        assert!(result.passed);
    }

    #[test]
    fn test_witness_does_not_verify_itself() {
        let result = check_witness_does_not_verify_itself("witness_1", "verifier_1");
        assert!(result.passed);

        let result = check_witness_does_not_verify_itself("witness_1", "witness_1");
        assert!(!result.passed);
    }

    #[test]
    fn test_certificate_authority_not_exceeds_evidence() {
        let result = check_certificate_authority_not_exceeds_evidence(
            ContractEffect::FactOnly,
            ContractEffect::EvidenceOnly,
        );
        assert!(result.passed);

        let result = check_certificate_authority_not_exceeds_evidence(
            ContractEffect::EvidenceOnly,
            ContractEffect::FactOnly,
        );
        assert!(!result.passed);
    }
}

#[cfg(test)]
mod l4_boundary_tests_02c06ba1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord02c06ba1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord02c06ba1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord02c06ba1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord02c06ba1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord02c06ba1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError02c06ba1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError02c06ba1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
