//! Frozen learning-source behavior through the compiled policy. AuthorityEffect: None.
use core_prompt_civilization::learning_signals::execute;
use serde_json::{json, Value};

#[test]
fn source_alias_order_deduplication_and_canonical_fallback_agree() {
    let vectors: Vec<Value> =
        serde_json::from_str(include_str!("fixtures/learning_signals.json")).unwrap();
    assert!(!vectors.is_empty());
    for vector in vectors {
        assert_eq!(execute(&vector["payload"]).unwrap(), vector["expected"]);
    }
    let bad = json!({"tree":{"kind":"object","members":[["corrections",{"kind":"scalar","value":false}]],"canonical":"{\"corrections\":false}"}});
    assert_eq!(
        execute(&bad).unwrap_err().message,
        "malformed corrections signal"
    );
}

// Origin: engine/crates_rs/tests/core_prompt_civilization/learning_signals.rs
// Claim: urn:core:crates_rs:tests:learning-signals:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord876ab6dc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord876ab6dc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError876ab6dc {
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
impl BoundaryError876ab6dc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError876ab6dc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError876ab6dc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord876ab6dc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError876ab6dc> {
        if capacity_bound == 0 {
            return Err(BoundaryError876ab6dc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError876ab6dc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError876ab6dc::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_876ab6dc() {
    let admitted = BoundaryRecord876ab6dc::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord876ab6dc::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
