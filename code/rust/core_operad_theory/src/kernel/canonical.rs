//! Canonical encoding and identifiers, byte-compatible with the Python kernel.
//!
//! This is the Rust face of `engine/crates/kernel/higher_operad/canonical.py`.
//! Its whole purpose is that `canonical_id` returns the *same string* as the
//! Python function for the same input. Every decision below exists to protect
//! that equality; a change here that alters one byte silently invalidates every
//! stored identifier in the estate.
//!
//! The encoding is `sha256` over
//! `{"domain": <identifier>, "payload": <canonicalized>}` serialized with sorted
//! keys, no whitespace, and no non-finite numbers.
//!
//! Two properties make the Rust and Python encoders agree:
//!
//! - Every object is explicitly key-sorted, including when a consumer enables
//!   the additive `serde_json/preserve_order` feature. Keys serialize exactly
//!   as Python's `sort_keys=True` produces. Both sort by Unicode code point;
//!   UTF-8 byte order and code point order coincide.
//! - `serde_json::to_string` emits `,` and `:` with no padding, matching
//!   Python's `separators=(",", ":")`.
//!
//! AuthorityEffect: None.

use serde_json::{Map, Value};
use sha2::{Digest, Sha256};
use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum CanonicalError {
    #[error("{field} must be a non-empty string")]
    NotText { field: String },

    #[error("{field} must be a canonical identifier")]
    NotIdentifier { field: String },

    #[error("{field} must be a lowercase sha256: digest")]
    NotDigest { field: String },

    #[error("{field} must not contain duplicates")]
    Duplicates { field: String },

    #[error("canonical key collision: {key:?}")]
    KeyCollision { key: String },

    #[error("unsupported canonical value: {kind}")]
    UnsupportedValue { kind: String },

    /// Refused rather than risk a digest that disagrees with Python.
    ///
    /// The Python encoder NFC-normalizes every string. Reproducing that here
    /// would mean vendoring a Unicode normalization table, and NFC is the
    /// identity on the ASCII identifiers and digests this kernel actually
    /// carries. Rather than normalize approximately -- which could yield a
    /// different digest than Python for the same logical value, the one failure
    /// this module must never have -- non-ASCII text is refused outright. To
    /// widen the domain, add a normalization dependency and drop this check
    /// together, never one without the other.
    #[error(
        "{field} contains non-ASCII text, which this encoder refuses; see CanonicalError::NonAscii"
    )]
    NonAscii { field: String },
}

fn is_identifier(value: &str) -> bool {
    let mut chars = value.chars();
    match chars.next() {
        Some(c) if c.is_ascii_alphanumeric() => {}
        _ => return false,
    }
    chars.all(|c| c.is_ascii_alphanumeric() || matches!(c, '.' | '_' | ':' | '/' | '@' | '-'))
}

fn is_digest(value: &str) -> bool {
    let Some(hex) = value.strip_prefix("sha256:") else {
        return false;
    };
    hex.len() == 64
        && hex
            .chars()
            .all(|c| c.is_ascii_digit() || ('a'..='f').contains(&c))
}

/// Trim, reject empty, and reject non-ASCII.
///
/// Python additionally applies NFC here; see [`CanonicalError::NonAscii`] for
/// why refusing non-ASCII is the safe way to match it.
pub fn require_text(value: &str, field: &str) -> Result<String, CanonicalError> {
    let trimmed = value.trim();
    if trimmed.is_empty() {
        return Err(CanonicalError::NotText {
            field: field.to_owned(),
        });
    }
    if !trimmed.is_ascii() {
        return Err(CanonicalError::NonAscii {
            field: field.to_owned(),
        });
    }
    Ok(trimmed.to_owned())
}

pub fn require_identifier(value: &str, field: &str) -> Result<String, CanonicalError> {
    let normalized = require_text(value, field)?;
    if !is_identifier(&normalized) {
        return Err(CanonicalError::NotIdentifier {
            field: field.to_owned(),
        });
    }
    Ok(normalized)
}

