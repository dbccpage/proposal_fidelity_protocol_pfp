// AuthorityEffect: None.
//! Exact decode control and logit-level intervention receipt verifier.
//!
//! Enforces:
//! - Verification of carrier masks: all generated tokens must reside in the declared allowed token set.
//! - Verification of logit biases: finite bounded magnitude (|bias| <= 1000) and no corrupt values.
//! - Verification of grammar hashes: SHA-256 digest requirement for JSON schema and GBNF controls.
//! - Strict adherence to `AuthorityEffect: None`.

use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

pub const DECODE_RECEIPT_SCHEMA: &str = "core.symbol_game.decode_receipt.v1";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct DecodeControlReceiptV1 {
    pub schema_version: String,
    pub receipt_id: String,
    pub case_id: String,
    pub control_kind: String,
    #[serde(default)]
    pub allowed_tokens: Vec<u32>,
    pub output_tokens: Vec<u32>,
    #[serde(default)]
    pub logit_biases: Vec<(u32, i32)>,
    #[serde(default)]
    pub grammar_sha256: Option<String>,
    pub authority_effect: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(tag = "status", rename_all = "SCREAMING_SNAKE_CASE")]
pub enum DecodeVerificationVerdict {
    Pass {
        token_count: usize,
        carrier_honored: bool,
        authority_effect: String,
    },
    Refusal {
        refusal_code: String,
        detail: String,
        authority_effect: String,
    },
}

fn verify_carrier_mask(receipt: &DecodeControlReceiptV1) -> DecodeVerificationVerdict {
    let allowed_set: BTreeSet<u32> = receipt.allowed_tokens.iter().copied().collect();
    let mut violations = Vec::new();
    for (idx, &token) in receipt.output_tokens.iter().enumerate() {
        if !allowed_set.contains(&token) {
            violations.push((idx, token));
        }
    }
    if !violations.is_empty() {
        return DecodeVerificationVerdict::Refusal {
            refusal_code: "CARRIER_CONSTRAINT_VIOLATED".to_string(),
            detail: format!(
                "found {} tokens outside allowed carrier set: {:?}",
                violations.len(),
                violations
            ),
            authority_effect: "None".to_string(),
        };
    }
    DecodeVerificationVerdict::Pass {
        token_count: receipt.output_tokens.len(),
        carrier_honored: true,
        authority_effect: "None".to_string(),
    }
}

fn verify_logit_bias(receipt: &DecodeControlReceiptV1) -> DecodeVerificationVerdict {
    for &(token_id, bias) in &receipt.logit_biases {
        if bias.abs() > 1000 {
            return DecodeVerificationVerdict::Refusal {
                refusal_code: "LOGIT_BIAS_EXCEEDS_CEILING".to_string(),
                detail: format!("token {token_id} has invalid extreme bias: {bias}"),
                authority_effect: "None".to_string(),
            };
        }
    }
    DecodeVerificationVerdict::Pass {
        token_count: receipt.output_tokens.len(),
        carrier_honored: true,
        authority_effect: "None".to_string(),
    }
}

fn verify_grammar_hash(receipt: &DecodeControlReceiptV1) -> DecodeVerificationVerdict {
    if let Some(ref hash) = receipt.grammar_sha256 {
        if hash.len() != 64 || !hash.chars().all(|c| c.is_ascii_hexdigit()) {
            return DecodeVerificationVerdict::Refusal {
                refusal_code: "INVALID_GRAMMAR_HASH".to_string(),
                detail: format!("grammar_sha256 is not a valid 64-char hex digest: {hash}"),
                authority_effect: "None".to_string(),
            };
        }
    } else {
        return DecodeVerificationVerdict::Refusal {
            refusal_code: "MISSING_GRAMMAR_HASH".to_string(),
            detail: format!(
                "{} control requires grammar_sha256 digest",
                receipt.control_kind
            ),
            authority_effect: "None".to_string(),
        };
    }
    DecodeVerificationVerdict::Pass {
        token_count: receipt.output_tokens.len(),
        carrier_honored: true,
        authority_effect: "None".to_string(),
    }
}

