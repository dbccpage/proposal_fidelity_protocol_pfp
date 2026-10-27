//! Measurement Envelope
//!
//! Provides provenance-first measurement wrappers with full traceability.
//! Contract: measurement_contract.md

use crate::measurement_kernel::{
    MeasurementMethod, MeasurementValue, RangeBehavior, ToleranceSpec, UnitSpec,
};
use core_types::domain_types::Hash256;
use core_types::FactLabel;
use serde::{Deserialize, Serialize};

/// Measurement identifier
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct MeasurementId(pub String);

/// The only fact label an unchecked measurement record can carry.
///
/// This is not checked evidence or certified authority. The broader shared
/// [`FactLabel`] remains available to actual checker boundaries, but raw
/// measurement records have no constructor for its `FactOnly` variant.
/// Serde retains the existing `"EvidenceOnly"` spelling and rejects attempted
/// promotions instead of silently relabelling them as unchecked evidence.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum RawEvidenceLabel {
    #[default]
    EvidenceOnly,
}

impl RawEvidenceLabel {
    /// Project the raw record's label without granting checked-fact status.
    pub fn fact_label(self) -> FactLabel {
        match self {
            Self::EvidenceOnly => FactLabel::EvidenceOnly,
        }
    }
}

/// Measurement envelope with full provenance
///
/// Measurements are provenance-first. A raw MeasurementValue must be wrapped
/// in an envelope carrying method, source, tolerance, and replay references.
///
/// **Default Authority:** EvidenceOnly
///
/// A separate checked measurement may become FactOnly only after:
/// - Source identity verification
/// - Method validation
/// - Tolerance semantics checking
/// - Input hash verification
/// - Measurement hash verification
/// - Witness refs validation
/// - Certificate refs validation
/// - Replay refs validation
///
/// This raw envelope does not implement that checker. Its payload fields and
/// references remain submitted evidence, not assertions that those checks ran.
/// An unchecked setter cannot promote it:
///
/// ```compile_fail,E0599
/// use core_measurement::measurement_envelope::MeasurementEnvelope;
/// fn unchecked_promotion(envelope: &mut MeasurementEnvelope) {
///     envelope.promote_to_fact_only();
/// }
/// ```
///
/// Nor may a caller assign a stronger shared label directly:
///
/// ```compile_fail,E0308
/// use core_measurement::measurement_envelope::MeasurementEnvelope;
/// use core_types::FactLabel;
/// fn forged_fact(envelope: &mut MeasurementEnvelope) {
///     envelope.authority_effect = FactLabel::FactOnly;
/// }
/// ```
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MeasurementEnvelope {
    /// Unique measurement identifier
    pub measurement_id: MeasurementId,

    /// The measured value
    pub value: MeasurementValue,

    /// Optional unit specification
    pub unit: Option<UnitSpec>,

    /// Method used to produce this measurement
    pub method: MeasurementMethod,

    /// Reference to the source artifact (Observable, Functional, Solver)
    pub source_ref: ArtifactRef,

    /// Reference to the measurement producer
    pub producer_ref: MeasurementProducerRef,

    /// Tolerance specification
    pub tolerance: ToleranceSpec,

    /// Range behavior for out-of-bounds values
    pub range_behavior: RangeBehavior,

    /// Replay references for verification
    pub replay_refs: Vec<ReplayRef>,

    /// Hash of input data
    pub input_hash: Hash256,

    /// Hash of the measurement itself
    pub measurement_hash: Hash256,

    /// Schema version hash
    pub schema_hash: Hash256,

    /// Referenced certificates (for CertifiedApproximation)
    pub certificate_refs: Vec<CertificateId>,

    /// Referenced witnesses
    pub witness_refs: Vec<WitnessId>,

    /// Raw evidence label; no unchecked FactOnly state is representable.
    pub authority_effect: RawEvidenceLabel,
}

impl MeasurementEnvelope {
    /// Check if this envelope has EvidenceOnly authority
    pub fn is_evidence_only(&self) -> bool {
        matches!(self.authority_effect.fact_label(), FactLabel::EvidenceOnly)
    }

    /// Raw envelopes never carry the checked-fact label.
    pub fn is_fact_only(&self) -> bool {
        matches!(self.authority_effect.fact_label(), FactLabel::FactOnly)
    }
}

/// Artifact reference - stable reference for addressability and hashing
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ArtifactRef {
    pub artifact_id: ArtifactId,
    pub artifact_family: ArtifactFamily,
    pub domain_kind: DomainArtifactKind,
    pub content_hash: Hash256,
    pub schema_version: SchemaVersion,
}

/// Artifact identifier
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ArtifactId(pub String);

/// Artifact family classification
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ArtifactFamily {
    Structure,
    Evidence,
    Fact,
    Decision,
    Action,
    Record,
    Domain,
}

/// Domain-specific artifact kind
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct DomainArtifactKind(pub String);

/// Schema version
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct SchemaVersion(pub String);

/// Measurement producer reference
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum MeasurementProducerRef {
    Observable(String),
    Functional(String),
    Solver(String),
    Analysis(String),
    Custom(String),
}

/// Replay reference for verification
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ReplayRef(pub String);

/// Certificate identifier
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct CertificateId(pub String);

