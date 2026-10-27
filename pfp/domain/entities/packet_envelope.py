"""Wire-shaped packet, candidate, and evaluation contracts for the lab.

These are deliberately plain transport objects.  Deserializing one never
creates a verified OESOS receipt or a continuation permit.
"""

from __future__ import annotations


from dataclasses import field
from dataclasses import dataclass
from typing import Any, Mapping

from pfp.domain.shared_kernel.canonical import (
    CanonicalizationError,
    canonical_unwire,
    canonical_wire,
    domain_digest,
    freeze,
)


PACKET_SCHEMA = "core.symbol-game.packet-envelope.v2"
CANDIDATE_SCHEMA = "core.symbol-game.candidate-artifact.v1"
EVALUATION_SCHEMA = "core.oesos.evaluation-receipt.v1"
LAB_TERMINAL_STATUSES = {
    "LabExactCandidate",
    "LabClosedResidualCandidate",
    "LabActiveClosureFailureCandidate",
    "DetectorInadequate",
    "AdapterFailure",
    "BudgetExhausted",
    "UnauthorizedContinuation",
    "StuckCorpus",
    "InvalidPacket",
}


def _is_digest(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and value
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise CanonicalizationError(f"{label} must be a string-keyed object")
    return value


def _require_fields(
    wire: Mapping[str, Any],
    required: frozenset[str],
    optional: frozenset[str],
    label: str,
) -> None:
    keys = frozenset(wire)
    missing = required - keys
    unknown = keys - required - optional
    if missing:
        raise CanonicalizationError(
            f"{label} is missing fields: {', '.join(sorted(missing))}"
        )
    if unknown:
        raise CanonicalizationError(
            f"{label} has unknown fields: {', '.join(sorted(unknown))}"
        )


def _require_string(
    wire: Mapping[str, Any],
    key: str,
    *,
    non_empty: bool = False,
) -> str:
    value = wire[key]
    if not isinstance(value, str) or (non_empty and not value):
        raise CanonicalizationError(f"{key} must be a string")
    return value


def _require_optional_string(value: Any, label: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise CanonicalizationError(f"{label} must be a string or null")
    return value


def _require_digest(wire: Mapping[str, Any], key: str) -> str:
    value = wire[key]
    if not _is_digest(value):
        raise CanonicalizationError(f"{key} must be a lowercase SHA-256 digest")
    return value


def _require_optional_digest(value: Any, label: str) -> str | None:
    value = _require_optional_string(value, label)
    if value is not None and not _is_digest(value):
        raise CanonicalizationError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_string_array(wire: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = wire[key]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise CanonicalizationError(f"{key} must be an array of strings")
    return tuple(value)


def _require_bool(wire: Mapping[str, Any], key: str) -> bool:
    value = wire[key]
    if type(value) is not bool:
        raise CanonicalizationError(f"{key} must be a boolean")
    return value


def _require_optional_bool(value: Any, label: str) -> bool | None:
    if value is not None and type(value) is not bool:
        raise CanonicalizationError(f"{label} must be a boolean or null")
    return value


def _require_positive_int(wire: Mapping[str, Any], key: str) -> int:
    value = wire[key]
    if type(value) is not int or value < 1:
        raise CanonicalizationError(f"{key} must be a positive integer")
    return value


@dataclass(frozen=True, slots=True)
class PacketEnvelopeV2:
    """Host-owned task envelope binding every fidelity-relevant field."""

    task_id: str
    packet_family: str
    carrier_id: str
    initial_state_hash: str
    payload: Any
    constraints: tuple[str, ...]
    protected_boundaries: tuple[str, ...]
    terminal_target: str = "ExactOrTypedObstruction"
    evidence_ceiling: str = "ReplayableLabEvidence"
    oracle_policy: str = "ExternalVerifierRequired"
    allowed_transforms: tuple[str, ...] = ("same_carrier_retraction",)
    step_budget: int = 8
    framing_mode: str = "strict"
    packet_kind: str = "problem"
    parent_event_id: str | None = None
    source_digest: str | None = None
    schema_version: str = field(default=PACKET_SCHEMA)
    authority_effect: str = field(default="None")

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", freeze(self.payload))

    def identity_fields(self) -> Mapping[str, Any]:
        return {
            "schema_version": self.schema_version,
            "packet_kind": self.packet_kind,
            "framing_mode": self.framing_mode,
            "task_id": self.task_id,
            "packet_family": self.packet_family,
            "carrier_id": self.carrier_id,
            "initial_state_hash": self.initial_state_hash,
            "payload": self.payload,
            "constraints": self.constraints,
            "protected_boundaries": self.protected_boundaries,
            "terminal_target": self.terminal_target,
            "evidence_ceiling": self.evidence_ceiling,
            "oracle_policy": self.oracle_policy,
            "allowed_transforms": self.allowed_transforms,
            "step_budget": self.step_budget,
            "parent_event_id": self.parent_event_id,
            "source_digest": self.source_digest,
            "authority_effect": self.authority_effect,
        }

    @property
    def packet_id(self) -> str:
        return domain_digest(
            "core.symbol-game.packet-envelope.v2", self.identity_fields()
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "packet_id": self.packet_id,
            "packet_kind": self.packet_kind,
            "framing_mode": self.framing_mode,
            "task_id": self.task_id,
            "packet_family": self.packet_family,
            "carrier_id": self.carrier_id,
            "initial_state_hash": self.initial_state_hash,
            "payload": canonical_wire(self.payload),
            "constraints": list(self.constraints),
            "protected_boundaries": list(self.protected_boundaries),
            "terminal_target": self.terminal_target,
            "evidence_ceiling": self.evidence_ceiling,
            "oracle_policy": self.oracle_policy,
            "allowed_transforms": list(self.allowed_transforms),
            "step_budget": self.step_budget,
            "parent_event_id": self.parent_event_id,
            "source_digest": self.source_digest,
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "PacketEnvelopeV2":
        wire = _require_mapping(wire, "packet envelope")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "packet_id",
                    "packet_kind",
                    "framing_mode",
                    "task_id",
                    "packet_family",
                    "carrier_id",
                    "initial_state_hash",
                    "payload",
                    "constraints",
                    "protected_boundaries",
                    "terminal_target",
                    "evidence_ceiling",
                    "oracle_policy",
                    "allowed_transforms",
                    "step_budget",
                    "authority_effect",
                }
            ),
            frozenset({"parent_event_id", "source_digest"}),
            "packet envelope",
        )
        schema_version = _require_string(wire, "schema_version")
        authority_effect = _require_string(wire, "authority_effect")
        framing_mode = _require_string(wire, "framing_mode")
        if schema_version != PACKET_SCHEMA:
            raise CanonicalizationError("packet schema version is unsupported")
        if authority_effect != "None":
            raise CanonicalizationError("packet authority effect must be None")
        if framing_mode not in {"strict", "extraction"}:
            raise CanonicalizationError("packet framing mode is unsupported")
        expected_packet_id = _require_digest(wire, "packet_id")
        packet = cls(
            task_id=_require_string(wire, "task_id", non_empty=True),
            packet_family=_require_string(wire, "packet_family", non_empty=True),
            carrier_id=_require_string(wire, "carrier_id", non_empty=True),
            initial_state_hash=_require_digest(wire, "initial_state_hash"),
            payload=canonical_unwire(wire["payload"]),
            constraints=_require_string_array(wire, "constraints"),
            protected_boundaries=_require_string_array(wire, "protected_boundaries"),
            terminal_target=_require_string(wire, "terminal_target", non_empty=True),
            evidence_ceiling=_require_string(wire, "evidence_ceiling", non_empty=True),
            oracle_policy=_require_string(wire, "oracle_policy", non_empty=True),
            allowed_transforms=_require_string_array(wire, "allowed_transforms"),
            step_budget=_require_positive_int(wire, "step_budget"),
            framing_mode=framing_mode,
            packet_kind=_require_string(wire, "packet_kind", non_empty=True),
            parent_event_id=_require_optional_digest(
                wire.get("parent_event_id"), "parent_event_id"
            ),
            source_digest=_require_optional_digest(
                wire.get("source_digest"), "source_digest"
            ),
            schema_version=schema_version,
            authority_effect=authority_effect,
        )
        if expected_packet_id != packet.packet_id:
            raise CanonicalizationError(
                "packet_id does not match canonical wire content"
            )
        return packet

from .candidate_artifact import CandidateArtifactV1


@dataclass(frozen=True, slots=True)
class AttemptEvidenceV1:
    """One replay-addressable producer/evaluator decision."""

    solver_id: str
    candidate_id: str | None
    candidate_state_hash: str | None
    accepted: bool
    reason: str


@dataclass(frozen=True, slots=True)
class EvaluationReceiptV1:
    """Serializable summary that requires independent replay on admission."""

    packet_id: str
    input_state_hash: str
    output_state_hash: str
    terminal_status: str
    runtime_id: str
    solver_registry_hash: str
    attempts: tuple[AttemptEvidenceV1, ...]
    parent_event_id: str | None
    event_root: str
    active_obstructions: tuple[str, ...]
    replay_required: bool = True
    schema_version: str = field(default=EVALUATION_SCHEMA)
    authority_effect: str = field(default="None")

    @property
    def receipt_id(self) -> str:
        return domain_digest("core.oesos.evaluation-receipt.v1", self)

    def transport_valid(self) -> bool:
        if (
            self.schema_version != EVALUATION_SCHEMA
            or self.replay_required is not True
            or self.authority_effect != "None"
            or self.terminal_status not in LAB_TERMINAL_STATUSES
            or not isinstance(self.attempts, tuple)
            or not isinstance(self.active_obstructions, tuple)
            or any(
                not isinstance(obstruction, str)
                for obstruction in self.active_obstructions
            )
        ):
            return False
        if any(
            not _is_digest(value)
            for value in (
                self.packet_id,
                self.input_state_hash,
                self.output_state_hash,
                self.runtime_id,
                self.solver_registry_hash,
                self.event_root,
            )
        ):
            return False
        if self.parent_event_id is not None and not _is_digest(self.parent_event_id):
            return False
        if len(self.active_obstructions) != len(set(self.active_obstructions)):
            return False
        for attempt in self.attempts:
            if (
                not isinstance(attempt, AttemptEvidenceV1)
                or not isinstance(attempt.solver_id, str)
                or not attempt.solver_id
                or not isinstance(attempt.reason, str)
                or not attempt.reason
                or type(attempt.accepted) is not bool
            ):
                return False
            if attempt.candidate_id is not None and not _is_digest(
                attempt.candidate_id
            ):
                return False
            if attempt.candidate_state_hash is not None and not _is_digest(
                attempt.candidate_state_hash
            ):
                return False
            if attempt.accepted and (
                attempt.candidate_id is None or attempt.candidate_state_hash is None
            ):
                return False
        return True

    @property
    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(
            attempt.candidate_id
            for attempt in self.attempts
            if attempt.candidate_id is not None
        )

    @property
    def solver_ids(self) -> tuple[str, ...]:
        return tuple(attempt.solver_id for attempt in self.attempts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "packet_id": self.packet_id,
            "input_state_hash": self.input_state_hash,
            "output_state_hash": self.output_state_hash,
            "terminal_status": self.terminal_status,
            "runtime_id": self.runtime_id,
            "solver_registry_hash": self.solver_registry_hash,
            "attempts": [
                {
                    "solver_id": attempt.solver_id,
                    "candidate_id": attempt.candidate_id,
                    "candidate_state_hash": attempt.candidate_state_hash,
                    "accepted": attempt.accepted,
                    "reason": attempt.reason,
                }
                for attempt in self.attempts
            ],
            "parent_event_id": self.parent_event_id,
            "event_root": self.event_root,
            "active_obstructions": list(self.active_obstructions),
            "replay_required": self.replay_required,
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "EvaluationReceiptV1":
        wire = _require_mapping(wire, "evaluation receipt")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "packet_id",
                    "input_state_hash",
                    "output_state_hash",
                    "terminal_status",
                    "runtime_id",
                    "solver_registry_hash",
                    "attempts",
                    "parent_event_id",
                    "event_root",
                    "active_obstructions",
                    "replay_required",
                    "authority_effect",
                }
            ),
            frozenset(),
            "evaluation receipt",
        )
        raw_attempts = wire["attempts"]
        if not isinstance(raw_attempts, list):
            raise CanonicalizationError("attempts must be an array")
        attempts: list[AttemptEvidenceV1] = []
        for index, raw_attempt in enumerate(raw_attempts):
            attempt = _require_mapping(raw_attempt, f"attempts[{index}]")
            _require_fields(
                attempt,
                frozenset(
                    {
                        "solver_id",
                        "candidate_id",
                        "candidate_state_hash",
                        "accepted",
                        "reason",
                    }
                ),
                frozenset(),
                f"attempts[{index}]",
            )
            attempts.append(
                AttemptEvidenceV1(
                    solver_id=_require_string(attempt, "solver_id", non_empty=True),
                    candidate_id=_require_optional_digest(
                        attempt["candidate_id"], f"attempts[{index}].candidate_id"
                    ),
                    candidate_state_hash=_require_optional_digest(
                        attempt["candidate_state_hash"],
                        f"attempts[{index}].candidate_state_hash",
                    ),
                    accepted=_require_bool(attempt, "accepted"),
                    reason=_require_string(attempt, "reason", non_empty=True),
                )
            )
        schema_version = _require_string(wire, "schema_version")
        authority_effect = _require_string(wire, "authority_effect")
        replay_required = _require_bool(wire, "replay_required")
        if schema_version != EVALUATION_SCHEMA:
            raise CanonicalizationError("evaluation schema version is unsupported")
        if authority_effect != "None":
            raise CanonicalizationError("evaluation authority effect must be None")
        if replay_required is not True:
            raise CanonicalizationError("evaluation replay must be required")
        receipt = cls(
            packet_id=_require_digest(wire, "packet_id"),
            input_state_hash=_require_digest(wire, "input_state_hash"),
            output_state_hash=_require_digest(wire, "output_state_hash"),
            terminal_status=_require_string(wire, "terminal_status", non_empty=True),
            runtime_id=_require_digest(wire, "runtime_id"),
            solver_registry_hash=_require_digest(wire, "solver_registry_hash"),
            attempts=tuple(attempts),
            parent_event_id=_require_optional_digest(
                wire["parent_event_id"], "parent_event_id"
            ),
            event_root=_require_digest(wire, "event_root"),
            active_obstructions=_require_string_array(wire, "active_obstructions"),
            replay_required=replay_required,
            schema_version=schema_version,
            authority_effect=authority_effect,
        )
        if not receipt.transport_valid():
            raise ValueError("evaluation receipt transport contract refused")
        return receipt