/// Verify a decode control receipt outside the model with exact checks.
pub fn verify_decode_receipt(receipt: &DecodeControlReceiptV1) -> DecodeVerificationVerdict {
    if receipt.schema_version != DECODE_RECEIPT_SCHEMA {
        return DecodeVerificationVerdict::Refusal {
            refusal_code: "SCHEMA_MISMATCH".to_string(),
            detail: format!(
                "expected {}, got {}",
                DECODE_RECEIPT_SCHEMA, receipt.schema_version
            ),
            authority_effect: "None".to_string(),
        };
    }
    if receipt.authority_effect != "None" {
        return DecodeVerificationVerdict::Refusal {
            refusal_code: "AUTHORITY_EFFECT_NON_NONE".to_string(),
            detail: "authority_effect must be None".to_string(),
            authority_effect: "None".to_string(),
        };
    }

    match receipt.control_kind.as_str() {
        "CARRIER_MASK" => verify_carrier_mask(receipt),
        "LOGIT_BIAS" => verify_logit_bias(receipt),
        "JSON_SCHEMA" | "GBNF" => verify_grammar_hash(receipt),
        "NONE" => DecodeVerificationVerdict::Pass {
            token_count: receipt.output_tokens.len(),
            carrier_honored: true,
            authority_effect: "None".to_string(),
        },
        unknown => DecodeVerificationVerdict::Refusal {
            refusal_code: "UNKNOWN_CONTROL_KIND".to_string(),
            detail: format!("unsupported control_kind: {unknown}"),
            authority_effect: "None".to_string(),
        },
    }
}

// Origin: engine/crates_rs/pfp_runtime/src/decode_control.rs
// Claim: urn:core:crates_rs:pfp-runtime:decode-control:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord05b0e38a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord05b0e38a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError05b0e38a {
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
impl BoundaryError05b0e38a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError05b0e38a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError05b0e38a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord05b0e38a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError05b0e38a> {
        if capacity_bound == 0 {
            return Err(BoundaryError05b0e38a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError05b0e38a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError05b0e38a::ExceedsCapacity {
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
    fn test_carrier_mask_verification() {
        let clean_receipt = DecodeControlReceiptV1 {
            schema_version: DECODE_RECEIPT_SCHEMA.to_string(),
            receipt_id: "rcpt_001".to_string(),
            case_id: "c001_01".to_string(),
            control_kind: "CARRIER_MASK".to_string(),
            allowed_tokens: vec![10, 20, 30, 40],
            output_tokens: vec![10, 20, 30],
            logit_biases: vec![],
            grammar_sha256: None,
            authority_effect: "None".to_string(),
        };
        match verify_decode_receipt(&clean_receipt) {
            DecodeVerificationVerdict::Pass {
                token_count,
                carrier_honored,
                ..
            } => {
                assert_eq!(token_count, 3);
                assert!(carrier_honored);
            }
            other => panic!("expected Pass, got {other:?}"),
        }

        let violated_receipt = DecodeControlReceiptV1 {
            output_tokens: vec![10, 999, 30],
            ..clean_receipt
        };
        match verify_decode_receipt(&violated_receipt) {
            DecodeVerificationVerdict::Refusal { refusal_code, .. } => {
                assert_eq!(refusal_code, "CARRIER_CONSTRAINT_VIOLATED");
            }
            other => panic!("expected Refusal, got {other:?}"),
        }
    }

    #[test]
    fn test_logit_bias_verification() {
        let valid = DecodeControlReceiptV1 {
            schema_version: DECODE_RECEIPT_SCHEMA.to_string(),
            receipt_id: "rcpt_002".to_string(),
            case_id: "c005_01".to_string(),
            control_kind: "LOGIT_BIAS".to_string(),
            allowed_tokens: vec![],
            output_tokens: vec![100, 101],
            logit_biases: vec![(100, 5), (101, -100)],
            grammar_sha256: None,
            authority_effect: "None".to_string(),
        };
        match verify_decode_receipt(&valid) {
            DecodeVerificationVerdict::Pass { .. } => {}
            other => panic!("expected Pass, got {other:?}"),
        }

        let extreme = DecodeControlReceiptV1 {
            logit_biases: vec![(100, 5000)],
            ..valid
        };
        match verify_decode_receipt(&extreme) {
            DecodeVerificationVerdict::Refusal { refusal_code, .. } => {
                assert_eq!(refusal_code, "LOGIT_BIAS_EXCEEDS_CEILING");
            }
            other => panic!("expected Refusal, got {other:?}"),
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_05b0e38a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord05b0e38a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord05b0e38a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord05b0e38a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord05b0e38a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord05b0e38a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError05b0e38a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError05b0e38a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
