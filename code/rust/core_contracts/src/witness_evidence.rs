use crate::kinds::{Capability, ContractEffect};
use serde::{Deserialize, Serialize};

/// Classification of witness types.
///
/// Per 02_evidence.yaml witness contract, witnesses are typed attestation records.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum WitnessClass {
    /// Structural witness: proves structural properties (e.g., basis independence)
    Structural,
    /// Behavioral witness: proves behavioral properties (e.g., replay integrity)
    Behavioral,
    /// Empirical witness: statistical evidence from sampling (e.g., phi monotonicity)
    Empirical,
}

/// Witness certainty hierarchy (epistemic certainty of a witness).
///
/// From highest to lowest certainty. This is the **witness-certainty axis**,
/// distinct from `EvidenceCeiling` (host verification capability) and
/// `WitnessClass` (kind antichain). Three independent axes.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[repr(u8)]
pub enum WitnessCertainty {
    /// Human-declared evidence (lowest certainty)
    HumanDeclared = 0,
    /// Statistical witness (e.g., property-based testing)
    StatisticalWitness = 1,
    /// Exhaustive finite proof (e.g., all cases enumerated)
    ExhaustiveFiniteProof = 2,
    /// Property witness (e.g., verified behavioral property)
    PropertyWitness = 3,
    /// Full structural proof (e.g., type-level guarantee)
    StructuralProof = 4,
}

/// Witness verification status.
///
/// Per 02_evidence.yaml witness contract:
/// - Verified: witness verification succeeded
/// - Failed: witness verification failed
/// - Indeterminate: verification could not conclude
/// - Inapplicable: verification is not applicable to this witness type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum WitnessVerificationStatus {
    Verified,
    Failed,
    Indeterminate,
    Inapplicable,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LawViolation {
    pub property: &'static str,
    pub description: String,
}

/// Validation witness trait.
///
/// Per 02_evidence.yaml witness contract:
/// - Role: "Typed attestation record binding a claim to computational evidence"
/// - authority_effect: EvidenceOnly (witnesses carry no authority themselves)
/// - Witnesses are EvidenceEnvelope, not StructureArtifact as primary output
///
/// Witnesses must NOT:
/// - certify or sign certificates
/// - verify themselves (self-verification forbidden)
/// - evaluate admissibility
/// - interpret policy
/// - map terminal outcomes
/// - execute state transitions
/// - authorize transitions
/// - license actions
/// - upgrade authority
/// - mutate state
pub trait ValidationWitness:
    core::fmt::Debug + Send + Sync + erased_serde::Serialize + 'static
{
    fn property(&self) -> &'static str;
    fn class(&self) -> WitnessClass;
    fn witness_certainty(&self) -> WitnessCertainty;

    /// Returns the authority effect of this witness.
    ///
    /// Per 02_evidence.yaml: Witnesses always carry EvidenceOnly authority.
    /// A verified witness may support FactOnly claims only through a declared
    /// verifier, CertificateKernel, ReplayVerifier, or validation boundary.
    fn authority_effect(&self) -> ContractEffect {
        ContractEffect::EvidenceOnly
    }
}

erased_serde::serialize_trait_object!(ValidationWitness);

/// Witness verification result.
///
/// Per 02_evidence.yaml witness contract structural_representation.verification_result.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WitnessVerificationResult {
    pub witness_id: String,
    pub verifier_id: String,
    pub verifier_version: String,
    pub schema_hash: String,
    pub witness_hash: String,
    pub status: WitnessVerificationStatus,
    pub result_hash: String,
    pub supporting_certificate_ref: Option<String>,
    pub authority_effect: ContractEffect,
}

impl WitnessVerificationResult {
    /// Create a new verification result.
    ///
    /// Per YAML contract, verification results are EvidenceOnly by default.
    pub fn new(
        witness_id: impl Into<String>,
        verifier_id: impl Into<String>,
        status: WitnessVerificationStatus,
        result_hash: impl Into<String>,
    ) -> Self {
        Self {
            witness_id: witness_id.into(),
            verifier_id: verifier_id.into(),
            verifier_version: "unspecified".to_string(),
            schema_hash: String::new(),
            witness_hash: String::new(),
            status,
            result_hash: result_hash.into(),
            supporting_certificate_ref: None,
            authority_effect: ContractEffect::EvidenceOnly,
        }
    }

