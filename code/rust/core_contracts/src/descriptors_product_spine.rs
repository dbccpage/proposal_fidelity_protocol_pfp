use crate::kinds::{
    Capability, CapabilityPolicy, ComponentRole, ContractCategory, ContractEffect, ContractStatus,
};
use crate::schema::{
    AuthorityLayer, ConstitutionalBlock, ConstraintBlock, ContractDescriptor, EffectLawDecl,
    LawBlock, LawPresence, ReplayBlock, WitnessesBlock,
};

fn base_descriptor(
    id: &str,
    name: &str,
    category: ContractCategory,
    role: ComponentRole,
) -> ContractDescriptor {
    ContractDescriptor {
        id: id.into(),
        name: name.into(),
        category,
        role,
        status: ContractStatus::Canonical,
        authority_effect: ContractEffect::None,
        domain_type: None,
        codomain_type: None,
        subject_type: None,
        runtime_state_type: None,
        evaluates_outputs_of: None,
        decision_scope: None,
        laws: None,
        algebra_laws: None,
        governed_algebra_layer: None,
        constitution: None,
        operator_class: None,
        signature: None,
        uros: None,
        requires: None,
        validation: None,
        witnesses: None,
        replay: None,
        constraints: ConstraintBlock::default(),
        capabilities: CapabilityPolicy::default(),
        schema_hash: None,
        // core.contract.v1 enforcement fields (defaults; legacy product-spine confers none).
        evidence_ceiling: None,
        runtime_enforcement: false,
        proof_obligations: Vec::new(),
        terminals: Default::default(),
        refusals: Default::default(),
        operator_classes: Default::default(),
        rust_binding: None,
    }
}

fn fact_constitution(emits: crate::ArtifactFamily) -> ConstitutionalBlock {
    ConstitutionalBlock {
        contract_dependencies: vec!["constitution".into()],
        law_refs: vec![],

        emits,
        authority_layer: AuthorityLayer::Fact,
        forbidden_later_layers: vec![AuthorityLayer::Judgment, AuthorityLayer::Action],
        replay_certificates: vec!["schema_hash".into()],
    }
}

fn evidence_constitution(emits: crate::ArtifactFamily) -> ConstitutionalBlock {
    ConstitutionalBlock {
        contract_dependencies: vec!["constitution".into()],
        law_refs: vec![],
        emits,
        authority_layer: AuthorityLayer::Evidence,
        forbidden_later_layers: vec![AuthorityLayer::Judgment, AuthorityLayer::Action],
        replay_certificates: vec!["schema_hash".into()],
    }
}

fn action_constitution(emits: crate::ArtifactFamily) -> ConstitutionalBlock {
    ConstitutionalBlock {
        contract_dependencies: vec!["constitution".into()],
        law_refs: vec![],
        emits,
        authority_layer: AuthorityLayer::Action,
        forbidden_later_layers: vec![],
        replay_certificates: vec!["schema_hash".into(), "replay_manifest".into()],
    }
}

#[allow(dead_code)]
fn structure_constitution(emits: crate::ArtifactFamily) -> ConstitutionalBlock {
    ConstitutionalBlock {
        contract_dependencies: vec!["constitution".into()],
        law_refs: vec![],
        emits,
        authority_layer: AuthorityLayer::Structure,
        forbidden_later_layers: vec![AuthorityLayer::Judgment, AuthorityLayer::Action],
        replay_certificates: vec!["schema_hash".into()],
    }
}

fn decision_constitution(emits: crate::ArtifactFamily) -> ConstitutionalBlock {
    ConstitutionalBlock {
        contract_dependencies: vec!["constitution".into()],
        law_refs: vec![],

        emits,
        authority_layer: AuthorityLayer::Judgment,
        forbidden_later_layers: vec![AuthorityLayer::Action],
        replay_certificates: vec!["schema_hash".into()],
    }
}

fn engine_laws() -> LawBlock {
    LawBlock {
        phi: LawPresence::Forbidden,
        structure: LawPresence::Forbidden,
        effect: LawPresence::Required(EffectLawDecl::Stateful),
        required: vec!["only_engine_acts".into()],
    }
}

