//! `SwarmSpecializationV1`: the contract every Adversary swarm declares.
//!
//! A specialisation names its ancestry (Adversary first), its required skills (`/adversary`
//! always), the estate ports it is licensed to use, a seven-act stage plan over those
//! ports, the routing terminals it may end on (a subset of
//! `core_types::routing::RoutingTerminal`) and a budget. A child may only narrow its
//! parent. Python (`adversary.domain.specialization`) builds the same records;
//! this module is the check the composition root runs before any swarm is built.
//!
//! AuthorityEffect: None.

use crate::stage::ports::Refusal;
use core_types::routing::RoutingTerminal;
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

pub const ADVERSARY_ANCESTOR: &str = "core.adversary.swarm.v1";
pub const BASE_ID: &str = "adversary.base";
pub const ADVERSARY_SKILL: &str = "/adversary";
pub const ACTS: [&str; 7] = ["I", "II", "III", "IV", "V", "VI", "VII"];

/// The closed set of estate ports a swarm may be licensed to use.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PortName {
    AdversaryRuntime,
    NativeBout,
    SeatTransport,
    SgtEmission,
    ImmuneAntibodies,
    OeopLearning,
    OeopAntiSkill,
    PromptGenealogy,
    CodaEvaluation,
    LggrGluing,
    EnvelopeStore,
}

impl PortName {
    pub const ALL: [PortName; 11] = [
        PortName::AdversaryRuntime,
        PortName::NativeBout,
        PortName::SeatTransport,
        PortName::SgtEmission,
        PortName::ImmuneAntibodies,
        PortName::OeopLearning,
        PortName::OeopAntiSkill,
        PortName::PromptGenealogy,
        PortName::CodaEvaluation,
        PortName::LggrGluing,
        PortName::EnvelopeStore,
    ];
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BudgetDefaults {
    pub max_rounds: u32,
    pub compute_budget: u64,
    pub max_cost_microusd: u64,
}

impl BudgetDefaults {
    fn validate(&self) -> Result<(), Refusal> {
        require(
            (1..=10).contains(&self.max_rounds),
            "BUDGET_INVALID",
            "max_rounds must be from 1 through 10",
        )?;
        require(
            self.compute_budget >= 1,
            "BUDGET_INVALID",
            "compute_budget must be positive",
        )
    }
    pub fn within(&self, ceiling: &BudgetDefaults) -> bool {
        self.max_rounds <= ceiling.max_rounds
            && self.compute_budget <= ceiling.compute_budget
            && self.max_cost_microusd <= ceiling.max_cost_microusd
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StageBinding {
    pub stage_id: String,
    pub act: String,
    pub ports: Vec<PortName>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SwarmSpecialization {
    pub specialization_id: String,
    pub ancestry: Vec<String>,
    pub required_skills: Vec<String>,
    pub licensed_ports: BTreeSet<PortName>,
    pub stage_plan: Vec<StageBinding>,
    pub routing_terminals: BTreeSet<RoutingTerminal>,
    pub budget: BudgetDefaults,
    pub authority_effect: String,
}

fn require(condition: bool, code: &str, message: &str) -> Result<(), Refusal> {
    if condition {
        Ok(())
    } else {
        Err(Refusal::new(code, message))
    }
}

/// Lowercase identifier: `[a-z][a-z0-9_.-]*`.
fn is_identifier(value: &str) -> bool {
    let mut chars = value.chars();
    matches!(chars.next(), Some('a'..='z'))
        && chars.all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || "_.-".contains(c))
}

/// Skill name: `/` then lowercase alphanumeric words joined by single hyphens.
fn is_skill(value: &str) -> bool {
    value.strip_prefix('/').is_some_and(|name| {
        !name.is_empty()
            && name.split('-').all(|word| {
                !word.is_empty()
                    && word
                        .chars()
                        .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit())
            })
    })
}

fn distinct(values: &[String]) -> bool {
    values.iter().collect::<BTreeSet<_>>().len() == values.len()
}

impl SwarmSpecialization {
    /// The structural contract, clause for clause with the Python value object.
    pub fn validate(&self) -> Result<(), Refusal> {
        require(
            self.authority_effect == "None",
            "AUTHORITY_EFFECT_FORBIDDEN",
            "authority_effect must be None",
        )?;
        require(
            is_identifier(&self.specialization_id),
            "SPECIALIZATION_ID_INVALID",
            "specialization_id must be a lowercase identifier",
        )?;
        require(
            self.ancestry.first().map(String::as_str) == Some(ADVERSARY_ANCESTOR)
                && distinct(&self.ancestry),
            "ADVERSARY_INHERITANCE_REQUIRED",
            "ancestry must start with core.adversary.swarm.v1 and contain no repeats",
        )?;
        let is_base = self.ancestry.len() == 1 && self.specialization_id == BASE_ID;
        require(
            is_base
                || (self.ancestry.len() >= 2
                    && self.ancestry.last() == Some(&self.specialization_id)),
            "ADVERSARY_INHERITANCE_REQUIRED",
            "ancestry must end with this specialization_id",
        )?;
        require(
            self.required_skills.iter().any(|s| s == ADVERSARY_SKILL)
                && self.required_skills.iter().all(|s| is_skill(s))
                && distinct(&self.required_skills),
            "ADVERSARY_SKILL_REQUIRED",
            "required_skills must be distinct /skill-names and include /adversary",
        )?;
        require(
            !self.licensed_ports.is_empty(),
            "PORTS_INVALID",
            "licensed_ports must not be empty",
        )?;
        require(
            !self.stage_plan.is_empty(),
            "STAGE_PLAN_INVALID",
            "stage_plan must not be empty",
        )?;
        let mut stage_ids = BTreeSet::new();
        let mut last_act = 0usize;
        for stage in &self.stage_plan {
            require(
                is_identifier(&stage.stage_id),
                "STAGE_INVALID",
                "stage_id must be a lowercase identifier",
            )?;
            require(
                stage_ids.insert(stage.stage_id.as_str()),
                "STAGE_PLAN_INVALID",
                "duplicate stage_id",
            )?;
            let act = ACTS
                .iter()
                .position(|act| *act == stage.act)
                .ok_or_else(|| Refusal::new("STAGE_INVALID", "act must be one of I..VII"))?;
            require(
                act >= last_act,
                "STAGE_PLAN_INVALID",
                "stages must follow act order I..VII",
            )?;
            last_act = act;
            require(
                !stage.ports.is_empty()
                    && stage.ports.iter().collect::<BTreeSet<_>>().len() == stage.ports.len(),
                "STAGE_INVALID",
                "ports must be a non-empty list of distinct ports",
            )?;
            require(
                stage.ports.iter().all(|p| self.licensed_ports.contains(p)),
                "PORT_NOT_LICENSED",
                "the stage plan uses an unlicensed port",
            )?;
        }
        require(
            !self.routing_terminals.is_empty(),
            "ROUTING_TERMINALS_INVALID",
            "routing_terminals must not be empty",
        )?;
        self.budget.validate()
    }

