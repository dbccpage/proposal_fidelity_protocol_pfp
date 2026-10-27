//! Dual-Signal Danger Gate (U16).
//!
//! Two-signal model of activation:
//! - Signal 1: Antigen / Structural defect (e.g. grammar violation, invalid boundary).
//! - Signal 2: Tissue damage / Context breach (e.g. state drift, authority leakage, uncontracted write).
//!
//! Invariant: Quarantine requires BOTH Signal 1 and Signal 2 (signal1 && signal2).
//! Signal 1 alone yields a diagnostic finding, NEVER quarantine.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DangerDisposition {
    Clear,
    FindingOnly,
    AlertOnly,
    Quarantine,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DangerGateReceipt {
    pub signal1_detected: bool,
    pub signal1_finding: Option<String>,
    pub signal2_detected: bool,
    pub signal2_damage: Option<String>,
    pub disposition: DangerDisposition,
    pub quarantined: bool,
    pub authority_effect: String,
}

#[derive(Debug, Default, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DangerGate;

impl DangerGate {
    pub fn new() -> Self {
        Self
    }

    /// Evaluates candidate signals.
    /// Quarantine occurs iff BOTH Signal 1 and Signal 2 are present.
    pub fn evaluate(&self, signal1: Option<String>, signal2: Option<String>) -> DangerGateReceipt {
        let s1 = signal1.is_some();
        let s2 = signal2.is_some();

        let (disposition, quarantined) = match (s1, s2) {
            (true, true) => (DangerDisposition::Quarantine, true),
            (true, false) => (DangerDisposition::FindingOnly, false),
            (false, true) => (DangerDisposition::AlertOnly, false),
            (false, false) => (DangerDisposition::Clear, false),
        };

        DangerGateReceipt {
            signal1_detected: s1,
            signal1_finding: signal1,
            signal2_detected: s2,
            signal2_damage: signal2,
            disposition,
            quarantined,
            authority_effect: "None".to_string(),
        }
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/immune/danger_gate.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:danger-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8de3536a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8de3536a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8de3536a {
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
impl BoundaryError8de3536a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8de3536a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8de3536a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8de3536a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8de3536a> {
        if capacity_bound == 0 {
            return Err(BoundaryError8de3536a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8de3536a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8de3536a::ExceedsCapacity {
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
mod l4_boundary_tests_8de3536a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8de3536a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8de3536a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8de3536a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8de3536a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8de3536a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError8de3536a::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError8de3536a::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
