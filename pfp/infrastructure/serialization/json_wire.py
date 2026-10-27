"""JSON wire serialization and deserialization adapter for Symbol Game packets."""

from __future__ import annotations

import json
from typing import Any, Mapping

from ...domain import (
    AuthorityEffect,
    BytePayload,
    CandidateArtifactV1,
    CodeChangePatchArtifactV1,
    CodeChangeProposalPayloadV1,
    CodeChangeRunRootV1,
    ContentDigest,
    DemandItemV1,
    EliminationReceiptV1,
    GateReceiptV1,
    InvariantViolationError,
    LlmTurnContentArtifactV1,
    LlmTurnPayloadV1,
    LlmTurnRunRootV1,
    ObjectiveTypedV1,
    ObstructionHintV1,
    PacketEnvelopeV2,
    PacketSchemaError,
    PayloadSizeLimitExceededError,
    PromptArtifactV1,
    ResearchClaimPayloadV1,
    ResearchClaimV1,
    ResearchRunRootV1,
    ResidualColour,
    WireKey,
)

ENVELOPE_SCHEMA_V2: str = "core.symbol-game.envelope.v2"


def serialize_envelope_v2(envelope: PacketEnvelopeV2) -> str:
    """Serializes a PacketEnvelopeV2 to a canonical JSON string."""
    return json.dumps(envelope.to_dict(), sort_keys=True, indent=2)


def deserialize_envelope_v2(raw_json: str) -> PacketEnvelopeV2:
    """Deserializes raw JSON into a validated PacketEnvelopeV2."""
    payload_vo = BytePayload.from_str(raw_json)
    try:
        data = json.loads(payload_vo.as_str())
    except json.JSONDecodeError as exc:
        raise PacketSchemaError(f"Invalid JSON envelope: {exc}") from exc

    schema = data.get(WireKey.SCHEMA_VERSION.value)
    if schema != ENVELOPE_SCHEMA_V2:
        raise PacketSchemaError(f"Expected schema {ENVELOPE_SCHEMA_V2!r}, got {schema!r}")

    packet_id = data.get(WireKey.PACKET_ID.value)
    if not packet_id or not isinstance(packet_id, str):
        raise PacketSchemaError("packet_id must be a non-empty string")

    return PacketEnvelopeV2(
        schema_version=schema,
        packet_id=packet_id,
        family=str(data.get(WireKey.FAMILY.value, "")),
        payload_schema=str(data.get(WireKey.PAYLOAD_SCHEMA.value, "")),
        payload=data.get(WireKey.PAYLOAD.value, {}),
        carrier_id=str(data.get(WireKey.CARRIER_ID.value, "")),
        parent_packet_id=data.get(WireKey.PARENT_PACKET_ID.value),
        conversation_root_id=data.get(WireKey.CONVERSATION_ROOT_ID.value),
        step_budget=data.get("step_budget"),
        authority_effect=AuthorityEffect.NONE.value,
    )


def serialize_prompt_artifact(artifact: PromptArtifactV1) -> str:
    """Serializes PromptArtifactV1 to JSON."""
    return json.dumps(artifact.to_dict(), sort_keys=True, indent=2)


def deserialize_prompt_artifact(raw_json: str) -> PromptArtifactV1:
    """Deserializes JSON to PromptArtifactV1."""
    payload_vo = BytePayload.from_str(raw_json)
    try:
        data = json.loads(payload_vo.as_str())
    except json.JSONDecodeError as exc:
        raise PacketSchemaError(f"Invalid JSON prompt artifact: {exc}") from exc
    return PromptArtifactV1.from_dict(data)


import hashlib
from pathlib import Path
import re
from ...domain.validation import _fail, _require_exact_dict, _require_stable_id

_FILE_STEM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def canonical_json_artifact_bytes(value: Mapping[str, Any]) -> bytes:
    """Encode a primitive artifact deterministically for content addressing."""
    primitive = _require_exact_dict(value, "JSON artifact")
    return (
        json.dumps(
            primitive,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


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


__all__ = [
    "ENVELOPE_SCHEMA_V2",
    "canonical_json_artifact_bytes",
    "deserialize_envelope_v2",
    "deserialize_prompt_artifact",
    "serialize_envelope_v2",
    "serialize_prompt_artifact",
    "write_content_addressed_json",
]

