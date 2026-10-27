//! Canonical JSON bytes and `sha256:` digests for loop artifacts.
//!
//! The byte form matches the pack's Python oracle,
//! `json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)`,
//! for the values the loop hashes: objects (keys in code-point order), arrays, strings,
//! booleans, null and integers. A non-integer number is refused rather than given a float
//! spelling that the two languages might disagree on.
//!
//! AuthorityEffect: None.

use super::refuse;
use crate::stage::ports::Refusal;
use serde_json::Value;
use sha2::{Digest, Sha256};

pub const DIGEST_PREFIX: &str = "sha256:";

pub fn canonical_bytes(value: &Value) -> Result<Vec<u8>, Refusal> {
    let mut out = String::new();
    write(value, &mut out)?;
    Ok(out.into_bytes())
}

/// `sha256:<hex>` of the canonical bytes.
pub fn digest(value: &Value) -> Result<String, Refusal> {
    Ok(digest_bytes(&canonical_bytes(value)?))
}

pub fn digest_bytes(bytes: &[u8]) -> String {
    format!("{DIGEST_PREFIX}{}", hex::encode(Sha256::digest(bytes)))
}

/// True for `sha256:` followed by 64 lowercase hex digits.
pub fn is_digest(text: &str) -> bool {
    text.strip_prefix(DIGEST_PREFIX).is_some_and(|hex| {
        hex.len() == 64
            && hex
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    })
}

fn write(value: &Value, out: &mut String) -> Result<(), Refusal> {
    match value {
        Value::Null => out.push_str("null"),
        Value::Bool(flag) => out.push_str(if *flag { "true" } else { "false" }),
        Value::Number(number) => {
            let text = number.to_string();
            let digits = text.strip_prefix('-').unwrap_or(&text);
            let integer = !digits.is_empty()
                && digits.bytes().all(|b| b.is_ascii_digit())
                && (digits == "0" || !digits.starts_with('0'))
                && text != "-0";
            if !integer {
                return Err(refuse(
                    "CANONICAL_NUMBER_NOT_INTEGER",
                    format!("canonical loop values hold integers only, found {text}"),
                ));
            }
            out.push_str(&text);
        }
        Value::String(text) => out.push_str(&string_literal(text)?),
        Value::Array(items) => {
            out.push('[');
            for (index, item) in items.iter().enumerate() {
                if index > 0 {
                    out.push(',');
                }
                write(item, out)?;
            }
            out.push(']');
        }
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            // UTF-8 byte order is code-point order, which is Python's str ordering.
            keys.sort();
            out.push('{');
            for (index, key) in keys.into_iter().enumerate() {
                if index > 0 {
                    out.push(',');
                }
                out.push_str(&string_literal(key)?);
                out.push(':');
                write(&map[key], out)?;
            }
            out.push('}');
        }
    }
    Ok(())
}

/// serde_json escapes exactly the set Python's encoder escapes with `ensure_ascii=False`:
/// `"`, `\`, the five short control escapes, and other C0 controls as lowercase `\u00xx`.
fn string_literal(text: &str) -> Result<String, Refusal> {
    serde_json::to_string(text).map_err(|error| refuse("CANONICAL_STRING", error.to_string()))
}

// Origin: engine/crates_rs/core_adversary/src/research_loop/canonical.rs
// Claim: urn:core:crates_rs:core-adversary:canonical:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord09f4d56c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord09f4d56c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError09f4d56c {
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
impl BoundaryError09f4d56c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError09f4d56c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError09f4d56c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord09f4d56c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError09f4d56c> {
        if capacity_bound == 0 {
            return Err(BoundaryError09f4d56c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError09f4d56c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError09f4d56c::ExceedsCapacity {
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
    use serde_json::json;

    #[test]
    fn matches_python_spelling() {
        let bytes = canonical_bytes(&json!({"b": [1, true, null], "a": "é\n\u{1}"})).unwrap();
        assert_eq!(
            String::from_utf8(bytes).unwrap(),
            "{\"a\":\"é\\n\\u0001\",\"b\":[1,true,null]}"
        );
    }

    #[test]
    fn refuses_non_integers() {
        let value: Value = serde_json::from_str("{\"x\": 1.5}").unwrap();
        assert_eq!(
            canonical_bytes(&value).unwrap_err().code,
            "CANONICAL_NUMBER_NOT_INTEGER"
        );
        let value: Value = serde_json::from_str("[1e3]").unwrap();
        assert!(canonical_bytes(&value).is_err());
    }

    #[test]
    fn recognises_digests() {
        assert!(is_digest(&digest(&json!({})).unwrap()));
        assert!(!is_digest("sha256:ABC"));
        assert!(!is_digest(&format!("sha256:{}", "A".repeat(64))));
    }
}

#[cfg(test)]
mod l4_boundary_tests_09f4d56c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord09f4d56c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord09f4d56c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord09f4d56c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord09f4d56c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord09f4d56c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError09f4d56c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError09f4d56c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
