"""Closed domain model for the governed OEOS task lifecycle.

The records in this module are pure values. They perform no filesystem,
database, provider, process, or network work. Hash chaining establishes the
internal consistency of the events held by a caller; it cannot prove that a
valid tail was not removed without an independently pinned chain tip.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, fields, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SCHEMA_TASK_ENVELOPE = "core.oeos.task-envelope.v1"
SCHEMA_CAPABILITY_SNAPSHOT = "core.oeos.capability-snapshot.v1"
SCHEMA_HARNESS_EVENT = "core.oeos.harness-event.v1"
SCHEMA_ENCRYPTED_ARTIFACT_REF = "core.oeos.encrypted-artifact-ref.v1"
GENESIS_EVENT_DIGEST = "sha256:" + ("0" * 64)

_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_SCOPED_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,254}\Z")
_HEAD_SHA = re.compile(r"[0-9a-f]{40}\Z")
_TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z\Z"
)


class TaskInvariantError(ValueError):
    """A stable typed refusal raised before an invalid task value can exist."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}:{message}")


class _ExactTypeValue:
    """Keep value equality inside one closed contract type."""

    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return all(
            getattr(self, field.name) == getattr(other, field.name)
            for field in fields(self)
        )

    def __hash__(self) -> int:
        return hash(
            (type(self), *(getattr(self, field.name) for field in fields(self)))
        )


def canonical_json(value: Any) -> str:
    """Return the single canonical JSON spelling used by OEOS v1 digests."""

    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise TaskInvariantError(
            "NON_CANONICAL_VALUE", "value is not canonical JSON"
        ) from exc


