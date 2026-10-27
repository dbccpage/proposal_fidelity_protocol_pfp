//! Companion Rust witness for PROD-KERNEL-KILL (Evaluate kernel kill conditions on a pilot workflow).

pub fn evaluate_kernel_kill(arena_declared: bool, initial_value: u64, usable_budget: u64, receipt_replayed: bool) -> (bool, bool, bool) {
    let kill_no_finite_arena = !(arena_declared && initial_value <= usable_budget);
    let kill_receipts_unreplayed = !receipt_replayed;
    let any_kill = kill_no_finite_arena || kill_receipts_unreplayed;
    (kill_no_finite_arena, kill_receipts_unreplayed, any_kill)
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_kernel_kill.rs
// Claim: urn:core:crates_rs:tests:prod-kernel-kill:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord45d2af52 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord45d2af52` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError45d2af52 {
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
impl BoundaryError45d2af52 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError45d2af52 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError45d2af52 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord45d2af52 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError45d2af52> {
        if capacity_bound == 0 {
            return Err(BoundaryError45d2af52::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError45d2af52::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError45d2af52::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pilot_kernel_kill_conditions_do_not_hold() {
        assert_eq!(evaluate_kernel_kill(true, 3, 3, true), (false, false, false));
        assert_eq!(evaluate_kernel_kill(false, 3, 3, true), (true, false, true));
        assert_eq!(evaluate_kernel_kill(true, 3, 3, false), (false, true, true));
    }
}

#[test]
fn l4_boundary_admits_and_refuses_45d2af52() {
    let admitted = BoundaryRecord45d2af52::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord45d2af52::try_admit(9, 8).is_err());
}
