"""Topological Carrier, Cell Bounds, and Homology Value Objects.

AuthorityEffect: None.
Governing standard: RULE_VO_EXACT_TYPE_EQUALITY_001.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple

from .base import ValueObject
from .taxonomy import VerificationStatusVO


def _require_int(name: str, value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be a strict int, got {type(value).__name__}")
    return value


def _require_non_negative_int(name: str, value: Any) -> int:
    v = _require_int(name, value)
    if v < 0:
        raise ValueError(f"{name} must be non-negative, got {v}")
    return v


def _require_non_empty_str(name: str, value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be str, got {type(value).__name__}")
    if not value.strip():
        raise ValueError(f"{name} cannot be empty or whitespace-only")
    return value



@dataclass(frozen=True)
class StaticCellBoundsVO(ValueObject):
    """Immutable bounds on carrier cell capacities."""

    max_vertices: int
    max_edges: int
    max_faces: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "max_vertices", _require_non_negative_int("max_vertices", self.max_vertices))
        object.__setattr__(self, "max_edges", _require_non_negative_int("max_edges", self.max_edges))
        object.__setattr__(self, "max_faces", _require_non_negative_int("max_faces", self.max_faces))


@dataclass(frozen=True)
class CarrierEdgeVO(ValueObject):
    """Directed, irreflexive 1-cell in a simplicial/cell complex."""

    id: str
    source: int
    target: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _require_non_empty_str("CarrierEdgeVO.id", self.id))
        object.__setattr__(self, "source", _require_int("CarrierEdgeVO.source", self.source))
        object.__setattr__(self, "target", _require_int("CarrierEdgeVO.target", self.target))
        if self.source == self.target:
            raise ValueError(f"irreflexive carrier: edge endpoints must differ (source={self.source}, target={self.target})")


@dataclass(frozen=True)
class CarrierFaceVO(ValueObject):
    """Oriented 2-cell bounded by declared 1-cells."""

    id: str
    boundary_edges: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _require_non_empty_str("CarrierFaceVO.id", self.id))
        if not isinstance(self.boundary_edges, tuple):
            if isinstance(self.boundary_edges, list):
                object.__setattr__(self, "boundary_edges", tuple(self.boundary_edges))
            else:
                raise TypeError(f"boundary_edges must be tuple or list, got {type(self.boundary_edges).__name__}")
        for e in self.boundary_edges:
            _require_non_empty_str("boundary_edge item", e)


@dataclass(frozen=True)
class CarrierVO(ValueObject):
    """Carrier complex K0 = (V, E, B) with static bounds and incident references."""

    name: str
    vertices: Tuple[int, ...]
    edges: Tuple[CarrierEdgeVO, ...]
    faces: Tuple[CarrierFaceVO, ...]
    static_cell_bounds: StaticCellBoundsVO

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _require_non_empty_str("CarrierVO.name", self.name))

        if isinstance(self.vertices, list):
            object.__setattr__(self, "vertices", tuple(self.vertices))
        elif not isinstance(self.vertices, tuple):
            raise TypeError("vertices must be tuple or list")
        for v in self.vertices:
            _require_int("vertex", v)

        if isinstance(self.edges, list):
            object.__setattr__(self, "edges", tuple(self.edges))
        elif not isinstance(self.edges, tuple):
            raise TypeError("edges must be tuple or list")
        for e in self.edges:
            if not isinstance(e, CarrierEdgeVO):
                raise TypeError(f"edge must be CarrierEdgeVO, got {type(e).__name__}")

        if isinstance(self.faces, list):
            object.__setattr__(self, "faces", tuple(self.faces))
        elif not isinstance(self.faces, tuple):
            raise TypeError("faces must be tuple or list")
        for f in self.faces:
            if not isinstance(f, CarrierFaceVO):
                raise TypeError(f"face must be CarrierFaceVO, got {type(f).__name__}")

        if not isinstance(self.static_cell_bounds, StaticCellBoundsVO):
            raise TypeError(f"static_cell_bounds must be StaticCellBoundsVO, got {type(self.static_cell_bounds).__name__}")

        # Bounds checks
        b = self.static_cell_bounds
        if len(self.vertices) > b.max_vertices:
            raise ValueError(f"vertex count ({len(self.vertices)}) exceeds max_vertices ({b.max_vertices})")
        if len(self.edges) > b.max_edges:
            raise ValueError(f"edge count ({len(self.edges)}) exceeds max_edges ({b.max_edges})")
        if len(self.faces) > b.max_faces:
            raise ValueError(f"face count ({len(self.faces)}) exceeds max_faces ({b.max_faces})")

        # Duplicate edge checks
        edge_ids = [e.id for e in self.edges]
        if len(set(edge_ids)) != len(edge_ids):
            raise ValueError("duplicate edge id in carrier")

        vertex_set = set(self.vertices)
        for e in self.edges:
            if e.source not in vertex_set or e.target not in vertex_set:
                raise ValueError(f"edge {e.id} endpoint ({e.source}->{e.target}) is not a declared vertex")

        for f in self.faces:
            for ref in f.boundary_edges:
                stripped = ref[1:] if ref.startswith("-") else ref
                if stripped not in edge_ids:
                    raise ValueError(f"face {f.id} boundary references undeclared edge {ref}")


@dataclass(frozen=True)
class BoundaryMatricesVO(ValueObject):
    """Integer boundary operators d1 (|V| x |E|) and d2 (|E| x |F|)."""

    d1: Tuple[Tuple[int, ...], ...]
    d2: Tuple[Tuple[int, ...], ...]

    def __post_init__(self) -> None:
        def _normalize_matrix(mat: Any, name: str) -> Tuple[Tuple[int, ...], ...]:
            if isinstance(mat, list):
                mat = tuple(tuple(r) if isinstance(r, list) else r for r in mat)
            if not isinstance(mat, tuple):
                raise TypeError(f"{name} must be tuple of tuples")
            for r in mat:
                if not isinstance(r, tuple):
                    raise TypeError(f"{name} row must be tuple")
                for c in r:
                    _require_int(f"{name} entry", c)
            return mat

        object.__setattr__(self, "d1", _normalize_matrix(self.d1, "d1"))
        object.__setattr__(self, "d2", _normalize_matrix(self.d2, "d2"))


@dataclass(frozen=True)
class ActiveObstructionVO(ValueObject):
    """Active non-exact 1-cycle obstruction awaiting chain-complex balance."""

    cycle_z: Tuple[int, ...]
    cycle_edges: Tuple[str, ...]
    d1_z: Tuple[int, ...]
    homology_status: VerificationStatusVO

    def __post_init__(self) -> None:
        if isinstance(self.cycle_z, list):
            object.__setattr__(self, "cycle_z", tuple(self.cycle_z))
        for z in self.cycle_z:
            _require_int("cycle_z entry", z)

        if isinstance(self.cycle_edges, list):
            object.__setattr__(self, "cycle_edges", tuple(self.cycle_edges))
        for e in self.cycle_edges:
            _require_non_empty_str("cycle_edge", e)

        if isinstance(self.d1_z, list):
            object.__setattr__(self, "d1_z", tuple(self.d1_z))
        for dz in self.d1_z:
            _require_int("d1_z entry", dz)

        if isinstance(self.homology_status, str):
            object.__setattr__(self, "homology_status", VerificationStatusVO(self.homology_status))
        elif not isinstance(self.homology_status, VerificationStatusVO):
            raise TypeError(f"homology_status must be VerificationStatusVO, got {type(self.homology_status).__name__}")



@dataclass(frozen=True)
class ClaimHygieneVO(ValueObject):
    """Mandatory 3-clause epistemic discipline record."""

    what_it_supports: str
    what_it_does_not_support: str
    next_test_needed: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "what_it_supports", _require_non_empty_str("what_it_supports", self.what_it_supports))
        object.__setattr__(self, "what_it_does_not_support", _require_non_empty_str("what_it_does_not_support", self.what_it_does_not_support))
        object.__setattr__(self, "next_test_needed", _require_non_empty_str("next_test_needed", self.next_test_needed))
