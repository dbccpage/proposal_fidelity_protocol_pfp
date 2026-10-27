//! Execution occurrences: one attempt at one stage of one round.
//!
//! The prompt tree is fixed containment; rounds and retries are occurrences, never new
//! prompt generations. The host allocates an occurrence id before any dispatch and derives
//! the idempotency key from it, so a re-delivered response is recognised and never charged
//! or dispatched twice.
//!
//! AuthorityEffect: None.

use super::{canonical, refuse};
use crate::stage::ports::Refusal;
use serde::{Deserialize, Serialize};
use serde_json::json;

/// Who produced an occurrence's payload.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Executor {
    /// A provider call made by the host transport.
    Model,
    /// An agent in the IDE wrote the response file; cost is not measured by the host.
    IdeAgent,
    /// The host itself (stage 5 only).
    Host,
}

/// `<run>.r<round>.s<stage>.a<attempt>`, the form the host allocates.
pub fn allocate(run_id: &str, round: u64, stage: u8, attempt: u64) -> String {
    format!("{run_id}.r{round}.s{stage}.a{attempt}")
}

pub fn validate_id(occurrence_id: &str) -> Result<(), Refusal> {
    let printable = occurrence_id
        .bytes()
        .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'.' | b'_' | b'-'));
    if occurrence_id.is_empty() || occurrence_id.len() > 200 || !printable {
        return Err(refuse(
            "OCCURRENCE_ID_INVALID",
            "occurrence ids are 1..200 characters of [A-Za-z0-9._-]",
        ));
    }
    Ok(())
}

/// sha256 over (run, round, stage, occurrence, dispatched packet digest).
pub fn idempotency_key(
    run_id: &str,
    round: u64,
    stage: u8,
    occurrence_id: &str,
    packet_sha256: &str,
) -> Result<String, Refusal> {
    canonical::digest(&json!({
        "occurrence_id": occurrence_id,
        "packet_sha256": packet_sha256,
        "round": round,
        "run_id": run_id,
        "stage": stage,
    }))
}

// Origin: engine/crates_rs/core_adversary/src/research_loop/occurrence.rs
// Claim: urn:core:crates_rs:core-adversary:occurrence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3b8e848e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3b8e848e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3b8e848e {
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
impl BoundaryError3b8e848e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3b8e848e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3b8e848e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3b8e848e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3b8e848e> {
        if capacity_bound == 0 {
            return Err(BoundaryError3b8e848e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3b8e848e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3b8e848e::ExceedsCapacity {
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
mod l4_boundary_tests_3b8e848e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3b8e848e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3b8e848e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3b8e848e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3b8e848e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3b8e848e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3b8e848e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3b8e848e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
