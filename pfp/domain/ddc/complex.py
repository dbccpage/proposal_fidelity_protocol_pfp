"""Simplicial Complex carrier for Discrete Deformation Calculus (DDC).

Represents a finite 2-truncated cell complex K = (V, E, F) over exact rational coefficients.
Enforces diagonal excision (no self-loops), strict orientation conventions, and provides
combinatorial incidence matrices for boundary and coboundary operators.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
)


@dataclass(frozen=True)
class Edge:
    """Directed 1-simplex (u, v) with exact positive rational weight omega_e >= 1."""

    u: str
    v: str
    weight: Fraction = Fraction(1)

    def __post_init__(self) -> None:
        if self.u == self.v:
            raise ValueError(
                f"Self-loop ({self.u} -> {self.v}) violates irreflexivity and diagonal excision."
            )
        w = Fraction(self.weight)
        if w <= 0:
            raise ValueError(f"Edge weight must be strictly positive, got {self.weight}.")
        object.__setattr__(self, "weight", w)

    @property
    def key(self) -> Tuple[str, str]:
        return (self.u, self.v)

    @property
    def reversed_key(self) -> Tuple[str, str]:
        return (self.v, self.u)


@dataclass(frozen=True)
class Face:
    """Oriented 2-simplex (u, v, w) with boundary partial_2 [u,v,w] = [v,w] - [u,w] + [u,v]."""

    u: str
    v: str
    w: str

    def __post_init__(self) -> None:
        nodes = (self.u, self.v, self.w)
        if len(set(nodes)) != 3:
            raise ValueError(
                f"Degenerate 2-simplex with non-distinct vertices: {nodes}. "
                "All 3 vertices of a face must be distinct."
            )

    @property
    def key(self) -> Tuple[str, str, str]:
        return (self.u, self.v, self.w)

    @property
    def boundary_edges(self) -> Tuple[Tuple[Tuple[str, str], int], ...]:
        """Returns signed boundary 1-simplices: ((v, w), +1), ((u, w), -1), ((u, v), +1)."""
        return (
            ((self.v, self.w), 1),
            ((self.u, self.w), -1),
            ((self.u, self.v), 1),
        )


@dataclass(frozen=True)
class SimplicialComplex:
    """Finite 2-truncated simplicial carrier K = (V, E, F).

    Carrier vertices V, directed edges E, and oriented 2-cells F.
    All edge weights are exact rational fractions.
    """

    vertices: Tuple[str, ...]
    edges: Tuple[Edge, ...]
    faces: Tuple[Face, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        # Check uniqueness of vertices
        if len(set(self.vertices)) != len(self.vertices):
            raise ValueError("Vertices in simplicial complex must be unique.")

        v_set = set(self.vertices)
        seen_edges: Set[Tuple[str, str]] = set()
        for e in self.edges:
            if e.u not in v_set:
                raise ValueError(f"Edge source '{e.u}' not in declared vertex set.")
            if e.v not in v_set:
                raise ValueError(f"Edge target '{e.v}' not in declared vertex set.")
            if e.key in seen_edges:
                raise ValueError(f"Duplicate edge {e.key} declared in complex.")
            seen_edges.add(e.key)

        seen_faces: Set[Tuple[str, str, str]] = set()
        for f in self.faces:
            for node in (f.u, f.v, f.w):
                if node not in v_set:
                    raise ValueError(f"Face vertex '{node}' not in declared vertex set.")
            for (u, v), _ in f.boundary_edges:
                if (u, v) not in seen_edges and (v, u) not in seen_edges:
                    raise ValueError(
                        f"Face {f.key} boundary edge {(u, v)} is absent in both orientations."
                    )
            if f.key in seen_faces:
                raise ValueError(f"Duplicate face {f.key} declared in complex.")
            seen_faces.add(f.key)

    @property
    def num_vertices(self) -> int:
        return len(self.vertices)

    @property
    def num_edges(self) -> int:
        return len(self.edges)

    @property
    def num_faces(self) -> int:
        return len(self.faces)

    @property
    def edge_keys(self) -> List[Tuple[str, str]]:
        return [e.key for e in self.edges]

    @property
    def face_keys(self) -> List[Tuple[str, str, str]]:
        return [f.key for f in self.faces]

    def edge_weight(self, u: str, v: str) -> Fraction:
        """Return the weight for edge (u, v), or default Fraction(1)."""
        for e in self.edges:
            if e.u == u and e.v == v:
                return e.weight
        return Fraction(1)

    def weights_dict(self) -> Dict[Tuple[str, str], Fraction]:
        """Return dictionary mapping edge keys to exact rational weights."""
        return {e.key: e.weight for e in self.edges}

    def has_edge(self, u: str, v: str) -> bool:
        return any(e.u == u and e.v == v for e in self.edges)

    def connected_components(self) -> List[List[str]]:
        """Computes connected components of the underlying 1-skeleton."""
        adj: Dict[str, Set[str]] = {v: set() for v in self.vertices}
        for e in self.edges:
            adj[e.u].add(e.v)
            adj[e.v].add(e.u)

        visited: Set[str] = set()
        components: List[List[str]] = []
        for v in self.vertices:
            if v not in visited:
                comp: List[str] = []
                stack = [v]
                visited.add(v)
                while stack:
                    curr = stack.pop()
                    comp.append(curr)
                    for nxt in adj[curr]:
                        if nxt not in visited:
                            visited.add(nxt)
                            stack.append(nxt)
                components.append(sorted(comp))
        return components

    def build_incidence_d0(self) -> Dict[Tuple[str, str], Dict[str, int]]:
        """Computes d^0 coboundary incidence: (d^0 f)(u, v) = f(v) - f(u).

        Returns mapping: edge (u, v) -> {v: +1, u: -1}.
        Notice d^0 = partial_1^T where partial_1(u -> v) = v - u.
        """
        return {e.key: {e.v: 1, e.u: -1} for e in self.edges}

    def build_incidence_d1(self) -> Dict[Tuple[str, str, str], Dict[Tuple[str, str], int]]:
        """Computes d^1 coboundary incidence:

        (d^1 h)(u, v, w) = h(v, w) - h(u, w) + h(u, v).
        Returns mapping: face (u, v, w) -> {(v, w): +1, (u, w): -1, (u, v): +1}.
        """
        return {
            f.key: {(f.v, f.w): 1, (f.u, f.w): -1, (f.u, f.v): 1}
            for f in self.faces
        }

    # Factory methods for canonical test graphs
    @classmethod
    def cycle_graph(
        cls,
        n: int,
        directed: bool = True,
        weights: Optional[Mapping[Tuple[str, str], Any]] = None,
        with_faces: bool = False,
    ) -> SimplicialComplex:
        """Construct an n-vertex directed cycle graph: 0 -> 1 -> ... -> n-1 -> 0."""
        if n < 3:
            raise ValueError(f"Cycle graph requires at least 3 vertices, got {n}.")
        vertices = tuple(f"v{i}" for i in range(n))
        edges_list: List[Edge] = []
        for i in range(n):
            u = vertices[i]
            v = vertices[(i + 1) % n]
            w = Fraction(weights.get((u, v), 1)) if weights else Fraction(1)
            edges_list.append(Edge(u=u, v=v, weight=w))

        faces_list: List[Face] = []
        if with_faces and n == 3:
            # Triangulate 3-cycle
            faces_list.append(Face(u=vertices[0], v=vertices[1], w=vertices[2]))

        return cls(vertices=vertices, edges=tuple(edges_list), faces=tuple(faces_list))

    @classmethod
    def complete_graph(
        cls,
        n: int,
        with_faces: bool = True,
        weights: Optional[Mapping[Tuple[str, str], Any]] = None,
    ) -> SimplicialComplex:
        """Construct an n-vertex complete tournament/acyclic graph with all directed edges i -> j for i < j."""
        if n < 2:
            raise ValueError(f"Complete graph requires at least 2 vertices, got {n}.")
        vertices = tuple(f"v{i}" for i in range(n))
        edges_list: List[Edge] = []
        for i in range(n):
            for j in range(i + 1, n):
                u = vertices[i]
                v = vertices[j]
                w = Fraction(weights.get((u, v), 1)) if weights else Fraction(1)
                edges_list.append(Edge(u=u, v=v, weight=w))

        faces_list: List[Face] = []
        if with_faces and n >= 3:
            for i in range(n):
                for j in range(i + 1, n):
                    for k in range(j + 1, n):
                        faces_list.append(Face(u=vertices[i], v=vertices[j], w=vertices[k]))

        return cls(vertices=vertices, edges=tuple(edges_list), faces=tuple(faces_list))

    @classmethod
    def path_graph(
        cls,
        n: int,
        weights: Optional[Mapping[Tuple[str, str], Any]] = None,
    ) -> SimplicialComplex:
        """Construct an n-vertex directed path graph: 0 -> 1 -> ... -> n-1 (acyclic tree)."""
        if n < 2:
            raise ValueError(f"Path graph requires at least 2 vertices, got {n}.")
        vertices = tuple(f"v{i}" for i in range(n))
        edges_list: List[Edge] = []
        for i in range(n - 1):
            u = vertices[i]
            v = vertices[i + 1]
            w = Fraction(weights.get((u, v), 1)) if weights else Fraction(1)
            edges_list.append(Edge(u=u, v=v, weight=w))
        return cls(vertices=vertices, edges=tuple(edges_list), faces=())
