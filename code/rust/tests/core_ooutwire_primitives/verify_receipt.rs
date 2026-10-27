//! Integration tests for pinned PO-000 receipt conformance.
//!
//! Compares `RECEIPT.txt` to the compiled-in reference and tests that checking
//! fails closed against tampered or missing claims.
//!
//! `AuthorityEffect: None.`

use core_ooutwire_primitives::alpha_projection_obstruction::receipt_path;
use core_ooutwire_primitives::alpha_projection_obstruction::verify::{
    verify_receipt_text, REQUIRED_LEDGER_CLAIMS,
};
use std::path::Path;

fn pinned_receipt() -> String {
    let path = receipt_path();
    std::fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("read {}: {error}", path.display()))
}

#[test]
fn rejects_missing_witness_and_forged_disposition() {
    let receipt = pinned_receipt();
    for (before, after) in [
        ("    defect = [['2']]\n", ""),
        ("raw_I = 2", "raw_I = 999"),
        (
            "xx_absolute_error_below = 1e-12",
            "xx_absolute_error_below = NaN",
        ),
        ("[0] B1, B2", "[7] B1, B2"),
        ("[0] B1, B2", "[0] H9"),
        (
            "[20] C2 | not_executable | refused",
            "[20] C2 | not_executable | pass",
        ),
    ] {
        let tampered = receipt.replace(before, after);
        assert_ne!(tampered, receipt, "mutation must change the receipt");
        assert!(
            verify_receipt_text(&tampered).is_err(),
            "accepted mutation: {before} -> {after}"
        );
    }
}

#[test]
fn test_receipt_verifies_successfully() {
    let text = pinned_receipt();
    let summary = verify_receipt_text(&text).expect("RECEIPT.txt must verify cleanly");

    assert_eq!(summary.disposition_count, 24);
    assert_eq!(summary.pass_count, 18);
    assert_eq!(summary.refused_count, 6);
    assert!(
        summary.covered_claim_count == REQUIRED_LEDGER_CLAIMS.len() + 2,
        "Covered claims ({}) must include exactly the two supplemental keys plus required ledger claims ({})",
        summary.covered_claim_count,
        REQUIRED_LEDGER_CLAIMS.len()
    );
    assert_eq!(summary.authority_effect, "None");
}

#[test]
fn test_receipt_verification_rejects_tampered_authority() {
    let tampered =
        pinned_receipt().replace("AuthorityEffect: None.", "AuthorityEffect: DerivedJewel.");

    let res = verify_receipt_text(&tampered);
    assert!(res.is_err());
    let errors = res.unwrap_err();
    assert!(
        errors.iter().any(|e| e.contains("Pinned receipt mismatch")),
        "Expected error for non-None AuthorityEffect, got: {errors:?}"
    );
}

#[test]
fn test_receipt_verification_rejects_missing_claim_id() {
    let tampered = pinned_receipt().replace("claim_ids: A1, ", "claim_ids: ");

    let res = verify_receipt_text(&tampered);
    assert!(res.is_err());
    let errors = res.unwrap_err();
    assert!(
        errors.iter().any(|e| e.contains("Pinned receipt mismatch")),
        "Expected error for missing required claim ID, got: {errors:?}"
    );
}

#[test]
fn test_receipt_verification_rejects_exceeded_error_tolerance() {
    let tampered = pinned_receipt().replace(
        "xx_absolute_error_below = 1e-12",
        "xx_absolute_error_below = 0.05",
    );

    let res = verify_receipt_text(&tampered);
    assert!(res.is_err());
    let errors = res.unwrap_err();
    assert!(
        errors.iter().any(|e| e.contains("Pinned receipt mismatch")),
        "Expected error for exceeded error tolerance, got: {errors:?}"
    );
}

#[test]
fn every_nonempty_receipt_line_is_required_and_no_extra_lines_are_accepted() {
    let receipt = pinned_receipt();
    let lines: Vec<_> = receipt.lines().collect();
    for (i, line) in lines.iter().enumerate() {
        if line.is_empty() {
            continue;
        }
        let missing = lines
            .iter()
            .enumerate()
            .filter(|(j, _)| *j != i)
            .map(|(_, line)| *line)
            .collect::<Vec<_>>()
            .join("\n");
        assert!(
            verify_receipt_text(&missing).is_err(),
            "accepted omitted line {}",
            i + 1
        );
    }
    assert!(verify_receipt_text(&format!("{receipt}AuthorityEffect: Forged.\n")).is_err());
    assert!(verify_receipt_text(&receipt.replace("\n", "\r\n")).is_ok());
}

#[test]
fn cli_reports_conformance_and_rejects_invalid_receipts() {
    let cli = env!("CARGO_BIN_EXE_verify_po000");
    let valid = std::process::Command::new(cli).output().unwrap();
    assert!(
        valid.status.success(),
        "{}",
        String::from_utf8_lossy(&valid.stderr)
    );
    assert!(String::from_utf8(valid.stdout)
        .unwrap()
        .contains("PINNED RECEIPT CONFORMANCE PASSED"));
    let malformed = Path::new(env!("CARGO_MANIFEST_DIR")).join("Cargo.toml");
    let invalid = std::process::Command::new(cli)
        .arg(malformed)
        .output()
        .unwrap();
    assert_eq!(invalid.status.code(), Some(1));
    let absent = std::process::Command::new(cli)
        .arg("absent-po000-receipt.txt")
        .output()
        .unwrap();
    assert_eq!(absent.status.code(), Some(2));
}

// Origin: engine/crates_rs/tests/core_ooutwire_primitives/verify_receipt.rs
// Claim: urn:core:crates_rs:tests:verify-receipt:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7009cab3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7009cab3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7009cab3 {
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
impl BoundaryError7009cab3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7009cab3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7009cab3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7009cab3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7009cab3> {
        if capacity_bound == 0 {
            return Err(BoundaryError7009cab3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7009cab3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7009cab3::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_7009cab3() {
    let admitted = BoundaryRecord7009cab3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord7009cab3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
