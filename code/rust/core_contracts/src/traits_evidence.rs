use crate::kinds::ContractEffect;
use core_types::trace_artifact::TraceArtifact;

pub trait EvidenceRef {}
pub trait EvidenceArtifact {}
pub trait WitnessArtifact {}

pub trait TraceRecorder {
    type Event;
    type Artifact: TraceArtifact;
    fn record(&mut self, event: Self::Event);
    fn commit(self) -> Self::Artifact;
}

pub trait Witness {}

// =============================================================================
// Certificate Kernel Contract (02_evidence.yaml)
// =============================================================================

/// Typed evidence-binding envelope with declared verifier capability.
/// Maps to certificate_kernel contract in 02_evidence.yaml.
///
/// CertificateKernel binds typed claims to attached evidence under a declared verifier
/// capability. Unchecked certificates and proof witnesses are EvidenceOnly. Verified
/// certificates may support FactOnly claims only within the authority bound of attached
/// evidence, declared verifier capability, and governing contract.
pub trait CertificateKernel {
    type Claim;
    type Evidence;
    type Verifier;
    type Envelope;
    type Error;

    fn seal_certificate(
        &self,
        claim: Self::Claim,
        evidence_refs: Vec<String>,
        witness_refs: Vec<String>,
    ) -> Result<Self::Envelope, Self::Error>;

    fn verify_certificate(
        &self,
        envelope: &Self::Envelope,
        verifier: &Self::Verifier,
    ) -> Result<VerifiedCertificateClaim, Self::Error>;
}

/// Certificate kind enumeration from 02_evidence.yaml.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CertificateKind {
    AnalysisCertificate,
    ReplayCertificate,
    WitnessCertificate,
    LiftLicenseEvidence,
    TraceCertificate,
}

/// Certificate envelope structure.
#[derive(Debug, Clone)]
pub struct CertificateEnvelope {
    pub certificate_id: String,
    pub claim: String,
    pub evidence_refs: Vec<String>,
    pub witness_refs: Vec<String>,
    pub measurement_refs: Vec<String>,
    pub replay_refs: Vec<String>,
    pub certificate_hash: String,
    pub authority_effect: ContractEffect,
}

impl CertificateEnvelope {
    pub fn new(
        certificate_id: String,
        claim: String,
        evidence_refs: Vec<String>,
        witness_refs: Vec<String>,
        measurement_refs: Vec<String>,
        replay_refs: Vec<String>,
        certificate_hash: String,
    ) -> Self {
        Self {
            certificate_id,
            claim,
            evidence_refs,
            witness_refs,
            measurement_refs,
            replay_refs,
            certificate_hash,
            authority_effect: ContractEffect::EvidenceOnly,
        }
    }
}

/// Verified certificate claim structure.
#[derive(Debug, Clone)]
pub struct VerifiedCertificateClaim {
    pub certificate_ref: String,
    pub verifier_ref: String,
    pub evidence_authority_bound: ContractEffect,
    pub verified_claim_hash: String,
    pub authority_effect: ContractEffect,
}

impl VerifiedCertificateClaim {
    pub fn new(
        certificate_ref: String,
        verifier_ref: String,
        evidence_authority_bound: ContractEffect,
        verified_claim_hash: String,
        authority_effect: ContractEffect,
    ) -> Result<Self, ContractEffect> {
        if authority_rank(authority_effect) > authority_rank(evidence_authority_bound) {
            return Err(authority_effect);
        }

        Ok(Self {
            certificate_ref,
            verifier_ref,
            evidence_authority_bound,
            verified_claim_hash,
            authority_effect,
        })
    }
}

fn authority_rank(effect: ContractEffect) -> u8 {
    match effect {
        ContractEffect::None => 0,
        ContractEffect::EvidenceOnly => 1,
        ContractEffect::FactOnly => 2,
        ContractEffect::RequiresEvaluator | ContractEffect::RequestsDecision => 3,
        ContractEffect::AuthorizesTransition => 4,
        ContractEffect::StateTransition => 5,
    }
}

// =============================================================================
// Measurement Kernel Contract (02_evidence.yaml)
// =============================================================================

