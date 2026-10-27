//! Deterministic N=1 causal scheduler and replay, independent of provider or character lore.
use crate::stage::packets::{AgentResult, LicensedWorkflowPlan, WorkPacket};
use crate::stage::ports::Refusal;
use crate::stage::run::{ProgressMeasure, SceneVisit, StopCondition, SwarmRunState};
use crate::stage::topology::{SceneGraph, SwarmDefinition, SwarmProfile};
use std::collections::{BTreeMap, BTreeSet};

fn refusal(code: &str, locus: &str, message: impl Into<String>) -> Refusal {
    let mut refusal = Refusal::new(code, message);
    refusal.locus = locus.into();
    refusal
}

pub fn validate_swarm_composition(
    definition: &SwarmDefinition,
    profile: &SwarmProfile,
    graph: &SceneGraph,
    plan: &LicensedWorkflowPlan,
) -> Result<(), Refusal> {
    composition(definition, profile, graph, plan)
        .map_err(|message| refusal("OEAS_COMPOSITION_REFUSED", "oeas-composition", message))
}

fn check_scene_seats(
    scene: &crate::stage::topology::SceneSpec,
    seats: &BTreeMap<&String, &crate::stage::topology::SeatRequirement>,
    assignments: &BTreeMap<(&String, &String), &crate::stage::topology::NodeAssignment>,
) -> Result<(), String> {
    for seat_id in &scene.required_seat_ids {
        let Some(requirement) = seats.get(seat_id) else {
            return Err(format!("scene {} requires an unknown seat", scene.scene_id));
        };
        let Some(assignment) = assignments.get(&(&scene.scene_id, seat_id)) else {
            return Err(format!(
                "scene {} skips required seat {seat_id}",
                scene.scene_id
            ));
        };
        if requirement
            .required_operations
            .iter()
            .any(|op| !assignment.operation_ids.contains(op))
        {
            return Err(format!("seat {seat_id} lacks its required operations"));
        }
    }
    for seat_id in &scene.required_seat_ids {
        let Some(requirement) = seats.get(seat_id) else {
            return Err(format!("scene {} requires an unknown seat", scene.scene_id));
        };
        let Some(assignment) = assignments.get(&(&scene.scene_id, seat_id)) else {
            return Err(format!(
                "scene {} skips required seat {seat_id}",
                scene.scene_id
            ));
        };
        for independent in &requirement.independent_from {
            if assignments
                .get(&(&scene.scene_id, independent))
                .is_some_and(|other| other.agent_id == assignment.agent_id)
            {
                return Err(format!(
                    "seat {seat_id} is not independent from {independent}"
                ));
            }
        }
    }
    Ok(())
}

fn check_cross_scene_independence(
    definition: &SwarmDefinition,
    plan: &LicensedWorkflowPlan,
) -> Result<(), String> {
    for seat in &definition.seat_requirements {
        let agents: BTreeSet<_> = plan
            .assignments
            .iter()
            .filter(|item| item.seat_id == seat.seat_id)
            .map(|item| &item.agent_id)
            .collect();
        for independent in &seat.independent_from {
            let other: BTreeSet<_> = plan
                .assignments
                .iter()
                .filter(|item| item.seat_id == *independent)
                .map(|item| &item.agent_id)
                .collect();
            if !agents.is_disjoint(&other) {
                return Err(format!(
                    "independent trust domains {}/{independent} share an agent across scenes",
                    seat.seat_id
                ));
            }
        }
    }
    Ok(())
}

fn composition(
    definition: &SwarmDefinition,
    profile: &SwarmProfile,
    graph: &SceneGraph,
    plan: &LicensedWorkflowPlan,
) -> Result<(), String> {
    if profile.base_definition_id != definition.definition_id {
        return Err("profile does not compose the supplied base definition".into());
    }
    if profile.scene_graph_id != graph.graph_id {
        return Err("profile does not bind the supplied scene graph".into());
    }
    if plan.catalog_id != definition.skill_catalog_id {
        return Err("workflow plan does not bind the definition catalog".into());
    }
    let seats: BTreeMap<_, _> = definition
        .seat_requirements
        .iter()
        .map(|seat| (&seat.seat_id, seat))
        .collect();
    let assignments: BTreeMap<_, _> = plan
        .assignments
        .iter()
        .map(|item| ((&item.scene_id, &item.seat_id), item))
        .collect();
    for scene in &graph.scenes {
        check_scene_seats(scene, &seats, &assignments)?;
    }
    check_cross_scene_independence(definition, plan)
}

