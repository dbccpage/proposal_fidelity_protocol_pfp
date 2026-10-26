//! Conformance checker for the pinned PO-000 v6.3 receipt.
//!
//! The checked-in receipt is the trusted reference, not evidence independently
//! derived here. Every line must match (LF and CRLF are interchangeable).
//! This rejects absent, extra, reordered, or changed fields, statuses, claim IDs,
//! and nonclaim boundaries. It does not establish the reference's mathematics.
//! The producer's separate replay test recomputes the pinned receipt.
//!
//! AuthorityEffect: None.

use std::collections::BTreeSet;

/// All 51 ledger claim IDs required by PO-000 v6.3.
pub const REQUIRED_LEDGER_CLAIMS: &[&str] = &[
    "A1",
    "A2",
    "A3",
    "A4",
    "A5",
    "A6",
    "A7",
    "B1",
    "B2",
    "B3",
    "B4",
    "C1",
    "C2",
    "C3",
    "C4",
    "D1",
    "D2",
    "D3",
    "D4",
    "D5",
    "D6",
    "D7",
    "D8",
    "D8a",
    "E1",
    "E2",
    "E3",
    "E4",
    "E4-commutator",
    "E4-second",
    "E5",
    "E6",
    "E7",
    "E8",
    "E9",
    "F1",
    "F2",
    "F3",
    "G1",
    "G2",
    "G3",
    "G4",
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "H7",
    "H8",
    "H9",
];

/// Counts from a receipt that matches the trusted reference.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerificationSummary {
    /// Number of recorded dispositions.
    pub disposition_count: usize,
    /// Total unique claim IDs recorded.
    pub covered_claim_count: usize,
    /// Number of recorded pass statuses; not independent proof approvals.
    pub pass_count: usize,
    /// Number of recorded refusals.
    pub refused_count: usize,
    /// Authority effect declared in the reference.
    pub authority_effect: String,
}

/// Check conformance to the compiled-in receipt, without running its producer.
///
/// No missing fields or unrecognized lines are silently ignored. Numeric changes
/// are rejected even within a tolerance: cross-machine numerical agreement is a
/// separate test. Updating the reference requires a new build and source review.
pub fn verify_receipt_text(text: &str) -> Result<VerificationSummary, Vec<String>> {
    let reference = include_str!("RECEIPT.txt");
    let actual: Vec<_> = text.lines().collect();
    let expected: Vec<_> = reference.lines().collect();
    if actual != expected {
        let mismatch = actual.iter().zip(&expected).position(|(a, b)| a != b);
        return Err(vec![format!(
            "Pinned receipt mismatch at line {} (expected {} lines, received {}); no mathematical verification performed",
            mismatch.unwrap_or(actual.len().min(expected.len())) + 1,
            expected.len(),
            actual.len()
        )]);
    }

    let claim_line = expected
        .iter()
        .find_map(|line| line.strip_prefix("claim_ids: "))
        .ok_or_else(|| vec!["Trusted reference is missing claim_ids".to_string()])?;
    let claims: BTreeSet<_> = claim_line.split(", ").collect();
    if REQUIRED_LEDGER_CLAIMS.iter().any(|id| !claims.contains(id)) || claims.len() != 53 {
        return Err(vec!["Trusted reference claim inventory is invalid".into()]);
    }
    let dispositions: Vec<_> = expected
        .iter()
        .filter(|line| line.starts_with('['))
        .collect();
    let pass_count = dispositions
        .iter()
        .filter(|line| line.ends_with(" | pass"))
        .count();
    let refused_count = dispositions
        .iter()
        .filter(|line| line.ends_with(" | refused"))
        .count();
    if dispositions.len() != 24 || pass_count != 18 || refused_count != 6 {
        return Err(vec![
            "Trusted reference disposition inventory is invalid".into()
        ]);
    }
    Ok(VerificationSummary {
        disposition_count: dispositions.len(),
        covered_claim_count: claims.len(),
        pass_count,
        refused_count,
        authority_effect: "None".into(),
    })
}