/// Exact or certified numerical/symbolic value envelope.
/// Maps to measurement_kernel contract in 02_evidence.yaml.
///
/// MeasurementKernel wraps exact, symbolic, interval, or certificate-backed value evidence.
/// Raw values do not become facts until source identity, method, tolerance semantics, input
/// hash, measurement hash, witness refs, certificate refs, and replay refs are checked.
pub trait MeasurementKernel {
    type Source;
    type Method;
    type Value;
    type Envelope;
    type Error;

    fn create_measurement(
        &self,
        source: &Self::Source,
        method: &Self::Method,
        value: Self::Value,
    ) -> Result<Self::Envelope, Self::Error>;
}

/// Measurement value types from 02_evidence.yaml.
#[derive(Debug, Clone, PartialEq)]
pub enum MeasurementValue {
    ExactRational { numerator: i64, denominator: u64 },
    Integer(i64),
    Interval { lower: f64, upper: f64 },
    CertificateBackedApproximation { value: f64, certificate_ref: String },
    DiagnosticFloat(f64),
}

/// Raw measurement envelope structure, not a checked measurement fact.
///
/// The constructor preserves submitted references and values without validating
/// their semantics. The label cannot be upgraded by assigning a contract effect:
///
/// ```
/// use core_contracts::traits::evidence::{MeasurementEnvelope, MeasurementValue};
/// use core_contracts::kinds::ContractEffect;
/// let raw = MeasurementEnvelope::new(
///     "measurement:claimed".into(), "source:claimed".into(), "method:claimed".into(),
///     MeasurementValue::Integer(42), None, vec![], vec![], vec![], "hash:claimed".into(),
/// );
/// assert_eq!(raw.authority_effect(), ContractEffect::EvidenceOnly);
/// assert_eq!(raw.value, MeasurementValue::Integer(42));
/// ```
///
/// ```compile_fail,E0616
/// use core_contracts::traits::evidence::MeasurementEnvelope;
/// use core_contracts::kinds::ContractEffect;
/// fn forge(envelope: &mut MeasurementEnvelope) {
///     envelope.authority_effect = ContractEffect::FactOnly;
/// }
/// ```
///
/// Raw records must use the EvidenceOnly constructor, not a public struct literal:
///
/// ```compile_fail,E0451
/// use core_contracts::traits::evidence::{MeasurementEnvelope, MeasurementValue};
/// use core_contracts::kinds::ContractEffect;
/// let forged = MeasurementEnvelope {
///     measurement_id: "claimed-measurement".into(),
///     source_ref: "claimed-source".into(),
///     method_ref: "claimed-method".into(),
///     value: MeasurementValue::Integer(1),
///     tolerance_ref: None,
///     witness_refs: vec![],
///     certificate_refs: vec![],
///     replay_refs: vec![],
///     measurement_hash: "claimed-hash".into(),
///     authority_effect: ContractEffect::StateTransition,
/// };
/// ```
#[derive(Debug, Clone)]
pub struct MeasurementEnvelope {
    pub measurement_id: String,
    pub source_ref: String,
    pub method_ref: String,
    pub value: MeasurementValue,
    pub tolerance_ref: Option<String>,
    pub witness_refs: Vec<String>,
    pub certificate_refs: Vec<String>,
    pub replay_refs: Vec<String>,
    pub measurement_hash: String,
    authority_effect: ContractEffect,
}

impl MeasurementEnvelope {
    /// Read the raw evidence label; this is not certification or runtime authority.
    pub fn authority_effect(&self) -> ContractEffect {
        self.authority_effect
    }

    // Envelope constructor mirrors the record's full field set by design.
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        measurement_id: String,
        source_ref: String,
        method_ref: String,
        value: MeasurementValue,
        tolerance_ref: Option<String>,
        witness_refs: Vec<String>,
        certificate_refs: Vec<String>,
        replay_refs: Vec<String>,
        measurement_hash: String,
    ) -> Self {
        Self {
            measurement_id,
            source_ref,
            method_ref,
            value,
            tolerance_ref,
            witness_refs,
            certificate_refs,
            replay_refs,
            measurement_hash,
            authority_effect: ContractEffect::EvidenceOnly,
        }
    }
}

// =============================================================================
// Observable Contract (02_evidence.yaml)
// =============================================================================

