"""Strict, content-addressable evidence bundles for research OESOS runs.

The ordinary :class:`~.orchestrator.RunReceipt` is an in-memory verifier
receipt.  This module publishes the smaller closed transport surface needed to
reconcile its packet, runtime, event-chain, wire-receipt, and candidate
identities without importing a solver implementation.  It does not grant
authority: every admitted layer has ``authority_effect == "None"`` and the
wire receipt continues to require independent replay.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from omega_engine_pfp.domain.shared_kernel.canonical import (
    CanonicalizationError,
    canonical_unwire,
    canonical_wire,
    domain_digest,
    freeze,
    thaw,
)
from .obstruction import DdaLetter
from .process_event import ProcessEvent, verify_event_chain
from .candidate_artifact import CandidateArtifactV1
from .packet_envelope import EvaluationReceiptV1, PacketEnvelopeV2


OESOS_EVIDENCE_BUNDLE_SCHEMA = "omega.oesos.evidence-bundle.v1"
RUNTIME_IDENTITY_SCHEMA = "omega.oesos.runtime-problem-identity.v1"
OESOS_EVIDENCE_BUNDLE_MEDIA_TYPE = "application/vnd.omega.oesos-evidence+json"
MAX_CANDIDATES = 4096
MAX_PROCESS_EVENTS = 65536

_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SAFE_PREFIX = re.compile(r"^[A-Za-z0-9_.-]+$")
_RUNTIME_FIELDS = frozenset(
    {
        "schema_version",
        "runtime_id",
        "packet_id",
        "projector_id",
        "projector_config_digest",
        "adapter_id",
        "adapter_config_digest",
        "native_initial_state",
        "detector_cases",
        "primitive_difference",
        "zero_relation",
        "observer_id",
        "witness_certificate",
        "protected_obstruction_ids",
        "cochain_declared",
        "authority_effect",
    }
)
_EVENT_FIELDS = frozenset(
    {
        "sequence",
        "event_type",
        "dda_letter",
        "input_state_hash",
        "output_state_hash",
        "details",
        "parent_hash",
        "event_hash",
        "authority_effect",
    }
)
_BUNDLE_FIELDS = frozenset(
    {
        "schema_version",
        "bundle_id",
        "research_parent_packet_id",
        "packet_envelope",
        "runtime_problem",
        "evaluation_receipt",
        "wire_receipt_id",
        "candidates",
        "process_events",
        "authority_effect",
    }
)


class OesosEvidenceBundleError(CanonicalizationError):
    """Raised when an OESOS evidence bundle fails closed."""


def _exact_object(
    value: Any,
    fields: frozenset[str],
    label: str,
) -> Mapping[str, Any]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise OesosEvidenceBundleError(f"{label} must be an exact JSON object")
    actual = frozenset(value)
    missing = fields - actual
    unknown = actual - fields
    if missing:
        raise OesosEvidenceBundleError(
            f"{label} is missing fields: {', '.join(sorted(missing))}"
        )
    if unknown:
        raise OesosEvidenceBundleError(
            f"{label} has unknown fields: {', '.join(sorted(unknown))}"
        )
    return value


def _digest(value: Any, label: str) -> str:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        raise OesosEvidenceBundleError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _optional_digest(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _digest(value, label)


def _string(value: Any, label: str, *, nonempty: bool = True) -> str:
    if type(value) is not str or (nonempty and not value):
        raise OesosEvidenceBundleError(f"{label} must be a string")
    return value


def _string_array(value: Any, label: str) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise OesosEvidenceBundleError(f"{label} must be an array of strings")
    return tuple(value)


def _none_authority(value: Any, label: str) -> None:
    """Refuse authority expansion hidden in canonical mappings/dataclasses."""

    primitive = thaw(freeze(value))

    def visit(node: Any, location: str) -> None:
        if type(node) is list:
            for index, item in enumerate(node):
                visit(item, f"{location}[{index}]")
            return
        if type(node) is not dict:
            return
        if "authority_effect" in node and node["authority_effect"] != "None":
            raise OesosEvidenceBundleError(f"{location}.authority_effect must be None")
        dataclass_fields = node.get("fields") if "$dataclass" in node else None
        if type(dataclass_fields) is list:
            for index, item in enumerate(dataclass_fields):
                if type(item) is not list or len(item) != 2 or type(item[0]) is not str:
                    raise OesosEvidenceBundleError(
                        f"{location}.fields[{index}] is not a canonical field"
                    )
                if item[0] == "authority_effect" and item[1] != "None":
                    raise OesosEvidenceBundleError(
                        f"{location}.authority_effect must be None"
                    )
                visit(item[1], f"{location}.{item[0]}")
        for key, item in node.items():
            if key != "fields":
                visit(item, f"{location}.{key}")

    visit(primitive, label)


@dataclass(frozen=True, slots=True)
class RuntimeProblemIdentityV1:
    """The exact data projection used by ``RuntimeProblem.runtime_id``."""

    packet_id: str
    projector_id: str
    projector_config_digest: str
    adapter_id: str
    adapter_config_digest: str
    native_initial_state: Any
    detector_cases: Any
    primitive_difference: str
    zero_relation: str
    observer_id: str
    witness_certificate: str
    protected_obstruction_ids: tuple[str, ...]
    cochain_declared: bool
    schema_version: str = field(default=RUNTIME_IDENTITY_SCHEMA)
    authority_effect: str = field(default="None")

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "native_initial_state", freeze(self.native_initial_state)
        )
        object.__setattr__(self, "detector_cases", freeze(self.detector_cases))
        self._validate()

    def _validate(self) -> None:
        if self.schema_version != RUNTIME_IDENTITY_SCHEMA:
            raise OesosEvidenceBundleError("runtime identity schema is unsupported")
        if self.authority_effect != "None":
            raise OesosEvidenceBundleError(
                "runtime identity authority effect must be None"
            )
        _digest(self.packet_id, "runtime_problem.packet_id")
        _digest(
            self.projector_config_digest,
            "runtime_problem.projector_config_digest",
        )
        _digest(self.adapter_config_digest, "runtime_problem.adapter_config_digest")
        for label, value in (
            ("projector_id", self.projector_id),
            ("adapter_id", self.adapter_id),
            ("primitive_difference", self.primitive_difference),
            ("zero_relation", self.zero_relation),
            ("observer_id", self.observer_id),
            ("witness_certificate", self.witness_certificate),
        ):
            _string(value, f"runtime_problem.{label}")
        if type(self.protected_obstruction_ids) is not tuple or any(
            type(item) is not str or not item for item in self.protected_obstruction_ids
        ):
            raise OesosEvidenceBundleError(
                "runtime_problem.protected_obstruction_ids must be strings"
            )
        if type(self.cochain_declared) is not bool:
            raise OesosEvidenceBundleError(
                "runtime_problem.cochain_declared must be a boolean"
            )
        _none_authority(
            self.native_initial_state, "runtime_problem.native_initial_state"
        )
        _none_authority(self.detector_cases, "runtime_problem.detector_cases")

    def runtime_fields(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "projector_id": self.projector_id,
            "projector_config_digest": self.projector_config_digest,
            "adapter_id": self.adapter_id,
            "adapter_config_digest": self.adapter_config_digest,
            "native_initial_state": self.native_initial_state,
            "detector_cases": self.detector_cases,
            "primitive_difference": self.primitive_difference,
            "zero_relation": self.zero_relation,
            "observer_id": self.observer_id,
            "witness_certificate": self.witness_certificate,
            "protected_obstruction_ids": self.protected_obstruction_ids,
            "cochain_declared": self.cochain_declared,
        }

    @property
    def runtime_id(self) -> str:
        return domain_digest("omega.oesos.runtime-problem.v1", self.runtime_fields())

    @classmethod
    def from_problem(cls, problem: RuntimeProblem) -> "RuntimeProblemIdentityV1":
        if type(problem) is not RuntimeProblem:
            raise OesosEvidenceBundleError("problem must be an exact RuntimeProblem")
        return cls(
            packet_id=problem.envelope.packet_id,
            projector_id=problem.projector.projector_id,
            projector_config_digest=getattr(problem.projector, "config_digest", ""),
            adapter_id=problem.adapter.adapter_id,
            adapter_config_digest=getattr(problem.adapter, "config_digest", ""),
            native_initial_state=problem.native_initial_state,
            detector_cases=problem.detector_cases,
            primitive_difference=problem.primitive_difference,
            zero_relation=problem.zero_relation,
            observer_id=problem.observer_id,
            witness_certificate=problem.witness_certificate,
            protected_obstruction_ids=problem.protected_obstruction_ids,
            cochain_declared=problem.cochain_declared,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "runtime_id": self.runtime_id,
            "packet_id": self.packet_id,
            "projector_id": self.projector_id,
            "projector_config_digest": self.projector_config_digest,
            "adapter_id": self.adapter_id,
            "adapter_config_digest": self.adapter_config_digest,
            "native_initial_state": canonical_wire(self.native_initial_state),
            "detector_cases": canonical_wire(self.detector_cases),
            "primitive_difference": self.primitive_difference,
            "zero_relation": self.zero_relation,
            "observer_id": self.observer_id,
            "witness_certificate": self.witness_certificate,
            "protected_obstruction_ids": list(self.protected_obstruction_ids),
            "cochain_declared": self.cochain_declared,
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RuntimeProblemIdentityV1":
        wire = _exact_object(value, _RUNTIME_FIELDS, "runtime problem identity")
        expected_runtime_id = _digest(wire["runtime_id"], "runtime_problem.runtime_id")
        if wire["schema_version"] != RUNTIME_IDENTITY_SCHEMA:
            raise OesosEvidenceBundleError("runtime identity schema is unsupported")
        if wire["authority_effect"] != "None":
            raise OesosEvidenceBundleError(
                "runtime identity authority effect must be None"
            )
        if type(wire["cochain_declared"]) is not bool:
            raise OesosEvidenceBundleError(
                "runtime_problem.cochain_declared must be a boolean"
            )
        runtime = cls(
            packet_id=_digest(wire["packet_id"], "runtime_problem.packet_id"),
            projector_id=_string(wire["projector_id"], "runtime_problem.projector_id"),
            projector_config_digest=_digest(
                wire["projector_config_digest"],
                "runtime_problem.projector_config_digest",
            ),
            adapter_id=_string(wire["adapter_id"], "runtime_problem.adapter_id"),
            adapter_config_digest=_digest(
                wire["adapter_config_digest"],
                "runtime_problem.adapter_config_digest",
            ),
            native_initial_state=canonical_unwire(wire["native_initial_state"]),
            detector_cases=canonical_unwire(wire["detector_cases"]),
            primitive_difference=_string(
                wire["primitive_difference"], "runtime_problem.primitive_difference"
            ),
            zero_relation=_string(
                wire["zero_relation"], "runtime_problem.zero_relation"
            ),
            observer_id=_string(wire["observer_id"], "runtime_problem.observer_id"),
            witness_certificate=_string(
                wire["witness_certificate"], "runtime_problem.witness_certificate"
            ),
            protected_obstruction_ids=_string_array(
                wire["protected_obstruction_ids"],
                "runtime_problem.protected_obstruction_ids",
            ),
            cochain_declared=wire["cochain_declared"],
            schema_version=wire["schema_version"],
            authority_effect=wire["authority_effect"],
        )
        if runtime.runtime_id != expected_runtime_id:
            raise OesosEvidenceBundleError(
                "runtime_id does not match the serialized runtime identity"
            )
        return runtime


def _event_to_dict(event: ProcessEvent) -> dict[str, Any]:
    return {
        "sequence": event.sequence,
        "event_type": event.event_type,
        "dda_letter": event.dda_letter,
        "input_state_hash": event.input_state_hash,
        "output_state_hash": event.output_state_hash,
        "details": canonical_wire(event.details),
        "parent_hash": event.parent_hash,
        "event_hash": event.event_hash,
        "authority_effect": event.authority_effect,
    }


def _event_from_dict(value: Any, index: int) -> ProcessEvent:
    label = f"process_events[{index}]"
    wire = _exact_object(value, _EVENT_FIELDS, label)
    if type(wire["sequence"]) is not int or wire["sequence"] < 0:
        raise OesosEvidenceBundleError(
            f"{label}.sequence must be a nonnegative integer"
        )
    if wire["authority_effect"] != "None":
        raise OesosEvidenceBundleError(f"{label}.authority_effect must be None")
    dda_letter = _string(wire["dda_letter"], f"{label}.dda_letter")
    if dda_letter not in {letter.value for letter in DdaLetter}:
        raise OesosEvidenceBundleError(f"{label}.dda_letter is unsupported")
    details = canonical_unwire(wire["details"])
    _none_authority(details, f"{label}.details")
    return ProcessEvent(
        sequence=wire["sequence"],
        event_type=_string(wire["event_type"], f"{label}.event_type"),
        dda_letter=dda_letter,
        input_state_hash=_digest(wire["input_state_hash"], f"{label}.input_state_hash"),
        output_state_hash=_digest(
            wire["output_state_hash"], f"{label}.output_state_hash"
        ),
        details=details,
        parent_hash=_optional_digest(wire["parent_hash"], f"{label}.parent_hash"),
        event_hash=_digest(wire["event_hash"], f"{label}.event_hash"),
        authority_effect=wire["authority_effect"],
    )


@dataclass(frozen=True, slots=True)
class OesosEvidenceBundleV1:
    """Closed transport evidence for one parent-bound OESOS run."""

    research_parent_packet_id: str
    packet_envelope: PacketEnvelopeV2
    runtime_problem: RuntimeProblemIdentityV1
    evaluation_receipt: EvaluationReceiptV1
    wire_receipt_id: str
    candidates: tuple[CandidateArtifactV1, ...]
    process_events: tuple[ProcessEvent, ...]
    schema_version: str = field(default=OESOS_EVIDENCE_BUNDLE_SCHEMA)
    authority_effect: str = field(default="None")

    def __post_init__(self) -> None:
        self._validate()

    def identity_fields(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "research_parent_packet_id": self.research_parent_packet_id,
            "packet_envelope": self.packet_envelope,
            "runtime_problem": self.runtime_problem,
            "evaluation_receipt": self.evaluation_receipt,
            "wire_receipt_id": self.wire_receipt_id,
            "candidates": self.candidates,
            "process_events": self.process_events,
            "authority_effect": self.authority_effect,
        }

    @property
    def bundle_id(self) -> str:
        return domain_digest(OESOS_EVIDENCE_BUNDLE_SCHEMA, self.identity_fields())

    def _validate(self) -> None:
        if self.schema_version != OESOS_EVIDENCE_BUNDLE_SCHEMA:
            raise OesosEvidenceBundleError("OESOS evidence schema is unsupported")
        if self.authority_effect != "None":
            raise OesosEvidenceBundleError("bundle authority effect must be None")
        parent = _digest(self.research_parent_packet_id, "research_parent_packet_id")
        if type(self.packet_envelope) is not PacketEnvelopeV2:
            raise OesosEvidenceBundleError("packet_envelope has the wrong type")
        if type(self.runtime_problem) is not RuntimeProblemIdentityV1:
            raise OesosEvidenceBundleError("runtime_problem has the wrong type")
        if type(self.evaluation_receipt) is not EvaluationReceiptV1:
            raise OesosEvidenceBundleError("evaluation_receipt has the wrong type")
        if type(self.candidates) is not tuple or len(self.candidates) > MAX_CANDIDATES:
            raise OesosEvidenceBundleError("candidates exceed the closed array bound")
        if type(self.process_events) is not tuple or not self.process_events:
            raise OesosEvidenceBundleError("process_events must be a nonempty tuple")
        if len(self.process_events) > MAX_PROCESS_EVENTS:
            raise OesosEvidenceBundleError(
                "process_events exceed the closed array bound"
            )

        # Round-trip each imported transport type through its own strict parser.
        PacketEnvelopeV2.from_dict(self.packet_envelope.to_dict())
        RuntimeProblemIdentityV1.from_dict(self.runtime_problem.to_dict())
        EvaluationReceiptV1.from_dict(self.evaluation_receipt.to_dict())
        for candidate in self.candidates:
            if type(candidate) is not CandidateArtifactV1:
                raise OesosEvidenceBundleError("candidate has the wrong type")
            CandidateArtifactV1.from_dict(candidate.to_dict())
            _none_authority(candidate.payload, "candidate.payload")
            _none_authority(candidate.metadata, "candidate.metadata")
        for event in self.process_events:
            if type(event) is not ProcessEvent:
                raise OesosEvidenceBundleError("process event has the wrong type")
            _event_from_dict(_event_to_dict(event), event.sequence)

        receipt = self.evaluation_receipt
        packet = self.packet_envelope
        runtime = self.runtime_problem
        _digest(self.wire_receipt_id, "wire_receipt_id")
        if receipt.receipt_id != self.wire_receipt_id:
            raise OesosEvidenceBundleError("wire_receipt_id does not match the receipt")
        if packet.parent_event_id != parent or receipt.parent_event_id != parent:
            raise OesosEvidenceBundleError(
                "packet and receipt do not bind the research parent packet"
            )
        if (
            runtime.packet_id != packet.packet_id
            or receipt.packet_id != packet.packet_id
        ):
            raise OesosEvidenceBundleError(
                "packet identities do not reconcile across bundle layers"
            )
        if runtime.runtime_id != receipt.runtime_id:
            raise OesosEvidenceBundleError(
                "runtime identity does not match the evaluation receipt"
            )
        _none_authority(packet.payload, "packet_envelope.payload")

        if not verify_event_chain(self.process_events, parent):
            raise OesosEvidenceBundleError("process event chain failed replay")
        first = self.process_events[0]
        terminal = self.process_events[-1]
        if (
            first.event_type != "declare-carrier"
            or first.input_state_hash != receipt.input_state_hash
            or first.output_state_hash != receipt.input_state_hash
            or first.details
            != freeze({"packet_id": packet.packet_id, "runtime_id": runtime.runtime_id})
        ):
            raise OesosEvidenceBundleError(
                "declaration event does not bind packet, runtime, and input state"
            )
        if (
            terminal.event_type != "terminal"
            or terminal.dda_letter != DdaLetter.T.value
            or terminal.input_state_hash != receipt.output_state_hash
            or terminal.output_state_hash != receipt.output_state_hash
            or terminal.event_hash != receipt.event_root
        ):
            raise OesosEvidenceBundleError(
                "terminal event does not bind the evaluation receipt"
            )
        terminal_details = thaw(terminal.details)
        expected_active = {"$tuple": list(receipt.active_obstructions)}
        if (
            type(terminal_details) is not dict
            or terminal_details.get("terminal_status") != receipt.terminal_status
            or terminal_details.get("active_obstructions") != expected_active
        ):
            raise OesosEvidenceBundleError(
                "terminal event details do not reconcile with the receipt"
            )

        referenced = tuple(receipt.candidate_ids)
        observed = tuple(candidate.candidate_id for candidate in self.candidates)
        if observed != referenced:
            raise OesosEvidenceBundleError(
                "candidate artifacts do not match receipt attempt references"
            )
        candidate_attempts = tuple(
            attempt for attempt in receipt.attempts if attempt.candidate_id is not None
        )
        for attempt, candidate in zip(candidate_attempts, self.candidates):
            if candidate.producer_id != attempt.solver_id:
                raise OesosEvidenceBundleError(
                    "candidate producer does not match the referring attempt"
                )
            if attempt.accepted and candidate.packet_id != packet.packet_id:
                raise OesosEvidenceBundleError(
                    "accepted candidate does not bind the evaluated packet"
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bundle_id": self.bundle_id,
            "research_parent_packet_id": self.research_parent_packet_id,
            "packet_envelope": self.packet_envelope.to_dict(),
            "runtime_problem": self.runtime_problem.to_dict(),
            "evaluation_receipt": self.evaluation_receipt.to_dict(),
            "wire_receipt_id": self.wire_receipt_id,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "process_events": [_event_to_dict(event) for event in self.process_events],
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "OesosEvidenceBundleV1":
        wire = _exact_object(value, _BUNDLE_FIELDS, "OESOS evidence bundle")
        expected_bundle_id = _digest(wire["bundle_id"], "bundle_id")
        if wire["schema_version"] != OESOS_EVIDENCE_BUNDLE_SCHEMA:
            raise OesosEvidenceBundleError("OESOS evidence schema is unsupported")
        if wire["authority_effect"] != "None":
            raise OesosEvidenceBundleError("bundle authority effect must be None")
        raw_candidates = wire["candidates"]
        raw_events = wire["process_events"]
        if type(raw_candidates) is not list or len(raw_candidates) > MAX_CANDIDATES:
            raise OesosEvidenceBundleError("candidates exceed the closed array bound")
        if (
            type(raw_events) is not list
            or not raw_events
            or len(raw_events) > MAX_PROCESS_EVENTS
        ):
            raise OesosEvidenceBundleError(
                "process_events must be a nonempty bounded array"
            )
        try:
            packet = PacketEnvelopeV2.from_dict(wire["packet_envelope"])
            runtime = RuntimeProblemIdentityV1.from_dict(wire["runtime_problem"])
            receipt = EvaluationReceiptV1.from_dict(wire["evaluation_receipt"])
            candidates = tuple(
                CandidateArtifactV1.from_dict(item) for item in raw_candidates
            )
            events = tuple(
                _event_from_dict(item, index) for index, item in enumerate(raw_events)
            )
        except OesosEvidenceBundleError:
            raise
        except Exception as exc:
            raise OesosEvidenceBundleError(
                "nested OESOS evidence transport failed strict parsing"
            ) from exc
        bundle = cls(
            research_parent_packet_id=_digest(
                wire["research_parent_packet_id"], "research_parent_packet_id"
            ),
            packet_envelope=packet,
            runtime_problem=runtime,
            evaluation_receipt=receipt,
            wire_receipt_id=_digest(wire["wire_receipt_id"], "wire_receipt_id"),
            candidates=candidates,
            process_events=events,
            schema_version=wire["schema_version"],
            authority_effect=wire["authority_effect"],
        )
        if bundle.bundle_id != expected_bundle_id:
            raise OesosEvidenceBundleError(
                "bundle_id does not match the serialized evidence"
            )
        return bundle


def build_oesos_evidence_bundle(
    problem: RuntimeProblem,
    run: RunReceipt,
    *,
    research_parent_packet_id: str,
) -> OesosEvidenceBundleV1:
    """Build and reconcile a strict bundle from a verifier-valid OESOS run."""

    parent = _digest(research_parent_packet_id, "research_parent_packet_id")
    if type(problem) is not RuntimeProblem:
        raise OesosEvidenceBundleError("problem must be an exact RuntimeProblem")
    if type(run) is not RunReceipt:
        raise OesosEvidenceBundleError("run must be an exact RunReceipt")
    if not run.evidence_valid():
        raise OesosEvidenceBundleError("run receipt evidence is invalid")
    if problem.envelope.parent_event_id != parent or run.parent_event_id != parent:
        raise OesosEvidenceBundleError("run is not bound to the research parent packet")
    runtime = RuntimeProblemIdentityV1.from_problem(problem)
    if (
        problem.envelope.packet_id != run.packet_id
        or runtime.runtime_id != problem.runtime_id
        or runtime.runtime_id != run.runtime_id
    ):
        raise OesosEvidenceBundleError(
            "problem and run packet/runtime identities do not reconcile"
        )
    receipt = run.to_wire_receipt()
    return OesosEvidenceBundleV1(
        research_parent_packet_id=parent,
        packet_envelope=problem.envelope,
        runtime_problem=runtime,
        evaluation_receipt=receipt,
        wire_receipt_id=receipt.receipt_id,
        candidates=run.candidate_artifacts,
        process_events=run.process_events,
    )


def verify_oesos_evidence_bundle(
    bundle: OesosEvidenceBundleV1,
    *,
    expected_research_parent_packet_id: str | None = None,
) -> bool:
    """Reparse and reconcile every bundle identity, raising on refusal."""

    if type(bundle) is not OesosEvidenceBundleV1:
        raise OesosEvidenceBundleError("bundle must be OesosEvidenceBundleV1")
    reparsed = OesosEvidenceBundleV1.from_dict(bundle.to_dict())
    if expected_research_parent_packet_id is not None and (
        reparsed.research_parent_packet_id
        != _digest(
            expected_research_parent_packet_id,
            "expected_research_parent_packet_id",
        )
    ):
        raise OesosEvidenceBundleError("bundle binds a different research parent")
    return True


def _duplicate_rejecting_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise OesosEvidenceBundleError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _artifact_bytes(bundle: OesosEvidenceBundleV1) -> bytes:
    try:
        encoded = json.dumps(
            bundle.to_dict(),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise OesosEvidenceBundleError(
            "bundle has no strict JSON representation"
        ) from exc
    return (encoded + "\n").encode("utf-8")


def write_oesos_evidence_bundle(
    bundle: OesosEvidenceBundleV1,
    output_directory: str | Path,
    *,
    filename_prefix: str = "oesos_evidence_bundle_v1",
) -> Path:
    """Exclusively write ``<prefix>_<content-sha256>.json`` evidence."""

    verify_oesos_evidence_bundle(bundle)
    if (
        type(filename_prefix) is not str
        or _SAFE_PREFIX.fullmatch(filename_prefix) is None
    ):
        raise OesosEvidenceBundleError("filename_prefix contains unsafe characters")
    content = _artifact_bytes(bundle)
    content_digest = hashlib.sha256(content).hexdigest()
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{filename_prefix}_{content_digest}.json"
    try:
        with path.open("xb") as stream:
            stream.write(content)
    except FileExistsError:
        try:
            existing = path.read_bytes()
        except OSError as exc:
            raise OesosEvidenceBundleError(
                f"cannot inspect evidence-bundle collision: {path}"
            ) from exc
        if existing != content:
            raise OesosEvidenceBundleError(
                f"content-addressed evidence-bundle collision: {path}"
            )
    return path


def read_oesos_evidence_bundle(path: str | Path) -> OesosEvidenceBundleV1:
    """Read strict JSON (including duplicate-key rejection) and verify it."""

    candidate = Path(path)
    try:
        value = json.loads(
            candidate.read_text(encoding="utf-8"),
            object_pairs_hook=_duplicate_rejecting_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                OesosEvidenceBundleError(f"non-finite JSON number: {token}")
            ),
        )
    except OesosEvidenceBundleError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OesosEvidenceBundleError(
            f"cannot read OESOS evidence bundle: {candidate}"
        ) from exc
    bundle = OesosEvidenceBundleV1.from_dict(value)
    verify_oesos_evidence_bundle(bundle)
    return bundle


__all__ = [
    "MAX_CANDIDATES",
    "MAX_PROCESS_EVENTS",
    "OESOS_EVIDENCE_BUNDLE_MEDIA_TYPE",
    "OESOS_EVIDENCE_BUNDLE_SCHEMA",
    "RUNTIME_IDENTITY_SCHEMA",
    "OesosEvidenceBundleError",
    "OesosEvidenceBundleV1",
    "RuntimeProblemIdentityV1",
    "build_oesos_evidence_bundle",
    "read_oesos_evidence_bundle",
    "verify_oesos_evidence_bundle",
    "write_oesos_evidence_bundle",
]
