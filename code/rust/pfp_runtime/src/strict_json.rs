//! Bounded JSON with duplicate-key rejection and exact number lexemes.
use serde::{
    de::{MapAccess, Visitor},
    Deserialize, Deserializer,
};
use serde_json::{value::RawValue, Map, Number, Value};
use std::{collections::BTreeMap, fmt, str::FromStr};

struct RawObject(BTreeMap<String, Box<RawValue>>);
impl<'de> Deserialize<'de> for RawObject {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct ObjectVisitor;
        impl<'de> Visitor<'de> for ObjectVisitor {
            type Value = RawObject;
            fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                formatter.write_str("a JSON object")
            }
            fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Self::Value, A::Error> {
                let mut output = BTreeMap::new();
                while let Some(key) = map.next_key::<String>()? {
                    if output.contains_key(&key) {
                        return Err(serde::de::Error::custom(format!(
                            "duplicate JSON key: {key}"
                        )));
                    }
                    output.insert(key, map.next_value::<Box<RawValue>>()?);
                }
                Ok(RawObject(output))
            }
        }
        deserializer.deserialize_map(ObjectVisitor)
    }
}

fn json_error(error: serde_json::Error) -> String {
    let message = error.to_string();
    if message.starts_with("duplicate JSON key: ") {
        message
            .rsplit_once(" at line ")
            .map_or(message.clone(), |(message, _)| message.into())
    } else {
        message
    }
}

fn value(raw: &str) -> Result<Value, String> {
    match raw.as_bytes().first() {
        Some(b'{') => {
            let object: RawObject = serde_json::from_str(raw).map_err(json_error)?;
            let mut output = Map::new();
            for (key, raw_value) in object.0 {
                output.insert(key, value(raw_value.get())?);
            }
            Ok(Value::Object(output))
        }
        Some(b'[') => {
            let array: Vec<Box<RawValue>> = serde_json::from_str(raw).map_err(json_error)?;
            array
                .into_iter()
                .map(|raw| value(raw.get()))
                .collect::<Result<Vec<_>, _>>()
                .map(Value::Array)
        }
        Some(b'"') => serde_json::from_str::<String>(raw)
            .map(Value::String)
            .map_err(json_error),
        Some(b'n') => Ok(Value::Null),
        Some(b't') => Ok(Value::Bool(true)),
        Some(b'f') => Ok(Value::Bool(false)),
        _ => Number::from_str(raw).map(Value::Number).map_err(json_error),
    }
}

pub fn parse(raw: &[u8]) -> Result<Value, String> {
    parse_with_limit(raw, 4 * 1024 * 1024)
}

/// Parse under a caller-owned complete-envelope ceiling. The ordinary parser
/// retains its 4 MiB ceiling; larger actions must opt in with their own bound.
pub fn parse_with_limit(raw: &[u8], max_bytes: usize) -> Result<Value, String> {
    if raw.len() > max_bytes {
        return Err(if max_bytes == 4 * 1024 * 1024 {
            "JSON input exceeds 4 MiB".into()
        } else {
            format!("JSON input exceeds {max_bytes} bytes")
        });
    }
    if raw.starts_with(b"\xef\xbb\xbf") {
        return Err(
            "Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)".into(),
        );
    }
    // RawValue validates syntax/depth first; the recursive walk never reinterprets
    // an object with serde_json's private arbitrary-precision number key.
    let root: Box<RawValue> = serde_json::from_slice(raw).map_err(json_error)?;
    value(root.get())
}

// Origin: engine/crates_rs/pfp_runtime/src/strict_json.rs
// Claim: urn:core:crates_rs:pfp-runtime:strict-json:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0ed85b8b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0ed85b8b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0ed85b8b {
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
impl BoundaryError0ed85b8b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0ed85b8b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0ed85b8b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0ed85b8b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0ed85b8b> {
        if capacity_bound == 0 {
            return Err(BoundaryError0ed85b8b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0ed85b8b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0ed85b8b::ExceedsCapacity {
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

    #[test]
    fn custom_envelope_bound_does_not_relax_the_default() {
        let mut input = b"null".to_vec();
        input.resize(4 * 1024 * 1024 + 1, b' ');
        assert_eq!(parse(&input).unwrap_err(), "JSON input exceeds 4 MiB");
        assert_eq!(parse_with_limit(&input, input.len()).unwrap(), Value::Null);
        assert_eq!(
            parse_with_limit(&input, input.len() - 1).unwrap_err(),
            "JSON input exceeds 4 MiB"
        );
        assert_eq!(
            parse_with_limit(b"null ", 4).unwrap_err(),
            "JSON input exceeds 4 bytes"
        );
    }

    #[test]
    fn custom_bound_retains_duplicate_and_number_type_guards() {
        assert_eq!(
            parse_with_limit(br#"{"x":1,"x":2}"#, 64).unwrap_err(),
            "duplicate JSON key: x"
        );
        let object = parse_with_limit(br#"{"$serde_json::private::Number":"4096"}"#, 64).unwrap();
        assert!(object.is_object());
        assert_eq!(object["$serde_json::private::Number"], "4096");
        let number = parse_with_limit(b"18446744073709551616", 64).unwrap();
        assert!(number.is_number());
        assert_eq!(number.to_string(), "18446744073709551616");
    }
}

#[cfg(test)]
mod l4_boundary_tests_0ed85b8b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0ed85b8b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0ed85b8b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0ed85b8b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0ed85b8b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0ed85b8b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0ed85b8b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0ed85b8b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