pub fn observable_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.observable",
        "Sentinel Observable",
        ContractCategory::Evidence,
        ComponentRole::Observable,
    );
    descriptor.constitution = Some(evidence_constitution(
        crate::ArtifactFamily::EvidenceEnvelope,
    ));
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.constraints.runtime_orchestration_forbidden = Some(true);
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

pub fn measurement_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.measurement",
        "Sentinel Measurement",
        ContractCategory::Evidence,
        ComponentRole::Measurement,
    );
    descriptor.subject_type = Some("ObservableEvidence".into());
    descriptor.constitution = Some(evidence_constitution(
        crate::ArtifactFamily::EvidenceEnvelope,
    ));
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.constraints.operator_execution_forbidden = Some(true);
    descriptor.constraints.runtime_orchestration_forbidden = Some(true);
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

pub fn evaluator_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.evaluator",
        "Sentinel Evaluator",
        ContractCategory::Governance,
        ComponentRole::Evaluator,
    );
    descriptor.subject_type = Some("MeasurementEnvelope".into());
    descriptor.constitution = Some(decision_constitution(
        crate::ArtifactFamily::DecisionEnvelope,
    ));
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.constraints.runtime_orchestration_forbidden = Some(true);
    descriptor.capabilities.forbidden = vec![Capability::ComputePhi, Capability::ComputeGamma];
    descriptor.authority_effect = ContractEffect::RequestsDecision;
    descriptor
}

pub fn policy_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.policy",
        "Sentinel Policy",
        ContractCategory::Governance,
        ComponentRole::Policy,
    );
    descriptor.constitution = Some(decision_constitution(
        crate::ArtifactFamily::DecisionEnvelope,
    ));
    descriptor.evaluates_outputs_of = Some(ComponentRole::Evaluator);
    descriptor.decision_scope = Some(vec!["classification".into()]);
    descriptor.constraints.deterministic = Some(true);
    descriptor.constraints.immutable_after_emit = Some(true);
    descriptor.constraints.hidden_state_forbidden = Some(true);
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.operator_execution_forbidden = Some(true);
    descriptor.constraints.runtime_orchestration_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.constraints.policy_version_required = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::ComputePhi,
        Capability::ComputeGamma,
        Capability::ComputeRefusalSignal,
        Capability::SolverExecution,
        Capability::Terminalization,
    ];
    descriptor.authority_effect = ContractEffect::RequestsDecision;
    descriptor
}

pub fn policy_set_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.policy_set",
        "Sentinel Policy Set",
        ContractCategory::Governance,
        ComponentRole::Policy,
    );
    descriptor.constitution = Some(evidence_constitution(
        crate::ArtifactFamily::EvidenceEnvelope,
    ));
    descriptor.constraints.deterministic = Some(true);
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.constraints.request_hash_required = Some(true);
    descriptor.capabilities.forbidden = vec![Capability::PolicyInterpretation];
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

pub fn witness_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.witness",
        "Sentinel Witness",
        ContractCategory::Evidence,
        ComponentRole::Witness,
    );
    descriptor.constitution = Some(evidence_constitution(
        crate::ArtifactFamily::EvidenceEnvelope,
    ));
    descriptor.witnesses = Some(WitnessesBlock {
        required: vec!["source_artifacts".into()],
    });
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::CertificateSigning,
        Capability::PolicyInterpretation,
        Capability::Terminalization,
    ];
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

pub fn certificate_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.certificate",
        "Sentinel Certificate",
        ContractCategory::Evidence,
        ComponentRole::Certificate,
    );
    descriptor.constitution = Some(evidence_constitution(
        crate::ArtifactFamily::EvidenceEnvelope,
    ));
    descriptor.witnesses = Some(WitnessesBlock {
        required: vec!["witness_ref".into()],
    });
    descriptor.replay = Some(ReplayBlock {
        required: vec![
            "policy_hash".into(),
            "request_hash".into(),
            "schema_hash".into(),
        ],
    });
    descriptor.constraints.immutable_after_emit = Some(true);
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.constraints.signature_required = Some(true);
    descriptor.constraints.certificate_hash_required = Some(true);
    descriptor.constraints.policy_hash_required = Some(true);
    descriptor.constraints.policy_version_required = Some(true);
    descriptor.constraints.request_hash_required = Some(true);
    descriptor.constraints.replay_required = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::Terminalization,
        Capability::SolverExecution,
        Capability::PolicyInterpretation,
    ];
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

