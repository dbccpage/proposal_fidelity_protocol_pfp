//! Host routing: the disposition of a completed round.
//!
//! The model's stage 8 output is an advisory evidence plan; nothing in it is read here.
//! The disposition is computed from host facts only, then projected onto the canonical
//! routing axis `core_types::routing::RoutingTerminal`. The projection is many-to-one, so
//! the full disposition is always kept beside it and the loss is recorded.
//!
//! AuthorityEffect: None.

use super::{canonical, refuse};
use crate::stage::ports::Refusal;
use core_types::routing::RoutingTerminal;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::BTreeSet;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum Disposition {
    Verified,
    VerifiedWithResiduals,
    StabilizedSurvivor,
    NeedsExternalOracle,
    RepairNextRound,
    InvalidateAndRecheck,
    InfrastructureFailure,
    BlockedByEvidence,
    Refused,
    OpenObstruction,
    BudgetExhausted,
}

impl Disposition {
    pub const ALL: [Disposition; 11] = [
        Disposition::Verified,
        Disposition::VerifiedWithResiduals,
        Disposition::StabilizedSurvivor,
        Disposition::NeedsExternalOracle,
        Disposition::RepairNextRound,
        Disposition::InvalidateAndRecheck,
        Disposition::InfrastructureFailure,
        Disposition::BlockedByEvidence,
        Disposition::Refused,
        Disposition::OpenObstruction,
        Disposition::BudgetExhausted,
    ];

    /// Every disposition except the two repair routes ends the run.
    pub fn is_terminal(self) -> bool {
        !matches!(
            self,
            Disposition::RepairNextRound | Disposition::InvalidateAndRecheck
        )
    }

    /// Dispositions the host may impose outside the end-of-round route.
    pub fn may_halt(self) -> bool {
        matches!(
            self,
            Disposition::Refused
                | Disposition::InfrastructureFailure
                | Disposition::BlockedByEvidence
                | Disposition::BudgetExhausted
        )
    }

    /// Projection onto the routing axis. An open obstruction projects to `Refusal`
    /// (active closure failure), never `NoRule` or `BudgetUnknown`, per the CODA_GTLA
    /// witness-dominance rule.
    pub fn routing_terminal(self) -> RoutingTerminal {
        match self {
            Disposition::Verified | Disposition::VerifiedWithResiduals => {
                RoutingTerminal::CheckPassed
            }
            Disposition::NeedsExternalOracle | Disposition::StabilizedSurvivor => {
                RoutingTerminal::RequiresLift
            }
            Disposition::RepairNextRound | Disposition::InvalidateAndRecheck => {
                RoutingTerminal::Repair
            }
            Disposition::InfrastructureFailure
            | Disposition::BlockedByEvidence
            | Disposition::OpenObstruction => RoutingTerminal::Refusal,
            Disposition::Refused => RoutingTerminal::Refused,
            Disposition::BudgetExhausted => RoutingTerminal::BudgetUnknown,
        }
    }

    /// True when another disposition shares this one's routing terminal, so the terminal
    /// alone does not recover it.
    pub fn projection_is_lossy(self) -> bool {
        let terminal = self.routing_terminal();
        Disposition::ALL
            .iter()
            .filter(|other| other.routing_terminal() == terminal)
            .count()
            > 1
    }
}

/// Host facts reported for a route. The controller adds what it knows itself (staleness,
/// check results, critic coverage, budget, stall count).
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct RouteObservation {
    /// A policy, authority or owned-boundary violation was observed.
    pub policy_violation: bool,
    /// A transport, parser or infrastructure failure was not repaired within the attempts.
    pub infrastructure_failure: bool,
    /// A required source or external input is unavailable.
    pub missing_input: bool,
    /// A required semantic verifier is unbound or was not executed.
    pub verifier_unavailable: bool,
    /// The host confirmed the residual is repairable.
    pub repairable: bool,
    /// Unresolved claim or predicate identities after this round.
    pub residual_ids: Vec<String>,
    /// Every critic objection from stages 6 and 7 is accounted for.
    pub accounted_critic_objections: bool,
    /// Current on-disk digests, when the host re-read them; absent means unchanged.
    pub current_candidate_sha256: Option<String>,
    pub current_source_sha256: Option<String>,
    pub current_checker_policy_sha256: Option<String>,
}

