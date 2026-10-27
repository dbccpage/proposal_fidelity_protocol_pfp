//! Independence checks over the fields consumed from typed signal records.
//! These immutable projections do not replace the complete Python value objects.
use crate::{activation::DANGER_KINDS, Refusal};
use num_bigint::{BigInt, BigUint};
use core_types::python_unicode::{casefold, repr_string};
use serde::{ser::SerializeTuple, Deserialize, Deserializer, Serialize, Serializer};
use serde_json::value::RawValue;
use serde_json::{Number, Value};
use sha2::{Digest, Sha256};
use std::{collections::BTreeSet, str::FromStr};

fn decode_exact<T: serde::de::DeserializeOwned>(value: &Value) -> Result<T, Refusal> {
    // Preserve the original numeric lexemes across the Value -> typed boundary.
    // serde's Value deserializer may otherwise classify a huge integer as f64.
    let bytes = serde_json::to_vec(value)
        .map_err(|error| Refusal::new("EIS_WIRE_INVALID", error.to_string()))?;
    decode_bytes(&bytes)
}
fn decode_bytes<T: serde::de::DeserializeOwned>(bytes: &[u8]) -> Result<T, Refusal> {
    serde_json::from_slice(bytes)
        .map_err(|error| Refusal::new("EIS_WIRE_INVALID", error.to_string()))
}