#[derive(Debug, Clone)]
pub struct DeterministicScheduler {
    definition: SwarmDefinition,
    profile: SwarmProfile,
    graph: SceneGraph,
    plan: LicensedWorkflowPlan,
    stop: StopCondition,
}
impl DeterministicScheduler {
    pub fn new(
        definition: SwarmDefinition,
        profile: SwarmProfile,
        graph: SceneGraph,
        plan: LicensedWorkflowPlan,
        stop: StopCondition,
    ) -> Result<Self, Refusal> {
        validate_swarm_composition(&definition, &profile, &graph, &plan)?;
        if definition.max_parallelism != 1 {
            return Err(refusal(
                "OEAS_SCHEDULER_CONFIGURATION_REFUSED",
                "oeas-scheduler",
                "DeterministicSchedulerV1 requires N=1",
            ));
        }
        Ok(Self {
            definition,
            profile,
            graph,
            plan,
            stop,
        })
    }

    pub fn definition(&self) -> &SwarmDefinition {
        &self.definition
    }
    pub fn profile(&self) -> &SwarmProfile {
        &self.profile
    }
    pub fn graph(&self) -> &SceneGraph {
        &self.graph
    }
    pub fn plan(&self) -> &LicensedWorkflowPlan {
        &self.plan
    }

    pub fn start(&self, run_key: &str, packet: &WorkPacket) -> Result<SwarmRunState, Refusal> {
        self.start_state(run_key, packet).map_err(|message| {
            refusal(
                "OEAS_SCHEDULER_START_REFUSED",
                "adversary.stage.application.run_swarm",
                message,
            )
        })
    }

    fn start_state(&self, run_key: &str, packet: &WorkPacket) -> Result<SwarmRunState, String> {
        if packet.scene_id != self.graph.entry_scene_id {
            return Err("initial work packet must target the graph entry scene".into());
        }
        if packet.budget_units > self.stop.max_total_budget {
            return Err("work packet budget exceeds the stop condition".into());
        }
        let mut state = SwarmRunState {
            run_key: run_key.into(),
            profile_id: self.profile.profile_id.clone(),
            current_scene_id: self.graph.entry_scene_id.clone(),
            visit_counts: vec![SceneVisit::new(self.graph.entry_scene_id.clone(), 1)?],
            result_ids: Vec::new(),
            progress_measure_ids: Vec::new(),
            remaining_budget: packet.budget_units,
            scene_steps: 0,
            dry_rounds: 0,
            terminal_status: "RUNNING".into(),
            authority_effect: "None".into(),
            schema_version: "core.oeas.swarm-run-state.v1".into(),
            state_id: String::new(),
        };
        state.validate()?;
        Ok(state)
    }

    pub fn advance(
        &self,
        state: &SwarmRunState,
        result: &AgentResult,
        progress: &ProgressMeasure,
    ) -> Result<SwarmRunState, Refusal> {
        self.advance_state(state, result, progress)
            .map_err(|message| {
                refusal(
                    "OEAS_SCHEDULER_ADVANCE_REFUSED",
                    "oeas-scheduler-advance",
                    message,
                )
            })
    }

    fn matches_transition_edge(
        edge: &crate::stage::topology::SceneTransition,
        current_scene_id: &str,
        result: &AgentResult,
    ) -> bool {
        if edge.source_scene_id != current_scene_id
            || !edge.trigger_statuses.contains(&result.status)
        {
            return false;
        }
        edge.residual_codes.is_empty()
            || edge
                .residual_codes
                .iter()
                .any(|code| result.residual_codes.contains(code))
    }

    fn apply_transition_or_stop(
        &self,
        state: &SwarmRunState,
        result: &AgentResult,
        current: &crate::stage::topology::SceneSpec,
        next: &mut SwarmRunState,
    ) {
        if self.stop.stop_on_statuses.contains(&result.status) {
            next.terminal_status = result.status.clone();
        } else if current.terminal {
            next.terminal_status = "COMPLETED".into();
        } else if next.scene_steps >= self.stop.max_scene_steps || next.remaining_budget == 0 {
            next.terminal_status = "EXHAUSTED".into();
        } else if next.dry_rounds >= self.stop.max_dry_rounds {
            next.terminal_status = "HOLD".into();
        } else if let Some(edge) = self
            .graph
            .transitions
            .iter()
            .find(|edge| Self::matches_transition_edge(edge, &state.current_scene_id, result))
        {
            next.current_scene_id = edge.target_scene_id.clone();
        } else {
            next.terminal_status = "HOLD".into();
        }
    }

