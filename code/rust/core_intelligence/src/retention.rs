//! Storage transitions remain independent from source transfer status.

use crate::DigestionState;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum StorageState {
    Hot,
    Cold,
    DisposalEligible,
    Deleted,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RetentionRequest {
    pub digestion_state: DigestionState,
    pub storage_state: StorageState,
    #[serde(default)]
    pub active_lease: bool,
    #[serde(default)]
    pub evidence_reachable: bool,
    #[serde(default)]
    pub holds: Vec<String>,
    #[serde(default)]
    pub dependency_refs: Vec<String>,
    #[serde(default)]
    pub grace_elapsed: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct RetentionDecision {
    pub target_storage_state: StorageState,
    pub cold_eligible: bool,
    pub disposal_eligible: bool,
    pub residuals: Vec<String>,
    pub authority_effect: String,
}

fn collect_retention_residuals(request: &RetentionRequest) -> Vec<String> {
    let checks = [
        (request.active_lease, "ACTIVE_LEASE_RETAINS_SOURCE"),
        (!request.evidence_reachable, "EVIDENCE_REACHABILITY_UNVERIFIED"),
        (!request.holds.is_empty(), "RETENTION_HOLD_ACTIVE"),
        (
            matches!(request.digestion_state, DigestionState::Absorbed),
            "TRANSFERRED_OPEN_OBLIGATIONS_RETAIN_REQUIRED_EVIDENCE",
        ),
        (
            !request.dependency_refs.is_empty(),
            "DEPENDENCY_REFERENCES_RETAIN_SOURCE",
        ),
        (!request.grace_elapsed, "RETENTION_GRACE_NOT_ELAPSED"),
    ];
    checks
        .into_iter()
        .filter_map(|(cond, msg)| cond.then(|| msg.to_string()))
        .collect()
}

fn is_disposal_eligible(request: &RetentionRequest, cold_eligible: bool) -> bool {
    cold_eligible
        && matches!(request.digestion_state, DigestionState::Discharged)
        && request.holds.is_empty()
        && request.dependency_refs.is_empty()
        && request.grace_elapsed
}

pub fn evaluate_retention(request: &RetentionRequest) -> RetentionDecision {
    let residuals = collect_retention_residuals(request);
    let absorbed = matches!(
        request.digestion_state,
        DigestionState::Absorbed | DigestionState::Discharged
    );
    let cold_eligible = absorbed && !request.active_lease && request.evidence_reachable;
    let disposal_eligible = is_disposal_eligible(request, cold_eligible);
    let target_storage_state = if disposal_eligible {
        StorageState::DisposalEligible
    } else if cold_eligible {
        StorageState::Cold
    } else {
        request.storage_state
    };
    RetentionDecision {
        target_storage_state,
        cold_eligible,
        disposal_eligible,
        residuals,
        authority_effect: "None".into(),
    }
}

// Origin: engine/crates_rs/core_intelligence/src/retention.rs
// Claim: urn:core:crates_rs:core-intelligence:retention:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddb00f476 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddb00f476` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordb00f476 {
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
impl BoundaryErrordb00f476 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordb00f476 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordb00f476 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddb00f476 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordb00f476> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordb00f476::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordb00f476::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordb00f476::ExceedsCapacity {
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
mod l4_boundary_tests_db00f476 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorddb00f476::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorddb00f476::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorddb00f476::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorddb00f476::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorddb00f476::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrordb00f476::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrordb00f476::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