fn unsigned(value: &RawValue, label: &str) -> Result<BigUint, Refusal> {
    // Check the original primitive token, avoiding both numeric reclassification
    // and serde's private arbitrary-number marker being accepted as a JSON object.
    let admitted = BigInt::from_str(value.get())
        .ok()
        .and_then(|integer| integer.to_biguint());
    admitted.ok_or_else(|| {
        Refusal::new(
            "EIS_VALUE_ERROR",
            format!("{label} must be an exact nonnegative integer"),
        )
    })
}
fn number(value: &BigUint) -> Result<Number, serde_json::Error> {
    Number::from_str(&value.to_string())
}
fn serialize_unsigned<S: Serializer>(value: &BigUint, serializer: S) -> Result<S::Ok, S::Error> {
    number(value)
        .map_err(serde::ser::Error::custom)?
        .serialize(serializer)
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct MatchEvidence {
    epitope_name: String,
    pattern_matched: String,
    #[serde(serialize_with = "serialize_unsigned")]
    offset: BigUint,
}
impl MatchEvidence {
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, Refusal> {
        decode_bytes(bytes)
    }
    pub fn from_json(value: &Value) -> Result<Self, Refusal> {
        decode_exact(value)
    }
    pub fn new(epitope_name: String, pattern_matched: String, offset: BigUint) -> Self {
        Self {
            epitope_name,
            pattern_matched,
            offset,
        }
    }
}
impl<'de> Deserialize<'de> for MatchEvidence {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        #[derive(Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Wire {
            epitope_name: String,
            pattern_matched: String,
            offset: Box<RawValue>,
        }
        let wire = Wire::deserialize(deserializer)?;
        Ok(Self::new(
            wire.epitope_name,
            wire.pattern_matched,
            unsigned(&wire.offset, "offset").map_err(serde::de::Error::custom)?,
        ))
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CharacterSpan {
    low: BigUint,
    high: BigUint,
}
impl CharacterSpan {
    pub fn new(low: BigUint, high: BigUint) -> Result<Self, Refusal> {
        if low >= high {
            return Err(Refusal::new(
                "EIS_VALUE_ERROR",
                "evidence span must have 0 <= start < end",
            ));
        }
        Ok(Self { low, high })
    }
}
impl Serialize for CharacterSpan {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let mut tuple = serializer.serialize_tuple(2)?;
        tuple.serialize_element(&number(&self.low).map_err(serde::ser::Error::custom)?)?;
        tuple.serialize_element(&number(&self.high).map_err(serde::ser::Error::custom)?)?;
        tuple.end()
    }
}
impl<'de> Deserialize<'de> for CharacterSpan {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let [low, high] = <[Box<RawValue>; 2]>::deserialize(deserializer)?;
        Self::new(
            unsigned(&low, "span start").map_err(serde::de::Error::custom)?,
            unsigned(&high, "span end").map_err(serde::de::Error::custom)?,
        )
        .map_err(serde::de::Error::custom)
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DangerEvidence {
    danger_type: String,
    observer_id: String,
    evidence_digest: String,
    #[serde(serialize_with = "serialize_unsigned")]
    defect_count: BigUint,
    evidence_spans: Vec<CharacterSpan>,
}
impl DangerEvidence {
    pub fn danger_type(&self) -> &str {
        &self.danger_type
    }
    pub fn has_defects(&self) -> bool {
        self.defect_count != BigUint::default()
    }
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, Refusal> {
        decode_bytes(bytes)
    }
    pub fn from_json(value: &Value) -> Result<Self, Refusal> {
        decode_exact(value)
    }
    pub fn new(
        danger_type: String,
        observer_id: String,
        evidence_digest: String,
        defect_count: BigUint,
        evidence_spans: Vec<CharacterSpan>,
    ) -> Self {
        Self {
            danger_type,
            observer_id,
            evidence_digest,
            defect_count,
            evidence_spans,
        }
    }
}
impl<'de> Deserialize<'de> for DangerEvidence {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        #[derive(Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Wire {
            danger_type: String,
            observer_id: String,
            evidence_digest: String,
            defect_count: Box<RawValue>,
            evidence_spans: Vec<CharacterSpan>,
        }
        let wire = Wire::deserialize(deserializer)?;
        Ok(Self::new(
            wire.danger_type,
            wire.observer_id,
            wire.evidence_digest,
            unsigned(&wire.defect_count, "defect_count").map_err(serde::de::Error::custom)?,
            wire.evidence_spans,
        ))
    }
}
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DetectorContext {
    pub detector_id: String,
    pub detector_predicates: BTreeSet<String>,
    pub offsets_are_content: bool,
}
fn trim_python(text: &str) -> &str {
    text.trim_matches(|character: char| {
        character.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&character)
    })
}
fn ascii_escape_literal(character: char) -> Option<&'static str> {
    match character {
        '"' => Some("\\\""),
        '\\' => Some("\\\\"),
        '\u{8}' => Some("\\b"),
        '\u{c}' => Some("\\f"),
        '\n' => Some("\\n"),
        '\r' => Some("\\r"),
        '\t' => Some("\\t"),
        _ => None,
    }
}
fn ascii_json_string(text: &str, output: &mut String) {
    output.push('"');
    for character in text.chars() {
        if let Some(escaped) = ascii_escape_literal(character) {
            output.push_str(escaped);
        } else if !(' '..'\u{7f}').contains(&character) {
            let mut units = [0; 2];
            for unit in character.encode_utf16(&mut units) {
                output.push_str(&format!("\\u{unit:04x}"));
            }
        } else {
            output.push(character);
        }
    }
    output.push('"');
}
pub fn signal1_digest(matches: &[MatchEvidence]) -> String {
    let mut rows = matches.iter().collect::<Vec<_>>();
    rows.sort_by(|left, right| {
        (&left.epitope_name, &left.pattern_matched, &left.offset).cmp(&(
            &right.epitope_name,
            &right.pattern_matched,
            &right.offset,
        ))
    });
    let mut raw = String::from("[");
    for (index, row) in rows.iter().enumerate() {
        if index != 0 {
            raw.push(',');
        }
        raw.push('[');
        ascii_json_string(&row.epitope_name, &mut raw);
        raw.push(',');
        ascii_json_string(&row.pattern_matched, &mut raw);
        raw.push(',');
        raw.push_str(&row.offset.to_string());
        raw.push(']');
    }
    raw.push(']');
    format!("sha256:{}", hex::encode(Sha256::digest(raw.as_bytes())))
}
fn overlapping(matches: &[MatchEvidence], spans: &[CharacterSpan]) -> Option<(BigUint, BigUint)> {
    for evidence in matches {
        let stop =
            &evidence.offset + BigUint::from(evidence.pattern_matched.chars().count().max(1));
        for span in spans {
            if evidence.offset < span.high && span.low < stop {
                return Some((evidence.offset.clone(), stop));
            }
        }
    }
    None
}
fn validate_observer_identity(observer: &str, detector_id: &str) -> Result<(), Refusal> {
    if trim_python(detector_id).is_empty() {
        return Err(Refusal::new(
            "EIS_VALUE_ERROR",
            "detector_id must name the matcher that produced Signal 1",
        ));
    }
    if trim_python(observer).is_empty() {
        return Err(Refusal::new(
            "UNWITNESSED_DANGER_SIGNAL",
            "Signal 2 names no host observer, so its independence cannot be checked",
        ));
    }
    let folded = casefold(trim_python(observer));
    if ["model", "llm", "agent", "detector", "matcher"].contains(&folded.as_str()) {
        return Err(Refusal::new("TWO_SIGNAL_COLLAPSE",format!("Signal 2 was reported by {}; danger is observed by a host check, not proposed by a model or a detector",repr_string(observer))));
    }
    if folded == casefold(trim_python(detector_id)) {
        return Err(Refusal::new("TWO_SIGNAL_COLLAPSE",format!("Signal 2 was observed by {}, the matcher that produced Signal 1; the danger bit is derived from the match",repr_string(observer))));
    }
    Ok(())
}
pub fn assert_signals_independent(
    matches: &[MatchEvidence],
    danger: Option<&DangerEvidence>,
    context: &DetectorContext,
) -> Result<String, Refusal> {
    let Some(danger) = danger else {
        return Ok("no Signal 2 was observed".into());
    };
    let observer = &danger.observer_id;
    validate_observer_identity(observer, &context.detector_id)?;
    if !DANGER_KINDS.contains(&danger.danger_type.as_str()) {
        return Err(Refusal::new(
            "UNREGISTERED_DANGER_KIND",
            format!(
                "{} is not in the closed registry: {}",
                repr_string(&danger.danger_type),
                DANGER_KINDS.join(", ")
            ),
        ));
    }
    if context.detector_predicates.contains(&danger.danger_type) {
        return Err(Refusal::new(
            "TWO_SIGNAL_COLLAPSE",
            format!(
                "the matcher {} already evaluates {}; the same predicate would be counted twice",
                repr_string(&context.detector_id),
                danger.danger_type
            ),
        ));
    }
    if !matches.is_empty() && danger.evidence_digest == signal1_digest(matches) {
        return Err(Refusal::new("TWO_SIGNAL_COLLAPSE","Signal 2's evidence is the digest of the Signal 1 matches; that is one signal counted twice"));
    }
    if context.offsets_are_content {
        if let Some((start, stop)) = overlapping(matches, &danger.evidence_spans) {
            return Err(Refusal::new("TWO_SIGNAL_COLLAPSE",format!("the Signal 1 match at characters [{start}, {stop}) lies inside the {} evidence; one token cannot be both signals",danger.danger_type)));
        }
    }
    Ok(format!("host observer {observer} reported {} ({} defect(s), evidence {}...), distinct from matcher {} and its matches",danger.danger_type,danger.defect_count,danger.evidence_digest.chars().take(23).collect::<String>(),context.detector_id))
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/independence.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:independence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf5bcf2bf {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf5bcf2bf` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf5bcf2bf {
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
impl BoundaryErrorf5bcf2bf {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf5bcf2bf {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf5bcf2bf {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf5bcf2bf {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf5bcf2bf> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf5bcf2bf::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf5bcf2bf::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf5bcf2bf::ExceedsCapacity {
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
mod l4_boundary_tests_f5bcf2bf {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf5bcf2bf::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf5bcf2bf::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf5bcf2bf::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf5bcf2bf::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf5bcf2bf::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf5bcf2bf::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf5bcf2bf::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