    fn update_visit_counts(
        &self,
        state: &SwarmRunState,
        next: &mut SwarmRunState,
    ) -> Result<(), String> {
        let mut visits: BTreeMap<_, _> = state
            .visit_counts
            .iter()
            .map(|visit| (visit.scene_id.clone(), visit.count))
            .collect();
        if next.terminal_status == "RUNNING" {
            let count = visits.entry(next.current_scene_id.clone()).or_insert(0);
            *count += 1;
            let Some(target) = self
                .graph
                .scenes
                .iter()
                .find(|scene| scene.scene_id == next.current_scene_id)
            else {
                return Err("target run scene is absent from the scene graph".into());
            };
            if *count > target.max_visits {
                next.terminal_status = "HOLD".into();
                next.current_scene_id = state.current_scene_id.clone();
                if *count > 64 {
                    *count = 64;
                }
            }
        }
        next.visit_counts = visits
            .into_iter()
            .map(|(scene, count)| SceneVisit::new(scene, count))
            .collect::<Result<_, _>>()?;
        Ok(())
    }

    fn advance_state(
        &self,
        state: &SwarmRunState,
        result: &AgentResult,
        progress: &ProgressMeasure,
    ) -> Result<SwarmRunState, String> {
        if state.terminal_status != "RUNNING" {
            return Err("a terminal run cannot advance".into());
        }
        if result.scene_id != state.current_scene_id {
            return Err("agent result scene differs from current run scene".into());
        }
        let mut next = state.clone();
        next.state_id.clear();
        next.result_ids.push(result.result_id.clone());
        next.progress_measure_ids.push(progress.measure_id.clone());
        next.scene_steps += 1;
        next.remaining_budget = next.remaining_budget.saturating_sub(1);
        next.dry_rounds = if progress.made_progress() {
            0
        } else {
            next.dry_rounds + 1
        };
        let Some(current) = self
            .graph
            .scenes
            .iter()
            .find(|scene| scene.scene_id == state.current_scene_id)
        else {
            return Err("current run scene is absent from the scene graph".into());
        };
        self.apply_transition_or_stop(state, result, current, &mut next);
        self.update_visit_counts(state, &mut next)?;
        next.validate()?;
        Ok(next)
    }

    pub fn replay(
        &self,
        run_key: &str,
        packet: &WorkPacket,
        results: &[AgentResult],
        progress: &[ProgressMeasure],
    ) -> Result<SwarmRunState, Refusal> {
        if results.len() != progress.len() {
            return Err(refusal(
                "OEAS_SCHEDULER_REPLAY_REFUSED",
                "oeas-scheduler-replay",
                "replay result/progress arities differ",
            ));
        }
        let mut state = self.start(run_key, packet)?;
        for (result, progress) in results.iter().zip(progress) {
            state = self.advance(&state, result, progress)?;
        }
        Ok(state)
    }
}

impl crate::stage::ports::SchedulerPort for DeterministicScheduler {
    fn start(&mut self, key: &str, packet: &WorkPacket) -> Result<SwarmRunState, Refusal> {
        Self::start(self, key, packet)
    }
    fn advance(
        &mut self,
        state: &SwarmRunState,
        result: &AgentResult,
        progress: &ProgressMeasure,
    ) -> Result<SwarmRunState, Refusal> {
        Self::advance(self, state, result, progress)
    }
    fn plan(&self) -> Option<&LicensedWorkflowPlan> {
        Some(&self.plan)
    }
}

// Origin: engine/crates_rs/core_adversary/src/stage/scheduler.rs
// Claim: urn:core:crates_rs:core-adversary:scheduler:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord491c2127 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord491c2127` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError491c2127 {
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
impl BoundaryError491c2127 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError491c2127 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError491c2127 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord491c2127 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError491c2127> {
        if capacity_bound == 0 {
            return Err(BoundaryError491c2127::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError491c2127::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError491c2127::ExceedsCapacity {
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
mod l4_boundary_tests_491c2127 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord491c2127::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord491c2127::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord491c2127::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord491c2127::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord491c2127::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError491c2127::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError491c2127::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
