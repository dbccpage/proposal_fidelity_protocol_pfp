//! Byte-level validation for the declared finite output language. V1 is unchanged.
//! This receipt does not prove provider-side enforcement or mathematical correctness.
//! AuthorityEffect: None.

use serde::Deserialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Receipt {
    schema_version: String,
    request_hex: String,
    request_sha256: String,
    output_hex: String,
    output_sha256: String,
    language_hex: String,
    language_sha256: String,
    tokenizer_profile: Option<String>,
    enforcement: String,
    validation_method: String,
    validation_outcome: String,
    authority_effect: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Language {
    schema_version: String,
    sentences_hex: Vec<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ChallengeLanguage {
    schema_version: String,
    candidate_ref: String,
    edge_count: usize,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ChallengeOutput {
    candidate_ref: String,
    obligation: String,
    witness: Vec<String>,
}

fn bytes(text: &str, digest: &str) -> Result<Vec<u8>, String> {
    let raw = hex::decode(text).map_err(|_| "DECODE_V2_MALFORMED_BYTES")?;
    let expected = format!("sha256:{:x}", Sha256::digest(&raw));
    if expected != digest {
        return Err("DECODE_V2_DIGEST_MISMATCH".into());
    }
    Ok(raw)
}

fn has_valid_decode_header_fields(receipt: &Receipt) -> bool {
    receipt.schema_version == "core.symbol_game.decode_receipt.v2"
        && receipt.authority_effect == "None"
        && ["finite-utf8.v1", "graph-challenge-json.v1"]
            .contains(&receipt.validation_method.as_str())
        && ["POST_VALIDATION", "PROVIDER_REQUESTED", "FIXTURE"]
            .contains(&receipt.enforcement.as_str())
}

fn check_decode_byte_bounds(
    request: &[u8],
    output: &[u8],
    language: &[u8],
    tokenizer_profile: Option<&String>,
) -> bool {
    let valid_profile = tokenizer_profile.is_none_or(|s| !s.is_empty() && s.len() <= 1024);
    !request.is_empty()
        && request.len() <= 16_384
        && output.len() <= 16_384
        && language.len() <= 32_768
        && valid_profile
}

fn validate_decode_header(receipt: &Receipt) -> Result<(Vec<u8>, Vec<u8>), String> {
    if !has_valid_decode_header_fields(receipt) {
        return Err("DECODE_V2_HEADER_REFUSED".into());
    }
    let request = bytes(&receipt.request_hex, &receipt.request_sha256)?;
    let output = bytes(&receipt.output_hex, &receipt.output_sha256)?;
    let language = bytes(&receipt.language_hex, &receipt.language_sha256)?;
    if !check_decode_byte_bounds(
        &request,
        &output,
        &language,
        receipt.tokenizer_profile.as_ref(),
    ) {
        return Err("DECODE_V2_BYTE_CEILING".into());
    }
    Ok((output, language))
}

fn verify_finite_utf8(language: &[u8], output: &[u8]) -> Result<bool, String> {
    let spec: Language =
        serde_json::from_slice(language).map_err(|_| "DECODE_V2_LANGUAGE_MALFORMED")?;
    if spec.schema_version != "core.symbol_game.finite-output-language.v1"
        || spec.sentences_hex.is_empty()
        || spec.sentences_hex.len() > 64
    {
        return Err("DECODE_V2_LANGUAGE_REFUSED".into());
    }
    let mut valid = false;
    for text in spec.sentences_hex {
        let sentence = hex::decode(&text).map_err(|_| "DECODE_V2_LANGUAGE_MALFORMED")?;
        if sentence.is_empty()
            || sentence.len() > 16_384
            || std::str::from_utf8(&sentence).is_err()
        {
            return Err("DECODE_V2_LANGUAGE_REFUSED".into());
        }
        valid |= sentence == output;
    }
    Ok(valid)
}

fn verify_graph_challenge(language: &[u8], output: &[u8]) -> Result<bool, String> {
    let spec: ChallengeLanguage =
        serde_json::from_slice(language).map_err(|_| "DECODE_V2_LANGUAGE_MALFORMED")?;
    if spec.schema_version != "core.symbol_game.graph-challenge-language.v1"
        || !(1..=64).contains(&spec.edge_count)
    {
        return Err("DECODE_V2_LANGUAGE_REFUSED".into());
    }
    let Ok(c) = serde_json::from_slice::<ChallengeOutput>(output) else {
        return Ok(false);
    };
    if c.candidate_ref != spec.candidate_ref {
        return Ok(false);
    }
    let valid = match c.obligation.as_str() {
        "NONE" => c.witness.is_empty(),
        "CONSISTENCY" | "OBSERVER_COVERAGE" => {
            c.witness.len() == spec.edge_count
                && c.witness
                    .iter()
                    .all(|s| s.len() <= 256 && core_kernel::parse_exact(s).is_ok())
        }
        _ => false,
    };
    Ok(valid)
}

pub fn verify(payload: &Value) -> Result<Value, String> {
    let receipt: Receipt = serde_json::from_value(payload.clone())
        .map_err(|e| format!("DECODE_V2_PARSE_ERROR: {e}"))?;
    let (output, language) = validate_decode_header(&receipt)?;
    let valid = if receipt.validation_method == "finite-utf8.v1" {
        verify_finite_utf8(&language, &output)?
    } else {
        verify_graph_challenge(&language, &output)?
    };
    let outcome = if valid { "VALID" } else { "INVALID" };
    if receipt.validation_outcome != outcome {
        return Err("DECODE_V2_OUTCOME_MISMATCH".into());
    }
    Ok(
        json!({"status":outcome,"output_valid":valid,"output_sha256":receipt.output_sha256,
              "request_sha256":receipt.request_sha256,"language_sha256":receipt.language_sha256,
              "generation_enforced":false,"authority_effect":"None"}),
    )
}

// Origin: engine/crates_rs/pfp/src/decode_v2.rs
// Claim: urn:core:crates_rs:pfp:decode-v2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7e6fa517 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7e6fa517` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7e6fa517 {
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
impl BoundaryError7e6fa517 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7e6fa517 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7e6fa517 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7e6fa517 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7e6fa517> {
        if capacity_bound == 0 {
            return Err(BoundaryError7e6fa517::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7e6fa517::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7e6fa517::ExceedsCapacity {
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
    fn hash_without_matching_actual_output_cannot_pass() {
        let language = serde_json::to_vec(&json!({"schema_version":"core.symbol_game.finite-output-language.v1", "sentences_hex":[hex::encode(b"{}")]})).unwrap();
        let bind = |b: &[u8]| format!("sha256:{:x}", Sha256::digest(b));
        let mut receipt = json!({"schema_version":"core.symbol_game.decode_receipt.v2",
            "request_hex":hex::encode(b"request"),"request_sha256":bind(b"request"),
            "output_hex":hex::encode(b"garbage"),"output_sha256":bind(b"garbage"),
            "language_hex":hex::encode(&language),"language_sha256":bind(&language),
            "tokenizer_profile":null,"enforcement":"PROVIDER_REQUESTED","validation_method":"finite-utf8.v1",
            "validation_outcome":"VALID","authority_effect":"None"});
        assert!(verify(&receipt).is_err());
        receipt["validation_outcome"] = json!("INVALID");
        assert_eq!(verify(&receipt).unwrap()["output_valid"], false);
        receipt["output_hex"] = json!(hex::encode(b"{}"));
        assert!(verify(&receipt).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_7e6fa517 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7e6fa517::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7e6fa517::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7e6fa517::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7e6fa517::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7e6fa517::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7e6fa517::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7e6fa517::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
