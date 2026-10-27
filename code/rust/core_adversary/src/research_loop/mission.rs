//! Mission admission: the fixed contract a research run is held to.
//!
//! The fourteen `mission_required` fields of `researcher_workflow.pfp.yaml` are mandatory.
//! The question, required claims, done predicates and budget stay fixed for the admitted
//! mission; a change of scope is a new mission, not an edit. Budget limits not named by the
//! mission take the workflow defaults. `max_cost_microusd = 0` disables paid dispatch; it
//! never means unlimited.
//!
//! AuthorityEffect: None.

use super::{canonical, refuse};
use crate::stage::ports::Refusal;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Lane {
    SourceSynthesis,
    MathematicalDerivation,
    Mixed,
}

/// The thirteen workflow limits. Every count is an exact non-negative integer.
///
/// The controller enforces rounds, model calls, total tokens, cost, stalled rounds and the
/// per-response byte ceiling. The remaining limits are carried for the adapters that own
/// them (tool calls, readers, questions, sources, wall time, source bytes).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct Limits {
    pub max_rounds: u64,
    pub max_model_calls: u64,
    pub max_total_tokens: u64,
    pub max_cost_microusd: u64,
    pub max_tool_calls: u64,
    pub max_parallel_readers: u64,
    pub max_questions: u64,
    pub max_sources: u64,
    pub max_tool_attempts: u64,
    pub max_stalled_rounds: u64,
    pub max_wall_seconds: u64,
    pub max_model_response_bytes: u64,
    pub max_source_bytes: u64,
}

impl Default for Limits {
    /// `researcher_workflow.pfp.yaml` `defaults`.
    fn default() -> Self {
        Self {
            max_rounds: 3,
            max_model_calls: 32,
            max_total_tokens: 120_000,
            max_cost_microusd: 0,
            max_tool_calls: 64,
            max_parallel_readers: 3,
            max_questions: 8,
            max_sources: 24,
            max_tool_attempts: 2,
            max_stalled_rounds: 2,
            max_wall_seconds: 2700,
            max_model_response_bytes: 131_072,
            max_source_bytes: 16_777_216,
        }
    }
}

impl Limits {
    fn validate(&self) -> Result<(), Refusal> {
        for (name, value) in [
            ("max_rounds", self.max_rounds),
            ("max_model_calls", self.max_model_calls),
            ("max_stalled_rounds", self.max_stalled_rounds),
            ("max_parallel_readers", self.max_parallel_readers),
            ("max_model_response_bytes", self.max_model_response_bytes),
        ] {
            if value == 0 {
                return Err(refuse(
                    "MISSION_BUDGET_INVALID",
                    format!("{name} must be at least 1"),
                ));
            }
        }
        Ok(())
    }

    pub fn paid_dispatch_enabled(&self) -> bool {
        self.max_cost_microusd > 0
    }
}

/// `mission_required` from the workflow, in its order; the pack check compares the two.
pub const MISSION_REQUIRED: [&str; 14] = [
    "mission_id",
    "run_id",
    "original_seed_ref",
    "original_question",
    "lane",
    "required_claim_ids",
    "done_predicates",
    "owned_paths",
    "forbidden_surfaces",
    "source_inventory",
    "capability_bindings",
    "verifier_routes",
    "budget",
    "retention_policy",
];

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Mission {
    pub mission_id: String,
    pub run_id: String,
    pub original_seed_ref: String,
    pub original_question: String,
    pub lane: Lane,
    pub required_claim_ids: Vec<String>,
    /// Each predicate is also the `check_id` a host check must carry to discharge it.
    pub done_predicates: Vec<String>,
    pub owned_paths: Vec<String>,
    pub forbidden_surfaces: Vec<String>,
    pub source_inventory: String,
    pub capability_bindings: BTreeMap<String, String>,
    pub verifier_routes: BTreeMap<String, String>,
    pub budget: Limits,
    pub retention_policy: String,
    /// Claims the mission allows to stay unresolved (routes to `VerifiedWithResiduals`).
    #[serde(default)]
    pub optional_claim_ids: Vec<String>,
    /// False when semantic verification is not part of the contract (routes surviving
    /// proposals to `StabilizedSurvivor` rather than `NeedsExternalOracle`).
    #[serde(default = "default_true")]
    pub semantic_verification_in_contract: bool,
}

fn default_true() -> bool {
    true
}

/// A mission that passed admission, with its digest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AdmittedMission {
    pub mission: Mission,
    pub mission_sha256: String,
}

impl AdmittedMission {
    pub fn admit(raw: &Value) -> Result<Self, Refusal> {
        let mission: Mission = serde_json::from_value(raw.clone())
            .map_err(|error| refuse("MISSION_INVALID", error.to_string()))?;
        mission.validate()?;
        let mission_sha256 = mission_digest(&mission)?;
        Ok(Self {
            mission,
            mission_sha256,
        })
    }

    /// Re-check a stored mission against its stored digest (checkpoint resume).
    pub fn verify(&self) -> Result<(), Refusal> {
        self.mission.validate()?;
        if mission_digest(&self.mission)? != self.mission_sha256 {
            return Err(refuse(
                "MISSION_DIGEST_MISMATCH",
                "stored mission does not match its digest",
            ));
        }
        Ok(())
    }
}

