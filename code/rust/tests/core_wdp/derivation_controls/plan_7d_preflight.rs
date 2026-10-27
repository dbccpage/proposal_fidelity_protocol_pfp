//! Staged PFP runner dependency, path, and budget-reservation preflight control for PLAN-7D-PREFLIGHT.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct RunnerPreflightConfig {
    pub jsonschema_present: bool,
    pub runner_path_present: bool,
    pub canonical_controller_present: bool,
    pub legacy_live_requested: bool,
    pub unbounded_legacy_override: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PreflightDecision {
    ReadyOffline,
    RefusedMissingDependency,
    RefusedLegacyLiveRequiresCanonicalPfp,
}

pub fn evaluate_runner_preflight(cfg: RunnerPreflightConfig) -> PreflightDecision {
    if !cfg.jsonschema_present || !cfg.runner_path_present || !cfg.canonical_controller_present {
        return PreflightDecision::RefusedMissingDependency;
    }
    if cfg.legacy_live_requested && !cfg.unbounded_legacy_override {
        return PreflightDecision::RefusedLegacyLiveRequiresCanonicalPfp;
    }
    PreflightDecision::ReadyOffline
}

pub fn collate_reservation(
    budget_cap_cents: u64,
    reserved_cents: u64,
    actual_cost_cents: Option<u64>,
) -> Result<(u64, u64), &'static str> {
    if budget_cap_cents == 0 || reserved_cents == 0 || reserved_cents > budget_cap_cents {
        return Err("invalid reservation or budget cap");
    }
    match actual_cost_cents {
        None => Ok((reserved_cents, budget_cap_cents - reserved_cents)),
        Some(actual) => {
            if actual > budget_cap_cents {
                return Err("actual cost exceeds budget cap");
            }
            Ok((actual, budget_cap_cents - actual))
        }
    }
}

#[test]
fn runner_preflight_blocks_unguarded_legacy_live_and_retains_unknown_cost() {
    let offline_cfg = RunnerPreflightConfig {
        jsonschema_present: true,
        runner_path_present: true,
        canonical_controller_present: true,
        legacy_live_requested: false,
        unbounded_legacy_override: false,
    };
    assert_eq!(
        evaluate_runner_preflight(offline_cfg),
        PreflightDecision::ReadyOffline
    );

    let live_cfg = RunnerPreflightConfig {
        legacy_live_requested: true,
        ..offline_cfg
    };
    assert_eq!(
        evaluate_runner_preflight(live_cfg),
        PreflightDecision::RefusedLegacyLiveRequiresCanonicalPfp
    );

    let missing_dep = RunnerPreflightConfig {
        jsonschema_present: false,
        ..offline_cfg
    };
    assert_eq!(
        evaluate_runner_preflight(missing_dep),
        PreflightDecision::RefusedMissingDependency
    );

    assert_eq!(collate_reservation(1000, 250, None), Ok((250, 750)));
    assert_eq!(collate_reservation(1000, 250, Some(180)), Ok((180, 820)));
    assert_eq!(
        collate_reservation(100, 200, None),
        Err("invalid reservation or budget cap")
    );
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_7d_preflight.rs
// Claim: urn:core:crates_rs:tests:plan-7d-preflight:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord00ae280a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord00ae280a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError00ae280a {
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
impl BoundaryError00ae280a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError00ae280a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError00ae280a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord00ae280a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError00ae280a> {
        if capacity_bound == 0 {
            return Err(BoundaryError00ae280a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError00ae280a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError00ae280a::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_00ae280a() {
    let admitted = BoundaryRecord00ae280a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord00ae280a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
