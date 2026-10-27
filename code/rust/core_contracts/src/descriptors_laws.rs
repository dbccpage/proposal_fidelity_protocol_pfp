use crate::binding::BoundContract;

// ─── Markers ──────────────────────────────────────────────────────────────────
pub trait RequiredLaw {}
pub trait ForbiddenLaw {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Required;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Forbidden;

impl RequiredLaw for Required {}
impl ForbiddenLaw for Forbidden {}

// ─── Authority Markers ────────────────────────────────────────────────────────
pub trait AuthorityEffectLaw {}

pub struct EffectNone;
pub struct EffectEvidenceOnly;
pub struct EffectFactOnly;
pub struct EffectRequiresEvaluator;
pub struct EffectRequestsDecision;
pub struct EffectAuthorizesTransition;
pub struct EffectStateTransition;

impl AuthorityEffectLaw for EffectNone {}
impl AuthorityEffectLaw for EffectEvidenceOnly {}
impl AuthorityEffectLaw for EffectFactOnly {}
impl AuthorityEffectLaw for EffectRequiresEvaluator {}
impl AuthorityEffectLaw for EffectRequestsDecision {}
impl AuthorityEffectLaw for EffectAuthorizesTransition {}
impl AuthorityEffectLaw for EffectStateTransition {}

// ─── Artifact Family Markers ──────────────────────────────────────────────────
pub trait ArtifactFamilyLaw {}

pub struct StructureArtifactFamily;
pub struct EvidenceEnvelopeFamily;
pub struct FactEnvelopeFamily;
pub struct DecisionEnvelopeFamily;
pub struct ActionLicenseFamily;
pub struct ActionFamily;
pub struct RecordFamily;

impl ArtifactFamilyLaw for StructureArtifactFamily {}
impl ArtifactFamilyLaw for EvidenceEnvelopeFamily {}
impl ArtifactFamilyLaw for FactEnvelopeFamily {}
impl ArtifactFamilyLaw for DecisionEnvelopeFamily {}
impl ArtifactFamilyLaw for ActionLicenseFamily {}
impl ArtifactFamilyLaw for ActionFamily {}
impl ArtifactFamilyLaw for RecordFamily {}

// ─── Axis ────────────────────────────────────────────────────────────────────
pub trait StructureLaw {}
pub trait EffectLaw {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Preserving;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Reductive;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Transforming;

impl StructureLaw for Preserving {}
impl StructureLaw for Reductive {}
impl StructureLaw for Transforming {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Pure;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ReadOnly;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Stateful;

impl EffectLaw for Pure {}
impl EffectLaw for ReadOnly {}
impl EffectLaw for Stateful {}

// ─── Strict Contract Base ────────────────────────────────────────────────────
pub trait StrictContractLaw: BoundContract {
    type Authority: AuthorityEffectLaw;
    type PrimaryFamily: ArtifactFamilyLaw;
}

pub trait StrictEvidenceOnlyContract:
    StrictContractLaw<Authority = EffectEvidenceOnly, PrimaryFamily = EvidenceEnvelopeFamily>
{
}

pub trait StrictDecisionContract:
    StrictContractLaw<Authority = EffectRequestsDecision, PrimaryFamily = DecisionEnvelopeFamily>
{
}

pub trait StrictActionLicenseContract:
    StrictContractLaw<Authority = EffectAuthorizesTransition, PrimaryFamily = ActionLicenseFamily>
{
}

pub trait StrictEngineActionContract:
    StrictContractLaw<Authority = EffectStateTransition, PrimaryFamily = ActionFamily>
{
}

pub trait StrictStructureArtifactContract:
    StrictContractLaw<Authority = EffectNone, PrimaryFamily = StructureArtifactFamily>
{
}

pub trait StrictStateStructureContract:
    StrictContractLaw<Authority = EffectEvidenceOnly, PrimaryFamily = StructureArtifactFamily>
{
}

// ─── Operator & Candidate Contracts ──────────────────────────────────────────
pub trait StrictLambdaContract: BoundContract {
    type Structure: StructureLaw;
    type Effect: EffectLaw;
    type MeasurementAccess: ForbiddenLaw;
    type EmitsActionLicense: ForbiddenLaw;
    type Executes: ForbiddenLaw;
}

pub trait StrictReducerContract: BoundContract {
    type Structure: StructureLaw;
    type Effect: EffectLaw;

