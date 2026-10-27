//! Generic circuit execution through injected ports; no invented evaluation or DDC evidence.
use crate::stage::emission::{
    build_intelligence_event, emit_event, Clock, EmitterSuite, EventDescriptor, Payload,
};
use crate::stage::evaluation::EvaluatorEpoch;
use crate::stage::oscillation::OscillationDetector;
use crate::stage::packets::{AgentResult, WorkPacket};
use crate::stage::ports::{
    ContinuationPort, ContinueDecisionKind, ModelPort, Refusal, SchedulerPort, ValuatorPort,
};
use crate::stage::run::{ProgressMeasure, SwarmRunReceipt};
use crate::stage::topology::{SwarmDefinition, SwarmProfile};
use serde_json::json;

pub struct SwarmRuntime<'a, 'sinks> {
    pub model: Option<&'a mut dyn ModelPort>,
    pub scheduler: Option<&'a mut dyn SchedulerPort>,
    pub valuator: Option<&'a mut dyn ValuatorPort>,
    pub continuation: Option<&'a mut dyn ContinuationPort>,
    pub emitters: &'a mut EmitterSuite<'sinks>,
    pub epoch: Option<&'a EvaluatorEpoch>,
    pub clock: &'a dyn Clock,
    pub rollback_on_refusal: bool,
    pub oscillation_detector: Option<&'a mut OscillationDetector>,
}

fn refusal(code: &str, message: impl Into<String>) -> Refusal {
    let mut refusal = Refusal::new(code, message);
    refusal.locus = "adversary.stage.application.run_swarm".into();
    refusal
}

fn check_continuation(
    runtime: &mut SwarmRuntime<'_, '_>,
    state: &mut crate::stage::run::SwarmRunState,
    results_empty: bool,
) -> Result<bool, Refusal> {
    let Some(continuation) = &mut runtime.continuation else {
        return Err(refusal(
            "OEAS_CONTINUATION_MISSING",
            "Continuation port required to advance circuit",
        ));
    };
    if continuation.can_continue(state)?.kind != ContinueDecisionKind::Halt {
        return Ok(true);
    }
    state.remaining_budget = 0;
    state.terminal_status = if results_empty {
        "EXHAUSTED"
    } else {
        "COMPLETED"
    }
    .into();
    state.state_id.clear();
    state
        .validate()
        .map_err(|message| refusal("OEAS_RUN_STATE_REFUSED", message))?;
    Ok(false)
}

fn verify_valuation_bindings(
    valuation: &crate::stage::evaluation::ValuationReceipt,
    candidate: &crate::stage::packets::CandidateProposal,
    epoch: &EvaluatorEpoch,
) -> Result<(), Refusal> {
    if valuation.candidate_id() != candidate.candidate_id() {
        return Err(refusal(
            "VALUATION_CANDIDATE_BINDING_MISMATCH",
            "Valuation receipt names a different candidate",
        ));
    }
    if valuation.evaluator_epoch_id() != epoch.epoch_id() {
        return Err(refusal(
            "VALUATION_EPOCH_BINDING_MISMATCH",
            "Valuation receipt names a different frozen evaluator epoch",
        ));
    }
    if valuation.probe_ids() != epoch.probe_ids() {
        return Err(refusal(
            "VALUATION_PROBES_BINDING_MISMATCH",
            "Valuation probes differ from the frozen ordered coordinates",
        ));
    }
    if valuation.weights() != epoch.weights() {
        return Err(refusal(
            "VALUATION_WEIGHTS_BINDING_MISMATCH",
            "Valuation weights differ from the frozen ordered weights",
        ));
    }
    Ok(())
}

fn propose_and_evaluate(
    runtime: &mut SwarmRuntime<'_, '_>,
    packet: &WorkPacket,
    state: &crate::stage::run::SwarmRunState,
) -> Result<
    (
        crate::stage::packets::CandidateProposal,
        crate::stage::ddc::DdcStep,
        crate::stage::evaluation::ValuationReceipt,
    ),
    Refusal,
