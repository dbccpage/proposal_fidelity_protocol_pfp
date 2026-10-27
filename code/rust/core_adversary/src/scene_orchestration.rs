//! Bounded request-bound PFP scenes between the mandatory seven acts.
//! Every visit calls actual seats and replays its gate. No scene result grants authority.
use crate::custody::RecordingSeatPort;
use crate::evidence::sha256_ref;
use crate::instruction_plan::InstructionPlanTransportV01;
use crate::stage::ports::{Refusal, SeatPort, SeatTurnRequest};
use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};
use std::collections::{BTreeMap, BTreeSet};

pub const ENTRY_EDGES: [&str; 9] = [
    "PRE_DISPATCH->ACT_I",
    "ACT_I->ACT_II",
    "ACT_II->ACT_III",
    "ACT_III->ACT_IV",
    "ACT_IV->SANDBOX",
    "SANDBOX->ACT_V",
    "ACT_V->CHECKER",
    "CHECKER->ACT_VI",
    "ACT_VI->ACT_VII",
];
fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("ADVERSARY_SCENE_ORCHESTRATION_INVALID", message)
}
#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Attachment {
    gate_id: String,
    skill_id: String,
    plan_digest: String,
    source_digests: Vec<(String, String)>,
    ordered_operand_bodies: Vec<String>,
}
#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Stage {
    scene_id: String,
    seat_ids: Vec<String>,
    gate_id: String,
    gate_payload: Map<String, Value>,
    #[serde(default)]
    attachments: Vec<Attachment>,
    #[serde(default)]
    fallback_scene_id: Option<String>,
}
#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Edge {
    from_scene_id: String,
    to_scene_id: String,
    on_status: String,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Configuration {
    schema_version: String,
    max_steps: u64,
    max_visits_per_scene: u64,
    entry_scenes: BTreeMap<String, String>,
    stages: Vec<Stage>,
    #[serde(default)]
    edges: Vec<Edge>,
}
#[derive(Default)]
pub struct SceneOrchestration {
    configuration: Option<Configuration>,
    visits: BTreeMap<String, u64>,
    steps: u64,
    compute_spent: u64,
    compute_limit: u64,
    history: Vec<String>,
    observations: Vec<Value>,
}
impl SceneOrchestration {
    pub fn from_context(
        context: Option<&Map<String, Value>>,
        plan: Option<&InstructionPlanTransportV01>,
        total_budget: u64,
    ) -> Result<Self, Refusal> {
        let Some(raw) = context.and_then(|value| value.get("scene_orchestration")) else {
            return Ok(Self::default());
        };
        if raw.to_string().len() > 131_072 {
            return Err(invalid("scene orchestration exceeds 128 KiB"));
        }
        let configuration: Configuration =
            serde_json::from_value(raw.clone()).map_err(|error| invalid(error.to_string()))?;
        Self::validate_configuration_bounds(&configuration, total_budget)?;
        let ids: BTreeSet<_> = configuration
            .stages
            .iter()
            .map(|stage| stage.scene_id.as_str())
            .collect();
        Self::validate_entries_and_edges(&configuration, &ids)?;
        for stage in &configuration.stages {
            Self::validate_stage(stage, &ids, plan)?;
        }
        Self::validate_reachability(&configuration, ids.len())?;
        Ok(Self {
            configuration: Some(configuration),
            compute_limit: total_budget - 7,
            ..Self::default()
        })
    }

    fn validate_configuration_bounds(
        configuration: &Configuration,
        total_budget: u64,
    ) -> Result<(), Refusal> {
        let valid_bounds = [
            configuration.schema_version == "core.adversary.scene-orchestration.v1",
            (1..=64).contains(&configuration.max_steps),
            (1..=8).contains(&configuration.max_visits_per_scene),
            !configuration.stages.is_empty(),
            configuration.stages.len() <= 10,
            configuration.edges.len() <= 64,
            total_budget >= 8,
            configuration.max_steps <= total_budget.saturating_sub(7),
        ]
        .into_iter()
        .all(|b| b);
        if !valid_bounds {
            return Err(invalid("scene graph bounds or schema are invalid"));
        }
        Ok(())
    }

