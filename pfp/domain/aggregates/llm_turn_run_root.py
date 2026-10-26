"""Pure domain models and constraints for LLM turn packets.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from omega_engine_pfp.domain.shared_kernel.canonical import (
    CanonicalizationError,
    domain_digest,
)
from omega_engine_pfp.domain.validation import (
    MAX_ARRAY_LENGTH,
    MAX_ID_LENGTH,
    MAX_STRING_LENGTH,
    _fail,
    _require_digest,
    _require_exact_dict,
    _require_fields,
    _require_nonnegative_int,
    _require_optional_digest,
    _require_positive_int,
    _require_stable_id,
    _require_string,
)

LLM_TURN_SCHEMA = "omega.symbol-game.llm-turn.v1"
LLM_TURN_CONTENT_SCHEMA = "omega.symbol-game.llm-turn-content.v1"
LLM_TURN_RUN_ROOT_SCHEMA = "omega.symbol-game.llm-turn-run-root.v1"
LLM_TURN_ATTEMPT_SCHEMA = "omega.symbol-game.llm-turn-attempt.v1"

LLM_TURN_PACKET_FAMILY = "llm_turn_v1"
LLM_TURN_FAMILY = "llm_turn"

PAYLOAD_DOMAIN = "omega.symbol-game.llm-turn-payload.v1"
CONTENT_DOMAIN = "omega.symbol-game.llm-turn-content.v1"
RUN_ROOT_DOMAIN = "omega.symbol-game.llm-turn-run-root.v1"
TURN_MANIFEST_DOMAIN = "omega.symbol-game.llm-turn-manifest.v1"

LLM_TURN_TERMINAL_TARGET = "TypedTurnOrProsePromptRefused"
LLM_TURN_EVIDENCE_CEILING = "ReplayableLabEvidence"
LLM_TURN_ORACLE_POLICY = "IndependentHostEvaluationRequired"

LLM_TURN_ENVELOPE_CONSTRAINTS = (
    "authority_effect_none",
    "objective_bound",
    "budgets_bound",
    "parent_packet_id_bound",
    "model_verdicts_untrusted",
    "consequential_turns_require_packet",
)

ALLOWED_ROLES = frozenset({"user", "assistant", "system", "tool"})
ALLOWED_TURN_KINDS = frozenset(
    {
        "prose",
        "code_change",
        "claimed_result",
        "tool_result",
        "status",
    }
)
CONSEQUENTIAL_TURN_KINDS = frozenset({"code_change", "claimed_result"})
REQUIRED_REPLY_FIELD_IDS = frozenset(
    {
        "PACKET_ID",
        "PARENT",
        "CANDIDATE",
        "RUN_ROOT",
        "OPEN_OBSTRUCTIONS",
        "AUTHORITY_EFFECT",
        "RESIDUAL_COLOUR",
    }
)
DEFAULT_REQUIRED_REPLY_FIELDS = (
    "AUTHORITY_EFFECT",
    "CANDIDATE",
    "OPEN_OBSTRUCTIONS",
    "PACKET_ID",
    "PARENT",
    "RESIDUAL_COLOUR",
    "RUN_ROOT",
)
RUN_ROOT_TERMINAL_STATUSES = frozenset(
    {
        "BudgetExhausted",
        "InvalidPacket",
        "OpenEvaluation",
        "PacketizedTurn",
        "ProsePromptRefused",
        "TransportValidated",
        "TypedRefusal",
    }
)
ATTEMPT_DISPOSITIONS = frozenset(
    {
        "AcceptedForEvaluation",
        "BudgetExhausted",
        "Refused",
    }
)

MAX_CANDIDATE_BUDGET = 32
MAX_OPERATION_BUDGET = 4096
MAX_CANONICAL_PAYLOAD_BYTES = 256 * 1024
MAX_CONTENT_BYTES = 1024 * 1024
MAX_REFUSALS = 256
MAX_ATTEMPTS = 64

REFUSAL_PROSE_PROMPT_REFUSED = "PROSE_PROMPT_REFUSED"
REFUSAL_MISSING_REPLY_FIELD = "MISSING_REPLY_FIELD"
REFUSAL_CONTENT_DIGEST_MISMATCH = "CONTENT_DIGEST_MISMATCH"
REFUSAL_CANDIDATE_BUDGET_EXCEEDED = "CANDIDATE_BUDGET_EXCEEDED"
REFUSAL_OPERATION_BUDGET_EXCEEDED = "OPERATION_BUDGET_EXCEEDED"
REFUSAL_MODEL_VERDICT_UNTRUSTED = "MODEL_VERDICT_UNTRUSTED"
REFUSAL_MARKDOWN_CLAIM_INJECTION = "MARKDOWN_CLAIM_INJECTION"
REFUSAL_REFUSAL_ERASURE = "REFUSAL_ERASURE"
REFUSAL_AUTHORITY_NON_NONE = "AUTHORITY_EFFECT_NON_NONE"
REFUSAL_CONSEQUENTIAL_WITHOUT_PACKET = "CONSEQUENTIAL_WITHOUT_PACKET"
REFUSAL_INVALID_MACHINE_BLOCK = "INVALID_MACHINE_BLOCK"
REFUSAL_PACKET_ID_ABSENT = "PACKET_ID_ABSENT_WITH_KNOWN_PACKET"
REFUSAL_PARENT_ABSENT = "PARENT_ABSENT_WITH_KNOWN_PARENT"
REFUSAL_MACHINE_FIELD_ORDER = "MACHINE_FIELD_ORDER_INVALID"
REFUSAL_REPLY_NOT_BOUND = "REPLY_TEXT_NOT_BOUND_TO_CANDIDATE"
REFUSAL_VERIFIED_PROPOSAL_FORBIDDEN = "VERIFIED_PROPOSAL_FORBIDDEN"
REFUSAL_TERMINAL_NOT_DERIVED = "TERMINAL_NOT_DERIVED_FROM_EVIDENCE"
REFUSAL_CANDIDATE_CONTENT_MISBIND = "CANDIDATE_CONTENT_MISBIND"
REFUSAL_ATTEMPT_ID_MISBIND = "ATTEMPT_ID_MISBIND"
REFUSAL_CONTENT_BYTES_REQUIRED = "CONTENT_BYTES_REQUIRED_FOR_CONSEQUENTIAL"
REFUSAL_REPLY_REQUIRED = "REPLY_TEXT_REQUIRED_FOR_CONSEQUENTIAL"
REFUSAL_POSITIVE_TERMINAL_NEEDS_REPLAY = "POSITIVE_TERMINAL_NEEDS_EVIDENCE_REPLAY"
REFUSAL_EXACT_WITHOUT_DUAL_WITNESS = "EXACT_WITHOUT_DUAL_WITNESS"
REFUSAL_EXACT_RESIDUAL_WITHOUT_DUAL_WITNESS = "EXACT_RESIDUAL_WITHOUT_DUAL_WITNESS"
REFUSAL_HOST_BINDING_OPEN = "HOST_BINDING_OPEN"
OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED = "CLAIM_EVALUATOR_RECEIPT_REQUIRED"
POSITIVE_LLM_TERMINALS = frozenset({"TransportValidated", "PacketizedTurn"})


def _canonical_json_size(value: Any) -> int:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CanonicalizationError("value is not strict JSON data") from exc
    return len(encoded)


def _validate_ordered_unique_strings(
    value: Any, label: str, *, maximum: int = MAX_ARRAY_LENGTH
) -> tuple[str, ...]:
    if type(value) is not tuple or any(type(item) is not str for item in value):
        _fail(f"{label} must be an exact tuple of strings")
    if len(value) > maximum:
        _fail(f"{label} exceeds the array resource limit")
    for index, item in enumerate(value):
        _require_string(item, f"{label}[{index}]", nonempty=True)
    if tuple(sorted(value)) != value or len(value) != len(set(value)):
        _fail(f"{label} must be unique and sorted")
    return value


def _string_tuple_from_wire(
    value: Any, label: str, *, maximum: int = MAX_ARRAY_LENGTH
) -> tuple[str, ...]:
    if type(value) is not list:
        _fail(f"{label} must be an array")
    if len(value) > maximum:
        _fail(f"{label} exceeds the array resource limit")
    result = tuple(
        _require_string(item, f"{label}[{index}]", nonempty=True)
        for index, item in enumerate(value)
    )
    return _validate_ordered_unique_strings(result, label, maximum=maximum)


def _turn_manifest_root(
    *,
    objective: str,
    role: str,
    turn_kind: str,
    content_sha256: str,
    parent_packet_id: str | None,
    conversation_root_id: str | None,
) -> str:
    return domain_digest(
        TURN_MANIFEST_DOMAIN,
        {
            "content_sha256": content_sha256,
            "conversation_root_id": conversation_root_id,
            "objective": objective,
            "parent_packet_id": parent_packet_id,
            "role": role,
            "turn_kind": turn_kind,
        },
    )


from omega_engine_pfp.domain.value_objects import (
    LlmPayloadV1,
    LlmTurnPayloadV1,
)


@dataclass(frozen=True, slots=True)
class LlmTurnContentArtifactV1:
    """Immutable content-addressed binding for one turn body."""

    packet_id: str
    producer_id: str
    content_encoding: str
    content_sha256: str
    content_byte_count: int
    claimed_summary: str | None = None
    schema_version: str = field(default=LLM_TURN_CONTENT_SCHEMA)
    authority_effect: str = field(default="None")
    explicit_task_id: str | None = None
    explicit_payload: Any = None

    def __post_init__(self) -> None:
        _require_digest(self.packet_id, "packet_id")
        _require_stable_id(self.producer_id, "producer_id")
        _require_string(self.content_encoding, "content_encoding", nonempty=True)
        if self.content_encoding != "utf8-lf-v1":
            _fail("content_encoding is unsupported")
        _require_digest(self.content_sha256, "content_sha256")
        _require_nonnegative_int(self.content_byte_count, "content_byte_count")
        if self.content_byte_count > MAX_CONTENT_BYTES:
            _fail("content_byte_count exceeds the content resource limit")
        if self.claimed_summary is not None:
            _require_string(self.claimed_summary, "claimed_summary")
        if self.schema_version != LLM_TURN_CONTENT_SCHEMA:
            _fail("llm-turn content schema version is unsupported")
        if self.authority_effect != "None":
            _fail("llm-turn content artifacts must carry AuthorityEffect None")

    @property
    def task_id(self) -> str:
        if self.explicit_task_id is not None:
            return self.explicit_task_id
        return self.task_packet_id

    @property
    def payload(self) -> Any:
        return self.explicit_payload

    def identity_fields(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "packet_id": self.packet_id,
            "producer_id": self.producer_id,
            "content_encoding": self.content_encoding,
            "content_sha256": self.content_sha256,
            "content_byte_count": self.content_byte_count,
            "claimed_summary": self.claimed_summary,
            "authority_effect": self.authority_effect,
        }

    @property
    def content_id(self) -> str:
        return domain_digest(CONTENT_DOMAIN, self.identity_fields())

    def to_dict(self) -> dict[str, Any]:
        return {
            "content_id": self.content_id,
            **self.identity_fields(),
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "LlmTurnContentArtifactV1":
        wire = _require_exact_dict(wire, "llm-turn content artifact")
        if "passed" in wire or "promotion_eligible" in wire or "verified" in wire:
            _fail("content artifact carries forbidden authority-bearing fields")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "content_id",
                    "packet_id",
                    "producer_id",
                    "content_encoding",
                    "content_sha256",
                    "content_byte_count",
                    "claimed_summary",
                    "authority_effect",
                }
            ),
            "llm-turn content artifact",
        )
        expected = _require_digest(wire["content_id"], "content_id")
        artifact = cls(
            packet_id=_require_digest(wire["packet_id"], "packet_id"),
            producer_id=_require_stable_id(wire["producer_id"], "producer_id"),
            content_encoding=_require_string(
                wire["content_encoding"], "content_encoding", nonempty=True
            ),
            content_sha256=_require_digest(wire["content_sha256"], "content_sha256"),
            content_byte_count=_require_nonnegative_int(
                wire["content_byte_count"], "content_byte_count"
            ),
            claimed_summary=(
                None
                if wire["claimed_summary"] is None
                else _require_string(wire["claimed_summary"], "claimed_summary")
            ),
            schema_version=_require_string(
                wire["schema_version"], "schema_version", nonempty=True
            ),
            authority_effect=_require_string(
                wire["authority_effect"], "authority_effect", nonempty=True
            ),
        )
        if expected != artifact.content_id:
            _fail("content_id does not match canonical wire content")
        return artifact


@dataclass(frozen=True, slots=True)
class LlmTurnAttemptV1:
    """One attach/evaluate attempt against an llm_turn packet."""

    attempt_index: int
    candidate_id: str
    content_id: str
    operation_count: int
    disposition: str
    refusal_codes: tuple[str, ...]
    schema_version: str = field(default=LLM_TURN_ATTEMPT_SCHEMA)
    authority_effect: str = field(default="None")
    explicit_task_id: str | None = None
    explicit_payload: Any = None

    def __post_init__(self) -> None:
        if type(self.attempt_index) is not int or self.attempt_index < 0:
            _fail("attempt_index must be a nonnegative integer")
        _require_digest(self.candidate_id, "candidate_id")
        _require_digest(self.content_id, "content_id")
        _require_nonnegative_int(self.operation_count, "operation_count")
        _require_string(self.disposition, "attempt disposition", nonempty=True)
        if self.disposition not in ATTEMPT_DISPOSITIONS:
            _fail("attempt disposition is unsupported")
        codes = _validate_ordered_unique_strings(
            self.refusal_codes, "attempt refusal_codes", maximum=MAX_REFUSALS
        )
        object.__setattr__(self, "refusal_codes", codes)
        if self.disposition == "AcceptedForEvaluation" and codes:
            _fail("accepted attempts cannot carry refusal codes")
        if self.disposition != "AcceptedForEvaluation" and not codes:
            _fail("refused/budget attempts require refusal codes")
        if self.schema_version != LLM_TURN_ATTEMPT_SCHEMA:
            _fail("attempt schema version is unsupported")
        if self.authority_effect != "None":
            _fail("attempts must carry AuthorityEffect None")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "attempt_index": self.attempt_index,
            "candidate_id": self.candidate_id,
            "content_id": self.content_id,
            "operation_count": self.operation_count,
            "disposition": self.disposition,
            "refusal_codes": list(self.refusal_codes),
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "LlmTurnAttemptV1":
        wire = _require_exact_dict(wire, "llm-turn attempt")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "attempt_index",
                    "candidate_id",
                    "content_id",
                    "operation_count",
                    "disposition",
                    "refusal_codes",
                    "authority_effect",
                }
            ),
            "llm-turn attempt",
        )
        return cls(
            attempt_index=_require_nonnegative_int(
                wire["attempt_index"], "attempt_index"
            ),
            candidate_id=_require_digest(wire["candidate_id"], "candidate_id"),
            content_id=_require_digest(wire["content_id"], "content_id"),
            operation_count=_require_nonnegative_int(
                wire["operation_count"], "operation_count"
            ),
            disposition=_require_string(
                wire["disposition"], "attempt disposition", nonempty=True
            ),
            refusal_codes=_string_tuple_from_wire(
                wire["refusal_codes"], "attempt refusal_codes", maximum=MAX_REFUSALS
            ),
            schema_version=_require_string(
                wire["schema_version"], "schema_version", nonempty=True
            ),
            authority_effect=_require_string(
                wire["authority_effect"], "authority_effect", nonempty=True
            ),
        )


@dataclass(frozen=True, slots=True)
class LlmTurnRunRootV1:
    """Complete llm-turn run root linking task, candidates, and terminal."""

    task_packet_id: str
    task_packet_sha256: str
    turn_kind: str
    candidate_ids: tuple[str, ...]
    content_ids: tuple[str, ...]
    attempts: tuple[LlmTurnAttemptV1, ...]
    refusals: tuple[str, ...]
    terminal_status: str
    open_obstruction_ids: tuple[str, ...]
    schema_version: str = field(default=LLM_TURN_RUN_ROOT_SCHEMA)
    authority_effect: str = field(default="None")
    explicit_task_id: str | None = None
    explicit_payload: Any = None

    def __post_init__(self) -> None:
        _require_digest(self.task_packet_id, "task_packet_id")
        _require_digest(self.task_packet_sha256, "task_packet_sha256")
        _require_string(self.turn_kind, "turn_kind", nonempty=True)
        if self.turn_kind not in ALLOWED_TURN_KINDS:
            _fail("turn_kind is unsupported")
        candidates = _validate_ordered_unique_strings(
            self.candidate_ids, "candidate_ids", maximum=MAX_CANDIDATE_BUDGET
        )
        contents = _validate_ordered_unique_strings(
            self.content_ids, "content_ids", maximum=MAX_CANDIDATE_BUDGET
        )
        object.__setattr__(self, "candidate_ids", candidates)
        object.__setattr__(self, "content_ids", contents)
        if type(self.attempts) is not tuple or any(
            not isinstance(item, LlmTurnAttemptV1) for item in self.attempts
        ):
            _fail("attempts must be a tuple of LlmTurnAttemptV1")
        if len(self.attempts) > MAX_ATTEMPTS:
            _fail("attempts exceed the resource limit")
        for index, attempt in enumerate(self.attempts):
            if attempt.attempt_index != index:
                _fail("attempts must be contiguous and zero-indexed")
        refusals = _validate_ordered_unique_strings(
            self.refusals, "refusals", maximum=MAX_REFUSALS
        )
        object.__setattr__(self, "refusals", refusals)
        _require_string(self.terminal_status, "terminal_status", nonempty=True)
        if self.terminal_status == "VerifiedProposal":
            _fail(REFUSAL_VERIFIED_PROPOSAL_FORBIDDEN)
        if self.terminal_status not in RUN_ROOT_TERMINAL_STATUSES:
            _fail("terminal_status is unsupported")
        open_ids = _validate_ordered_unique_strings(
            self.open_obstruction_ids,
            "open_obstruction_ids",
            maximum=MAX_REFUSALS,
        )
        object.__setattr__(self, "open_obstruction_ids", open_ids)
        if self.terminal_status in {"TransportValidated", "PacketizedTurn"}:
            if not candidates or not contents or not self.attempts:
                _fail(
                    "TransportValidated/PacketizedTurn requires candidates, "
                    "content, and attempts"
                )
            if refusals:
                _fail(
                    "TransportValidated/PacketizedTurn cannot retain refusals"
                )
        if self.terminal_status == "TransportValidated" and open_ids:
            _fail("TransportValidated cannot retain open obstructions")
        if self.terminal_status == "TypedRefusal" and not refusals:
            _fail("TypedRefusal requires at least one refusal code")
        if self.terminal_status == "ProsePromptRefused" and (
            REFUSAL_PROSE_PROMPT_REFUSED not in refusals
        ):
            _fail("ProsePromptRefused requires PROSE_PROMPT_REFUSED")
        if self.schema_version != LLM_TURN_RUN_ROOT_SCHEMA:
            _fail("llm-turn run root schema version is unsupported")
        if self.authority_effect != "None":
            _fail("llm-turn run roots must carry AuthorityEffect None")

    @property
    def task_id(self) -> str:
        if self.explicit_task_id is not None:
            return self.explicit_task_id
        return self.task_packet_id

    @property
    def payload(self) -> Any:
        return self.explicit_payload

    def identity_fields(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "task_packet_id": self.task_packet_id,
            "task_packet_sha256": self.task_packet_sha256,
            "turn_kind": self.turn_kind,
            "candidate_ids": list(self.candidate_ids),
            "content_ids": list(self.content_ids),
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "refusals": list(self.refusals),
            "terminal_status": self.terminal_status,
            "open_obstruction_ids": list(self.open_obstruction_ids),
            "authority_effect": self.authority_effect,
        }

    @property
    def run_root_id(self) -> str:
        return domain_digest(RUN_ROOT_DOMAIN, self.identity_fields())

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_root_id": self.run_root_id,
            **self.identity_fields(),
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "LlmTurnRunRootV1":
        wire = _require_exact_dict(wire, "llm-turn run root")
        if "passed" in wire or "promotion_eligible" in wire or "verified" in wire:
            _fail("run root carries forbidden authority-bearing fields")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "run_root_id",
                    "task_packet_id",
                    "task_packet_sha256",
                    "turn_kind",
                    "candidate_ids",
                    "content_ids",
                    "attempts",
                    "refusals",
                    "terminal_status",
                    "open_obstruction_ids",
                    "authority_effect",
                }
            ),
            "llm-turn run root",
        )
        expected = _require_digest(wire["run_root_id"], "run_root_id")
        raw_attempts = wire["attempts"]
        if type(raw_attempts) is not list or len(raw_attempts) > MAX_ATTEMPTS:
            _fail("attempts must be a bounded array")
        root = cls(
            task_packet_id=_require_digest(wire["task_packet_id"], "task_packet_id"),
            task_packet_sha256=_require_digest(
                wire["task_packet_sha256"], "task_packet_sha256"
            ),
            turn_kind=_require_string(wire["turn_kind"], "turn_kind", nonempty=True),
            candidate_ids=_string_tuple_from_wire(
                wire["candidate_ids"],
                "candidate_ids",
                maximum=MAX_CANDIDATE_BUDGET,
            ),
            content_ids=_string_tuple_from_wire(
                wire["content_ids"], "content_ids", maximum=MAX_CANDIDATE_BUDGET
            ),
            attempts=tuple(LlmTurnAttemptV1.from_dict(item) for item in raw_attempts),
            refusals=_string_tuple_from_wire(
                wire["refusals"], "refusals", maximum=MAX_REFUSALS
            ),
            terminal_status=_require_string(
                wire["terminal_status"], "terminal_status", nonempty=True
            ),
            open_obstruction_ids=_string_tuple_from_wire(
                wire["open_obstruction_ids"],
                "open_obstruction_ids",
                maximum=MAX_REFUSALS,
            ),
            schema_version=_require_string(
                wire["schema_version"], "schema_version", nonempty=True
            ),
            authority_effect=_require_string(
                wire["authority_effect"], "authority_effect", nonempty=True
            ),
        )
        if expected != root.run_root_id:
            _fail("run_root_id does not match canonical wire content")
        return root





from omega_engine_pfp.domain.shared_kernel.canonical import thaw, freeze, canonical_bytes, canonical_wire, canonical_unwire, domain_digest
from omega_engine_pfp.domain.entities.candidate_artifact import CandidateArtifactV1
from omega_engine_pfp.domain.entities.packet_envelope import PacketEnvelopeV2
from omega_engine_pfp.domain.aggregates.research_claim import canonical_json_artifact_bytes


# Presenter
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_STABLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")

_MACHINE_FIELD_ORDER = (
    "PACKET_ID",
    "PARENT",
    "CANDIDATE",
    "RUN_ROOT",
    "OPEN_OBSTRUCTIONS",
    "RESIDUAL_COLOUR",
    "AUTHORITY_EFFECT",
)


def _duplicate_rejecting_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def loads_strict_json(text: str, label: str = "JSON") -> Any:
    """Parse JSON while refusing duplicate keys and non-finite constants."""

    def _reject_constant(value: str) -> None:
        _fail(f"non-finite JSON number is refused: {value}")

    try:
        return json.loads(
            text,
            object_pairs_hook=_duplicate_rejecting_object,
            parse_constant=_reject_constant,
        )
    except CanonicalizationError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise CanonicalizationError(f"invalid JSON in {label}") from exc


def parse_machine_reply_block(text: str) -> dict[str, str]:
    """Parse the leading machine field block from an assistant reply.

    Expected exact order (first non-empty lines)::

        PACKET_ID=<hex64>
        PARENT=<hex64|ABSENT>
        CANDIDATE=<hex64|ABSENT>
        RUN_ROOT=<hex64|ABSENT>
        OPEN_OBSTRUCTIONS=<csv|none>
        RESIDUAL_COLOUR=<Open|Closed|Exact>
        AUTHORITY_EFFECT=None
    """
    if type(text) is not str:
        raise TypeError("text must be a string")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    index = 0
    while index < len(lines) and lines[index].strip() == "":
        index += 1
    fields: dict[str, str] = {}
    order: list[str] = []
    while index < len(lines):
        line = lines[index].strip()
        if not line or "=" not in line:
            break
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key not in REQUIRED_REPLY_FIELD_IDS:
            break
        if key in fields:
            _fail(f"duplicate machine reply field: {key}")
        fields[key] = value
        order.append(key)
        index += 1
    fields["__order__"] = ",".join(order)
    return fields


def validate_machine_reply_fields(
    fields: Mapping[str, str],
    *,
    required: Sequence[str],
    expected_packet_id: str | None = None,
    expected_parent: str | None = None,
    phase: str = "proposal",
    expected_candidate_id: str | None = None,
    expected_run_root_id: str | None = None,
) -> tuple[str, ...]:
    """Return sorted refusal codes for a parsed machine block."""
    refusals: set[str] = set()
    order_raw = fields.get("__order__")
    clean = {key: value for key, value in fields.items() if key != "__order__"}
    present = frozenset(clean)
    for key in required:
        if key not in present:
            refusals.add(REFUSAL_MISSING_REPLY_FIELD)
            refusals.add(f"MISSING:{key}")
    if order_raw is not None:
        order = tuple(part for part in order_raw.split(",") if part)
        expected_order = tuple(key for key in _MACHINE_FIELD_ORDER if key in present)
        if order != expected_order:
            refusals.add(REFUSAL_MACHINE_FIELD_ORDER)
    authority = clean.get("AUTHORITY_EFFECT")
    if authority is not None and authority != "None":
        refusals.add(REFUSAL_AUTHORITY_NON_NONE)
    packet_id = clean.get("PACKET_ID")
    if packet_id is not None:
        if packet_id == "ABSENT":
            if expected_packet_id is not None:
                refusals.add(REFUSAL_PACKET_ID_ABSENT)
                refusals.add(REFUSAL_INVALID_MACHINE_BLOCK)
        elif _SHA256.fullmatch(packet_id) is None:
            refusals.add(REFUSAL_INVALID_MACHINE_BLOCK)
        elif expected_packet_id is not None and packet_id != expected_packet_id:
            refusals.add(REFUSAL_INVALID_MACHINE_BLOCK)
    parent = clean.get("PARENT")
    if parent is not None:
        if parent in {"ABSENT", "none"}:
            if expected_parent is not None:
                refusals.add(REFUSAL_PARENT_ABSENT)
                refusals.add(REFUSAL_INVALID_MACHINE_BLOCK)
        elif _SHA256.fullmatch(parent) is None:
            refusals.add(REFUSAL_INVALID_MACHINE_BLOCK)
        elif expected_parent is not None and parent != expected_parent:
            refusals.add(REFUSAL_INVALID_MACHINE_BLOCK)
    candidate = clean.get("CANDIDATE")
    run_root = clean.get("RUN_ROOT")
    if phase == "proposal":
        if candidate is not None and candidate not in {"ABSENT", "none"}:
            refusals.add(REFUSAL_INVALID_MACHINE_BLOCK)
            refusals.add("CANDIDATE_MUST_BE_ABSENT_IN_PROPOSAL_PHASE")
        if run_root is not None and run_root not in {"ABSENT", "none"}:
            refusals.add(REFUSAL_INVALID_MACHINE_BLOCK)
            refusals.add("RUN_ROOT_MUST_BE_ABSENT_IN_PROPOSAL_PHASE")
    else:
        if candidate is not None and candidate not in {"ABSENT", "none"}:
            if _SHA256.fullmatch(candidate) is None:
                refusals.add(REFUSAL_INVALID_MACHINE_BLOCK)
            elif (
                expected_candidate_id is not None
                and candidate != expected_candidate_id
            ):
                refusals.add(REFUSAL_INVALID_MACHINE_BLOCK)
        if run_root is not None and run_root not in {"ABSENT", "none"}:
            if _SHA256.fullmatch(run_root) is None:
                refusals.add(REFUSAL_INVALID_MACHINE_BLOCK)
            elif (
                expected_run_root_id is not None and run_root != expected_run_root_id
            ):
                refusals.add(REFUSAL_INVALID_MACHINE_BLOCK)
    open_obs = clean.get("OPEN_OBSTRUCTIONS")
    if open_obs is not None and open_obs not in {"none", "ABSENT", ""}:
        for token in open_obs.split(","):
            token = token.strip()
            if not token or _STABLE_ID.fullmatch(token) is None:
                refusals.add(REFUSAL_INVALID_MACHINE_BLOCK)
                refusals.add("OPEN_OBSTRUCTIONS_TOKEN_INVALID")
                break
    return tuple(sorted(refusals))


def render_llm_turn_run_root_markdown(root: LlmTurnRunRootV1) -> str:
    """Render a non-authoritative Markdown view of a verified run root."""
    if not isinstance(root, LlmTurnRunRootV1):
        raise TypeError("root must be a LlmTurnRunRootV1")
    lines = [
        "# LLM Turn Run Root",
        "",
        f"- run_root_id: `{root.run_root_id}`",
        f"- task_packet_id: `{root.task_packet_id}`",
        f"- task_packet_sha256: `{root.task_packet_sha256}`",
        f"- turn_kind: `{root.turn_kind}`",
        f"- terminal_status: `{root.terminal_status}`",
        f"- authority_effect: `{root.authority_effect}`",
        "",
        "## Candidates",
    ]
    if root.candidate_ids:
        for candidate_id in root.candidate_ids:
            lines.append(f"- `{candidate_id}`")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Content"])
    if root.content_ids:
        for content_id in root.content_ids:
            lines.append(f"- `{content_id}`")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Attempts"])
    if root.attempts:
        for attempt in root.attempts:
            lines.append(
                f"- attempt[{attempt.attempt_index}] disposition=`{attempt.disposition}` "
                f"candidate=`{attempt.candidate_id}` content=`{attempt.content_id}`"
            )
            if attempt.refusal_codes:
                lines.append(
                    "  refusals: "
                    + ", ".join(f"`{code}`" for code in attempt.refusal_codes)
                )
    else:
        lines.append("- (none)")
    lines.extend(["", "## Refusals"])
    if root.refusals:
        for code in root.refusals:
            lines.append(f"- `{code}`")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Open obstructions"])
    if root.open_obstruction_ids:
        for code in root.open_obstruction_ids:
            lines.append(f"- `{code}`")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append(
        "_This Markdown is a non-authoritative rendering. "
        "Machine state lives in the run root._"
    )
    lines.append("")
    return "\n".join(lines)


def verify_markdown_does_not_mutate_claims(
    root: LlmTurnRunRootV1, markdown: str
) -> None:
    """Fail closed if rendered Markdown erases a refusal or invents a claim."""
    if type(markdown) is not str:
        raise TypeError("markdown must be a string")
    for code in root.refusals:
        if f"`{code}`" not in markdown:
            _fail(REFUSAL_REFUSAL_ERASURE)
    forbidden_phrases = (
        "promotion_eligible",
        "promotion eligible",
        "trusted proposal",
        "verified safe to merge",
        "authority_effect: `Promote`",
        "authority_effect: Promote",
    )
    lowered = markdown.casefold()
    for phrase in forbidden_phrases:
        if phrase.casefold() in lowered:
            _fail(REFUSAL_MARKDOWN_CLAIM_INJECTION)
    if f"`{root.terminal_status}`" not in markdown:
        _fail(REFUSAL_MARKDOWN_CLAIM_INJECTION)
    if "`None`" not in markdown and "authority_effect: `None`" not in markdown:
        _fail(REFUSAL_MARKDOWN_CLAIM_INJECTION)




# Use Cases
def bind_content_bytes(
    *,
    packet_id: str,
    producer_id: str,
    content_bytes: bytes,
    claimed_summary: str | None = None,
    content_encoding: str = "utf8-lf-v1",
) -> LlmTurnContentArtifactV1:
    """Content-address immutable turn body bytes into a typed content artifact."""
    if type(content_bytes) is not bytes:
        raise TypeError("content_bytes must be exact bytes")
    if len(content_bytes) > MAX_CONTENT_BYTES:
        _fail("content_bytes exceeds the content resource limit")
    digest = hashlib.sha256(content_bytes).hexdigest()
    return LlmTurnContentArtifactV1(
        packet_id=packet_id,
        producer_id=producer_id,
        content_encoding=content_encoding,
        content_sha256=digest,
        content_byte_count=len(content_bytes),
        claimed_summary=claimed_summary,
    )


def verify_content_bytes(
    artifact: LlmTurnContentArtifactV1, content_bytes: bytes
) -> None:
    """Fail closed if supplied bytes do not match the content artifact binding."""
    if type(content_bytes) is not bytes:
        raise TypeError("content_bytes must be exact bytes")
    digest = hashlib.sha256(content_bytes).hexdigest()
    if (
        digest != artifact.content_sha256
        or len(content_bytes) != artifact.content_byte_count
    ):
        _fail(REFUSAL_CONTENT_DIGEST_MISMATCH)


def build_llm_turn_envelope(
    payload: LlmTurnPayloadV1,
    *,
    task_id: str,
    carrier_id: str = "omega-llm-turn-v1",
    step_budget: int | None = None,
) -> PacketEnvelopeV2:
    """Bind a typed llm-turn payload into the host-owned packet envelope."""
    if not isinstance(payload, LlmTurnPayloadV1):
        raise TypeError("payload must be a LlmTurnPayloadV1")
    _require_string(task_id, "task_id", nonempty=True)
    _require_string(carrier_id, "carrier_id", nonempty=True)
    budget = (
        int(payload.operation_budget)
        if step_budget is None
        else _require_positive_int(step_budget, "step_budget")
    )
    manifest = payload.turn_manifest_root
    return PacketEnvelopeV2(
        task_id=task_id,
        packet_family=LLM_TURN_PACKET_FAMILY,
        carrier_id=carrier_id,
        initial_state_hash=manifest,
        payload=payload.to_dict(),
        constraints=LLM_TURN_ENVELOPE_CONSTRAINTS,
        protected_boundaries=(
            "authority_effect",
            "promotion",
            "verified",
            "trusted",
        ),
        terminal_target=LLM_TURN_TERMINAL_TARGET,
        evidence_ceiling=LLM_TURN_EVIDENCE_CEILING,
        oracle_policy=LLM_TURN_ORACLE_POLICY,
        allowed_transforms=("emit_evidence", "evaluate"),
        step_budget=budget,
        framing_mode="strict",
        packet_kind="problem",
        parent_event_id=str(payload.parent_packet_id) if payload.parent_packet_id else None,
        source_digest=manifest,
        authority_effect="None",
    )


def parse_llm_turn_envelope(
    value: PacketEnvelopeV2 | Mapping[str, Any],
) -> LlmTurnPayloadV1:
    """Strictly parse and cross-check an llm-turn envelope and payload."""
    if isinstance(value, PacketEnvelopeV2):
        envelope = PacketEnvelopeV2.from_dict(value.to_dict())
    else:
        envelope = PacketEnvelopeV2.from_dict(
            _require_exact_dict(value, "llm-turn packet envelope")
        )
    if envelope.packet_family != LLM_TURN_PACKET_FAMILY:
        _fail("llm-turn packet family is unsupported")
    if envelope.constraints != LLM_TURN_ENVELOPE_CONSTRAINTS:
        _fail("llm-turn packet constraints are not canonical")
    if envelope.terminal_target != LLM_TURN_TERMINAL_TARGET:
        _fail("llm-turn packet terminal target is unsupported")
    if envelope.evidence_ceiling != LLM_TURN_EVIDENCE_CEILING:
        _fail("llm-turn packet evidence ceiling is unsupported")
    if envelope.oracle_policy != LLM_TURN_ORACLE_POLICY:
        _fail("llm-turn packet oracle policy is unsupported")
    if (
        envelope.packet_kind != "problem"
        or envelope.framing_mode != "strict"
        or envelope.authority_effect != "None"
    ):
        _fail("llm-turn packet framing or authority is unsupported")
    primitive_payload = thaw(envelope.payload)
    payload = LlmTurnPayloadV1.from_dict(
        _require_exact_dict(primitive_payload, "llm-turn payload")
    )
    payload_parent = str(payload.parent_packet_id) if payload.parent_packet_id else None
    if envelope.parent_event_id != payload_parent:
        _fail("envelope parent_event_id does not match payload parent_packet_id")
    payload_manifest = str(payload.turn_manifest_root) if payload.turn_manifest_root else None
    if envelope.initial_state_hash != payload_manifest:
        _fail("envelope initial_state_hash does not bind the turn manifest")
    if envelope.source_digest != payload_manifest:
        _fail("envelope source_digest does not bind the turn manifest")
    return payload


def attach_llm_turn_candidate(
    envelope: PacketEnvelopeV2 | Mapping[str, Any],
    content: LlmTurnContentArtifactV1,
    *,
    producer_id: str | None = None,
    claimed_terminal: str | None = None,
    claimed_valid: bool | None = None,
    reply_text: str | None = None,
) -> CandidateArtifactV1:
    """Attach immutable turn content as an untrusted candidate for one packet."""
    payload = parse_llm_turn_envelope(envelope)
    if str(payload.turn_kind) in CONSEQUENTIAL_TURN_KINDS and reply_text is None:
        _fail(
            "consequential turns require reply_text at attach to bind reply_sha256"
        )
    if isinstance(envelope, PacketEnvelopeV2):
        packet = PacketEnvelopeV2.from_dict(envelope.to_dict())
    else:
        packet = PacketEnvelopeV2.from_dict(
            _require_exact_dict(envelope, "llm-turn packet envelope")
        )
    if not isinstance(content, LlmTurnContentArtifactV1):
        raise TypeError("content must be a LlmTurnContentArtifactV1")
    if str(content.packet_id) != str(packet.packet_id):
        _fail("content packet_id does not match the task packet")
    if str(content.content_sha256) != str(payload.content_sha256):
        _fail("content content_sha256 does not match the task payload binding")
    if int(content.content_byte_count) != int(payload.content_byte_count):
        _fail("content content_byte_count does not match the task payload binding")
    producer = producer_id or content.producer_id
    _require_stable_id(producer, "producer_id")
    machine_fields: dict[str, str] = {}
    reply_sha256: str | None = None
    if reply_text is not None:
        machine_fields = parse_machine_reply_block(reply_text)
        normalized = reply_text.replace("\r\n", "\n").replace("\r", "\n")
        reply_sha256 = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    meta: dict[str, Any] = {
        "family": LLM_TURN_FAMILY,
        "content_id": content.content_id,
        "machine_fields": machine_fields,
        "turn_kind": str(payload.turn_kind),
    }
    if reply_sha256 is not None:
        meta["reply_sha256"] = reply_sha256
    return CandidateArtifactV1(
        packet_id=packet.packet_id,
        producer_id=producer,
        payload=content.to_dict(),
        witness=content.content_sha256,
        claimed_terminal=claimed_terminal,
        claimed_valid=claimed_valid,
        metadata=meta,
        authority_effect="None",
    )


def llm_turn_task_packet_sha256(payload: LlmTurnPayloadV1) -> str:
    """Canonical digest of the task packet a run root is opened for.

    `task_packet_id` identifies the *task*; this identifies its *content*. Both
    used to be `sha256(task_id)`, which recorded the same fact twice and left
    the packet's content bound to nothing. Two turns for one task id with
    different objectives, budgets, required reply fields or kill conditions
    therefore produced an identical `run_root_id`: saving one silently
    overwrote the other, and a swapped or stale payload changed evaluation
    policy without changing any id or failing any validation.

    `identity_fields` carries `task_packet_sha256`, so digesting the payload
    here is what puts the task packet inside the run root's own identity.
    """
    return domain_digest(PAYLOAD_DOMAIN, payload.to_dict())


def _derive_llm_turn_terminal(
    *,
    refusals: set[str],
    open_obstructions: set[str],
    has_candidate: bool,
    has_content: bool,
    has_attempt: bool,
    turn_kind: str,
) -> str:
    if REFUSAL_CANDIDATE_BUDGET_EXCEEDED in refusals or (
        REFUSAL_OPERATION_BUDGET_EXCEEDED in refusals
    ):
        return "BudgetExhausted"
    if REFUSAL_PROSE_PROMPT_REFUSED in refusals:
        return "ProsePromptRefused"
    if refusals:
        return "TypedRefusal"
    if not has_candidate or not has_content or not has_attempt:
        return "InvalidPacket"
    if open_obstructions:
        if turn_kind == "claimed_result" and (
            OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED in open_obstructions
        ):
            return "PacketizedTurn"
        return "OpenEvaluation"
    if turn_kind == "claimed_result":
        return "PacketizedTurn"
    return "TransportValidated"


def _assert_candidate_binds_content(
    candidate: CandidateArtifactV1, content: LlmTurnContentArtifactV1
) -> None:
    """Refuse evaluating a candidate against a substituted content artifact."""
    try:
        bound = LlmTurnContentArtifactV1.from_dict(
            _require_exact_dict(thaw(candidate.payload), "candidate.payload")
        )
    except (CanonicalizationError, TypeError, ValueError) as exc:
        _fail(f"{REFUSAL_CANDIDATE_CONTENT_MISBIND}: {exc}")
    if bound.content_id != content.content_id:
        _fail(f"{REFUSAL_CANDIDATE_CONTENT_MISBIND}: content_id mismatch")
    if candidate.witness != content.content_sha256:
        _fail(f"{REFUSAL_CANDIDATE_CONTENT_MISBIND}: witness mismatch")
    meta = thaw(candidate.metadata)
    if not isinstance(meta, Mapping):
        _fail(f"{REFUSAL_CANDIDATE_CONTENT_MISBIND}: metadata missing")
    if meta.get("content_id") != content.content_id:
        _fail(f"{REFUSAL_CANDIDATE_CONTENT_MISBIND}: metadata content_id")
    if meta.get("family") != LLM_TURN_FAMILY:
        _fail(f"{REFUSAL_CANDIDATE_CONTENT_MISBIND}: family mismatch")


def evaluate_llm_turn_candidate(
    envelope: PacketEnvelopeV2 | Mapping[str, Any],
    candidate: CandidateArtifactV1,
    content: LlmTurnContentArtifactV1,
    *,
    prior_candidate_count: int = 0,
    operation_count: int = 1,
    content_bytes: bytes | None = None,
    reply_text: str | None = None,
    machine_phase: str = "proposal",
) -> LlmTurnRunRootV1:
    """Evaluate a turn candidate against budgets and packet fences."""
    payload = parse_llm_turn_envelope(envelope)
    if isinstance(envelope, PacketEnvelopeV2):
        packet = PacketEnvelopeV2.from_dict(envelope.to_dict())
    else:
        packet = PacketEnvelopeV2.from_dict(
            _require_exact_dict(envelope, "llm-turn packet envelope")
        )
    if not isinstance(candidate, CandidateArtifactV1):
        raise TypeError("candidate must be a CandidateArtifactV1")
    if not isinstance(content, LlmTurnContentArtifactV1):
        raise TypeError("content must be a LlmTurnContentArtifactV1")
    if candidate.packet_id != packet.packet_id or content.packet_id != packet.packet_id:
        _fail("candidate/content packet_id does not match the task packet")
    CandidateArtifactV1.from_dict(candidate.to_dict())
    _assert_candidate_binds_content(candidate, content)
    _ = candidate.claimed_valid

    refusals: set[str] = set()
    open_obstructions: set[str] = set()

    if str(payload.turn_kind) in CONSEQUENTIAL_TURN_KINDS:
        if content_bytes is None:
            refusals.add(REFUSAL_CONTENT_BYTES_REQUIRED)
        if reply_text is None:
            refusals.add(REFUSAL_REPLY_REQUIRED)
            refusals.add(REFUSAL_PROSE_PROMPT_REFUSED)
        meta_pre = thaw(candidate.metadata)
        if not isinstance(meta_pre, Mapping) or not meta_pre.get("reply_sha256"):
            refusals.add(REFUSAL_REPLY_NOT_BOUND)
            refusals.add(REFUSAL_REPLY_REQUIRED)

    if content_bytes is not None:
        verify_content_bytes(content, content_bytes)

    if prior_candidate_count >= int(payload.candidate_budget):
        refusals.add(REFUSAL_CANDIDATE_BUDGET_EXCEEDED)
    if operation_count > int(payload.operation_budget):
        refusals.add(REFUSAL_OPERATION_BUDGET_EXCEEDED)

    if str(content.content_sha256) != str(payload.content_sha256):
        refusals.add(REFUSAL_CONTENT_DIGEST_MISMATCH)

    machine_fields: dict[str, str] = {}
    meta_raw = thaw(candidate.metadata)
    meta: Mapping[str, Any] = (
        meta_raw if isinstance(meta_raw, Mapping) else {}
    )
    raw_fields = meta.get("machine_fields") if isinstance(meta, Mapping) else None
    if isinstance(raw_fields, Mapping):
        machine_fields = {
            str(key): str(value) for key, value in raw_fields.items()
        }

    if reply_text is not None:
        parsed = parse_machine_reply_block(reply_text)
        normalized_reply = reply_text.replace("\r\n", "\n").replace("\r", "\n")
        reply_digest = hashlib.sha256(normalized_reply.encode("utf-8")).hexdigest()
        attached_reply_sha = meta.get("reply_sha256") if isinstance(meta, Mapping) else None
        if (
            isinstance(attached_reply_sha, str)
            and attached_reply_sha
            and attached_reply_sha != reply_digest
        ):
            refusals.add(REFUSAL_REPLY_NOT_BOUND)
        clean_attached = {
            key: value
            for key, value in machine_fields.items()
            if key != "__order__"
        }
        clean_parsed = {
            key: value for key, value in parsed.items() if key != "__order__"
        }
        if clean_attached and clean_attached != clean_parsed:
            refusals.add(REFUSAL_REPLY_NOT_BOUND)
        machine_fields = parsed if parsed else machine_fields
        if content_bytes is not None:
            normalized_reply = reply_text.replace("\r\n", "\n").replace("\r", "\n")
            bound = content_bytes.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            reply_bytes = normalized_reply.encode("utf-8")
            if bound != reply_bytes:
                lines = normalized_reply.split("\n")
                index = 0
                while index < len(lines) and lines[index].strip() == "":
                    index += 1
                while index < len(lines):
                    line = lines[index].strip()
                    if not line or "=" not in line:
                        break
                    key = line.partition("=")[0].strip()
                    if key not in REQUIRED_REPLY_FIELD_IDS:
                        break
                    index += 1
                if index < len(lines) and lines[index].strip() == "":
                    index += 1
                body = "\n".join(lines[index:]).encode("utf-8")
                if body != bound and not normalized_reply.encode("utf-8").endswith(
                    bound
                ):
                    refusals.add(REFUSAL_REPLY_NOT_BOUND)

    if str(payload.turn_kind) in CONSEQUENTIAL_TURN_KINDS:
        if not machine_fields:
            refusals.add(REFUSAL_PROSE_PROMPT_REFUSED)
            refusals.add(REFUSAL_CONSEQUENTIAL_WITHOUT_PACKET)
        else:
            field_refusals = validate_machine_reply_fields(
                machine_fields,
                required=payload.required_reply_fields,
                expected_packet_id=str(packet.packet_id) if packet.packet_id else None,
                expected_parent=str(payload.parent_packet_id) if payload.parent_packet_id else None,
                phase=machine_phase,
                expected_candidate_id=str(candidate.candidate_id)
                if machine_phase == "host_status" and candidate.candidate_id
                else None,
            )
            refusals.update(field_refusals)
            if field_refusals:
                refusals.add(REFUSAL_PROSE_PROMPT_REFUSED)
    elif machine_fields:
        field_refusals = validate_machine_reply_fields(
            machine_fields,
            required=payload.required_reply_fields,
            expected_packet_id=str(packet.packet_id) if packet.packet_id else None,
            expected_parent=str(payload.parent_packet_id) if payload.parent_packet_id else None,
            phase=machine_phase,
        )
        refusals.update(field_refusals)

    if str(payload.turn_kind) == "claimed_result":
        open_obstructions.add(OBSTRUCTION_CLAIM_EVALUATOR_REQUIRED)

    if candidate.claimed_valid is True and refusals:
        refusals.add(REFUSAL_MODEL_VERDICT_UNTRUSTED)

    attempt_disposition = "AcceptedForEvaluation"
    attempt_refusals: tuple[str, ...] = ()
    if REFUSAL_CANDIDATE_BUDGET_EXCEEDED in refusals or (
        REFUSAL_OPERATION_BUDGET_EXCEEDED in refusals
    ):
        attempt_disposition = "BudgetExhausted"
        attempt_refusals = tuple(sorted(refusals))
    elif refusals:
        attempt_disposition = "Refused"
        attempt_refusals = tuple(sorted(refusals))

    terminal = _derive_llm_turn_terminal(
        refusals=refusals,
        open_obstructions=open_obstructions,
        has_candidate=True,
        has_content=True,
        has_attempt=True,
        turn_kind=str(payload.turn_kind),
    )

    packet_bytes = canonical_json_artifact_bytes(packet.to_dict())
    attempt = LlmTurnAttemptV1(
        attempt_index=0,
        candidate_id=candidate.candidate_id,
        content_id=content.content_id,
        operation_count=operation_count,
        disposition=attempt_disposition,
        refusal_codes=attempt_refusals,
    )
    return LlmTurnRunRootV1(
        task_packet_id=packet.packet_id,
        task_packet_sha256=hashlib.sha256(packet_bytes).hexdigest(),
        turn_kind=str(payload.turn_kind),
        candidate_ids=(candidate.candidate_id,),
        content_ids=(content.content_id,),
        attempts=(attempt,),
        refusals=tuple(sorted(refusals)),
        terminal_status=terminal,
        open_obstruction_ids=tuple(sorted(open_obstructions)),
    )


def verify_llm_turn_run_root_shape(
    value: LlmTurnRunRootV1 | Mapping[str, Any],
) -> LlmTurnRunRootV1:
    """Parse + terminal re-derivation + attempt ID cross-links (not full replay)."""
    if isinstance(value, LlmTurnRunRootV1):
        root = LlmTurnRunRootV1.from_dict(value.to_dict())
    else:
        root = LlmTurnRunRootV1.from_dict(
            _require_exact_dict(value, "llm-turn run root")
        )
    if root.terminal_status == "VerifiedProposal":
        _fail(REFUSAL_VERIFIED_PROPOSAL_FORBIDDEN)
    candidate_set = set(root.candidate_ids)
    content_set = set(root.content_ids)
    for attempt in root.attempts:
        if attempt.candidate_id not in candidate_set:
            _fail(f"{REFUSAL_ATTEMPT_ID_MISBIND}: candidate_id")
        if attempt.content_id not in content_set:
            _fail(f"{REFUSAL_ATTEMPT_ID_MISBIND}: content_id")
    expected = _derive_llm_turn_terminal(
        refusals=set(root.refusals),
        open_obstructions=set(root.open_obstruction_ids),
        has_candidate=bool(root.candidate_ids),
        has_content=bool(root.content_ids),
        has_attempt=bool(root.attempts),
        turn_kind=root.turn_kind,
    )
    if expected != root.terminal_status:
        _fail(
            f"{REFUSAL_TERMINAL_NOT_DERIVED}: wire={root.terminal_status} "
            f"derived={expected}"
        )
    return root


def verify_llm_turn_run_root(
    value: LlmTurnRunRootV1 | Mapping[str, Any],
    *,
    packet: PacketEnvelopeV2 | Mapping[str, Any] | None = None,
    candidate: CandidateArtifactV1 | None = None,
    content: LlmTurnContentArtifactV1 | None = None,
    content_bytes: bytes | None = None,
    reply_text: str | None = None,
    prior_candidate_count: int = 0,
    operation_count: int = 1,
    machine_phase: str = "proposal",
) -> LlmTurnRunRootV1:
    """Shape-check plus optional full evaluate replay for positive terminals."""
    root = verify_llm_turn_run_root_shape(value)
    if root.terminal_status not in POSITIVE_LLM_TERMINALS:
        return root
    if packet is None or candidate is None or content is None or content_bytes is None:
        _fail(REFUSAL_POSITIVE_TERMINAL_NEEDS_REPLAY)
    if root.turn_kind in CONSEQUENTIAL_TURN_KINDS and reply_text is None:
        _fail(REFUSAL_POSITIVE_TERMINAL_NEEDS_REPLAY)
    recomputed = evaluate_llm_turn_candidate(
        packet,
        candidate,
        content,
        prior_candidate_count=prior_candidate_count,
        operation_count=operation_count,
        content_bytes=content_bytes,
        reply_text=reply_text,
        machine_phase=machine_phase,
    )
    if recomputed.run_root_id != root.run_root_id:
        _fail(
            f"{REFUSAL_TERMINAL_NOT_DERIVED}: run_root_id replay mismatch "
            f"wire={root.run_root_id} derived={recomputed.run_root_id}"
        )
    return root


def build_payload_from_content(
    *,
    objective: str,
    role: str,
    turn_kind: str,
    content_bytes: bytes,
    candidate_budget: int = 3,
    operation_budget: int = 20,
    parent_packet_id: str | None = None,
    conversation_root_id: str | None = None,
    required_reply_fields: Sequence[str] | None = None,
) -> LlmTurnPayloadV1:
    """Convenience constructor that binds content bytes into a payload."""
    if type(content_bytes) is not bytes:
        raise TypeError("content_bytes must be exact bytes")
    if len(content_bytes) > MAX_CONTENT_BYTES:
        _fail("content_bytes exceeds the content resource limit")
    fields = (
        DEFAULT_REQUIRED_REPLY_FIELDS
        if required_reply_fields is None
        else tuple(required_reply_fields)
    )
    return LlmTurnPayloadV1(
        objective=objective,
        role=role,
        turn_kind=turn_kind,
        content_sha256=hashlib.sha256(content_bytes).hexdigest(),
        content_byte_count=len(content_bytes),
        candidate_budget=candidate_budget,
        operation_budget=operation_budget,
        required_reply_fields=tuple(sorted(set(fields))),
        parent_packet_id=parent_packet_id,
        conversation_root_id=conversation_root_id,
    )