def digest_payload(schema: str, value: Any) -> str:
    """Digest a typed payload without granting it evidentiary authority."""

    if type(schema) is not str or not _SCOPED_IDENTIFIER.fullmatch(schema):
        raise TaskInvariantError(
            "INVALID_SCHEMA", "schema must be a bounded identifier"
        )
    material = schema.encode("utf-8") + b"\x00" + canonical_json(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(material).hexdigest()


def utc_now() -> str:
    """Return a canonical UTC timestamp; clocks remain injectable at use sites."""

    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _require_exact_str(value: object, field: str, pattern: re.Pattern[str]) -> str:
    if type(value) is not str or pattern.fullmatch(value) is None:
        raise TaskInvariantError("INVALID_FIELD", f"{field} has an invalid value")
    return value


def _require_digest(value: object, field: str) -> str:
    return _require_exact_str(value, field, _DIGEST)


def require_sha256_digest(value: object, field: str = "digest") -> str:
    """Public exact SHA-256 validator shared by application value records."""

    return _require_digest(value, field)


def require_identifier(value: object, field: str = "identifier") -> str:
    """Public bounded identifier validator for metadata-only operations."""

    return _require_exact_str(value, field, _IDENTIFIER)


def _require_timestamp(value: object, field: str) -> str:
    if type(value) is not str or _TIMESTAMP.fullmatch(value) is None:
        raise TaskInvariantError("INVALID_TIMESTAMP", f"{field} must be canonical UTC")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise TaskInvariantError("INVALID_TIMESTAMP", f"{field} is invalid") from exc
    canonical = parsed.isoformat(timespec="microseconds").replace("+00:00", "Z")
    if parsed.tzinfo != timezone.utc or canonical != value:
        raise TaskInvariantError("INVALID_TIMESTAMP", f"{field} must be UTC")
    return value


def _require_exact_int(value: object, field: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise TaskInvariantError(
            "INVALID_FIELD",
            f"{field} must be an exact integer in [{minimum}, {maximum}]",
        )
    return value


class TaskStateV1(str, Enum):
    SUBMITTED = "SUBMITTED"
    QUEUED = "QUEUED"
    PREFLIGHT = "PREFLIGHT"
    RUNNING = "RUNNING"
    NEEDS_INPUT = "NEEDS_INPUT"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    REFUSED = "REFUSED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    STATUS_UNKNOWN = "STATUS_UNKNOWN"


TERMINAL_STATES = frozenset(
    {
        TaskStateV1.COMPLETED,
        TaskStateV1.REFUSED,
        TaskStateV1.FAILED,
        TaskStateV1.CANCELLED,
    }
)

ALLOWED_TRANSITIONS: Mapping[TaskStateV1, frozenset[TaskStateV1]] = {
    TaskStateV1.SUBMITTED: frozenset(
        {TaskStateV1.QUEUED, TaskStateV1.REFUSED, TaskStateV1.CANCELLED}
    ),
    TaskStateV1.QUEUED: frozenset(
        {
            TaskStateV1.PREFLIGHT,
            TaskStateV1.REFUSED,
            TaskStateV1.FAILED,
            TaskStateV1.CANCELLED,
        }
    ),
    TaskStateV1.PREFLIGHT: frozenset(
        {
            TaskStateV1.RUNNING,
            TaskStateV1.NEEDS_INPUT,
            TaskStateV1.REFUSED,
            TaskStateV1.FAILED,
            TaskStateV1.CANCELLED,
            TaskStateV1.STATUS_UNKNOWN,
        }
    ),
    TaskStateV1.RUNNING: frozenset(
        {
            TaskStateV1.NEEDS_INPUT,
            TaskStateV1.VERIFYING,
            TaskStateV1.REFUSED,
            TaskStateV1.FAILED,
            TaskStateV1.CANCELLED,
            TaskStateV1.STATUS_UNKNOWN,
        }
    ),
    TaskStateV1.NEEDS_INPUT: frozenset(
        {
            TaskStateV1.QUEUED,
            TaskStateV1.REFUSED,
            TaskStateV1.FAILED,
            TaskStateV1.CANCELLED,
        }
    ),
    TaskStateV1.VERIFYING: frozenset(
        {
            TaskStateV1.COMPLETED,
            TaskStateV1.REFUSED,
            TaskStateV1.FAILED,
            TaskStateV1.CANCELLED,
            TaskStateV1.STATUS_UNKNOWN,
        }
    ),
    TaskStateV1.STATUS_UNKNOWN: frozenset(
        {
            TaskStateV1.QUEUED,
            TaskStateV1.VERIFYING,
            TaskStateV1.FAILED,
            TaskStateV1.CANCELLED,
        }
    ),
    TaskStateV1.COMPLETED: frozenset(),
    TaskStateV1.REFUSED: frozenset(),
    TaskStateV1.FAILED: frozenset(),
    TaskStateV1.CANCELLED: frozenset(),
}


@dataclass(frozen=True, slots=True, eq=False)
class ActionLimitsV1(_ExactTypeValue):
    """Operator-declared task ceiling; this is not an action licence."""

    mutating: bool
    max_steps: int
    max_wall_seconds: int
    max_cost_microunits: int

    def __post_init__(self) -> None:
        if type(self.mutating) is not bool:
            raise TaskInvariantError("INVALID_FIELD", "mutating must be an exact bool")
        _require_exact_int(self.max_steps, "max_steps", 1, 1_000_000)
        _require_exact_int(self.max_wall_seconds, "max_wall_seconds", 1, 604_800)
        _require_exact_int(self.max_cost_microunits, "max_cost_microunits", 0, 10**15)

    def to_canonical(self) -> dict[str, object]:
        return {
            "max_cost_microunits": self.max_cost_microunits,
            "max_steps": self.max_steps,
            "max_wall_seconds": self.max_wall_seconds,
            "mutating": self.mutating,
        }

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> ActionLimitsV1:
        if type(value) is not dict or set(value) != {
            "max_cost_microunits",
            "max_steps",
            "max_wall_seconds",
            "mutating",
        }:
            raise TaskInvariantError(
                "INVALID_ACTION_LIMITS", "action limit fields differ"
            )
        return cls(
            mutating=value["mutating"],  # type: ignore[arg-type]
            max_steps=value["max_steps"],  # type: ignore[arg-type]
            max_wall_seconds=value["max_wall_seconds"],  # type: ignore[arg-type]
            max_cost_microunits=value["max_cost_microunits"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True, eq=False)
class EncryptedArtifactRefV1(_ExactTypeValue):
    """Integrity metadata for one raw artifact held outside task records.

    The reference is not evidence that encryption or custody is sound. Callers
    must replay the named envelope through the exact protector before using the
    artifact. No plaintext, ciphertext, key material, or path is carried here.
    """

    plaintext_sha256: str
    encrypted_envelope_digest: str
    artifact_schema: str
    protector_id: str
    byte_length: int
    schema: str = SCHEMA_ENCRYPTED_ARTIFACT_REF
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _require_digest(self.plaintext_sha256, "plaintext_sha256")
        _require_digest(self.encrypted_envelope_digest, "encrypted_envelope_digest")
        _require_exact_str(self.artifact_schema, "artifact_schema", _SCOPED_IDENTIFIER)
        _require_exact_str(self.protector_id, "protector_id", _SCOPED_IDENTIFIER)
        _require_exact_int(self.byte_length, "byte_length", 0, (2**63) - 1)
        if self.schema != SCHEMA_ENCRYPTED_ARTIFACT_REF:
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "encrypted artifact reference schema differs"
            )
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN",
                "encrypted artifact references grant no authority",
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "artifact_schema": self.artifact_schema,
            "authority_effect": self.authority_effect,
            "byte_length": self.byte_length,
            "encrypted_envelope_digest": self.encrypted_envelope_digest,
            "plaintext_sha256": self.plaintext_sha256,
            "protector_id": self.protector_id,
            "schema": self.schema,
        }

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> EncryptedArtifactRefV1:
        expected = {
            "artifact_schema",
            "authority_effect",
            "byte_length",
            "encrypted_envelope_digest",
            "plaintext_sha256",
            "protector_id",
            "schema",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_ENCRYPTED_ARTIFACT_REF",
                "encrypted artifact reference fields differ",
            )
        return cls(
            plaintext_sha256=value["plaintext_sha256"],  # type: ignore[arg-type]
            encrypted_envelope_digest=value[  # type: ignore[arg-type]
                "encrypted_envelope_digest"
            ],
            artifact_schema=value["artifact_schema"],  # type: ignore[arg-type]
            protector_id=value["protector_id"],  # type: ignore[arg-type]
            byte_length=value["byte_length"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True, eq=False)
class TaskEnvelopeV1(_ExactTypeValue):
    task_id: str
    idempotency_key: str
    task_family: str
    repository: str
    repository_head_sha: str
    encrypted_request_ref: EncryptedArtifactRefV1
    requested_skills: tuple[str, ...]
    action_limits: ActionLimitsV1
    policy_digest: str
    schema: str = SCHEMA_TASK_ENVELOPE

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_TASK_ENVELOPE:
            raise TaskInvariantError("SCHEMA_MISMATCH", "task envelope schema differs")
        _require_exact_str(self.task_id, "task_id", _IDENTIFIER)
        _require_exact_str(self.idempotency_key, "idempotency_key", _IDENTIFIER)
        _require_exact_str(self.task_family, "task_family", _SCOPED_IDENTIFIER)
        _require_exact_str(self.repository, "repository", _SCOPED_IDENTIFIER)
        _require_exact_str(self.repository_head_sha, "repository_head_sha", _HEAD_SHA)
        if type(self.encrypted_request_ref) is not EncryptedArtifactRefV1:
            raise TaskInvariantError(
                "INVALID_ENCRYPTED_REQUEST_REF",
                "encrypted_request_ref type differs",
            )
        _require_digest(self.policy_digest, "policy_digest")
        if type(self.requested_skills) is not tuple or any(
            type(item) is not str or _IDENTIFIER.fullmatch(item) is None
            for item in self.requested_skills
        ):
            raise TaskInvariantError(
                "INVALID_REQUESTED_SKILLS",
                "requested_skills must be an exact identifier tuple",
            )
        if tuple(sorted(set(self.requested_skills))) != self.requested_skills:
            raise TaskInvariantError(
                "INVALID_REQUESTED_SKILLS", "requested_skills must be sorted and unique"
            )
        if type(self.action_limits) is not ActionLimitsV1:
            raise TaskInvariantError(
                "INVALID_ACTION_LIMITS", "action_limits type differs"
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "action_limits": self.action_limits.to_canonical(),
            "encrypted_request_ref": self.encrypted_request_ref.to_canonical(),
            "idempotency_key": self.idempotency_key,
            "policy_digest": self.policy_digest,
            "repository": self.repository,
            "repository_head_sha": self.repository_head_sha,
            "requested_skills": list(self.requested_skills),
            "schema": self.schema,
            "task_family": self.task_family,
            "task_id": self.task_id,
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> TaskEnvelopeV1:
        expected = {
            "action_limits",
            "encrypted_request_ref",
            "idempotency_key",
            "policy_digest",
            "repository",
            "repository_head_sha",
            "requested_skills",
            "schema",
            "task_family",
            "task_id",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError("INVALID_ENVELOPE", "task envelope fields differ")
        skills = value["requested_skills"]
        limits = value["action_limits"]
        encrypted_request_ref = value["encrypted_request_ref"]
        if (
            type(skills) is not list
            or type(limits) is not dict
            or type(encrypted_request_ref) is not dict
        ):
            raise TaskInvariantError("INVALID_ENVELOPE", "nested envelope types differ")
        return cls(
            task_id=value["task_id"],  # type: ignore[arg-type]
            idempotency_key=value["idempotency_key"],  # type: ignore[arg-type]
            task_family=value["task_family"],  # type: ignore[arg-type]
            repository=value["repository"],  # type: ignore[arg-type]
            repository_head_sha=value["repository_head_sha"],  # type: ignore[arg-type]
            encrypted_request_ref=EncryptedArtifactRefV1.from_canonical(
                encrypted_request_ref
            ),
            requested_skills=tuple(skills),
            action_limits=ActionLimitsV1.from_canonical(limits),
            policy_digest=value["policy_digest"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
        )


class FacetStateV1(str, Enum):
    OBSERVED_TRUE = "OBSERVED_TRUE"
    OBSERVED_FALSE = "OBSERVED_FALSE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True, eq=False)
class CapabilityFacetV1(_ExactTypeValue):
    state: FacetStateV1
    evidence_digest: str | None

    def __post_init__(self) -> None:
        if type(self.state) is not FacetStateV1:
            raise TaskInvariantError(
                "INVALID_CAPABILITY_FACET", "facet state type differs"
            )
        if self.state is FacetStateV1.UNKNOWN:
            if self.evidence_digest is not None:
                raise TaskInvariantError(
                    "INVALID_CAPABILITY_FACET", "unknown facet cannot claim evidence"
                )
        else:
            _require_digest(self.evidence_digest, "evidence_digest")

    def to_canonical(self) -> dict[str, object]:
        return {"evidence_digest": self.evidence_digest, "state": self.state.value}

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> CapabilityFacetV1:
        if type(value) is not dict or set(value) != {"evidence_digest", "state"}:
            raise TaskInvariantError("INVALID_CAPABILITY_FACET", "facet fields differ")
        try:
            state = FacetStateV1(value["state"])
        except (TypeError, ValueError) as exc:
            raise TaskInvariantError(
                "INVALID_CAPABILITY_FACET", "facet state differs"
            ) from exc
        return cls(state=state, evidence_digest=value["evidence_digest"])  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True, eq=False)
class CapabilityRecordV1(_ExactTypeValue):
    capability_id: str
    capability_kind: str
    registered: CapabilityFacetV1
    configured: CapabilityFacetV1
    reachable: CapabilityFacetV1
    healthy: CapabilityFacetV1
    authorized: CapabilityFacetV1

    def __post_init__(self) -> None:
        _require_exact_str(self.capability_id, "capability_id", _SCOPED_IDENTIFIER)
        _require_exact_str(self.capability_kind, "capability_kind", _IDENTIFIER)
        for field in (
            self.registered,
            self.configured,
            self.reachable,
            self.healthy,
            self.authorized,
        ):
            if type(field) is not CapabilityFacetV1:
                raise TaskInvariantError(
                    "INVALID_CAPABILITY_RECORD", "capability facet type differs"
                )

    def to_canonical(self) -> dict[str, object]:
        return {
            "authorized": self.authorized.to_canonical(),
            "capability_id": self.capability_id,
            "capability_kind": self.capability_kind,
            "configured": self.configured.to_canonical(),
            "healthy": self.healthy.to_canonical(),
            "reachable": self.reachable.to_canonical(),
            "registered": self.registered.to_canonical(),
        }

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> CapabilityRecordV1:
        expected = {
            "authorized",
            "capability_id",
            "capability_kind",
            "configured",
            "healthy",
            "reachable",
            "registered",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_CAPABILITY_RECORD", "record fields differ"
            )
        facets = {}
        for name in ("registered", "configured", "reachable", "healthy", "authorized"):
            raw = value[name]
            if type(raw) is not dict:
                raise TaskInvariantError(
                    "INVALID_CAPABILITY_RECORD", "facet value differs"
                )
            facets[name] = CapabilityFacetV1.from_canonical(raw)
        return cls(
            capability_id=value["capability_id"],  # type: ignore[arg-type]
            capability_kind=value["capability_kind"],  # type: ignore[arg-type]
            **facets,
        )


@dataclass(frozen=True, slots=True, eq=False)
class CapabilitySnapshotV1(_ExactTypeValue):
    snapshot_id: str
    captured_at_utc: str
    capabilities: tuple[CapabilityRecordV1, ...]
    schema: str = SCHEMA_CAPABILITY_SNAPSHOT

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_CAPABILITY_SNAPSHOT:
            raise TaskInvariantError("SCHEMA_MISMATCH", "capability schema differs")
        _require_exact_str(self.snapshot_id, "snapshot_id", _IDENTIFIER)
        _require_timestamp(self.captured_at_utc, "captured_at_utc")
        if type(self.capabilities) is not tuple or any(
            type(item) is not CapabilityRecordV1 for item in self.capabilities
        ):
            raise TaskInvariantError(
                "INVALID_CAPABILITY_SNAPSHOT", "capabilities must be an exact tuple"
            )
        keys = tuple(
            (item.capability_kind, item.capability_id) for item in self.capabilities
        )
        if tuple(sorted(set(keys))) != keys:
            raise TaskInvariantError(
                "INVALID_CAPABILITY_SNAPSHOT", "capabilities must be sorted and unique"
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "capabilities": [item.to_canonical() for item in self.capabilities],
            "captured_at_utc": self.captured_at_utc,
            "schema": self.schema,
            "snapshot_id": self.snapshot_id,
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> CapabilitySnapshotV1:
        expected = {"capabilities", "captured_at_utc", "schema", "snapshot_id"}
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_CAPABILITY_SNAPSHOT", "snapshot fields differ"
            )
        raw = value["capabilities"]
        if type(raw) is not list or any(type(item) is not dict for item in raw):
            raise TaskInvariantError(
                "INVALID_CAPABILITY_SNAPSHOT", "capabilities differ"
            )
        return cls(
            snapshot_id=value["snapshot_id"],  # type: ignore[arg-type]
            captured_at_utc=value["captured_at_utc"],  # type: ignore[arg-type]
            capabilities=tuple(CapabilityRecordV1.from_canonical(item) for item in raw),
            schema=value["schema"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True, eq=False)
class HarnessEventV1(_ExactTypeValue):
    task_id: str
    sequence: int
    event_type: str
    from_state: TaskStateV1 | None
    to_state: TaskStateV1
    occurred_at_utc: str
    payload_digest: str
    previous_event_digest: str
    event_digest: str
    schema: str = SCHEMA_HARNESS_EVENT
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_HARNESS_EVENT or self.authority_effect != "None":
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "event schema or authority differs"
            )
        _require_exact_str(self.task_id, "task_id", _IDENTIFIER)
        _require_exact_int(self.sequence, "sequence", 1, 10**9)
        _require_exact_str(self.event_type, "event_type", _IDENTIFIER)
        if self.from_state is not None and type(self.from_state) is not TaskStateV1:
            raise TaskInvariantError("INVALID_EVENT_STATE", "from_state type differs")
        if type(self.to_state) is not TaskStateV1:
            raise TaskInvariantError("INVALID_EVENT_STATE", "to_state type differs")
        _require_timestamp(self.occurred_at_utc, "occurred_at_utc")
        _require_digest(self.payload_digest, "payload_digest")
        _require_digest(self.previous_event_digest, "previous_event_digest")
        _require_digest(self.event_digest, "event_digest")
        if self.event_digest != self.recomputed_digest:
            raise TaskInvariantError(
                "EVENT_DIGEST_MISMATCH", "event digest does not replay"
            )

    def _digest_fields(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "event_type": self.event_type,
            "from_state": self.from_state.value if self.from_state else None,
            "occurred_at_utc": self.occurred_at_utc,
            "payload_digest": self.payload_digest,
            "previous_event_digest": self.previous_event_digest,
            "schema": self.schema,
            "sequence": self.sequence,
            "task_id": self.task_id,
            "to_state": self.to_state.value,
        }

    @property
    def recomputed_digest(self) -> str:
        return digest_payload(self.schema, self._digest_fields())

    def to_canonical(self) -> dict[str, object]:
        return {**self._digest_fields(), "event_digest": self.event_digest}

    @classmethod
    def create(
        cls,
        *,
        task_id: str,
        sequence: int,
        event_type: str,
        from_state: TaskStateV1 | None,
        to_state: TaskStateV1,
        occurred_at_utc: str,
        payload_digest: str,
        previous_event_digest: str,
    ) -> HarnessEventV1:
        fields = {
            "authority_effect": "None",
            "event_type": event_type,
            "from_state": from_state.value if from_state else None,
            "occurred_at_utc": occurred_at_utc,
            "payload_digest": payload_digest,
            "previous_event_digest": previous_event_digest,
            "schema": SCHEMA_HARNESS_EVENT,
            "sequence": sequence,
            "task_id": task_id,
            "to_state": to_state.value,
        }
        return cls(
            task_id=task_id,
            sequence=sequence,
            event_type=event_type,
            from_state=from_state,
            to_state=to_state,
            occurred_at_utc=occurred_at_utc,
            payload_digest=payload_digest,
            previous_event_digest=previous_event_digest,
            event_digest=digest_payload(SCHEMA_HARNESS_EVENT, fields),
        )

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> HarnessEventV1:
        expected = {
            "authority_effect",
            "event_digest",
            "event_type",
            "from_state",
            "occurred_at_utc",
            "payload_digest",
            "previous_event_digest",
            "schema",
            "sequence",
            "task_id",
            "to_state",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError("INVALID_EVENT", "event fields differ")
        try:
            from_state = (
                None
                if value["from_state"] is None
                else TaskStateV1(value["from_state"])
            )
            to_state = TaskStateV1(value["to_state"])
        except (TypeError, ValueError) as exc:
            raise TaskInvariantError(
                "INVALID_EVENT_STATE", "event state differs"
            ) from exc
        return cls(
            task_id=value["task_id"],  # type: ignore[arg-type]
            sequence=value["sequence"],  # type: ignore[arg-type]
            event_type=value["event_type"],  # type: ignore[arg-type]
            from_state=from_state,
            to_state=to_state,
            occurred_at_utc=value["occurred_at_utc"],  # type: ignore[arg-type]
            payload_digest=value["payload_digest"],  # type: ignore[arg-type]
            previous_event_digest=value["previous_event_digest"],  # type: ignore[arg-type]
            event_digest=value["event_digest"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


def verify_event_chain(events: tuple[HarnessEventV1, ...]) -> TaskStateV1:
    """Verify the complete supplied chain and return its resulting state."""

    if type(events) is not tuple or not events:
        raise TaskInvariantError("EMPTY_EVENT_CHAIN", "at least one event is required")
    expected_previous = GENESIS_EVENT_DIGEST
    expected_state: TaskStateV1 | None = None
    task_id = events[0].task_id
    for expected_sequence, event in enumerate(events, start=1):
        if type(event) is not HarnessEventV1:
            raise TaskInvariantError("INVALID_EVENT", "event type differs")
        if event.task_id != task_id or event.sequence != expected_sequence:
            raise TaskInvariantError(
                "EVENT_SEQUENCE_MISMATCH", "event stream identity differs"
            )
        if event.previous_event_digest != expected_previous:
            raise TaskInvariantError("EVENT_CHAIN_BROKEN", "previous digest differs")
        if event.event_digest != event.recomputed_digest:
            raise TaskInvariantError("EVENT_DIGEST_MISMATCH", "event digest differs")
        if expected_sequence == 1:
            if (
                event.event_type != "TASK_SUBMITTED"
                or event.from_state is not None
                or event.to_state is not TaskStateV1.SUBMITTED
            ):
                raise TaskInvariantError(
                    "INVALID_INITIAL_EVENT", "first event must submit"
                )
        else:
            if event.from_state is not expected_state:
                raise TaskInvariantError(
                    "EVENT_STATE_CHAIN_BROKEN", "event state link differs"
                )
            if (
                event.from_state is not event.to_state
                and event.to_state not in ALLOWED_TRANSITIONS[event.from_state]
            ):
                raise TaskInvariantError(
                    "ILLEGAL_TASK_TRANSITION", "event transition is not allowed"
                )
        expected_state = event.to_state
        expected_previous = event.event_digest
    if expected_state is None:
        raise TaskInvariantError(
            "INVALID_TASK_EVENT_LOG", "task event log yielded no valid terminal state"
        )
    return expected_state


@dataclass(frozen=True, slots=True, eq=False)
class TaskAggregateV1(_ExactTypeValue):
    envelope: TaskEnvelopeV1
    capability_snapshot: CapabilitySnapshotV1
    state: TaskStateV1
    version: int
    cancellation_requested: bool
    events: tuple[HarnessEventV1, ...]
    encrypted_input_ref: EncryptedArtifactRefV1 | None = None

    def __post_init__(self) -> None:
        if type(self.envelope) is not TaskEnvelopeV1:
            raise TaskInvariantError("INVALID_AGGREGATE", "envelope type differs")
        if type(self.capability_snapshot) is not CapabilitySnapshotV1:
            raise TaskInvariantError("INVALID_AGGREGATE", "snapshot type differs")
        if type(self.state) is not TaskStateV1:
            raise TaskInvariantError("INVALID_AGGREGATE", "state type differs")
        _require_exact_int(self.version, "version", 1, 10**9)
        if type(self.cancellation_requested) is not bool:
            raise TaskInvariantError("INVALID_AGGREGATE", "cancellation flag differs")
        replayed = verify_event_chain(self.events)
        if self.version != len(self.events) or replayed is not self.state:
            raise TaskInvariantError(
                "AGGREGATE_REPLAY_MISMATCH", "snapshot differs from chain"
            )
        observed_cancellation = any(
            event.event_type == "CANCELLATION_REQUESTED" for event in self.events
        )
        if self.cancellation_requested is not observed_cancellation:
            raise TaskInvariantError(
                "AGGREGATE_REPLAY_MISMATCH",
                "cancellation flag differs from its evidence event",
            )
        self._validate_input_reference()

    @property
    def operator_input_version(self) -> int | None:
        """Sequence of the latest input binding, including legacy missing refs."""
        return next(
            (event.sequence for event in reversed(self.events)
             if event.event_type == "OPERATOR_INPUT_BOUND"),
            None,
        )

    def _validate_input_reference(self) -> None:
        # Older snapshots contain only a digest; never invent their lost ref.
        if self.encrypted_input_ref is None:
            return
        if type(self.encrypted_input_ref) is not EncryptedArtifactRefV1:
            raise TaskInvariantError("INVALID_OPERATOR_INPUT", "input reference type differs")
        version = self.operator_input_version
        if version is None:
            raise TaskInvariantError("OPERATOR_INPUT_BINDING_MISMATCH", "input binding event is absent")
        event = self.events[version - 1]
        expected = digest_payload(
            "core.oeos.operator-input.v1",
            {"encrypted_input_ref": self.encrypted_input_ref.to_canonical()},
        )
        if (
            event.task_id != self.envelope.task_id
            or event.from_state not in {TaskStateV1.NEEDS_INPUT, TaskStateV1.STATUS_UNKNOWN}
            or event.to_state is not TaskStateV1.QUEUED
            or event.payload_digest != expected
        ):
            raise TaskInvariantError("OPERATOR_INPUT_BINDING_MISMATCH", "reference differs from latest task input event")

    @property
    def chain_tip(self) -> str:
        return self.events[-1].event_digest

    @classmethod
    def submit(
        cls,
        envelope: TaskEnvelopeV1,
        capability_snapshot: CapabilitySnapshotV1,
        occurred_at_utc: str,
    ) -> TaskAggregateV1:
        event = HarnessEventV1.create(
            task_id=envelope.task_id,
            sequence=1,
            event_type="TASK_SUBMITTED",
            from_state=None,
            to_state=TaskStateV1.SUBMITTED,
            occurred_at_utc=occurred_at_utc,
            payload_digest=digest_payload(
                "core.oeos.task-submitted-payload.v1",
                {
                    "capability_snapshot_digest": capability_snapshot.canonical_digest,
                    "envelope_digest": envelope.canonical_digest,
                },
            ),
            previous_event_digest=GENESIS_EVENT_DIGEST,
        )
        return cls(
            envelope, capability_snapshot, TaskStateV1.SUBMITTED, 1, False, (event,)
        )

    def transition(
        self,
        target: TaskStateV1,
        *,
        occurred_at_utc: str,
        payload_digest: str,
        event_type: str = "TASK_STATE_CHANGED",
        encrypted_input_ref: EncryptedArtifactRefV1 | None = None,
    ) -> TaskAggregateV1:
        if type(target) is not TaskStateV1:
            raise TaskInvariantError("INVALID_EVENT_STATE", "target state type differs")
        if target not in ALLOWED_TRANSITIONS[self.state]:
            raise TaskInvariantError(
                "ILLEGAL_TASK_TRANSITION",
                f"{self.state.value} cannot transition to {target.value}",
            )
        if event_type == "OPERATOR_INPUT_BOUND":
            if type(encrypted_input_ref) is not EncryptedArtifactRefV1:
                raise TaskInvariantError("INVALID_OPERATOR_INPUT", "input binding requires an encrypted reference")
        elif encrypted_input_ref is not None:
            raise TaskInvariantError("INVALID_OPERATOR_INPUT", "reference requires an input binding event")
        event = HarnessEventV1.create(
            task_id=self.envelope.task_id,
            sequence=self.version + 1,
            event_type=event_type,
            from_state=self.state,
            to_state=target,
            occurred_at_utc=occurred_at_utc,
            payload_digest=payload_digest,
            previous_event_digest=self.chain_tip,
        )
        return replace(
            self,
            state=target,
            version=self.version + 1,
            events=self.events + (event,),
            encrypted_input_ref=(
                encrypted_input_ref if encrypted_input_ref is not None else self.encrypted_input_ref
            ),
        )

    def record(
        self,
        event_type: str,
        *,
        occurred_at_utc: str,
        payload_digest: str,
        cancellation_requested: bool | None = None,
    ) -> TaskAggregateV1:
        event = HarnessEventV1.create(
            task_id=self.envelope.task_id,
            sequence=self.version + 1,
            event_type=event_type,
            from_state=self.state,
            to_state=self.state,
            occurred_at_utc=occurred_at_utc,
            payload_digest=payload_digest,
            previous_event_digest=self.chain_tip,
        )
        flag = self.cancellation_requested
        if cancellation_requested is not None:
            if type(cancellation_requested) is not bool:
                raise TaskInvariantError(
                    "INVALID_AGGREGATE", "cancellation flag differs"
                )
            if event_type != "CANCELLATION_REQUESTED" or not cancellation_requested:
                raise TaskInvariantError(
                    "INVALID_CANCELLATION_EVENT",
                    "only a cancellation-request event may set the monotonic flag",
                )
            flag = cancellation_requested
        return replace(
            self,
            version=self.version + 1,
            cancellation_requested=flag,
            events=self.events + (event,),
        )


__all__ = [
    "ALLOWED_TRANSITIONS",
    "GENESIS_EVENT_DIGEST",
    "SCHEMA_CAPABILITY_SNAPSHOT",
    "SCHEMA_HARNESS_EVENT",
    "SCHEMA_TASK_ENVELOPE",
    "TERMINAL_STATES",
    "ActionLimitsV1",
    "CapabilityFacetV1",
    "CapabilityRecordV1",
    "CapabilitySnapshotV1",
    "FacetStateV1",
    "HarnessEventV1",
    "TaskAggregateV1",
    "TaskEnvelopeV1",
    "TaskInvariantError",
    "TaskStateV1",
    "canonical_json",
    "digest_payload",
    "require_identifier",
    "require_sha256_digest",
    "utc_now",
    "verify_event_chain",
]