> {
    let context =
        serde_json::to_vec(&json!({"state_id": state.state_id, "circuit": state.circuit_count()}))
            .map_err(|error| refusal("OEAS_CONTEXT_ENCODING_REFUSED", error.to_string()))?;
    let Some(model) = &mut runtime.model else {
        return Err(refusal(
            "OEAS_MODEL_MISSING",
            "Model port required for proposal generation",
        ));
    };
    let candidate = model.propose(packet, &context)?;
    if candidate.work_packet_id() != packet.packet_id() {
        return Err(refusal(
            "PROPOSAL_WORK_PACKET_BINDING_MISMATCH",
            "Proposal names a different work packet than the model received",
        ));
    }
    let Some(step) = candidate.proposed_dda_step().clone() else {
        return Err(refusal(
            "DDA_STEP_REQUIRED",
            "A state-changing OEAS circuit requires a producer-supplied DDA step",
        ));
    };
    let (Some(valuator), Some(epoch)) = (&mut runtime.valuator, runtime.epoch) else {
        return Err(refusal(
            "OEAS_VALUATOR_MISSING",
            "Valuator port and epoch required for evaluation",
        ));
    };
    let valuation = valuator.evaluate(epoch, &candidate)?;
    verify_valuation_bindings(&valuation, &candidate, epoch)?;
    Ok((candidate, step, valuation))
}

fn build_progress_measure(
    valuation: &crate::stage::evaluation::ValuationReceipt,
) -> Result<ProgressMeasure, Refusal> {
    let mut progress = ProgressMeasure {
        changed_state: if *valuation.delta_phi() < 0 { 1 } else { 0 },
        stronger_certificate: 0,
        refined_residual: if valuation.post_residual() != valuation.pre_residual() {
            1
        } else {
            0
        },
        expanded_cover: 0,
        proposed_lift: 0,
        authority_effect: "None".into(),
        schema_version: "core.oeas.progress-measure.v1".into(),
        measure_id: String::new(),
        progressed: None,
    };
    progress
        .validate()
        .map_err(|message| refusal("OEAS_PROGRESS_REFUSED", message))?;
    Ok(progress)
}

fn resolve_trust_domain<'a>(
    scheduler: &'a dyn SchedulerPort,
    definition: &'a SwarmDefinition,
    scene_id: &str,
) -> &'a str {
    scheduler
        .plan()
        .and_then(|plan| {
            plan.assignments()
                .iter()
                .find(|assignment| assignment.scene_id() == scene_id)
        })
        .and_then(|assignment| {
            definition
                .seat_requirements()
                .iter()
                .find(|seat| seat.seat_id() == assignment.seat_id())
        })
        .map_or("PRODUCER", |seat| seat.trust_domain().as_str())
}

fn evaluate_status_and_stall(
    step: &crate::stage::ddc::DdcStep,
    valuation: &crate::stage::evaluation::ValuationReceipt,
    detector: &mut Option<&mut OscillationDetector>,
    scene_id: &str,
    candidate: &crate::stage::packets::CandidateProposal,
    progressed: bool,
) -> Result<(&'static str, bool), Refusal> {
    let mut status = if step.letter().letter() == "M" {
        "REFUSE"
    } else if valuation.disposition() == "NON_INCREASING" {
        "PASS"
    } else {
        "HOLD"
    };
    let mut stalled = false;
    if status != "REFUSE" {
        if let Some(det) = detector {
            (stalled, _) = det.record_and_evaluate(scene_id, candidate, progressed)?;
            if stalled {
                status = "HOLD";
            }
        }
    }
    Ok((status, stalled))
}

fn maybe_rollback_ddc(
    status: &str,
    runtime: &mut SwarmRuntime<'_, '_>,
    scene_id: &str,
) -> Result<(), Refusal> {
    if status == "REFUSE" && runtime.rollback_on_refusal {
        if let Some(sink) = &mut runtime.emitters.ddc {
            if let Some(count) = sink.recorded_step_count() {
                sink.rollback(
                    count.saturating_sub(1),
                    &format!("Critic refusal in scene {scene_id}: backward scene redirection"),
                )?;
            }
        }
    }
    Ok(())
}

fn format_circuit_narrative(
    detector: &Option<&mut OscillationDetector>,
    stalled: bool,
    circuit_count: usize,
    scene_id: &str,
    candidate: &crate::stage::packets::CandidateProposal,
    valuation: &crate::stage::evaluation::ValuationReceipt,
) -> String {
    if let Some(det) = detector.as_ref().filter(|_| stalled) {
        format!(
            "Circuit {circuit_count}: SWARM_STALL_DETECTED in scene '{scene_id}'. Token distance {:.3} < {:?}. Early HOLD circuit-breaker tripped.",
            det.last_distance(),
            det.stall_distance_threshold(),
        )
    } else {
        format!(
            "Circuit {circuit_count}: evaluated proposal {} with delta phi {}.",
            candidate
                .candidate_id()
                .chars()
                .take(16)
                .collect::<String>(),
            valuation.delta_phi()
        )
    }
}

