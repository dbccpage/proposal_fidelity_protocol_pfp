"""Thin swarm-facing API for the Symbol Game communication path.

Four typed operations. One import path. One cognitive object per function.
Hides the large internal modules behind minimal typed surfaces.

AuthorityEffect: None. No promotion, evaluation, or verification authority.
"""

from __future__ import annotations

from typing import Any, Sequence

from omega_engine_pfp.domain import (
    DEFAULT_REQUIRED_REPLY_FIELDS,
    DemandItemV1,
    LlmTurnPayloadV1,
    ObjectiveTypedV1,
    ObstructionHintV1,
    PromptArtifactV1,
    RegimeKind,
    ResidualColour,
    build_payload_from_prompt_artifact,
    compile_prompt_artifact,
    render_prompt_body,
)
from omega_engine_pfp.domain.ports.reply_control_port import ReplyControlPort
from omega_engine_pfp.infrastructure.adapters.reply_control_adapter import (
    RustReplyControlAdapter,
)
from omega_engine_pfp.infrastructure.serialization import CanonicalizationError

VALID_RESIDUAL_COLOURS = frozenset(member.value for member in ResidualColour)


def _reply_control(payload: dict[str, Any], port: ReplyControlPort | None) -> dict[str, Any]:
    outcome = (port if port is not None else RustReplyControlAdapter()).invoke(payload)
    if outcome.is_err:
        refusal = outcome.unwrap_err()
        raise CanonicalizationError(f"{refusal.code}: {refusal.message}")
    record = outcome.unwrap()
    if not record.get("success"):
        raise CanonicalizationError(str(record.get("error", "REPLY_CONTROL_REFUSED")))
    result = record.get("result")
    if not isinstance(result, dict):
        raise CanonicalizationError("REPLY_CONTROL_RESULT_INVALID")
    return result


def compile_prompt(
    regime_kind: RegimeKind | str,
    regime_definition_bytes: bytes,
    objective_typed: ObjectiveTypedV1,
    *,
    admitted_constructors: Sequence[str] = (),
    open_obstructions: Sequence[ObstructionHintV1] = (),
    demand_set: Sequence[DemandItemV1] = (),
    kill_conditions: Sequence[str] = ("F-01_inherited_meaning",),
    required_reply_fields: Sequence[str] = DEFAULT_REQUIRED_REPLY_FIELDS,
    residual_colour: ResidualColour | str = ResidualColour.OPEN,
    dual_witness_required: bool | None = None,
    dual_witness_ref: str | None = None,
    parent_packet_id: str | None = None,
    conversation_root_id: str | None = None,
    prompt_body_bytes: bytes | None = None,
) -> tuple[PromptArtifactV1, bytes]:
    """Compile a PromptArtifactV1 and its canonical rendered prompt body bytes.

    If prompt_body_bytes is not supplied, it is deterministically rendered from
    the regime bytes and structured sections.
    """
    if prompt_body_bytes is None:
        prompt_body_bytes = render_prompt_body(
            regime_definition_bytes,
            objective_typed=objective_typed,
            admitted_constructors=admitted_constructors,
            open_obstructions=open_obstructions,
            demand_set=demand_set,
            kill_conditions=kill_conditions,
            required_reply_fields=required_reply_fields,
        )

    artifact = compile_prompt_artifact(
        regime_kind=regime_kind,
        regime_definition_bytes=regime_definition_bytes,
        prompt_body_bytes=prompt_body_bytes,
        objective_typed=objective_typed,
        admitted_constructors=admitted_constructors,
        open_obstructions=open_obstructions,
        demand_set=demand_set,
        kill_conditions=kill_conditions,
        required_reply_fields=required_reply_fields,
        residual_colour=residual_colour,
        dual_witness_required=dual_witness_required,
        dual_witness_ref=dual_witness_ref,
        parent_packet_id=parent_packet_id,
        conversation_root_id=conversation_root_id,
    )
    return artifact, prompt_body_bytes


def create_turn(
    prompt_artifact: PromptArtifactV1,
    *,
    role: str = "user",
    turn_kind: str = "prose",
    candidate_budget: int = 3,
    operation_budget: int = 20,
) -> LlmTurnPayloadV1:
    """Build an LlmTurnPayloadV1 bound to the given PromptArtifactV1."""
    return build_payload_from_prompt_artifact(
        prompt_artifact,
        role=role,
        turn_kind=turn_kind,
        candidate_budget=candidate_budget,
        operation_budget=operation_budget,
    )


def parse_machine_block(reply_text: str, *, port: ReplyControlPort | None = None) -> dict[str, str]:
    """Extract untrusted machine fields through the native reply-control port."""
    result = _reply_control({"operation": "parse", "reply_text": reply_text}, port)
    return {key: result["machine_fields"][key] for key in result["field_order"]}


def validate_reply_residual(
    machine_fields: dict[str, str],
    *,
    dual_witness_digest: str | None = None,
    port: ReplyControlPort | None = None,
) -> tuple[str, list[str]]:
    """Check declared authority/residual fields; a digest is not host proof."""
    result = _reply_control(
        {
            "operation": "validate",
            "machine_fields": machine_fields,
            "dual_witness_digest": dual_witness_digest,
        },
        port,
    )
    return result["residual_colour"], list(result["refusal_codes"])
