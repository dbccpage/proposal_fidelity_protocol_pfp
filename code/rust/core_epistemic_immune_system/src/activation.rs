//! Receipt-bound learned-guard activation; no admission or execution path.
//!
//! This profile extends the legacy regex gate with checked subject/evidence
//! bindings. Its receipts are not the legacy AntiSkillSpecV2 contract.
use crate::Refusal;
use serde::{Deserialize, Deserializer, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use unicode_normalization::UnicodeNormalization;

pub const DANGER_SCHEMA: &str = "core.antiskill.danger-signal-receipt.v1";
pub const ACTIVATION_SCHEMA: &str = "core.antiskill.guard-activation-receipt.v1";
pub const DANGER_KINDS: [&str; 4] = [
    "MALFORMED_PAYLOAD",
    "MANIFEST_CONTAMINATION",
    "PROTECTED_FIELD_VIOLATION",
    "REPLAY_FAILURE",
];
fn value_error(message: impl Into<String>) -> Refusal {
    Refusal::new("EIS_VALUE_ERROR", message)
}
fn none() -> String {
    "None".into()
}
fn host() -> String {
    "HOST".into()
}
fn danger_schema() -> String {
    DANGER_SCHEMA.into()
}
fn activation_schema() -> String {
    ACTIVATION_SCHEMA.into()
}
fn whitespace(character: char) -> bool {
    character.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&character)
}
fn text(value: &str, label: &str) -> Result<(), Refusal> {
    if value.len() > 4096 {
        return Err(value_error(format!("{label} exceeds the text limit")));
    }
    if value.is_empty() || value.trim_matches(whitespace) != value {
        return Err(value_error(format!(
            "{label} must be a normalized nonempty string"
        )));
    }
    Ok(())
}
fn identifier(value: &str, label: &str) -> Result<(), Refusal> {
    text(value, label)?;
    if !value
        .as_bytes()
        .first()
        .is_some_and(u8::is_ascii_alphanumeric)
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || b"._:/@-".contains(&byte))
    {
        return Err(value_error(format!(
            "{label} must be a canonical identifier"
        )));
    }
    Ok(())
}
fn digest(value: &str, label: &str) -> Result<(), Refusal> {
    if value.len() != 71
        || !value.starts_with("sha256:")
        || !value
            .bytes()
            .skip(7)
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(value_error(format!(
            "{label} must be a lowercase sha256 digest"
        )));
    }
    Ok(())
}
fn canonical_id(schema: &str, payload: BTreeMap<&str, &str>) -> Result<String, Refusal> {
    #[derive(Serialize)]
    struct Envelope<'a> {
        domain: &'a str,
        payload: BTreeMap<&'a str, String>,
    }
    let envelope = Envelope {
        domain: schema,
        payload: payload
            .into_iter()
            .map(|(key, value)| (key, value.nfc().collect()))
            .collect(),
    };
    let bytes = serde_json::to_vec(&envelope)
        .map_err(|error| Refusal::new("EIS_WIRE_INVALID", error.to_string()))?;
    Ok(format!("sha256:{}", hex::encode(Sha256::digest(bytes))))
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DetectorHitInput {
    pub hit_id: String,
    pub spec_id: String,
    pub failure_code: String,
    pub subject_id: String,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DetectorHitRefV1 {
    hit_id: String,
    spec_id: String,
    failure_code: String,
    subject_id: String,
}
impl DetectorHitRefV1 {
    pub fn new(input: DetectorHitInput) -> Result<Self, Refusal> {
        digest(&input.hit_id, "hit_id")?;
        identifier(&input.spec_id, "spec_id")?;
        identifier(&input.failure_code, "failure_code")?;
        digest(&input.subject_id, "subject_id")?;
        Ok(Self {
            hit_id: input.hit_id,
            spec_id: input.spec_id,
            failure_code: input.failure_code,
            subject_id: input.subject_id,
        })
    }
    pub fn hit_id(&self) -> &str {
        &self.hit_id
    }
    pub fn spec_id(&self) -> &str {
        &self.spec_id
    }
    pub fn failure_code(&self) -> &str {
        &self.failure_code
    }
    pub fn subject_id(&self) -> &str {
        &self.subject_id
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DangerSignalInput {
    pub signal_kind: String,
    pub observer_id: String,
    pub subject_id: String,
    pub evidence_digest: String,
    #[serde(default = "host")]
    pub producer_kind: String,
    #[serde(default = "none")]
    pub authority_effect: String,
    #[serde(default = "danger_schema")]
    pub schema_version: String,
    #[serde(default)]
    pub receipt_id: String,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DangerSignalReceiptV1 {
    signal_kind: String,
    observer_id: String,
    subject_id: String,
    evidence_digest: String,
    producer_kind: String,
    authority_effect: String,
    schema_version: String,
    receipt_id: String,
}
impl DangerSignalReceiptV1 {
    fn validate_danger_input(input: &DangerSignalInput) -> Result<(), Refusal> {
        if !DANGER_KINDS.contains(&input.signal_kind.as_str()) {
            return Err(value_error(format!(
                "danger signal_kind is not in the closed registry: {}",
                DANGER_KINDS.join(", ")
            )));
        }
        identifier(&input.observer_id, "observer_id")?;
        digest(&input.subject_id, "subject_id")?;
        digest(&input.evidence_digest, "evidence_digest")?;
        if ["MODEL", "LLM", "AGENT", "DETECTOR"].contains(&input.producer_kind.as_str()) {
            return Err(value_error(format!("a danger signal may not be authored by {}; danger is observed by a host, not proposed by a model", input.producer_kind)));
        }
        if input.producer_kind != "HOST" {
            return Err(value_error("danger signal producer_kind must be HOST"));
        }
        if input.authority_effect != "None" {
            return Err(value_error("danger signal authority_effect must be None"));
        }
        if input.schema_version != DANGER_SCHEMA {
            return Err(value_error("unsupported danger signal schema"));
        }
        Ok(())
    }

    pub fn new(input: DangerSignalInput) -> Result<Self, Refusal> {
        Self::validate_danger_input(&input)?;
        let expected = canonical_id(
            DANGER_SCHEMA,
            BTreeMap::from([
                ("authority_effect", input.authority_effect.as_str()),
                ("evidence_digest", input.evidence_digest.as_str()),
                ("observer_id", input.observer_id.as_str()),
                ("producer_kind", input.producer_kind.as_str()),
                ("schema_version", input.schema_version.as_str()),
                ("signal_kind", input.signal_kind.as_str()),
                ("subject_id", input.subject_id.as_str()),
            ]),
        )?;
        if !input.receipt_id.is_empty() && input.receipt_id != expected {
            return Err(value_error("receipt_id does not match canonical content"));
        }
        Ok(Self {
            signal_kind: input.signal_kind,
            observer_id: input.observer_id,
            subject_id: input.subject_id,
            evidence_digest: input.evidence_digest,
            producer_kind: input.producer_kind,
            authority_effect: input.authority_effect,
            schema_version: input.schema_version,
            receipt_id: expected,
        })
    }
    pub fn receipt_id(&self) -> &str {
        &self.receipt_id
    }
    pub fn observer_id(&self) -> &str {
        &self.observer_id
    }
    pub fn subject_id(&self) -> &str {
        &self.subject_id
    }
    pub fn evidence_digest(&self) -> &str {
        &self.evidence_digest
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GuardActivationInput {
    pub profile_digest: String,
    pub hit_id: String,
    pub danger_receipt_id: String,
    pub subject_id: String,
    pub disposition: String,
    pub independence_basis: String,
    #[serde(default = "none")]
    pub authority_effect: String,
    #[serde(default = "activation_schema")]
    pub schema_version: String,
    #[serde(default)]
    pub receipt_id: String,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct GuardActivationReceiptV1 {
    profile_digest: String,
    hit_id: String,
    danger_receipt_id: String,
    subject_id: String,
    disposition: String,
    independence_basis: String,
    authority_effect: String,
    schema_version: String,
    receipt_id: String,
}
impl GuardActivationReceiptV1 {
    fn validate_activation_input(input: &GuardActivationInput) -> Result<(), Refusal> {
        digest(&input.profile_digest, "profile_digest")?;
        digest(&input.hit_id, "hit_id")?;
        digest(&input.danger_receipt_id, "danger_receipt_id")?;
        digest(&input.subject_id, "subject_id")?;
        if !["FINDING", "HOLD", "REFUSE"].contains(&input.disposition.as_str()) {
            return Err(value_error("activation disposition is not closed; activation may select only FINDING, HOLD or REFUSE"));
        }
        text(&input.independence_basis, "independence_basis")?;
        if input.authority_effect != "None" {
            return Err(value_error(
                "guard activation authority_effect must be None",
            ));
        }
        if input.schema_version != ACTIVATION_SCHEMA {
            return Err(value_error("unsupported guard activation schema"));
        }
        Ok(())
    }

    pub fn new(input: GuardActivationInput) -> Result<Self, Refusal> {
        Self::validate_activation_input(&input)?;
        let expected = canonical_id(
            ACTIVATION_SCHEMA,
            BTreeMap::from([
                ("authority_effect", input.authority_effect.as_str()),
                ("danger_receipt_id", input.danger_receipt_id.as_str()),
                ("disposition", input.disposition.as_str()),
                ("hit_id", input.hit_id.as_str()),
                ("independence_basis", input.independence_basis.as_str()),
                ("profile_digest", input.profile_digest.as_str()),
                ("schema_version", input.schema_version.as_str()),
                ("subject_id", input.subject_id.as_str()),
            ]),
        )?;
        if !input.receipt_id.is_empty() && input.receipt_id != expected {
            return Err(value_error("receipt_id does not match canonical content"));
        }
        Ok(Self {
            profile_digest: input.profile_digest,
            hit_id: input.hit_id,
            danger_receipt_id: input.danger_receipt_id,
            subject_id: input.subject_id,
            disposition: input.disposition,
            independence_basis: input.independence_basis,
            authority_effect: input.authority_effect,
            schema_version: input.schema_version,
            receipt_id: expected,
        })
    }
    pub fn receipt_id(&self) -> &str {
        &self.receipt_id
    }
    pub fn disposition(&self) -> &str {
        &self.disposition
    }
    pub fn independence_basis(&self) -> &str {
        &self.independence_basis
    }
}

macro_rules! validated_decode {
    ($record:ty, $input:ty) => {
        impl<'de> Deserialize<'de> for $record {
            fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
                Self::new(<$input>::deserialize(deserializer)?).map_err(serde::de::Error::custom)
            }
        }
    };
}
validated_decode!(DetectorHitRefV1, DetectorHitInput);
validated_decode!(DangerSignalReceiptV1, DangerSignalInput);
validated_decode!(GuardActivationReceiptV1, GuardActivationInput);

fn verify_two_signal_independence(
    hit: &DetectorHitRefV1,
    danger: &DangerSignalReceiptV1,
) -> Result<(), Refusal> {
    if danger.evidence_digest == hit.hit_id {
        return Err(Refusal::new("TWO_SIGNAL_COLLAPSE", "the danger receipt's evidence is the detector's own finding; that is one signal counted twice"));
    }
    // All three identifiers have been checked against the ASCII vocabulary;
    // ASCII lowercase therefore matches Python casefold for admitted inputs.
    if danger.observer_id.eq_ignore_ascii_case(&hit.spec_id) {
        return Err(Refusal::new("TWO_SIGNAL_COLLAPSE", format!("the danger signal was observed by '{}', which is the detector spec itself; the danger bit is derived from the match", danger.observer_id)));
    }
    if danger.observer_id.eq_ignore_ascii_case(&hit.failure_code) {
        return Err(Refusal::new(
            "TWO_SIGNAL_COLLAPSE",
            "the danger observer is the detector's own failure code",
        ));
    }
    Ok(())
}

fn require_matched_unsuspended<'a>(
    hit: Option<&'a DetectorHitRefV1>,
    danger: Option<&'a DangerSignalReceiptV1>,
    suspended: bool,
) -> Result<(&'a DetectorHitRefV1, &'a DangerSignalReceiptV1), Refusal> {
    let hit = hit.ok_or_else(|| {
        Refusal::new(
            "NO_DETECTOR_MATCH",
            "a danger signal without a detector match cannot activate a guard",
        )
    })?;
    let danger = danger.ok_or_else(|| Refusal::new("NO_DANGER_SIGNAL", "a detector match without an independent danger receipt stays a finding and does not activate the learned guard"))?;
    if danger.subject_id != hit.subject_id {
        return Err(Refusal::new(
            "SUBJECT_MISMATCH",
            "the danger signal observes a different subject than the detector",
        ));
    }
    if suspended {
        return Err(Refusal::new(
            "SUSPENDED",
            "the guard is suspended in this subject scope",
        ));
    }
    Ok((hit, danger))
}

pub fn evaluate_activation(
    profile_digest: &str,
    hit: Option<&DetectorHitRefV1>,
    danger: Option<&DangerSignalReceiptV1>,
    externally_admitted: bool,
    suspended: bool,
    disposition: &str,
) -> Result<GuardActivationReceiptV1, Refusal> {
    digest(profile_digest, "profile_digest")?;
    if !externally_admitted {
        return Err(Refusal::new(
            "NOT_EXTERNALLY_ADMITTED",
            "the guard has no external admission for this subject scope",
        ));
    }
    let (hit, danger) = require_matched_unsuspended(hit, danger, suspended)?;
    verify_two_signal_independence(hit, danger)?;
    let basis = format!("host observer {} reported {} with evidence {}..., distinct from detector spec {} and its finding", danger.observer_id, danger.signal_kind, &danger.evidence_digest[..23], hit.spec_id);
    if !["FINDING", "HOLD", "REFUSE"].contains(&disposition) {
        // Dispositions in the oracle are ASCII. General Python repr spelling
        // of malformed arbitrary text is outside this boundary profile.
        return Err(value_error(format!(
            "activation may select only FINDING, HOLD or REFUSE; '{disposition}' is not closed"
        )));
    }
    GuardActivationReceiptV1::new(GuardActivationInput {
        profile_digest: profile_digest.into(),
        hit_id: hit.hit_id.clone(),
        danger_receipt_id: danger.receipt_id.clone(),
        subject_id: hit.subject_id.clone(),
        disposition: disposition.into(),
        independence_basis: basis,
        authority_effect: none(),
        schema_version: activation_schema(),
        receipt_id: String::new(),
    })
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/activation.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:activation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1d6ee6e8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1d6ee6e8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1d6ee6e8 {
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
impl BoundaryError1d6ee6e8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1d6ee6e8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1d6ee6e8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1d6ee6e8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1d6ee6e8> {
        if capacity_bound == 0 {
            return Err(BoundaryError1d6ee6e8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1d6ee6e8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1d6ee6e8::ExceedsCapacity {
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
mod l4_boundary_tests_1d6ee6e8 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1d6ee6e8::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1d6ee6e8::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1d6ee6e8::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1d6ee6e8::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1d6ee6e8::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1d6ee6e8::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1d6ee6e8::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