    const IDEMPOTENT: bool;
}

pub trait StrictTransformContract: BoundContract {
    type Structure: StructureLaw;
    type Effect: EffectLaw;
}

pub trait StrictValidatorContract:
    StrictContractLaw<Authority = EffectEvidenceOnly, PrimaryFamily = EvidenceEnvelopeFamily>
{
    type StructuralCheckingOnly: RequiredLaw;
    type Certification: ForbiddenLaw;
    type Evaluation: ForbiddenLaw;
    type Execution: ForbiddenLaw;
    type Mutation: ForbiddenLaw;
    type TraceWriting: ForbiddenLaw;
}

pub trait StrictLLMAdapterContract:
    StrictContractLaw<Authority = EffectEvidenceOnly, PrimaryFamily = EvidenceEnvelopeFamily>
{
    type CandidateOnly: RequiredLaw;
    type Certification: ForbiddenLaw;
    type Validation: ForbiddenLaw;
    type Evaluation: ForbiddenLaw;
    type OperatorClassification: ForbiddenLaw;
    type ActionLicensing: ForbiddenLaw;
    type Execution: ForbiddenLaw;
}

pub trait StrictPacketizationContract:
    StrictContractLaw<Authority = EffectEvidenceOnly, PrimaryFamily = EvidenceEnvelopeFamily>
{
    type RoundtripWitness: RequiredLaw;
    type SemanticValidation: ForbiddenLaw;
    type Certification: ForbiddenLaw;
    type Evaluation: ForbiddenLaw;
    type Execution: ForbiddenLaw;
}

pub trait StrictLiftLicenseContract:
    StrictContractLaw<Authority = EffectAuthorizesTransition, PrimaryFamily = ActionLicenseFamily>
{
    type AuthorityDoesNotExceedEvidence: RequiredLaw;
    type ScopeBound: RequiredLaw;
    type NonTransferable: RequiredLaw;
    type ReplayManifest: RequiredLaw;
    type Execution: ForbiddenLaw;
    type Mutation: ForbiddenLaw;
    type SelfCertification: ForbiddenLaw;
}

// ─── Observer Contracts ──────────────────────────────────────────────────────
pub trait StrictMetaContract: BoundContract {
    type Effect: EffectLaw;

    const STATELESS: bool;
    const OPERATOR_EXECUTION_FORBIDDEN: bool;
    const RUNTIME_ORCHESTRATION_FORBIDDEN: bool;
}

pub trait StrictValidationContract: BoundContract {
    type Effect: EffectLaw;

