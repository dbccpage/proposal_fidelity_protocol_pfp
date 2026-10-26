"""Declared prompt encoding and exact finite projection evidence.

Origin: omega_engine_woland domain projection schema omega.woland.projection-measurement.v1.
Claim: an admitted carrier is degree one, and every declared edge has one source span.
Scope fence: this file does not claim that a source span proves the prompt's meaning.
The caller authors the encoding.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any, Protocol

from omega_engine_operations.domain.rop.result import Refusal, Result
from omega_engine_woland.domain.evidence import (
    ObstructionMeasurementV1,
    canonical_rational,
    is_sha256_ref,
    sha256_ref,
)
from omega_engine_woland.domain.network import Network


def _text(value: Any, name: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be nonempty text")


def _exact_vector(values: Any, name: str) -> tuple[Fraction, ...]:
    if type(values) not in (tuple, list) or not values:
        raise ValueError(f"{name} must be a nonempty exact vector")
    if any(type(value) is not Fraction for value in values):
        raise TypeError(f"{name} entries must be exact Fraction values")
    return tuple(values)


def _digest(payload: Any) -> str:
    return sha256_ref(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    )


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """A nonempty UTF-8 byte span explicitly assigned to one carrier edge."""

    edge_index: int
    start: int
    end: int
    interpretation: str

    def __post_init__(self) -> None:
        if any(type(v) is not int for v in (self.edge_index, self.start, self.end)):
            raise TypeError("span indices must be exact integers")
        if self.edge_index < 0 or self.start < 0 or self.end <= self.start:
            raise ValueError("span requires edge >= 0 and 0 <= start < end")
        _text(self.interpretation, "interpretation")

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_index": self.edge_index,
            "start": self.start,
            "end": self.end,
            "interpretation": self.interpretation,
        }


def _prompt_source(carrier: "HumanProblemCarrier") -> bytes:
    _text(carrier.prompt, "prompt")
    if type(carrier.max_prompt_bytes) is not int or not 0 < carrier.max_prompt_bytes <= 1048576:
        raise ValueError("max_prompt_bytes must be an exact integer in 1..1048576")
    source = carrier.prompt.encode("utf-8")
    if len(source) > carrier.max_prompt_bytes:
        raise ValueError("PROMPT_BOUND_EXCEEDED: prompt is never silently truncated")
    return source


def _nodes_are_distinct_text(nodes: Any) -> bool:
    exact = all(type(node) is str and node for node in nodes)
    return exact and len(set(nodes)) == len(nodes)


def _network_within_bounds(network: Network) -> None:
    if type(network) is not Network:
        raise TypeError("network must be an exact Network value")
    bounded = (
        2 <= len(network.nodes) <= 32
        and 1 <= len(network.edges) <= 64
        and len(network.faces) <= 64
    )
    if not bounded:
        raise ValueError("carrier exceeds the declared finite bounds")
    if not _nodes_are_distinct_text(network.nodes):
        raise ValueError("nodes must be distinct nonempty strings")
    if network.tetrahedra or network.four_simplices:
        raise ValueError(
            "CARRIER_DEGREE_UNLICENSED: adapter declares degree one and faces only"
        )


def _index_cells(
    network: Network,
) -> tuple[tuple[tuple[int, ...], ...], tuple[tuple[int, ...], ...]]:
    index = {node: position for position, node in enumerate(network.nodes)}
    try:
        edges = tuple(tuple(index[node] for node in edge) for edge in network.edges)
        faces = tuple(tuple(index[node] for node in face) for face in network.faces)
    except (KeyError, TypeError) as exc:
        raise ValueError("carrier cells name an absent or invalid vertex") from exc
    return edges, faces


def _edges_are_canonical(edges: tuple[tuple[int, ...], ...]) -> bool:
    ordered = edges == tuple(sorted(set(edges)))
    ascending = all(len(edge) == 2 and edge[0] < edge[1] for edge in edges)
    return ordered and ascending


def _faces_are_canonical(faces: tuple[tuple[int, ...], ...]) -> bool:
    ordered = faces == tuple(sorted(set(faces)))
    ascending = all(len(face) == 3 and face[0] < face[1] < face[2] for face in faces)
    return ordered and ascending


def _faces_cover_edges(
    edges: tuple[tuple[int, ...], ...],
    faces: tuple[tuple[int, ...], ...],
) -> bool:
    return all(
        (left, middle) in edges and (left, right) in edges and (middle, right) in edges
        for left, middle, right in faces
    )


def _admit_cell_order(network: Network) -> tuple[tuple[int, ...], ...]:
    edges, faces = _index_cells(network)
    if not _edges_are_canonical(edges):
        raise ValueError("edges must be unique, ascending and in canonical basis order")
    if not _faces_are_canonical(faces):
        raise ValueError("faces must be unique, ascending and in canonical basis order")
    if not _faces_cover_edges(edges, faces):
        raise ValueError("MISSING_FACE_BOUNDARY: every face edge must be explicitly declared")
    return edges


def _spans_are_typed(spans: Any) -> bool:
    return type(spans) in (tuple, list) and all(type(span) is SourceSpan for span in spans)


def _span_out_of_bounds(span: SourceSpan, previous: int, source: bytes, edge_count: int) -> bool:
    return span.start < previous or span.end > len(source) or span.edge_index >= edge_count


def _decode_span(source: bytes, span: SourceSpan) -> None:
    try:
        source[span.start : span.end].decode("utf-8")
        source[: span.start].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("source span splits a UTF-8 character") from exc


def _admit_source_spans(carrier: "HumanProblemCarrier", source: bytes, edge_count: int) -> None:
    if not _spans_are_typed(carrier.source_spans):
        raise TypeError("source_spans must contain exact SourceSpan values")
    spans = tuple(carrier.source_spans)
    if spans != tuple(sorted(spans, key=lambda span: span.start)):
        raise ValueError("source spans must be in source order")
    previous = 0
    for span in spans:
        if _span_out_of_bounds(span, previous, source, edge_count):
            raise ValueError(
                "source spans overlap, exceed prompt bounds or name an absent edge"
            )
        _decode_span(source, span)
        previous = span.end
    covered = {span.edge_index for span in spans}
    if covered != set(range(edge_count)):
        raise ValueError("every declared edge requires an explicit source span")
    object.__setattr__(carrier, "source_spans", spans)


@dataclass(frozen=True, slots=True)
class HumanProblemCarrier:
    prompt: str
    network: Network
    source_spans: tuple[SourceSpan, ...]
    max_prompt_bytes: int = 16384

    def __post_init__(self) -> None:
        source = _prompt_source(self)
        _network_within_bounds(self.network)
        edges = _admit_cell_order(self.network)
        _admit_source_spans(self, source, len(edges))

    @property
    def prompt_digest(self) -> str:
        return sha256_ref(self.prompt.encode("utf-8"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_digest": self.prompt_digest,
            "prompt_bytes": len(self.prompt.encode("utf-8")),
            "max_prompt_bytes": self.max_prompt_bytes,
            "nodes": list(self.network.nodes),
            "edges": [list(e) for e in self.network.edges],
            "faces": [list(f) for f in self.network.faces],
            "source_spans": [span.to_dict() for span in self.source_spans],
            "carrier_degree": 1,
        }

    @property
    def carrier_digest(self) -> str:
        return _digest(self.to_dict())


def _aligned_edge_operators(
    retraction: "ProjectionRetraction",
) -> tuple[Any, tuple[tuple[Fraction, ...], ...], tuple[tuple[Fraction, ...], ...]]:
    rates = tuple(_exact_vector(value, "rate") for value in retraction.rates)
    observers = tuple(_exact_vector(value, "observer") for value in retraction.observers)
    projectors = tuple(
        tuple(_exact_vector(row, "projector row") for row in projector)
        for projector in retraction.projectors
    )
    same_edges = rates and len(rates) == len(observers) and len(rates) == len(projectors)
    if not same_edges:
        raise ValueError(
            "projectors, rates and observers must cover the same nonempty edge set"
        )
    return projectors, rates, observers


def _edge_dimension_refused(
    projector: tuple[tuple[Fraction, ...], ...],
    rate: tuple[Fraction, ...],
    observer: tuple[Fraction, ...],
) -> bool:
    dim = len(rate)
    square = len(projector) == dim and all(len(row) == dim for row in projector)
    return dim > 16 or not square or len(observer) != dim


def _admit_edge_dimensions(
    projectors: Any,
    rates: tuple[tuple[Fraction, ...], ...],
    observers: tuple[tuple[Fraction, ...], ...],
) -> None:
    for projector, rate, observer in zip(projectors, rates, observers, strict=True):
        if _edge_dimension_refused(projector, rate, observer):
            raise ValueError(
                "each edge requires a square projector and matching vector dimensions <= 16"
            )


def _admit_disclosures(retraction: "ProjectionRetraction") -> None:
    for name in ("precision_boundaries", "continuum_approximations"):
        entries = getattr(retraction, name)
        if type(entries) not in (tuple, list):
            raise TypeError(f"{name} must be an ordered tuple of disclosures")
        for entry in entries:
            _text(entry, name)
        object.__setattr__(retraction, name, tuple(entries))


@dataclass(frozen=True, slots=True)
class ProjectionRetraction:
    """Declared tangent projector, rate and observer for each edge's exact space.

    P is admitted as a pure linear idempotent natively. The retained cochain is
    O(P L); the projection loss is (I-P)L. No NL retraction theorem is implied.
    """

    projection_id: str
    projectors: tuple[tuple[tuple[Fraction, ...], ...], ...]
    rates: tuple[tuple[Fraction, ...], ...]
    observers: tuple[tuple[Fraction, ...], ...]
    epsilon_proj: Fraction
    precision_boundaries: tuple[str, ...] = ()
    continuum_approximations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.projection_id, "projection_id")
        if type(self.epsilon_proj) is not Fraction or self.epsilon_proj < 0:
            raise TypeError("epsilon_proj must be a nonnegative exact Fraction")
        projectors, rates, observers = _aligned_edge_operators(self)
        _admit_edge_dimensions(projectors, rates, observers)
        _admit_disclosures(self)
        object.__setattr__(self, "projectors", projectors)
        object.__setattr__(self, "rates", rates)
        object.__setattr__(self, "observers", observers)

    def to_dict(self) -> dict[str, Any]:
        return {
            "projection_id": self.projection_id,
            "projectors": [
                [[canonical_rational(x) for x in row] for row in p] for p in self.projectors
            ],
            "rates": [[canonical_rational(x) for x in v] for v in self.rates],
            "observers": [[canonical_rational(x) for x in v] for v in self.observers],
            "epsilon_proj": canonical_rational(self.epsilon_proj),
            "precision_boundaries": list(self.precision_boundaries),
            "continuum_approximations": list(self.continuum_approximations),
        }

    @property
    def projection_digest(self) -> str:
        return _digest(self.to_dict())


def projection_request(
    carrier: HumanProblemCarrier, retraction: ProjectionRetraction
) -> dict[str, Any]:
    """Inert exact wire declaration, shared by request binding and adapters."""
    if type(carrier) is not HumanProblemCarrier or type(retraction) is not ProjectionRetraction:
        raise TypeError("exact projection declaration types required")
    return {"carrier": carrier.to_dict(), "retraction": retraction.to_dict()}


def projection_request_digest(
    carrier: HumanProblemCarrier, retraction: ProjectionRetraction
) -> str:
    """Native framed commitment to declared data, without evaluating meaning."""
    domain = b"omega.symbol-game.projection-evaluate-request.v1"
    raw = json.dumps(
        projection_request(carrier, retraction),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256_ref(len(domain).to_bytes(4, "big") + domain + len(raw).to_bytes(8, "big") + raw)


@dataclass(frozen=True, slots=True)
class NormalResidual:
    edge_index: int
    vector: tuple[Fraction, ...]
    l1_norm: Fraction

    def __post_init__(self) -> None:
        if type(self.edge_index) is not int or self.edge_index < 0:
            raise TypeError("edge_index must be a nonnegative exact int")
        object.__setattr__(self, "vector", _exact_vector(self.vector, "normal residual"))
        if type(self.l1_norm) is not Fraction or self.l1_norm < 0:
            raise TypeError("normal residual norm must be a nonnegative Fraction")

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_index": self.edge_index,
            "vector": [canonical_rational(x) for x in self.vector],
            "l1_norm": canonical_rational(self.l1_norm),
        }


@dataclass(frozen=True, slots=True)
class AdapterLossEntry:
    kind: str
    detail: str
    source_start: int | None = None
    source_end: int | None = None

    def __post_init__(self) -> None:
        if self.kind not in {
            "DROPPED_CONTEXT",
            "PRECISION_BOUNDARY",
            "CONTINUUM_APPROXIMATION",
            "NORMAL_RESIDUAL",
            "PROJECTION_OBSTRUCTION",
            "MEASUREMENT_UNAVAILABLE",
        }:
            raise ValueError("unknown adapter loss kind")
        if type(self.detail) is not str or not self.detail:
            raise ValueError("loss detail must be nonempty text, preserving source whitespace")
        if (self.source_start is None) != (self.source_end is None):
            raise ValueError("loss span requires both endpoints")
        if self.source_start is not None and (
            type(self.source_start) is not int
            or type(self.source_end) is not int
            or not 0 <= self.source_start < self.source_end
        ):
            raise ValueError("loss span requires exact 0 <= start < end")

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "detail": self.detail,
            "source_start": self.source_start,
            "source_end": self.source_end,
        }


@dataclass(frozen=True, slots=True)
class AdapterLossLedger:
    prompt_digest: str
    carrier_digest: str
    projection_digest: str
    entries: tuple[AdapterLossEntry, ...]

    def __post_init__(self) -> None:
        if not all(
            is_sha256_ref(v)
            for v in (self.prompt_digest, self.carrier_digest, self.projection_digest)
        ):
            raise ValueError("loss ledger must bind exact prompt/carrier/projection digests")
        if type(self.entries) not in (tuple, list) or any(
            type(entry) is not AdapterLossEntry for entry in self.entries
        ):
            raise TypeError("entries must contain exact AdapterLossEntry values")
        object.__setattr__(self, "entries", tuple(self.entries))

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": "omega.woland.adapter-loss-ledger.v1",
            "prompt_digest": self.prompt_digest,
            "carrier_digest": self.carrier_digest,
            "projection_digest": self.projection_digest,
            "entries": [entry.to_dict() for entry in self.entries],
            "entry_count": len(self.entries),
            "authority_effect": "None",
        }

    @property
    def digest(self) -> str:
        return _digest(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "digest": self.digest}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> AdapterLossLedger:
        expected = {
            "schema_version",
            "prompt_digest",
            "carrier_digest",
            "projection_digest",
            "entries",
            "entry_count",
            "authority_effect",
            "digest",
        }
        if (
            type(payload) is not dict
            or set(payload) != expected
            or payload["schema_version"] != "omega.woland.adapter-loss-ledger.v1"
            or payload["authority_effect"] != "None"
        ):
            raise ValueError("LossLedgerTampered: invalid ledger envelope")
        ledger = cls(
            payload["prompt_digest"],
            payload["carrier_digest"],
            payload["projection_digest"],
            tuple(AdapterLossEntry(**entry) for entry in payload["entries"]),
        )
        if (
            type(payload["entry_count"]) is not int
            or payload["entry_count"] != len(ledger.entries)
            or payload["digest"] != ledger.digest
        ):
            raise ValueError("LossLedgerTampered: count or digest mismatch")
        return ledger


@dataclass(frozen=True, slots=True)
class NativeProjectionEvidenceV1:
    measurement: ObstructionMeasurementV1
    normal_residuals: tuple[NormalResidual, ...]
    projected_cochain: tuple[Fraction, ...]
    input_digest: str
    native_outcomes_json: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            type(self.measurement) is not ObstructionMeasurementV1
            or not self.measurement.is_measured
        ):
            raise TypeError("native projection requires exact measured functional evidence")
        if not is_sha256_ref(self.input_digest):
            raise ValueError("input_digest must be sha256 bound")
        if any(type(r) is not NormalResidual for r in self.normal_residuals):
            raise TypeError("normal_residuals must be NormalResidual values")
        object.__setattr__(self, "normal_residuals", tuple(self.normal_residuals))
        object.__setattr__(
            self, "projected_cochain", _exact_vector(self.projected_cochain, "projected cochain")
        )
        object.__setattr__(self, "native_outcomes_json", tuple(self.native_outcomes_json))


class ProjectionMeasurementPort(Protocol):
    def measure(
        self, carrier: HumanProblemCarrier, retraction: ProjectionRetraction
    ) -> Result[NativeProjectionEvidenceV1, Refusal]: ...


class ProjectionStatus(str, Enum):
    MEASURED = "MEASURED"
    REFUSED = "REFUSED"
    NOT_MEASURED = "NOT_MEASURED"


def _admit_projection_types(receipt: "ProjectionMeasurementV1") -> None:
    exact = (
        type(receipt.status) is ProjectionStatus
        and type(receipt.measurement) is ObstructionMeasurementV1
        and type(receipt.loss_ledger) is AdapterLossLedger
    )
    if not exact:
        raise TypeError(
            "projection receipt requires exact status, measurement and loss ledger types"
        )


def _admit_projection_authority(receipt: "ProjectionMeasurementV1") -> None:
    degree_one = type(receipt.carrier_degree) is int and receipt.carrier_degree == 1
    if receipt.authority_effect != "None" or not degree_one:
        raise ValueError("projection receipt grants no authority or higher degree")


def _not_measured_carries_values(receipt: "ProjectionMeasurementV1") -> bool:
    return bool(
        receipt.measurement.is_measured
        or receipt.normal_residuals
        or receipt.projected_cochain
        or receipt.input_digest is not None
    )


def _admit_projection_status(receipt: "ProjectionMeasurementV1") -> None:
    if receipt.status is ProjectionStatus.NOT_MEASURED:
        if _not_measured_carries_values(receipt):
            raise ValueError("NOT_MEASURED cannot carry native measured values")
    elif not receipt.measurement.is_measured or not is_sha256_ref(receipt.input_digest):
        raise ValueError("MEASURED/REFUSED requires input-bound native measurement")
    measured = receipt.status is ProjectionStatus.MEASURED
    if measured != (receipt.refusal_code is None):
        raise ValueError("nonadmissible projection receipt requires a refusal code")


def _projection_values_exact(receipt: "ProjectionMeasurementV1") -> bool:
    residuals = all(type(item) is NormalResidual for item in receipt.normal_residuals)
    cochain = all(type(item) is Fraction for item in receipt.projected_cochain)
    return residuals and cochain


def _admit_projection_values(receipt: "ProjectionMeasurementV1") -> None:
    if not _projection_values_exact(receipt):
        raise TypeError("projection receipt values must be exact")
    object.__setattr__(receipt, "normal_residuals", tuple(receipt.normal_residuals))
    object.__setattr__(receipt, "projected_cochain", tuple(receipt.projected_cochain))
    object.__setattr__(receipt, "native_outcomes_json", tuple(receipt.native_outcomes_json))


@dataclass(frozen=True, slots=True)
class ProjectionMeasurementV1:
    status: ProjectionStatus
    measurement: ObstructionMeasurementV1
    normal_residuals: tuple[NormalResidual, ...]
    projected_cochain: tuple[Fraction, ...]
    loss_ledger: AdapterLossLedger
    input_digest: str | None = None
    refusal_code: str | None = None
    native_outcomes_json: tuple[str, ...] = ()
    carrier_degree: int = 1
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _admit_projection_types(self)
        _admit_projection_authority(self)
        _admit_projection_status(self)
        _admit_projection_values(self)

    @property
    def is_admissible(self) -> bool:
        return self.status is ProjectionStatus.MEASURED

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "omega.woland.projection-measurement.v1",
            "status": self.status.value,
            "measurement": self.measurement.to_dict(),
            "normal_residuals": [r.to_dict() for r in self.normal_residuals],
            "projected_cochain": [canonical_rational(x) for x in self.projected_cochain],
            "loss_ledger": self.loss_ledger.to_dict(),
            "input_digest": self.input_digest,
            "refusal_code": self.refusal_code,
            "native_outcomes": [json.loads(outcome) for outcome in self.native_outcomes_json],
            "carrier_degree": self.carrier_degree,
            "authority_effect": self.authority_effect,
        }
