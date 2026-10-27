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
    let reference = include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../ppo/rust_crates/RECEIPT.txt"
    ));
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

// Origin: engine/crates_rs/core_ooutwire_primitives/src/alpha_projection_obstruction/verify.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:verify:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5ffa14d3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5ffa14d3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5ffa14d3 {
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
impl BoundaryError5ffa14d3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5ffa14d3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5ffa14d3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5ffa14d3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5ffa14d3> {
        if capacity_bound == 0 {
            return Err(BoundaryError5ffa14d3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5ffa14d3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5ffa14d3::ExceedsCapacity {
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
mod l4_boundary_tests_5ffa14d3 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5ffa14d3::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5ffa14d3::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5ffa14d3::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5ffa14d3::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5ffa14d3::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5ffa14d3::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5ffa14d3::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
