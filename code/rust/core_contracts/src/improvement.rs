//! Canonical improvement / maintenance contract family (V1).
//!
//! Normative types for the host-governed maintenance loop live here once.
//! Producers and consumers outside this module may reference these types; they
//! must not invent shadow semantic contracts or provenance fields.
//!
//! Encoding: every maintenance contract is serialized with
//! [`canonical_json::CORE_CANONICAL_JSON_V1`] (compact, recursively key-sorted,
//! raw-Unicode). Floating-point fields are forbidden. Raw inputs are always
//! hashed independently of semantic JSON.

#[path = "improvement_canonical_json.rs"]
pub mod canonical_json;
#[path = "improvement_ids.rs"]
pub mod ids;
#[path = "improvement_types.rs"]
pub mod types;

pub use canonical_json::{
    dumps_canonical_v1, hash_canonical_v1, hash_raw_bytes, CanonicalJsonError,
    CORE_CANONICAL_JSON_V1,
};
pub use ids::{derive_candidate_id_from_body, derive_candidate_id_v1, derive_finding_id_v1};
pub use types::*;

use serde::Serialize;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CanonicalOrderError {
    Json(CanonicalJsonError),
    Order,
    Width,
}

impl std::fmt::Display for CanonicalOrderError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Json(error) => write!(formatter, "{error}"),
            Self::Order => write!(formatter, "key order changed the canonical digest"),
            Self::Width => write!(formatter, "canonical digest is not 64 hex bytes"),
        }
    }
}

impl std::error::Error for CanonicalOrderError {}

impl From<CanonicalJsonError> for CanonicalOrderError {
    fn from(error: CanonicalJsonError) -> Self {
        Self::Json(error)
    }
}

/// Two objects with the same integer fields in opposite declaration order
/// have one canonical digest, and that digest is the raw hash of the canonical bytes.
pub fn admit_canonical_key_order() -> Result<String, CanonicalOrderError> {
    #[derive(Serialize)]
    struct Left {
        b: i64,
        a: i64,
    }
    #[derive(Serialize)]
    struct Right {
        a: i64,
        b: i64,
    }
    let left_value = Left { b: 2, a: 1 };
    let right_value = Right { a: 1, b: 2 };
    let left_bytes = dumps_canonical_v1(&left_value)?;
    let right_bytes = dumps_canonical_v1(&right_value)?;
    if left_bytes != right_bytes {
        return Err(CanonicalOrderError::Order);
    }
    let from_bytes = hash_raw_bytes(&left_bytes);
    let from_value = hash_canonical_v1(&left_value)?;
    let from_swap = hash_canonical_v1(&right_value)?;
    if from_bytes != from_value || from_value != from_swap {
        return Err(CanonicalOrderError::Order);
    }
    verify_digest_and_width(&from_value, left_bytes.len(), right_bytes.len())?;
    Ok(from_value)
}

fn verify_digest_and_width(
    from_value: &str,
    left_len: usize,
    right_len: usize,
) -> Result<(), CanonicalOrderError> {
    if from_value.len() != 64 || from_value.bytes().any(|byte| !byte.is_ascii_hexdigit()) {
        return Err(CanonicalOrderError::Width);
    }
    let width = left_len
        .checked_add(right_len)
        .ok_or(CanonicalOrderError::Width)?;
    if width != left_len.checked_mul(2).ok_or(CanonicalOrderError::Width)? {
        return Err(CanonicalOrderError::Width);
    }
    Ok(())
}

// Origin: engine/crates_rs/core_contracts/src/improvement.rs
// Claim: urn:core:crates_rs:core-contracts:improvement:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod canonical_order_tests {
    use super::*;

    #[test]
    fn swapped_keys_share_one_sha256() {
        let digest = admit_canonical_key_order();
        assert!(digest.is_ok());
        if let Ok(digest) = digest {
            assert_eq!(digest.len(), 64);
        }
    }
}
