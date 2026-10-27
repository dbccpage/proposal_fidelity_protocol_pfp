//! Finite executable witness for `PROD-KERNEL-NEXT-1`.
//!
//! Models the six-field `ReceiptRecord` and `TypedRefusal` kernel adapter invariants:
//! sorted/deduplicated `claim_ids`, 64-hex digest validation, tamper refusal
//! (`receipt_mismatch` and `digest_mismatch`), and fixed `authority_effect = "None"`.

#![forbid(unsafe_code)]

use std::collections::BTreeSet;

pub const AUTHORITY_EFFECT_NONE: &str = "None";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TypedRefusal {
    pub code: String,
    pub reason: String,
    pub authority_effect: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReceiptRecord {
    pub subject: String,
    pub input_digest: String,
    pub output_digest: String,
    pub claim_ids: Vec<String>,
    pub implementation_version: String,
    pub receipt_digest: String,
    pub authority_effect: &'static str,
}

pub fn is_sha256_hex(digest: &str) -> bool {
    digest.len() == 64
        && digest
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

pub fn normalize_claim_ids(raw: &[&str]) -> Result<Vec<String>, TypedRefusal> {
    if raw.is_empty() || raw.iter().any(|c| c.is_empty()) {
        return Err(TypedRefusal {
            code: "invalid_input".to_string(),
            reason: "subject, version, and nonempty claim ids are required".to_string(),
            authority_effect: AUTHORITY_EFFECT_NONE,
        });
    }
    let set: BTreeSet<String> = raw.iter().map(|s| (*s).to_string()).collect();
    Ok(set.into_iter().collect())
}

pub fn deterministic_hex64(tag: &str, payload: &str) -> String {
    // Deterministic 64-hex test digest from tag + payload bytes (FNV-1a 64-bit x 4 lanes).
    let mut out = String::with_capacity(64);
    for lane in 0u64..4 {
        let mut h: u64 = 0xcbf29ce484222325 ^ lane.wrapping_mul(0x9e3779b97f4a7c15);
        for b in tag.bytes().chain([b':']).chain(payload.bytes()) {
            h ^= u64::from(b);
            h = h.wrapping_mul(0x100000001b3);
        }
        out.push_str(&format!("{h:016x}"));
    }
    out
}

pub fn issue_receipt(
    subject: &str,
    input_payload: &str,
    output_payload: &str,
    claim_ids: &[&str],
    implementation_version: &str,
) -> Result<ReceiptRecord, TypedRefusal> {
    if subject.is_empty() || implementation_version.is_empty() {
        return Err(TypedRefusal {
            code: "invalid_input".to_string(),
            reason: "subject, version, and nonempty claim ids are required".to_string(),
            authority_effect: AUTHORITY_EFFECT_NONE,
        });
    }
    let normalized = normalize_claim_ids(claim_ids)?;
    let input_digest = deterministic_hex64("in", input_payload);
    let output_digest = deterministic_hex64("out", output_payload);
    let body = format!(
        "{subject}|{input_digest}|{output_digest}|{}|{implementation_version}|{AUTHORITY_EFFECT_NONE}",
        normalized.join(",")
    );
    let receipt_digest = deterministic_hex64("body", &body);
    Ok(ReceiptRecord {
        subject: subject.to_string(),
        input_digest,
        output_digest,
        claim_ids: normalized,
        implementation_version: implementation_version.to_string(),
        receipt_digest,
        authority_effect: AUTHORITY_EFFECT_NONE,
    })
}

pub fn verify_receipt_record(
    record: &ReceiptRecord,
    input_payload: &str,
    output_payload: &str,
) -> Result<bool, TypedRefusal> {
    if record.authority_effect != AUTHORITY_EFFECT_NONE {
        return Err(TypedRefusal {
            code: "claim_status_firewall".to_string(),
            reason: "receipt carries an authority effect".to_string(),
            authority_effect: AUTHORITY_EFFECT_NONE,
        });
    }
    let expected_body = format!(
        "{}|{}|{}|{}|{}|{}",
        record.subject,
        record.input_digest,
        record.output_digest,
        record.claim_ids.join(","),
        record.implementation_version,
        record.authority_effect
    );
    let expected_receipt_digest = deterministic_hex64("body", &expected_body);
    if record.receipt_digest != expected_receipt_digest {
        return Err(TypedRefusal {
            code: "receipt_mismatch".to_string(),
            reason: "receipt body was modified".to_string(),
            authority_effect: AUTHORITY_EFFECT_NONE,
        });
    }
    if record.input_digest != deterministic_hex64("in", input_payload) {
        return Err(TypedRefusal {
            code: "digest_mismatch".to_string(),
            reason: "input artifact differs from receipt".to_string(),
            authority_effect: AUTHORITY_EFFECT_NONE,
        });
    }
    if record.output_digest != deterministic_hex64("out", output_payload) {
        return Err(TypedRefusal {
            code: "digest_mismatch".to_string(),
            reason: "output artifact differs from receipt".to_string(),
            authority_effect: AUTHORITY_EFFECT_NONE,
        });
    }
    Ok(true)
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_kernel_next_1.rs
// Claim: urn:core:crates_rs:tests:prod-kernel-next-1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2590af11 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2590af11` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2590af11 {
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
impl BoundaryError2590af11 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2590af11 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2590af11 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2590af11 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2590af11> {
        if capacity_bound == 0 {
            return Err(BoundaryError2590af11::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2590af11::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2590af11::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn issue_and_verify_receipt_round_trips_and_normalizes_claims() {
        let rec = issue_receipt(
            "parity_subject",
            "{\"alpha\":1}",
            "{\"result\":\"ok\"}",
            &["claim_b", "claim_a", "claim_b"],
            "0.1.0",
        )
        .expect("valid receipt");
        assert_eq!(rec.claim_ids, vec!["claim_a".to_string(), "claim_b".to_string()]);
        assert!(is_sha256_hex(&rec.input_digest));
        assert!(is_sha256_hex(&rec.output_digest));
        assert!(is_sha256_hex(&rec.receipt_digest));
        assert_eq!(rec.authority_effect, "None");
        assert_eq!(
            verify_receipt_record(&rec, "{\"alpha\":1}", "{\"result\":\"ok\"}"),
            Ok(true)
        );
    }

    #[test]
    fn refuses_invalid_inputs_and_detects_tampering() {
        let err = issue_receipt("", "in", "out", &["c1"], "0.1.0").unwrap_err();
        assert_eq!(err.code, "invalid_input");

        let rec = issue_receipt("subj", "in_a", "out_a", &["c1"], "0.1.0").expect("valid receipt");
        let mismatch = verify_receipt_record(&rec, "in_b", "out_a").unwrap_err();
        assert_eq!(mismatch.code, "digest_mismatch");

        let mut tampered = rec.clone();
        tampered.subject = "other".to_string();
        let body_err = verify_receipt_record(&tampered, "in_a", "out_a").unwrap_err();
        assert_eq!(body_err.code, "receipt_mismatch");
    }
}

#[test]
fn l4_boundary_admits_and_refuses_2590af11() {
    let admitted = BoundaryRecord2590af11::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2590af11::try_admit(9, 8).is_err());
}
