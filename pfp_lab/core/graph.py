"""Finite constraint graphs: the declared carrier of a PFP scenario.

AuthorityEffect: None.
Contract: urn:pfp-lab:core:graph:v1
Provenance: ported from ``Edge`` and ``ConstraintGraph`` in
``papers/005_pfp_practitioners_field_manual/code/l1_symbol_game_governor.py``;
``pfp_lab/core/PROVENANCE.md`` records its digest and every change.

Every graph is validated on construction: names are admitted, self-loops and
duplicate vertices or directed edges are refused, and the size stays within the
declared bounds that keep the obstruction search finite.
"""

from __future__ import annotations

from dataclasses import dataclass

from pfp_lab.core.admission import AdmissionError, admit_int, admit_name

MAX_VERTICES = 12
MAX_EDGES = 16
MAX_WEIGHT = 1000

EdgeKey = tuple[str, str]


@dataclass(frozen=True, slots=True)
class Edge:
    """Directed edge ``source -> target`` with a positive integer weight."""

    source: str
    target: str
    weight: int

    def __post_init__(self) -> None:
        admit_name(self.source, field="edge source")
        admit_name(self.target, field="edge target")
        admit_int(self.weight, minimum=1, maximum=MAX_WEIGHT, field="edge weight")
        if self.source == self.target:
            raise AdmissionError(f"self-loop {self.source} -> {self.target} violates irreflexivity")

    @property
    def key(self) -> EdgeKey:
        return (self.source, self.target)


@dataclass(frozen=True, slots=True)
class ConstraintGraph:
    """Declared vertices and directed edges; immutable once admitted."""

    vertices: tuple[str, ...]
    edges: tuple[Edge, ...]

    def __post_init__(self) -> None:
        _check_vertices(self.vertices)
        _check_edges(self.vertices, self.edges)

    def has_vertex(self, name: str) -> bool:
        return name in self.vertices

    def edge(self, source: str, target: str) -> Edge | None:
        """The declared edge ``source -> target``, if any."""
        for candidate in self.edges:
            if candidate.key == (source, target):
                return candidate
        return None

    def components(self) -> tuple[tuple[str, ...], ...]:
        """Connected components of the underlying undirected graph, each sorted."""
        neighbours: dict[str, set[str]] = {name: set() for name in self.vertices}
        for item in self.edges:
            neighbours[item.source].add(item.target)
            neighbours[item.target].add(item.source)
        seen: set[str] = set()
        found: list[tuple[str, ...]] = []
        for start in self.vertices:
            if start not in seen:
                found.append(_reach(start, neighbours, seen))
        return tuple(found)


def _reach(start: str, neighbours: dict[str, set[str]], seen: set[str]) -> tuple[str, ...]:
    """All vertices reachable from ``start``; marks them in ``seen``."""
    seen.add(start)
    stack = [start]
    members: list[str] = []
    while stack:
        current = stack.pop()
        members.append(current)
        fresh = neighbours[current] - seen
        seen.update(fresh)
        stack.extend(fresh)
    return tuple(sorted(members))


def _check_vertices(vertices: tuple[str, ...]) -> None:
    if type(vertices) is not tuple:
        raise AdmissionError("vertices must be a tuple")
    if not 1 <= len(vertices) <= MAX_VERTICES:
        raise AdmissionError(f"a graph needs 1 to {MAX_VERTICES} vertices, got {len(vertices)}")
    for name in vertices:
        admit_name(name, field="vertex")
    if len(set(vertices)) != len(vertices):
        raise AdmissionError("duplicate vertex in declared carrier")


def _check_edges(vertices: tuple[str, ...], edges: tuple[Edge, ...]) -> None:
    if type(edges) is not tuple:
        raise AdmissionError("edges must be a tuple")
    if len(edges) > MAX_EDGES:
        raise AdmissionError(f"a graph may declare at most {MAX_EDGES} edges, got {len(edges)}")
    declared = set(vertices)
    keys: set[EdgeKey] = set()
    for item in edges:
        if type(item) is not Edge:
            raise AdmissionError("edges must be Edge values")
        if item.source not in declared or item.target not in declared:
            raise AdmissionError(f"edge {item.source} -> {item.target} leaves the declared carrier")
        if item.key in keys:
            raise AdmissionError(f"duplicate directed edge {item.source} -> {item.target}")
        keys.add(item.key)


__all__ = ["MAX_EDGES", "MAX_VERTICES", "MAX_WEIGHT", "ConstraintGraph", "Edge", "EdgeKey"]