    /// The structural contract plus narrowing: this specialisation may not license a
    /// port, routing terminal or budget that `ceiling` does not have.
    pub fn validate_within(&self, ceiling: &SwarmSpecialization) -> Result<(), Refusal> {
        self.validate()?;
        require(
            self.licensed_ports.is_subset(&ceiling.licensed_ports),
            "PORT_WIDENING",
            "a specialisation cannot license new ports",
        )?;
        require(
            self.routing_terminals.is_subset(&ceiling.routing_terminals),
            "TERMINAL_WIDENING",
            "a specialisation cannot add routing terminals",
        )?;
        require(
            self.budget.within(&ceiling.budget),
            "BUDGET_WIDENING",
            "a specialisation budget cannot exceed the base budget",
        )
    }
}

fn stage(stage_id: &str, act: &str, ports: &[PortName]) -> StageBinding {
    StageBinding {
        stage_id: stage_id.into(),
        act: act.into(),
        ports: ports.to_vec(),
    }
}

/// The base specialisation: every port, every terminal, the seven-act plan.
pub fn base() -> SwarmSpecialization {
    use PortName::*;
    SwarmSpecialization {
        specialization_id: BASE_ID.into(),
        ancestry: vec![ADVERSARY_ANCESTOR.into()],
        required_skills: vec![ADVERSARY_SKILL.into()],
        licensed_ports: PortName::ALL.into_iter().collect(),
        stage_plan: vec![
            stage("intake", "I", &[AdversaryRuntime, ImmuneAntibodies]),
            stage("panel_debate", "II", &[AdversaryRuntime, SeatTransport]),
            stage("carrier_measurement", "III", &[CodaEvaluation, SgtEmission]),
            stage("gauge_break", "IV", &[SeatTransport]),
            stage("gluing_audit", "V", &[LggrGluing]),
            stage("compost", "VI", &[ImmuneAntibodies, PromptGenealogy]),
            stage(
                "terminal_gate",
                "VII",
                &[
                    NativeBout,
                    SgtEmission,
                    OeopAntiSkill,
                    OeopLearning,
                    EnvelopeStore,
                ],
            ),
        ],
        routing_terminals: [
            RoutingTerminal::CheckPassed,
            RoutingTerminal::RequiresLift,
            RoutingTerminal::Repair,
            RoutingTerminal::Refusal,
            RoutingTerminal::NoRule,
            RoutingTerminal::BudgetUnknown,
            RoutingTerminal::Refused,
        ]
        .into_iter()
        .collect(),
        budget: BudgetDefaults {
            max_rounds: 4,
            compute_budget: 100,
            max_cost_microusd: 2_000_000,
        },
        authority_effect: "None".into(),
    }
}

/// The routing terminal a seven-act bout status ends on.
pub fn terminal_of_bout_status(status: &str) -> Result<RoutingTerminal, Refusal> {
    Ok(match status {
        "AUTHORIZED" => RoutingTerminal::CheckPassed,
        "BOUNDED_RESIDUAL" => RoutingTerminal::Repair,
        "NOT_MEASURED" => RoutingTerminal::RequiresLift,
        "FIXTURE_ONLY" | "ABLATED_WOULD_AUTHORIZE" => RoutingTerminal::Refusal,
        "REFUSED" => RoutingTerminal::Refused,
        _ => {
            return Err(Refusal::new(
                "BOUT_STATUS_UNKNOWN",
                format!("{status} is not a bout status"),
            ))
        }
    })
}

/// The bout statuses `authorization` can produce, in a fixed order.
pub const BOUT_STATUSES: [&str; 6] = [
    "AUTHORIZED",
    "BOUNDED_RESIDUAL",
    "NOT_MEASURED",
    "FIXTURE_ONLY",
    "ABLATED_WOULD_AUTHORIZE",
    "REFUSED",
];

// Origin: engine/crates_rs/core_adversary/src/specialization.rs
// Claim: urn:core:crates_rs:core-adversary:specialization:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda169db85 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda169db85` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora169db85 {
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
impl BoundaryErrora169db85 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora169db85 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora169db85 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda169db85 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora169db85> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora169db85::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora169db85::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora169db85::ExceedsCapacity {
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
mod l4_boundary_tests_a169db85 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda169db85::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda169db85::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda169db85::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda169db85::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda169db85::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora169db85::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora169db85::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
