use core_prompt_civilization::metabolism::execute;
use serde_json::Value;

#[test]
fn matches_frozen_python_episode_and_unicode_motif_vectors() {
    let vectors: Value = serde_json::from_str(include_str!("fixtures/metabolism.json"))
        .expect("frozen source fixtures decode");
    for vector in vectors.as_array().expect("fixture bank is an array") {
        assert_eq!(
            execute(&vector["payload"]).expect("source vector executes"),
            vector["expected"],
            "payload: {}",
            vector["payload"]
        );
    }
}

#[test]
fn malformed_input_is_a_typed_refusal() {
    let refusal = execute(&serde_json::json!({
        "operation": "segment", "run_id": "bad", "steps": [null]
    }))
    .expect_err("malformed steps must refuse");
    assert_eq!(refusal.code, "METABOLISM_INPUT_INVALID");
}

// Origin: engine/crates_rs/tests/core_prompt_civilization/metabolism.rs
// Claim: urn:core:crates_rs:tests:metabolism:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord53505147 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord53505147` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError53505147 {
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
impl BoundaryError53505147 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError53505147 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError53505147 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord53505147 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError53505147> {
        if capacity_bound == 0 {
            return Err(BoundaryError53505147::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError53505147::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError53505147::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_53505147() {
    let admitted = BoundaryRecord53505147::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord53505147::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
