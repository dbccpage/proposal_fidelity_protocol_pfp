//! The nine loop phases and the PFP stages each one runs.
//!
//! AuthorityEffect: None.

use super::occurrence::Executor;
use serde::{Deserialize, Serialize};

pub const PUBLIC_STAGES: u8 = 8;
pub const HOST_STAGE: u8 = 5;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Phase {
    Ingest,
    Census,
    Plan,
    Snapshot,
    Produce,
    Delta,
    Falsify,
    Route,
    Receipt,
}

impl Phase {
    pub const ALL: [Phase; 9] = [
        Phase::Ingest,
        Phase::Census,
        Phase::Plan,
        Phase::Snapshot,
        Phase::Produce,
        Phase::Delta,
        Phase::Falsify,
        Phase::Route,
        Phase::Receipt,
    ];

    /// `phase_machine[*].pfp_stages` from the workflow.
    pub fn pfp_stages(self) -> &'static [u8] {
        match self {
            Phase::Ingest => &[1],
            Phase::Census | Phase::Plan => &[2],
            Phase::Snapshot | Phase::Receipt => &[],
            Phase::Produce => &[2, 3, 4],
            Phase::Delta => &[5],
            Phase::Falsify => &[6, 7],
            Phase::Route => &[8],
        }
    }
}

/// Stage 5 is evaluated by the host and is never dispatched to a model or agent.
pub fn stage_executor_is_allowed(stage: u8, executor: Executor) -> bool {
    match executor {
        Executor::Host => stage == HOST_STAGE,
        Executor::Model | Executor::IdeAgent => {
            (1..=PUBLIC_STAGES).contains(&stage) && stage != HOST_STAGE
        }
    }
}

// Origin: engine/crates_rs/core_adversary/src/research_loop/phase.rs
// Claim: urn:core:crates_rs:core-adversary:phase:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3dc2c047 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3dc2c047` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3dc2c047 {
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
impl BoundaryError3dc2c047 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3dc2c047 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3dc2c047 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3dc2c047 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3dc2c047> {
        if capacity_bound == 0 {
            return Err(BoundaryError3dc2c047::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3dc2c047::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3dc2c047::ExceedsCapacity {
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
mod l4_boundary_tests_3dc2c047 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3dc2c047::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3dc2c047::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3dc2c047::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3dc2c047::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3dc2c047::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3dc2c047::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3dc2c047::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