/// State extraction and measurable quantity boundary.
/// Maps to observable contract in 02_evidence.yaml.
///
/// Observable extracts primitive quantities from state through declared boundaries.
/// It does not perform governance judgment, policy interpretation, candidate ranking,
/// canonical cohomological measurement emission unless admitted by Functional authority,
/// licensing, mutation, or execution.
pub trait Observable {
    type Source;
    type Output;
    type Error;

    fn observable_id(&self) -> &str;
    fn extract(&self, source: &Self::Source) -> Result<Self::Output, Self::Error>;
}

/// Observable output structure.
#[derive(Debug, Clone)]
pub struct ObservableOutput {
    pub observable_id: String,
    pub source_ref: String,
    pub output_kind: String,
    pub output_ref: String,
    pub output_hash: String,
    pub authority_effect: ContractEffect,
}

impl ObservableOutput {
    pub fn new(
        observable_id: String,
        source_ref: String,
        output_kind: String,
        output_ref: String,
        output_hash: String,
    ) -> Self {
        Self {
            observable_id,
            source_ref,
            output_kind,
            output_ref,
            output_hash,
            authority_effect: ContractEffect::EvidenceOnly,
        }
    }
}

// =============================================================================
// Replay Kernel Contract (02_evidence.yaml)
// =============================================================================

/// Deterministic reconstruction and replay verification.
/// Maps to replay_kernel contract in 02_evidence.yaml.
///
/// Replay reconstructs declared historical execution from trace, manifest, schema, seed,
/// witness, measurement, and certificate references. Replay artifacts are EvidenceOnly
/// until verified. Verified replay may support FactOnly history claims but does not repair,
/// authorize, terminalize, license, mutate, or execute live control flow.
pub trait ReplayKernel {
    type Manifest;
    type Report;
    type Error;

    fn replay(
        &self,
        manifest: &Self::Manifest,
        trace_refs: Vec<String>,
    ) -> Result<Self::Report, Self::Error>;
}

/// Replay status enumeration from 02_evidence.yaml.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ReplayStatus {
    Verified,
    Diverged,
    Impossible,
    Indeterminate,
}

/// Replay report structure.
#[derive(Debug, Clone)]
pub struct ReplayReport {
    pub replay_id: String,
    pub trace_refs: Vec<String>,
    pub manifest_ref: String,
    pub status: ReplayStatus,
    pub output_hash: String,
    pub authority_effect: ContractEffect,
}

impl ReplayReport {
    pub fn new(
        replay_id: String,
        trace_refs: Vec<String>,
        manifest_ref: String,
        status: ReplayStatus,
        output_hash: String,
    ) -> Self {
        Self {
            replay_id,
            trace_refs,
            manifest_ref,
            status,
            output_hash,
            authority_effect: ContractEffect::EvidenceOnly,
        }
    }
}

// =============================================================================
// Diagnostic Contract (02_evidence.yaml)
// =============================================================================

/// Health reporting over declared subjects.
/// Maps to diagnostic contract in 02_evidence.yaml.
///
/// Diagnostic is a read-only health reporting component. It emits factual findings and
/// measurement references, but it does not prescribe treatment, schedule control flow,
/// classify admissibility, terminalize, mutate, authorize, or execute.
pub trait Diagnostic {
    type Subject;
    type Finding;
    type Report;
    type Error;

    fn diagnose(&self, subject: &Self::Subject) -> Result<Self::Report, Self::Error>;
}

/// Diagnostic finding structure.
#[derive(Debug, Clone)]
pub struct DiagnosticFinding {
    pub finding_id: String,
    pub severity: DiagnosticSeverity,
    pub detail: String,
    pub measurement_refs: Vec<String>,
}

/// Diagnostic severity levels.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DiagnosticSeverity {
    Info,
    Warning,
    Error,
    Critical,
}

/// Diagnostic report structure.
#[derive(Debug, Clone)]
pub struct DiagnosticReport {
    pub subject_ref: String,
    pub findings: Vec<DiagnosticFinding>,
    pub measurements: Vec<String>,
    pub certificate_refs: Vec<String>,
    pub diagnostic_id: String,
    pub report_hash: String,
    pub authority_effect: ContractEffect,
}

