"""Declared rational graph tasks and inert, byte-bound execution evidence.

Origin: adversary domain schema core.adversary.graph-task.v1.
Claim: an admitted task binds a frozen edge basis, a repair catalog, and exact Fraction weights.
Scope fence: this file does not claim a mathematical certificate. Rust owns the mathematics.
Source spans record a human interpretation; they do not prove its semantics.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from adversary.domain.evidence import (
    CandidateCheckV1,
    CheckerVerdict,
    ObstructionMeasurementV1,
    canonical_rational,
    parse_exact_rational,
    sha256_ref,
)
from adversary.domain.intelligence_mining import canonical_bytes
from adversary.domain.network import Network
from adversary.domain.projection import (
    HumanProblemCarrier,
    ProjectionRetraction,
    SourceSpan,
)

TASK_SCHEMA = "core.adversary.graph-task.v1"
CANDIDATE_SCHEMA = "core.adversary.graph-candidate.v1"
MAX_TASK_BYTES = 1_048_576
MAX_CANDIDATE_BYTES = 16_384


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON constant: {value}")


def read_json(raw: bytes, limit: int = MAX_TASK_BYTES) -> Any:
    if type(raw) is not bytes or not raw or len(raw) > limit:
        raise ValueError("empty or oversized exact JSON bytes")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_constant)


def _keys(value: Any, names: set[str]) -> dict[str, Any]:
    if type(value) is not dict or set(value) != names:
        raise ValueError(f"expected exactly these fields: {sorted(names)}")
    return value


def _text(value: Any, name: str, limit: int = 128) -> str:
    if type(value) is not str or not value.strip() or len(value.encode("utf-8")) > limit:
        raise ValueError(f"{name} requires bounded nonempty text")
    return value


def _rational(value: Any) -> Fraction:
    if type(value) is not str or len(value) > 256:
        raise ValueError("coefficients must be bounded canonical rational strings")
    result = parse_exact_rational(value)
    if canonical_rational(result) != value:
        raise ValueError("coefficient is not a canonical rational string")
    return result


@dataclass(frozen=True, slots=True)
class GraphPatchV1:
    edits: tuple[tuple[str, Fraction], ...] = ()

    def __post_init__(self) -> None:
        if type(self.edits) is not tuple or len(self.edits) > 64:
            raise ValueError("patch requires at most 64 frozen edits")
        for edge, value in self.edits:
            _text(edge, "edge_id")
            if type(value) is not Fraction:
                raise TypeError("patch values must be exact Fractions")
        if len({edge for edge, _ in self.edits}) != len(self.edits):
            raise ValueError("duplicate patch edge")

    def to_dict(self) -> dict[str, Any]:
        return {
            "patch": [
                {"edge_id": edge, "value": canonical_rational(value)} for edge, value in self.edits
            ]
        }

    @classmethod
    def from_dict(cls, data: Any) -> GraphPatchV1:
        entries = _keys(data, {"patch"})["patch"]
        if type(entries) is not list or len(entries) > 64:
            raise ValueError("patch must be a bounded array")
        rows = [_keys(row, {"edge_id", "value"}) for row in entries]
        return cls(
            tuple((_text(row["edge_id"], "edge_id"), _rational(row["value"])) for row in rows)
        )


@dataclass(frozen=True, slots=True)
class GraphObserverV1:
    observer_id: str
    edge_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.observer_id, "observer_id")
        if type(self.edge_ids) is not tuple or len(self.edge_ids) > 64:
            raise ValueError("observer must declare a frozen bounded edge selection")
        for edge in self.edge_ids:
            _text(edge, "observer edge")
        if len(set(self.edge_ids)) != len(self.edge_ids):
            raise ValueError("an observer cannot repeat an edge")


def _admit_graph_task_identity(task: "GraphTaskV1") -> None:
    _text(task.task_id, "task_id")
    _text(task.interpretation, "interpretation", 4096)
    if type(task.carrier) is not HumanProblemCarrier:
        raise TypeError("carrier must be an exact HumanProblemCarrier")
    for name in (
        "edge_ids",
        "omega",
        "edit_weights",
        "protected_edges",
        "repair_catalog",
        "observers",
    ):
        if type(getattr(task, name)) is not tuple:
            raise TypeError(f"{name} must be a frozen tuple")
    size = len(task.carrier.network.edges)
    if len(task.edge_ids) != size or len(set(task.edge_ids)) != size:
        raise ValueError("one unique edge ID per declared edge is required")
    for edge in task.edge_ids:
        _text(edge, "edge_id")


def _admit_graph_task_weights(task: "GraphTaskV1") -> None:
    size = len(task.carrier.network.edges)
    if len(task.omega) != size or len(task.edit_weights) != size:
        raise ValueError("one value and edit weight per declared edge is required")
    for value in (*task.omega, *task.edit_weights):
        if type(value) is not Fraction:
            raise TypeError("values and weights must be exact Fractions")
        _rational(canonical_rational(value))
    if any(weight <= 0 for weight in task.edit_weights):
        raise ValueError("edit weights must be strictly positive")
    distinct = len(set(task.protected_edges)) == len(task.protected_edges)
    declared = set(task.protected_edges) <= set(task.edge_ids)
    if not distinct or not declared:
        raise ValueError("protected edges must be distinct declared IDs")


def _admit_graph_catalog_members(task: "GraphTaskV1") -> None:
    patches_exact = all(type(patch) is GraphPatchV1 for patch in task.repair_catalog)
    if not 1 <= len(task.repair_catalog) <= 64 or not patches_exact:
        raise ValueError("catalog requires 1..64 exact patches, including the unchanged graph")
    encoded = [canonical_bytes(patch.to_dict()) for patch in task.repair_catalog]
    if len(set(encoded)) != len(encoded) or GraphPatchV1() not in task.repair_catalog:
        raise ValueError("catalog must be distinct and include the unchanged graph")


def _admit_graph_catalog_order(task: "GraphTaskV1") -> None:
    order = {edge: index for index, edge in enumerate(task.edge_ids)}
    for patch in task.repair_catalog:
        for _, value in patch.edits:
            _rational(canonical_rational(value))
        if any(edge not in order for edge, _ in patch.edits):
            raise ValueError("catalog names an undeclared edge")
        positions = tuple(order[edge] for edge, _ in patch.edits)
        if positions != tuple(sorted(positions)):
            raise ValueError("patch edits must follow the declared edge basis")


def _admit_graph_observers(task: "GraphTaskV1") -> None:
    observers_exact = all(type(observer) is GraphObserverV1 for observer in task.observers)
    if len(task.observers) > 64 or not observers_exact:
        raise ValueError("observer family must contain at most 64 exact declarations")
    if len({observer.observer_id for observer in task.observers}) != len(task.observers):
        raise ValueError("duplicate observer ID")
    if any(not set(observer.edge_ids) <= set(task.edge_ids) for observer in task.observers):
        raise ValueError("observer names an undeclared edge")
    if sum(len(observer.edge_ids) for observer in task.observers) > 64:
        raise ValueError("stacked observer maps exceed the 64-row native ceiling")


def _catalog_candidate_too_wide(task: "GraphTaskV1", reference: str, patch: GraphPatchV1) -> bool:
    payload = {"schema_version": CANDIDATE_SCHEMA, "task_ref": reference, **patch.to_dict()}
    return len(canonical_bytes(payload)) > MAX_CANDIDATE_BYTES


def _admit_graph_budget(task: "GraphTaskV1") -> None:
    if type(task.max_candidates) is not int or not 0 <= task.max_candidates <= 64:
        raise ValueError("max_candidates must be an exact int in 0..64")
    if type(task.critique_rounds) is not int or not 0 <= task.critique_rounds <= 2:
        raise ValueError("critique_rounds must be an exact int in 0..2")
    if len(task.to_bytes()) > MAX_TASK_BYTES:
        raise ValueError("task byte ceiling exceeded")
    reference = sha256_ref(task.to_bytes())
    if any(_catalog_candidate_too_wide(task, reference, patch) for patch in task.repair_catalog):
        raise ValueError("catalog candidate exceeds the declared candidate byte ceiling")


_TASK_ARRAY_KEYS = (
    "edge_ids",
    "omega",
    "protected_edges",
    "repair_catalog",
    "edit_weights",
    "observers",
)


def _require_task_arrays(data: dict[str, Any]) -> None:
    for key in _TASK_ARRAY_KEYS:
        if type(data[key]) is not list:
            raise ValueError(f"{key} must be an array")


def _task_spans(spans: Any) -> tuple[SourceSpan, ...]:
    return tuple(
        SourceSpan(**_keys(item, {"edge_index", "start", "end", "interpretation"}))
        for item in spans
    )


def _task_network(carrier: dict[str, Any]) -> Network:
    return Network(
        tuple(carrier["nodes"]),
        tuple(tuple(edge) for edge in carrier["edges"]),
        tuple(tuple(face) for face in carrier["faces"]),
    )


def _task_observers(rows: list[Any]) -> tuple[GraphObserverV1, ...]:
    observers: list[GraphObserverV1] = []
    for item in rows:
        row = _keys(item, {"observer_id", "edge_ids"})
        if type(row["edge_ids"]) is not list:
            raise ValueError("observer edge_ids must be an array")
        observers.append(GraphObserverV1(row["observer_id"], tuple(row["edge_ids"])))
    return tuple(observers)


def _task_weights(values: list[Any]) -> tuple[Fraction, ...]:
    return tuple(_rational(value) for value in values)


def _task_catalog(rows: list[Any]) -> tuple[GraphPatchV1, ...]:
    return tuple(GraphPatchV1.from_dict(row) for row in rows)


@dataclass(frozen=True, slots=True)
class GraphTaskV1:
    task_id: str
    carrier: HumanProblemCarrier
    interpretation: str
    edge_ids: tuple[str, ...]
    omega: tuple[Fraction, ...]
    protected_edges: tuple[str, ...]
    repair_catalog: tuple[GraphPatchV1, ...]
    edit_weights: tuple[Fraction, ...]
    observers: tuple[GraphObserverV1, ...]
    max_candidates: int = 64
    critique_rounds: int = 2

    def __post_init__(self) -> None:
        _admit_graph_task_identity(self)
        _admit_graph_task_weights(self)
        _admit_graph_catalog_members(self)
        _admit_graph_catalog_order(self)
        _admit_graph_observers(self)
        _admit_graph_budget(self)

    def to_dict(self) -> dict[str, Any]:
        network = self.carrier.network
        return {
            "schema_version": TASK_SCHEMA,
            "task_id": self.task_id,
            "source": {
                "text": self.carrier.prompt,
                "interpretation": self.interpretation,
                "spans": [span.to_dict() for span in self.carrier.source_spans],
            },
            "carrier": {
                "nodes": list(network.nodes),
                "edges": [list(e) for e in network.edges],
                "faces": [list(f) for f in network.faces],
            },
            "edge_ids": list(self.edge_ids),
            "omega": [canonical_rational(v) for v in self.omega],
            "protected_edges": list(self.protected_edges),
            "repair_catalog": [patch.to_dict() for patch in self.repair_catalog],
            "edit_weights": [canonical_rational(v) for v in self.edit_weights],
            "observers": [
                {"observer_id": o.observer_id, "edge_ids": list(o.edge_ids)} for o in self.observers
            ],
            "budget": {
                "max_candidates": self.max_candidates,
                "critique_rounds": self.critique_rounds,
            },
        }

    def to_bytes(self) -> bytes:
        return canonical_bytes(self.to_dict())

    @property
    def task_ref(self) -> str:
        return sha256_ref(self.to_bytes())

    def candidate_bytes(self, patch: GraphPatchV1) -> bytes:
        return canonical_bytes(
            {"schema_version": CANDIDATE_SCHEMA, "task_ref": self.task_ref, **patch.to_dict()}
        )

    def retraction(self, values: tuple[Fraction, ...]) -> ProjectionRetraction:
        if len(values) != len(self.edge_ids):
            raise ValueError("candidate cannot alter the edge basis")
        return ProjectionRetraction(
            "declared-graph-identity-v1",
            tuple(((Fraction(1),),) for _ in values),
            tuple((value,) for value in values),
            tuple((Fraction(1),) for _ in values),
            Fraction(0),
        )

    @classmethod
    def from_bytes(cls, raw: bytes) -> GraphTaskV1:
        data = _keys(
            read_json(raw),
            {
                "schema_version",
                "task_id",
                "source",
                "carrier",
                "edge_ids",
                "omega",
                "protected_edges",
                "repair_catalog",
                "edit_weights",
                "observers",
                "budget",
            },
        )
        if data["schema_version"] != TASK_SCHEMA:
            raise ValueError("graph task schema mismatch")
        source = _keys(data["source"], {"text", "interpretation", "spans"})
        carrier = _keys(data["carrier"], {"nodes", "edges", "faces"})
        budget = _keys(data["budget"], {"max_candidates", "critique_rounds"})
        _require_task_arrays(data)
        return cls(
            data["task_id"],
            HumanProblemCarrier(
                source["text"],
                _task_network(carrier),
                _task_spans(source["spans"]),
            ),
            source["interpretation"],
            tuple(data["edge_ids"]),
            _task_weights(data["omega"]),
            tuple(data["protected_edges"]),
            _task_catalog(data["repair_catalog"]),
            _task_weights(data["edit_weights"]),
            _task_observers(data["observers"]),
            budget["max_candidates"],
            budget["critique_rounds"],
        )


def permitted_values(task: GraphTaskV1, raw: bytes) -> tuple[Fraction, ...]:
    """Reject any attempted reinterpretation or constraint mutation before scoring."""
    data = _keys(read_json(raw, MAX_CANDIDATE_BYTES), {"schema_version", "task_ref", "patch"})
    if data["schema_version"] != CANDIDATE_SCHEMA or data["task_ref"] != task.task_ref:
        raise ValueError("TASK_BINDING_MISMATCH")
    patch = GraphPatchV1.from_dict({"patch": data["patch"]})
    if patch not in task.repair_catalog:
        raise ValueError("PATCH_NOT_IN_CATALOG")
    if raw != task.candidate_bytes(patch):
        raise ValueError(
            "CANDIDATE_LANGUAGE_VIOLATION: actual bytes must match a declared canonical catalog sentence"
        )
    values = list(task.omega)
    for edge, value in patch.edits:
        index = task.edge_ids.index(edge)
        if edge in task.protected_edges and value != task.omega[index]:
            raise ValueError(f"PROTECTED_EDGE_CHANGED: {edge}")
        values[index] = value
    return tuple(values)


def _admit_candidate_binding(item: "GraphCandidateEvaluationV1") -> None:
    if type(item.candidate_bytes) is not bytes or not item.candidate_bytes:
        raise TypeError("candidate evidence requires exact nonempty bytes")
    substituted = (
        type(item.check) is not CandidateCheckV1
        or item.check.candidate_content_sha256 != item.candidate_ref
        or item.check.candidate_id != item.candidate_ref
    )
    if substituted:
        raise ValueError("candidate checker substituted the actual candidate bytes")
    if type(item.native_evidence_bytes) is not bytes:
        raise TypeError("native evidence requires actual bytes")


def _admit_candidate_fields(item: "GraphCandidateEvaluationV1") -> None:
    if item.measurement is not None and type(item.measurement) is not ObstructionMeasurementV1:
        raise TypeError("measurement requires an exact ObstructionMeasurementV1")
    if item.edit_cost is not None and (type(item.edit_cost) is not Fraction or item.edit_cost < 0):
        raise ValueError("edit cost requires a nonnegative exact Fraction")
    if item.observer_sound is not None and type(item.observer_sound) is not bool:
        raise TypeError("observer coverage requires an exact bool or unknown")


def _native_result_contradicts(item: "GraphCandidateEvaluationV1", receipt: dict[str, Any]) -> bool:
    functional = receipt["projection"]["functional_receipt"]
    return (
        receipt["candidate_ref"] != item.candidate_ref
        or parse_exact_rational(functional["phi1"]) != item.measurement.phi1
        or parse_exact_rational(functional["gamma2"]) != item.measurement.gamma2
        or parse_exact_rational(receipt["edit_cost"]) != item.edit_cost
        or receipt["observer_coverage"]["sound"] is not item.observer_sound
    )


def _admit_candidate_native(item: "GraphCandidateEvaluationV1") -> None:
    if item.native_evidence_bytes:
        fields_present = (
            item.check.verdict is CheckerVerdict.ACCEPTED
            and item.measurement is not None
            and item.edit_cost is not None
            and item.observer_sound is not None
        )
        if not fields_present:
            raise ValueError("native evidence requires all independently checked result fields")
        payload = read_json(item.native_evidence_bytes)
        if _native_result_contradicts(item, payload["evaluation"]["result"]):
            raise ValueError("typed result contradicts retained native evidence bytes")
        return
    if item.measurement is not None or item.edit_cost is not None or item.observer_sound is not None:
        raise ValueError("measurement and coverage require actual native evidence bytes")


@dataclass(frozen=True, slots=True)
class GraphCandidateEvaluationV1:
    candidate_bytes: bytes
    check: CandidateCheckV1
    measurement: ObstructionMeasurementV1 | None = None
    edit_cost: Fraction | None = None
    observer_sound: bool | None = None
    native_evidence_bytes: bytes = b""
    reason: str = ""

    def __post_init__(self) -> None:
        _admit_candidate_binding(self)
        _admit_candidate_fields(self)
        _admit_candidate_native(self)

    @property
    def candidate_ref(self) -> str:
        return sha256_ref(self.candidate_bytes)

    @property
    def verified_repair(self) -> bool:
        return (
            self.check.verdict is CheckerVerdict.ACCEPTED
            and self.measurement is not None
            and self.measurement.is_exact_joint_zero()
            and self.observer_sound is True
            and bool(self.native_evidence_bytes)
            and self.edit_cost is not None
        )

    @property
    def independently_checked(self) -> bool:
        return self.check.verdict is CheckerVerdict.REJECTED or (
            self.check.verdict is CheckerVerdict.ACCEPTED and bool(self.native_evidence_bytes)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_ref": self.candidate_ref,
            "candidate_hex": self.candidate_bytes.hex(),
            "check": self.check.to_dict(),
            "measurement": self.measurement.to_dict() if self.measurement else None,
            "edit_cost": canonical_rational(self.edit_cost) if self.edit_cost is not None else None,
            "observer_sound": self.observer_sound,
            "native_evidence_hex": self.native_evidence_bytes.hex(),
            "native_evidence_ref": sha256_ref(self.native_evidence_bytes)
            if self.native_evidence_bytes
            else None,
            "verified_repair": self.verified_repair,
            "reason": self.reason,
        }


def _admit_graph_result_status(result: "GraphTaskResultV1") -> None:
    flags = (result.search_complete, result.optimality_certified)
    if any(type(value) is not bool for value in flags):
        raise TypeError("search flags require exact booleans")
    known_status = result.search_status in {
        "NOT_REQUESTED",
        "PERMISSIONS_MISSING",
        "COMPLETE",
        "BUDGET_EXHAUSTED",
        "VERIFICATION_INCOMPLETE",
    }
    if result.mode not in {"diagnose", "repair"} or not known_status:
        raise ValueError("unknown graph execution status")
    if result.search_complete is not (result.search_status == "COMPLETE"):
        raise ValueError("search status and catalog completeness disagree")


def _evaluations_bounded(result: "GraphTaskResultV1") -> bool:
    if type(result.evaluations) is not tuple or len(result.evaluations) > 64:
        return False
    seen = {item.candidate_ref for item in result.evaluations}
    return len(seen) == len(result.evaluations)


def _selected_evaluation(
    result: "GraphTaskResultV1",
) -> "GraphCandidateEvaluationV1 | None":
    return next(
        (
            item
            for item in result.evaluations
            if item.candidate_ref == result.selected_candidate_ref
        ),
        None,
    )


def _selected_repair_missing(
    selected: "GraphCandidateEvaluationV1 | None",
) -> bool:
    return selected is None or not selected.verified_repair


def _admit_graph_result_choice(result: "GraphTaskResultV1") -> None:
    if not _evaluations_bounded(result):
        raise ValueError("evaluations require a distinct bounded frozen tuple")
    selected = _selected_evaluation(result)
    if result.selected_candidate_ref is not None and _selected_repair_missing(selected):
        raise ValueError("selected repair lacks independently checked evidence")
    if result.optimality_certified and (not result.search_complete or selected is None):
        raise ValueError("optimality requires a complete checked catalog and verified repair")


def _evidence_task_substituted(
    item: "GraphCandidateEvaluationV1",
    task_ref: str,
) -> bool:
    if not item.native_evidence_bytes:
        return False
    evidence_task = read_json(item.native_evidence_bytes)["request"]["task_ref"]
    return evidence_task != task_ref


def _admit_graph_result_evidence(result: "GraphTaskResultV1") -> None:
    for item in (result.original, *result.evaluations):
        if _evidence_task_substituted(item, result.task_ref):
            raise ValueError("native evidence substituted the original task")


def _admit_graph_result_selection(result: "GraphTaskResultV1") -> None:
    _admit_graph_result_choice(result)
    _admit_graph_result_evidence(result)


@dataclass(frozen=True, slots=True)
class GraphTaskResultV1:
    task_ref: str
    mode: str
    original: GraphCandidateEvaluationV1
    evaluations: tuple[GraphCandidateEvaluationV1, ...]
    selected_candidate_ref: str | None
    search_status: str
    search_complete: bool
    optimality_certified: bool
    model_turns: tuple[bytes, ...] = ()
    challenges: tuple[bytes, ...] = ()
    source_events: tuple[bytes, ...] = ()
    harvest_bytes: bytes = b""
    metrics_bytes: bytes = b"{}"

    def __post_init__(self) -> None:
        _admit_graph_result_status(self)
        _admit_graph_result_selection(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "core.adversary.graph-task-result.v1",
            "authority_effect": "None",
            "task_ref": self.task_ref,
            "mode": self.mode,
            "original_diagnosis": self.original.to_dict(),
            "candidate_evaluations": [item.to_dict() for item in self.evaluations],
            "selected_candidate_ref": self.selected_candidate_ref,
            "search_status": self.search_status,
            "search_complete": self.search_complete,
            "optimality_certified": self.optimality_certified,
            "optimality_scope": "declared finite catalog only",
            "model_turns": [read_json(raw) for raw in self.model_turns],
            "challenges": [read_json(raw) for raw in self.challenges],
            "source_events": [
                {"event_ref": sha256_ref(raw), "event_hex": raw.hex()} for raw in self.source_events
            ],
            "intelligence_harvest": read_json(self.harvest_bytes) if self.harvest_bytes else None,
            "metrics": read_json(self.metrics_bytes),
        }
