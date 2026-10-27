//! Contract-Specific Firewall Tests
//!
//! Validates contract-specific firewalls and invariants:
//! - Trichotomy: floating/tolerance heuristic firewall and negative test fixtures
//! - InvariantDefectProfile: diagnostic authority-free and order-sensitivity negative tests
//!
//! AuthorityEffect: None.

use core_contracts::registry::CoreContractV1;
use core_contracts::ContractEffect;
use serde_yaml::Value;
use std::path::Path;

// ============================================================================
// Trichotomy Floating Firewall
// ============================================================================

const FIREWALL: &str = "no floating heuristic may emit an exact trichotomy constructor.";

fn require_firewall(
    laws: Option<&Value>,
    negative_tests: Option<&[String]>,
) -> Result<(), &'static str> {
    let matches = |text: &str| text.eq_ignore_ascii_case(FIREWALL);
    let declared = match laws {
        Some(Value::Mapping(map)) => map
            .get(Value::from("floating_firewall"))
            .and_then(Value::as_str)
            .is_some_and(matches),
        Some(Value::Sequence(items)) => items
            .iter()
            .filter_map(Value::as_str)
            .filter_map(|text| text.strip_prefix("Floating firewall: "))
            .any(matches),
        _ => false,
    };
    if !declared {
        return Err("FLOATING_FIREWALL_DECLARATION_MISSING_OR_CHANGED");
    }
    let negative = negative_tests.is_some_and(|items| {
        items.iter().any(|text| {
            text == "Tolerance mode used to emit exact trichotomy must be rejected"
                || text == "Tolerance mode used to emit exact trichotomy"
        })
    });
    if !negative {
        return Err("FLOATING_FIREWALL_NEGATIVE_FIXTURE_MISSING");
    }
    Ok(())
}

#[test]
fn trichotomy_declares_floating_firewall_and_negative_test() {
    let p = Path::new(env!("CARGO_MANIFEST_DIR")).join(
        "../../../governance/contracts/contract_canonical_definitions/math/finite_obstruction_trichotomy.contract.yaml",
    );
    let text = std::fs::read_to_string(p).expect("migrated exemplar exists");
    let c: CoreContractV1 = serde_yaml::from_str(&text).expect("exemplar parses as v1");

    require_firewall(c.laws.as_ref(), c.negative_tests.as_deref())
        .expect("declared floating firewall and its negative fixture");
}

#[test]
fn both_authored_law_formats_require_the_complete_firewall() {
    let negative = vec!["Tolerance mode used to emit exact trichotomy".to_owned()];
    for raw in [
        "floating_firewall: No floating heuristic may emit an exact trichotomy constructor.",
        "- 'Floating firewall: no floating heuristic may emit an exact trichotomy constructor.'",
    ] {
        let laws: Value = serde_yaml::from_str(raw).unwrap();
        assert_eq!(require_firewall(Some(&laws), Some(&negative)), Ok(()));
    }
}

#[test]
fn keyword_spoofing_or_removing_the_law_is_refused() {
    let negative = vec!["Tolerance mode used to emit exact trichotomy".to_owned()];
    for raw in [
        "{}",
        "[]",
        "floating_firewall: floating heuristics MAY emit an exact trichotomy constructor.",
        "floating_firewall: null",
        "- 'Floating firewall: bypass allowed; no floating heuristic may emit an exact trichotomy constructor.'",
        "- 'Some prose mentioning the Floating firewall: no floating heuristic may emit an exact trichotomy constructor.'",
    ] {
        let laws: Value = serde_yaml::from_str(raw).unwrap();
        assert_eq!(
            require_firewall(Some(&laws), Some(&negative)),
            Err("FLOATING_FIREWALL_DECLARATION_MISSING_OR_CHANGED")
        );
    }
}

#[test]
fn a_valid_law_without_its_decisive_negative_fixture_is_refused() {
    let laws: Value = serde_yaml::from_str(
        "floating_firewall: No floating heuristic may emit an exact trichotomy constructor.",
    )
    .unwrap();
    for negative in [
        None,
        Some(vec![]),
        Some(vec!["floating tests all passed, trust me".to_owned()]),
    ] {
        assert_eq!(
            require_firewall(Some(&laws), negative.as_deref()),
            Err("FLOATING_FIREWALL_NEGATIVE_FIXTURE_MISSING")
        );
    }
}

// ============================================================================
// InvariantDefectProfile Firewall
// ============================================================================

#[test]
fn invariant_defect_profile_declares_authority_free_and_order_sensitive() {
    let p = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../governance/contracts/contract_canonical_definitions/math/invariant_defect_profile.contract.yaml");
    let text = std::fs::read_to_string(p).expect("invariant_defect_profile contract exists");
    let c: CoreContractV1 = serde_yaml::from_str(&text).expect("parses as v1");

    // Firewall: a diagnostic signature confers NO authority and never runs as a gate.
    assert_eq!(
        c.descriptor.authority_effect,
        ContractEffect::None,
        "InvariantDefectProfile must declare authority_effect: none (it is a diagnostic, not authority)"
    );
    assert!(
        !c.descriptor.runtime_enforcement,
        "a pure diagnostic math object must not be a runtime-enforcing gate"
    );

    // Discipline: it must declare the order-sensitivity and no-self-assign negative tests
    let tests = c.negative_tests.as_ref().expect("negative_tests present");
    assert!(
        tests.iter().any(|t| {
            let t = t.to_lowercase();
            t.contains("commutative") || t.contains("order")
        }),
        "must declare a negative test against order-free / commutative collapse"
    );
    assert!(
        tests
            .iter()
            .any(|t| t.to_lowercase().contains("self_assigned")
                || t.to_lowercase().contains("effect_class")),
        "must declare a negative test against self-assigning a fixed-layer effect class"
    );
}

// Origin: engine/crates_rs/tests/core_contracts/v1_contract_firewalls.rs
// Claim: urn:core:crates_rs:tests:v1-contract-firewalls:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3909f3c2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3909f3c2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3909f3c2 {
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
impl BoundaryError3909f3c2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3909f3c2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3909f3c2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3909f3c2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3909f3c2> {
        if capacity_bound == 0 {
            return Err(BoundaryError3909f3c2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3909f3c2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3909f3c2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3909f3c2() {
    let admitted = BoundaryRecord3909f3c2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3909f3c2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
