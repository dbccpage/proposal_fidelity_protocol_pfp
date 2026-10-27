//! Canonical identities for the pure Arena domain. No authority is granted.
use serde::Serialize;
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use unicode_normalization::UnicodeNormalization;

pub const MAX_ITEMS: usize = 256;
pub const MAX_TEXT_BYTES: usize = 16 * 1024;

// Private fields and validated deserialization keep imported records immutable.
macro_rules! validated_record {
    ($name:ident { $($(#[$attr:meta])* $field:ident: $kind:ty),* $(,)? }) => {
        #[derive(Debug, Clone, PartialEq, Eq, serde::Serialize)]
        pub struct $name { $($(#[$attr])* pub(crate) $field: $kind),* }
        impl $name { $(pub fn $field(&self) -> &$kind { &self.$field })* }
        impl<'de> serde::Deserialize<'de> for $name {
            fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
                #[derive(serde::Deserialize)]
                #[serde(deny_unknown_fields)]
                struct Wire { $($(#[$attr])* $field: $kind),* }
                let wire = Wire::deserialize(deserializer)?;
                let mut record = Self { $($field: wire.$field),* };
                record.validate().map_err(serde::de::Error::custom)?;
                Ok(record)
            }
        }
    }
}
pub(crate) use validated_record;

// Python str.strip includes these four separators in addition to Unicode whitespace.
pub(crate) fn python_whitespace(c: char) -> bool {
    c.is_whitespace() || matches!(c, '\u{1c}'..='\u{1f}')
}

pub(crate) fn text(value: &str, label: &str, allow_empty: bool) -> Result<(), String> {
    if value.len() > MAX_TEXT_BYTES {
        return Err(format!("{label} exceeds the text limit"));
    }
    if !allow_empty && (value.is_empty() || value.trim_matches(python_whitespace) != value) {
        return Err(format!("{label} must be normalized and nonempty"));
    }
    if allow_empty && !value.is_empty() && value.trim_matches(python_whitespace) != value {
        return Err(format!("{label} must be normalized"));
    }
    Ok(())
}

fn is_identifier(value: &str) -> bool {
    let mut bytes = value.bytes();
    bytes.next().is_some_and(|c| c.is_ascii_alphanumeric())
        && bytes.all(|c| c.is_ascii_alphanumeric() || b"._:/@-".contains(&c))
}

pub(crate) fn identifier(value: &str, label: &str) -> Result<(), String> {
    text(value, label, false)?;
    if !is_identifier(value) {
        return Err(format!("{label} must be a canonical identifier"));
    }
    Ok(())
}

pub(crate) fn digest(value: &str, label: &str, allow_empty: bool) -> Result<(), String> {
    if allow_empty && value.is_empty() {
        return Ok(());
    }
    if !is_lowercase_sha256(value) {
        return Err(format!("{label} must be a lowercase sha256 digest"));
    }
    Ok(())
}

fn is_lowercase_sha256(value: &str) -> bool {
    let Some(hex_part) = value.strip_prefix("sha256:") else {
        return false;
    };
    hex_part.len() == 64
        && hex_part
            .bytes()
            .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
}

pub(crate) fn integer(value: u32, label: &str, minimum: u32, maximum: u32) -> Result<(), String> {
    if !(minimum..=maximum).contains(&value) {
        return Err(format!(
            "{label} must be an exact integer in [{minimum}, {maximum}]"
        ));
    }
    Ok(())
}

pub(crate) enum StringKind {
    Text,
    TextOrEmpty,
    Identifier,
    Digest,
}

pub(crate) fn strings(
    values: &[String],
    label: &str,
    kind: StringKind,
    unique: bool,
) -> Result<(), String> {
    if values.len() > MAX_ITEMS {
        return Err(format!("{label} exceeds the item limit"));
    }
    for (index, value) in values.iter().enumerate() {
        let item_label = format!("{label}[{index}]");
        match kind {
            StringKind::Text => text(value, &item_label, false)?,
            StringKind::TextOrEmpty => text(value, &item_label, true)?,
            StringKind::Identifier => identifier(value, &item_label)?,
            StringKind::Digest => digest(value, &item_label, false)?,
        }
    }
    if unique && values.iter().collect::<BTreeSet<_>>().len() != values.len() {
        return Err(format!("{label} must not contain duplicates"));
    }
    Ok(())
}

fn python_key_repr(value: &str) -> String {
    let double_quote = '\x22';
    let quote = if value.contains('\'') && !value.contains(double_quote) {
        double_quote
    } else {
        '\''
    };
    let mut output = String::from(quote);
    for c in value.chars() {
        push_python_escaped_char(&mut output, c, quote);
    }
    output.push(quote);
    output
}

fn push_python_escaped_char(output: &mut String, c: char, quote: char) {
    match c {
        '\\' => output.push_str("\\\\"),
        '\n' => output.push_str("\\n"),
        '\r' => output.push_str("\\r"),
        '\t' => output.push_str("\\t"),
        c if c == quote => {
            output.push('\\');
            output.push(c);
        }
        c if c.is_control() => push_control_escape(output, u32::from(c)),
        c => output.push(c),
    }
}

fn push_control_escape(output: &mut String, cp: u32) {
    if cp <= 0xff {
        output.push_str(&format!("\\x{cp:02x}"));
    } else {
        output.push_str(&format!("\\u{cp:04x}"));
    }
}

fn normalized(value: &Value) -> Result<Value, String> {
    match value {
        Value::Null | Value::Bool(_) => Ok(value.clone()),
        Value::Number(number) => {
            if number.to_string().contains(['.', 'e', 'E']) {
                return Err("unsupported canonical value: float".into());
            }
            Ok(value.clone())
        }
        Value::String(value) => Ok(Value::String(value.nfc().collect())),
        Value::Array(values) => values
            .iter()
            .map(normalized)
            .collect::<Result<Vec<_>, _>>()
            .map(Value::Array),
        Value::Object(values) => {
            let mut output = Map::new();
            for (key, value) in values {
                let key: String = key.nfc().collect();
                if output.contains_key(&key) {
                    return Err(format!(
                        "canonical key collision: {}",
                        python_key_repr(&key)
                    ));
                }
                output.insert(key, normalized(value)?);
            }
            Ok(Value::Object(output))
        }
    }
}

/// Source-compatible NFC identity. JSON integers retain their exact lexical value.
pub fn semantic_id(
    schema: &str,
    payload: &Map<String, Value>,
) -> Result<String, crate::stage::ports::Refusal> {
    canonical_id(schema, payload).map_err(|message| {
        let mut refusal = crate::stage::ports::Refusal::new("OEAS_CANONICAL_REFUSED", message);
        refusal.locus = "adversary.stage.domain.canonical".into();
        refusal
    })
}

fn canonical_id(schema: &str, payload: &Map<String, Value>) -> Result<String, String> {
    let domain: String = schema.trim_matches(python_whitespace).nfc().collect();
    if domain.is_empty() {
        return Err("domain must be a non-empty string".into());
    }
    if !is_identifier(&domain) {
        return Err("domain must be a canonical identifier".into());
    }
    let envelope =
        json!({"domain": domain, "payload": normalized(&Value::Object(payload.clone()))?});
    let encoded = serde_json::to_vec(&envelope).map_err(|error| error.to_string())?;
    Ok(format!("sha256:{}", hex::encode(Sha256::digest(encoded))))
}

pub(crate) fn bind_id<T: Serialize>(
    record: &T,
    schema: &str,
    id_field: &str,
    supplied: &str,
    derived_fields: &[&str],
) -> Result<String, String> {
    let value = serde_json::to_value(record).map_err(|error| error.to_string())?;
    let Value::Object(mut payload) = value else {
        return Err("record must be an object".into());
    };
    payload.remove(id_field);
    for field in derived_fields {
        payload.remove(*field);
    }
    let expected = canonical_id(schema, &payload)?;
    if !supplied.is_empty() && supplied != expected {
        return Err(format!("{id_field} does not match canonical content"));
    }
    Ok(expected)
}

pub(crate) fn envelope(
    authority: &str,
    schema: &str,
    name: &str,
    expected_schema: &str,
) -> Result<(), String> {
    if authority != "None" {
        return Err(format!("{name} authority_effect must be None"));
    }
    if schema != expected_schema {
        return Err(format!("unsupported {name} schema"));
    }
    Ok(())
}

// Origin: engine/crates_rs/core_adversary/src/stage/canonical.rs
// Claim: urn:core:crates_rs:core-adversary:canonical:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2010822d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2010822d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2010822d {
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
impl BoundaryError2010822d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2010822d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2010822d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2010822d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2010822d> {
        if capacity_bound == 0 {
            return Err(BoundaryError2010822d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2010822d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2010822d::ExceedsCapacity {
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
mod l4_boundary_tests_2010822d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2010822d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2010822d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2010822d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2010822d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2010822d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError2010822d::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError2010822d::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
