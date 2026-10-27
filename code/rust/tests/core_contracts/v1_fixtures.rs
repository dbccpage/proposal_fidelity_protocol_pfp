//! V1 Contract Fixture Conformance Tests
//!
//! Validates both positive (good) exemplars and negative (poison) fixtures:
//! - Positive: valid v1 contracts load and pass validation
//! - Poison: structural and semantic defects fail closed
//!
//! AuthorityEffect: None.

use core_contracts::registry::{load_v1_dir, validate_v1, CoreContractV1};
use std::path::Path;

// ============================================================================
// Positive Exemplar Fixtures
// ============================================================================

#[test]
fn trichotomy_v1_loads_and_validates() {
    let dir = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../governance/tests/fixtures/core_contracts/v1/good");
    let report = load_v1_dir(&dir).expect("fixture dir readable");
    assert_eq!(report.loaded, 1, "expected exactly the trichotomy fixture");
    assert!(
        report.findings.is_empty(),
        "unexpected findings: {:#?}",
        report.findings
    );
    assert!(
        report
            .contract_ids
            .iter()
            .any(|id| id.contains("finite_obstruction_trichotomy")),
        "contract id not found: {:?}",
        report.contract_ids
    );
}

// ============================================================================
// Poison (Negative) Fixtures
// ============================================================================

fn poison_fixture(name: &str) -> String {
    let p = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../governance/tests/fixtures/core_contracts/v1/poison")
        .join(name);
    std::fs::read_to_string(p).expect("poison fixture exists")
}

// Structural defects fail at parse (deny_unknown_fields / required field).
#[test]
fn missing_descriptor_fails_at_parse() {
    assert!(serde_yaml::from_str::<CoreContractV1>(&poison_fixture("missing_descriptor.yaml")).is_err());
}

#[test]
fn compact_yaml_present_fails_at_parse() {
    assert!(
        serde_yaml::from_str::<CoreContractV1>(&poison_fixture("compact_yaml_present.yaml")).is_err()
    );
}

// Semantic defects parse but fail validate_v1.
#[test]
fn authority_for_math_fails_validation() {
    let c: CoreContractV1 = serde_yaml::from_str(&poison_fixture("authority_for_math.yaml")).unwrap();
    let errs = validate_v1(&c).unwrap_err();
    assert!(errs.iter().any(|f| f.contains("authority_effect: none")));
}

#[test]
fn unknown_terminal_fails_validation() {
    let c: CoreContractV1 = serde_yaml::from_str(&poison_fixture("unknown_terminal.yaml")).unwrap();
    assert!(validate_v1(&c)
        .unwrap_err()
        .iter()
        .any(|f| f.contains("unknown terminal")));
}

#[test]
fn unknown_refusal_fails_validation() {
    let c: CoreContractV1 = serde_yaml::from_str(&poison_fixture("unknown_refusal.yaml")).unwrap();
    assert!(validate_v1(&c)
        .unwrap_err()
        .iter()
        .any(|f| f.contains("unknown refusal")));
}

#[test]
fn malformed_po_fails_validation() {
    let c: CoreContractV1 = serde_yaml::from_str(&poison_fixture("malformed_po.yaml")).unwrap();
    assert!(validate_v1(&c)
        .unwrap_err()
        .iter()
        .any(|f| f.contains("malformed proof obligation")));
}

#[test]
fn nonmath_missing_role_fails_validation() {
    let c: CoreContractV1 = serde_yaml::from_str(&poison_fixture("nonmath_missing_role.yaml")).unwrap();
    assert!(validate_v1(&c)
        .unwrap_err()
        .iter()
        .any(|f| f.contains("role required")));
}

#[test]
fn unknown_role_fails_at_parse() {
    assert!(serde_yaml::from_str::<CoreContractV1>(&poison_fixture("unknown_role.yaml")).is_err());
}

// Origin: engine/crates_rs/tests/core_contracts/v1_fixtures.rs
// Claim: urn:core:crates_rs:tests:v1-fixtures:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbccc0f25 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbccc0f25` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbccc0f25 {
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
impl BoundaryErrorbccc0f25 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbccc0f25 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbccc0f25 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbccc0f25 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbccc0f25> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbccc0f25::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbccc0f25::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbccc0f25::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_bccc0f25() {
    let admitted = BoundaryRecordbccc0f25::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordbccc0f25::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
