//! `core.canonical_json.v1` — compact, recursively key-sorted, raw-Unicode JSON.
//!
//! Matches the existing conductor/assurance compact form with
//! `ensure_ascii=False` (raw UTF-8 in strings) and recursively sorted object
//! keys. Maintenance contracts forbid floating-point fields.

use serde::Serialize;
use serde_json::Value;
use sha2::{Digest, Sha256};
use thiserror::Error;

/// Wire encoding tag for the maintenance contract family.
pub const CORE_CANONICAL_JSON_V1: &str = "core.canonical_json.v1";

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum CanonicalJsonError {
    #[error("canonical json serialization failed: {0}")]
    Serialize(String),
    #[error("floating-point values are forbidden in maintenance contracts")]
    FloatForbidden,
    #[error("value is not valid canonical JSON")]
    InvalidValue,
}

/// Serialize `value` as `core.canonical_json.v1` bytes.
///
/// Rules:
/// - compact separators (`","`, `":"`)
/// - object keys sorted recursively, including with `serde_json/preserve_order`
/// - raw Unicode (no `\uXXXX` escaping of non-ASCII)
/// - no floating-point numbers
pub fn dumps_canonical_v1<T: Serialize + ?Sized>(value: &T) -> Result<Vec<u8>, CanonicalJsonError> {
    let raw =
        serde_json::to_value(value).map_err(|e| CanonicalJsonError::Serialize(e.to_string()))?;
    let normalized = normalize_value(raw)?;
    // Normalization explicitly sorts keys, independent of serde_json features.
    let text = serde_json::to_string(&normalized)
        .map_err(|e| CanonicalJsonError::Serialize(e.to_string()))?;
    Ok(text.into_bytes())
}

/// SHA-256 (lowercase hex) of the canonical JSON encoding of `value`.
pub fn hash_canonical_v1<T: Serialize + ?Sized>(value: &T) -> Result<String, CanonicalJsonError> {
    let bytes = dumps_canonical_v1(value)?;
    Ok(hash_raw_bytes(&bytes))
}

/// SHA-256 (lowercase hex) of arbitrary raw bytes — independent of JSON encoding.
pub fn hash_raw_bytes(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

fn normalize_number(n: serde_json::Number) -> Result<Value, CanonicalJsonError> {
    if n.is_f64() && !n.is_i64() && !n.is_u64() {
        // Reject true floats. Integers that happen to be f64-representable
        // still serialize as integers via serde_json when constructed as
        // i64/u64; a pure float Number is refused.
        if n.as_i64().is_none() && n.as_u64().is_none() {
            return Err(CanonicalJsonError::FloatForbidden);
        }
    }
    // Also refuse any Number that is not an integer.
    if n.as_i64().is_none() && n.as_u64().is_none() {
        return Err(CanonicalJsonError::FloatForbidden);
    }
    Ok(Value::Number(n))
}

fn normalize_value(value: Value) -> Result<Value, CanonicalJsonError> {
    match value {
        Value::Null | Value::Bool(_) | Value::String(_) => Ok(value),
        Value::Number(n) => normalize_number(n),
        Value::Array(items) => {
            let mut out = Vec::with_capacity(items.len());
            for item in items {
                out.push(normalize_value(item)?);
            }
            Ok(Value::Array(out))
        }
        Value::Object(map) => {
            let mut out = serde_json::Map::new();
            for (k, v) in map {
                out.insert(k, normalize_value(v)?);
            }
            out.sort_keys();
            Ok(Value::Object(out))
        }
    }
}

// Origin: engine/crates_rs/core_contracts/src/improvement_canonical_json.rs
// Claim: urn:core:crates_rs:core-contracts:improvement-canonical-json:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use std::collections::BTreeMap;

    #[test]
    fn key_order_is_stable_across_map_construction_order() {
        let mut a = BTreeMap::new();
        a.insert("z", 1);
        a.insert("a", 2);
        let mut b = BTreeMap::new();
        b.insert("a", 2);
        b.insert("z", 1);
        assert_eq!(
            dumps_canonical_v1(&a).unwrap(),
            dumps_canonical_v1(&b).unwrap()
        );
        assert_eq!(
            String::from_utf8(dumps_canonical_v1(&a).unwrap()).unwrap(),
            r#"{"a":2,"z":1}"#
        );
    }

    #[test]
    fn canonical_bytes_sort_nested_maps_independent_of_serde_features() {
        fn nested(reverse: bool) -> Value {
            let mut inner = serde_json::Map::new();
            let pairs = if reverse {
                [("z", 1), ("a", 2)]
            } else {
                [("a", 2), ("z", 1)]
            };
            for (key, value) in pairs {
                inner.insert(key.into(), json!(value));
            }
            let mut outer = serde_json::Map::new();
            outer.insert("z".into(), json!(0));
            outer.insert(
                "a".into(),
                Value::Array(vec![Value::Object(inner), json!(9)]),
            );
            Value::Object(outer)
        }

        let first = nested(true);
        let second = nested(false);
        assert_eq!(first, second);
        assert_eq!(
            dumps_canonical_v1(&first).unwrap(),
            br#"{"a":[{"a":2,"z":1},9],"z":0}"#
        );
        assert_eq!(
            dumps_canonical_v1(&first).unwrap(),
            dumps_canonical_v1(&second).unwrap()
        );
        assert_eq!(
            hash_canonical_v1(&first).unwrap(),
            hash_canonical_v1(&second).unwrap()
        );
        // Arrays retain semantic order while object keys are canonicalized.
        assert_ne!(
            hash_canonical_v1(&json!([1, 2])).unwrap(),
            hash_canonical_v1(&json!([2, 1])).unwrap()
        );
    }

    #[test]
    fn raw_unicode_is_not_escaped() {
        let v = json!({"path": "café.txt"});
        let bytes = dumps_canonical_v1(&v).unwrap();
        let s = String::from_utf8(bytes).unwrap();
        assert!(s.contains("café"), "raw unicode expected, got {s}");
        assert!(!s.contains("\\u00e9"));
    }

    #[test]
    fn floats_are_forbidden() {
        let v = json!({"score": 1.5});
        assert_eq!(
            dumps_canonical_v1(&v).unwrap_err(),
            CanonicalJsonError::FloatForbidden
        );
    }

    #[test]
    fn raw_byte_hash_is_independent_of_json() {
        let raw = b"hello\r\nworld\0";
        let h1 = hash_raw_bytes(raw);
        let h2 = hash_raw_bytes(raw);
        assert_eq!(h1, h2);
        assert_eq!(h1.len(), 64);
        // Different from hashing a JSON string of the same content.
        let json_hash = hash_canonical_v1(&"hello\r\nworld\0").unwrap();
        assert_ne!(h1, json_hash);
    }

    #[test]
    fn bom_and_missing_newline_change_raw_hash() {
        let a = b"line";
        let b = b"line\n";
        let c = b"\xEF\xBB\xBFline";
        assert_ne!(hash_raw_bytes(a), hash_raw_bytes(b));
        assert_ne!(hash_raw_bytes(a), hash_raw_bytes(c));
    }

    #[test]
    fn crlf_vs_lf_change_raw_hash() {
        assert_ne!(hash_raw_bytes(b"a\r\nb"), hash_raw_bytes(b"a\nb"));
    }

    #[test]
    fn invalid_utf8_is_hashable_as_raw_bytes() {
        let raw = b"\x80\xFF not utf8";
        let h = hash_raw_bytes(raw);
        assert_eq!(h.len(), 64);
    }
}
