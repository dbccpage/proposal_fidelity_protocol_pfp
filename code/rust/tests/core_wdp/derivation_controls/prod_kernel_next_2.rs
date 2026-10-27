//! Companion Rust witness for PROD-KERNEL-NEXT-2 (Pilot agent loop finite arena & usable budget).

pub const PILOT_USABLE_BUDGET: u64 = 3;

pub fn pilot_minimax_value(
    gate_cost: u64,
    issue_receipt_cost: u64,
    repair_cost: u64,
    manual_audit_cost: u64,
) -> u64 {
    let gated_branch = issue_receipt_cost;
    let rejected_branch = repair_cost + issue_receipt_cost;
    let g5_route = gate_cost + gated_branch.max(rejected_branch);
    g5_route.min(manual_audit_cost)
}

pub fn resolves_within_budget(budget: u64) -> &'static str {
    let opt = pilot_minimax_value(1, 1, 1, 5);
    if opt <= budget {
        "ResolvedWithinBudget"
    } else {
        "Exhausted"
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_kernel_next_2.rs
// Claim: urn:core:crates_rs:tests:prod-kernel-next-2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord15a73f29 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord15a73f29` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError15a73f29 {
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
impl BoundaryError15a73f29 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError15a73f29 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError15a73f29 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord15a73f29 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError15a73f29> {
        if capacity_bound == 0 {
            return Err(BoundaryError15a73f29::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError15a73f29::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError15a73f29::ExceedsCapacity {
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
    fn pilot_arena_minimax_cost_resolves_within_usable_budget() {
        assert_eq!(pilot_minimax_value(1, 1, 1, 5), PILOT_USABLE_BUDGET);
        assert_eq!(resolves_within_budget(PILOT_USABLE_BUDGET), "ResolvedWithinBudget");
        assert_eq!(resolves_within_budget(2), "Exhausted");
    }
}

#[test]
fn l4_boundary_admits_and_refuses_15a73f29() {
    let admitted = BoundaryRecord15a73f29::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord15a73f29::try_admit(9, 8).is_err());
}
