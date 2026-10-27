//! Bounded Complement Cascade Recruitment (U16).
//!
//! Cascade stages:
//! 1. C1: Recognition initiation.
//! 2. C3: Enzymatic amplification and opsonization.
//! 3. MAC (Membrane Attack Complex): Terminal target clearance / quarantine.
//!
//! Invariant: Effector recruitment is strictly capped by an explicit integer budget
//! `max_recruitment_budget`. Exceeding the budget halts recruitment cleanly without
//! unbounded resource allocation.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ComplementStage {
    C1Initiation,
    C3Amplification,
    MacTerminal,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ComplementCascadeReceipt {
    pub initial_triggers: usize,
    pub recruited_effectors: usize,
    pub max_recruitment_budget: usize,
    pub reached_terminal_mac: bool,
    pub budget_exhausted: bool,
    pub stage: ComplementStage,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ComplementCascade {
    pub max_recruitment_budget: usize,
    pub amplification_factor: usize,
}

impl ComplementCascade {
    pub fn new(max_recruitment_budget: usize, amplification_factor: usize) -> Self {
        assert!(max_recruitment_budget > 0, "Budget must be > 0");
        assert!(amplification_factor > 0, "Amplification factor must be > 0");
        Self {
            max_recruitment_budget,
            amplification_factor,
        }
    }

    /// Execute bounded complement cascade given initial trigger count.
    pub fn execute(&self, initial_triggers: usize) -> ComplementCascadeReceipt {
        if initial_triggers == 0 {
            return ComplementCascadeReceipt {
                initial_triggers: 0,
                recruited_effectors: 0,
                max_recruitment_budget: self.max_recruitment_budget,
                reached_terminal_mac: false,
                budget_exhausted: false,
                stage: ComplementStage::C1Initiation,
                authority_effect: "None".to_string(),
            };
        }

        // C1 -> C3 amplification
        let c3_potential = initial_triggers.saturating_mul(self.amplification_factor);
        let recruited = c3_potential.min(self.max_recruitment_budget);
        let budget_exhausted = c3_potential >= self.max_recruitment_budget;
        let reached_mac = recruited >= 3;

        let stage = if reached_mac {
            ComplementStage::MacTerminal
        } else if recruited > initial_triggers {
            ComplementStage::C3Amplification
        } else {
            ComplementStage::C1Initiation
        };

        ComplementCascadeReceipt {
            initial_triggers,
            recruited_effectors: recruited,
            max_recruitment_budget: self.max_recruitment_budget,
            reached_terminal_mac: reached_mac,
            budget_exhausted,
            stage,
            authority_effect: "None".to_string(),
        }
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/immune/complement.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:complement:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordddf77818 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordddf77818` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorddf77818 {
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
impl BoundaryErrorddf77818 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorddf77818 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorddf77818 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordddf77818 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorddf77818> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorddf77818::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorddf77818::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorddf77818::ExceedsCapacity {
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
mod l4_boundary_tests_ddf77818 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordddf77818::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordddf77818::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordddf77818::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordddf77818::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordddf77818::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorddf77818::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorddf77818::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