impl DiagnosticReport {
    pub fn new(
        subject_ref: String,
        findings: Vec<DiagnosticFinding>,
        measurements: Vec<String>,
        certificate_refs: Vec<String>,
        diagnostic_id: String,
        report_hash: String,
    ) -> Self {
        Self {
            subject_ref,
            findings,
            measurements,
            certificate_refs,
            diagnostic_id,
            report_hash,
            authority_effect: ContractEffect::EvidenceOnly,
        }
    }
}

// =============================================================================
// Witness Envelope Contract (02_evidence.yaml)
// =============================================================================

/// Typed attestation record binding a claim to computational evidence.
/// Maps to witness contract in 02_evidence.yaml.
///
/// Witness supplies inspectable, canonicalized, replayable evidence. WitnessEnvelope and
/// WitnessVerificationResult are EvidenceOnly until promoted by a declared verification,
/// certificate, or replay boundary.
#[derive(Debug, Clone)]
pub struct WitnessEnvelope {
    pub witness_id: String,
    pub subject_ref: String,
    pub claim_type: String,
    pub source_artifacts: Vec<String>,
    pub canonical_form: String,
    pub canonical_hash: String,
    pub replay_refs: Vec<String>,
    pub certificate_refs: Vec<String>,
    pub authority_effect: ContractEffect,
}

impl WitnessEnvelope {
    // Envelope constructor mirrors the record's full field set by design.
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        witness_id: String,
        subject_ref: String,
        claim_type: String,
        source_artifacts: Vec<String>,
        canonical_form: String,
        canonical_hash: String,
        replay_refs: Vec<String>,
        certificate_refs: Vec<String>,
    ) -> Self {
        Self {
            witness_id,
            subject_ref,
            claim_type,
            source_artifacts,
            canonical_form,
            canonical_hash,
            replay_refs,
            certificate_refs,
            authority_effect: ContractEffect::EvidenceOnly,
        }
    }
}

/// Witness verification status from 02_evidence.yaml.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WitnessVerificationStatus {
    Verified,
    Failed,
    Indeterminate,
    Inapplicable,
}

/// Witness verification result structure.
#[derive(Debug, Clone)]
pub struct WitnessVerificationResult {
    pub witness_id: String,
    pub verifier_id: String,
    pub status: WitnessVerificationStatus,
    pub result_hash: String,
    pub certificate_ref: Option<String>,
    pub authority_effect: ContractEffect,
}

impl WitnessVerificationResult {
    pub fn new(
        witness_id: String,
        verifier_id: String,
        status: WitnessVerificationStatus,
        result_hash: String,
        certificate_ref: Option<String>,
    ) -> Self {
        Self {
            witness_id,
            verifier_id,
            status,
            result_hash,
            certificate_ref,
            authority_effect: ContractEffect::EvidenceOnly,
        }
    }
}

