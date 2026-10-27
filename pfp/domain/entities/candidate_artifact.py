"""CandidateArtifact entity: untrusted proposal tied to one packet.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping

from pfp.domain.shared_kernel.canonical import (
    CanonicalizationError,
    canonical_unwire,
    canonical_wire,
    domain_digest,
    freeze,
)

CANDIDATE_SCHEMA = "core.symbol-game.candidate-artifact.v1"
_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CanonicalizationError(f"{name} must be a mapping")
    return value


def _require_fields(
    value: Mapping[str, Any],
    required: frozenset[str],
    optional: frozenset[str],
    name: str,
) -> None:
    keys = frozenset(value.keys())
    missing = required - keys
    if missing:
        raise CanonicalizationError(f"{name} missing required fields: {sorted(missing)}")
    extra = keys - (required | optional)
    if extra:
        raise CanonicalizationError(f"{name} contains unknown fields: {sorted(extra)}")


def _require_string(value: Any, name: str, nonempty: bool = False) -> str:
    if type(value) is not str:
        raise CanonicalizationError(f"{name} must be a string")
    if nonempty and not value:
        raise CanonicalizationError(f"{name} cannot be empty")
    return value


def _require_optional_string(value: Any, name: str) -> str | None:
    if value is None:
        return None
    return _require_string(value, name)


def _require_optional_bool(value: Any, name: str) -> bool | None:
    if value is None:
        return None
    if type(value) is not bool:
        raise CanonicalizationError(f"{name} must be a boolean or null")
    return value


def _require_digest(value: Any, name: str) -> str:
    string = _require_string(value, name, nonempty=True)
    if not _DIGEST_PATTERN.match(string):
        raise CanonicalizationError(f"{name} must be a 64-character lowercase hex digest")
    return string


@dataclass(frozen=True, slots=True)
class CandidateArtifactV1:
    """Untrusted proposal tied to one packet.

    ``claimed_terminal`` is retained for audit but never controls evaluation.
    """

    packet_id: str
    producer_id: str
    payload: Any
    witness: str
    claimed_terminal: str | None = None
    claimed_valid: bool | None = None
    metadata: Any = field(default_factory=dict)
    schema_version: str = field(default=CANDIDATE_SCHEMA)
    authority_effect: str = field(default="None")

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", freeze(self.payload))
        object.__setattr__(self, "metadata", freeze(self.metadata))

    @property
    def candidate_id(self) -> str:
        return domain_digest(
            "core.symbol-game.candidate-artifact.v1",
            {
                "schema_version": self.schema_version,
                "packet_id": self.packet_id,
                "producer_id": self.producer_id,
                "payload": self.payload,
                "witness": self.witness,
                "claimed_terminal": self.claimed_terminal,
                "claimed_valid": self.claimed_valid,
                "metadata": self.metadata,
                "authority_effect": self.authority_effect,
            },
        )

    def payload_dict(self) -> Mapping[str, Any]:
        return {
            "schema_version": self.schema_version,
            "packet_id": self.packet_id,
            "producer_id": self.producer_id,
            "payload": self.payload,
            "witness": self.witness,
            "claimed_terminal": self.claimed_terminal,
            "claimed_valid": self.claimed_valid,
            "metadata": self.metadata,
            "authority_effect": self.authority_effect,
        }

    # DDD compatibility properties
    @property
    def task_id(self) -> str:
        return self.packet_id

    @property
    def content_artifact_id(self) -> str | None:
        return None

    @property
    def content_sha256(self) -> str | None:
        return None

    @property
    def content_bytes_len(self) -> int | None:
        return None

    @property
    def parent_packet_id(self) -> str | None:
        return None

    @property
    def dual_witness_ref(self) -> str | None:
        return self.witness if self.witness else None

    @classmethod
    def create(
        cls,
        *,
        schema_version: str = CANDIDATE_SCHEMA,
        packet_id: str | None = None,
        task_id: str | None = None,
        producer_id: str = "",
        payload: Any = None,
        witness: str = "",
        claimed_terminal: str | None = None,
        claimed_valid: bool | None = None,
        metadata: Any = None,
        authority_effect: str = "None",
        candidate_id: str | None = None,
        content_artifact_id: str | None = None,
        content_sha256: str | None = None,
        content_bytes_len: int | None = None,
        parent_packet_id: str | None = None,
        dual_witness_ref: str | None = None,
    ) -> CandidateArtifactV1:
        pid = packet_id if packet_id is not None else (task_id if task_id is not None else "")
        wit = witness if witness else (dual_witness_ref if dual_witness_ref else "")
        auth = authority_effect.value if hasattr(authority_effect, "value") else str(authority_effect)
        return cls(
            packet_id=str(pid),
            producer_id=str(producer_id),
            payload=payload,
            witness=str(wit),
            claimed_terminal=str(claimed_terminal) if claimed_terminal is not None else None,
            claimed_valid=bool(claimed_valid) if claimed_valid is not None else None,
            metadata=metadata if metadata is not None else {},
            schema_version=str(schema_version),
            authority_effect=auth,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "candidate_id": self.candidate_id,
            "packet_id": self.packet_id,
            "producer_id": self.producer_id,
            "payload": canonical_wire(self.payload),
            "witness": self.witness,
            "claimed_terminal": self.claimed_terminal,
            "claimed_valid": self.claimed_valid,
            "metadata": canonical_wire(self.metadata),
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> CandidateArtifactV1:
        wire = _require_mapping(wire, "candidate artifact")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "candidate_id",
                    "packet_id",
                    "producer_id",
                    "payload",
                    "witness",
                    "claimed_terminal",
                    "claimed_valid",
                    "metadata",
                    "authority_effect",
                }
            ),
            frozenset({"task_id", "content_artifact_id", "content_sha256", "content_bytes_len", "parent_packet_id", "dual_witness_ref"}),
            "candidate artifact",
        )
        schema_version = _require_string(wire["schema_version"], "schema_version")
        authority_effect = _require_string(wire["authority_effect"], "authority_effect")
        if schema_version != CANDIDATE_SCHEMA:
            raise CanonicalizationError("candidate schema version is unsupported")
        if authority_effect != "None":
            raise CanonicalizationError("candidate authority effect must be None")
        expected_candidate_id = _require_digest(wire["candidate_id"], "candidate_id")
        candidate = cls(
            packet_id=_require_digest(wire["packet_id"], "packet_id"),
            producer_id=_require_string(wire["producer_id"], "producer_id", nonempty=True),
            payload=canonical_unwire(wire["payload"]),
            witness=_require_string(wire["witness"], "witness", nonempty=True),
            claimed_terminal=_require_optional_string(
                wire["claimed_terminal"], "claimed_terminal"
            ),
            claimed_valid=_require_optional_bool(
                wire["claimed_valid"], "claimed_valid"
            ),
            metadata=canonical_unwire(wire["metadata"]),
            schema_version=schema_version,
            authority_effect=authority_effect,
        )
        if expected_candidate_id != candidate.candidate_id:
            raise CanonicalizationError(
                "candidate_id does not match canonical wire content"
            )
        return candidate


__all__ = ["CandidateArtifactV1", "CANDIDATE_SCHEMA"]