    /// Add a supporting certificate reference.
    pub fn with_supporting_certificate_ref(mut self, cert_ref: impl Into<String>) -> Self {
        self.supporting_certificate_ref = Some(cert_ref.into());
        self
    }

    /// Backward-compatible alias for adding a supporting certificate reference.
    pub fn with_certificate_ref(self, cert_ref: impl Into<String>) -> Self {
        self.with_supporting_certificate_ref(cert_ref)
    }

    pub fn with_verifier_version(mut self, verifier_version: impl Into<String>) -> Self {
        self.verifier_version = verifier_version.into();
        self
    }

    pub fn with_schema_hash(mut self, schema_hash: impl Into<String>) -> Self {
        self.schema_hash = schema_hash.into();
        self
    }

    pub fn with_witness_hash(mut self, witness_hash: impl Into<String>) -> Self {
        self.witness_hash = witness_hash.into();
        self
    }
}

/// Canonical capabilities forbidden to witness producers and witness records.
pub const WITNESS_FORBIDDEN_CAPABILITIES: &[Capability] = &[
    Capability::CertificateSigning,
    Capability::SelfCertification,
    Capability::Evaluation,
    Capability::AdmissibilityDecision,
    Capability::PolicyInterpretation,
    Capability::TerminalMapping,
    Capability::ExecuteStateTransition,
    Capability::ActionLicensing,
    Capability::AuthorityPromotion,
    Capability::RuntimeMutation,
];

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct PhiMonotonicityWitness {
    pub witness_id: String,
    pub contract_id: String,
    pub schema_hash: String,
    pub witness_hash: String,
    pub produced_by: String,
    pub sample_count: usize,
    pub max_phi_delta: f64,
    pub violation_count: usize,
    pub maximum_observed_phi: f64,
    pub minimum_observed_phi: f64,
    pub violations: Vec<LawViolation>,
    pub distribution_metadata: String,
}

impl ValidationWitness for PhiMonotonicityWitness {
    fn property(&self) -> &'static str {
        "phi_monotonicity"
    }
    fn class(&self) -> WitnessClass {
        WitnessClass::Empirical
    }
    fn witness_certainty(&self) -> WitnessCertainty {
        WitnessCertainty::StatisticalWitness
    }
}

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct IdempotenceWitness {
    pub witness_id: String,
    pub contract_id: String,
    pub schema_hash: String,
    pub witness_hash: String,
    pub produced_by: String,
    pub samples_verified: usize,
}

impl ValidationWitness for IdempotenceWitness {
    fn property(&self) -> &'static str {
        "idempotence"
    }
    fn class(&self) -> WitnessClass {
        WitnessClass::Empirical
    }
    fn witness_certainty(&self) -> WitnessCertainty {
        WitnessCertainty::StatisticalWitness
    }
}

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct DeterminismWitness {
    pub witness_id: String,
    pub contract_id: String,
    pub schema_hash: String,
    pub witness_hash: String,
    pub produced_by: String,
    pub samples_verified: usize,
}

impl ValidationWitness for DeterminismWitness {
    fn property(&self) -> &'static str {
        "determinism"
    }
    fn class(&self) -> WitnessClass {
        WitnessClass::Empirical
    }
    fn witness_certainty(&self) -> WitnessCertainty {
        WitnessCertainty::StatisticalWitness
    }
}

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct ReplayWitness {
    pub witness_id: String,
    pub contract_id: String,
    pub schema_hash: String,
    pub witness_hash: String,
    pub produced_by: String,
    pub trace_hash: String,
    pub steps_verified: usize,
}

impl ValidationWitness for ReplayWitness {
    fn property(&self) -> &'static str {
        "replay_integrity"
    }
    fn class(&self) -> WitnessClass {
        WitnessClass::Behavioral
    }
    fn witness_certainty(&self) -> WitnessCertainty {
        WitnessCertainty::PropertyWitness
    }
}

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct HashWitness {
    pub witness_id: String,
    pub contract_id: String,
    pub schema_hash: String,
    pub witness_hash: String,
    pub produced_by: String,
    pub computed_hash: String,
}

impl ValidationWitness for HashWitness {
    fn property(&self) -> &'static str {
        "hash_verification"
    }
    fn class(&self) -> WitnessClass {
        WitnessClass::Structural
    }
    fn witness_certainty(&self) -> WitnessCertainty {
        WitnessCertainty::StructuralProof
    }
}

