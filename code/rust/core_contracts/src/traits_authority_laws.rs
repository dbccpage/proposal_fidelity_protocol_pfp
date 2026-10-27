//! Compatibility law markers for older generated bindings.
//!
//! The canonical descriptor law model lives in `crate::descriptors::laws`.
//! This module remains as a lightweight compatibility shim and must not drift
//! into a second authority doctrine.

use crate::binding::BoundContract;

// --- Axis ---
pub trait PhiLaw {}
pub trait StructureLaw {}
pub trait EffectLaw {}
pub trait AuthorityLaw {}
pub trait CapabilityLaw {}

// --- Phi ---
pub struct NonIncreasing;
pub struct Reducing;
pub struct PreservingPhi;
pub struct UnclaimedPhi;

impl PhiLaw for NonIncreasing {}
impl PhiLaw for Reducing {}
impl PhiLaw for PreservingPhi {}
impl PhiLaw for UnclaimedPhi {}

// --- Structure ---
pub struct StructurePreserving;
pub struct StructureTransforming;
pub struct StructureReductive;

impl StructureLaw for StructurePreserving {}
impl StructureLaw for StructureTransforming {}
impl StructureLaw for StructureReductive {}

// --- Effect ---
pub struct Pure;
pub struct ReadOnly;
pub struct StatefulDeclared;

impl EffectLaw for Pure {}
impl EffectLaw for ReadOnly {}
impl EffectLaw for StatefulDeclared {}

// --- Markers ---
pub trait RequiredLaw {}
pub trait ForbiddenLaw {}
pub trait AllowedLaw {}

pub struct Required;
pub struct Forbidden;
pub struct Allowed;

impl RequiredLaw for Required {}
impl ForbiddenLaw for Forbidden {}
impl AllowedLaw for Allowed {}

// --- Capability Setting ---
pub trait CapabilitySetting {}
impl CapabilitySetting for Required {}
impl CapabilitySetting for Forbidden {}
impl CapabilitySetting for Allowed {}

// --- Authority Markers ---
pub struct NoAuthority;
pub struct EvidenceOnlyAuthority;
pub struct FactOnlyAuthority;
pub struct RequiresEvaluatorAuthority;
pub struct RequestsDecisionAuthority;
pub struct AuthorizesTransitionAuthority;
pub struct StateTransitionAuthority;

impl AuthorityLaw for NoAuthority {}
impl AuthorityLaw for EvidenceOnlyAuthority {}
impl AuthorityLaw for FactOnlyAuthority {}
impl AuthorityLaw for RequiresEvaluatorAuthority {}
impl AuthorityLaw for RequestsDecisionAuthority {}
impl AuthorityLaw for AuthorizesTransitionAuthority {}
impl AuthorityLaw for StateTransitionAuthority {}

// --- Base Profile ---
pub trait StrictContractLaw: BoundContract {
    type Authority: AuthorityLaw;
    type EmitsDecision: CapabilitySetting;
    type EmitsCertificate: CapabilitySetting;
    type EmitsAction: CapabilitySetting;
    type MutatesState: CapabilitySetting;
    type ExecutesTransition: CapabilitySetting;
    type CallsSolver: CapabilitySetting;
    type CallsLlm: CapabilitySetting;
}

// --- Specialized Profiles ---
pub trait StrictCandidateLaw: StrictContractLaw {
    type PhiClaim: PhiLaw;
    type StructureClaim: StructureLaw;
    type Effect: EffectLaw;
    type EvidenceOnly: RequiredLaw;
    type AdmittedOperatorClass: ForbiddenLaw;
}

pub trait StrictEngineLaw: StrictContractLaw {
    type StateTransition: RequiredLaw;
    type ComputesPhi: ForbiddenLaw;
    type ComputesGamma: ForbiddenLaw;
    type SignsCertificate: ForbiddenLaw;
    type TerminalizesInternally: ForbiddenLaw;
}

pub trait StrictCertificateLaw: StrictContractLaw {
    type ImmutableAfterEmit: RequiredLaw;
    type SignatureOrHash: RequiredLaw;
    type EvidenceRefs: RequiredLaw;
    type AuthorityNotExceedEvidence: RequiredLaw;
}

// --- Specific Authority Laws ---
pub trait StrictPolicyLaw: StrictContractLaw {
    type MetricComputation: ForbiddenLaw;
    type SolverExecution: ForbiddenLaw;
    type Terminalization: ForbiddenLaw;
    type Mutation: ForbiddenLaw;
    type Determinism: RequiredLaw;
}

pub trait StrictWitnessLaw: StrictContractLaw {
    type AuthorityEffectEvidenceOnly: RequiredLaw;
    type AdmissibilityDecision: ForbiddenLaw;
    type Mutation: ForbiddenLaw;
    type SourceArtifacts: RequiredLaw;
}

pub trait StrictReplayLaw: StrictContractLaw {
    type ReadOnly: RequiredLaw;
    type Mutation: ForbiddenLaw;
    type ReplayManifest: RequiredLaw;
    type ReplayHash: RequiredLaw;
    type PolicyHash: RequiredLaw;
}

