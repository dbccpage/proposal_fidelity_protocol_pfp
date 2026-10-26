"""Run turn and bout execution command handlers for Symbol Game CLI presentation layer.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

from omega_engine_governance.domain.intelligence_community import canonical_intelligence_route
from omega_engine_pfp.domain import (
    DEFAULT_REQUIRED_REPLY_FIELDS,
    ObjectiveTypedV1,
    RegimeKind,
    attach_llm_turn_candidate,
    bind_content_bytes,
    build_llm_turn_envelope,
    build_payload_from_content,
    compile_prompt_artifact,
    render_prompt_body,
)
from omega_engine_pfp.functional_boundary import require_rust_functional
from omega_engine_pfp.infrastructure.serialization import (
    write_content_addressed_json,
)

from .io_utils import _write_json, _write_text


def cmd_run_turn(args: argparse.Namespace) -> int:
    """Executes a complete Symbol Game turn / problem reduction, writing all prompt and response packets."""
    require_rust_functional("cmd_run_turn")
    prompt_text = args.prompt if args.prompt is not None else ""
    if not prompt_text and getattr(args, "prompt_file", None) is not None:
        prompt_text = args.prompt_file.read_text(encoding="utf-8")

    task_id = args.task_id
    if not task_id:
        h = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:8]
        task_id = f"symgam_{int(time.time())}_{h}"

    base_out = Path(args.output_dir) if args.output_dir else Path(canonical_intelligence_route("_intelligence/symbol_game"))
    runs_dir = base_out / "runs" if not str(base_out).endswith("runs") else base_out
    run_dir = runs_dir / task_id
    run_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = base_out / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # 1. Compile & build prompt packet (PromptArtifactV1 & PacketEnvelopeV2)
    prompt_bytes = prompt_text.encode("utf-8")
    obj_summary = args.objective or (prompt_text[:80] if prompt_text else "Symbol Game prompt turn")
    objective_typed = ObjectiveTypedV1(
        kind="prompt_turn",
        summary=obj_summary,
        target_obstruction_ids=(),
        target_demand_ids=(),
    )
    prompt_body_bytes = render_prompt_body(
        b"symbol_game_regime_v1",
        objective_typed=objective_typed,
        admitted_constructors=(),
        open_obstructions=(),
        demand_set=(),
        kill_conditions=("F-01_inherited_meaning",),
        required_reply_fields=tuple(sorted(set(DEFAULT_REQUIRED_REPLY_FIELDS))),
    )
    prompt_artifact = compile_prompt_artifact(
        regime_kind=RegimeKind.SYMBOL_ONLY.value,
        regime_definition_bytes=b"symbol_game_regime_v1",
        prompt_body_bytes=prompt_body_bytes,
        objective_typed=objective_typed,
        admitted_constructors=(),
        open_obstructions=(),
        demand_set=(),
        kill_conditions=("F-01_inherited_meaning",),
        required_reply_fields=tuple(sorted(set(DEFAULT_REQUIRED_REPLY_FIELDS))),
        residual_colour="Open",
        dual_witness_required=False,
    )

    prompt_payload = build_payload_from_content(
        objective=obj_summary,
        role=args.role,
        turn_kind="prose",
        content_bytes=prompt_bytes,
        candidate_budget=args.candidate_budget,
        operation_budget=args.operation_budget,
    )
    prompt_envelope = build_llm_turn_envelope(
        prompt_payload,
        task_id=task_id,
        carrier_id=args.carrier_id,
        step_budget=args.max_steps,
    )

    # Write prompt packets to run directory and content-addressed store
    _write_json(run_dir / "prompt_packet.json", prompt_envelope.to_dict())
    _write_json(run_dir / "prompt_artifact.json", prompt_artifact.to_dict())
    write_content_addressed_json(artifacts_dir, "prompt-packet", prompt_envelope.to_dict())
    write_content_addressed_json(artifacts_dir, "prompt-artifact", prompt_artifact.to_dict())

    # 2. Execute SymbolGameEngine
    from omega_engine_pfp.controllers.symbol_game_engine import SymbolGameEngine

    engine = SymbolGameEngine(target_dir=run_dir)
    outcome = engine.execute_turn(task_id=task_id, prompt=prompt_text)
    reduction = engine.solve_problem(prompt_text, task_id=task_id, max_steps=args.max_steps)

    # 3. Build & write response packet (CandidateArtifactV1 & LlmTurnContentArtifactV1)
    response_content = (
        f"```machine\n"
        f"AUTHORITY_EFFECT=None\n"
        f"RESIDUAL_COLOUR={'Exact' if outcome.is_exact else 'Open'}\n"
        f"PURITY={outcome.purity:.4f}\n"
        f"L1_OBSTRUCTION={outcome.l1_obstruction:.4f}\n"
        f"VERDICT={outcome.verdict}\n"
        f"```\n\n"
        f"Step Outcome: {outcome.step_id} - Verdict: {outcome.verdict}\n"
        f"Evidence: {outcome.evidence_sha256}\n"
    )
    content_artifact = bind_content_bytes(
        packet_id=prompt_envelope.packet_id,
        producer_id=args.producer_id,
        content_bytes=prompt_bytes,
        claimed_summary=f"Turn step {outcome.step_id} prompt content",
    )
    candidate = attach_llm_turn_candidate(
        prompt_envelope,
        content_artifact,
        producer_id=args.producer_id,
        reply_text=response_content,
        claimed_terminal=outcome.is_exact,
        claimed_valid=True,
    )

    # Write response packet to run directory and content-addressed store
    _write_json(run_dir / "response_packet.json", candidate.to_dict())
    _write_json(run_dir / "candidate_artifact.json", candidate.to_dict())
    _write_json(
        run_dir / "turn_outcome.json",
        outcome.to_dict()
        if hasattr(outcome, "to_dict")
        else {
            "step_id": outcome.step_id,
            "purity": outcome.purity,
            "l1_obstruction": outcome.l1_obstruction,
            "is_exact": outcome.is_exact,
            "verdict": outcome.verdict,
            "evidence_sha256": outcome.evidence_sha256,
            "authority_effect": "None",
        },
    )
    write_content_addressed_json(artifacts_dir, "candidate-packet", candidate.to_dict())

    # 4. Write full receipt.json
    receipt = {
        "schema_version": "omega.symbol-game.receipt.v1",
        "task_id": task_id,
        "prompt_packet_id": prompt_envelope.packet_id,
        "candidate_id": candidate.candidate_id,
        "status": reduction.get("status", "COMPLETED"),
        "steps_executed": reduction.get("steps_executed", 1),
        "is_resolved": reduction.get("is_resolved", outcome.is_exact),
        "outcome": {
            "step_id": outcome.step_id,
            "purity": outcome.purity,
            "l1_obstruction": outcome.l1_obstruction,
            "verdict": outcome.verdict,
            "is_exact": outcome.is_exact,
        },
        "reduction_score": reduction.get("final_score", {}),
        "authority_effect": "None",
    }
    _write_json(run_dir / "receipt.json", receipt)

    # 5. Write trace / dda_actions
    traces = [
        {
            "step": 0,
            "action": "PROMPT_ENVELOPE_SEALED",
            "packet_id": prompt_envelope.packet_id,
            "task_id": task_id,
            "authority_effect": "None",
        },
        {
            "step": 1,
            "action": "MANIFOLD_RETRACTION_STEP",
            "step_id": outcome.step_id,
            "purity": outcome.purity,
            "l1_obstruction": outcome.l1_obstruction,
            "verdict": outcome.verdict,
            "authority_effect": "None",
        },
        {
            "step": 2,
            "action": "CANDIDATE_RESPONSE_ATTACHED",
            "candidate_id": candidate.candidate_id,
            "authority_effect": "None",
        },
    ]
    trace_path = run_dir / "trace.jsonl"
    with trace_path.open("w", encoding="utf-8") as f:
        for t in traces:
            f.write(json.dumps(t) + "\n")
    dda_path = run_dir / "dda_actions.jsonl"
    with dda_path.open("w", encoding="utf-8") as f:
        for t in traces:
            f.write(json.dumps(t) + "\n")

    # 6. Render summary.md
    summary_md = (
        f"# Symbol Game Run Summary: `{task_id}`\n\n"
        f"**AuthorityEffect:** `None`\n\n"
        f"## Execution Details\n"
        f"- **Task ID:** `{task_id}`\n"
        f"- **Prompt Packet ID:** `{prompt_envelope.packet_id}`\n"
        f"- **Candidate ID:** `{candidate.candidate_id}`\n"
        f"- **Verdict:** `{outcome.verdict}`\n"
        f"- **Purity:** `{outcome.purity:.4f}`\n"
        f"- **L1 Obstruction:** `{outcome.l1_obstruction:.4f}`\n"
        f"- **Status:** `{reduction.get('status', 'COMPLETED')}`\n\n"
        f"## Prompt Body\n"
        f"```text\n{prompt_text}\n```\n\n"
        f"## Candidate Response\n"
        f"```text\n{response_content}\n```\n\n"
        f"_This markdown summary is a non-authoritative rendering. Machine state lives in receipt.json._\n"
    )
    _write_text(run_dir / "summary.md", summary_md)

    if args.output is not None:
        _write_json(args.output, receipt)
    else:
        sys.stdout.write(json.dumps(receipt, indent=2) + "\n")

    return 0