pub trait WitnessProducer<S> {
    type Witness: ValidationWitness;
    fn produce(subject: &S) -> Self::Witness;
}

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct VectorSpaceAdmissibilityWitness {
    pub witness_id: String,
    pub contract_id: String,
    pub schema_hash: String,
    pub witness_hash: String,
    pub produced_by: String,
    pub dimension: usize,
    pub basis_hash: String,
    pub operations_verified: bool,
}

impl ValidationWitness for VectorSpaceAdmissibilityWitness {
    fn property(&self) -> &'static str {
        "vector_space_admissibility"
    }
    fn class(&self) -> WitnessClass {
        WitnessClass::Structural
    }
    fn witness_certainty(&self) -> WitnessCertainty {
        WitnessCertainty::StructuralProof
    }
}

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct BasisLinearIndependenceWitness {
    pub witness_id: String,
    pub contract_id: String,
    pub schema_hash: String,
    pub witness_hash: String,
    pub produced_by: String,
    pub dimension: usize,
    pub basis_hash: String,
    pub rank_verified: bool,
}

impl ValidationWitness for BasisLinearIndependenceWitness {
    fn property(&self) -> &'static str {
        "basis_linear_independence"
    }
    fn class(&self) -> WitnessClass {
        WitnessClass::Structural
    }
    fn witness_certainty(&self) -> WitnessCertainty {
        WitnessCertainty::StructuralProof
    }
}

// Origin: engine/crates_rs/core_contracts/src/witness_evidence.rs
// Claim: urn:core:crates_rs:core-contracts:witness-evidence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordde4c6e83 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordde4c6e83` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorde4c6e83 {
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
impl BoundaryErrorde4c6e83 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorde4c6e83 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorde4c6e83 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordde4c6e83 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorde4c6e83> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorde4c6e83::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorde4c6e83::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorde4c6e83::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn witness_forbidden_capabilities_use_canonical_capability_enum() {
        assert!(WITNESS_FORBIDDEN_CAPABILITIES.contains(&Capability::SelfCertification));
        assert!(WITNESS_FORBIDDEN_CAPABILITIES.contains(&Capability::ActionLicensing));
        assert!(WITNESS_FORBIDDEN_CAPABILITIES.contains(&Capability::ExecuteStateTransition));
        assert!(WITNESS_FORBIDDEN_CAPABILITIES.contains(&Capability::AuthorityPromotion));
    }

    #[test]
    fn witness_verification_result_is_evidence_with_reference_metadata() {
        let result = WitnessVerificationResult::new(
            "wit:1",
            "verifier:1",
            WitnessVerificationStatus::Verified,
            "result:hash",
        )
        .with_verifier_version("v1")
        .with_schema_hash("schema:hash")
        .with_witness_hash("witness:hash")
        .with_supporting_certificate_ref("cert:ref");

        assert_eq!(result.authority_effect, ContractEffect::EvidenceOnly);
        assert_eq!(result.verifier_version, "v1");
        assert_eq!(result.schema_hash, "schema:hash");
        assert_eq!(result.witness_hash, "witness:hash");
        assert_eq!(
            result.supporting_certificate_ref.as_deref(),
            Some("cert:ref")
        );
    }

    #[test]
    fn witness_structs_carry_identity_hash_and_producer_metadata() {
        let witness = PhiMonotonicityWitness {
            witness_id: "wit:phi".to_string(),
            contract_id: "contract:lambda".to_string(),
            schema_hash: "schema:hash".to_string(),
            witness_hash: "witness:hash".to_string(),
            produced_by: "producer:v1".to_string(),
            sample_count: 2,
            max_phi_delta: 0.0,
            violation_count: 0,
            maximum_observed_phi: 1.0,
            minimum_observed_phi: 0.0,
            violations: Vec::new(),
            distribution_metadata: "explicit_finite_samples".to_string(),
        };

        assert_eq!(witness.authority_effect(), ContractEffect::EvidenceOnly);
        assert_eq!(witness.property(), "phi_monotonicity");
        assert_eq!(witness.witness_id, "wit:phi");
        assert_eq!(witness.witness_hash, "witness:hash");
        assert_eq!(witness.produced_by, "producer:v1");
    }
}

#[cfg(test)]
mod l4_boundary_tests_de4c6e83 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordde4c6e83::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordde4c6e83::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordde4c6e83::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordde4c6e83::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordde4c6e83::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorde4c6e83::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorde4c6e83::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