    const READ_ONLY: bool;
    const MUTATION_FORBIDDEN: bool;
    const TYPED_OUTPUT_REQUIRED: bool;
}

// ─── Algebra Contracts ───────────────────────────────────────────────────────
pub trait StrictAlgebraContract: BoundContract {
    const DECLARATIVE_ONLY: bool;
    const NO_EXECUTION: bool;
    const NO_HIDDEN_STATE: bool;
    const NO_RUNTIME_DEPENDENCY: bool;
}

// ─── Product Authority Law Contracts ──────────────────────────────────────────
pub trait StrictPolicyContract: BoundContract {
    type MetricComputation: ForbiddenLaw;
    type SolverExecution: ForbiddenLaw;
    type Terminalization: ForbiddenLaw;
    type Mutation: ForbiddenLaw;
    type Determinism: RequiredLaw;
}

pub trait StrictWitnessContract:
    StrictContractLaw<Authority = EffectEvidenceOnly, PrimaryFamily = EvidenceEnvelopeFamily>
{
    type SelfVerification: ForbiddenLaw;
    type Certification: ForbiddenLaw;
    type AdmissibilityDecision: ForbiddenLaw;
    type Mutation: ForbiddenLaw;
    type SourceArtifacts: RequiredLaw;
}

pub trait StrictCertificateKernelContract:
    StrictContractLaw<Authority = EffectEvidenceOnly, PrimaryFamily = EvidenceEnvelopeFamily>
{
    type EvidenceRefs: RequiredLaw;
    type VerifierCapability: RequiredLaw;
    type AuthorityDoesNotExceedEvidence: RequiredLaw;
    type SelfCertification: ForbiddenLaw;
    type Execution: ForbiddenLaw;
    type Mutation: ForbiddenLaw;
}

pub trait StrictReplayContract:
    StrictContractLaw<Authority = EffectEvidenceOnly, PrimaryFamily = EvidenceEnvelopeFamily>
{
    type ReadOnly: RequiredLaw;
    type Mutation: ForbiddenLaw;
    type Repair: ForbiddenLaw;
    type Execution: ForbiddenLaw;
    type ReplayManifest: RequiredLaw;
}

pub trait StrictTerminalMapperContract:
    StrictContractLaw<Authority = EffectRequestsDecision, PrimaryFamily = DecisionEnvelopeFamily>
{
    type Certification: ForbiddenLaw;
    type Evaluation: ForbiddenLaw;
    type PolicyDefinition: ForbiddenLaw;
    type MeasurementComputation: ForbiddenLaw;
    type Execution: ForbiddenLaw;
    type Mutation: ForbiddenLaw;
    type ActionLicensing: ForbiddenLaw;
}

pub trait StrictPublicVerifyContract: BoundContract {
    type ReadOnly: RequiredLaw;
    type Signing: ForbiddenLaw;
    type Mutation: ForbiddenLaw;
    type RawPayload: ForbiddenLaw;
}

pub trait StrictTraceContract:
    StrictContractLaw<Authority = EffectEvidenceOnly, PrimaryFamily = EvidenceEnvelopeFamily>
{
    type ImmutableAfterEmit: RequiredLaw;
    type Mutation: ForbiddenLaw;
    type Certification: ForbiddenLaw;
    type PolicyInterpretation: ForbiddenLaw;
    type Execution: ForbiddenLaw;
}

pub trait StrictSearchContract:
    StrictContractLaw<Authority = EffectEvidenceOnly, PrimaryFamily = EvidenceEnvelopeFamily>
{
    type CandidateGenerationOnly: RequiredLaw;
    type MeasurementComputation: ForbiddenLaw;
    type Evaluation: ForbiddenLaw;
    type Certification: ForbiddenLaw;
    type ActionLicensing: ForbiddenLaw;
    type Execution: ForbiddenLaw;
}

pub trait StrictMathStructureContract: BoundContract {
    type Effect: EffectLaw;
    type EmitsDecision: ForbiddenLaw;
    type EmitsCertificate: ForbiddenLaw;
    type EmitsAction: ForbiddenLaw;
    type CustomerClaim: ForbiddenLaw;
}

pub trait StrictMathComputationContract: BoundContract {
    type Effect: EffectLaw;
    type EmitsDecision: ForbiddenLaw;
    type EmitsCertificate: ForbiddenLaw;
    type EmitsAction: ForbiddenLaw;
    type CustomerClaim: ForbiddenLaw;
}

// ─── Assertions ──────────────────────────────────────────────────────────────
pub trait SameLaw<T> {}

impl<T> SameLaw<T> for T {}

pub fn assert_lambda_laws<C>()
where
    C: StrictLambdaContract<
        Structure = Preserving,
        Effect = Pure,
        MeasurementAccess = Forbidden,
        EmitsActionLicense = Forbidden,
        Executes = Forbidden,
    >,
{
}

pub fn assert_reducer_laws<C>()
where
    C: StrictReducerContract<Structure = Reductive, Effect = Pure>,
{
}

pub fn assert_transform_laws<C>()
where
    C: StrictTransformContract<Structure = Transforming, Effect = Pure>,
{
}

pub fn assert_meta_laws<C>()
where
    C: StrictMetaContract<Effect = ReadOnly>,
{
}

pub fn assert_validation_laws<C>()
where
    C: StrictValidationContract<Effect = ReadOnly>,
{
}

pub fn assert_policy_laws<C>()
where
    C: StrictPolicyContract<
        MetricComputation = Forbidden,
        SolverExecution = Forbidden,
        Terminalization = Forbidden,
        Mutation = Forbidden,
        Determinism = Required,
    >,
{
}

pub fn assert_witness_laws<C>()
where
    C: StrictWitnessContract<
        SelfVerification = Forbidden,
        Certification = Forbidden,
        AdmissibilityDecision = Forbidden,
        Mutation = Forbidden,
        SourceArtifacts = Required,
    >,
{
}

pub fn assert_certificate_kernel_laws<C>()
where
    C: StrictCertificateKernelContract<
        EvidenceRefs = Required,
        VerifierCapability = Required,
        AuthorityDoesNotExceedEvidence = Required,
        SelfCertification = Forbidden,
        Execution = Forbidden,
        Mutation = Forbidden,
    >,
{
}

pub fn assert_replay_laws<C>()
where
    C: StrictReplayContract<
        ReadOnly = Required,
        Mutation = Forbidden,
        Repair = Forbidden,
        Execution = Forbidden,
        ReplayManifest = Required,
    >,
{
}

pub fn assert_terminal_mapper_laws<C>()
where
    C: StrictTerminalMapperContract<
        Certification = Forbidden,
        Evaluation = Forbidden,
        PolicyDefinition = Forbidden,
        MeasurementComputation = Forbidden,
        Execution = Forbidden,
        Mutation = Forbidden,
        ActionLicensing = Forbidden,
    >,
{
}

pub fn assert_public_verify_laws<C>()
where
    C: StrictPublicVerifyContract<
        ReadOnly = Required,
        Signing = Forbidden,
        Mutation = Forbidden,
        RawPayload = Forbidden,
    >,
{
}

pub fn assert_structure_artifact_laws<C>()
where
    C: StrictStructureArtifactContract,
{
}

pub fn assert_state_structure_laws<C>()
where
    C: StrictStateStructureContract,
{
}

pub fn assert_trace_laws<C>()
where
    C: StrictTraceContract<
        ImmutableAfterEmit = Required,
        Mutation = Forbidden,
        Certification = Forbidden,
        PolicyInterpretation = Forbidden,
        Execution = Forbidden,
    >,
{
}

pub fn assert_search_laws<C>()
where
    C: StrictSearchContract<
        CandidateGenerationOnly = Required,
        MeasurementComputation = Forbidden,
        Evaluation = Forbidden,
        Certification = Forbidden,
        ActionLicensing = Forbidden,
        Execution = Forbidden,
    >,
{
}

pub fn assert_lift_license_laws<C>()
where
    C: StrictLiftLicenseContract<
        AuthorityDoesNotExceedEvidence = Required,
        ScopeBound = Required,
        NonTransferable = Required,
        ReplayManifest = Required,
        Execution = Forbidden,
        Mutation = Forbidden,
        SelfCertification = Forbidden,
    >,
{
}

pub fn assert_validator_laws<C>()
where
    C: StrictValidatorContract<
        StructuralCheckingOnly = Required,
        Certification = Forbidden,
        Evaluation = Forbidden,
        Execution = Forbidden,
        Mutation = Forbidden,
        TraceWriting = Forbidden,
    >,
{
}

pub fn assert_llm_adapter_laws<C>()
where
    C: StrictLLMAdapterContract<
        CandidateOnly = Required,
        Certification = Forbidden,
        Validation = Forbidden,
        Evaluation = Forbidden,
        OperatorClassification = Forbidden,
        ActionLicensing = Forbidden,
        Execution = Forbidden,
    >,
{
}

pub fn assert_packetization_laws<C>()
where
    C: StrictPacketizationContract<
        RoundtripWitness = Required,
        SemanticValidation = Forbidden,
        Certification = Forbidden,
        Evaluation = Forbidden,
        Execution = Forbidden,
    >,
{
}

pub fn assert_math_structure_laws<C>()
where
    C: StrictMathStructureContract<
        Effect = Pure,
        EmitsDecision = Forbidden,
        EmitsCertificate = Forbidden,
        EmitsAction = Forbidden,
        CustomerClaim = Forbidden,
    >,
{
}

pub fn assert_math_computation_laws<C>()
where
    C: StrictMathComputationContract<
        Effect = Pure,
        EmitsDecision = Forbidden,
        EmitsCertificate = Forbidden,
        EmitsAction = Forbidden,
        CustomerClaim = Forbidden,
    >,
{
}

// Origin: engine/crates_rs/core_contracts/src/descriptors_laws.rs
// Claim: urn:core:crates_rs:core-contracts:descriptors-laws:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3bc80dae {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3bc80dae` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3bc80dae {
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
impl BoundaryError3bc80dae {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3bc80dae {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3bc80dae {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3bc80dae {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3bc80dae> {
        if capacity_bound == 0 {
            return Err(BoundaryError3bc80dae::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3bc80dae::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3bc80dae::ExceedsCapacity {
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
    use crate::binding::{
        ContractDescriptor as BindingContractDescriptor, GeneratedContractImage, LawBinding,
        TypeBinding,
    };
    use crate::kinds::{
        ComponentRole, ContractCategory, ContractEffect, ContractStatus, SchemaHash,
    };

    struct MockPolicyContract;
    impl crate::sealed::Sealed for MockPolicyContract {}

    static MOCK_POLICY_DESCRIPTOR: BindingContractDescriptor = BindingContractDescriptor {
        id: "mock_policy_contract",
        category: ContractCategory::Governance,
        role: ComponentRole::Policy,
        status: ContractStatus::Canonical,
        authority_effect: ContractEffect::RequestsDecision,
        phi_law: LawBinding::Forbidden,
        structure_law: LawBinding::Forbidden,
        effect_law: LawBinding::Forbidden,
        input_type: TypeBinding::Forbidden,
        output_type: TypeBinding::Forbidden,
        subject_type: TypeBinding::Forbidden,
        runtime_state_type: TypeBinding::Forbidden,
        evidence_requirements: &[],
        forbidden_authority: &[],
        schema_hash: SchemaHash([1; 32]),
    };

    impl GeneratedContractImage for MockPolicyContract {
        const DESCRIPTOR: &'static BindingContractDescriptor = &MOCK_POLICY_DESCRIPTOR;
    }

    impl BoundContract for MockPolicyContract {
        type Input = ();
        type Output = ();
        type Subject = ();
        type RuntimeState = ();
    }

    impl StrictPolicyContract for MockPolicyContract {
        type MetricComputation = Forbidden;
        type SolverExecution = Forbidden;
        type Terminalization = Forbidden;
        type Mutation = Forbidden;
        type Determinism = Required;
    }

    struct MockCertificateContract;
    impl crate::sealed::Sealed for MockCertificateContract {}

    static MOCK_CERT_DESCRIPTOR: BindingContractDescriptor = BindingContractDescriptor {
        id: "mock_certificate_kernel_contract",
        category: ContractCategory::Evidence,
        role: ComponentRole::CertificateKernel,
        status: ContractStatus::Canonical,
        authority_effect: ContractEffect::EvidenceOnly,
        phi_law: LawBinding::Forbidden,
        structure_law: LawBinding::Forbidden,
        effect_law: LawBinding::Forbidden,
        input_type: TypeBinding::Forbidden,
        output_type: TypeBinding::Forbidden,
        subject_type: TypeBinding::Forbidden,
        runtime_state_type: TypeBinding::Forbidden,
        evidence_requirements: &[],
        forbidden_authority: &[],
        schema_hash: SchemaHash([2; 32]),
    };

    impl GeneratedContractImage for MockCertificateContract {
        const DESCRIPTOR: &'static BindingContractDescriptor = &MOCK_CERT_DESCRIPTOR;
    }

    impl BoundContract for MockCertificateContract {
        type Input = ();
        type Output = ();
        type Subject = ();
        type RuntimeState = ();
    }

    impl StrictContractLaw for MockCertificateContract {
        type Authority = EffectEvidenceOnly;
        type PrimaryFamily = EvidenceEnvelopeFamily;
    }

    impl StrictCertificateKernelContract for MockCertificateContract {
        type EvidenceRefs = Required;
        type VerifierCapability = Required;
        type AuthorityDoesNotExceedEvidence = Required;
        type SelfCertification = Forbidden;
        type Execution = Forbidden;
        type Mutation = Forbidden;
    }

    #[test]
    fn test_assert_policy_laws_compiles() {
        assert_policy_laws::<MockPolicyContract>();
    }

    #[test]
    fn test_assert_certificate_kernel_laws_compiles() {
        assert_certificate_kernel_laws::<MockCertificateContract>();
    }
}

#[cfg(test)]
mod l4_boundary_tests_3bc80dae {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3bc80dae::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3bc80dae::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3bc80dae::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3bc80dae::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3bc80dae::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3bc80dae::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3bc80dae::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