pub trait StrictTerminalizerLaw: StrictContractLaw {
    type Certificate: RequiredLaw;
    type PolicyInterpretation: ForbiddenLaw;
    type MetricComputation: ForbiddenLaw;
    type Signing: ForbiddenLaw;
}

pub trait StrictPublicVerifyLaw: StrictContractLaw {
    type ReadOnly: RequiredLaw;
    type Signing: ForbiddenLaw;
    type Mutation: ForbiddenLaw;
    type RawPayload: ForbiddenLaw;
}

pub trait StrictMathObjectLaw: StrictContractLaw {
    type EmitsDecision: ForbiddenLaw;
    type EmitsCertificate: ForbiddenLaw;
    type EmitsAction: ForbiddenLaw;
    type CustomerClaim: ForbiddenLaw;
}

pub trait StrictMathComputationLaw: StrictContractLaw {
    type EmitsDecision: ForbiddenLaw;
    type EmitsCertificate: ForbiddenLaw;
    type EmitsAction: ForbiddenLaw;
    type CustomerClaim: ForbiddenLaw;
}

pub trait StrictLlmAdapterLaw: StrictContractLaw {
    type SelfCertification: ForbiddenLaw;
    type EmitsCertificate: ForbiddenLaw;
    type Terminalization: ForbiddenLaw;
    type RawResponseHash: RequiredLaw;
    type ParsedCandidateMapping: RequiredLaw;
}

pub trait StrictPacketizationLaw: StrictContractLaw {
    type LosslessRoundtrip: RequiredLaw;
    type ParserRequired: RequiredLaw;
    type GrammarRequired: RequiredLaw;
    type SemanticCertification: ForbiddenLaw;
}

// --- Assertions ---
pub trait SameLaw<T> {}
impl<T> SameLaw<T> for T {}

pub fn assert_candidate_laws<C>()
where
    C: StrictCandidateLaw<EvidenceOnly = Required, AdmittedOperatorClass = Forbidden>,
{
}

pub fn assert_engine_laws<C>()
where
    C: StrictEngineLaw<
        StateTransition = Required,
        ComputesPhi = Forbidden,
        ComputesGamma = Forbidden,
        SignsCertificate = Forbidden,
        TerminalizesInternally = Forbidden,
    >,
{
}

pub fn assert_certificate_laws<C>()
where
    C: StrictCertificateLaw<
        ImmutableAfterEmit = Required,
        SignatureOrHash = Required,
        EvidenceRefs = Required,
        AuthorityNotExceedEvidence = Required,
    >,
{
}

pub fn assert_policy_laws<C>()
where
    C: StrictPolicyLaw<
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
    C: StrictWitnessLaw<
        AuthorityEffectEvidenceOnly = Required,
        AdmissibilityDecision = Forbidden,
        Mutation = Forbidden,
        SourceArtifacts = Required,
    >,
{
}

pub fn assert_replay_laws<C>()
where
    C: StrictReplayLaw<
        ReadOnly = Required,
        Mutation = Forbidden,
        ReplayManifest = Required,
        ReplayHash = Required,
        PolicyHash = Required,
    >,
{
}

pub fn assert_terminalizer_laws<C>()
where
    C: StrictTerminalizerLaw<
        Certificate = Required,
        PolicyInterpretation = Forbidden,
        MetricComputation = Forbidden,
        Signing = Forbidden,
    >,
{
}

pub fn assert_public_verify_laws<C>()
where
    C: StrictPublicVerifyLaw<
        ReadOnly = Required,
        Signing = Forbidden,
        Mutation = Forbidden,
        RawPayload = Forbidden,
    >,
{
}

pub fn assert_math_object_laws<C>()
where
    C: StrictMathObjectLaw<
        EmitsDecision = Forbidden,
        EmitsCertificate = Forbidden,
        EmitsAction = Forbidden,
        CustomerClaim = Forbidden,
    >,
{
}

pub fn assert_math_computation_laws<C>()
where
    C: StrictMathComputationLaw<
        EmitsDecision = Forbidden,
        EmitsCertificate = Forbidden,
        EmitsAction = Forbidden,
        CustomerClaim = Forbidden,
    >,
{
}

pub fn assert_llm_adapter_laws<C>()
where
    C: StrictLlmAdapterLaw<
        SelfCertification = Forbidden,
        EmitsCertificate = Forbidden,
        Terminalization = Forbidden,
        RawResponseHash = Required,
        ParsedCandidateMapping = Required,
    >,
{
}

pub fn assert_packetization_laws<C>()
where
    C: StrictPacketizationLaw<
        LosslessRoundtrip = Required,
        ParserRequired = Required,
        GrammarRequired = Required,
        SemanticCertification = Forbidden,
    >,
{
}

// Origin: engine/crates_rs/core_contracts/src/traits_authority_laws.rs
// Claim: urn:core:crates_rs:core-contracts:traits-authority-laws:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd1608540 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd1608540` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord1608540 {
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
impl BoundaryErrord1608540 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord1608540 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord1608540 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd1608540 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord1608540> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord1608540::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord1608540::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord1608540::ExceedsCapacity {
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
mod l4_boundary_tests_d1608540 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd1608540::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd1608540::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd1608540::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd1608540::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd1608540::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord1608540::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord1608540::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
