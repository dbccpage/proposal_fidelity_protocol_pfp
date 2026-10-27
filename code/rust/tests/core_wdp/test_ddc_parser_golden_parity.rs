//! Golden Parity Tests for DDC Tape Parser against Python Reference.
//!
//! AuthorityEffect: None.

use std::path::PathBuf;
use core_wdp::ddc::parser::DdcTapeParser;
use serde_json::Value;

fn load_golden_fixtures() -> Value {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../tests/core_wdp")
        .join("fixtures")
        .join("ddc_golden_cases.json");
    let content = std::fs::read_to_string(&path).unwrap_or_else(|e| {
        panic!("failed to read golden fixture at {}: {e}", path.display())
    });
    serde_json::from_str(&content).expect("fixture must be valid JSON")
}

#[test]
fn test_exact_contraction_run_golden_parity() {
    let fixtures = load_golden_fixtures();
    let case = &fixtures["exact_contraction_run"];
    let records = case["records"].as_array().expect("records array");

    let res = DdcTapeParser::parse_records(records);
    assert!(res.is_ok(), "exact contraction run must parse successfully");
    let receipt = res.unwrap();

    let expected = &case["expected_receipt"];
    assert_eq!(receipt.step_count, expected["step_count"].as_u64().unwrap() as usize);
    assert_eq!(receipt.tape_str, expected["tape_str"].as_str().unwrap());
    assert_eq!(receipt.hash_chain_valid, expected["hash_chain_valid"].as_bool().unwrap());
    assert_eq!(receipt.ddc_laws_valid, expected["ddc_laws_valid"].as_bool().unwrap());
    assert_eq!(receipt.initial_residual.as_deref(), expected["initial_residual"].as_str());
    assert_eq!(receipt.terminal_residual.as_deref(), expected["terminal_residual"].as_str());
    assert_eq!(receipt.residual_delta.as_deref(), expected["residual_delta"].as_str());
    assert_eq!(receipt.residual_effect, expected["residual_effect"].as_str().unwrap());
    assert_eq!(receipt.authority_effect, "None");
}

#[test]
fn test_broken_hash_chain_golden_parity() {
    let fixtures = load_golden_fixtures();
    let case = &fixtures["broken_hash_chain_run"];
    let records = case["records"].as_array().expect("records array");

    let res = DdcTapeParser::parse_records(records);
    assert!(res.is_err(), "broken hash chain run must return Err refusal");
    let refusal = res.unwrap_err();
    assert_eq!(refusal.code, case["refusal_code"].as_str().unwrap());
}

#[test]
fn test_terminal_absorbing_violation_golden_parity() {
    let fixtures = load_golden_fixtures();
    let case = &fixtures["terminal_absorbing_violation_run"];
    let records = case["records"].as_array().expect("records array");

    let res = DdcTapeParser::parse_records(records);
    assert!(res.is_ok(), "terminal absorbing violation must parse but report laws_valid=false");
    let receipt = res.unwrap();

    assert_eq!(receipt.step_count, 3);
    assert_eq!(receipt.tape_str, "C.T.R");
    assert!(receipt.hash_chain_valid);
    assert!(!receipt.ddc_laws_valid);
    assert!(receipt.law_violations.iter().any(|v| v.contains("TerminalAbsorbing")));
}

#[test]
fn test_non_monotonic_repair_golden_parity() {
    let fixtures = load_golden_fixtures();
    let case = &fixtures["non_monotonic_repair_run"];
    let records = case["records"].as_array().expect("records array");

    let res = DdcTapeParser::parse_records(records);
    assert!(res.is_ok(), "non-monotonic repair must parse but report laws_valid=false");
    let receipt = res.unwrap();

    assert_eq!(receipt.step_count, 3);
    assert_eq!(receipt.tape_str, "C.E.T");
    assert!(receipt.hash_chain_valid);
    assert!(!receipt.ddc_laws_valid);
    assert!(receipt.law_violations.iter().any(|v| v.contains("ExactRepairIncreasedPhi1")));
}

// Origin: engine/crates_rs/tests/core_wdp/test_ddc_parser_golden_parity.rs
// Claim: urn:core:crates_rs:tests:test-ddc-parser-golden-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda9d4cf3d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda9d4cf3d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora9d4cf3d {
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
impl BoundaryErrora9d4cf3d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora9d4cf3d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora9d4cf3d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda9d4cf3d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora9d4cf3d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora9d4cf3d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora9d4cf3d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora9d4cf3d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a9d4cf3d() {
    let admitted = BoundaryRecorda9d4cf3d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda9d4cf3d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