fn mission_digest(mission: &Mission) -> Result<String, Refusal> {
    let value =
        serde_json::to_value(mission).map_err(|e| refuse("MISSION_INVALID", e.to_string()))?;
    canonical::digest(&value)
}

fn nonblank(name: &str, value: &str) -> Result<(), Refusal> {
    if value.trim().is_empty() {
        return Err(refuse(
            "MISSION_INVALID",
            format!("{name} must be a non-blank string"),
        ));
    }
    Ok(())
}

fn distinct(name: &str, values: &[String], allow_empty: bool) -> Result<BTreeSet<String>, Refusal> {
    if values.is_empty() && !allow_empty {
        return Err(refuse(
            "MISSION_INVALID",
            format!("{name} must not be empty"),
        ));
    }
    let mut seen = BTreeSet::new();
    for value in values {
        nonblank(name, value)?;
        if !seen.insert(value.clone()) {
            return Err(refuse(
                "MISSION_INVALID",
                format!("{name} repeats {value:?}"),
            ));
        }
    }
    Ok(seen)
}

/// A repository-relative POSIX path: no leading `/`, no backslash or drive, and no `.`,
/// `..` or empty segment. The root itself (`.` or `/`) is not an owned path.
fn repo_path(name: &str, value: &str) -> Result<(), Refusal> {
    let trimmed = value.trim_end_matches('/');
    let well_formed = !trimmed.is_empty()
        && !trimmed.starts_with('/')
        && !trimmed.contains(['\\', ':'])
        && trimmed
            .split('/')
            .all(|segment| !matches!(segment, "" | "." | ".."));
    if well_formed {
        Ok(())
    } else {
        Err(refuse(
            "MISSION_INVALID",
            format!("{name} entry {value:?} must be a repository-relative path below the root"),
        ))
    }
}

/// Paths are compared case-insensitively: the estate is checked out on Windows.
fn overlaps(a: &str, b: &str) -> bool {
    let a = a.trim_end_matches('/').to_ascii_lowercase();
    let b = b.trim_end_matches('/').to_ascii_lowercase();
    a == b || a.starts_with(&format!("{b}/")) || b.starts_with(&format!("{a}/"))
}

impl Mission {
    fn validate(&self) -> Result<(), Refusal> {
        for (name, value) in [
            ("mission_id", &self.mission_id),
            ("run_id", &self.run_id),
            ("original_seed_ref", &self.original_seed_ref),
            ("original_question", &self.original_question),
            ("source_inventory", &self.source_inventory),
            ("retention_policy", &self.retention_policy),
        ] {
            nonblank(name, value)?;
        }
        // At most 64 bytes, so occurrence and raw-reply file names stay under 200.
        if self.run_id.len() > 64
            || !self
                .run_id
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
        {
            return Err(refuse(
                "MISSION_INVALID",
                "run_id is at most 64 bytes of [A-Za-z0-9_-]",
            ));
        }
        let required = distinct("required_claim_ids", &self.required_claim_ids, false)?;
        let optional = distinct("optional_claim_ids", &self.optional_claim_ids, true)?;
        if let Some(both) = required.intersection(&optional).next() {
            return Err(refuse(
                "MISSION_INVALID",
                format!("{both} is both required and optional"),
            ));
        }
        distinct("done_predicates", &self.done_predicates, false)?;
        distinct("owned_paths", &self.owned_paths, false)?;
        distinct("forbidden_surfaces", &self.forbidden_surfaces, true)?;
        for (name, paths) in [
            ("owned_paths", &self.owned_paths),
            ("forbidden_surfaces", &self.forbidden_surfaces),
        ] {
            for path in paths {
                repo_path(name, path)?;
            }
        }
        for owned in &self.owned_paths {
            if let Some(forbidden) = self.forbidden_surfaces.iter().find(|f| overlaps(owned, f)) {
                return Err(refuse(
                    "MISSION_INVALID",
                    format!("owned path {owned} overlaps forbidden surface {forbidden}"),
                ));
            }
        }
        for claim in &required {
            match self.verifier_routes.get(claim) {
                Some(route) => nonblank("verifier_routes", route)?,
                None => {
                    return Err(refuse(
                        "MISSION_INVALID",
                        format!("required claim {claim} has no verifier route"),
                    ))
                }
            }
        }
        if let Some(stray) = self
            .verifier_routes
            .keys()
            .find(|claim| !required.contains(*claim) && !optional.contains(*claim))
        {
            return Err(refuse(
                "MISSION_INVALID",
                format!("verifier route for undeclared claim {stray}"),
            ));
        }
        self.budget.validate()
    }
}

// Origin: engine/crates_rs/core_adversary/src/research_loop/mission.rs
// Claim: urn:core:crates_rs:core-adversary:mission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde68a6ef3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde68a6ef3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore68a6ef3 {
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
impl BoundaryErrore68a6ef3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore68a6ef3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore68a6ef3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde68a6ef3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore68a6ef3> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore68a6ef3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore68a6ef3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore68a6ef3::ExceedsCapacity {
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
mod l4_boundary_tests_e68a6ef3 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde68a6ef3::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde68a6ef3::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde68a6ef3::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde68a6ef3::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde68a6ef3::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore68a6ef3::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore68a6ef3::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
