"""LLM Turn command handlers for Symbol Game CLI presentation layer.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from omega_engine_pfp.infrastructure.serialization import CanonicalizationError
from omega_engine_pfp.domain import (
    CandidateArtifactV1,
    LlmTurnContentArtifactV1,
    LlmTurnPayloadV1,
    PacketEnvelopeV2,
    attach_llm_turn_candidate,
    bind_content_bytes,
    build_llm_turn_envelope,
    build_payload_from_content,
    evaluate_llm_turn_candidate,
    parse_llm_turn_envelope,
    render_llm_turn_run_root_markdown,
    verify_markdown_does_not_mutate_claims as verify_llm_markdown_claims,
    verify_llm_turn_run_root,
)
from omega_engine_pfp.infrastructure.serialization import (
    write_content_addressed_json,
)
from .io_utils import _read_json, _write_json, _write_text


def cmd_create_task(args: argparse.Namespace) -> int:
    if args.payload is not None:
        payload_wire = _read_json(args.payload)
        payload = LlmTurnPayloadV1.from_dict(payload_wire)
    else:
        if args.content_bytes is None:
            raise CanonicalizationError("create-task requires --payload or --content-bytes")
        content_bytes = args.content_bytes.read_bytes()
        parent = args.parent_packet_id
        payload = build_payload_from_content(
            objective=args.objective,
            role=args.role,
            turn_kind=args.turn_kind,
            content_bytes=content_bytes,
            candidate_budget=args.candidate_budget,
            operation_budget=args.operation_budget,
            parent_packet_id=parent,
            conversation_root_id=args.conversation_root_id,
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


def cmd_attach_candidate(args: argparse.Namespace) -> int:
    envelope_wire = _read_json(args.packet)
    envelope = PacketEnvelopeV2.from_dict(envelope_wire)
    parse_llm_turn_envelope(envelope)
    content_bytes = args.content_bytes.read_bytes()
    artifact = bind_content_bytes(
        packet_id=envelope.packet_id,
        producer_id=args.producer_id,
        content_bytes=content_bytes,
        encoding=args.content_encoding,
        declared_sha256=args.content_sha256,
        claimed_summary=args.claimed_summary,
    )
    candidate = attach_llm_turn_candidate(
        envelope,
        artifact,
        producer_id=args.producer_id,
        claimed_terminal=args.claimed_terminal,
        claimed_valid=args.claimed_valid,
    )
    if args.artifact_dir is not None:
        write_content_addressed_json(args.artifact_dir, "llm-turn-candidate", candidate.to_dict())
    _write_json(args.output, candidate.to_dict())
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    envelope = PacketEnvelopeV2.from_dict(_read_json(args.packet))
    candidate = CandidateArtifactV1.from_dict(_read_json(args.candidate))
    if args.content is not None:
        content_artifact = LlmTurnContentArtifactV1.from_dict(_read_json(args.content))
    elif args.content_bytes is not None:
        raw_bytes = args.content_bytes.read_bytes()
        content_artifact = bind_content_bytes(
            packet_id=envelope.packet_id,
            producer_id=candidate.producer_id,
            content_bytes=raw_bytes,
        )
    elif args.reply_text is not None:
        raw_bytes = args.reply_text.read_bytes()
        content_artifact = bind_content_bytes(
            packet_id=envelope.packet_id,
            producer_id=candidate.producer_id,
            content_bytes=raw_bytes,
        )
    else:
        content_artifact = None

    run_root = evaluate_llm_turn_candidate(
        envelope,
        candidate,
        content_artifact=content_artifact,
        prior_candidate_count=args.prior_candidate_count,
        operation_count=args.operation_count,
    )
    if args.artifact_dir is not None:
        write_content_addressed_json(args.artifact_dir, "llm-turn-run-root", run_root.to_dict())
    _write_json(args.output, run_root.to_dict())
    return 0


def cmd_verify_run_root(args: argparse.Namespace) -> int:
    wire = _read_json(args.run_root)
    run_root = verify_llm_turn_run_root(wire)
    _write_json(args.output, run_root.to_dict())
    return 0


def cmd_render_markdown(args: argparse.Namespace) -> int:
    wire = _read_json(args.run_root)
    run_root = verify_llm_turn_run_root(wire)
    md = render_llm_turn_run_root_markdown(run_root)
    verify_llm_markdown_claims(md, run_root)
    _write_text(args.output, md)
    return 0
