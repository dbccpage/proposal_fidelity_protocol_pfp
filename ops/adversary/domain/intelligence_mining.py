"""Inert intelligence candidates and an independent host-replay boundary.

These packets neither execute a workflow nor admit a skill, antibody, or rule.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from operations.domain.rop.result import Refusal, Result

from .evidence import CandidateCheckV1, ObstructionMeasurementV1, is_sha256_ref, sha256_ref

MINING_TRIGGERS = frozenset(
    {"EXACT_REPAIR", "DEFECT_HUNTER_REFUTATION", "FALSE_GREEN", "STRUCTURAL_DEFECT"}
)
MINED_KINDS = frozenset({"SKILL", "ANTIBODY", "INVARIANT_RULE"})


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _text(value: str, label: str, *, empty: bool = False) -> None:
    if type(value) is not str or (not empty and not value.strip()):
        raise ValueError(
            f"{label} must be an exact {'possibly empty' if empty else 'nonempty'} str"
        )


def _refs(value: tuple[str, ...], label: str) -> None:
    if type(value) is not tuple or any(not is_sha256_ref(item) for item in value):
        raise TypeError(f"{label} must be an exact tuple of sha256 references")
    if tuple(sorted(set(value))) != value:
        raise ValueError(f"{label} must be unique and sorted")


@dataclass(frozen=True, slots=True)
class MiningObservationV1:
    """Exact source-event, candidate, and declared carrier bytes for one replay.

    Source events are not authenticated by a caller flag: the injected replay
    port must validate their custody and reproduce the host check itself.
    """

    candidate_id: str
    candidate_bytes: bytes
    carrier_bytes: bytes
    source_event_bytes: bytes
    trigger: str
    failure_class: str = ""
    target_pattern: str = ""

    def __post_init__(self) -> None:
        _text(self.candidate_id, "candidate_id")
        if type(self.trigger) is not str or self.trigger not in MINING_TRIGGERS:
            raise ValueError("unknown mining trigger")
        for name in ("candidate_bytes", "carrier_bytes", "source_event_bytes"):
            if type(getattr(self, name)) is not bytes or not getattr(self, name):
                raise TypeError(f"{name} must be nonempty exact bytes")
        for name in ("failure_class", "target_pattern"):
            _text(getattr(self, name), name, empty=self.trigger == "EXACT_REPAIR")
        if self.trigger == "EXACT_REPAIR" and (self.failure_class or self.target_pattern):
            raise ValueError("EXACT_REPAIR carries no alleged failure pattern")

    @property
    def subject_ref(self) -> str:
        return sha256_ref(self.candidate_bytes)

    @property
    def carrier_ref(self) -> str:
        return sha256_ref(self.carrier_bytes)

    @property
    def source_event_ref(self) -> str:
        return sha256_ref(self.source_event_bytes)

    @property
    def observation_ref(self) -> str:
        return sha256_ref(canonical_bytes(self.to_dict()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "core.adversary.mining-observation.v1",
            "candidate_id": self.candidate_id,
            "candidate_content_sha256": self.subject_ref,
            "carrier_context_sha256": self.carrier_ref,
            "source_event_sha256": self.source_event_ref,
            "trigger": self.trigger,
            "failure_class": self.failure_class,
            "target_pattern": self.target_pattern,
        }

    def __hash__(self) -> int:
        return hash((type(self), self.observation_ref))


@dataclass(frozen=True, slots=True)
class ReplayedMiningEvidenceV1:
    """A trusted host replay's evidence, still checked for packet substitution.

    A receipt alone cannot reproduce a mathematical result. The replay port
    owns exact host/certificate verification; the miner owns binding and
    eligibility checks. No production replay adapter is supplied by default.
    """

    observation_ref: str
    candidate_check: CandidateCheckV1
    measurement: ObstructionMeasurementV1 | None = None
    measurement_receipt_bytes: bytes = b""
    joint_kernel_receipt_bytes: bytes = b""

    def __post_init__(self) -> None:
        if not is_sha256_ref(self.observation_ref):
            raise ValueError("observation_ref must be a sha256 reference")
        if type(self.candidate_check) is not CandidateCheckV1:
            raise TypeError("candidate_check must be an exact CandidateCheckV1")
        if self.measurement is not None and type(self.measurement) is not ObstructionMeasurementV1:
            raise TypeError("measurement must be an exact ObstructionMeasurementV1 or None")
        for name in ("measurement_receipt_bytes", "joint_kernel_receipt_bytes"):
            if type(getattr(self, name)) is not bytes:
                raise TypeError(f"{name} must be exact bytes")

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.observation_ref,
                self.candidate_check,
                self.measurement,
                self.measurement_receipt_bytes,
                self.joint_kernel_receipt_bytes,
            )
        )


class IntelligenceReplayPort(Protocol):
    """Validate source custody and independently rerun exact declared host checks.

    Implementations must bind their result to the complete observation digest,
    verify the native exact measurement certificate and joint-kernel witness,
    and return a refusal when an event, host, or witness is unavailable. Reading
    a stored PASS/REJECTED flag is not an implementation of this protocol.
    """

    def replay(
        self, observation: MiningObservationV1
    ) -> Result[ReplayedMiningEvidenceV1, Refusal]: ...


@dataclass(frozen=True, slots=True)
class MinedCandidateV1:
    """A review candidate whose identity excludes ephemeral observations."""

    kind: str
    failure_class: str
    target_pattern: str
    subject_refs: tuple[str, ...]
    carrier_refs: tuple[str, ...]
    source_event_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    status: str = "CANDIDATE"
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if type(self.kind) is not str or self.kind not in MINED_KINDS:
            raise ValueError("unknown mined candidate kind")
        if self.status != "CANDIDATE" or self.authority_effect != "None":
            raise ValueError("mining cannot admit a candidate or mint authority")
        for name in ("failure_class", "target_pattern"):
            _text(getattr(self, name), name, empty=self.kind == "SKILL")
        for name in ("subject_refs", "carrier_refs", "source_event_refs", "evidence_refs"):
            _refs(getattr(self, name), name)
            if not getattr(self, name):
                raise ValueError(f"{name} cannot be empty")
        if self.kind == "SKILL" and (self.failure_class or self.target_pattern):
            raise ValueError("skill candidate carries no failure class")
        if self.kind == "INVARIANT_RULE" and len(self.source_event_refs) < 2:
            raise ValueError("invariant candidate requires distinct source events")

    @property
    def candidate_ref(self) -> str:
        semantic: dict[str, Any] = {
            "schema_version": "core.adversary.mined-candidate.v1",
            "kind": self.kind,
            "failure_class": self.failure_class,
            "target_pattern": self.target_pattern,
        }
        if self.kind == "SKILL":
            semantic.update(subject_refs=self.subject_refs, carrier_refs=self.carrier_refs)
        return sha256_ref(canonical_bytes(semantic))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "core.adversary.mined-candidate.v1",
            "candidate_ref": self.candidate_ref,
            "kind": self.kind,
            "failure_class": self.failure_class,
            "target_pattern": self.target_pattern,
            "subject_refs": list(self.subject_refs),
            "carrier_refs": list(self.carrier_refs),
            "source_event_refs": list(self.source_event_refs),
            "evidence_refs": list(self.evidence_refs),
            "distinct_source_events": len(self.source_event_refs),
            "status": self.status,
            "AuthorityEffect": self.authority_effect,
        }

    def __hash__(self) -> int:
        return hash((type(self), canonical_bytes(self.to_dict())))


@dataclass(frozen=True, slots=True)
class MiningResidualV1:
    observation_ref: str
    code: str
    message: str

    def __post_init__(self) -> None:
        if not is_sha256_ref(self.observation_ref):
            raise ValueError("residual requires an observation reference")
        _text(self.code, "code")
        _text(self.message, "message")

    def to_dict(self) -> dict[str, str]:
        return {
            "observation_ref": self.observation_ref,
            "code": self.code,
            "message": self.message,
        }

    def __hash__(self) -> int:
        return hash((type(self), self.observation_ref, self.code, self.message))


@dataclass(frozen=True, slots=True)
class IntelligenceHarvestV1:
    candidates: tuple[MinedCandidateV1, ...]
    residuals: tuple[MiningResidualV1, ...]
    distinct_observations: int

    def __post_init__(self) -> None:
        for name, expected in (("candidates", MinedCandidateV1), ("residuals", MiningResidualV1)):
            values = getattr(self, name)
            if type(values) is not tuple or any(type(item) is not expected for item in values):
                raise TypeError(f"{name} must be an exact typed tuple")
        if type(self.distinct_observations) is not int or self.distinct_observations < 0:
            raise TypeError("distinct_observations must be a nonnegative exact int")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "core.adversary.intelligence-harvest.v1",
            "candidates": [item.to_dict() for item in self.candidates],
            "residuals": [item.to_dict() for item in self.residuals],
            "distinct_observations": self.distinct_observations,
            "AuthorityEffect": "None",
        }

    def __hash__(self) -> int:
        return hash((type(self), self.candidates, self.residuals, self.distinct_observations))
