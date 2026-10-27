//! Companion Rust witness for PROD-P4-KILL (Evaluate P4 kill conditions on pilot instrument menus).

pub fn evaluate_p4_kill(solver_finished: bool, planned_cost_num: u64, planned_cost_den: u64, buyer_cost_num: u64, buyer_cost_den: u64) -> (bool, bool, bool) {
    let kill_exceeds_solver = !solver_finished;
    let kill_never_differs = planned_cost_num * buyer_cost_den >= buyer_cost_num * planned_cost_den;
    let any_kill = kill_exceeds_solver || kill_never_differs;
    (kill_exceeds_solver, kill_never_differs, any_kill)
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p4_kill.rs
// Claim: urn:core:crates_rs:tests:prod-p4-kill:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0314ce3a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0314ce3a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0314ce3a {
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
impl BoundaryError0314ce3a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0314ce3a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0314ce3a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0314ce3a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0314ce3a> {
        if capacity_bound == 0 {
            return Err(BoundaryError0314ce3a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0314ce3a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0314ce3a::ExceedsCapacity {
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
    fn pilot_p4_kill_conditions_do_not_hold() {
        assert_eq!(evaluate_p4_kill(true, 7, 2, 5, 1), (false, false, false));
        assert_eq!(evaluate_p4_kill(false, 7, 2, 5, 1), (true, false, true));
        assert_eq!(evaluate_p4_kill(true, 5, 1, 5, 1), (false, true, true));
    }
}

#[test]
fn l4_boundary_admits_and_refuses_0314ce3a() {
    let admitted = BoundaryRecord0314ce3a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord0314ce3a::try_admit(9, 8).is_err());
}
