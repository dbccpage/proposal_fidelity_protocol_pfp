"""Use cases for PromptArtifact and EliminationReceipt compilation, rendering, and storage.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from omega_engine_pfp.domain.aggregates.llm_turn_run_root import LlmTurnPayloadV1
from omega_engine_pfp.domain.aggregates.prompt_artifact import (
    EliminationReceiptV1,
    PromptArtifactV1,
)
from omega_engine_pfp.domain.aggregates.prompt_artifact import (
    compile_prompt_artifact as compile_canonical_prompt_artifact,
)
from omega_engine_pfp.domain.aggregates.prompt_artifact import (
    render_prompt_body as render_canonical_prompt_body,
)
from omega_engine_pfp.domain.aggregates.research_claim import (
    canonical_json_artifact_bytes,
)
from omega_engine_pfp.domain.shared_kernel.canonical import CanonicalizationError
from omega_engine_pfp.domain.validation import (
    _fail,
    _require_stable_id,
    normalize_utf8_lf,
    raw_content_sha256,
)
from omega_engine_pfp.domain.value_objects import (
    DemandItemV1,
    ObjectiveTypedV1,
    ObstructionHintV1,
    RegimeKind,
    ResidualColour,
)

_FILE_STEM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def write_content_addressed_json(
    directory: str | Path,
    artifact_kind: str,
    value: Mapping[str, Any],
) -> Path:
    """Write immutable ``<kind>_<sha256>.json`` content, reusing exact matches."""
    artifact_kind = _require_stable_id(artifact_kind, "artifact_kind")
    if _FILE_STEM.fullmatch(artifact_kind) is None:
        _fail("artifact_kind must be a portable filename stem")
    content = canonical_json_artifact_bytes(value)
    digest = hashlib.sha256(content).hexdigest()
    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{artifact_kind}_{digest}.json"
    try:
        with output_path.open("xb") as stream:
            stream.write(content)
    except FileExistsError:
        if output_path.read_bytes() != content:
            raise CanonicalizationError(
                "content-addressed artifact path contains different bytes"
            )
    return output_path


def load_regime_id(regime_path: str | Path) -> tuple[str, bytes]:
    """Load regime file, apply utf8-lf normalization, and return (regime_id, bytes)."""
    data = Path(regime_path).read_bytes()
    normalized = normalize_utf8_lf(data)
    regime_id, _ = raw_content_sha256(normalized)
    return regime_id, normalized


def compile_prompt_artifact(
    *,
    regime_kind: str | RegimeKind,
    regime_definition_bytes: bytes,
    prompt_body_bytes: bytes,
    objective_typed: ObjectiveTypedV1,
    admitted_constructors: Sequence[str] = (),
    open_obstructions: Sequence[ObstructionHintV1] = (),
    demand_set: Sequence[DemandItemV1] = (),
    kill_conditions: Sequence[str] = (),
    required_reply_fields: Sequence[str] = (),
    residual_colour: str | ResidualColour = ResidualColour.OPEN,
    dual_witness_required: bool | None = None,
    dual_witness_ref: str | None = None,
    parent_packet_id: str | None = None,
    conversation_root_id: str | None = None,
    explicit_artifact_id: str | None = None,
    normalize_body: bool = True,
) -> PromptArtifactV1:
    """Compile through the canonical domain implementation.

    The legacy explicit ID remains an application alias. Wire admission always
    recomputes the content identity and does not trust that alias.
    """
    artifact = compile_canonical_prompt_artifact(
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
        normalize_body=normalize_body,
    )
    return replace(artifact, explicit_artifact_id=explicit_artifact_id)


def prompt_artifact_to_content_binding(
    artifact: PromptArtifactV1,
) -> tuple[str, int]:
    """LlmTurnPayloadV1.content_sha256 must equal prompt body, not artifact id."""
    return artifact.prompt_body_sha256, artifact.prompt_body_byte_count


prompt_artifact_to_turn_content_binding = prompt_artifact_to_content_binding


def build_payload_from_prompt_artifact(
    artifact: PromptArtifactV1,
    *,
    task_id: str = "prompt_artifact_task",
    role: str = "user",
    turn_kind: str = "prose",
    candidate_budget: int = 3,
    operation_budget: int = 20,
) -> LlmTurnPayloadV1:
    """Build an LlmTurnPayloadV1 bound to a PromptArtifactV1."""
    content_sha, content_len = prompt_artifact_to_content_binding(artifact)
    objective_summary = artifact.objective_typed.summary
    objective_text = f"[prompt_artifact:{artifact.prompt_artifact_id}] {objective_summary}"
    return LlmTurnPayloadV1.create(
        task_id=task_id,
        role=role,
        turn_kind=turn_kind,
        objective=objective_text,
        prompt_artifact_id=artifact.prompt_artifact_id,
        prompt_body_sha256=content_sha,
        prompt_body_bytes_len=content_len,
        required_reply_fields=artifact.required_reply_fields,
        candidate_budget=candidate_budget,
        operation_budget=operation_budget,
    )


def create_elimination_receipt(
    *,
    packet_id: str,
    prior_residual_colour: str | ResidualColour,
    new_residual_colour: str | ResidualColour,
    evidence_root: str,
    eliminated_obstruction_ids: Sequence[str] = (),
    dual_witness_ref: str | None = None,
) -> EliminationReceiptV1:
    """Host-authored constructor for an elimination receipt.

    Sorts eliminated_obstruction_ids and enforces residual transition law.
    """
    prior_str = prior_residual_colour.value if isinstance(prior_residual_colour, ResidualColour) else str(prior_residual_colour)
    new_str = new_residual_colour.value if isinstance(new_residual_colour, ResidualColour) else str(new_residual_colour)
    elim_tuple = tuple(sorted(set(eliminated_obstruction_ids)))

    return EliminationReceiptV1(
        packet_id=packet_id,
        eliminated_obstruction_ids=elim_tuple,
        prior_residual_colour=prior_str,
        new_residual_colour=new_str,
        evidence_root=evidence_root,
        dual_witness_ref=dual_witness_ref,
    )


def render_prompt_body(
    regime_bytes: bytes,
    *,
    objective_typed: ObjectiveTypedV1,
    admitted_constructors: Sequence[str] = (),
    open_obstructions: Sequence[ObstructionHintV1] = (),
    demand_set: Sequence[DemandItemV1] = (),
    kill_conditions: Sequence[str] = (),
    required_reply_fields: Sequence[str] = (),
) -> bytes:
    """Render through the canonical domain implementation."""
    return render_canonical_prompt_body(
        regime_bytes,
        objective_typed=objective_typed,
        admitted_constructors=admitted_constructors,
        open_obstructions=open_obstructions,
        demand_set=demand_set,
        kill_conditions=kill_conditions,
        required_reply_fields=required_reply_fields,
    )


def render_elimination_receipt_block(receipt: EliminationReceiptV1) -> str:
    """Render the machine elimination receipt block appended after host verify."""
    elim_str = ", ".join(receipt.eliminated_obstruction_ids) if receipt.eliminated_obstruction_ids else "none"
    dual_str = receipt.dual_witness_ref if receipt.dual_witness_ref is not None else "null"
    return (
        "```elimination_receipt\n"
        f"ELIMINATED: {elim_str}\n"
        f"PRIOR_RESIDUAL_COLOUR: {receipt.prior_residual_colour}\n"
        f"NEW_RESIDUAL_COLOUR: {receipt.new_residual_colour}\n"
        f"EVIDENCE_ROOT: {receipt.evidence_root}\n"
        f"DUAL_WITNESS_REF: {dual_str}\n"
        f"AUTHORITY_EFFECT: {receipt.authority_effect}\n"
        "```\n"
    )


def parse_elimination_receipt_block(text: str) -> dict[str, str] | None:
    """Parse elimination receipt block fields if present in text."""
    pattern = re.compile(r"```elimination_receipt\s*\n(.*?)```", re.DOTALL)
    match = pattern.search(text)
    if match is None:
        return None
    block_text = match.group(1)
    fields: dict[str, str] = {}
    field_pattern = re.compile(r"^([A-Z_]+):\s*(.*)$", re.MULTILINE)
    for fm in field_pattern.finditer(block_text):
        key = fm.group(1).strip()
        value = fm.group(2).strip()
        if key in fields:
            _fail(f"duplicate elimination receipt field: {key}")
        fields[key] = value
    return fields


def write_prompt_artifact(
    directory: str | Path,
    artifact: PromptArtifactV1,
    *,
    writer: Callable[[str | Path, str, Mapping[str, Any]], Path] | None = None,
) -> Path:
    """Filename digest is Layer B of JSON bytes - not prompt_artifact_id."""
    fn = writer or write_content_addressed_json
    return fn(
        directory,
        "prompt-artifact",
        artifact.to_dict(),
    )


def write_prompt_body(directory: str | Path, body: bytes) -> Path:
    """Content-addressed prompt body write with exclusive create and collision check."""
    digest, _ = raw_content_sha256(body)
    path = Path(directory) / f"prompt-body_{digest}.bin"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(body)
    except FileExistsError:
        if path.read_bytes() != body:
            _fail("content-addressed prompt body path contains different bytes")
    return path


def write_elimination_receipt(
    directory: str | Path,
    receipt: EliminationReceiptV1,
    *,
    writer: Callable[[str | Path, str, Mapping[str, Any]], Path] | None = None,
) -> Path:
    """Content-addressed write of elimination receipt JSON."""
    fn = writer or write_content_addressed_json
    return fn(
        directory,
        "elimination-receipt",
        receipt.to_dict(),
    )




class CompilePromptUseCase:
    """Compiles a new PromptArtifact."""

    def execute(
        self,
        *,
        prompt_artifact_id: str,
        regime_kind: str,
        prompt_body: str,
        regime_metadata: Mapping[str, Any] | None = None,
        admitted_constructors: Sequence[str] = (),
        open_obstructions: Sequence[ObstructionHintV1] = (),
        demand_set: Sequence[DemandItemV1] = (),
        kill_conditions: Sequence[str] = (),
        required_reply_fields: Sequence[str] = (),
        objective: ObjectiveTypedV1 | None = None,
        residual_colour: str = "Open",
        dual_witness_required: bool = False,
        dual_witness_ref: str | None = None,
        parent_packet_id: str | None = None,
        conversation_root_id: str | None = None,
    ) -> PromptArtifactV1:
        if objective is None:
            objective = ObjectiveTypedV1(
                kind="prompt_turn",
                summary=f"Prompt artifact for {prompt_artifact_id}",
            )
        rk = "prose-regime" if regime_kind in ("fence_only", "prose") else regime_kind
        if rk not in ("prose-regime", "code-diff-regime", "lean4-proof-regime", "hybrid-regime"):
            rk = "prose-regime"
        regime_bytes = f"regime:{rk}".encode("utf-8")
        body_bytes = prompt_body.encode("utf-8")
        col = "Open"
        if str(residual_colour) in ("Closed", "Exact"):
            col = str(residual_colour)
        return compile_prompt_artifact(
            regime_kind=rk,
            regime_definition_bytes=regime_bytes,
            prompt_body_bytes=body_bytes,
            objective_typed=objective,
            admitted_constructors=admitted_constructors,
            open_obstructions=open_obstructions,
            demand_set=demand_set,
            kill_conditions=kill_conditions,
            required_reply_fields=required_reply_fields,
            residual_colour=col,
            dual_witness_required=dual_witness_required,
            dual_witness_ref=dual_witness_ref,
            parent_packet_id=parent_packet_id,
            conversation_root_id=conversation_root_id,
            explicit_artifact_id=prompt_artifact_id,
        )


class EliminateObstructionUseCase:
    """Records that a host check eliminated obstructions, as an EliminationReceiptV1.

    The receipt says what the host checked. It does not authorize anything.
    """

    def execute(
        self,
        *,
        packet_id: str,
        prior_residual_colour: str | ResidualColour,
        new_residual_colour: str | ResidualColour,
        evidence_root: str,
        eliminated_obstruction_ids: Sequence[str] = (),
        dual_witness_ref: str | None = None,
    ) -> EliminationReceiptV1:
        return create_elimination_receipt(
            packet_id=packet_id,
            prior_residual_colour=prior_residual_colour,
            new_residual_colour=new_residual_colour,
            evidence_root=evidence_root,
            eliminated_obstruction_ids=eliminated_obstruction_ids,
            dual_witness_ref=dual_witness_ref,
        )


class ValidateReplyResidualUseCase:
    """Checks that a reply carries every field its PromptArtifact requires.

    The reply must be a JSON object, and each required field must be one of its
    top-level keys. A field name that appears only inside a value does not count.
    Text that is not a JSON object fails.
    """

    def execute(
        self,
        *,
        artifact: PromptArtifactV1,
        reply_content: str,
    ) -> bool:
        try:
            reply = json.loads(reply_content)
        except (TypeError, ValueError):
            return False
        if not isinstance(reply, dict):
            return False
        return all(field_name in reply for field_name in artifact.required_reply_fields)

__all__ = [
    "CompilePromptUseCase",
    "EliminateObstructionUseCase",
    "ValidateReplyResidualUseCase",

    "build_payload_from_prompt_artifact",
    "compile_prompt_artifact",
    "create_elimination_receipt",
    "load_regime_id",
    "parse_elimination_receipt_block",
    "prompt_artifact_to_content_binding",
    "prompt_artifact_to_turn_content_binding",
    "render_elimination_receipt_block",
    "render_prompt_body",
    "write_elimination_receipt",
    "write_prompt_artifact",
    "write_prompt_body",
]