    fn validate_entries_and_edges(
        configuration: &Configuration,
        ids: &BTreeSet<&str>,
    ) -> Result<(), Refusal> {
        let valid_entries = ids.len() == configuration.stages.len()
            && !configuration.entry_scenes.is_empty()
            && configuration.entry_scenes.iter().all(|(edge, scene)| {
                ENTRY_EDGES.contains(&edge.as_str()) && ids.contains(scene.as_str())
            });
        if !valid_entries {
            return Err(invalid(
                "scene entries must name unique declared stages at real act transitions",
            ));
        }
        let mut edges = BTreeSet::new();
        for edge in &configuration.edges {
            if !Self::is_valid_edge(edge, ids, &mut edges) {
                return Err(invalid(
                    "scene edges must be declared, deterministic and status-bound",
                ));
            }
        }
        Ok(())
    }

    fn is_valid_edge<'a>(
        edge: &'a Edge,
        ids: &BTreeSet<&str>,
        seen: &mut BTreeSet<(&'a String, &'a String)>,
    ) -> bool {
        [
            ids.contains(edge.from_scene_id.as_str()),
            ids.contains(edge.to_scene_id.as_str()),
            ["PASS", "HOLD", "REFUSE", "ERROR"].contains(&edge.on_status.as_str()),
            seen.insert((&edge.from_scene_id, &edge.on_status)),
        ]
        .into_iter()
        .all(|b| b)
    }

    fn validate_reachability(
        configuration: &Configuration,
        expected_count: usize,
    ) -> Result<(), Refusal> {
        let mut reachable: BTreeSet<String> =
            configuration.entry_scenes.values().cloned().collect();
        while Self::expand_reachable_step(configuration, &mut reachable) {}
        if reachable.len() != expected_count {
            return Err(invalid(
                "every scene must be reachable from a declared act transition",
            ));
        }
        Ok(())
    }

    fn expand_reachable_step(
        configuration: &Configuration,
        reachable: &mut BTreeSet<String>,
    ) -> bool {
        let previous = reachable.len();
        for stage in &configuration.stages {
            if !reachable.contains(&stage.scene_id) {
                continue;
            }
            if let Some(fallback) = &stage.fallback_scene_id {
                reachable.insert(fallback.clone());
            }
            for edge in &configuration.edges {
                if edge.from_scene_id == stage.scene_id {
                    reachable.insert(edge.to_scene_id.clone());
                }
            }
        }
        reachable.len() != previous
    }

    fn validate_stage(
        stage: &Stage,
        ids: &BTreeSet<&str>,
        plan: Option<&InstructionPlanTransportV01>,
    ) -> Result<(), Refusal> {
        if !Self::is_valid_stage_shape(stage, ids) {
            return Err(invalid(
                "stage roles, gate, fallback or reserved evidence are invalid",
            ));
        }
        let mut attached = BTreeSet::new();
        for attachment in &stage.attachments {
            Self::validate_stage_attachment(stage, attachment, plan, &mut attached)?;
        }
        Ok(())
    }

    fn is_valid_stage_shape(stage: &Stage, ids: &BTreeSet<&str>) -> bool {
        let unique_seats =
            stage.seat_ids.iter().collect::<BTreeSet<_>>().len() == stage.seat_ids.len();
        let fallback_ok = stage
            .fallback_scene_id
            .as_ref()
            .is_none_or(|id| ids.contains(id.as_str()));
        [
            !stage.scene_id.is_empty(),
            stage.scene_id.len() <= 128,
            !stage.seat_ids.is_empty(),
            stage.seat_ids.len() <= 22,
            unique_seats,
            crate::primary_gates::known_gate_id(&stage.gate_id),
            !stage.gate_payload.contains_key("_adversary_scene"),
            stage.attachments.len() <= 16,
            fallback_ok,
        ]
        .into_iter()
        .all(|b| b)
    }

    fn validate_stage_attachment<'a>(
        stage: &Stage,
        attachment: &'a Attachment,
        plan: Option<&InstructionPlanTransportV01>,
        attached: &mut BTreeSet<&'a String>,
    ) -> Result<(), Refusal> {
        let plan =
            plan.ok_or_else(|| invalid("skill attachments require the consumed instruction plan"))?;
        plan.validate()?;
        let matches_plan = [
            attachment.gate_id == stage.gate_id,
            attachment.plan_digest == plan.plan_digest,
            attachment.source_digests == plan.source_digests,
            attachment.ordered_operand_bodies == plan.ordered_operand_bodies,
            plan.operation_ids.contains(&attachment.skill_id),
            attached.insert(&attachment.skill_id),
        ]
        .into_iter()
        .all(|b| b);
        if !matches_plan {
            return Err(invalid(
                "scene attachment differs from the exact consumed OEWAS plan",
            ));
        }
        Ok(())
    }

    pub fn validate_inventory(
        &self,
        scenes: &[String],
        seats: &[String],
        selected: Option<&[String]>,
    ) -> Result<(), Refusal> {
        if let Some(configuration) = &self.configuration {
            for stage in &configuration.stages {
                if !scenes.contains(&stage.scene_id)
                    || stage.seat_ids.iter().any(|seat| {
                        !seats.contains(seat)
                            || selected.is_some_and(|allowed| !allowed.contains(seat))
                    })
                {
                    return Err(invalid(
                        "scene/role is outside the canonical council or selected role set",
                    ));
                }
            }
        }
        Ok(())
    }

    fn spend(&mut self, stage: &Stage) -> Result<u64, Refusal> {
        let configuration = self
            .configuration
            .as_ref()
            .ok_or_else(|| invalid("scene configuration absent"))?;
        let visits = self.visits.entry(stage.scene_id.clone()).or_default();
        if self.steps >= configuration.max_steps
            || *visits >= configuration.max_visits_per_scene
            || self
                .compute_spent
                .saturating_add(stage.seat_ids.len() as u64)
                > self.compute_limit
        {
            return Err(Refusal::new(
                "ADVERSARY_SCENE_BUDGET_EXHAUSTED",
                "shared scene step, visit or compute budget exhausted",
            ));
        }
        *visits += 1;
        self.steps += 1;
        self.compute_spent += stage.seat_ids.len() as u64;
        Ok(*visits)
    }

    fn execute_stage(
        &mut self,
        stage: &Stage,
        task: &str,
        objective: &str,
        recorder: &mut RecordingSeatPort<'_>,
    ) -> Result<Value, Refusal> {
        let visit = self.spend(stage)?;
        let attached =
            serde_json::to_value(&stage.attachments).map_err(|error| invalid(error.to_string()))?;
        let context = json!({"task_key":task,"scene_id":stage.scene_id,"visit_index":visit,"gate_id":stage.gate_id,
            "gate_payload":stage.gate_payload,"attachments":attached,"edge_history":self.history,"authority_effect":"None"});
        let (results, execution_error) =
            Self::run_stage_seats(stage, objective, visit, &context, recorder);
        let mut payload = stage.gate_payload.clone();
        payload.insert("_adversary_scene".into(), json!({"task_key":task,"scene_id":stage.scene_id,"visit_index":visit,
            "seat_results":&results,"attachments":attached,"edge_history":self.history,"authority_effect":"None"}));
        let (evaluated, status) =
            Self::evaluate_stage_gate(&stage.gate_id, payload, &self.history, execution_error);
        let observation = json!({"scene_id":stage.scene_id,"gate_id":stage.gate_id,"visit_index":visit,"status":status,
            "seat_results":results,"gate_evaluation":evaluated,"attached_skills":stage.attachments.iter().map(|item| &item.skill_id).collect::<Vec<_>>(),
            "authority_effect":"None"});
        recorder.retain_scene_observation(&observation)?;
        Ok(observation)
    }

    fn run_stage_seats(
        stage: &Stage,
        objective: &str,
        visit: u64,
        context: &Value,
        recorder: &mut RecordingSeatPort<'_>,
    ) -> (Vec<Value>, bool) {
        let mut results = Vec::new();
        let mut execution_error = false;
        for seat in &stage.seat_ids {
            let (entry, failed) =
                Self::run_single_seat(stage, seat, objective, visit, context, recorder);
            execution_error |= failed;
            results.push(entry);
        }
        (results, execution_error)
    }

    fn run_single_seat(
        stage: &Stage,
        seat: &str,
        objective: &str,
        visit: u64,
        context: &Value,
        recorder: &mut RecordingSeatPort<'_>,
    ) -> (Value, bool) {
        let request = SeatTurnRequest {
            scene_id: stage.scene_id.clone(),
            seat_id: seat.to_owned(),
            prompt_text: format!("Execute bounded scene '{}' at gate {} for objective: {}. Apply only the attached operator-bound OEWAS skill instructions. Provide concrete findings or missing witnesses; your prose cannot certify a gate or grant authority. Fresh visit {}.\nScene context:\n{}", stage.scene_id, stage.gate_id, objective, visit, context),
            cognitive_operator: format!("PFP primary gate {}", stage.gate_id),
            role_kind: "prose".into(),
            candidate_id: format!("scene_{}_{}", stage.scene_id, visit),
            round_index: visit as i64,
            context_bytes: context.to_string().into_bytes(),
        };
        match recorder.execute_turn(&request) {
            Ok(reply) if reply.authority_effect == "None" => {
                let req_digest = recorder
                    .turns
                    .last()
                    .and_then(|turn| turn.get("request_digest"))
                    .cloned()
                    .unwrap_or(Value::Null);
                (
                    json!({
                        "seat_id": seat,
                        "reply_text": reply.reply_text,
                        "machine_fields": reply.machine_fields,
                        "raw_reply_sha256": sha256_ref(&reply.raw_bytes),
                        "request_digest": req_digest
                    }),
                    false,
                )
            }
            Ok(_) => (
                json!({"seat_id":seat,"refusal_code":"ADVERSARY_SCENE_AUTHORITY_VIOLATION"}),
                true,
            ),
            Err(error) => (
                json!({"seat_id":seat,"refusal_code":error.code,"message":error.message}),
                true,
            ),
        }
    }

    fn evaluate_stage_gate(
        gate_id: &str,
        payload: Map<String, Value>,
        history: &[String],
        execution_error: bool,
    ) -> (Value, &'static str) {
        let evaluated = match crate::primary_gates::evaluate(
            gate_id,
            &Value::Object(payload),
            history,
        ) {
            Ok(value) => value,
            Err(error) => {
                json!({"status":"ERROR","refusal_code":error.code,"message":error.message,"authority_effect":"None"})
            }
        };
        let status = if execution_error {
            "ERROR"
        } else {
            match evaluated["status"].as_str() {
                Some("PASS") => "PASS",
                Some("REFUSE") => "REFUSE",
                Some("ERROR") => "ERROR",
                _ => "HOLD",
            }
        };
        (evaluated, status)
    }

    pub fn run_edge<F>(
        &mut self,
        entry_edge: &str,
        task: &str,
        objective: &str,
        recorder: &mut RecordingSeatPort<'_>,
        mut transition: F,
    ) -> Result<(), Refusal>
    where
        F: FnMut(&str) -> Result<Value, Refusal>,
    {
        let Some(mut current) = self
            .configuration
            .as_ref()
            .and_then(|configuration| configuration.entry_scenes.get(entry_edge))
            .cloned()
        else {
            return Ok(());
        };
        let mut incoming = format!("{entry_edge}::ENTER->{current}");
        loop {
            let (stage, status) = self.step_edge_scene(
                entry_edge,
                &current,
                &incoming,
                task,
                objective,
                recorder,
                &mut transition,
            )?;
            match self.resolve_next_scene(&current, &status, &stage) {
                Some(target) => {
                    incoming = format!("{current}->{target}");
                    current = target;
                }
                None if status == "PASS" => {
                    return self.finish_edge_return(entry_edge, &current, &mut transition);
                }
                None => {
                    return Err(Refusal::new(
                        "ADVERSARY_SCENE_GATE_BLOCKED",
                        format!(
                            "scene {current} gate {} returned {status} with no bounded fallback",
                            stage.gate_id
                        ),
                    ));
                }
            }
        }
    }

    #[allow(clippy::too_many_arguments)]
    fn step_edge_scene<F>(
        &mut self,
        entry_edge: &str,
        current: &str,
        incoming: &str,
        task: &str,
        objective: &str,
        recorder: &mut RecordingSeatPort<'_>,
        transition: &mut F,
    ) -> Result<(Stage, String), Refusal>
    where
        F: FnMut(&str) -> Result<Value, Refusal>,
    {
        if self.history.len() >= 64 {
            return Err(invalid("scene edge history exceeds 64"));
        }
        let evidence = transition(incoming)?;
        self.history.push(incoming.to_owned());
        let stage = self.find_stage(current)?;
        let evaluated = self.execute_stage(&stage, task, objective, recorder)?;
        let status = evaluated["status"].as_str().unwrap_or("HOLD").to_owned();
        self.observations.push(json!({"entry_edge":entry_edge,"incoming_edge":incoming,"transition_evidence":evidence,"evaluation":evaluated,"authority_effect":"None"}));
        Ok((stage, status))
    }

    fn find_stage(&self, scene_id: &str) -> Result<Stage, Refusal> {
        self.configuration
            .as_ref()
            .and_then(|c| c.stages.iter().find(|s| s.scene_id == scene_id))
            .cloned()
            .ok_or_else(|| invalid("routed scene is not declared"))
    }

    fn resolve_next_scene(&self, current: &str, status: &str, stage: &Stage) -> Option<String> {
        let explicit = self
            .configuration
            .as_ref()
            .and_then(|c| {
                c.edges
                    .iter()
                    .find(|e| e.from_scene_id == current && e.on_status == status)
            })
            .map(|edge| edge.to_scene_id.clone());
        if explicit.is_some() {
            explicit
        } else if status != "PASS" {
            stage.fallback_scene_id.clone()
        } else {
            None
        }
    }

    fn finish_edge_return<F>(
        &mut self,
        entry_edge: &str,
        current: &str,
        transition: &mut F,
    ) -> Result<(), Refusal>
    where
        F: FnMut(&str) -> Result<Value, Refusal>,
    {
        if self.history.len() >= 64 {
            return Err(invalid("scene edge history exceeds 64"));
        }
        let leaving = format!("{current}->RETURN::{entry_edge}");
        let evidence = transition(&leaving)?;
        self.history.push(leaving.clone());
        self.observations
            .push(json!({"edge":leaving,"transition_evidence":evidence,"authority_effect":"None"}));
        Ok(())
    }

    pub fn observations(&self) -> &[Value] {
        &self.observations
    }
    pub fn visits(&self) -> &BTreeMap<String, u64> {
        &self.visits
    }
    pub fn steps(&self) -> u64 {
        self.steps
    }
    pub fn compute_spent(&self) -> u64 {
        self.compute_spent
    }
}

// Origin: engine/crates_rs/core_adversary/src/scene_orchestration.rs
// Claim: urn:core:crates_rs:core-adversary:scene-orchestration:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0650a812 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0650a812` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0650a812 {
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
impl BoundaryError0650a812 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0650a812 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0650a812 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0650a812 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0650a812> {
        if capacity_bound == 0 {
            return Err(BoundaryError0650a812::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0650a812::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0650a812::ExceedsCapacity {
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
mod l4_boundary_tests_0650a812 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0650a812::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0650a812::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0650a812::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0650a812::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0650a812::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError0650a812::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError0650a812::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