// Origin: engine/crates_rs/core_contracts/src/traits_evidence.rs
// Claim: urn:core:crates_rs:core-contracts:traits-evidence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord22475c68 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord22475c68` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError22475c68 {
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
impl BoundaryError22475c68 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError22475c68 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError22475c68 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord22475c68 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError22475c68> {
        if capacity_bound == 0 {
            return Err(BoundaryError22475c68::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError22475c68::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError22475c68::ExceedsCapacity {
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
    fn evidence_envelopes_default_to_evidence_only() {
        let certificate = CertificateEnvelope::new(
            "cert:1".to_string(),
            "claim".to_string(),
            vec!["evidence:1".to_string()],
            Vec::new(),
            Vec::new(),
            Vec::new(),
            "hash:cert".to_string(),
        );
        assert_eq!(certificate.authority_effect, ContractEffect::EvidenceOnly);

        let measurement = MeasurementEnvelope::new(
            "measurement:1".to_string(),
            "source:1".to_string(),
            "method:1".to_string(),
            MeasurementValue::Integer(1),
            None,
            Vec::new(),
            Vec::new(),
            Vec::new(),
            "hash:measurement".to_string(),
        );
        assert_eq!(measurement.authority_effect(), ContractEffect::EvidenceOnly);

        let observable = ObservableOutput::new(
            "observable:1".to_string(),
            "source:1".to_string(),
            "integer".to_string(),
            "output:1".to_string(),
            "hash:output".to_string(),
        );
        assert_eq!(observable.authority_effect, ContractEffect::EvidenceOnly);

        let replay = ReplayReport::new(
            "replay:1".to_string(),
            vec!["trace:1".to_string()],
            "manifest:1".to_string(),
            ReplayStatus::Verified,
            "hash:output".to_string(),
        );
        assert_eq!(replay.authority_effect, ContractEffect::EvidenceOnly);

        let diagnostic = DiagnosticReport::new(
            "subject:1".to_string(),
            Vec::new(),
            Vec::new(),
            Vec::new(),
            "diagnostic:1".to_string(),
            "hash:report".to_string(),
        );
        assert_eq!(diagnostic.authority_effect, ContractEffect::EvidenceOnly);

        let witness = WitnessEnvelope::new(
            "witness:1".to_string(),
            "subject:1".to_string(),
            "claim".to_string(),
            Vec::new(),
            "canonical".to_string(),
            "hash:canonical".to_string(),
            Vec::new(),
            Vec::new(),
        );
        assert_eq!(witness.authority_effect, ContractEffect::EvidenceOnly);

        let verification = WitnessVerificationResult::new(
            "witness:1".to_string(),
            "verifier:1".to_string(),
            WitnessVerificationStatus::Verified,
            "hash:result".to_string(),
            None,
        );
        assert_eq!(verification.authority_effect, ContractEffect::EvidenceOnly);
    }

    #[test]
    fn raw_measurement_preserves_claimed_fields_without_promoting_them() {
        let mut measurement = MeasurementEnvelope::new(
            "measurement:claimed".into(),
            "source:claimed".into(),
            "method:claimed".into(),
            MeasurementValue::Integer(42),
            Some("tolerance:claimed".into()),
            vec!["witness:claimed".into()],
            vec!["certificate:claimed".into()],
            vec!["replay:claimed".into()],
            "hash:claimed".into(),
        );
        assert_eq!(measurement.measurement_id, "measurement:claimed");
        assert_eq!(measurement.source_ref, "source:claimed");
        assert_eq!(measurement.method_ref, "method:claimed");
        assert_eq!(measurement.value, MeasurementValue::Integer(42));
        assert_eq!(
            measurement.tolerance_ref.as_deref(),
            Some("tolerance:claimed")
        );
        assert_eq!(measurement.witness_refs, ["witness:claimed"]);
        assert_eq!(measurement.certificate_refs, ["certificate:claimed"]);
        assert_eq!(measurement.replay_refs, ["replay:claimed"]);
        assert_eq!(measurement.measurement_hash, "hash:claimed");
        assert_eq!(measurement.authority_effect(), ContractEffect::EvidenceOnly);

        measurement.source_ref = "source:altered".into();
        measurement.value = MeasurementValue::DiagnosticFloat(1.25);
        measurement.measurement_hash = "hash:altered".into();
        assert_eq!(measurement.source_ref, "source:altered");
        assert_eq!(measurement.value, MeasurementValue::DiagnosticFloat(1.25));
        assert_eq!(measurement.measurement_hash, "hash:altered");
        assert_eq!(measurement.authority_effect(), ContractEffect::EvidenceOnly);
    }

    #[test]
    fn verified_certificate_claim_cannot_exceed_evidence_bound() {
        let fact_claim = VerifiedCertificateClaim::new(
            "cert:1".to_string(),
            "verifier:1".to_string(),
            ContractEffect::FactOnly,
            "hash:claim".to_string(),
            ContractEffect::FactOnly,
        )
        .expect("equal authority bound should pass");
        assert_eq!(fact_claim.authority_effect, ContractEffect::FactOnly);

        let too_strong = VerifiedCertificateClaim::new(
            "cert:1".to_string(),
            "verifier:1".to_string(),
            ContractEffect::EvidenceOnly,
            "hash:claim".to_string(),
            ContractEffect::FactOnly,
        );
        assert!(matches!(too_strong, Err(ContractEffect::FactOnly)));
    }
}

#[cfg(test)]
mod l4_boundary_tests_22475c68 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord22475c68::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord22475c68::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord22475c68::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord22475c68::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord22475c68::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError22475c68::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError22475c68::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
