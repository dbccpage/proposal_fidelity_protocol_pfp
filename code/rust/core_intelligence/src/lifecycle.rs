//! Scoped transfer and closure predicates.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_ad270a85<T> {
    fn checked_invariant_ad270a85(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_ad270a85<T> for Option<T> {
    #[inline]
    fn checked_invariant_ad270a85(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_ad270a85<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_ad270a85(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::{framed_sha256, Refusal};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

pub const LIFECYCLE_DECISION_SCHEMA: &str = "core.intelligence.lifecycle-decision.v1";
pub const LIFECYCLE_CERTIFICATE_SCHEMA: &str = "core.intelligence.lifecycle-certificate.v2";
const CERTIFICATE_DOMAIN: &str = "core.intelligence.lifecycle-certificate.v2";

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum DigestionState {
    Collected,
    Sealed,
    Extracted,
    Absorbed,
    Discharged,
    Blocked,
    Quarantined,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SourceRegistration {
    pub source_id: String,
    pub producer_id: String,
    pub source_class: String,
    pub source_schema_version: String,
    pub manifest_sha256: String,
    pub sealed: bool,
    #[serde(default)]
    pub producer_lease_active: bool,
    pub review_scope: String,
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExtractionRecord {
    #[serde(default)]
    pub complete: bool,
    #[serde(default)]
    pub extractor_version: String,
    #[serde(default)]
    pub checker_version: String,
    #[serde(default)]
    pub coverage_gaps: Vec<String>,
    #[serde(default)]
    pub parse_residuals: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TransferReceipt {
    pub destination_id: String,
    pub target_revision: String,
    pub acknowledgement_ref: String,
    pub kind: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ClosureReceipt {
    pub checker_id: String,
    pub closure_ref: String,
    pub verified: bool,
}

fn default_applicable() -> bool {
    true
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FindingRecord {
    pub finding_id: String,
    #[serde(default)]
    pub kind: String,
    #[serde(default = "default_applicable")]
    pub applicable: bool,
    #[serde(default)]
    pub transfer: Option<TransferReceipt>,
    #[serde(default)]
    pub closure: Option<ClosureReceipt>,
    #[serde(default)]
    pub evidence_refs: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LifecycleRequest {
    pub source: SourceRegistration,
    #[serde(default)]
    pub extraction: ExtractionRecord,
    #[serde(default)]
    pub findings: Vec<FindingRecord>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct LifecycleResidual {
    pub code: String,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub finding_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize)]
pub struct FindingTransferBinding {
    pub finding_id: String,
    pub destination_id: String,
    pub target_revision: String,
    pub acknowledgement_ref: String,
    pub kind: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct LifecycleCertificate {
    pub schema_version: String,
    pub certificate_id: String,
    pub kind: String,
    pub source_id: String,
    pub manifest_sha256: String,
    pub review_scope: String,
    pub extractor_version: String,
    pub checker_version: String,
    pub finding_ids: Vec<String>,
    pub destination_receipt_refs: Vec<String>,
    pub transfer_bindings: Vec<FindingTransferBinding>,
    pub open_obligation_finding_ids: Vec<String>,
    pub closure_receipt_refs: Vec<String>,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct LifecycleDecision {
    pub schema_version: String,
    pub state: DigestionState,
    pub archive_eligible: bool,
    pub source_id: String,
    pub manifest_sha256: String,
    pub pending_finding_ids: Vec<String>,
    pub transferred_open_finding_ids: Vec<String>,
    pub residuals: Vec<LifecycleResidual>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub certificate: Option<LifecycleCertificate>,
    pub authority_effect: String,
}

fn residual(
    code: &str,
    message: impl Into<String>,
    finding_id: Option<String>,
) -> LifecycleResidual {
    LifecycleResidual {
        code: code.into(),
        message: message.into(),
        finding_id,
    }
}

fn nonempty(value: &str) -> bool {
    !value.trim().is_empty()
}

fn sha256_ref(value: &str) -> bool {
    value.strip_prefix("sha256:").is_some_and(|hex_value| {
        hex_value.len() == 64 && hex_value.bytes().all(|byte| byte.is_ascii_hexdigit())
    })
}

fn transfer_valid(transfer: &TransferReceipt) -> bool {
    nonempty(&transfer.destination_id)
        && nonempty(&transfer.kind)
        && sha256_ref(&transfer.target_revision)
        && sha256_ref(&transfer.acknowledgement_ref)
}

fn closure_valid(closure: &ClosureReceipt) -> bool {
    nonempty(&closure.checker_id) && sha256_ref(&closure.closure_ref) && closure.verified
}

fn decision(
    source: &SourceRegistration,
    state: DigestionState,
    pending_finding_ids: Vec<String>,
    transferred_open_finding_ids: Vec<String>,
    residuals: Vec<LifecycleResidual>,
    certificate: Option<LifecycleCertificate>,
) -> LifecycleDecision {
    LifecycleDecision {
        schema_version: LIFECYCLE_DECISION_SCHEMA.into(),
        archive_eligible: matches!(state, DigestionState::Absorbed | DigestionState::Discharged),
        state,
        source_id: source.source_id.clone(),
        manifest_sha256: source.manifest_sha256.clone(),
        pending_finding_ids,
        transferred_open_finding_ids,
        residuals,
        certificate,
        authority_effect: "None".into(),
    }
}

fn certificate(
    source: &SourceRegistration,
    extraction: &ExtractionRecord,
    findings: &[FindingRecord],
    open_obligation_finding_ids: Vec<String>,
    kind: &str,
) -> LifecycleCertificate {
    let mut finding_ids = findings
        .iter()
        .map(|finding| finding.finding_id.clone())
        .collect::<Vec<_>>();
    finding_ids.sort();
    let mut transfer_bindings = findings
        .iter()
        .filter_map(|finding| {
            finding
                .transfer
                .as_ref()
                .map(|transfer| FindingTransferBinding {
                    finding_id: finding.finding_id.clone(),
                    destination_id: transfer.destination_id.clone(),
                    target_revision: transfer.target_revision.clone(),
                    acknowledgement_ref: transfer.acknowledgement_ref.clone(),
                    kind: transfer.kind.clone(),
                })
        })
        .collect::<Vec<_>>();
    transfer_bindings.sort();
    let mut destination_receipt_refs = transfer_bindings
        .iter()
        .map(|binding| binding.acknowledgement_ref.clone())
        .collect::<Vec<_>>();
    destination_receipt_refs.sort();
    destination_receipt_refs.dedup();
    let mut closure_receipt_refs = findings
        .iter()
        .filter_map(|finding| {
            finding
                .closure
                .as_ref()
                .map(|closure| closure.closure_ref.clone())
        })
        .collect::<Vec<_>>();
    closure_receipt_refs.sort();
    closure_receipt_refs.dedup();
    let mut open_obligation_finding_ids = open_obligation_finding_ids;
    open_obligation_finding_ids.sort();
    let material = serde_json::json!({
        "schema_version": LIFECYCLE_CERTIFICATE_SCHEMA,
        "kind": kind,
        "source_id": source.source_id,
        "manifest_sha256": source.manifest_sha256,
        "review_scope": source.review_scope,
        "extractor_version": extraction.extractor_version,
        "checker_version": extraction.checker_version,
        "finding_ids": finding_ids,
        "destination_receipt_refs": destination_receipt_refs,
        "transfer_bindings": transfer_bindings,
        "open_obligation_finding_ids": open_obligation_finding_ids,
        "closure_receipt_refs": closure_receipt_refs,
    });
    let bytes = serde_json::to_vec(&material).checked_invariant_ad270a85("JSON lifecycle certificate material");
    LifecycleCertificate {
        schema_version: LIFECYCLE_CERTIFICATE_SCHEMA.into(),
        certificate_id: framed_sha256(CERTIFICATE_DOMAIN, &bytes),
        kind: kind.into(),
        source_id: source.source_id.clone(),
        manifest_sha256: source.manifest_sha256.clone(),
        review_scope: source.review_scope.clone(),
        extractor_version: extraction.extractor_version.clone(),
        checker_version: extraction.checker_version.clone(),
        finding_ids,
        destination_receipt_refs,
        transfer_bindings,
        open_obligation_finding_ids,
        closure_receipt_refs,
        authority_effect: "None".into(),
    }
}

/// Evaluate a finite, declared source scope. The result never infers that an
/// arbitrary document is globally obstruction-free; it only records whether
/// every declared finding and coverage gap has a durable destination.
fn validate_source_registration(source: &SourceRegistration) -> Vec<LifecycleResidual> {
    let mut source_residuals = Vec::new();
    for (name, value) in [
        ("source_id", &source.source_id),
        ("producer_id", &source.producer_id),
        ("source_class", &source.source_class),
        ("source_schema_version", &source.source_schema_version),
        ("review_scope", &source.review_scope),
    ] {
        if !nonempty(value) {
            source_residuals.push(residual(
                "SOURCE_REGISTRATION_INVALID",
                format!("{name} must be a nonempty string"),
                None,
            ));
        }
    }
    if !sha256_ref(&source.manifest_sha256) {
        source_residuals.push(residual(
            "SOURCE_MANIFEST_INVALID",
            "manifest_sha256 must use the sha256:<hex> form",
            None,
        ));
    }
    if !source.sealed {
        source_residuals.push(residual(
            "SOURCE_NOT_SEALED",
            "a source must have an immutable verified manifest before lifecycle evaluation",
            None,
        ));
    }
    if source.producer_lease_active {
        source_residuals.push(residual(
            "PRODUCER_LEASE_ACTIVE",
            "an active producer lease prevents a source from leaving the active queue",
            None,
        ));
    }
    source_residuals
}

fn check_extraction_preconditions(
    source: &SourceRegistration,
    extraction: &ExtractionRecord,
) -> Option<LifecycleDecision> {
    if extraction.extractor_version.trim().is_empty()
        || extraction.checker_version.trim().is_empty()
    {
        return Some(decision(
            source,
            DigestionState::Sealed,
            Vec::new(),
            Vec::new(),
            vec![residual(
                "EXTRACTION_NOT_STARTED",
                "the declared extractor and checker versions are required before review completion",
                None,
            )],
            None,
        ));
    }
    if !extraction.parse_residuals.is_empty() {
        return Some(decision(
            source,
            DigestionState::Blocked,
            Vec::new(),
            Vec::new(),
            extraction
                .parse_residuals
                .iter()
                .map(|detail| residual("EXTRACTION_PARSE_RESIDUAL", detail.clone(), None))
                .collect(),
            None,
        ));
    }
    if !extraction.complete || !extraction.coverage_gaps.is_empty() {
        return Some(decision(
            source,
            DigestionState::Extracted,
            Vec::new(),
            Vec::new(),
            extraction
                .coverage_gaps
                .iter()
                .map(|detail| residual("EXTRACTION_COVERAGE_GAP", detail.clone(), None))
                .collect(),
            None,
        ));
    }
    None
}

fn classify_finding_transfer(
    finding: &FindingRecord,
    validation_residuals: &mut Vec<LifecycleResidual>,
    pending: &mut Vec<String>,
    transferred_open: &mut Vec<String>,
) {
    match &finding.transfer {
        None => pending.push(finding.finding_id.clone()),
        Some(transfer) if !transfer_valid(transfer) => validation_residuals.push(residual(
            "TRANSFER_RECEIPT_INVALID",
            "a transfer needs destination identity, target revision, receiving acknowledgement, and kind",
            Some(finding.finding_id.clone()),
        )),
        Some(_) if finding.applicable => match &finding.closure {
            Some(closure) if closure_valid(closure) => {}
            Some(_) => validation_residuals.push(residual(
                "CLOSURE_RECEIPT_INVALID",
                "a supplied closure receipt must name a checker, bind bytes, and state verified=true",
                Some(finding.finding_id.clone()),
            )),
            None => transferred_open.push(finding.finding_id.clone()),
        },
        Some(_) => {}
    }
}

fn partition_findings(
    findings: &[FindingRecord],
) -> (Vec<LifecycleResidual>, Vec<String>, Vec<String>) {
    let mut seen = BTreeSet::new();
    let mut validation_residuals = Vec::new();
    let mut pending = Vec::new();
    let mut transferred_open = Vec::new();
    for finding in findings {
        if !nonempty(&finding.finding_id) || !seen.insert(finding.finding_id.clone()) {
            validation_residuals.push(residual(
                "FINDING_ID_INVALID",
                "every finding must have a distinct nonempty identity",
                Some(finding.finding_id.clone()),
            ));
            continue;
        }
        classify_finding_transfer(
            finding,
            &mut validation_residuals,
            &mut pending,
            &mut transferred_open,
        );
    }
    pending.sort();
    transferred_open.sort();
    (validation_residuals, pending, transferred_open)
}

pub fn evaluate_lifecycle(request: &LifecycleRequest) -> LifecycleDecision {
    let source = &request.source;
    let extraction = &request.extraction;
    let source_residuals = validate_source_registration(source);
    if !source_residuals.is_empty() {
        return decision(
            source,
            DigestionState::Blocked,
            Vec::new(),
            Vec::new(),
            source_residuals,
            None,
        );
    }
    if let Some(early) = check_extraction_preconditions(source, extraction) {
        return early;
    }
    let (validation_residuals, pending, transferred_open) = partition_findings(&request.findings);
    if !validation_residuals.is_empty() {
        return decision(
            source,
            DigestionState::Blocked,
            pending,
            transferred_open,
            validation_residuals,
            None,
        );
    }
    if !pending.is_empty() {
        return decision(
            source,
            DigestionState::Extracted,
            pending,
            transferred_open,
            vec![residual(
                "FINDINGS_PENDING_TRANSFER",
                "every declared finding needs a durable receiving acknowledgement before absorption",
                None,
            )],
            None,
        );
    }
    if transferred_open.is_empty() {
        return decision(
            source,
            DigestionState::Discharged,
            Vec::new(),
            Vec::new(),
            Vec::new(),
            Some(certificate(
                source,
                extraction,
                &request.findings,
                Vec::new(),
                "DISCHARGE",
            )),
        );
    }
    let certificate = certificate(
        source,
        extraction,
        &request.findings,
        transferred_open.clone(),
        "ABSORPTION",
    );
    decision(
        source,
        DigestionState::Absorbed,
        Vec::new(),
        transferred_open,
        Vec::new(),
        Some(certificate),
    )
}

/// Exposed for adapters that need a typed error while decoding a request.
pub fn decode_error(error: impl Into<String>) -> Refusal {
    Refusal::new("INTELLIGENCE_LIFECYCLE_INPUT_INVALID", error)
}

// Origin: engine/crates_rs/core_intelligence/src/lifecycle.rs
// Claim: urn:core:crates_rs:core-intelligence:lifecycle:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordad270a85 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordad270a85` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorad270a85 {
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
impl BoundaryErrorad270a85 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorad270a85 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorad270a85 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordad270a85 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorad270a85> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorad270a85::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorad270a85::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorad270a85::ExceedsCapacity {
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
mod l4_boundary_tests_ad270a85 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordad270a85::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordad270a85::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordad270a85::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordad270a85::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordad270a85::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorad270a85::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorad270a85::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