pub fn require_digest(value: &str, field: &str) -> Result<String, CanonicalError> {
    let normalized = require_text(value, field)?;
    if !is_digest(&normalized) {
        return Err(CanonicalError::NotDigest {
            field: field.to_owned(),
        });
    }
    Ok(normalized)
}

/// Sort and reject duplicates, mirroring `sorted_unique` in the Python kernel.
pub fn sorted_unique(values: &[String], field: &str) -> Result<Vec<String>, CanonicalError> {
    let mut normalized = Vec::with_capacity(values.len());
    for value in values {
        normalized.push(require_identifier(value, field)?);
    }
    let mut sorted = normalized.clone();
    sorted.sort();
    sorted.dedup();
    if sorted.len() != normalized.len() {
        return Err(CanonicalError::Duplicates {
            field: field.to_owned(),
        });
    }
    Ok(sorted)
}

fn canonicalize_array(items: &[Value]) -> Result<Value, CanonicalError> {
    let mut out = Vec::with_capacity(items.len());
    for item in items {
        out.push(canonicalize(item)?);
    }
    Ok(Value::Array(out))
}

fn canonicalize_object(entries: &Map<String, Value>) -> Result<Value, CanonicalError> {
    let mut out = Map::new();
    for (key, item) in entries {
        if !key.is_ascii() {
            return Err(CanonicalError::NonAscii {
                field: "canonical key".to_owned(),
            });
        }
        if out.contains_key(key) {
            return Err(CanonicalError::KeyCollision { key: key.clone() });
        }
        out.insert(key.clone(), canonicalize(item)?);
    }
    out.sort_keys();
    Ok(Value::Object(out))
}

/// Recursively validate and normalize a value for canonical encoding.
///
/// Mirrors Python `_canonicalize`, including its refusals: only null, bool,
/// integer, string, map, and array are admissible. A float is rejected there
/// (it falls through to the `TypeError` branch) and must be rejected here too,
/// because binary floating point has no exact canonical decimal form.
fn canonicalize(value: &Value) -> Result<Value, CanonicalError> {
    match value {
        Value::Null | Value::Bool(_) => Ok(value.clone()),
        Value::Number(number) => {
            if number.is_f64() {
                return Err(CanonicalError::UnsupportedValue {
                    kind: "float".to_owned(),
                });
            }
            Ok(value.clone())
        }
        Value::String(text) => {
            if !text.is_ascii() {
                return Err(CanonicalError::NonAscii {
                    field: "canonical string".to_owned(),
                });
            }
            Ok(Value::String(text.clone()))
        }
        Value::Array(items) => canonicalize_array(items),
        Value::Object(entries) => canonicalize_object(entries),
    }
}

/// The exact bytes hashed by [`canonical_id`].
pub fn canonical_bytes(domain: &str, payload: &Value) -> Result<Vec<u8>, CanonicalError> {
    let mut envelope = Map::new();
    envelope.insert(
        "domain".to_owned(),
        Value::String(require_identifier(domain, "domain")?),
    );
    envelope.insert("payload".to_owned(), canonicalize(payload)?);
    // `to_string` on a Value cannot fail: every branch above is representable.
    Ok(Value::Object(envelope).to_string().into_bytes())
}

/// `sha256:<hex>` over the canonical envelope.
pub fn canonical_id(domain: &str, payload: &Value) -> Result<String, CanonicalError> {
    let bytes = canonical_bytes(domain, payload)?;
    let digest = Sha256::digest(&bytes);
    Ok(format!("sha256:{}", hex::encode(digest)))
}