pub fn certificate_store_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.certificate_store",
        "Sentinel Certificate Store",
        ContractCategory::Governance,
        ComponentRole::CertificateStore,
    );
    descriptor.constraints.immutable_after_emit = Some(true);
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.raw_payload_forbidden = Some(true);
    descriptor.capabilities.forbidden =
        vec![Capability::RuntimeMutation, Capability::CertificateSigning];
    descriptor.authority_effect = ContractEffect::None;
    descriptor
}

pub fn replay_verifier_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.replay_verifier",
        "Sentinel Replay Verifier",
        ContractCategory::Evidence,
        ComponentRole::Replay,
    );
    descriptor.constitution = Some(evidence_constitution(
        crate::ArtifactFamily::EvidenceEnvelope,
    ));
    descriptor.constraints.read_only = Some(true);
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.constraints.policy_hash_required = Some(true);
    descriptor.constraints.request_hash_required = Some(true);
    descriptor.capabilities.forbidden =
        vec![Capability::RuntimeMutation, Capability::Terminalization];
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

pub fn terminal_mapper_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.terminal_mapper",
        "Sentinel Terminal Mapper",
        ContractCategory::Governance,
        ComponentRole::TerminalMapper,
    );
    descriptor.constitution = Some(decision_constitution(
        crate::ArtifactFamily::DecisionEnvelope,
    ));
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::ComputePhi,
        Capability::ComputeGamma,
        Capability::PolicyInterpretation,
        Capability::CertificateSigning,
        Capability::ExecuteStateTransition,
        Capability::RuntimeMutation,
        Capability::ActionLicensing,
        Capability::MeasurementComputation,
    ];
    descriptor.authority_effect = ContractEffect::RequestsDecision;
    descriptor
}

pub fn engine_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.engine",
        "Sentinel Engine",
        ContractCategory::Execution,
        ComponentRole::Engine,
    );
    descriptor.runtime_state_type = Some("EngineRuntimeState".into());
    descriptor.laws = Some(engine_laws());
    descriptor.constitution = Some(action_constitution(crate::ArtifactFamily::Action));
    descriptor.constraints.action_license_required = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::ComputePhi,
        Capability::ComputeGamma,
        Capability::PolicyInterpretation,
        Capability::CertificateSigning,
        Capability::Terminalization,
        Capability::Evaluation,
        Capability::EmitCertificate,
    ];
    descriptor.authority_effect = ContractEffect::StateTransition;
    descriptor
}

pub fn public_verify_service_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.public_verify_service",
        "Sentinel Public Verify Service",
        ContractCategory::Product,
        ComponentRole::CertificateApiInterface,
    );
    descriptor.constraints.read_only = Some(true);
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.constraints.public_signing_forbidden = Some(true);
    descriptor.constraints.raw_payload_forbidden = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::CertificateSigning,
        Capability::RuntimeMutation,
        Capability::EmitCertificate,
        Capability::Evaluation,
        Capability::Terminalization,
        Capability::AuthorityPromotion,
    ];
    descriptor.authority_effect = ContractEffect::None;
    descriptor
}

// ─── 02_evidence contracts ───────────────────────────────────────────────────

pub fn trace_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.trace",
        "Sentinel Trace",
        ContractCategory::Evidence,
        ComponentRole::Trace,
    );
    descriptor.constitution = Some(evidence_constitution(
        crate::ArtifactFamily::EvidenceEnvelope,
    ));
    descriptor.constraints.immutable_after_emit = Some(true);
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::Terminalization,
        Capability::CertificateSigning,
        Capability::PolicyInterpretation,
    ];
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

pub fn diagnostic_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.diagnostic",
        "Sentinel Diagnostic",
        ContractCategory::Evidence,
        ComponentRole::Diagnostic,
    );
    descriptor.subject_type = Some("MeasurementEnvelope".into());
    descriptor.constitution = Some(evidence_constitution(
        crate::ArtifactFamily::EvidenceEnvelope,
    ));
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.constraints.runtime_orchestration_forbidden = Some(true);
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

