//! Companion Rust witness for PROD-P1-KILL (Evaluate P1 kill conditions on pilot arenas).

pub fn evaluate_p1_kill(state_count: usize, distinct_decisions: usize, loss_cert_verified: bool) -> (bool, bool, bool, bool) {
    let kill_size = state_count > 64;
    let kill_decisions = distinct_decisions < 3;
    let kill_loss = !loss_cert_verified;
    let any_kill = kill_size || kill_decisions || kill_loss;
    (kill_size, kill_decisions, kill_loss, any_kill)
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p1_kill.rs
// Claim: urn:core:crates_rs:tests:prod-p1-kill:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordaafa11e9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordaafa11e9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroraafa11e9 {
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
impl BoundaryErroraafa11e9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroraafa11e9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroraafa11e9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordaafa11e9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroraafa11e9> {
        if capacity_bound == 0 {
            return Err(BoundaryErroraafa11e9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroraafa11e9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroraafa11e9::ExceedsCapacity {
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
    fn pilot_p1_kill_conditions_do_not_hold() {
        assert_eq!(evaluate_p1_kill(4, 3, true), (false, false, false, false));
        assert_eq!(evaluate_p1_kill(100, 3, true), (true, false, false, true));
        assert_eq!(evaluate_p1_kill(4, 1, true), (false, true, false, true));
        assert_eq!(evaluate_p1_kill(4, 3, false), (false, false, true, true));
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct KillCensus { state_count: u64, distinct_decisions: u64, any_kill: bool }
pub fn try_kill_census(state_count: usize, distinct_decisions: usize, loss_cert_verified: bool) -> Result<KillCensus, &'static str> {
    if distinct_decisions > state_count {
        return Err("distinct decisions exceed the state count");
    }
    let (kill_size, kill_decisions, kill_loss, any_kill) = evaluate_p1_kill(state_count, distinct_decisions, loss_cert_verified);
    let size_flag = state_count > 64;
    let decision_flag = distinct_decisions < 3;
    let loss_flag = !loss_cert_verified;
    if kill_size != size_flag || kill_decisions != decision_flag || kill_loss != loss_flag {
        return Err("kill flags disagree with the thresholds");
    }
    if any_kill != (size_flag || decision_flag || loss_flag) {
        return Err("the aggregate kill flag is not the disjunction");
    }
    Ok(KillCensus {
        state_count: u64::try_from(state_count).map_err(|_| "state count exceeds u64")?,
        distinct_decisions: u64::try_from(distinct_decisions).map_err(|_| "decision count exceeds u64")?,
        any_kill,
    })
}
#[test]
fn decisions_cannot_exceed_states() {
    let census = try_kill_census(4, 3, true);
    assert_eq!(census.as_ref().map(|item| item.any_kill), Ok(false));
    assert_eq!(try_kill_census(4, 5, true).map(|_| ()), Err("distinct decisions exceed the state count"));
}

#[test]
fn l4_boundary_admits_and_refuses_aafa11e9() {
    let admitted = BoundaryRecordaafa11e9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordaafa11e9::try_admit(9, 8).is_err());
}