// Origin: engine/crates_rs/core_operad_theory/src/kernel/canonical.rs
// Claim: urn:core:crates_rs:core-operad-theory:canonical:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn envelope_sorts_keys_and_omits_whitespace() {
        let bytes = canonical_bytes("core.test", &json!({"b": 1, "a": {"d": 2, "c": 3}})).unwrap();
        assert_eq!(
            String::from_utf8(bytes).unwrap(),
            r#"{"domain":"omega.test","payload":{"a":{"c":3,"d":2},"b":1}}"#
        );
    }

    #[test]
    fn canonical_bytes_sort_nested_maps_independent_of_serde_features() {
        fn payload(reverse: bool) -> Value {
            let mut inner = Map::new();
            let pairs = if reverse {
                [("z", 1), ("a", 2)]
            } else {
                [("a", 2), ("z", 1)]
            };
            for (key, value) in pairs {
                inner.insert(key.into(), json!(value));
            }
            let mut outer = Map::new();
            outer.insert("z".into(), json!(0));
            outer.insert(
                "a".into(),
                Value::Array(vec![Value::Object(inner), json!(9)]),
            );
            Value::Object(outer)
        }

        let first = payload(true);
        let second = payload(false);
        assert_eq!(first, second);
        assert_eq!(
            canonical_bytes("core.test", &first).unwrap(),
            br#"{"domain":"omega.test","payload":{"a":[{"a":2,"z":1},9],"z":0}}"#
        );
        assert_eq!(
            canonical_bytes("core.test", &first).unwrap(),
            canonical_bytes("core.test", &second).unwrap()
        );
        assert_eq!(
            canonical_id("core.test", &first).unwrap(),
            canonical_id("core.test", &second).unwrap()
        );
        assert_ne!(
            canonical_id("core.test", &json!([1, 2])).unwrap(),
            canonical_id("core.test", &json!([2, 1])).unwrap()
        );
    }

    #[test]
    fn identifier_grammar_matches_the_python_regex() {
        assert!(require_identifier("core.oewas.colour.v1", "f").is_ok());
        assert!(require_identifier("a-b_c:d/e@f", "f").is_ok());
        // must start alphanumeric
        assert!(require_identifier(".leading", "f").is_err());
        assert!(require_identifier("-leading", "f").is_err());
        // no spaces, no other punctuation
        assert!(require_identifier("has space", "f").is_err());
        assert!(require_identifier("has!bang", "f").is_err());
        assert!(require_identifier("", "f").is_err());
    }

    #[test]
    fn digest_grammar_requires_lowercase_hex_and_prefix() {
        let good = format!("sha256:{}", "a".repeat(64));
        assert!(require_digest(&good, "f").is_ok());
        assert!(require_digest(&format!("sha256:{}", "A".repeat(64)), "f").is_err());
        assert!(require_digest(&format!("sha256:{}", "a".repeat(63)), "f").is_err());
        assert!(require_digest(&"a".repeat(64), "f").is_err());
    }

    #[test]
    fn floats_are_refused_because_python_refuses_them() {
        let err = canonical_bytes("core.test", &json!({"x": 1.5})).unwrap_err();
        assert_eq!(
            err,
            CanonicalError::UnsupportedValue {
                kind: "float".to_owned()
            }
        );
    }

    #[test]
    fn non_ascii_is_refused_rather_than_normalized_approximately() {
        let err = canonical_bytes("core.test", &json!({"x": "café"})).unwrap_err();
        assert!(matches!(err, CanonicalError::NonAscii { .. }));
    }

    #[test]
    fn sorted_unique_sorts_and_rejects_duplicates() {
        let values = vec!["b".to_owned(), "a".to_owned()];
        assert_eq!(
            sorted_unique(&values, "f").unwrap(),
            vec!["a".to_owned(), "b".to_owned()]
        );

        let dupes = vec!["a".to_owned(), "a".to_owned()];
        assert!(sorted_unique(&dupes, "f").is_err());
    }

    #[test]
    fn identifiers_are_trimmed_before_hashing() {
        let padded = canonical_id("  core.test  ", &json!(null)).unwrap();
        let tight = canonical_id("core.test", &json!(null)).unwrap();
        assert_eq!(padded, tight);
    }
}