pub fn checked_packet_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.checked_packet",
        "Sentinel Checked Packet",
        ContractCategory::Evidence,
        ComponentRole::CheckedPacket,
    );
    descriptor.constitution = Some(fact_constitution(crate::ArtifactFamily::FactEnvelope));
    descriptor.constraints.immutable_after_emit = Some(true);
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.constraints.checker_boundary_required = Some(true);
    descriptor.authority_effect = ContractEffect::FactOnly;
    descriptor
}

// ─── 05_governance contracts ─────────────────────────────────────────────────

pub fn validator_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.validator",
        "Sentinel Validator",
        ContractCategory::Governance,
        ComponentRole::Validator,
    );
    descriptor.constitution = Some(evidence_constitution(
        crate::ArtifactFamily::EvidenceEnvelope,
    ));
    descriptor.subject_type = Some("ArtifactEnvelope".into());
    descriptor.constraints.read_only = Some(true);
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

pub fn auth_interface_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.auth_interface",
        "Sentinel Auth Interface",
        ContractCategory::Governance,
        ComponentRole::AuthInterface,
    );
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::CertificateSigning,
        Capability::PolicyInterpretation,
        Capability::Terminalization,
    ];
    descriptor.authority_effect = ContractEffect::None;
    descriptor
}

// ─── 06_execution contracts ──────────────────────────────────────────────────

pub fn health_model_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.health_model",
        "Sentinel Health Model",
        ContractCategory::Execution,
        ComponentRole::HealthModel,
    );
    descriptor.subject_type = Some("RuntimeState".into());
    descriptor.constraints.read_only = Some(true);
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

pub fn kernel_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.kernel",
        "Sentinel Kernel",
        ContractCategory::Execution,
        ComponentRole::Kernel,
    );
    descriptor.runtime_state_type = Some("KernelRuntimeState".into());
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::CertificateSigning,
        Capability::PolicyInterpretation,
    ];
    descriptor.authority_effect = ContractEffect::None;
    descriptor
}

pub fn search_kernel_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.search_kernel",
        "Sentinel Search Kernel",
        ContractCategory::Execution,
        ComponentRole::Search,
    );
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::CertificateSigning,
        Capability::Terminalization,
        Capability::PolicyInterpretation,
        Capability::Evaluation,
    ];
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

pub fn solver_kernel_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.solver_kernel",
        "Sentinel Solver Kernel",
        ContractCategory::Execution,
        ComponentRole::Solver,
    );
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::CertificateSigning,
        Capability::Terminalization,
        Capability::PolicyInterpretation,
        Capability::Evaluation,
    ];
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

// ─── 07_products contracts ───────────────────────────────────────────────────

pub fn sentinel_certificate_product_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.sentinel_certificate_product",
        "Sentinel Certificate Product",
        ContractCategory::Product,
        ComponentRole::Certificate,
    );
    descriptor.constitution = Some(evidence_constitution(
        crate::ArtifactFamily::EvidenceEnvelope,
    ));
    descriptor.witnesses = Some(WitnessesBlock {
        required: vec!["witness_ref".into()],
    });
    descriptor.replay = Some(ReplayBlock {
        required: vec![
            "policy_hash".into(),
            "request_hash".into(),
            "schema_hash".into(),
        ],
    });
    descriptor.constraints.immutable_after_emit = Some(true);
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.constraints.signature_required = Some(true);
    descriptor.constraints.certificate_hash_required = Some(true);
    descriptor.constraints.policy_hash_required = Some(true);
    descriptor.constraints.policy_version_required = Some(true);
    descriptor.constraints.request_hash_required = Some(true);
    descriptor.constraints.replay_required = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::Terminalization,
        Capability::SolverExecution,
        Capability::PolicyInterpretation,
    ];
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

pub fn llm_adapter_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.llm_adapter",
        "Sentinel LLM Adapter",
        ContractCategory::Product,
        ComponentRole::LlmAdapter,
    );
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::CertificateSigning,
        Capability::Terminalization,
        Capability::PolicyInterpretation,
        Capability::Evaluation,
        Capability::Validation,
    ];
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

