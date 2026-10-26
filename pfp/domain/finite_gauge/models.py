"""Immutable finite-gauge value objects and typed refusals.

These types contain no host I/O and do not depend on the Paper 002 adapter.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class GaugeRefusalCode(str, Enum):
    """Fail-closed reasons emitted by the finite-gauge application."""

    CHECKER_UNAVAILABLE = "CHECKER_UNAVAILABLE"
    CHECK_FAILED = "CHECK_FAILED"
    REPLAY_FAILED = "REPLAY_FAILED"
    SEARCH_DIVERGENCE = "SEARCH_DIVERGENCE"
    RUN_ALREADY_STARTED = "RUN_ALREADY_STARTED"
    RUN_CAPACITY_REACHED = "RUN_CAPACITY_REACHED"
    EVENT_SINK_FAILED = "EVENT_SINK_FAILED"
    RUNTIME_DEPENDENCY_FAILED = "RUNTIME_DEPENDENCY_FAILED"


@dataclass(frozen=True, slots=True)
class GaugeRefusal:
    """Typed failure track for a bounded finite-gauge run."""

    code: GaugeRefusalCode
    message: str
    authority_effect: str = "None"


@dataclass(frozen=True, slots=True)
class SignedEdge:
    source: str
    target: str
    odd: int

    def __post_init__(self) -> None:
        if not self.source or not self.target or self.odd not in (0, 1):
            raise ValueError("signed edge needs named endpoints and parity 0 or 1")


@dataclass(frozen=True, slots=True)
class GraphSpec:
    title: str
    description: str
    vertices: tuple[str, ...]
    edges: tuple[SignedEdge, ...]


@dataclass(frozen=True, slots=True)
class CheckerIdentity:
    checker_version: str
    checker_sha256: str
    sign_graph_sha256: str


@dataclass(frozen=True, slots=True)
class CandidateCheck:
    index: int
    bits: tuple[int, ...]
    valid: bool


@dataclass(frozen=True, slots=True)
class GaugeFrontier:
    next_index: int
    stop_index: int


@dataclass(frozen=True, slots=True)
class Witness:
    kind: str
    vertices: tuple[str, ...] = ()
    bits: tuple[int, ...] = ()
    steps: tuple[tuple[str, str, int], ...] = ()

    def to_wire(self) -> dict[str, Any]:
        if self.kind == "gauge":
            return {"type": self.kind, "vertices": self.vertices, "bits": self.bits}
        return {"type": self.kind, "steps": self.steps}


@dataclass(frozen=True, slots=True)
class SearchReceipt:
    status: str
    receipt_sha256: str
    presentation_digest: str
    graph_digest: str
    node_budget: int
    checks: tuple[CandidateCheck, ...]
    frontier: GaugeFrontier
    witness: Witness | None
    complete_oracle_used: bool


_FIXTURES: dict[str, GraphSpec] = {
    "gauge_even_triangle": GraphSpec(
        title="Even sign triangle",
        description="A finite signed rewrite graph with a diagonal Z2 gauge witness.",
        vertices=("v0", "v1", "v2"),
        edges=(SignedEdge("v0", "v1", 1), SignedEdge("v1", "v2", 1), SignedEdge("v0", "v2", 0)),
    ),
    "gauge_odd_triangle": GraphSpec(
        title="Odd sign triangle",
        description="An odd parity cycle obstructs every vertex gauge in this grammar.",
        vertices=("v0", "v1", "v2"),
        edges=(SignedEdge("v0", "v1", 1), SignedEdge("v1", "v2", 1), SignedEdge("v0", "v2", 1)),
    ),
    "gauge_chain": GraphSpec(
        title="Four vertex chain",
        description="A larger, exact finite control with both odd and even edge constraints.",
        vertices=("v0", "v1", "v2", "v3"),
        edges=(SignedEdge("v0", "v1", 1), SignedEdge("v1", "v2", 0), SignedEdge("v2", "v3", 1)),
    ),
}


def fixture_catalog() -> dict[str, GraphSpec]:
    """Return a detached catalog mapping while retaining immutable values."""
    return dict(_FIXTURES)


def _validate_custom_graph(config: RunConfig) -> None:
    if not isinstance(config.vertices, tuple) or not 1 <= len(config.vertices) <= 8:
        raise ValueError("custom graph needs 1 to 8 vertices")
    if any(not isinstance(vertex, str) or not vertex or len(vertex) > 64 for vertex in config.vertices):
        raise ValueError("vertex names must be nonempty strings of at most 64 characters")
    if len(set(config.vertices)) != len(config.vertices):
        raise ValueError("custom graph has duplicate vertex names")
    if not isinstance(config.edges, tuple) or len(config.edges) > 32:
        raise ValueError("custom graph needs at most 32 edges")
    for edge in config.edges:
        if (
            not isinstance(edge, tuple)
            or len(edge) != 3
            or edge[0] not in config.vertices
            or edge[1] not in config.vertices
            or type(edge[2]) is not int
            or edge[2] not in (0, 1)
        ):
            raise ValueError("each edge needs declared endpoints and exact parity 0 or 1")


@dataclass(frozen=True, slots=True)
class RunConfig:
    """Validated request value object for a finite gauge run."""

    fixture_id: str
    node_budget: int = 8
    pace_ms: int = 180
    vertices: tuple[str, ...] | None = None
    edges: tuple[tuple[str, str, int], ...] | None = None
    objective: str = ""

    def __post_init__(self) -> None:
        if self.fixture_id not in _FIXTURES and self.fixture_id != "custom_graph":
            raise ValueError("unknown finite graph fixture")
        if type(self.node_budget) is not int or not 1 <= self.node_budget <= 256:
            raise ValueError("node_budget must be an integer from 1 to 256")
        if type(self.pace_ms) is not int or not 0 <= self.pace_ms <= 2000:
            raise ValueError("pace_ms must be an integer from 0 to 2000")
        if not isinstance(self.objective, str) or len(self.objective) > 500:
            raise ValueError("objective must be text of at most 500 characters")
        if self.fixture_id == "custom_graph":
            _validate_custom_graph(self)
        elif self.vertices is not None or self.edges is not None:
            raise ValueError("fixture run cannot override its pinned graph")

    @classmethod
    def from_packet(cls, packet: dict[str, Any]) -> RunConfig:
        if not isinstance(packet, dict):
            raise ValueError("input packet must be a mapping")
        allowed = {"schema", "fixture_id", "graph", "node_budget", "pace_ms", "objective"}
        unknown = set(packet) - allowed
        if unknown:
            raise ValueError("unknown input fields: " + ", ".join(sorted(unknown)))
        if packet.get("schema") != "symbol_game.finite_gauge_input.v1":
            raise ValueError("input packet schema must be symbol_game.finite_gauge_input.v1")
        graph = packet.get("graph")
        if graph is None:
            return cls._from_fixture_packet(packet)
        return cls._from_graph_packet(packet, graph)

    @classmethod
    def _from_fixture_packet(cls, packet: dict[str, Any]) -> RunConfig:
        return cls(
            fixture_id=packet.get("fixture_id", "gauge_even_triangle"),
            node_budget=packet.get("node_budget", 8),
            pace_ms=packet.get("pace_ms", 180),
            objective=packet.get("objective", ""),
        )

    @classmethod
    def _from_graph_packet(cls, packet: dict[str, Any], graph: Any) -> RunConfig:
        if packet.get("fixture_id") not in (None, "custom_graph"):
            raise ValueError("custom graph input cannot also select a fixture")
        if not isinstance(graph, dict) or set(graph) != {"vertices", "edges"}:
            raise ValueError("graph must contain exactly vertices and edges")
        if not isinstance(graph["vertices"], list) or not isinstance(graph["edges"], list):
            raise ValueError("graph vertices and edges must be lists")
        edges = tuple(_parse_edge(edge) for edge in graph["edges"])
        return cls(
            fixture_id="custom_graph",
            node_budget=packet.get("node_budget", 8),
            pace_ms=packet.get("pace_ms", 180),
            vertices=tuple(graph["vertices"]),
            edges=edges,
            objective=packet.get("objective", ""),
        )

    def to_packet(self) -> dict[str, Any]:
        packet: dict[str, Any] = {
            "schema": "symbol_game.finite_gauge_input.v1",
            "node_budget": self.node_budget,
            "pace_ms": self.pace_ms,
        }
        if self.objective:
            packet["objective"] = self.objective
        if self.fixture_id == "custom_graph":
            packet["graph"] = {"vertices": self.vertices, "edges": self.edges}
        else:
            packet["fixture_id"] = self.fixture_id
        return packet

    def graph_spec(self) -> GraphSpec:
        if self.fixture_id != "custom_graph":
            return _FIXTURES[self.fixture_id]
        if self.vertices is None or self.edges is None:
            raise ValueError("validated custom graph lost its vertices or edges")
        return GraphSpec(
            title="Custom signed graph",
            description=self.objective,
            vertices=self.vertices,
            edges=tuple(SignedEdge(*edge) for edge in self.edges),
        )


def _parse_edge(edge: Any) -> tuple[str, str, int]:
    if not isinstance(edge, list) or len(edge) != 3:
        raise ValueError("graph edges must be [source, target, parity] lists")
    return edge[0], edge[1], edge[2]
