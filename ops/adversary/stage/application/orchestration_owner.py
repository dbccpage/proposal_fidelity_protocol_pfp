"""Advance the stage application path delegated by ``run_swarm``.

``run_swarm`` starts a circuit and delegates its advancement loop to
``advance_owned_run``. Stage hosts and teamwork do not own this delegated
loop. ``ArtifactRuntime.workflow`` takes the same ``advance_bout`` step.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import replace

from operations.domain.rop.result import Err, Ok, Refusal, Result

from ..domain import (
    AUTHORITY_EFFECT_NONE,
    AgentResultV1,
    CandidateProposalV1,
    DdaLetter,
    DdcLetter,
    ProgressMeasureV1,
    SwarmDefinitionV1,
    SwarmProfileV1,
    SwarmRunReceiptV1,
    ValuationReceiptV1,
    WorkPacketV1,
    canonical_json_bytes,
)
from .emission import build_intelligence_event, emit_event
from .ports import ContinueDecisionKindV1
from .run_swarm import SwarmRuntimeV1
from .scheduler import advance_bout

OWNER_ID = "adversary.stage.application.orchestration_owner"


def advance_owned_run(
    *,
    defn: SwarmDefinitionV1,
    profile: SwarmProfileV1,
    rt: SwarmRuntimeV1,
    initial_packet: WorkPacketV1,
    run_key: str,
    host_request: bytes | None,
    current_state,
) -> Result[SwarmRunReceiptV1, Refusal]:
    """Advance one swarm until it leaves RUNNING and return that run's receipt."""
    from .run_swarm import _scene_operation_ids, dispatch_host_request

    results: list[AgentResultV1] = []
    progress_measures: list[ProgressMeasureV1] = []
    terminal_cause = ""

    while current_state.terminal_status == "RUNNING":
        if rt.cont is None:
            return Err(
                Refusal(
                    code="OEAS_CONTINUATION_MISSING",
                    message="Continuation port required to advance circuit",
                    locus="adversary.stage.application.run_swarm",
                )
            )
        cont_decision_res = rt.cont.can_continue(current_state)
        if cont_decision_res.is_err:
            return Err(cont_decision_res.unwrap_err())
        if cont_decision_res.unwrap().kind == ContinueDecisionKindV1.HALT:
            current_state = replace(
                current_state,
                remaining_budget=0,
                terminal_status="COMPLETED" if results else "EXHAUSTED",
                state_id="",
            )
            terminal_cause = "halt"
            break

        host_result = dispatch_host_request(
            rt,
            _scene_operation_ids(rt, current_state.current_scene_id),
            host_request,
        )
        if host_result.is_err:
            return Err(host_result.unwrap_err())
        host_reply = host_result.unwrap()

        context_bytes = canonical_json_bytes(
            {"state_id": current_state.state_id, "circuit": current_state.circuit_count}
        )
        if rt.model is None:
            return Err(
                Refusal(
                    code="OEAS_MODEL_MISSING",
                    message="Model port required for proposal generation",
                    locus="adversary.stage.application.run_swarm",
                )
            )
        proposal_res = rt.model.propose(initial_packet, context_bytes)
        if proposal_res.is_err:
            return Err(proposal_res.unwrap_err())
        proposal = proposal_res.unwrap()
        if type(proposal) is not CandidateProposalV1:
            return Err(
                Refusal(
                    code="PROPOSAL_TYPE_MISMATCH",
                    message="Model must return an exact CandidateProposalV1",
                    locus="adversary.stage.application.run_swarm",
                )
            )
        if proposal.work_packet_id != initial_packet.packet_id:
            return Err(
                Refusal(
                    code="PROPOSAL_WORK_PACKET_BINDING_MISMATCH",
                    message="Proposal names a different work packet than the model received",
                    locus="adversary.stage.application.run_swarm",
                )
            )
        dda_step = proposal.proposed_dda_step
        if dda_step is None:
            return Err(
                Refusal(
                    code="DDA_STEP_REQUIRED",
                    message="A state-changing OEAS circuit requires a producer-supplied DDA step",
                    locus="adversary.stage.application.run_swarm",
                )
            )

        if rt.valuator is None or rt.epoch is None:
            return Err(
                Refusal(
                    code="OEAS_VALUATOR_MISSING",
                    message="Valuator port and epoch required for evaluation",
                    locus="adversary.stage.application.run_swarm",
                )
            )
        val_res = rt.valuator.evaluate(rt.epoch, proposal)
        if val_res.is_err:
            return Err(val_res.unwrap_err())
        val_receipt = val_res.unwrap()

        # An internally consistent receipt is not evidence about this proposal
        # until its complete frozen coordinate binding has been checked. Keep
        # these guards before deriving progress/results or advancing/emitting.
        if type(val_receipt) is not ValuationReceiptV1:
            return Err(
                Refusal(
                    code="VALUATION_RECEIPT_TYPE_MISMATCH",
                    message="Valuator must return an exact ValuationReceiptV1",
                    locus="adversary.stage.application.run_swarm",
                )
            )
        if val_receipt.candidate_id != proposal.candidate_id:
            return Err(
                Refusal(
                    code="VALUATION_CANDIDATE_BINDING_MISMATCH",
                    message="Valuation receipt names a different candidate",
                    locus="adversary.stage.application.run_swarm",
                )
            )
        if val_receipt.evaluator_epoch_id != rt.epoch.epoch_id:
            return Err(
                Refusal(
                    code="VALUATION_EPOCH_BINDING_MISMATCH",
                    message="Valuation receipt names a different frozen evaluator epoch",
                    locus="adversary.stage.application.run_swarm",
                )
            )
        if val_receipt.probe_ids != rt.epoch.probe_ids:
            return Err(
                Refusal(
                    code="VALUATION_PROBES_BINDING_MISMATCH",
                    message="Valuation probes differ from the frozen ordered coordinates",
                    locus="adversary.stage.application.run_swarm",
                )
            )
        if val_receipt.weights != rt.epoch.weights:
            return Err(
                Refusal(
                    code="VALUATION_WEIGHTS_BINDING_MISMATCH",
                    message="Valuation weights differ from the frozen ordered weights",
                    locus="adversary.stage.application.run_swarm",
                )
            )

        # Residual arithmetic carries no witness of a stronger certificate.
        # In particular, an unchanged valuation must not reset the dry-round cap.
        progress = ProgressMeasureV1(
            changed_state=1 if val_receipt.delta_phi < 0 else 0,
            stronger_certificate=0,
            refined_residual=1 if val_receipt.post_residual != val_receipt.pre_residual else 0,
        )
        assigned_seat_domain = "PRODUCER"
        sched_plan = getattr(rt.scheduler, "plan", None)
        if sched_plan is not None and defn is not None:
            assignment = next(
                (a for a in sched_plan.assignments if a.scene_id == current_state.current_scene_id),
                None,
            )
            if assignment:
                seat = next(
                    (s for s in defn.seat_requirements if s.seat_id == assignment.seat_id),
                    None,
                )
                if seat:
                    assigned_seat_domain = seat.trust_domain

        if dda_step.letter in (DdaLetter.M, DdcLetter.M):
            result_status = "REFUSE"
        elif val_receipt.disposition == "NON_INCREASING":
            result_status = "PASS"
        else:
            result_status = "HOLD"

        is_stalled = False
        if rt.oscillation_detector is not None and result_status != "REFUSE":
            is_stalled, _ = rt.oscillation_detector.record_and_evaluate(
                current_state.current_scene_id, proposal, progressed=progress.progressed
            )
            if is_stalled:
                result_status = "HOLD"

        agent_result = AgentResultV1(
            agent_id=proposal.producer_agent_id,
            trust_domain=assigned_seat_domain,
            scene_id=current_state.current_scene_id,
            work_packet_id=initial_packet.packet_id,
            status=result_status,
            candidate_ids=(proposal.candidate_id,),
            artifact_refs=proposal.artifact_refs,
        )

        adv_res = advance_bout(rt.scheduler, current_state, agent_result, progress)
        if adv_res.is_err:
            return Err(adv_res.unwrap_err())
        next_state = adv_res.unwrap()

        if is_stalled:
            next_state = replace(
                next_state,
                terminal_status="HOLD",
                remaining_budget=0,
                state_id="",
            )
            terminal_cause = "stall"

        dda_event, dda_payload = build_intelligence_event(
            ie_id=f"ie_{run_key}_{next_state.circuit_count}",
            actor_id=proposal.producer_agent_id,
            actor_kind="SWARM_AGENT",
            event_kind="DDA",
            source_system="adversary.stage",
            session_id=run_key,
            payload={
                "dda_step": dda_step.to_dict(),
                "valuation_receipt_id": val_receipt.receipt_id,
            },
        )
        dda_emit_res = emit_event(dda_event, dda_payload, rt.emitters, dda_step=dda_step)
        if dda_emit_res.is_err:
            return Err(dda_emit_res.unwrap_err())

        if result_status == "REFUSE" and rt.rollback_on_refusal:
            ddc_sink = getattr(rt.emitters, "ddc", None) or getattr(rt.emitters, "dda", None)
            if ddc_sink is not None and hasattr(ddc_sink, "rollback"):
                ddc_sink.rollback(
                    checkpoint_index=max(0, len(ddc_sink.recorded_steps) - 1),
                    reason=f"Critic refusal in scene {current_state.current_scene_id}: backward scene redirection",
                )

        if is_stalled:
            narrative_payload = (
                f"Circuit {next_state.circuit_count}: SWARM_STALL_DETECTED in scene "
                f"'{current_state.current_scene_id}'. Token distance {rt.oscillation_detector.last_distance:.3f} "
                f"< {rt.oscillation_detector.stall_distance_threshold}. Early HOLD circuit-breaker tripped."
            )
        else:
            narrative_payload = (
                f"Circuit {next_state.circuit_count}: evaluated proposal "
                f"{proposal.candidate_id[:16]} with delta phi {val_receipt.delta_phi}."
            )
        if host_reply is not None:
            narrative_payload = f"{narrative_payload} Host reply {host_reply.hex()}."

        narrative_event, narrative_payload_dict = build_intelligence_event(
            ie_id=f"ie_narrative_{run_key}_{next_state.circuit_count}",
            actor_id=proposal.producer_agent_id,
            actor_kind="SWARM_AGENT",
            event_kind="NARRATIVE",
            source_system="adversary.stage",
            session_id=run_key,
            payload=narrative_payload,
        )
        narrative_emit_res = emit_event(narrative_event, narrative_payload_dict, rt.emitters)
        if narrative_emit_res.is_err:
            return Err(narrative_emit_res.unwrap_err())

        current_state = next_state
        results.append(agent_result)
        progress_measures.append(progress)

    return Ok(
        SwarmRunReceiptV1(
            swarm_definition_id=defn.definition_id,
            profile_id=profile.profile_id,
            scene_graph_id=profile.scene_graph_id,
            initial_work_packet_id=initial_packet.packet_id,
            results=tuple(results),
            progress_measures=tuple(progress_measures),
            causal_result_ids=tuple(result.result_id for result in results),
            final_state=current_state,
            authority_effect=AUTHORITY_EFFECT_NONE,
            terminal_cause=terminal_cause,
        )
    )