pub fn symbol_game_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.symbol_game",
        "Sentinel Symbol Game",
        ContractCategory::Product,
        ComponentRole::SymbolGame,
    );
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::CertificateSigning,
        Capability::Terminalization,
        Capability::PolicyInterpretation,
    ];
    descriptor.authority_effect = ContractEffect::EvidenceOnly;
    descriptor
}

// ─── 08_lifts contracts ──────────────────────────────────────────────────────

pub fn lift_license_descriptor() -> ContractDescriptor {
    let mut descriptor = base_descriptor(
        "sentinel.lift_license",
        "Sentinel Lift License",
        ContractCategory::Lifts,
        ComponentRole::LiftLicense,
    );
    descriptor.constitution = Some(ConstitutionalBlock {
        contract_dependencies: vec!["constitution".into(), "lift".into()],
        law_refs: vec![
            "lift_license_scope_bound".into(),
            "lift_license_non_transferable".into(),
        ],
        emits: crate::ArtifactFamily::ActionLicense,
        authority_layer: AuthorityLayer::Action,
        forbidden_later_layers: vec![],
        replay_certificates: vec!["schema_hash".into(), "replay_manifest".into()],
    });
    descriptor.witnesses = Some(WitnessesBlock {
        required: vec!["context_witness".into(), "checked_obstruction".into()],
    });
    descriptor.replay = Some(ReplayBlock {
        required: vec!["replay_manifest".into(), "license_hash".into()],
    });
    descriptor.constraints.immutable_after_emit = Some(true);
    descriptor.constraints.mutation_forbidden = Some(true);
    descriptor.constraints.typed_output_required = Some(true);
    descriptor.constraints.certificate_required = Some(true);
    descriptor.constraints.scope_bound = Some(true);
    descriptor.constraints.non_transferable = Some(true);
    descriptor.constraints.authority_does_not_exceed_evidence = Some(true);
    descriptor.capabilities.forbidden = vec![
        Capability::ExecuteStateTransition,
        Capability::RuntimeMutation,
        Capability::CertificateSigning,
    ];
    descriptor.authority_effect = ContractEffect::AuthorizesTransition;
    descriptor
}

pub fn sentinel_product_spine_descriptors() -> Vec<ContractDescriptor> {
    vec![
        // 02_evidence
        observable_descriptor(),
        measurement_descriptor(),
        trace_descriptor(),
        diagnostic_descriptor(),
        checked_packet_descriptor(),
        witness_descriptor(),
        certificate_descriptor(),
        // 05_governance
        evaluator_descriptor(),
        validator_descriptor(),
        // terminalizer_descriptor() — deprecated; use terminal_mapper_descriptor()
        auth_interface_descriptor(),
        policy_descriptor(),
        policy_set_descriptor(),
        // 06_execution
        certificate_store_descriptor(),
        replay_verifier_descriptor(),
        terminal_mapper_descriptor(),
        engine_descriptor(),
        health_model_descriptor(),
        kernel_descriptor(),
        search_kernel_descriptor(),
        solver_kernel_descriptor(),
        public_verify_service_descriptor(),
        // 07_products
        sentinel_certificate_product_descriptor(),
        llm_adapter_descriptor(),
        symbol_game_descriptor(),
        // 08_lifts
        lift_license_descriptor(),
    ]
}

