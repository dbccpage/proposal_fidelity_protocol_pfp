"""JSON API Router for Symbol Game Presentation Layer.

Exposes deterministic services for prompt compiling, turn evaluation,
code change proposal verification, and coboundary scoring.
AuthorityEffect: None (const).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from pfp.domain import (
    CandidateArtifactV1,
    DemandItemV1,
    ObjectiveTypedV1,
    ObstructionHintV1,
    PacketEnvelopeV2,
    PromptArtifactV1,
    bind_content_bytes,
    compile_prompt_artifact,
    evaluate_llm_turn_candidate,
    render_prompt_body,
)
from pfp.fixtures.gate11_residual_dual import (
    parse_gate11_symbolic_reply,
)


class ApiResponse:
    def __init__(self, status_code: int, data: Mapping[str, Any]) -> None:
        self.status_code = status_code
        self.data = dict(data)

    def to_json(self) -> str:
        return json.dumps(self.data, indent=2, sort_keys=True)


class SymbolGameApiRouter:
    """REST-like dispatcher for Symbol Game presentation queries and commands."""

    @staticmethod
    def health() -> ApiResponse:
        return ApiResponse(
            200,
            {
                "status": "healthy",
                "service": "core.symbol_game.ui.api.v1",
                "authority_effect": "None",
                "operations": [
                    "POST /api/prompt/compile",
                    "POST /api/prompt/verify",
                    "POST /api/turn/evaluate",
                    "POST /api/proposal/score",
                ],
            },
        )

    @staticmethod
    def compile_prompt(payload: Mapping[str, Any]) -> ApiResponse:
        try:
            regime_text = payload.get("regime_text", "")
            regime_bytes = regime_text.encode("utf-8")
            regime_kind = payload.get("regime_kind", "fence_only")

            obj_data = payload.get("objective", {})
            objective_typed = ObjectiveTypedV1(
                kind=obj_data.get("kind", "prompt_turn"),
                summary=obj_data.get("summary", "structured prompt turn"),
                target_obstruction_ids=tuple(
                    sorted(set(obj_data.get("target_obstruction_ids", [])))
                ),
                target_demand_ids=tuple(sorted(set(obj_data.get("target_demand_ids", [])))),
            )

            open_obs = tuple(
                ObstructionHintV1.from_dict(x) for x in payload.get("open_obstructions", [])
            )
            demand_set = tuple(DemandItemV1.from_dict(x) for x in payload.get("demand_set", []))
            admitted_constructors = tuple(sorted(set(payload.get("admitted_constructors", []))))
            kill_conditions = tuple(
                sorted(set(payload.get("kill_conditions", ["F-01_inherited_meaning"])))
            )
            from pfp.domain import DEFAULT_REQUIRED_REPLY_FIELDS

            required_reply_fields = tuple(
                sorted(set(payload.get("required_reply_fields", DEFAULT_REQUIRED_REPLY_FIELDS)))
            )
            residual_colour = payload.get("residual_colour", "Open")
            dual_witness_required = payload.get("dual_witness_required", residual_colour == "Exact")
            dual_witness_ref = payload.get("dual_witness_ref")
            prompt_body_text = payload.get("prompt_body_text")
            prompt_body_bytes = prompt_body_text.encode("utf-8") if prompt_body_text else None

            if prompt_body_bytes is None:
                prompt_body_bytes = render_prompt_body(
                    regime_bytes,
                    objective_typed=objective_typed,
                    admitted_constructors=admitted_constructors,
                    open_obstructions=open_obs,
                    demand_set=demand_set,
                    kill_conditions=kill_conditions,
                    required_reply_fields=required_reply_fields,
                )

            artifact = compile_prompt_artifact(
                regime_kind=regime_kind,
                regime_definition_bytes=regime_bytes,
                prompt_body_bytes=prompt_body_bytes,
                objective_typed=objective_typed,
                admitted_constructors=admitted_constructors,
                open_obstructions=open_obs,
                demand_set=demand_set,
                kill_conditions=kill_conditions,
                required_reply_fields=required_reply_fields,
                residual_colour=residual_colour,
                dual_witness_required=dual_witness_required,
                dual_witness_ref=dual_witness_ref,
                parent_packet_id=payload.get("parent_packet_id"),
                conversation_root_id=payload.get("conversation_root_id"),
            )

            rendered = prompt_body_bytes.decode("utf-8")
            return ApiResponse(
                200,
                {
                    "success": True,
                    "artifact": artifact.to_dict(),
                    "rendered_body": rendered,
                    "prompt_body_sha256": artifact.prompt_body_sha256,
                    "authority_effect": "None",
                },
            )
        except Exception as exc:
            return ApiResponse(
                400, {"success": False, "error": str(exc), "authority_effect": "None"}
            )

    @staticmethod
    def verify_prompt(payload: Mapping[str, Any]) -> ApiResponse:
        try:
            artifact_wire = payload.get("artifact", {})
            artifact = PromptArtifactV1.from_dict(artifact_wire)
            body_text = payload.get("prompt_body_text")
            if body_text is not None:
                artifact.verify_prompt_body(body_text.encode("utf-8"))
            return ApiResponse(
                200,
                {
                    "success": True,
                    "valid": True,
                    "prompt_artifact_id": artifact.prompt_artifact_id,
                    "residual_colour": artifact.residual_colour,
                    "authority_effect": "None",
                },
            )
        except Exception as exc:
            return ApiResponse(
                400,
                {"success": False, "valid": False, "error": str(exc), "authority_effect": "None"},
            )

    @staticmethod
    def evaluate_turn(payload: Mapping[str, Any]) -> ApiResponse:
        try:
            packet_wire = payload.get("packet", {})
            candidate_wire = payload.get("candidate", {})
            envelope = PacketEnvelopeV2.from_dict(packet_wire)
            candidate = CandidateArtifactV1.from_dict(candidate_wire)

            content_text = payload.get("content_text")
            content_artifact = None
            if content_text is not None:
                content_artifact = bind_content_bytes(
                    packet_id=envelope.packet_id,
                    producer_id=candidate.producer_id,
                    content_bytes=content_text.encode("utf-8"),
                )

            run_root = evaluate_llm_turn_candidate(
                envelope,
                candidate,
                content_artifact=content_artifact,
                prior_candidate_count=payload.get("prior_candidate_count", 0),
                operation_count=payload.get("operation_count", 1),
            )
            return ApiResponse(
                200,
                {
                    "success": True,
                    "run_root": run_root.to_dict(),
                    "host_passed": run_root.receipt.host_valid if run_root.receipt else False,
                    "authority_effect": "None",
                },
            )
        except Exception as exc:
            return ApiResponse(
                400, {"success": False, "error": str(exc), "authority_effect": "None"}
            )

    @staticmethod
    def score_proposal(payload: Mapping[str, Any]) -> ApiResponse:
        try:
            reply_markdown = payload.get("reply_markdown", "")
            from pfp.infrastructure.adapters.exact_rust_adapter import (
                RustExactEngineAdapter,
            )

            result = parse_gate11_symbolic_reply(reply_markdown, RustExactEngineAdapter())
            return ApiResponse(
                200,
                {
                    "success": True,
                    "score_result": result,
                    "authority_effect": "None",
                },
            )
        except Exception as exc:
            return ApiResponse(
                400, {"success": False, "error": str(exc), "authority_effect": "None"}
            )

    @classmethod
    def dispatch(cls, method: str, path: str, body: Mapping[str, Any] | None = None) -> ApiResponse:
        m = method.upper().strip()
        p = path.strip()
        body_dict = dict(body or {})

        if m == "GET" and (p == "/api/health" or p == "/health"):
            return cls.health()
        if m == "POST" and p == "/api/prompt/compile":
            return cls.compile_prompt(body_dict)
        if m == "POST" and p == "/api/prompt/verify":
            return cls.verify_prompt(body_dict)
        if m == "POST" and p == "/api/turn/evaluate":
            return cls.evaluate_turn(body_dict)
        if m == "POST" and p == "/api/proposal/score":
            return cls.score_proposal(body_dict)

        return ApiResponse(
            404, {"error": f"Endpoint not found: {m} {p}", "authority_effect": "None"}
        )
