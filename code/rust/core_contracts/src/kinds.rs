use super::sealed::Sealed;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SchemaRef(pub &'static str);

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct SchemaHash(pub [u8; 32]);

impl core::fmt::Display for SchemaHash {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        for byte in self.0 {
            write!(f, "{:02x}", byte)?;
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BaseValidationWitness {
    pub validation_id: &'static str,
    pub schema_hash: SchemaHash,
    pub validator_version: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BaseValidationViolation {
    pub message: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MutabilityMode {
    Immutable,
    Controlled {
        allowed_fields: &'static [&'static str],
    },
}

pub trait BaseType: Sealed {
    fn schema() -> &'static SchemaRef;
    fn validate(&self) -> Result<BaseValidationWitness, BaseValidationViolation>;
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ContractCategory {
    Constitution,
    State,
    Evidence,
    Obstruction,
    Action,
    OperatorCandidate,
    OperatorAlgebra,
    Governance,
    Execution,
    Representation,
    Product,
    Lifts,
    Math,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ComponentRole {
    BaseType,
    Carrier,
    Packet,
    CheckedPacket,
    Certificate,
    CertificateKernel,
    CertificateStore,
    CertificateApiInterface,
    Witness,
    Diagnostic,
    HealthModel,
    Measurement,
    Observable,
    Evaluator,
    Validator,
    Terminalizer,
    TerminalMapper,
    Engine,
    Kernel,
    Pipeline,
    Runtime,
    Policy,
    Search,
    Solver,
    Replay,
    Lift,
    LiftLicense,
    LlmAdapter,
    WebsiteApi,
    SymbolGame,
    Packetization,
    /// Core Structure Sweep product boundary (corpus-scale
    /// structure-correspondence sweep with a deterministic authority rail;
    /// see core/07_products/structure_sweep.contract.yaml).
    StructureSweep,
    ProductKernelIntake,
    FixedLayerOperatorAlgebra,
    DeclaredActionCandidate,
    RepresentationBoundary,
    IntakeConstructor,
    ProposalGenerator,
    Trace,
    AnalysisUnit,
    Boundary,
    AuthInterface,
    MathObject,
    MathComputation,
    PublicVerifyService,
    SearchKernel,
    SolverKernel,
    CounterfeitDetector,
    /// Constitution-layer doctrine (root law, taxonomy, conventions, naming, law hierarchy).
    /// No operational validator — falls through `validate()`'s `_ => {}` catch-all.
    Constitution,
}

/// Contract-policy effect. The v1 YAML spelling remains strict snake_case
/// (`none`, `evidence_only`, ...); PascalCase (`None`) is rejected.
///
/// This type is deliberately named [`ContractEffect`] so the only enum named
/// `AuthorityEffect` in the workspace is the canonical runtime firewall type in
/// `core_types`. Contract transitions describe what a contract permits; they
/// are not authority-bearing artifacts and have no conversion into
/// `core_types::AuthorityEffect` or `CertifiedAuthority`.
///
/// The wire vocabulary remains unchanged for contract compatibility. This enum
/// also does **not** project onto
/// `core_types::authority_lattice::AuthorityEffectLevel`: ranking
/// `AuthorizesTransition`, `StateTransition`, `RequiresEvaluator`, and
/// `RequestsDecision` on that strength chain would itself be an authority
/// decision.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ContractEffect {
    None,
    EvidenceOnly,
    FactOnly,
    RequiresEvaluator,
    RequestsDecision,
    AuthorizesTransition,
    StateTransition,
}

// Origin: engine/crates_rs/core_contracts/src/kinds.rs
// Claim: urn:core:crates_rs:core-contracts:kinds:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod authority_effect_casing_tests {
    use super::ContractEffect;

    #[test]
    fn authority_effect_is_snake_case_strict() {
        let e: ContractEffect = serde_yaml::from_str("none").unwrap();
        assert_eq!(e, ContractEffect::None);
        assert_eq!(
            serde_yaml::from_str::<ContractEffect>("evidence_only").unwrap(),
            ContractEffect::EvidenceOnly
        );
        // strict: PascalCase no longer deserializes
        assert!(serde_yaml::from_str::<ContractEffect>("None").is_err());
    }
}

impl ContractEffect {
    pub const fn is_execution(self) -> bool {
        matches!(self, ContractEffect::StateTransition)
    }

    pub const fn is_license(self) -> bool {
        matches!(self, ContractEffect::AuthorizesTransition)
    }

    pub const fn is_decision(self) -> bool {
        matches!(
            self,
            ContractEffect::RequiresEvaluator | ContractEffect::RequestsDecision
        )
    }

    pub const fn is_evidence_layer(self) -> bool {
        matches!(
            self,
            ContractEffect::None | ContractEffect::EvidenceOnly | ContractEffect::FactOnly
        )
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ArtifactKind {
    StructureArtifact,
    EvidenceEnvelope,
    FactEnvelope,
    DecisionEnvelope,
    ActionLicense,
    Action,
    Record,
    StateEnvelope,
    CandidateEnvelope,
    TerminalEnvelope,
    CheckedTerminalEnvelope,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum Capability {
    CarryLaws,

    // Execution / mutation
    ExecuteStateTransition,
    RuntimeMutation,
    OrchestrateRuntime,
    EmitAction,
    ActionLicensing,
    ApplyLift,
    Repair,

    // Governance / decision
    EmitDecision,
    PolicyInterpretation,
    PolicyDefinition,
    Evaluation,
    Validation,
    AdmissibilityDecision,
    AuthorityPromotion,

    // Evidence / certificate
    EmitCertificate,
    CertificateSigning,
    StoreCertificate,
    SelfCertification,
    TraceWriting,
    RawPayloadExposure,
    PublicSigning,

    // Terminal mapping
    TerminalMapping,
    Terminalization,

    // Solver / search / model
    SolverExecution,
    CandidateGeneration,
    CallLlm,

    // Measurement / functional
    MeasurementComputation,
    ComputePhi,
    ComputeGamma,
    ComputeXi,
    ComputeQuotientMass,
    ComputeClosureDefect,
    ComputeCohomologicalStatus,
    ComputeRefusalSignal,

    // Claims
    SemanticTruthClaim,
}

#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct CapabilityPolicy {
    #[serde(default)]
    pub forbidden: Vec<Capability>,
    #[serde(default)]
    pub required: Vec<Capability>,
}

impl CapabilityPolicy {
    pub fn forbids(&self, capability: Capability) -> bool {
        self.forbidden.contains(&capability)
    }

    pub fn requires(&self, capability: Capability) -> bool {
        self.required.contains(&capability)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct KindDescriptor {
    pub category: ContractCategory,
    pub role: ComponentRole,
    pub authority_effect: ContractEffect,
    pub capability_policy: CapabilityPolicy,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ContractStatus {
    Canonical,
    Staged,
    Archived,
    Deprecated,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn authority_effect_helpers_partition_layers() {
        assert!(ContractEffect::StateTransition.is_execution());
        assert!(!ContractEffect::AuthorizesTransition.is_execution());

        assert!(ContractEffect::AuthorizesTransition.is_license());
        assert!(!ContractEffect::RequestsDecision.is_license());

        assert!(ContractEffect::RequiresEvaluator.is_decision());
        assert!(ContractEffect::RequestsDecision.is_decision());
        assert!(!ContractEffect::FactOnly.is_decision());

        assert!(ContractEffect::None.is_evidence_layer());
        assert!(ContractEffect::EvidenceOnly.is_evidence_layer());
        assert!(ContractEffect::FactOnly.is_evidence_layer());
        assert!(!ContractEffect::StateTransition.is_evidence_layer());
    }

    #[test]
    fn capability_policy_helpers_report_membership() {
        let policy = CapabilityPolicy {
            forbidden: vec![
                Capability::RawPayloadExposure,
                Capability::SelfCertification,
            ],
            required: vec![Capability::ActionLicensing],
        };

        assert!(policy.forbids(Capability::RawPayloadExposure));
        assert!(policy.forbids(Capability::SelfCertification));
        assert!(!policy.forbids(Capability::ComputePhi));
        assert!(policy.requires(Capability::ActionLicensing));
        assert!(!policy.requires(Capability::ExecuteStateTransition));
    }
}