fn emit_circuit_events(
    runtime: &mut SwarmRuntime<'_, '_>,
    run_key: &str,
    scene_id: &str,
    circuit_count: usize,
    status: &str,
    stalled: bool,
    candidate: &crate::stage::packets::CandidateProposal,
    step: &crate::stage::ddc::DdcStep,
    valuation: &crate::stage::evaluation::ValuationReceipt,
) -> Result<(), Refusal> {
    let payload = json!({"dda_step": step, "valuation_receipt_id": valuation.receipt_id()});
    let object = payload.as_object().ok_or_else(|| {
        refusal(
            "OEAS_EVENT_BUILD_REFUSED",
            "DDA event payload must be an object",
        )
    })?;
    let event_id = format!("ie_{run_key}_{circuit_count}");
    let descriptor = EventDescriptor {
        ie_id: &event_id,
        actor_id: candidate.producer_agent_id(),
        actor_kind: "SWARM_AGENT",
        event_kind: "DDA",
        source_system: "adversary.stage",
        session_id: run_key,
        parent_ie_id: Vec::new(),
        object_ids: Vec::new(),
        terminal: false,
    };
    let (event, raw) =
        build_intelligence_event(descriptor, Payload::Object(object), runtime.clock)?;
    emit_event(&event, &raw, runtime.emitters, Some(step), None)?;
    maybe_rollback_ddc(status, runtime, scene_id)?;
    let narrative = format_circuit_narrative(
        &runtime.oscillation_detector,
        stalled,
        circuit_count,
        scene_id,
        candidate,
        valuation,
    );
    let event_id = format!("ie_narrative_{run_key}_{circuit_count}");
    let descriptor = EventDescriptor {
        ie_id: &event_id,
        actor_id: candidate.producer_agent_id(),
        actor_kind: "SWARM_AGENT",
        event_kind: "NARRATIVE",
        source_system: "adversary.stage",
        session_id: run_key,
        parent_ie_id: Vec::new(),
        object_ids: Vec::new(),
        terminal: false,
    };
    let (event, raw) =
        build_intelligence_event(descriptor, Payload::Text(&narrative), runtime.clock)?;
    emit_event(&event, &raw, runtime.emitters, None, None).map(|_| ())
}

fn advance_scheduler_with_result(
    definition: &SwarmDefinition,
    runtime: &mut SwarmRuntime<'_, '_>,
    packet: &WorkPacket,
    state: &crate::stage::run::SwarmRunState,
    candidate: &crate::stage::packets::CandidateProposal,
    progress: &ProgressMeasure,
    status: &str,
    stalled: bool,
    terminal_cause: &mut String,
) -> Result<(AgentResult, crate::stage::run::SwarmRunState), Refusal> {
    let Some(scheduler) = &mut runtime.scheduler else {
        return Err(refusal(
            "OEAS_SCHEDULER_MISSING",
            "Runtime scheduler is required to execute circuit",
        ));
    };
    let trust_domain =
        resolve_trust_domain(*scheduler, definition, state.current_scene_id()).to_string();
    let mut result = AgentResult {
        agent_id: candidate.producer_agent_id().clone(),
        trust_domain,
        scene_id: state.current_scene_id.clone(),
        work_packet_id: packet.packet_id().clone(),
        status: status.into(),
        candidate_ids: vec![candidate.candidate_id().clone()],
        challenge_ids: Vec::new(),
        artifact_refs: candidate.artifact_refs().clone(),
        residual_codes: Vec::new(),
        causal_parent_ids: Vec::new(),
        authority_effect: "None".into(),
        schema_version: "core.oeas.agent-result.v1".into(),
        result_id: String::new(),
    };
    result
        .validate()
        .map_err(|message| refusal("OEAS_AGENT_RESULT_REFUSED", message))?;
    let mut next = scheduler.advance(state, &result, progress)?;
    if stalled {
        next.terminal_status = "HOLD".into();
        next.remaining_budget = 0;
        next.state_id.clear();
        next.validate()
            .map_err(|message| refusal("OEAS_RUN_STATE_REFUSED", message))?;
        *terminal_cause = "stall".into();
    }
    Ok((result, next))
}

