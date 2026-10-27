"""Prompt Artifact command handlers for Symbol Game CLI presentation layer.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pfp.domain import (
    DEFAULT_REQUIRED_REPLY_FIELDS,
    DemandItemV1,
    ObjectiveTypedV1,
    ObstructionHintV1,
    PromptArtifactV1,
    RegimeKind,
    ResidualColour,
    build_llm_turn_envelope,
    build_payload_from_prompt_artifact,
    compile_prompt_artifact,
    render_prompt_body,
)
from pfp.infrastructure.serialization import (
    write_content_addressed_json,
)
from .io_utils import _parse_csv, _read_json, _write_json


def cmd_compile_prompt(args: argparse.Namespace) -> int:
    regime_bytes = args.regime_bytes.read_bytes()
    prompt_body_bytes = args.prompt_body_bytes.read_bytes() if args.prompt_body_bytes else None

    if args.objective_json:
        obj_data = _read_json(args.objective_json)
        objective_typed = ObjectiveTypedV1.from_dict(obj_data)
    else:
        target_obs = _parse_csv(args.target_obstruction_ids)
        target_dem = _parse_csv(args.target_demand_ids)
        objective_typed = ObjectiveTypedV1(
            kind=args.objective_kind,
            summary=args.objective_summary,
            target_obstruction_ids=target_obs,
            target_demand_ids=target_dem,
        )

    open_obstructions = ()
    if args.obstructions_json:
        obs_raw = _read_json(args.obstructions_json)
        open_obstructions = tuple(ObstructionHintV1.from_dict(x) for x in obs_raw)

    demand_set = ()
    if args.demands_json:
        dem_raw = _read_json(args.demands_json)
        demand_set = tuple(DemandItemV1.from_dict(x) for x in dem_raw)

    admitted_constructors = _parse_csv(args.admitted_constructors)
    kill_conditions = _parse_csv(args.kill_conditions)
    required_reply_fields = _parse_csv(args.required_reply_fields)
    if not required_reply_fields:
        required_reply_fields = tuple(sorted(set(DEFAULT_REQUIRED_REPLY_FIELDS)))

    dual_witness_required = (
        (args.dual_witness_required == "true")
        if args.dual_witness_required is not None
        else (args.residual_colour == "Exact")
    )

    if prompt_body_bytes is None:
        prompt_body_bytes = render_prompt_body(
            regime_bytes,
            objective_typed=objective_typed,
            admitted_constructors=admitted_constructors,
            open_obstructions=open_obstructions,
            demand_set=demand_set,
            kill_conditions=kill_conditions,
            required_reply_fields=required_reply_fields,
        )

    artifact = compile_prompt_artifact(
        regime_kind=args.regime_kind,
        regime_definition_bytes=regime_bytes,
        prompt_body_bytes=prompt_body_bytes,
        objective_typed=objective_typed,
        admitted_constructors=admitted_constructors,
        open_obstructions=open_obstructions,
        demand_set=demand_set,
        kill_conditions=kill_conditions,
        required_reply_fields=required_reply_fields,
        residual_colour=args.residual_colour,
        dual_witness_required=dual_witness_required,
        dual_witness_ref=args.dual_witness_ref,
        parent_packet_id=args.parent_packet_id,
        conversation_root_id=args.conversation_root_id,
    )

    if args.artifact_dir is not None:
        write_content_addressed_json(args.artifact_dir, "prompt-artifact", artifact.to_dict())
    _write_json(args.output, artifact.to_dict())
    return 0


def cmd_verify_prompt(args: argparse.Namespace) -> int:
    wire = _read_json(args.artifact)
    artifact = PromptArtifactV1.from_dict(wire)
    if args.prompt_body_bytes:
        artifact.verify_prompt_body(args.prompt_body_bytes.read_bytes())
    _write_json(args.output, artifact.to_dict())
    return 0


def cmd_create_task_from_prompt(args: argparse.Namespace) -> int:
    wire = _read_json(args.artifact)
    artifact = PromptArtifactV1.from_dict(wire)
    payload = build_payload_from_prompt_artifact(
        artifact,
        role=args.role,
        turn_kind=args.turn_kind,
        candidate_budget=args.candidate_budget,
        operation_budget=args.operation_budget,
    )
    envelope = build_llm_turn_envelope(
        payload,
        task_id=args.task_id,
        carrier_id=args.carrier_id,
        step_budget=args.step_budget,
    )
    if args.artifact_dir is not None:
        write_content_addressed_json(args.artifact_dir, "llm-turn-task", envelope.to_dict())
    _write_json(args.output, envelope.to_dict())
    return 0
