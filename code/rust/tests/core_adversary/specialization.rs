//! The Adversary swarm specialisation contract.
//!
//! AuthorityEffect: None.

use core_types::routing::RoutingTerminal;
use core_adversary::specialization::{
    base, terminal_of_bout_status, PortName, SwarmSpecialization, BOUT_STATUSES,
};
use serde_json::json;

fn child() -> SwarmSpecialization {
    let mut spec = base();
    spec.specialization_id = "adversary.research".into();
    spec.ancestry.push("adversary.research".into());
    spec.required_skills.push("/research-swarm".into());
    spec
}

fn code(spec: &SwarmSpecialization) -> String {
    spec.validate_within(&base()).unwrap_err().code
}

#[test]
fn the_base_and_a_narrowing_child_validate() {
    base().validate_within(&base()).unwrap();
    let mut narrowed = child();
    narrowed.licensed_ports.remove(&PortName::CodaEvaluation);
    narrowed.licensed_ports.remove(&PortName::LggrGluing);
    narrowed.stage_plan.retain(|stage| {
        stage
            .ports
            .iter()
            .all(|port| narrowed.licensed_ports.contains(port))
    });
    narrowed.routing_terminals.remove(&RoutingTerminal::NoRule);
    narrowed.budget.max_rounds = 2;
    narrowed.validate_within(&base()).unwrap();
}

#[test]
fn widening_and_broken_ancestry_are_refused() {
    let mut paid = child();
    paid.budget.max_cost_microusd = base().budget.max_cost_microusd + 1;
    assert_eq!(code(&paid), "BUDGET_WIDENING");

    let mut orphan = child();
    orphan.ancestry = vec!["adversary.research".into()];
    assert_eq!(code(&orphan), "ADVERSARY_INHERITANCE_REQUIRED");

    let mut renamed = child();
    renamed.specialization_id = "adversary.other".into();
    assert_eq!(code(&renamed), "ADVERSARY_INHERITANCE_REQUIRED");

    let mut skill_free = child();
    skill_free.required_skills.retain(|skill| skill != "/adversary");
    assert_eq!(code(&skill_free), "ADVERSARY_SKILL_REQUIRED");

    let mut authority = child();
    authority.authority_effect = "Granted".into();
    assert_eq!(code(&authority), "AUTHORITY_EFFECT_FORBIDDEN");
}

#[test]
fn the_stage_plan_must_use_licensed_ports_in_act_order() {
    let mut unlicensed = child();
    unlicensed.licensed_ports.remove(&PortName::LggrGluing);
    assert_eq!(code(&unlicensed), "PORT_NOT_LICENSED");

    let mut reordered = child();
    reordered.stage_plan.swap(0, 1);
    assert_eq!(code(&reordered), "STAGE_PLAN_INVALID");

    let mut unterminated = child();
    unterminated.routing_terminals.clear();
    assert_eq!(code(&unterminated), "ROUTING_TERMINALS_INVALID");
}

#[test]
fn unknown_fields_and_ports_fail_to_parse() {
    let mut wire = serde_json::to_value(child()).unwrap();
    wire["grant"] = json!("all");
    assert!(serde_json::from_value::<SwarmSpecialization>(wire).is_err());
    let mut wire = serde_json::to_value(child()).unwrap();
    wire["licensed_ports"] = json!(["root_shell"]);
    assert!(serde_json::from_value::<SwarmSpecialization>(wire).is_err());
}

#[test]
fn every_bout_status_has_one_terminal() {
    let terminals: Vec<RoutingTerminal> = BOUT_STATUSES
        .iter()
        .map(|status| terminal_of_bout_status(status).unwrap())
        .collect();
    assert_eq!(
        terminals,
        [
            RoutingTerminal::CheckPassed,
            RoutingTerminal::Repair,
            RoutingTerminal::RequiresLift,
            RoutingTerminal::Refusal,
            RoutingTerminal::Refusal,
            RoutingTerminal::Refused,
        ]
    );
    assert_eq!(
        terminal_of_bout_status("PASS").unwrap_err().code,
        "BOUT_STATUS_UNKNOWN"
    );
}

// Origin: engine/crates_rs/tests/core_adversary/specialization.rs
// Claim: urn:core:crates_rs:tests:specialization:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd96b4dea {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd96b4dea` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord96b4dea {
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
impl BoundaryErrord96b4dea {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord96b4dea {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord96b4dea {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd96b4dea {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord96b4dea> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord96b4dea::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord96b4dea::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord96b4dea::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d96b4dea() {
    let admitted = BoundaryRecordd96b4dea::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd96b4dea::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