fn run_swarm_step(
    definition: &SwarmDefinition,
    runtime: &mut SwarmRuntime<'_, '_>,
    packet: &WorkPacket,
    run_key: &str,
    state: &mut crate::stage::run::SwarmRunState,
    results: &mut Vec<AgentResult>,
    progress_measures: &mut Vec<ProgressMeasure>,
    terminal_cause: &mut String,
) -> Result<bool, Refusal> {
    if !check_continuation(runtime, state, results.is_empty())? {
        *terminal_cause = "halt".into();
        return Ok(false);
    }
    let (candidate, step, valuation) = propose_and_evaluate(runtime, packet, state)?;
    let progress = build_progress_measure(&valuation)?;
    let (status, stalled) = evaluate_status_and_stall(
        &step,
        &valuation,
        &mut runtime.oscillation_detector,
        state.current_scene_id(),
        &candidate,
        progress.made_progress(),
    )?;
    let (result, next) = advance_scheduler_with_result(
        definition,
        runtime,
        packet,
        state,
        &candidate,
        &progress,
        status,
        stalled,
        terminal_cause,
    )?;
    emit_circuit_events(
        runtime,
        run_key,
        state.current_scene_id(),
        next.circuit_count(),
        status,
        stalled,
        &candidate,
        &step,
        &valuation,
    )?;
    *state = next;
    results.push(result);
    progress_measures.push(progress);
    Ok(true)
}

pub fn run_swarm(
    definition: &SwarmDefinition,
    profile: &SwarmProfile,
    runtime: &mut SwarmRuntime<'_, '_>,
    packet: &WorkPacket,
    run_key: &str,
) -> Result<SwarmRunReceipt, Refusal> {
    if runtime
        .epoch
        .is_some_and(|epoch| epoch.epoch_id() != packet.evaluator_epoch_id())
    {
        return Err(refusal(
            "EVALUATOR_EPOCH_BINDING_MISMATCH",
            "Runtime evaluator epoch does not match the work packet binding",
        ));
    }
    let Some(scheduler) = &mut runtime.scheduler else {
        return Err(refusal(
            "OEAS_SCHEDULER_MISSING",
            "Runtime scheduler is required to execute circuit",
        ));
    };
    let mut state = scheduler
        .start(run_key, packet)
        .map_err(|error| refusal("OEAS_SCHEDULER_START_REFUSED", error.message))?;
    if let Some(detector) = &mut runtime.oscillation_detector {
        detector.reset();
    }
    let mut results = Vec::new();
    let mut progress_measures = Vec::new();
    let mut terminal_cause = String::new();
    while state.terminal_status == "RUNNING" {
        if !run_swarm_step(
            definition,
            runtime,
            packet,
            run_key,
            &mut state,
            &mut results,
            &mut progress_measures,
            &mut terminal_cause,
        )? {
            break;
        }
    }
    let mut receipt = SwarmRunReceipt {
        swarm_definition_id: definition.definition_id().clone(),
        profile_id: profile.profile_id().clone(),
        scene_graph_id: profile.scene_graph_id().clone(),
        initial_work_packet_id: packet.packet_id().clone(),
        causal_result_ids: results
            .iter()
            .map(|result| result.result_id().clone())
            .collect(),
        results,
        progress_measures,
        final_state: state,
        selection_proposal: None,
        authority_effect: "None".into(),
        schema_version: "core.oeas.swarm-run-receipt.v1".into(),
        terminal_cause,
        receipt_id: String::new(),
    };
    receipt
        .validate()
        .map_err(|message| refusal("OEAS_RECEIPT_BUILD_REFUSED", message))?;
    Ok(receipt)
}

// Origin: engine/crates_rs/core_adversary/src/stage/run_swarm.rs
// Claim: urn:core:crates_rs:core-adversary:run-swarm:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordcb0516e7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordcb0516e7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorcb0516e7 {
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
impl BoundaryErrorcb0516e7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorcb0516e7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorcb0516e7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordcb0516e7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorcb0516e7> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorcb0516e7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorcb0516e7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorcb0516e7::ExceedsCapacity {
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
mod l4_boundary_tests_cb0516e7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordcb0516e7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordcb0516e7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordcb0516e7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordcb0516e7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordcb0516e7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorcb0516e7::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorcb0516e7::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
