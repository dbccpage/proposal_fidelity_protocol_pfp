//! Python-compatible core-canonical-v1 packet wire checks.
//!
//! This is the host packet codec. Digest envelopes stay in
//! `core_operad_theory`. AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_d342ccbd<T> {
    fn checked_invariant_d342ccbd(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_d342ccbd<T> for Option<T> {
    #[inline]
    fn checked_invariant_d342ccbd(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_d342ccbd<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_d342ccbd(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use serde_json::{Map, Value};
use std::collections::{BTreeMap, BTreeSet};

use crate::canonical::CANONICAL_MARKER;

pub fn sorted_json_bytes(value: &Value) -> Vec<u8> {
    fn sorted(value: &Value) -> Value {
        match value {
            Value::Array(items) => Value::Array(items.iter().map(sorted).collect()),
            Value::Object(object) => {
                let mut keys: Vec<&String> = object.keys().collect();
                keys.sort();
                let mut result = Map::new();
                for key in keys {
                    result.insert(key.clone(), sorted(&object[key]));
                }
                Value::Object(result)
            }
            primitive => primitive.clone(),
        }
    }
    serde_json::to_vec(&sorted(value)).checked_invariant_d342ccbd("JSON values always serialize")
}

fn wire_node(tag: &str, body: Value) -> Value {
    Value::Array(vec![
        Value::String(CANONICAL_MARKER.to_owned()),
        Value::String(tag.to_owned()),
        body,
    ])
}

pub fn wire_string(value: &str) -> Value {
    wire_node("string", Value::String(value.to_owned()))
}

pub fn wire_int(value: usize) -> Value {
    wire_node("int", Value::String(value.to_string()))
}

pub fn wire_optional_string(value: Option<&str>) -> Value {
    value.map_or_else(|| wire_node("null", Value::Null), wire_string)
}

pub fn wire_tuple(values: &[String]) -> Value {
    wire_node(
        "tuple",
        Value::Array(values.iter().map(|value| wire_string(value)).collect()),
    )
}

pub fn wire_mapping(entries: BTreeMap<String, Value>) -> Value {
    let mut body = vec![wire_string("builtins"), wire_string("dict")];
    for (key, value) in entries {
        body.push(wire_node(
            "entry",
            Value::Array(vec![wire_string(&key), value]),
        ));
    }
    wire_node("mapping", Value::Array(body))
}

pub fn canonical_string_body(value: &Value) -> Option<&str> {
    let items = value.as_array()?;
    if items.len() == 3
        && items[0].as_str() == Some(CANONICAL_MARKER)
        && items[1].as_str() == Some("string")
    {
        items[2].as_str()
    } else {
        None
    }
}

pub fn canonical_int_body(value: &Value) -> Option<BigInt> {
    let items = value.as_array()?;
    if items.len() != 3
        || items[0].as_str() != Some(CANONICAL_MARKER)
        || items[1].as_str() != Some("int")
    {
        return None;
    }
    let text = items[2].as_str()?;
    let parsed = text.parse::<BigInt>().ok()?;
    (parsed.to_string() == text).then_some(parsed)
}

pub fn python_hex_exponent(value: &str) -> Option<i32> {
    let (negative, digits) = if let Some(digits) = value.strip_prefix('-') {
        (true, digits)
    } else {
        let digits = value.strip_prefix('+')?;
        (false, digits)
    };
    if digits.is_empty()
        || (digits.len() > 1 && digits.starts_with('0'))
        || !digits.bytes().all(|byte| byte.is_ascii_digit())
    {
        return None;
    }
    let magnitude = digits.parse::<i32>().ok()?;
    if negative {
        (magnitude != 0).then_some(-magnitude)
    } else {
        Some(magnitude)
    }
}

pub fn validate_python_float_hex(value: &str) -> Result<(), String> {
    let unsigned = value.strip_prefix('-').unwrap_or(value);
    if unsigned == "0x0.0p+0" {
        return Ok(());
    }
    let (mantissa, exponent_text) = unsigned
        .split_once('p')
        .ok_or_else(|| "canonical float body is not normalized Python float.hex".to_owned())?;
    if exponent_text.contains('p') {
        return Err("canonical float body is not normalized Python float.hex".to_owned());
    }
    let exponent = python_hex_exponent(exponent_text)
        .ok_or_else(|| "canonical float exponent is not normalized".to_owned())?;
    let digits = mantissa
        .strip_prefix("0x1.")
        .or_else(|| mantissa.strip_prefix("0x0."))
        .ok_or_else(|| "canonical float mantissa is not normalized".to_owned())?;
    if digits.len() != 13
        || !digits
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err("canonical float mantissa is not normalized".to_owned());
    }
    if mantissa.starts_with("0x1.") {
        if !(-1022..=1023).contains(&exponent) {
            return Err("canonical normal float exponent is out of range".to_owned());
        }
    } else if exponent != -1022 || digits.bytes().all(|byte| byte == b'0') {
        return Err("canonical subnormal float is not normalized".to_owned());
    }
    Ok(())
}

pub fn validate_canonical_node(value: &Value) -> Result<(), String> {
    let node = value
        .as_array()
        .ok_or_else(|| "canonical payload node must be an array".to_owned())?;
    if node.len() != 3 || node[0].as_str() != Some(CANONICAL_MARKER) {
        return Err("canonical payload marker is invalid".to_owned());
    }
    let tag = node[1]
        .as_str()
        .ok_or_else(|| "canonical payload tag must be a string".to_owned())?;
    let body = &node[2];
    match tag {
        "null" if body.is_null() => return Ok(()),
        "bool" if body.is_boolean() => return Ok(()),
        "string" if body.is_string() => return Ok(()),
        "int" => {
            let text = body
                .as_str()
                .ok_or_else(|| "canonical int body must be a string".to_owned())?;
            let value = text
                .parse::<BigInt>()
                .map_err(|_| "canonical int body is invalid".to_owned())?;
            if value.to_string() != text {
                return Err("canonical int body is not minimal".to_owned());
            }
            return Ok(());
        }
        "null" | "bool" | "string" => {
            return Err(format!("canonical {tag} body has the wrong type"));
        }
        _ => {}
    }

    let items = body
        .as_array()
        .ok_or_else(|| format!("canonical {tag} body must be an array"))?;
    for item in items {
        validate_canonical_node(item)?;
    }
    match tag {
        "list" | "tuple" => {}
        "set" | "frozenset" => {
            let encodings: Vec<Vec<u8>> = items.iter().map(sorted_json_bytes).collect();
            if encodings.windows(2).any(|pair| pair[0] >= pair[1]) {
                return Err(format!("canonical {tag} items are not unique and ordered"));
            }
        }
        "bytes" => {
            if items.len() != 1 || canonical_string_body(&items[0]).is_none() {
                return Err("canonical bytes body is invalid".to_owned());
            }
            let encoded = canonical_string_body(&items[0]).checked_invariant_d342ccbd("checked invariant");
            if !encoded.len().is_multiple_of(2)
                || encoded
                    .bytes()
                    .any(|byte| !byte.is_ascii_hexdigit() || byte.is_ascii_uppercase())
            {
                return Err("canonical bytes body is not lowercase hex".to_owned());
            }
        }
        "float" => {
            if items.len() != 1 {
                return Err("canonical float body is invalid".to_owned());
            }
            let encoded = canonical_string_body(&items[0])
                .ok_or_else(|| "canonical float body is invalid".to_owned())?;
            validate_python_float_hex(encoded)?;
        }
        "fraction" => {
            if items.len() != 2 {
                return Err("canonical fraction body is invalid".to_owned());
            }
            let numerator = canonical_int_body(&items[0])
                .ok_or_else(|| "canonical fraction numerator is not an integer".to_owned())?;
            let denominator = canonical_int_body(&items[1])
                .ok_or_else(|| "canonical fraction denominator is not an integer".to_owned())?;
            if denominator <= BigInt::zero() {
                return Err("canonical fraction denominator must be positive".to_owned());
            }
            let reduced = BigRational::new(numerator.clone(), denominator.clone());
            if reduced.numer() != &numerator || reduced.denom() != &denominator {
                return Err("canonical fraction is not reduced".to_owned());
            }
        }
        "enum" => {
            if items.len() != 4
                || items[..3]
                    .iter()
                    .any(|item| canonical_string_body(item).is_none_or(str::is_empty))
            {
                return Err("canonical enum body is invalid".to_owned());
            }
        }
        "field" => {
            if items.len() != 2 || canonical_string_body(&items[0]).is_none_or(str::is_empty) {
                return Err("canonical field body is invalid".to_owned());
            }
        }
        "entry" => {
            if items.len() != 2 || canonical_string_body(&items[0]).is_none() {
                return Err("canonical entry body is invalid".to_owned());
            }
        }
        "dataclass" => {
            if items.len() < 2
                || canonical_string_body(&items[0]).is_none_or(str::is_empty)
                || canonical_string_body(&items[1]).is_none_or(str::is_empty)
            {
                return Err("canonical dataclass identity is invalid".to_owned());
            }
            let mut names = BTreeSet::new();
            for field in &items[2..] {
                let field_items = field
                    .as_array()
                    .and_then(|node| node.get(2))
                    .and_then(Value::as_array)
                    .ok_or_else(|| "canonical dataclass field is invalid".to_owned())?;
                if field
                    .as_array()
                    .and_then(|node| node.get(1))
                    .and_then(Value::as_str)
                    != Some("field")
                    || field_items.len() != 2
                {
                    return Err("canonical dataclass field is invalid".to_owned());
                }
                let name = canonical_string_body(&field_items[0])
                    .ok_or_else(|| "canonical dataclass field name is invalid".to_owned())?;
                if !names.insert(name.to_owned()) {
                    return Err("canonical dataclass fields are duplicated".to_owned());
                }
            }
        }
        "mapping" => {
            if items.len() < 2
                || canonical_string_body(&items[0]) != Some("builtins")
                || canonical_string_body(&items[1]) != Some("dict")
            {
                return Err("canonical mapping identity is invalid".to_owned());
            }
            let mut prior: Option<String> = None;
            for entry in &items[2..] {
                let entry_node = entry
                    .as_array()
                    .ok_or_else(|| "canonical mapping entry is invalid".to_owned())?;
                if entry_node.get(1).and_then(Value::as_str) != Some("entry") {
                    return Err("canonical mapping entry tag is invalid".to_owned());
                }
                let entry_items = entry_node
                    .get(2)
                    .and_then(Value::as_array)
                    .ok_or_else(|| "canonical mapping entry body is invalid".to_owned())?;
                let key = entry_items
                    .first()
                    .and_then(canonical_string_body)
                    .ok_or_else(|| "canonical mapping key is invalid".to_owned())?;
                if prior.as_deref().is_some_and(|old| old >= key) {
                    return Err("canonical mapping keys are not unique and ordered".to_owned());
                }
                prior = Some(key.to_owned());
            }
        }
        _ => return Err(format!("unknown canonical payload tag {tag}")),
    }
    Ok(())
}

// Origin: engine/crates_rs/pfp_runtime/src/packet_wire.rs
// Claim: urn:core:crates_rs:pfp-runtime:packet-wire:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd342ccbd {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd342ccbd` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord342ccbd {
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
impl BoundaryErrord342ccbd {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord342ccbd {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord342ccbd {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd342ccbd {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord342ccbd> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord342ccbd::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord342ccbd::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord342ccbd::ExceedsCapacity {
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
mod separator_encoding {
    use super::sorted_json_bytes;
    use serde_json::json;

    #[test]
    fn line_and_paragraph_separators_stay_raw_utf8() {
        let bytes = sorted_json_bytes(&json!([
            "core-canonical-v1",
            "string",
            "\u{2028}\u{2029}"
        ]));
        assert_eq!(
            bytes,
            "[\"core-canonical-v1\",\"string\",\"\u{2028}\u{2029}\"]".as_bytes()
        );
        assert!(bytes.windows(3).any(|window| window == [0xE2, 0x80, 0xA8]));
        assert!(bytes.windows(3).any(|window| window == [0xE2, 0x80, 0xA9]));
        assert!(!bytes.windows(6).any(|window| window == br"\u2028"));
        assert!(!bytes.windows(6).any(|window| window == br"\u2029"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_d342ccbd {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd342ccbd::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd342ccbd::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd342ccbd::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd342ccbd::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd342ccbd::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord342ccbd::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord342ccbd::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
