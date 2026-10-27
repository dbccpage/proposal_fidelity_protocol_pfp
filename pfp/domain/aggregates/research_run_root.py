"""Semantic, content-addressed roots for bounded research-family runs.

This module deliberately separates replay identity from occurrence identity.
Trace timestamps, random run identifiers, temporary paths, challenges, and the
TraceLogger's occurrence hash chain are not authority and do not participate in
the semantic DDA root.  All remaining declared evidence is canonicalized and
hashed.  The resulting receipt is still lab evidence: ``authority_effect`` is
always ``"None"`` and no signature or authentication claim is made here.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

from governance.contracts.ddc_packets import (
    DDATapeDFA,
    DDATapeValidationError,
)

from .research_claim import ResearchClaimPayloadV1 as ResearchClaimPayloadV1
from .research_claim import ResearchClaimV1 as ResearchClaimV1

RUN_ROOT_SCHEMA = "core.symbol-game.research-run-root.v1"
RESEARCH_RUN_ROOT_SCHEMA = RUN_ROOT_SCHEMA
RESEARCH_CLAIM_FAMILY = "research_claim_v1"
RESEARCH_CLAIM_SCHEMA = "core.symbol-game.research-claim.v1"
SEMANTIC_STEP_SCHEMA = "core.symbol-game.semantic-dda-step.v1"
RESEARCH_PACKET_MEDIA_TYPE = "application/vnd.core.research-packet+json"
SOURCE_INTAKE_MEDIA_TYPE = "application/vnd.core.source-intake+json"
DDA_TRACE_MEDIA_TYPE = "application/x-core-dda-trace+jsonl"
OESOS_EVIDENCE_BUNDLE_MEDIA_TYPE = "application/vnd.core.oesos-evidence+json"

MAX_TRACE_BYTES = 16 * 1024 * 1024
MAX_TRACE_LINE_BYTES = 1024 * 1024
MAX_TRACE_STEPS = 4096
MAX_SEMANTIC_DEPTH = 64
MAX_SEMANTIC_COLLECTION_ITEMS = 4096
MAX_RUN_ROOT_ARTIFACTS = 256
MAX_RUN_ROOT_CODES = 256
MAX_RUN_ROOT_STRING_BYTES = 8192

ARTIFACT_AVAILABILITIES = frozenset({"AVAILABLE", "BOUND_ONLY", "MISSING"})
RESEARCH_TERMINAL_STATUSES = frozenset(
    {
        "FINITE_NUMERICAL_SHADOW_CLOSED",
        "FINITE_NUMERICAL_SHADOW_CLOSED_EXTERNAL_SOURCE_BYTES_REQUIRED",
        "FINITE_NUMERICAL_SHADOW_CLOSED_SOURCE_UNVERIFIED",
        "FINITE_RESIDUAL_CLOSED",
        "REFUSED",
    }
)
RESEARCH_EVIDENCE_PROFILES = frozenset({"LocalReplayableFiniteEvidence", "RefusalOnly"})
_FAMILY_TERMINAL_STATUSES = {
    "witten_airy_finite_v1": frozenset(
        {
            "FINITE_NUMERICAL_SHADOW_CLOSED",
            "FINITE_NUMERICAL_SHADOW_CLOSED_EXTERNAL_SOURCE_BYTES_REQUIRED",
            "FINITE_NUMERICAL_SHADOW_CLOSED_SOURCE_UNVERIFIED",
            "REFUSED",
        }
    ),
    "gr_constraint_closure_finite_v1": frozenset({"FINITE_RESIDUAL_CLOSED", "REFUSED"}),
    "witten_chern_simons_full_v1": frozenset({"REFUSED"}),
    "gr_stretch_claims_v1": frozenset({"REFUSED"}),
}
_REFUSAL_FAMILIES = frozenset({"witten_chern_simons_full_v1", "gr_stretch_claims_v1"})

# Keys in this exact allowlist carry occurrence metadata rather than scientific
# semantics.  Matching is case-insensitive but never suffix- or substring-based.
# In particular, ``source_path`` is not discarded merely because it contains
# the word "path".
OCCURRENCE_ONLY_KEYS = frozenset(
    {
        "artifact_path",
        "challenge",
        "challenge_id",
        "created_at",
        "jsonl_path",
        "nonce",
        "occurrence_id",
        "oesos_trace",
        "output_path",
        "packet_artifact",
        "path",
        "prev_step_hash",
        "recorded_at",
        "run_id",
        "runner_id",
        "step_hash",
        "step_id",
        "source_intake_artifact",
        "temp_path",
        "temporary_path",
        "timestamp",
        "timestamp_utc",
        "trace_path",
        "uuid",
        "uuid_hex",
    }
)

_TRACE_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "dda_dialect",
        "timestamp_utc",
        "runner_id",
        "campaign",
        "run_id",
        "step_id",
        "letter",
        "effect",
        "action_name",
        "cochain_dim",
        "coboundary_map",
        "input_state",
        "output_state",
        "witness",
        "obstruction_id",
        "residual_before",
        "residual_after",
        "residual_delta",
        "residual_energy",
        "structure_delta",
        "evidence",
        "refusal_reason",
        "authority_effect",
        "prev_step_hash",
        "step_hash",
    }
)
_TRACE_OPTIONAL_OCCURRENCE_FIELDS = OCCURRENCE_ONLY_KEYS - _TRACE_REQUIRED_FIELDS
_TRACE_PROFILES = {
    "core.dda.trace.v2": ("dda_dialect", "DDA_STEP_"),
    "core.ddc.trace.v2": ("ddc_dialect", "DDC_STEP_"),
}
_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ResearchRunRootError(ValueError):
    """Raised when a semantic run root or one of its artifacts fails closed."""


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ResearchRunRootError("value has no strict JSON representation") from exc


def _domain_digest(domain: str, value: Any) -> str:
    if type(domain) is not str or not domain:
        raise ResearchRunRootError("digest domain must be a nonempty string")
    payload = domain.encode("utf-8") + b"\x00" + _canonical_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _is_digest(value: Any) -> bool:
    return type(value) is str and _DIGEST_PATTERN.fullmatch(value) is not None


def _require_digest(value: Any, label: str) -> str:
    if not _is_digest(value):
        raise ResearchRunRootError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_optional_digest(value: Any, label: str) -> str | None:
    if value is not None:
        _require_digest(value, label)
    return value


def _require_nonempty_string(value: Any, label: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ResearchRunRootError(f"{label} must be a trimmed nonempty string")
    if len(value.encode("utf-8")) > MAX_RUN_ROOT_STRING_BYTES:
        raise ResearchRunRootError(f"{label} exceeds the string resource limit")
    return value


def _require_optional_string(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _require_nonempty_string(value, label)


def _require_exact_fields(
    value: Any,
    expected: frozenset[str],
    label: str,
) -> Mapping[str, Any]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise ResearchRunRootError(f"{label} must be an exact JSON object")
    actual = frozenset(value)
    missing = expected - actual
    unknown = actual - expected
    if missing:
        raise ResearchRunRootError(
            f"{label} is missing fields: {', '.join(sorted(missing))}"
        )
    if unknown:
        raise ResearchRunRootError(
            f"{label} has unknown fields: {', '.join(sorted(unknown))}"
        )
    return value


def _portable_label(value: Any) -> str:
    label = _require_nonempty_string(value, "artifact label")
    if "\\" in label or ":" in label:
        raise ResearchRunRootError("artifact label must be a POSIX relative path")
    path = PurePosixPath(label)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ResearchRunRootError("artifact label must stay below the artifact root")
    normalized = path.as_posix()
    if normalized != label:
        raise ResearchRunRootError("artifact label is not normalized")
    return label


def _float_hex(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if type(value) not in {int, float}:
        raise ResearchRunRootError(f"{label} must be a finite number or null")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise ResearchRunRootError(f"{label} must be finite") from exc
    if not math.isfinite(number):
        raise ResearchRunRootError(f"{label} must be finite")
    return number.hex()


def _validate_float_hex(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ResearchRunRootError(f"{label} must be a canonical float hex or null")
    try:
        number = float.fromhex(value)
    except ValueError as exc:
        raise ResearchRunRootError(f"{label} is not a float hex") from exc
    if not math.isfinite(number) or number.hex() != value:
        raise ResearchRunRootError(f"{label} is not a canonical finite float hex")
    return value


def _duplicate_rejecting_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ResearchRunRootError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ResearchRunRootError(f"non-finite JSON number is refused: {value}")


def _loads_json(text: str, label: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_duplicate_rejecting_object,
            parse_constant=_reject_json_constant,
        )
    except ResearchRunRootError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ResearchRunRootError(f"invalid JSON in {label}") from exc


def _sanitize_semantic_value(value: Any, *, depth: int = 0) -> Any:
    """Canonicalize evidence while dropping only declared occurrence fields.

    Occurrence values are never harvested as global replacement tokens.  A path,
    UUID, or challenge may also be legitimate scientific data elsewhere in a
    record; rewriting matching strings outside their declared field would make
    distinct semantic traces collide.
    """

    if depth > MAX_SEMANTIC_DEPTH:
        raise ResearchRunRootError("semantic evidence exceeds the nesting limit")
    if value is None or type(value) in {bool, int}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ResearchRunRootError("semantic evidence contains a non-finite float")
        return {"$float_hex": value.hex()}
    if type(value) is str:
        return value
    if type(value) is list:
        if len(value) > MAX_SEMANTIC_COLLECTION_ITEMS:
            raise ResearchRunRootError("semantic evidence collection is too large")
        return [_sanitize_semantic_value(item, depth=depth + 1) for item in value]
    if type(value) is tuple:
        if len(value) > MAX_SEMANTIC_COLLECTION_ITEMS:
            raise ResearchRunRootError("semantic evidence collection is too large")
        return [_sanitize_semantic_value(item, depth=depth + 1) for item in value]
    if type(value) is dict:
        if len(value) > MAX_SEMANTIC_COLLECTION_ITEMS:
            raise ResearchRunRootError("semantic evidence object is too large")
        sanitized: dict[str, Any] = {}
        for key in sorted(value):
            if type(key) is not str:
                raise ResearchRunRootError("semantic evidence keys must be strings")
            if key.casefold() in OCCURRENCE_ONLY_KEYS:
                continue
            sanitized[key] = _sanitize_semantic_value(value[key], depth=depth + 1)
        return sanitized
    raise ResearchRunRootError(
        f"unsupported semantic evidence value: {type(value).__qualname__}"
    )


@dataclass(frozen=True, slots=True)
class ArtifactRefV1:
    """Digest-bound artifact locator relative to a caller-supplied root."""

    label: str
    media_type: str
    content_sha256: str
    byte_count: int
    required: bool
    availability: str

    def __post_init__(self) -> None:
        _portable_label(self.label)
        _require_nonempty_string(self.media_type, "artifact media_type")
        _require_digest(self.content_sha256, "artifact content_sha256")
        if type(self.byte_count) is not int or self.byte_count < 0:
            raise ResearchRunRootError(
                "artifact byte_count must be a nonnegative integer"
            )
        if type(self.required) is not bool:
            raise ResearchRunRootError("artifact required must be a boolean")
        if self.availability not in ARTIFACT_AVAILABILITIES:
            raise ResearchRunRootError(
                "artifact availability must be AVAILABLE, BOUND_ONLY, or MISSING"
            )
        if self.required and self.availability != "AVAILABLE":
            raise ResearchRunRootError("required artifacts must be locally AVAILABLE")

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "media_type": self.media_type,
            "content_sha256": self.content_sha256,
            "byte_count": self.byte_count,
            "required": self.required,
            "availability": self.availability,
        }

    @classmethod
    def from_dict(cls, value: Any) -> ArtifactRefV1:
        wire = _require_exact_fields(
            value,
            frozenset(
                {
                    "label",
                    "media_type",
                    "content_sha256",
                    "byte_count",
                    "required",
                    "availability",
                }
            ),
            "artifact ref",
        )
        return cls(
            label=wire["label"],
            media_type=wire["media_type"],
            content_sha256=wire["content_sha256"],
            byte_count=wire["byte_count"],
            required=wire["required"],
            availability=wire["availability"],
        )


@dataclass(frozen=True, slots=True)
class SemanticDdaStepV1:
    """Occurrence-free semantic view of one TraceLogger step."""

    letter: str
    operation: str
    input_type: str
    output_type: str
    certificate: str
    residual_before_hex: str | None
    residual_after_hex: str | None
    effect: str
    obstruction_id: str | None
    evidence_root: str

    def __post_init__(self) -> None:
        _require_nonempty_string(self.letter, "DDA letter")
        _require_nonempty_string(self.operation, "DDA operation")
        _require_nonempty_string(self.input_type, "DDA input_type")
        _require_nonempty_string(self.output_type, "DDA output_type")
        _require_nonempty_string(self.certificate, "DDA certificate")
        _validate_float_hex(self.residual_before_hex, "residual_before_hex")
        _validate_float_hex(self.residual_after_hex, "residual_after_hex")
        _require_nonempty_string(self.effect, "DDA effect")
        _require_optional_string(self.obstruction_id, "DDA obstruction_id")
        _require_digest(self.evidence_root, "DDA evidence_root")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SEMANTIC_STEP_SCHEMA,
            "letter": self.letter,
            "operation": self.operation,
            "input_type": self.input_type,
            "output_type": self.output_type,
            "certificate": self.certificate,
            "residual_before_hex": self.residual_before_hex,
            "residual_after_hex": self.residual_after_hex,
            "effect": self.effect,
            "obstruction_id": self.obstruction_id,
            "evidence_root": self.evidence_root,
        }

    @classmethod
    def from_dict(cls, value: Any) -> SemanticDdaStepV1:
        wire = _require_exact_fields(
            value,
            frozenset(
                {
                    "schema_version",
                    "letter",
                    "operation",
                    "input_type",
                    "output_type",
                    "certificate",
                    "residual_before_hex",
                    "residual_after_hex",
                    "effect",
                    "obstruction_id",
                    "evidence_root",
                }
            ),
            "semantic DDA step",
        )
        if wire["schema_version"] != SEMANTIC_STEP_SCHEMA:
            raise ResearchRunRootError("unsupported semantic DDA step schema")
        return cls(
            letter=wire["letter"],
            operation=wire["operation"],
            input_type=wire["input_type"],
            output_type=wire["output_type"],
            certificate=wire["certificate"],
            residual_before_hex=wire["residual_before_hex"],
            residual_after_hex=wire["residual_after_hex"],
            effect=wire["effect"],
            obstruction_id=wire["obstruction_id"],
            evidence_root=wire["evidence_root"],
        )


def _semantic_step_from_record(record: Any, line_number: int) -> SemanticDdaStepV1:
    if type(record) is not dict or any(type(key) is not str for key in record):
        raise ResearchRunRootError(f"trace line {line_number} must be an object")
    schema = record.get("schema_version")
    profile = _TRACE_PROFILES.get(schema) if type(schema) is str else None
    if profile is None:
        raise ResearchRunRootError(f"trace line {line_number} has an unsupported schema")
    dialect_key, _ = profile
    required = (_TRACE_REQUIRED_FIELDS - {"dda_dialect"}) | {dialect_key}
    keys = frozenset(record)
    missing = required - keys
    unknown = keys - required - _TRACE_OPTIONAL_OCCURRENCE_FIELDS
    if missing:
        raise ResearchRunRootError(
            f"trace line {line_number} is missing fields: {', '.join(sorted(missing))}"
        )
    if unknown:
        raise ResearchRunRootError(
            f"trace line {line_number} has unknown fields: {', '.join(sorted(unknown))}"
        )
    if record["authority_effect"] != "None":
        raise ResearchRunRootError(f"trace line {line_number} elevates authority")
    for key in (
        dialect_key,
        "runner_id",
        "campaign",
        "run_id",
        "step_id",
        "letter",
        "effect",
        "action_name",
        "cochain_dim",
        "coboundary_map",
        "input_state",
        "output_state",
        "witness",
    ):
        _require_nonempty_string(record[key], f"trace line {line_number} {key}")
    if record["letter"] not in {"C", "R", "E", "I", "Λ", "Lambda", "L", "D", "M", "T", "Z"}:
        raise ResearchRunRootError("DDA trace record must contain exactly one letter")
    _require_optional_string(
        record["obstruction_id"], f"trace line {line_number} obstruction_id"
    )
    _require_optional_string(
        record["refusal_reason"], f"trace line {line_number} refusal_reason"
    )
    _float_hex(record["residual_before"], "residual_before")
    _float_hex(record["residual_after"], "residual_after")
    _float_hex(record["residual_delta"], "residual_delta")
    _float_hex(record["residual_energy"], "residual_energy")
    if type(record["structure_delta"]) is not dict:
        raise ResearchRunRootError("trace structure_delta must be an object")
    if type(record["evidence"]) is not dict:
        raise ResearchRunRootError("trace evidence must be an object")
    if record["prev_step_hash"] is not None:
        _require_digest(record["prev_step_hash"], "trace prev_step_hash")
    _require_digest(record["step_hash"], "trace step_hash")

    evidence_payload = {
        "trace_schema": record["schema_version"],
        dialect_key: record[dialect_key],
        "cochain_dim": record["cochain_dim"],
        "coboundary_map": record["coboundary_map"],
        "residual_delta": record["residual_delta"],
        "residual_energy": record["residual_energy"],
        "structure_delta": record["structure_delta"],
        "evidence": record["evidence"],
        "refusal_reason": record["refusal_reason"],
        "authority_effect": record["authority_effect"],
    }
    sanitized_evidence = _sanitize_semantic_value(evidence_payload)
    evidence_root = _domain_digest(
        "core.symbol-game.semantic-dda-evidence.v1", sanitized_evidence
    )

    def semantic_text(key: str) -> str:
        sanitized = _sanitize_semantic_value(record[key])
        if type(sanitized) is not str or not sanitized:
            raise ResearchRunRootError(f"trace {key} has no semantic text")
        return sanitized

    obstruction = record["obstruction_id"]
    if obstruction is not None:
        obstruction = _sanitize_semantic_value(obstruction)
    return SemanticDdaStepV1(
        letter=semantic_text("letter"),
        operation=semantic_text("action_name"),
        input_type=semantic_text("input_state"),
        output_type=semantic_text("output_state"),
        certificate=semantic_text("witness"),
        residual_before_hex=_float_hex(record["residual_before"], "residual_before"),
        residual_after_hex=_float_hex(record["residual_after"], "residual_after"),
        effect=semantic_text("effect"),
        obstruction_id=obstruction,
        evidence_root=evidence_root,
    )


def semantic_dda_root(steps: tuple[SemanticDdaStepV1, ...]) -> str:
    """Return an order-sensitive, domain-separated hash chain for DDA steps."""

    if type(steps) is not tuple or not steps:
        raise ResearchRunRootError("semantic DDA trace must be a nonempty tuple")
    if any(type(step) is not SemanticDdaStepV1 for step in steps):
        raise ResearchRunRootError("semantic DDA trace contains an invalid step")
    head = _domain_digest(
        "core.symbol-game.semantic-dda-chain.seed.v1",
        {"schema_version": SEMANTIC_STEP_SCHEMA},
    )
    for index, step in enumerate(steps):
        head = _domain_digest(
            "core.symbol-game.semantic-dda-chain.step.v1",
            {"index": index, "previous": head, "step": step.to_dict()},
        )
    return _domain_digest(
        "core.symbol-game.semantic-dda-chain.terminal.v1",
        {"step_count": len(steps), "head": head},
    )


def _native_trace_step_hash(record: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in record.items() if key != "step_hash"}
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_native_trace_chain(records: tuple[dict[str, Any], ...]) -> None:
    if not records:
        raise ResearchRunRootError("DDA trace must contain at least one step")
    first = records[0]
    dialect_key, step_prefix = _TRACE_PROFILES[first["schema_version"]]
    stable_fields = ("schema_version", dialect_key, "runner_id", "campaign", "run_id")
    previous: dict[str, Any] | None = None
    for index, record in enumerate(records, start=1):
        if any(record.get(field) != first[field] for field in stable_fields):
            raise ResearchRunRootError(
                "DDA trace occurrence identity changed mid-chain"
            )
        if record["step_id"] != f"{step_prefix}{index:03d}":
            raise ResearchRunRootError("DDA trace step sequence is not canonical")
        expected_parent = None if previous is None else previous["step_hash"]
        if record["prev_step_hash"] != expected_parent:
            raise ResearchRunRootError("DDA trace prev_step_hash chain is broken")
        if record["step_hash"] != _native_trace_step_hash(record):
            raise ResearchRunRootError("DDA trace step_hash does not replay")
        if previous is not None:
            if previous["output_state"] != record["input_state"]:
                raise ResearchRunRootError("DDA trace state continuity is broken")
            if previous["residual_after"] != record["residual_before"]:
                raise ResearchRunRootError("DDA trace residual continuity is broken")

        before = record["residual_before"]
        after = record["residual_after"]
        expected_delta = (
            None if before is None or after is None else float(after) - float(before)
        )
        if record["residual_delta"] != expected_delta:
            raise ResearchRunRootError("DDA trace residual_delta does not replay")
        expected_energy = 0.0 if after is None else float(after)
        if record["residual_energy"] != expected_energy:
            raise ResearchRunRootError("DDA trace residual_energy does not replay")

        letter = record["letter"]
        effect = record["effect"]
        if letter == "E":
            if (
                effect != "obstruction_eliminated"
                or not record["obstruction_id"]
                or before is None
                or after is None
                or float(after) >= float(before)
            ):
                raise ResearchRunRootError("DDA E step does not eliminate obstruction")
        if letter in {"L", "Lambda", "Λ"} and (
            effect != "structure_added" or not record["structure_delta"]
        ):
            raise ResearchRunRootError("DDA lift step lacks declared structure")
        if letter == "Z" and (
            effect != "refusal" or before != after or not record["refusal_reason"]
        ):
            raise ResearchRunRootError("DDA Z step does not retain a typed refusal")
        if letter == "I" and effect != "integration":
            raise ResearchRunRootError("DDA I step lacks integration semantics")
        if letter == "T" and effect != "terminalization":
            raise ResearchRunRootError("DDA T step lacks terminal semantics")
        previous = record

    tape = ".".join(record["letter"] for record in records)
    try:
        DDATapeDFA.validate(tape, dialect=first[dialect_key])
    except DDATapeValidationError as exc:
        raise ResearchRunRootError("DDA trace violates its declared grammar") from exc


def _read_validated_trace_records(trace_path: str | Path) -> tuple[dict[str, Any], ...]:
    path = Path(trace_path)
    try:
        byte_count = path.stat().st_size
        if byte_count > MAX_TRACE_BYTES:
            raise ResearchRunRootError("DDA trace exceeds the byte resource limit")
        data = path.read_bytes()
        if len(data) != byte_count:
            raise ResearchRunRootError("DDA trace changed while it was read")
        text = data.decode("utf-8", errors="strict")
    except ResearchRunRootError:
        raise
    except (OSError, UnicodeError) as exc:
        raise ResearchRunRootError(f"cannot read DDA trace: {path}") from exc
    lines = text.splitlines()
    if not lines:
        raise ResearchRunRootError("DDA trace must contain at least one step")
    if len(lines) > MAX_TRACE_STEPS:
        raise ResearchRunRootError("DDA trace exceeds the step resource limit")
    if any(len(line.encode("utf-8")) > MAX_TRACE_LINE_BYTES for line in lines):
        raise ResearchRunRootError("DDA trace line exceeds the byte resource limit")
    records = tuple(
        _loads_json(line, f"trace line {number}")
        for number, line in enumerate(lines, start=1)
    )
    steps = tuple(
        _semantic_step_from_record(record, number)
        for number, record in enumerate(records, start=1)
    )
    del steps
    _validate_native_trace_chain(records)
    return records


def semantic_dda_from_trace(
    trace_path: str | Path,
) -> tuple[tuple[SemanticDdaStepV1, ...], str]:
    """Strictly decode a TraceLogger JSONL file and derive its semantic root."""

    records = _read_validated_trace_records(trace_path)
    steps = tuple(
        _semantic_step_from_record(record, number)
        for number, record in enumerate(records, start=1)
    )
    return steps, semantic_dda_root(steps)


def semantic_dda_from_records(
    records: tuple[dict[str, Any], ...],
) -> tuple[tuple[SemanticDdaStepV1, ...], str]:
    """Validate original trace records extracted from a checked storage envelope.

    Envelope custody belongs to its storage owner. This operation still checks
    the original occurrence hashes, grammar, effects and continuity.
    """
    if type(records) is not tuple or not records or len(records) > MAX_TRACE_STEPS:
        raise ResearchRunRootError("DDA trace record count is invalid")
    try:
        lines = tuple(json.dumps(row, ensure_ascii=False, allow_nan=False).encode("utf-8")
                      for row in records)
    except (ValueError, TypeError, UnicodeError) as exc:
        raise ResearchRunRootError("DDA trace records are not finite UTF-8 JSON") from exc
    raw = b"\n".join(lines)
    if len(raw) > MAX_TRACE_BYTES:
        raise ResearchRunRootError("DDA trace exceeds the byte resource limit")
    if any(len(line) > MAX_TRACE_LINE_BYTES for line in lines):
        raise ResearchRunRootError("DDA trace line exceeds the byte resource limit")
    steps = tuple(_semantic_step_from_record(row, i) for i, row in enumerate(records, 1))
    _validate_native_trace_chain(records)
    return steps, semantic_dda_root(steps)


@dataclass(frozen=True, slots=True)
class ResearchRunRootV1:
    """Complete semantic identity for one bounded research-family occurrence."""

    claim_packet_id: str
    family_id: str
    source_manifest_root: str
    claim_manifest_root: str
    source_intake_receipt_id: str
    terminal_status: str
    semantic_dda_root: str
    semantic_trace_label: str
    artifact_manifest: tuple[ArtifactRefV1, ...]
    refusal_codes: tuple[str, ...]
    unresolved_obligations: tuple[str, ...]
    evidence_profile: str
    oesos_event_root: str | None = None
    oesos_runtime_root: str | None = None
    oesos_wire_root: str | None = None
    oesos_bridge_root: str | None = None
    schema_version: str = RUN_ROOT_SCHEMA
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema_version != RUN_ROOT_SCHEMA:
            raise ResearchRunRootError("unsupported research run-root schema")
        _require_digest(self.claim_packet_id, "claim_packet_id")
        _require_nonempty_string(self.family_id, "family_id")
        _require_digest(self.source_manifest_root, "source_manifest_root")
        _require_digest(self.claim_manifest_root, "claim_manifest_root")
        _require_digest(self.source_intake_receipt_id, "source_intake_receipt_id")
        _require_nonempty_string(self.terminal_status, "terminal_status")
        if self.terminal_status not in RESEARCH_TERMINAL_STATUSES:
            raise ResearchRunRootError("unsupported research terminal_status")
        _require_digest(self.semantic_dda_root, "semantic_dda_root")
        _portable_label(self.semantic_trace_label)
        _require_nonempty_string(self.evidence_profile, "evidence_profile")
        if self.evidence_profile not in RESEARCH_EVIDENCE_PROFILES:
            raise ResearchRunRootError("unsupported research evidence_profile")
        if self.authority_effect != "None":
            raise ResearchRunRootError("research run roots never elevate authority")
        for field_name, value in (
            ("oesos_event_root", self.oesos_event_root),
            ("oesos_runtime_root", self.oesos_runtime_root),
            ("oesos_wire_root", self.oesos_wire_root),
            ("oesos_bridge_root", self.oesos_bridge_root),
        ):
            _require_optional_digest(value, field_name)
        oesos_core_roots = (
            self.oesos_event_root,
            self.oesos_runtime_root,
            self.oesos_wire_root,
        )
        if any(value is not None for value in oesos_core_roots) and any(
            value is None for value in oesos_core_roots
        ):
            raise ResearchRunRootError("OESOS core roots must be present as one set")
        if self.oesos_bridge_root is not None:
            raise ResearchRunRootError(
                "oesos_bridge_root is not replay-reachable in run-root v1"
            )
        if type(self.artifact_manifest) is not tuple or any(
            type(ref) is not ArtifactRefV1 for ref in self.artifact_manifest
        ):
            raise ResearchRunRootError("artifact_manifest must be an artifact tuple")
        if len(self.artifact_manifest) > MAX_RUN_ROOT_ARTIFACTS:
            raise ResearchRunRootError("artifact_manifest exceeds the resource limit")
        labels = tuple(ref.label for ref in self.artifact_manifest)
        if labels != tuple(sorted(labels)):
            raise ResearchRunRootError("artifact_manifest must be sorted by label")
        if len(set(labels)) != len(labels):
            raise ResearchRunRootError("artifact_manifest contains duplicate labels")
        trace_refs = tuple(
            ref
            for ref in self.artifact_manifest
            if ref.label == self.semantic_trace_label
            and ref.media_type == DDA_TRACE_MEDIA_TYPE
            and ref.required
            and ref.availability == "AVAILABLE"
        )
        if len(trace_refs) != 1:
            raise ResearchRunRootError(
                "semantic_trace_label must name exactly one required AVAILABLE "
                "application/x-core-dda-trace+jsonl artifact"
            )
        for media_type, label in (
            (RESEARCH_PACKET_MEDIA_TYPE, "research packet"),
            (SOURCE_INTAKE_MEDIA_TYPE, "source intake"),
        ):
            refs = tuple(
                ref
                for ref in self.artifact_manifest
                if ref.media_type == media_type
                and ref.required
                and ref.availability == "AVAILABLE"
            )
            if len(refs) != 1:
                raise ResearchRunRootError(
                    f"artifact_manifest must contain exactly one required {label}"
                )
        oesos_refs = tuple(
            ref
            for ref in self.artifact_manifest
            if ref.media_type == OESOS_EVIDENCE_BUNDLE_MEDIA_TYPE
            and ref.required
            and ref.availability == "AVAILABLE"
        )
        expected_oesos_refs = 1 if self.oesos_event_root is not None else 0
        if len(oesos_refs) != expected_oesos_refs:
            raise ResearchRunRootError(
                "OESOS roots and evidence-bundle artifacts do not correspond"
            )
        _validate_sorted_unique_strings(self.refusal_codes, "refusal_codes")
        _validate_sorted_unique_strings(
            self.unresolved_obligations, "unresolved_obligations"
        )

    def identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "claim_packet_id": self.claim_packet_id,
            "family_id": self.family_id,
            "source_manifest_root": self.source_manifest_root,
            "claim_manifest_root": self.claim_manifest_root,
            "source_intake_receipt_id": self.source_intake_receipt_id,
            "terminal_status": self.terminal_status,
            "semantic_dda_root": self.semantic_dda_root,
            "semantic_trace_label": self.semantic_trace_label,
            "oesos_event_root": self.oesos_event_root,
            "oesos_runtime_root": self.oesos_runtime_root,
            "oesos_wire_root": self.oesos_wire_root,
            "oesos_bridge_root": self.oesos_bridge_root,
            "artifact_manifest": [ref.to_dict() for ref in self.artifact_manifest],
            "refusal_codes": list(self.refusal_codes),
            "unresolved_obligations": list(self.unresolved_obligations),
            "evidence_profile": self.evidence_profile,
            "authority_effect": self.authority_effect,
        }

    @property
    def root_id(self) -> str:
        return _domain_digest(
            "core.symbol-game.research-run-root.identity.v1", self.identity_dict()
        )

    def to_dict(self) -> dict[str, Any]:
        wire = self.identity_dict()
        wire["root_id"] = self.root_id
        return wire

    @classmethod
    def from_dict(cls, value: Any) -> ResearchRunRootV1:
        wire = _require_exact_fields(
            value,
            frozenset(
                {
                    "schema_version",
                    "claim_packet_id",
                    "family_id",
                    "source_manifest_root",
                    "claim_manifest_root",
                    "source_intake_receipt_id",
                    "terminal_status",
                    "semantic_dda_root",
                    "semantic_trace_label",
                    "oesos_event_root",
                    "oesos_runtime_root",
                    "oesos_wire_root",
                    "oesos_bridge_root",
                    "artifact_manifest",
                    "refusal_codes",
                    "unresolved_obligations",
                    "evidence_profile",
                    "authority_effect",
                    "root_id",
                }
            ),
            "research run root",
        )
        for array_field in (
            "artifact_manifest",
            "refusal_codes",
            "unresolved_obligations",
        ):
            if type(wire[array_field]) is not list:
                raise ResearchRunRootError(f"{array_field} must be an array")
        result = cls(
            claim_packet_id=wire["claim_packet_id"],
            family_id=wire["family_id"],
            source_manifest_root=wire["source_manifest_root"],
            claim_manifest_root=wire["claim_manifest_root"],
            source_intake_receipt_id=wire["source_intake_receipt_id"],
            terminal_status=wire["terminal_status"],
            semantic_dda_root=wire["semantic_dda_root"],
            semantic_trace_label=wire["semantic_trace_label"],
            artifact_manifest=tuple(
                ArtifactRefV1.from_dict(ref) for ref in wire["artifact_manifest"]
            ),
            refusal_codes=tuple(wire["refusal_codes"]),
            unresolved_obligations=tuple(wire["unresolved_obligations"]),
            evidence_profile=wire["evidence_profile"],
            oesos_event_root=wire["oesos_event_root"],
            oesos_runtime_root=wire["oesos_runtime_root"],
            oesos_wire_root=wire["oesos_wire_root"],
            oesos_bridge_root=wire["oesos_bridge_root"],
            schema_version=wire["schema_version"],
            authority_effect=wire["authority_effect"],
        )
        _require_digest(wire["root_id"], "root_id")
        if wire["root_id"] != result.root_id:
            raise ResearchRunRootError("research run root identity mismatch")
        return result


def _validate_sorted_unique_strings(values: Any, label: str) -> None:
    if type(values) is not tuple or any(
        type(value) is not str or not value for value in values
    ):
        raise ResearchRunRootError(f"{label} must be a tuple of nonempty strings")
    if len(values) > MAX_RUN_ROOT_CODES:
        raise ResearchRunRootError(f"{label} exceeds the resource limit")
    for value in values:
        _require_nonempty_string(value, label)
    if values != tuple(sorted(values)):
        raise ResearchRunRootError(f"{label} must be sorted")
    if len(set(values)) != len(values):
        raise ResearchRunRootError(f"{label} must not contain duplicates")


def artifact_ref_from_path(
    path: str | Path,
    artifact_root: str | Path,
    *,
    media_type: str,
    required: bool = True,
) -> ArtifactRefV1:
    """Create an AVAILABLE artifact reference using a normalized relative label."""

    root = Path(artifact_root).resolve()
    candidate = Path(path).resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ResearchRunRootError("artifact is outside the supplied root") from exc
    if not candidate.is_file():
        raise ResearchRunRootError(f"artifact is missing or not a file: {candidate}")
    return ArtifactRefV1(
        label=relative.as_posix(),
        media_type=media_type,
        content_sha256=_sha256_file(candidate),
        byte_count=candidate.stat().st_size,
        required=required,
        availability="AVAILABLE",
    )


def build_research_run_root(
    *,
    trace_path: str | Path,
    claim_packet_id: str,
    family_id: str,
    source_manifest_root: str,
    claim_manifest_root: str,
    source_intake_receipt_id: str,
    terminal_status: str,
    artifact_manifest: Iterable[ArtifactRefV1],
    refusal_codes: Iterable[str] = (),
    unresolved_obligations: Iterable[str] = (),
    evidence_profile: str = "ReplayableLabEvidence",
    oesos_event_root: str | None = None,
    oesos_runtime_root: str | None = None,
    oesos_wire_root: str | None = None,
    oesos_bridge_root: str | None = None,
) -> ResearchRunRootV1:
    """Build a normalized run root directly from a TraceLogger JSONL artifact."""

    _, dda_root = semantic_dda_from_trace(trace_path)
    artifacts = tuple(sorted(tuple(artifact_manifest), key=lambda ref: ref.label))
    trace_candidate = Path(trace_path)
    if not trace_candidate.is_file():
        raise ResearchRunRootError(f"semantic trace is missing: {trace_candidate}")
    trace_digest = _sha256_file(trace_candidate)
    trace_size = trace_candidate.stat().st_size
    matching_trace_refs = tuple(
        ref
        for ref in artifacts
        if ref.media_type == DDA_TRACE_MEDIA_TYPE
        and ref.required
        and ref.availability == "AVAILABLE"
        and ref.content_sha256 == trace_digest
        and ref.byte_count == trace_size
    )
    if len(matching_trace_refs) != 1:
        raise ResearchRunRootError(
            "trace_path bytes must match exactly one required AVAILABLE "
            "application/x-core-dda-trace+jsonl artifact"
        )
    return ResearchRunRootV1(
        claim_packet_id=claim_packet_id,
        family_id=family_id,
        source_manifest_root=source_manifest_root,
        claim_manifest_root=claim_manifest_root,
        source_intake_receipt_id=source_intake_receipt_id,
        terminal_status=terminal_status,
        semantic_dda_root=dda_root,
        semantic_trace_label=matching_trace_refs[0].label,
        artifact_manifest=artifacts,
        refusal_codes=tuple(sorted(tuple(refusal_codes))),
        unresolved_obligations=tuple(sorted(tuple(unresolved_obligations))),
        evidence_profile=evidence_profile,
        oesos_event_root=oesos_event_root,
        oesos_runtime_root=oesos_runtime_root,
        oesos_wire_root=oesos_wire_root,
        oesos_bridge_root=oesos_bridge_root,
    )


def write_research_run_root(
    run_root: ResearchRunRootV1,
    output_directory: str | Path,
    *,
    filename_prefix: str = "research_run_root_v1",
) -> Path:
    """Exclusively write a root-id-named JSON receipt and verify collisions."""

    if type(run_root) is not ResearchRunRootV1:
        raise ResearchRunRootError("run_root must be ResearchRunRootV1")
    if (
        type(filename_prefix) is not str
        or not filename_prefix
        or re.fullmatch(r"[A-Za-z0-9_.-]+", filename_prefix) is None
    ):
        raise ResearchRunRootError("filename_prefix contains unsafe characters")
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(run_root.to_dict(), indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    content_root = hashlib.sha256(encoded).hexdigest()
    path = directory / f"{filename_prefix}_{content_root}.json"
    try:
        with path.open("xb") as handle:
            handle.write(encoded)
    except FileExistsError:
        try:
            existing = path.read_bytes()
        except OSError as exc:
            raise ResearchRunRootError(
                f"cannot inspect run-root collision: {path}"
            ) from exc
        if existing != encoded:
            raise ResearchRunRootError(f"content-addressed run-root collision: {path}")
    return path


def read_research_run_root(path: str | Path) -> ResearchRunRootV1:
    """Read and strictly verify a serialized research run root."""

    candidate = Path(path)
    try:
        value = _loads_json(candidate.read_text(encoding="utf-8"), str(candidate))
    except (OSError, UnicodeError) as exc:
        raise ResearchRunRootError(
            f"cannot read research run root: {candidate}"
        ) from exc
    return ResearchRunRootV1.from_dict(value)


def _verify_research_terminal_semantics(
    run_root: ResearchRunRootV1,
    payload: Any,
    intake: Any,
    trace_records: tuple[dict[str, Any], ...],
) -> None:
    allowed_statuses = _FAMILY_TERMINAL_STATUSES.get(payload.family)
    if allowed_statuses is None or run_root.terminal_status not in allowed_statuses:
        raise ResearchRunRootError(
            "research family and terminal_status do not reconcile"
        )
    payload_obligations = tuple(
        sorted(
            {
                obligation
                for claim in payload.claims
                for obligation in claim.unresolved_obligations
            }
        )
    )
    if run_root.unresolved_obligations != payload_obligations:
        raise ResearchRunRootError(
            "run-root obligations do not match the research claims"
        )

    letters = tuple(record["letter"] for record in trace_records)
    refused = run_root.terminal_status == "REFUSED"
    if payload.disposition == "refuse_unsupported" and not refused:
        raise ResearchRunRootError("unsupported research disposition was promoted")
    if payload.family in _REFUSAL_FAMILIES and run_root.oesos_event_root is not None:
        raise ResearchRunRootError("refusal-only family cannot claim OESOS roots")
    if refused:
        if (
            run_root.evidence_profile != "RefusalOnly"
            or not run_root.refusal_codes
            or len(letters) < 2
            or letters[-2:] != ("Z", "T")
        ):
            raise ResearchRunRootError(
                "refused run lacks a typed Z refusal and RefusalOnly profile"
            )
    elif (
        payload.disposition != "evaluate_finite"
        or run_root.evidence_profile != "LocalReplayableFiniteEvidence"
        or "Z" in letters
        or "E" not in letters
        or len(letters) < 2
        or letters[-2:] != ("I", "T")
    ):
        raise ResearchRunRootError("finite closed run lacks E.I.T success semantics")

    source_unverified_status = run_root.terminal_status.endswith("SOURCE_UNVERIFIED")
    external_status = run_root.terminal_status.endswith(
        "EXTERNAL_SOURCE_BYTES_REQUIRED"
    )
    has_external_source = any(
        not receipt.repository_tracked_expected for receipt in intake.receipts
    )
    if not refused:
        if intake.all_verified is source_unverified_status:
            raise ResearchRunRootError(
                "source verification state and terminal_status do not reconcile"
            )
        if external_status != (intake.all_verified and has_external_source):
            raise ResearchRunRootError(
                "external-source fence and terminal_status do not reconcile"
            )


def verify_research_run_root(
    run_root: ResearchRunRootV1,
    artifact_root: str | Path | None = None,
) -> bool:
    """Recompute identity and, when requested, rehash every AVAILABLE artifact."""

    if type(run_root) is not ResearchRunRootV1:
        raise ResearchRunRootError("run_root must be ResearchRunRootV1")
    ResearchRunRootV1.from_dict(run_root.to_dict())
    if artifact_root is None:
        return True
    root = Path(artifact_root).resolve()
    for ref in run_root.artifact_manifest:
        if ref.availability != "AVAILABLE":
            continue
        candidate = root.joinpath(*PurePosixPath(ref.label).parts).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ResearchRunRootError(
                f"artifact escapes the supplied root: {ref.label}"
            ) from exc
        if not candidate.is_file():
            raise ResearchRunRootError(f"available artifact is missing: {ref.label}")
        if candidate.stat().st_size != ref.byte_count:
            raise ResearchRunRootError(f"artifact byte count changed: {ref.label}")
        if _sha256_file(candidate) != ref.content_sha256:
            raise ResearchRunRootError(f"artifact digest changed: {ref.label}")
    packet_ref = next(
        ref
        for ref in run_root.artifact_manifest
        if ref.media_type == RESEARCH_PACKET_MEDIA_TYPE
        and ref.required
        and ref.availability == "AVAILABLE"
    )
    intake_ref = next(
        ref
        for ref in run_root.artifact_manifest
        if ref.media_type == SOURCE_INTAKE_MEDIA_TYPE
        and ref.required
        and ref.availability == "AVAILABLE"
    )
    packet_path = root.joinpath(*PurePosixPath(packet_ref.label).parts)
    intake_path = root.joinpath(*PurePosixPath(intake_ref.label).parts)
    try:
        from pfp.domain import PacketEnvelopeV2

        from .research_claim import (
            SourceIntakeBundleV1,
            parse_research_claim_envelope,
        )

        packet_wire = _loads_json(
            packet_path.read_text(encoding="utf-8"),
            "research packet artifact",
        )
        intake_wire = _loads_json(
            intake_path.read_text(encoding="utf-8"),
            "source intake artifact",
        )
        packet = PacketEnvelopeV2.from_dict(packet_wire)
        payload = parse_research_claim_envelope(packet)
        intake = SourceIntakeBundleV1.from_dict(intake_wire)
    except Exception as exc:
        raise ResearchRunRootError(
            "research packet or source-intake artifact failed strict replay"
        ) from exc
    if (
        packet.packet_id != run_root.claim_packet_id
        or payload.family != run_root.family_id
        or payload.source_manifest_root != run_root.source_manifest_root
        or payload.claim_manifest_root != run_root.claim_manifest_root
        or intake.packet_id != packet.packet_id
        or intake.source_manifest_root != payload.source_manifest_root
        or intake.receipt_id != run_root.source_intake_receipt_id
    ):
        raise ResearchRunRootError(
            "research packet, intake, and run-root identities do not reconcile"
        )
    if len(intake.receipts) != len(payload.sources):
        raise ResearchRunRootError(
            "source-intake receipts do not reconcile with packet sources"
        )
    for source, receipt in zip(payload.sources, intake.receipts):
        if (
            receipt.source_id != source.source_id
            or receipt.path != source.path
            or receipt.normalization != source.normalization
            or receipt.expected_sha256 != source.sha256
            or receipt.expected_byte_count != source.byte_count
            or receipt.repository_tracked_expected
            is not source.repository_tracked_expected
        ):
            raise ResearchRunRootError(
                "source-intake receipts do not reconcile with packet sources"
            )
    trace_path = root.joinpath(*PurePosixPath(run_root.semantic_trace_label).parts)
    trace_records = _read_validated_trace_records(trace_path)
    semantic_steps = tuple(
        _semantic_step_from_record(record, number)
        for number, record in enumerate(trace_records, start=1)
    )
    recomputed_dda_root = semantic_dda_root(semantic_steps)
    if recomputed_dda_root != run_root.semantic_dda_root:
        raise ResearchRunRootError(
            "semantic trace does not match the bound semantic_dda_root"
        )
    _verify_research_terminal_semantics(run_root, payload, intake, trace_records)
    if run_root.oesos_event_root is not None:
        bundle_ref = next(
            ref
            for ref in run_root.artifact_manifest
            if ref.media_type == OESOS_EVIDENCE_BUNDLE_MEDIA_TYPE
            and ref.required
            and ref.availability == "AVAILABLE"
        )
        bundle_path = root.joinpath(*PurePosixPath(bundle_ref.label).parts)
        try:
            from pfp.domain.entities.oesos_evidence_bundle import (
                read_oesos_evidence_bundle,
                verify_oesos_evidence_bundle,
            )

            bundle = read_oesos_evidence_bundle(bundle_path)
            verify_oesos_evidence_bundle(
                bundle,
                expected_research_parent_packet_id=packet.packet_id,
            )
        except Exception as exc:
            raise ResearchRunRootError(
                "OESOS evidence bundle failed strict replay"
            ) from exc
        if (
            bundle.evaluation_receipt.event_root != run_root.oesos_event_root
            or bundle.runtime_problem.runtime_id != run_root.oesos_runtime_root
            or bundle.wire_receipt_id != run_root.oesos_wire_root
        ):
            raise ResearchRunRootError(
                "OESOS evidence bundle does not reconcile with run-root identities"
            )
        if any(record["letter"] == "E" for record in trace_records) and (
            bundle.evaluation_receipt.terminal_status != "LabExactCandidate"
            or bundle.evaluation_receipt.active_obstructions
        ):
            raise ResearchRunRootError(
                "outer E step is not backed by an exact OESOS receipt"
            )
    return True


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise ResearchRunRootError(f"cannot hash artifact: {path}") from exc
    return digest.hexdigest()





