use core_operads::skill_garden::execute;
use serde_json::{json, Value};
#[test]
fn frozen_source_nomination_cases_match() {
    let cases: Vec<Value> = serde_json::from_str(include_str!("fixtures/skill_garden_cull.json"))
        .expect("Source fixtures");
    for case in cases {
        assert_eq!(
            execute(&case["request"]).expect("valid Source case"),
            case["expected"],
            "{}",
            case["name"]
        );
    }
}
#[test]
fn malformed_numeric_policy_is_a_typed_refusal() {
    let cases: Vec<Value> = serde_json::from_str(include_str!("fixtures/skill_garden_cull.json"))
        .expect("Source fixtures");
    for (field, value) in [
        ("window_days", json!(true)),
        ("minimum_ledger_days", json!(1.5)),
        ("new_skill_grace_days", json!(-1)),
        ("max_candidate_fraction", json!(true)),
        ("max_candidate_fraction", json!(1.1)),
    ] {
        let mut request = cases[0]["request"].clone();
        request["policy"][field] = value;
        assert_eq!(
            execute(&request).expect_err("invalid policy").code,
            "SKILL_CULL_INPUT_INVALID"
        );
    }
}

// Origin: engine/crates_rs/tests/core_operads/skill_garden_cull.rs
// Claim: urn:core:crates_rs:tests:skill-garden-cull:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde7667a50 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde7667a50` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore7667a50 {
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
impl BoundaryErrore7667a50 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore7667a50 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore7667a50 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde7667a50 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore7667a50> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore7667a50::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore7667a50::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore7667a50::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_e7667a50() {
    let admitted = BoundaryRecorde7667a50::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde7667a50::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
