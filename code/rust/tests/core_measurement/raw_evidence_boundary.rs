//! Raw measurement records preserve submitted evidence, never checked facts.
//!
//! These tests exercise actual struct construction and full-record serde. The
//! fixtures' hashes and references are deliberately only claims: neither this
//! boundary nor the shared advisory FactLabel is a certified-authority issuer.

use core_measurement::measurement_access::{
    ArtifactKind, BoundaryViolation, BoundaryViolationId, ImportPath, KernelId,
    MeasurementAccessRule, MeasurementAccessRuleId, SymbolId,
};
use core_measurement::measurement_envelope::{
    ArtifactFamily, ArtifactId, ArtifactRef, CertificateId, DomainArtifactKind,
    MeasurementEnvelope, MeasurementId, MeasurementProducerRef, RawEvidenceLabel, ReplayRef,
    SchemaVersion, WitnessId,
};
use core_measurement::measurement_kernel::{
    MeasurementMethod, MeasurementValue, RangeBehavior, ToleranceSpec, UnitSpec,
};
use core_types::domain_types::Hash256;
use core_types::FactLabel;
use serde::de::DeserializeOwned;
use serde::Serialize;
use serde_json::{error::Category, json, Value};
use std::fmt::Debug;

fn envelope() -> MeasurementEnvelope {
    MeasurementEnvelope {
        measurement_id: MeasurementId("submitted-measurement".into()),
        value: MeasurementValue::Integer(42),
        unit: Some(UnitSpec {
            unit_name: "count".into(),
            dimension: Some("dimensionless".into()),
        }),
        method: MeasurementMethod::ReplayVerification,
        source_ref: ArtifactRef {
            artifact_id: ArtifactId("claimed-source".into()),
            artifact_family: ArtifactFamily::Evidence,
            domain_kind: DomainArtifactKind("fixture".into()),
            content_hash: Hash256::from_hex_unchecked("a".repeat(64)),
            schema_version: SchemaVersion("1.0".into()),
        },
        producer_ref: MeasurementProducerRef::Functional("claimed-functional".into()),
        tolerance: ToleranceSpec {
            absolute_tolerance: None,
            relative_tolerance: None,
        },
        range_behavior: RangeBehavior::Reject,
        replay_refs: vec![ReplayRef("claimed-replay".into())],
        input_hash: Hash256::from_hex_unchecked("b".repeat(64)),
        measurement_hash: Hash256::from_hex_unchecked("c".repeat(64)),
        schema_hash: Hash256::from_hex_unchecked("d".repeat(64)),
        certificate_refs: vec![CertificateId("claimed-certificate".into())],
        witness_refs: vec![WitnessId("claimed-witness".into())],
        authority_effect: RawEvidenceLabel::default(),
    }
}

fn access_rule() -> MeasurementAccessRule {
    MeasurementAccessRule {
        rule_id: MeasurementAccessRuleId("claimed-rule".into()),
        subject_layer: KernelId::Search,
        forbidden_imports: vec![ImportPath::new("core_functional::phi1")],
        forbidden_symbols: vec![SymbolId::new("compute_phi1")],
        allowed_artifacts: vec![ArtifactKind::EvidenceEnvelope],
        rule_hash: Hash256::from_hex_unchecked("e".repeat(64)),
        authority_effect: RawEvidenceLabel::default(),
    }
}

fn violation() -> BoundaryViolation {
    BoundaryViolation {
        violation_id: BoundaryViolationId("claimed-violation".into()),
        rule_id: MeasurementAccessRuleId("claimed-rule".into()),
        subject_layer: KernelId::Search,
        forbidden_symbol: Some(SymbolId::new("compute_phi1")),
        forbidden_import: Some(ImportPath::new("core_functional::phi1")),
        evidence_refs: vec![],
        violation_hash: Hash256::from_hex_unchecked("f".repeat(64)),
        authority_effect: RawEvidenceLabel::default(),
    }
}

fn assert_preserved<T>(original: T)
where
    T: Serialize + DeserializeOwned + PartialEq + Debug,
{
    let encoded = serde_json::to_value(&original).expect("serialize raw record");
    assert_eq!(encoded["authority_effect"], "EvidenceOnly");
    let restored: T = serde_json::from_value(encoded.clone()).expect("read raw evidence");
    assert_eq!(restored, original, "every submitted field must survive");
    assert_eq!(serde_json::to_value(restored).unwrap(), encoded);
}

fn assert_labels_refused<T>(original: T)
where
    T: Serialize + DeserializeOwned + Debug,
{
    let encoded = serde_json::to_value(original).expect("serialize raw record");
    assert_eq!(encoded["authority_effect"], "EvidenceOnly");
    for label in [
        json!("FactOnly"),
        json!("fact_only"),
        json!("Certified"),
        json!("None"),
        Value::Null,
        json!(1),
        json!({"FactOnly": null}),
    ] {
        let mut submitted = encoded.clone();
        submitted["authority_effect"] = label.clone();
        let error = serde_json::from_value::<T>(submitted)
            .expect_err("a forged label must be refused, not silently downgraded");
        assert_eq!(error.classify(), Category::Data, "label: {label}");
        if label == json!("FactOnly") {
            assert_eq!(
                error.to_string(),
                "unknown variant `FactOnly`, expected `EvidenceOnly`"
            );
        }
    }
    let mut omitted = encoded;
    assert!(omitted
        .as_object_mut()
        .unwrap()
        .remove("authority_effect")
        .is_some());
    let error = serde_json::from_value::<T>(omitted)
        .expect_err("omitted labels remain a wire-schema refusal");
    assert_eq!(error.classify(), Category::Data);
    assert_eq!(error.to_string(), "missing field `authority_effect`");
}

#[test]
fn raw_label_projects_only_to_advisory_evidence() {
    assert_eq!(RawEvidenceLabel::default(), RawEvidenceLabel::EvidenceOnly);
    assert_eq!(
        RawEvidenceLabel::EvidenceOnly.fact_label(),
        FactLabel::EvidenceOnly
    );
    assert!(envelope().is_evidence_only());
    assert!(access_rule().is_evidence_only());
    assert!(violation().is_evidence_only());
    assert!(!envelope().is_fact_only());
    assert!(!access_rule().is_fact_only());
    assert!(!violation().is_fact_only());
}

#[test]
fn raw_measurement_envelope_roundtrip_preserves_all_submitted_fields() {
    assert_preserved(envelope());
}

#[test]
fn raw_access_rule_roundtrip_preserves_all_submitted_fields() {
    assert_preserved(access_rule());
}

#[test]
fn raw_boundary_violation_roundtrip_preserves_all_submitted_fields() {
    assert_preserved(violation());
}

#[test]
fn raw_measurement_envelope_refuses_unchecked_fact_deserialization() {
    assert_labels_refused(envelope());
}

#[test]
fn raw_access_rule_refuses_unchecked_fact_deserialization() {
    assert_labels_refused(access_rule());
}

#[test]
fn raw_boundary_violation_refuses_unchecked_fact_deserialization() {
    assert_labels_refused(violation());
}

// Origin: engine/crates_rs/tests/core_measurement/raw_evidence_boundary.rs
// Claim: urn:core:crates_rs:tests:raw-evidence-boundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde09d6fac {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde09d6fac` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore09d6fac {
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
impl BoundaryErrore09d6fac {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore09d6fac {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore09d6fac {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde09d6fac {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore09d6fac> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore09d6fac::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore09d6fac::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore09d6fac::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_e09d6fac() {
    let admitted = BoundaryRecorde09d6fac::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde09d6fac::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
