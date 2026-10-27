"""Build, strictly parse, and independently replay Adversary stage run receipts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from governance.contracts import DDCTapeDFA, DDCTapeValidationError
from operations.domain.rop.result import Err, Ok, Refusal, Result

from ..domain import (
    AUTHORITY_EFFECT_NONE,
    AgentResultV1,
    CandidateSelectionProposalV1,
    DdcLetter,
    DdcStepV1,
    ProgressMeasureV1,
    SceneVisitV1,
    SwarmRunReceiptV1,
    SwarmRunStateV1,
    WorkPacketV1,
    canonical_json_bytes,
    strict_json_loads,
    validate_ddc_purity,
)
from ..domain.canonical import (
    digest,
    exact_bool,
    exact_object,
    identifier,
    integer,
    text,
    wire_tuple,
)
from .scheduler import DeterministicSchedulerV1


def _agent_result_from_dict(value: Any) -> AgentResultV1:
    wire = exact_object(
        value,
        frozenset(
            {
                "agent_id",
                "trust_domain",
                "scene_id",
                "work_packet_id",
                "status",
                "candidate_ids",
                "challenge_ids",
                "artifact_refs",
                "residual_codes",
                "causal_parent_ids",
                "authority_effect",
                "schema_version",
                "result_id",
            }
        ),
        "agent result",
    )
    return AgentResultV1(
        agent_id=identifier(wire["agent_id"], "agent_id"),
        trust_domain=identifier(wire["trust_domain"], "trust_domain"),
        scene_id=identifier(wire["scene_id"], "scene_id"),
        work_packet_id=digest(wire["work_packet_id"], "work_packet_id"),
        status=text(wire["status"], "status"),
        candidate_ids=wire_tuple(wire["candidate_ids"], "candidate_ids", digests=True),
        challenge_ids=wire_tuple(wire["challenge_ids"], "challenge_ids", digests=True),
        artifact_refs=wire_tuple(wire["artifact_refs"], "artifact_refs", digests=True),
        residual_codes=wire_tuple(
            wire["residual_codes"], "residual_codes", identifiers=True
        ),
        causal_parent_ids=wire_tuple(
            wire["causal_parent_ids"], "causal_parent_ids", digests=True
        ),
        authority_effect=text(wire["authority_effect"], "authority_effect"),
        schema_version=text(wire["schema_version"], "schema_version"),
        result_id=digest(wire["result_id"], "result_id"),
    )


def _progress_from_dict(value: Any) -> ProgressMeasureV1:
    wire = exact_object(
        value,
        frozenset(
            {
                "changed_state",
                "stronger_certificate",
                "refined_residual",
                "expanded_cover",
                "proposed_lift",
                "authority_effect",
                "schema_version",
                "progressed",
                "measure_id",
            }
        ),
        "progress measure",
    )
    parsed = ProgressMeasureV1(
        changed_state=integer(wire["changed_state"], "changed_state"),
        stronger_certificate=integer(
            wire["stronger_certificate"], "stronger_certificate"
        ),
        refined_residual=integer(wire["refined_residual"], "refined_residual"),
        expanded_cover=integer(wire["expanded_cover"], "expanded_cover"),
        proposed_lift=integer(wire["proposed_lift"], "proposed_lift"),
        authority_effect=text(wire["authority_effect"], "authority_effect"),
        schema_version=text(wire["schema_version"], "schema_version"),
        measure_id=digest(wire["measure_id"], "measure_id"),
    )
    if exact_bool(wire["progressed"], "progressed") != parsed.progressed:
        raise ValueError("caller-authored progress flag differs")
    return parsed


def _state_from_dict(value: Any) -> SwarmRunStateV1:
    wire = exact_object(
        value,
        frozenset(
            {
                "run_key",
                "profile_id",
                "current_scene_id",
                "visit_counts",
                "result_ids",
                "progress_measure_ids",
                "remaining_budget",
                "scene_steps",
                "dry_rounds",
                "terminal_status",
                "authority_effect",
                "schema_version",
                "state_id",
            }
        ),
        "swarm run state",
    )
    if type(wire["visit_counts"]) is not list:
        raise ValueError("visit_counts must be an exact JSON array")
    visits: list[SceneVisitV1] = []
    for item in wire["visit_counts"]:
        visit_wire = exact_object(item, frozenset({"scene_id", "count"}), "scene visit")
        visits.append(
            SceneVisitV1(
                scene_id=identifier(visit_wire["scene_id"], "scene_id"),
                count=integer(visit_wire["count"], "count", minimum=1, maximum=64),
            )
        )
    return SwarmRunStateV1(
        run_key=identifier(wire["run_key"], "run_key"),
        profile_id=digest(wire["profile_id"], "profile_id"),
        current_scene_id=identifier(wire["current_scene_id"], "current_scene_id"),
        visit_counts=tuple(visits),
        result_ids=wire_tuple(
            wire["result_ids"], "result_ids", digests=True, unique=False
        ),
        progress_measure_ids=wire_tuple(
            wire["progress_measure_ids"],
            "progress_measure_ids",
            digests=True,
            unique=False,
        ),
        remaining_budget=integer(wire["remaining_budget"], "remaining_budget"),
        scene_steps=integer(wire["scene_steps"], "scene_steps"),
        dry_rounds=integer(wire["dry_rounds"], "dry_rounds"),
        terminal_status=text(wire["terminal_status"], "terminal_status"),
        authority_effect=text(wire["authority_effect"], "authority_effect"),
        schema_version=text(wire["schema_version"], "schema_version"),
        state_id=digest(wire["state_id"], "state_id"),
    )


def _selection_from_dict(value: Any) -> CandidateSelectionProposalV1:
    wire = exact_object(
        value,
        frozenset(
            {
                "selector_agent_id",
                "evaluator_epoch_id",
                "frontier_candidate_ids",
                "selected_candidate_id",
                "disposition",
                "evidence_refs",
                "nonclaims",
                "authority_effect",
                "schema_version",
                "proposal_id",
            }
        ),
        "candidate selection proposal",
    )
    return CandidateSelectionProposalV1(
        selector_agent_id=identifier(wire["selector_agent_id"], "selector_agent_id"),
        evaluator_epoch_id=digest(wire["evaluator_epoch_id"], "evaluator_epoch_id"),
        frontier_candidate_ids=wire_tuple(
            wire["frontier_candidate_ids"], "frontier_candidate_ids", digests=True
        ),
        selected_candidate_id=digest(
            wire["selected_candidate_id"], "selected_candidate_id", allow_empty=True
        ),
        disposition=text(wire["disposition"], "disposition"),
        evidence_refs=wire_tuple(wire["evidence_refs"], "evidence_refs", digests=True),
        nonclaims=wire_tuple(wire["nonclaims"], "nonclaims"),
        authority_effect=text(wire["authority_effect"], "authority_effect"),
        schema_version=text(wire["schema_version"], "schema_version"),
        proposal_id=digest(wire["proposal_id"], "proposal_id"),
    )


def parse_swarm_run_receipt(raw: bytes) -> Result[SwarmRunReceiptV1, Refusal]:
    try:
        value = strict_json_loads(raw)
        fields = {
            "swarm_definition_id",
            "profile_id",
            "scene_graph_id",
            "initial_work_packet_id",
            "results",
            "progress_measures",
            "causal_result_ids",
            "final_state",
            "selection_proposal",
            "authority_effect",
            "schema_version",
            "receipt_id",
        }
        if isinstance(value, dict) and "terminal_cause" in value:
            fields.add("terminal_cause")
        wire = exact_object(value, frozenset(fields), "swarm run receipt")
        cause = wire.get("terminal_cause", "")
        if "terminal_cause" in wire and cause not in ("halt", "stall"):
            raise ValueError("terminal_cause must be halt or stall")
        if (
            type(wire["results"]) is not list
            or type(wire["progress_measures"]) is not list
        ):
            raise ValueError("receipt result collections must be exact JSON arrays")
        selection = (
            None
            if wire["selection_proposal"] is None
            else _selection_from_dict(wire["selection_proposal"])
        )
        receipt = SwarmRunReceiptV1(
            swarm_definition_id=digest(
                wire["swarm_definition_id"], "swarm_definition_id"
            ),
            profile_id=digest(wire["profile_id"], "profile_id"),
            scene_graph_id=digest(wire["scene_graph_id"], "scene_graph_id"),
            initial_work_packet_id=digest(
                wire["initial_work_packet_id"], "initial_work_packet_id"
            ),
            results=tuple(_agent_result_from_dict(item) for item in wire["results"]),
            progress_measures=tuple(
                _progress_from_dict(item) for item in wire["progress_measures"]
            ),
            causal_result_ids=wire_tuple(
                wire["causal_result_ids"],
                "causal_result_ids",
                digests=True,
                unique=False,
            ),
            final_state=_state_from_dict(wire["final_state"]),
            selection_proposal=selection,
            authority_effect=text(wire["authority_effect"], "authority_effect"),
            schema_version=text(wire["schema_version"], "schema_version"),
            terminal_cause=cause,
            receipt_id=digest(wire["receipt_id"], "receipt_id"),
        )
        if canonical_json_bytes(receipt.to_dict()) != raw:
            raise ValueError("swarm run receipt is not strict canonical JSON")
        return Ok(receipt)
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return Err(
            Refusal(
                code="OEAS_RECEIPT_PARSE_REFUSED",
                message=str(exc),
                locus="oeas-run-receipt",
            )
        )


def build_swarm_run_receipt(
    scheduler: DeterministicSchedulerV1,
    run_key: str,
    packet: WorkPacketV1,
    results: tuple[AgentResultV1, ...],
    progress_measures: tuple[ProgressMeasureV1, ...],
    selection_proposal: CandidateSelectionProposalV1 | None = None,
) -> SwarmRunReceiptV1:
    final_state = scheduler.replay(run_key, packet, results, progress_measures)
    return SwarmRunReceiptV1(
        swarm_definition_id=scheduler.definition.definition_id,
        profile_id=scheduler.profile.profile_id,
        scene_graph_id=scheduler.graph.graph_id,
        initial_work_packet_id=packet.packet_id,
        results=results,
        progress_measures=progress_measures,
        causal_result_ids=tuple(result.result_id for result in results),
        final_state=final_state,
        selection_proposal=selection_proposal,
    )


def verify_swarm_run_receipt(
    receipt: SwarmRunReceiptV1,
    scheduler: DeterministicSchedulerV1,
    run_key: str,
    packet: WorkPacketV1,
) -> Result[SwarmRunReceiptV1, Refusal]:
    try:
        if type(receipt) is not SwarmRunReceiptV1:
            raise TypeError("receipt must be exact SwarmRunReceiptV1")
        if receipt.swarm_definition_id != scheduler.definition.definition_id:
            raise ValueError("receipt definition binding differs")
        if receipt.profile_id != scheduler.profile.profile_id:
            raise ValueError("receipt profile binding differs")
        if receipt.scene_graph_id != scheduler.graph.graph_id:
            raise ValueError("receipt scene graph binding differs")
        if receipt.initial_work_packet_id != packet.packet_id:
            raise ValueError("receipt work packet binding differs")
        for result in receipt.results:
            if result.work_packet_id != packet.packet_id:
                raise ValueError("result work packet binding differs")
        replayed_state = scheduler.replay(
            run_key, packet, receipt.results, receipt.progress_measures
        )
        if receipt.terminal_cause == "halt":
            if replayed_state.terminal_status != "RUNNING":
                raise ValueError("halt applies only while the replay is running")
            replayed_state = replace(
                replayed_state,
                remaining_budget=0,
                terminal_status="EXHAUSTED" if not receipt.results else "COMPLETED",
                state_id="",
            )
        elif receipt.terminal_cause == "stall":
            replayed_state = replace(
                replayed_state,
                terminal_status="HOLD",
                remaining_budget=0,
                state_id="",
            )
        elif receipt.terminal_cause != "":
            raise ValueError("terminal_cause is not closed")
        if replayed_state.to_dict() != receipt.final_state.to_dict():
            raise ValueError("stored final state differs from independent replay")
        return Ok(receipt)
    except (TypeError, ValueError) as exc:
        return Err(
            Refusal(
                code="OEAS_REPLAY_REFUSED",
                message=str(exc),
                locus="oeas-run-replay",
            )
        )


@dataclass(frozen=True)
class DdcTapeAuditReportV1:
    """Independent audit and replay reconstruction of a DDC tape from serialized JSONL records."""

    active_tape: str
    active_steps: tuple[DdcStepV1, ...]
    rolled_back_steps: tuple[dict[str, Any], ...]
    compensation_branches: dict[str, tuple[DdcStepV1, ...]]
    head_sha256: str
    record_count: int
    is_terminalized: bool
    dfa_valid: bool
    authority_effect: str = AUTHORITY_EFFECT_NONE


def audit_and_reconstruct_ddc_tape_from_jsonl(
    path: Path | str,
    *,
    expected_head_sha256: str | None = None,
) -> Result[DdcTapeAuditReportV1, Refusal]:
    """Audit and reconstruct an active DDC tape and refusal-rollback history from serialized JSONL records.

    Enforces:
    1. Pure UTF-8 without BOM.
    2. Strict append-only cryptographic hash chain continuity (sequence monotonicity,
       parent_sha256 pointer matching, record_sha256 canonical integrity).
    3. Strict AuthorityEffect == 'None' on every audit entry.
    4. Exact step purity (validate_ddc_purity).
    5. Clean active tape reconstruction by tracking rollbacks to checkpoint indices.
    6. DDCTapeDFA validation: validate() for terminalized tapes ending in T, or
       validate_prefix() for incomplete runs terminating in HOLD or EXHAUSTED.
    """
    p = Path(path)
    if not p.is_file():
        return Err(
            Refusal(
                code="DDC_AUDIT_FILE_NOT_FOUND",
                message=f"JSONL tape file not found: {p}",
                locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
            )
        )

    try:
        raw_bytes = p.read_bytes()
    except OSError as exc:
        return Err(
            Refusal(
                code="DDC_AUDIT_READ_FAILED",
                message=f"Could not read JSONL tape file: {exc}",
                locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
            )
        )

    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        return Err(
            Refusal(
                code="DDC_AUDIT_BOM_FORBIDDEN",
                message="UTF-8 BOM detected; files must be pure UTF-8 without BOM",
                locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
            )
        )

    lines = [line.strip() for line in raw_bytes.splitlines() if line.strip()]
    if not lines:
        return Err(
            Refusal(
                code="DDC_AUDIT_EMPTY_LOG",
                message="JSONL tape log is empty",
                locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
            )
        )

    prev_hash: str | None = None
    active_steps: list[DdcStepV1] = []
    rolled_back_steps: list[dict[str, Any]] = []
    compensation_branches: dict[str, list[DdcStepV1]] = {}
    is_terminalized = False

    for idx, raw_line in enumerate(lines):
        try:
            record = strict_json_loads(raw_line)
        except (ValueError, UnicodeDecodeError) as exc:
            return Err(
                Refusal(
                    code="DDC_AUDIT_CORRUPTED",
                    message=f"Line {idx} failed JSON decode: {exc}",
                    locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
                )
            )

        if not isinstance(record, dict):
            return Err(
                Refusal(
                    code="DDC_AUDIT_CORRUPTED",
                    message=f"Line {idx} record must be a JSON object",
                    locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
                )
            )

        # 1. Authority effect check
        auth_effect = record.get("authority_effect")
        if auth_effect != AUTHORITY_EFFECT_NONE:
            return Err(
                Refusal(
                    code="DDC_AUDIT_AUTHORITY_LEAK",
                    message=f"Line {idx} authority_effect must be '{AUTHORITY_EFFECT_NONE}', got {auth_effect!r}",
                    locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
                )
            )

        # 2. Sequence check
        seq = record.get("sequence")
        if type(seq) is not int or seq != idx:
            return Err(
                Refusal(
                    code="DDC_AUDIT_SEQUENCE_MISMATCH",
                    message=f"Line {idx} sequence mismatch: expected {idx}, got {seq}",
                    locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
                )
            )

        # 3. Parent hash pointer check
        parent = record.get("parent_sha256")
        if idx == 0:
            if parent is not None:
                return Err(
                    Refusal(
                        code="DDC_AUDIT_PARENT_HASH_MISMATCH",
                        message=f"Line 0 parent_sha256 must be None, got {parent!r}",
                        locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
                    )
                )
        else:
            if parent != prev_hash:
                return Err(
                    Refusal(
                        code="DDC_AUDIT_PARENT_HASH_MISMATCH",
                        message=f"Line {idx} parent_sha256 mismatch: expected {prev_hash}, got {parent}",
                        locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
                    )
                )

        # 4. Record digest recomputation
        record_digest = record.get("record_sha256")
        try:
            material = canonical_json_bytes({
                k: v for k, v in record.items() if k != "record_sha256"
            })
        except (TypeError, ValueError) as exc:
            return Err(Refusal(
                code="DDC_AUDIT_CORRUPTED",
                message=f"Line {idx} has invalid canonical data: {exc}",
                locus="adversary.stage.application.replay",
            ))
        recomputed_digest = hashlib.sha256(material).hexdigest()
        if record_digest != recomputed_digest:
            return Err(
                Refusal(
                    code="DDC_AUDIT_RECORD_HASH_MISMATCH",
                    message=f"Line {idx} record_sha256 mismatch: expected {recomputed_digest}, got {record_digest}",
                    locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
                )
            )

        prev_hash = record_digest

        # 5. Record type handling
        rec_type = record.get("record_type", "step")
        if rec_type == "step":
            try:
                step = DdcStepV1.from_dict(record)
            except Exception as exc:
                return Err(
                    Refusal(
                        code="DDC_AUDIT_STEP_DESERIALIZATION_FAILED",
                        message=f"Line {idx} step deserialization failed: {exc}",
                        locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
                    )
                )
            purity = validate_ddc_purity(step)
            if purity.is_err:
                return Err(
                    Refusal(
                        code="DDC_AUDIT_PURITY_VIOLATION",
                        message=f"Line {idx} impure DDC step: {purity.unwrap_err().message}",
                        locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
                    )
                )
            active_steps.append(step)
            if step.letter == DdcLetter.T:
                is_terminalized = True

        elif rec_type == "rollback":
            target_idx = record.get("checkpoint_index")
            if (
                target_idx is None
                or type(target_idx) is not int
                or target_idx < 0
                or target_idx > len(active_steps)
            ):
                return Err(
                    Refusal(
                        code="DDC_AUDIT_INVALID_CHECKPOINT",
                        message=f"Line {idx} rollback target {target_idx} is out of bounds [0, {len(active_steps)}]",
                        locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
                    )
                )
            rolled = active_steps[target_idx:]
            active_steps = active_steps[:target_idx]
            for s in rolled:
                rolled_back_steps.append({
                    "step": s,
                    "reason": record.get("reason", ""),
                    "rolled_back_from_index": target_idx,
                    "authority_effect": AUTHORITY_EFFECT_NONE,
                })
            is_terminalized = any(s.letter == DdcLetter.T for s in active_steps)

        elif rec_type == "compensation_branch":
            try:
                b_id = identifier(record["branch_id"], "branch_id")
                if b_id in compensation_branches:
                    raise ValueError("duplicate compensation branch_id")
                raw_branch_steps = record["steps"]
                if type(raw_branch_steps) is not list:
                    raise ValueError("compensation steps must be an array")
                branch_steps = []
                for s_item in raw_branch_steps:
                    if type(s_item) is not dict or s_item.get("authority_effect") != AUTHORITY_EFFECT_NONE:
                        raise ValueError("compensation step must explicitly declare AuthorityEffect None")
                    s_parsed = DdcStepV1.from_dict(s_item)
                    purity = validate_ddc_purity(s_parsed)
                    if purity.is_err:
                        return Err(purity.unwrap_err())
                    branch_steps.append(s_parsed)
            except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
                return Err(Refusal(
                    code="DDC_AUDIT_COMPENSATION_INVALID",
                    message=f"Line {idx} has invalid compensation data: {exc}",
                    locus="adversary.stage.application.replay",
                ))
            compensation_branches[b_id] = branch_steps

        else:
            return Err(
                Refusal(
                    code="DDC_AUDIT_UNKNOWN_RECORD_TYPE",
                    message=f"Line {idx} unrecognized record_type: {rec_type!r}",
                    locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
                )
            )

    # 6. Verify head digest against expectation if provided
    if expected_head_sha256 is not None and prev_hash != expected_head_sha256:
        return Err(
            Refusal(
                code="DDC_AUDIT_HEAD_HASH_MISMATCH",
                message=f"Log head hash mismatch: expected {expected_head_sha256}, got {prev_hash}",
                locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
            )
        )

    # 7. Reconstruct active tape and validate against DFA
    active_tape = " · ".join(s.letter.value for s in active_steps) if active_steps else ""
    try:
        if is_terminalized:
            DDCTapeDFA.validate(active_tape, dialect=DDCTapeDFA.LEGACY_V1)
        else:
            # Runs terminating in HOLD or EXHAUSTED do not end in terminal rune T; validate prefix
            if active_tape:
                DDCTapeDFA.validate_prefix(active_tape, dialect=DDCTapeDFA.LEGACY_V1)
    except DDCTapeValidationError as exc:
        return Err(
            Refusal(
                code="DDC_AUDIT_DFA_VIOLATION",
                message=f"Reconstructed active tape '{active_tape}' violates DDCTapeDFA: {exc}",
                locus="adversary.stage.application.replay.audit_and_reconstruct_ddc_tape_from_jsonl",
            )
        )

    return Ok(
        DdcTapeAuditReportV1(
            active_tape=active_tape,
            active_steps=tuple(active_steps),
            rolled_back_steps=tuple(rolled_back_steps),
            compensation_branches={k: tuple(v) for k, v in compensation_branches.items()},
            head_sha256=prev_hash or "",
            record_count=len(lines),
            is_terminalized=is_terminalized,
            dfa_valid=True,
            authority_effect=AUTHORITY_EFFECT_NONE,
        )
    )


__all__ = [
    "DdcTapeAuditReportV1",
    "audit_and_reconstruct_ddc_tape_from_jsonl",
    "build_swarm_run_receipt",
    "parse_swarm_run_receipt",
    "verify_swarm_run_receipt",
]