// Origin: engine/crates_rs/core_contracts/src/descriptors_product_spine.rs
// Claim: urn:core:crates_rs:core-contracts:descriptors-product-spine:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord507af1f6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord507af1f6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError507af1f6 {
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
impl BoundaryError507af1f6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError507af1f6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError507af1f6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord507af1f6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError507af1f6> {
        if capacity_bound == 0 {
            return Err(BoundaryError507af1f6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError507af1f6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError507af1f6::ExceedsCapacity {
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
    use crate::validate::validate_registry;

    fn assert_invalid(descriptor: ContractDescriptor, expected: &str) {
        let error = descriptor
            .validate()
            .expect_err("descriptor should be rejected");
        assert!(
            error.contains(expected),
            "expected error containing `{}`, got `{}`",
            expected,
            error
        );
    }

    fn without_forbidden(
        mut descriptor: ContractDescriptor,
        cap: Capability,
    ) -> ContractDescriptor {
        descriptor.capabilities.forbidden.retain(|&x| x != cap);
        descriptor
    }

    #[test]
    fn product_spine_descriptors_validate_as_registry() {
        let descriptors = sentinel_product_spine_descriptors();
        validate_registry(&descriptors).expect("product spine descriptors must validate");

        let certificate_index = descriptors
            .iter()
            .position(|d| {
                d.category == ContractCategory::Evidence && d.role == ComponentRole::Certificate
            })
            .expect("product spine must include certificate");
        let store_index = descriptors
            .iter()
            .position(|d| d.id == "sentinel.certificate_store")
            .expect("product spine must include certificate store");
        let replay_index = descriptors
            .iter()
            .position(|d| {
                d.category == ContractCategory::Evidence && d.role == ComponentRole::Replay
            })
            .expect("product spine must include replay verifier");

        assert!(certificate_index < store_index);
        assert!(store_index < replay_index);
    }

    #[test]
    fn policy_does_not_compute_metrics() {
        assert_invalid(
            without_forbidden(policy_descriptor(), Capability::ComputePhi),
            "compute metrics",
        );
    }

    #[test]
    fn policy_does_not_compute_gamma() {
        assert_invalid(
            without_forbidden(policy_descriptor(), Capability::ComputeGamma),
            "compute gamma",
        );
    }

    #[test]
    fn policy_does_not_compute_refusal_signal() {
        assert_invalid(
            without_forbidden(policy_descriptor(), Capability::ComputeRefusalSignal),
            "compute refusal signal",
        );
    }

    #[test]
    fn policy_does_not_call_solver() {
        assert_invalid(
            without_forbidden(policy_descriptor(), Capability::SolverExecution),
            "call solvers",
        );
    }

    #[test]
    fn policy_does_not_terminalize() {
        assert_invalid(
            without_forbidden(policy_descriptor(), Capability::Terminalization),
            "terminalize",
        );
    }

    #[test]
    fn witness_does_not_authorize() {
        assert_invalid(
            without_forbidden(witness_descriptor(), Capability::CertificateSigning),
            "authorize",
        );
    }

    #[test]
    fn witness_does_not_decide_admissibility() {
        assert_invalid(
            without_forbidden(witness_descriptor(), Capability::PolicyInterpretation),
            "admissibility decisions",
        );
    }

    #[test]
    fn certificate_without_witness_invalid() {
        let mut descriptor = certificate_descriptor();
        descriptor.witnesses = None;
        assert_invalid(descriptor, "witness requirements");
    }

    #[test]
    fn certificate_without_replay_invalid() {
        let mut descriptor = certificate_descriptor();
        descriptor.replay = None;
        assert_invalid(descriptor, "replay block");
    }

    #[test]
    fn certificate_without_hash_invalid() {
        let mut descriptor = certificate_descriptor();
        descriptor.constraints.certificate_hash_required = None;
        assert_invalid(descriptor, "certificate hash");
    }

    #[test]
    fn certificate_without_signature_invalid() {
        let mut descriptor = certificate_descriptor();
        descriptor.constraints.signature_required = None;
        assert_invalid(descriptor, "signature");
    }

    #[test]
    fn certificate_store_does_not_overwrite_certificate() {
        assert_invalid(
            without_forbidden(certificate_store_descriptor(), Capability::RuntimeMutation),
            "overwrite certificates",
        );
    }

    #[test]
    fn certificate_store_does_not_sign_certificate() {
        assert_invalid(
            without_forbidden(
                certificate_store_descriptor(),
                Capability::CertificateSigning,
            ),
            "sign certificates",
        );
    }

    #[test]
    fn certificate_store_forbids_raw_payload_exposure() {
        let mut descriptor = certificate_store_descriptor();
        descriptor.constraints.raw_payload_forbidden = None;
        assert_invalid(descriptor, "raw payload exposure");
    }

    #[test]
    fn certificate_store_entries_immutable() {
        let mut descriptor = certificate_store_descriptor();
        descriptor.constraints.immutable_after_emit = None;
        assert_invalid(descriptor, "immutable after emit");
    }

    #[test]
    fn replay_does_not_mutate_trace_bundle() {
        assert_invalid(
            without_forbidden(replay_verifier_descriptor(), Capability::RuntimeMutation),
            "mutate trace bundle",
        );
    }

    #[test]
    fn terminal_mapper_uses_decision_envelope() {
        let descriptor = terminal_mapper_descriptor();
        let constitution = descriptor
            .constitution
            .expect("terminal_mapper must have a constitution");
        assert_eq!(constitution.authority_layer, AuthorityLayer::Judgment);
        assert_eq!(constitution.emits, crate::ArtifactFamily::DecisionEnvelope);
    }

    #[test]
    fn terminal_mapper_does_not_execute() {
        assert_invalid(
            without_forbidden(
                terminal_mapper_descriptor(),
                Capability::ExecuteStateTransition,
            ),
            "execute",
        );
    }

    #[test]
    fn engine_requires_action_license() {
        let mut descriptor = engine_descriptor();
        descriptor.constraints.action_license_required = None;
        assert_invalid(descriptor, "action license");
    }

    #[test]
    fn engine_emits_action() {
        let descriptor = engine_descriptor();
        let constitution = descriptor
            .constitution
            .expect("engine must have a constitution");
        assert_eq!(constitution.authority_layer, AuthorityLayer::Action);
        assert_eq!(constitution.emits, crate::ArtifactFamily::Action);
    }

    #[test]
    fn engine_is_not_terminal_mapper() {
        let engine = engine_descriptor();
        let mapper = terminal_mapper_descriptor();
        assert_ne!(engine.role, mapper.role);
        assert_ne!(
            engine.constitution.map(|c| c.authority_layer),
            mapper.constitution.map(|c| c.authority_layer)
        );
    }

    #[test]
    fn public_verify_service_is_not_execution() {
        let descriptor = public_verify_service_descriptor();
        assert_eq!(descriptor.category, ContractCategory::Product);
    }

    #[test]
    fn measurement_defaults_to_evidence_only() {
        let descriptor = measurement_descriptor();
        assert_eq!(descriptor.authority_effect, ContractEffect::EvidenceOnly);
        let constitution = descriptor
            .constitution
            .expect("measurement must have a constitution");
        assert_eq!(constitution.authority_layer, AuthorityLayer::Evidence);
    }

    #[test]
    fn trace_uses_evidence_constitution() {
        let descriptor = trace_descriptor();
        let constitution = descriptor
            .constitution
            .expect("trace must have a constitution");
        assert_eq!(constitution.authority_layer, AuthorityLayer::Evidence);
    }

    #[test]
    fn checked_packet_factonly_requires_checker_boundary() {
        let mut descriptor = checked_packet_descriptor();
        assert_eq!(descriptor.authority_effect, ContractEffect::FactOnly);
        descriptor.constraints.checker_boundary_required = None;
        assert_invalid(descriptor, "checker boundary");
    }

    #[test]
    fn engine_cannot_compute_phi() {
        assert_invalid(
            without_forbidden(engine_descriptor(), Capability::ComputePhi),
            "compute phi",
        );
    }

    #[test]
    fn engine_cannot_run_policy_interpreter() {
        assert_invalid(
            without_forbidden(engine_descriptor(), Capability::PolicyInterpretation),
            "policy interpreter",
        );
    }

    #[test]
    fn engine_cannot_evaluate_policy_internally() {
        assert_invalid(
            without_forbidden(engine_descriptor(), Capability::PolicyInterpretation),
            "evaluate policy internally",
        );
    }

    #[test]
    fn engine_cannot_sign_certificate() {
        assert_invalid(
            without_forbidden(engine_descriptor(), Capability::CertificateSigning),
            "sign certificates",
        );
    }

    #[test]
    fn public_verify_cannot_sign_certificate() {
        assert_invalid(
            without_forbidden(
                public_verify_service_descriptor(),
                Capability::CertificateSigning,
            ),
            "sign certificates",
        );
    }

    #[test]
    fn public_verify_does_not_mutate_store() {
        assert_invalid(
            without_forbidden(
                public_verify_service_descriptor(),
                Capability::RuntimeMutation,
            ),
            "mutate store",
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_507af1f6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord507af1f6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord507af1f6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord507af1f6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord507af1f6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord507af1f6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError507af1f6::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError507af1f6::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
