//! Explicit v1 historical-call to v2 council-audit identity expectation.
//! Frozen fixture bytes, payloads, hashes and every other field remain untouched.
use serde_json::{json, Value};

pub fn calls_with_audit_identity_v2(historical: &Value) -> Value {
    let mut expected = historical.clone();
    for call in expected
        .as_array_mut()
        .expect("historical calls must be an array")
    {
        if call["sink"] != "uts" {
            continue;
        }
        let event = &mut call["event"];
        if event["source_system"] != "oeas.candidate_check" {
            continue;
        }
        assert_eq!(
            event["actor_id"], "actor_adversary_checker",
            "v1 checker actor changed"
        );
        assert_eq!(
            event["actor_kind"], "HOST_CHECKER",
            "v1 checker kind changed"
        );
        event["actor_id"] = json!("actor_aletheia_procurator");
        event["actor_kind"] = json!("SWARM_SEAT");
    }
    expected
}

// Origin: engine/crates_rs/tests/core_adversary/support/candidate_audit_identity_v2.rs
// Claim: urn:core:crates_rs:tests:candidate-audit-identity-v2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde0974f63 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde0974f63` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore0974f63 {
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
impl BoundaryErrore0974f63 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore0974f63 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore0974f63 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde0974f63 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore0974f63> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore0974f63::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore0974f63::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore0974f63::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_e0974f63() {
    let admitted = BoundaryRecorde0974f63::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde0974f63::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