/// Witness identifier
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct WitnessId(pub String);

// Origin: engine/crates_rs/core_measurement/src/measurement_envelope.rs
// Claim: urn:core:crates_rs:core-measurement:measurement-envelope:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde2b933aa {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde2b933aa` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore2b933aa {
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
impl BoundaryErrore2b933aa {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore2b933aa {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore2b933aa {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde2b933aa {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore2b933aa> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore2b933aa::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore2b933aa::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore2b933aa::ExceedsCapacity {
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
    use crate::measurement_kernel::{DiagnosticPurpose, MeasurementValue};

    fn create_test_envelope() -> MeasurementEnvelope {
        MeasurementEnvelope {
            measurement_id: MeasurementId("test-001".to_string()),
            value: MeasurementValue::Integer(42),
            unit: None,
            method: MeasurementMethod::DirectObservation,
            source_ref: ArtifactRef {
                artifact_id: ArtifactId("artifact-001".to_string()),
                artifact_family: ArtifactFamily::Evidence,
                domain_kind: DomainArtifactKind("test".to_string()),
                content_hash: Hash256::from_hex_unchecked("a".repeat(64)),
                schema_version: SchemaVersion("1.0".to_string()),
            },
            producer_ref: MeasurementProducerRef::Observable("obs-001".to_string()),
            tolerance: ToleranceSpec {
                absolute_tolerance: None,
                relative_tolerance: None,
            },
            range_behavior: RangeBehavior::Unbounded,
            replay_refs: vec![],
            input_hash: Hash256::from_hex_unchecked("b".repeat(64)),
            measurement_hash: Hash256::from_hex_unchecked("c".repeat(64)),
            schema_hash: Hash256::from_hex_unchecked("d".repeat(64)),
            certificate_refs: vec![],
            witness_refs: vec![],
            authority_effect: RawEvidenceLabel::default(),
        }
    }

    #[test]
    fn measurement_envelope_records_source_ref() {
        let envelope = create_test_envelope();
        assert_eq!(envelope.source_ref.artifact_id.0, "artifact-001");
    }

    #[test]
    fn measurement_envelope_records_hashes() {
        let envelope = create_test_envelope();
        assert_eq!(envelope.input_hash.as_str(), &"b".repeat(64));
        assert_eq!(envelope.measurement_hash.as_str(), &"c".repeat(64));
        assert_eq!(envelope.schema_hash.as_str(), &"d".repeat(64));
    }

    #[test]
    fn measurement_authority_effect_defaults_to_evidence_only() {
        let envelope = create_test_envelope();
        assert!(envelope.is_evidence_only());
        assert!(!envelope.is_fact_only());
        assert_eq!(
            envelope.authority_effect.fact_label(),
            FactLabel::EvidenceOnly
        );
    }

    #[test]
    fn raw_measurement_remains_evidence_when_claimed_provenance_changes() {
        let mut envelope = create_test_envelope();
        envelope.method = MeasurementMethod::ReplayVerification;
        envelope
            .witness_refs
            .push(WitnessId("claimed-witness".into()));
        envelope
            .certificate_refs
            .push(CertificateId("claimed-certificate".into()));
        envelope
            .replay_refs
            .push(ReplayRef("claimed-replay".into()));
        assert!(envelope.is_evidence_only());
        assert!(!envelope.is_fact_only());
        assert_eq!(
            envelope.authority_effect.fact_label(),
            FactLabel::EvidenceOnly
        );
    }

    #[test]
    fn measurement_envelope_records_schema_hash() {
        let envelope = create_test_envelope();
        assert_eq!(envelope.schema_hash.as_str(), &"d".repeat(64));
    }

    #[test]
    fn measurement_envelope_records_range_behavior() {
        let envelope = create_test_envelope();
        assert_eq!(envelope.range_behavior, RangeBehavior::Unbounded);
    }

    #[test]
    fn measurement_envelope_records_producer_ref() {
        let envelope = create_test_envelope();
        match &envelope.producer_ref {
            MeasurementProducerRef::Observable(id) => assert_eq!(id, "obs-001"),
            _ => panic!("Expected Observable producer"),
        }
    }

    #[test]
    fn scalarized_display_score_forbidden_for_governance() {
        let diagnostic_value = MeasurementValue::DiagnosticFloat {
            value: 0.95,
            purpose: DiagnosticPurpose::VisualizationOnly,
        };

        // Cannot convert to governance scalar
        assert!(diagnostic_value.try_into_governance_scalar().is_err());
    }

    #[test]
    fn measurement_value_alone_has_no_authority() {
        // MeasurementValue by itself is just a value type
        // Wrapping a value does not turn it into a checked fact.
        let value = MeasurementValue::Integer(42);

        // Value is just data - the envelope preserves its unverified status.
        let envelope = MeasurementEnvelope {
            value: value.clone(),
            authority_effect: RawEvidenceLabel::default(),
            ..create_test_envelope()
        };

        assert!(envelope.is_evidence_only());
    }
}

#[cfg(test)]
mod l4_boundary_tests_e2b933aa {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde2b933aa::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde2b933aa::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde2b933aa::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde2b933aa::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde2b933aa::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore2b933aa::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore2b933aa::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