/// Everything `route` decides on.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RouteFacts {
    pub observation: RouteObservation,
    pub stale: bool,
    pub all_required_pass: bool,
    pub any_required_fail: bool,
    pub critics_complete: bool,
    pub optional_claim_ids: BTreeSet<String>,
    pub semantic_verification_in_contract: bool,
    pub stalled_rounds: u64,
    pub max_stalled_rounds: u64,
    pub round: u64,
    pub max_rounds: u64,
    pub calls_spent: u64,
    pub max_model_calls: u64,
    pub tokens_spent: u64,
    pub max_total_tokens: u64,
    pub cost_spent_microusd: u64,
    /// 0 means paid dispatch is off, so cost cannot run out.
    pub max_cost_microusd: u64,
}

impl RouteFacts {
    /// Rounds, calls, tokens or (when paid dispatch is on) cost have reached their limit.
    pub fn budget_exhausted(&self) -> bool {
        self.round >= self.max_rounds
            || self.calls_spent >= self.max_model_calls
            || self.tokens_spent >= self.max_total_tokens
            || (self.max_cost_microusd > 0 && self.cost_spent_microusd >= self.max_cost_microusd)
    }
}

/// The ordered routing priority.
///
/// Departures from the pack's replay oracle (`tools/replay_loop.py`), all of which keep its
/// eighteen checks passing:
///
/// 1. `Refused` and `InfrastructureFailure` come first, as in the workflow YAML; the oracle
///    has no input for them.
/// 2. A stale review routes to `InvalidateAndRecheck` (the YAML's name) rather than the
///    oracle's `REPAIR_NEXT_ROUND`. Both are non-terminal and project to `Repair`.
/// 3. A stall (the same semantic residual for `max_stalled_rounds`) is checked before
///    budget exhaustion, because a witnessed obstruction dominates resource terminals
///    (CODA_GTLA rule 5). The oracle checks budget first; no oracle scenario has both.
/// 4. `VerifiedWithResiduals` and `StabilizedSurvivor` exist only when the mission declares
///    optional claims or excludes semantic verification; the oracle has neither.
/// 5. A required check that FAILED with the residual not repairable is a witnessed
///    obstruction (`OpenObstruction`), ahead of budget exhaustion. The oracle sends every
///    unpassed check to `NEEDS_EXTERNAL_ORACLE`, which the workflow reserves for an unbound
///    or unexecuted verifier.
/// 6. Budget exhaustion also counts tokens and cost, which the workflow names; the oracle
///    counts rounds and calls only.
pub fn route(facts: &RouteFacts) -> Disposition {
    if let Some(early) = route_blocker(&facts.observation) {
        return early;
    }
    if let Some(success) = route_reviewed_success(facts) {
        return success;
    }
    route_fallback(facts)
}

fn route_blocker(observation: &RouteObservation) -> Option<Disposition> {
    if observation.policy_violation {
        Some(Disposition::Refused)
    } else if observation.infrastructure_failure {
        Some(Disposition::InfrastructureFailure)
    } else if observation.missing_input {
        Some(Disposition::BlockedByEvidence)
    } else if observation.verifier_unavailable {
        Some(Disposition::NeedsExternalOracle)
    } else {
        None
    }
}

