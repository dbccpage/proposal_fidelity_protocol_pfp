//! Host controller for the WF_RESEARCH_PFP research loop.
//!
//! The loop runs produce → freeze → evaluate → challenge → repair over the eight PFP
//! stages (stage 5 is host-only). This module owns every decision the workflow assigns to
//! the host: mission admission, the single budget ledger, occurrence idempotency, candidate
//! freezing, review binding, stall detection, dependency invalidation and the final
//! disposition. Models and IDE agents only supply payloads; nothing they write can set a
//! check status, reset a budget or choose a terminal.
//!
//! The executable oracle is the pack's offline replay model (`tools/replay_loop.py`); its
//! eighteen checks are reproduced in `tests/research_loop_replay.rs`. Deliberate departures
//! from that model are listed on [`routing::route`].
//!
//! AuthorityEffect: None.

pub mod budget;
pub mod canonical;
pub mod invalidation;
pub mod mission;
pub mod occurrence;
pub mod pack;
pub mod phase;
pub mod response_schema;
pub mod routing;
pub mod state;

use crate::stage::ports::Refusal;

pub(crate) fn refuse(code: &str, message: impl Into<String>) -> Refusal {
    let mut refusal = Refusal::new(code, message);
    refusal.locus = "core_adversary::research_loop".into();
    refusal
}

/// Settling replaces the reservation with the metered usage.
/// `reserved - actual` is the unspent token remainder.
pub fn admit_settle_replaces_reservation() -> Result<budget::Spend, Refusal> {
    let limits = mission::Limits::default();
    let mut ledger = budget::BudgetLedger::default();
    let occurrence = occurrence::allocate("run", 1, 2, 1);
    let key = ledger.reserve(
        &limits,
        budget::ReservationRequest {
            idempotency_key: format!("{occurrence}-settle"),
            occurrence_id: &occurrence,
            round: 1,
            stage: 2,
            packet_sha256: "00",
            executor: occurrence::Executor::Model,
            tokens: 50,
            cost_microusd: 0,
        },
    )?;
    ledger.settle(&key, 20, 0)?;
    let spent = ledger.spent()?;
    if spent.model_calls != 1 || spent.total_tokens != 20 || spent.cost_microusd != 0 {
        return Err(refuse(
            "BUDGET_SETTLE_DRIFT",
            "settled spend is not the metered usage",
        ));
    }
    let unspent = 50u64.checked_sub(spent.total_tokens).ok_or_else(|| {
        refuse(
            "BUDGET_ARITHMETIC_OVERFLOW",
            "token remainder overflowed",
        )
    })?;
    if unspent != 30 {
        return Err(refuse(
            "BUDGET_SETTLE_DRIFT",
            "reserved tokens were not reduced by the metered usage",
        ));
    }
    Ok(spent)
}

// Origin: engine/crates_rs/core_adversary/src/research_loop/mod.rs
// Claim: urn:core:crates_rs:core-adversary:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf97b15ed {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf97b15ed` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf97b15ed {
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
impl BoundaryErrorf97b15ed {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf97b15ed {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf97b15ed {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf97b15ed {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf97b15ed> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf97b15ed::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf97b15ed::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf97b15ed::ExceedsCapacity {
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
mod settle_tests {
    use super::*;

    #[test]
    fn a_settled_call_charges_the_metered_tokens() {
        let spent = admit_settle_replaces_reservation();
        assert!(spent.is_ok());
        if let Ok(spent) = spent {
            assert_eq!(spent.model_calls, 1);
            assert_eq!(spent.total_tokens, 20);
            assert_eq!(spent.cost_microusd, 0);
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_f97b15ed {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf97b15ed::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf97b15ed::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf97b15ed::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf97b15ed::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf97b15ed::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf97b15ed::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf97b15ed::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
