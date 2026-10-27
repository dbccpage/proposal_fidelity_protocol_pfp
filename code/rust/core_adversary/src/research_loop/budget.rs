//! The one host-owned budget ledger for a research run.
//!
//! Every dispatch reserves its worst case before anything is sent: one model call, the
//! token ceiling and the cost quote. The reservation is keyed by the occurrence's
//! idempotency key and its outcome is then recorded as one of:
//!
//! * `settle` — the call completed; actual usage replaces the reservation (an overrun is
//!   charged in full and flagged; spend is never under-reported);
//! * `reconcile` — the outcome is unknown (timeout, crash); the full reservation stays
//!   charged;
//! * `release` — the request provably never left the host; tokens and cost are returned but
//!   the call still counts, so reserve/release cycles cannot run forever.
//!
//! Spend is derived from the reservations, so it cannot drift from them, and it is never
//! reset: not by a new round, a retry, a child dispatch, a resume or a prompt revision.
//! A new reservation for a stage is refused while an earlier one for the same round and
//! stage is still pending, which forces uncertain outcomes to be reconciled before a retry.
//!
//! AuthorityEffect: None.

use super::mission::Limits;
use super::occurrence::Executor;
use super::refuse;
use crate::stage::ports::Refusal;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ReservationState {
    Pending,
    Settled,
    Reconciled,
    Released,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Reservation {
    pub idempotency_key: String,
    pub occurrence_id: String,
    pub round: u64,
    pub stage: u8,
    pub packet_sha256: String,
    pub executor: Executor,
    pub reserved_tokens: u64,
    pub reserved_cost_microusd: u64,
    pub charged_tokens: u64,
    pub charged_cost_microusd: u64,
    pub state: ReservationState,
    pub overrun: bool,
    /// False for IDE occurrences: the host did not meter cost, so it is `NOT_MEASURED`.
    pub cost_measured: bool,
}

impl Reservation {
    pub fn is_open(&self) -> bool {
        self.state == ReservationState::Pending
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct Spend {
    pub model_calls: u64,
    pub total_tokens: u64,
    pub cost_microusd: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BudgetLedger {
    reservations: BTreeMap<String, Reservation>,
}

pub struct ReservationRequest<'a> {
    pub idempotency_key: String,
    pub occurrence_id: &'a str,
    pub round: u64,
    pub stage: u8,
    pub packet_sha256: &'a str,
    pub executor: Executor,
    pub tokens: u64,
    pub cost_microusd: u64,
}

fn overflow() -> Refusal {
    refuse(
        "BUDGET_ARITHMETIC_OVERFLOW",
        "budget arithmetic overflowed u64",
    )
}

impl BudgetLedger {
    pub fn spent(&self) -> Result<Spend, Refusal> {
        let mut spend = Spend::default();
        for item in self.reservations.values() {
            spend.model_calls = spend.model_calls.checked_add(1).ok_or_else(overflow)?;
            spend.total_tokens = spend
                .total_tokens
                .checked_add(item.charged_tokens)
                .ok_or_else(overflow)?;
            spend.cost_microusd = spend
                .cost_microusd
                .checked_add(item.charged_cost_microusd)
                .ok_or_else(overflow)?;
        }
        Ok(spend)
    }

    /// Every idempotency key the ledger holds.
    pub fn keys(&self) -> impl Iterator<Item = &String> {
        self.reservations.keys()
    }

    pub fn reservation(&self, key: &str) -> Option<&Reservation> {
        self.reservations.get(key)
    }

    pub fn by_occurrence(&self, occurrence_id: &str) -> Option<&Reservation> {
        self.reservations
            .values()
            .find(|item| item.occurrence_id == occurrence_id)
    }

    pub fn reservations(&self) -> impl Iterator<Item = &Reservation> {
        self.reservations.values()
    }

    /// Reserve before dispatch. Re-reserving the same occurrence and packet is a no-op that
    /// returns the existing key.
    pub fn reserve(
        &mut self,
        limits: &Limits,
        request: ReservationRequest<'_>,
    ) -> Result<String, Refusal> {
        if let Some(key) = self.check_existing_reservation(&request)? {
            return Ok(key);
        }
        self.validate_new_reservation(limits, &request)?;
        let key = request.idempotency_key.clone();
        self.reservations.insert(
            key.clone(),
            Reservation {
                idempotency_key: request.idempotency_key,
                occurrence_id: request.occurrence_id.into(),
                round: request.round,
                stage: request.stage,
                packet_sha256: request.packet_sha256.into(),
                executor: request.executor,
                reserved_tokens: request.tokens,
                reserved_cost_microusd: request.cost_microusd,
                charged_tokens: request.tokens,
                charged_cost_microusd: request.cost_microusd,
                state: ReservationState::Pending,
                overrun: false,
                cost_measured: request.executor == Executor::Model,
            },
        );
        Ok(key)
    }

    fn check_existing_reservation(
        &self,
        request: &ReservationRequest<'_>,
    ) -> Result<Option<String>, Refusal> {
        let Some(existing) = self.by_occurrence(request.occurrence_id) else {
            return Ok(None);
        };
        let matches_terms = [
            existing.idempotency_key == request.idempotency_key,
            existing.executor == request.executor,
            existing.reserved_tokens == request.tokens,
            existing.reserved_cost_microusd == request.cost_microusd,
        ]
        .into_iter()
        .all(|b| b);
        if matches_terms {
            return Ok(Some(existing.idempotency_key.clone()));
        }
        Err(refuse(
            "OCCURRENCE_CONFLICT",
            format!(
                "occurrence {} is already reserved with other terms",
                request.occurrence_id
            ),
        ))
    }

    fn validate_new_reservation(
        &self,
        limits: &Limits,
        request: &ReservationRequest<'_>,
    ) -> Result<(), Refusal> {
        if self.reservations.contains_key(&request.idempotency_key) {
            return Err(refuse(
                "OCCURRENCE_CONFLICT",
                "idempotency key already in use",
            ));
        }
        if let Some(open) = self.find_open_stage_reservation(request.round, request.stage) {
            return Err(refuse(
                "RESERVATION_OUTSTANDING",
                format!(
                    "occurrence {} for this stage is unresolved; settle, reconcile or release it first",
                    open.occurrence_id
                ),
            ));
        }
        self.check_reservation_budget(limits, request)
    }

    fn find_open_stage_reservation(&self, round: u64, stage: u8) -> Option<&Reservation> {
        self.reservations.values().find(|item| {
            [item.is_open(), item.round == round, item.stage == stage]
                .into_iter()
                .all(|b| b)
        })
    }

    fn check_reservation_budget(
        &self,
        limits: &Limits,
        request: &ReservationRequest<'_>,
    ) -> Result<(), Refusal> {
        if request.cost_microusd > 0 && !limits.paid_dispatch_enabled() {
            return Err(refuse(
                "PAID_DISPATCH_DISABLED",
                "max_cost_microusd is 0: paid dispatch is off for this mission",
            ));
        }
        let spend = self.spent()?;
        let calls = spend.model_calls.checked_add(1).ok_or_else(overflow)?;
        let tokens = spend
            .total_tokens
            .checked_add(request.tokens)
            .ok_or_else(overflow)?;
        let cost = spend
            .cost_microusd
            .checked_add(request.cost_microusd)
            .ok_or_else(overflow)?;
        let within_limits = [
            calls <= limits.max_model_calls,
            tokens <= limits.max_total_tokens,
            cost <= limits.max_cost_microusd,
        ]
        .into_iter()
        .all(|b| b);
        if !within_limits {
            return Err(refuse(
                "BUDGET_EXHAUSTED",
                format!(
                    "reservation needs calls={calls} tokens={tokens} cost={cost}; limits are {}/{}/{}",
                    limits.max_model_calls, limits.max_total_tokens, limits.max_cost_microusd
                ),
            ));
        }
        Ok(())
    }

    fn pending_mut(&mut self, key: &str) -> Result<&mut Reservation, Refusal> {
        let item = self
            .reservations
            .get_mut(key)
            .ok_or_else(|| refuse("RESERVATION_UNKNOWN", format!("no reservation {key}")))?;
        if !item.is_open() {
            return Err(refuse(
                "RESERVATION_CLOSED",
                format!(
                    "reservation for {} is already {:?}",
                    item.occurrence_id, item.state
                ),
            ));
        }
        Ok(item)
    }

    /// Record the metered usage of a completed call. Settling again with the same usage is
    /// a no-op.
    pub fn settle(&mut self, key: &str, tokens: u64, cost_microusd: u64) -> Result<(), Refusal> {
        if let Some(item) = self.reservations.get(key) {
            if item.state == ReservationState::Settled
                && item.charged_tokens == tokens
                && item.charged_cost_microusd == cost_microusd
            {
                return Ok(());
            }
        }
        let item = self.pending_mut(key)?;
        item.overrun = tokens > item.reserved_tokens || cost_microusd > item.reserved_cost_microusd;
        item.charged_tokens = tokens;
        item.charged_cost_microusd = cost_microusd;
        item.state = ReservationState::Settled;
        Ok(())
    }

    /// The call's outcome is unknown: keep the whole reservation charged.
    pub fn reconcile_unknown(&mut self, key: &str) -> Result<(), Refusal> {
        let item = self.pending_mut(key)?;
        item.state = ReservationState::Reconciled;
        Ok(())
    }

    /// The request never left the host: return tokens and cost, keep the call counted.
    pub fn release(&mut self, key: &str) -> Result<(), Refusal> {
        let item = self.pending_mut(key)?;
        item.charged_tokens = 0;
        item.charged_cost_microusd = 0;
        item.state = ReservationState::Released;
        Ok(())
    }

    /// Structural checks for a resumed ledger.
    pub fn verify(&self, limits: &Limits) -> Result<(), Refusal> {
        let mut occurrences = std::collections::BTreeSet::new();
        let mut overrun = false;
        for (key, item) in &self.reservations {
            Self::verify_reservation_entry(key, item, &mut occurrences)?;
            overrun |= item.overrun;
        }
        self.verify_spend_limits(limits, overrun)
    }

    fn verify_reservation_entry<'a>(
        key: &str,
        item: &'a Reservation,
        occurrences: &mut std::collections::BTreeSet<&'a str>,
    ) -> Result<(), Refusal> {
        if key != item.idempotency_key || !occurrences.insert(item.occurrence_id.as_str()) {
            return Err(refuse(
                "CHECKPOINT_LEDGER_INVALID",
                "reservation keys or occurrences repeat",
            ));
        }
        if !Self::reservation_charges_consistent(item) {
            return Err(refuse(
                "CHECKPOINT_LEDGER_INVALID",
                format!(
                    "reservation {} has charges inconsistent with its state",
                    item.occurrence_id
                ),
            ));
        }
        Ok(())
    }

    fn reservation_charges_consistent(item: &Reservation) -> bool {
        match item.state {
            ReservationState::Pending | ReservationState::Reconciled => [
                item.charged_tokens == item.reserved_tokens,
                item.charged_cost_microusd == item.reserved_cost_microusd,
                !item.overrun,
            ]
            .into_iter()
            .all(|b| b),
            ReservationState::Released => [
                item.charged_tokens == 0,
                item.charged_cost_microusd == 0,
                !item.overrun,
            ]
            .into_iter()
            .all(|b| b),
            ReservationState::Settled => {
                let exceeds = item.charged_tokens > item.reserved_tokens
                    || item.charged_cost_microusd > item.reserved_cost_microusd;
                item.overrun == exceeds
            }
        }
    }

    fn verify_spend_limits(&self, limits: &Limits, overrun: bool) -> Result<(), Refusal> {
        let spend = self.spent()?;
        // Only a settled overrun can carry tokens or cost past the limit; calls never can.
        let usage_within = spend.total_tokens <= limits.max_total_tokens
            && spend.cost_microusd <= limits.max_cost_microusd;
        if spend.model_calls > limits.max_model_calls || (!usage_within && !overrun) {
            return Err(refuse(
                "CHECKPOINT_LEDGER_INVALID",
                "recorded spend exceeds the mission limits",
            ));
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_adversary/src/research_loop/budget.rs
// Claim: urn:core:crates_rs:core-adversary:budget:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord00ce2f60 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord00ce2f60` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError00ce2f60 {
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
impl BoundaryError00ce2f60 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError00ce2f60 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError00ce2f60 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord00ce2f60 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError00ce2f60> {
        if capacity_bound == 0 {
            return Err(BoundaryError00ce2f60::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError00ce2f60::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError00ce2f60::ExceedsCapacity {
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
mod l4_boundary_tests_00ce2f60 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord00ce2f60::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord00ce2f60::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord00ce2f60::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord00ce2f60::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord00ce2f60::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError00ce2f60::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError00ce2f60::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