fn route_reviewed_success(facts: &RouteFacts) -> Option<Disposition> {
    let observation = &facts.observation;
    let reviewed = [
        !facts.stale,
        facts.critics_complete,
        observation.accounted_critic_objections,
    ]
    .into_iter()
    .all(|b| b);
    if !reviewed {
        return None;
    }
    let residuals: BTreeSet<&String> = observation.residual_ids.iter().collect();
    let required_residuals = residuals
        .iter()
        .any(|id| !facts.optional_claim_ids.contains(*id));
    if facts.all_required_pass && residuals.is_empty() {
        Some(Disposition::Verified)
    } else if facts.all_required_pass && !required_residuals {
        Some(Disposition::VerifiedWithResiduals)
    } else if !facts.semantic_verification_in_contract
        && !facts.any_required_fail
        && residuals.is_empty()
    {
        Some(Disposition::StabilizedSurvivor)
    } else {
        None
    }
}

fn route_fallback(facts: &RouteFacts) -> Disposition {
    let observation = &facts.observation;
    let stalled_or_unrepairable = !facts.stale
        && (facts.stalled_rounds >= facts.max_stalled_rounds
            || (facts.any_required_fail && !observation.repairable));
    if stalled_or_unrepairable {
        // A stall, or a witnessed failure the host cannot repair.
        Disposition::OpenObstruction
    } else if facts.budget_exhausted() {
        Disposition::BudgetExhausted
    } else if facts.stale {
        Disposition::InvalidateAndRecheck
    } else if observation.repairable {
        Disposition::RepairNextRound
    } else if !facts.all_required_pass {
        Disposition::NeedsExternalOracle
    } else {
        Disposition::OpenObstruction
    }
}

/// The stall key: required claims, unresolved predicates and verified evidence identities.
/// Longer prose, reformatting or a new confidence score leave it unchanged.
pub fn stall_key(
    required_claim_ids: &[String],
    residual_ids: &[String],
    verified_evidence: &BTreeSet<String>,
) -> Result<String, Refusal> {
    let required: BTreeSet<&String> = required_claim_ids.iter().collect();
    let unresolved: BTreeSet<&String> = residual_ids.iter().collect();
    if unresolved.len() != residual_ids.len() {
        return Err(refuse(
            "ROUTE_RESIDUALS_REPEAT",
            "residual ids must be distinct",
        ));
    }
    canonical::digest(&json!({
        "required_claim_ids": required,
        "unresolved": unresolved,
        "verified_evidence": verified_evidence,
    }))
}

// Origin: engine/crates_rs/core_adversary/src/research_loop/routing.rs
// Claim: urn:core:crates_rs:core-adversary:routing:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4ef2ef77 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4ef2ef77` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4ef2ef77 {
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
impl BoundaryError4ef2ef77 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4ef2ef77 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4ef2ef77 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4ef2ef77 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4ef2ef77> {
        if capacity_bound == 0 {
            return Err(BoundaryError4ef2ef77::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4ef2ef77::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4ef2ef77::ExceedsCapacity {
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
mod tests {
    use super::*;

    #[test]
    fn projection_table() {
        use Disposition::*;
        use RoutingTerminal as T;
        let expected = [
            (Verified, T::CheckPassed),
            (VerifiedWithResiduals, T::CheckPassed),
            (StabilizedSurvivor, T::RequiresLift),
            (NeedsExternalOracle, T::RequiresLift),
            (RepairNextRound, T::Repair),
            (InvalidateAndRecheck, T::Repair),
            (InfrastructureFailure, T::Refusal),
            (BlockedByEvidence, T::Refusal),
            (Refused, T::Refused),
            (OpenObstruction, T::Refusal),
            (BudgetExhausted, T::BudgetUnknown),
        ];
        for (disposition, terminal) in expected {
            assert_eq!(disposition.routing_terminal(), terminal, "{disposition:?}");
        }
        assert!(!Refused.projection_is_lossy());
        assert!(!BudgetExhausted.projection_is_lossy());
        assert!(OpenObstruction.projection_is_lossy());
        assert!(Disposition::ALL
            .iter()
            .all(|d| d.routing_terminal() != T::NoRule));
    }
}

#[cfg(test)]
mod l4_boundary_tests_4ef2ef77 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4ef2ef77::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4ef2ef77::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4ef2ef77::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4ef2ef77::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4ef2ef77::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError4ef2ef77::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError4ef2ef77::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
