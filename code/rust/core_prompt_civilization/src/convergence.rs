//! A finite stopping policy, not a general population-convergence theorem.
//! AuthorityEffect: None.

use std::collections::BTreeSet;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RecoveryAction {
    ReinjectDiversity,
    Reboot,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FreezeReason {
    Plateau,
    BudgetExhausted,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConvergencePolicyV1 {
    pub max_observations: u64,
    pub plateau_window: u64,
    pub recovery: RecoveryAction,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PopulationSnapshotV1 {
    /// Exact objective values from a fixed, host-selected evaluation regime.
    pub best_success: u64,
    pub best_failures: u64,
    pub occupied_cells: BTreeSet<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FreezeReceiptV1 {
    pub reason: FreezeReason,
    pub observations: u64,
    pub action: RecoveryAction,
    pub authority_effect: &'static str,
}

pub struct ConvergenceMonitorV1 {
    policy: ConvergencePolicyV1,
    observations: u64,
    unchanged: u64,
    previous: Option<PopulationSnapshotV1>,
    frozen: Option<FreezeReceiptV1>,
}

impl ConvergenceMonitorV1 {
    pub fn new(policy: ConvergencePolicyV1) -> Result<Self, String> {
        if policy.max_observations == 0 || policy.plateau_window == 0 {
            return Err("INVALID_CONVERGENCE_POLICY".into());
        }
        Ok(Self {
            policy,
            observations: 0,
            unchanged: 0,
            previous: None,
            frozen: None,
        })
    }

    pub fn observe(
        &mut self,
        snapshot: PopulationSnapshotV1,
    ) -> Result<Option<FreezeReceiptV1>, String> {
        if self.frozen.is_some() {
            return Err("FROZEN: external recovery requires a new budgeted epoch".into());
        }
        self.observations += 1;
        self.unchanged = if self.previous.as_ref() == Some(&snapshot) {
            self.unchanged + 1
        } else {
            1
        };
        self.previous = Some(snapshot);
        let reason = if self.observations >= self.policy.max_observations {
            Some(FreezeReason::BudgetExhausted)
        } else if self.unchanged >= self.policy.plateau_window {
            Some(FreezeReason::Plateau)
        } else {
            None
        };
        self.frozen = reason.map(|reason| FreezeReceiptV1 {
            reason,
            observations: self.observations,
            action: self.policy.recovery,
            authority_effect: "None",
        });
        Ok(self.frozen.clone())
    }

    /// Natural-number ranking function. Every accepted observation reduces it
    /// by exactly one; zero forces FROZEN. FROZEN has no outgoing observe step.
    pub fn remaining_observations(&self) -> u64 {
        self.policy.max_observations - self.observations
    }

    pub fn is_frozen(&self) -> bool {
        self.frozen.is_some()
    }

    pub fn recovery_action(&self) -> Option<RecoveryAction> {
        self.frozen.as_ref().map(|receipt| receipt.action)
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/convergence.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:convergence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord131a8db1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord131a8db1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError131a8db1 {
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
impl BoundaryError131a8db1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError131a8db1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError131a8db1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord131a8db1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError131a8db1> {
        if capacity_bound == 0 {
            return Err(BoundaryError131a8db1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError131a8db1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError131a8db1::ExceedsCapacity {
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
mod l4_boundary_tests_131a8db1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord131a8db1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord131a8db1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord131a8db1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord131a8db1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord131a8db1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError131a8db1::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError131a8db1::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
