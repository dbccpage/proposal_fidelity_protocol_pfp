"""Carrier network topology for the Adversary acts.

`Network` is a pure value object: nodes, directed edges, and optional 2- and
3-cells. It computes nothing. It was the one name Adversary used from the retired
Python crate `engine.crates.residuals.network_residual` (removed in
5e12f22f4); the class body is carried over unchanged. Residual and boundary
calculations stay with the Rust crates.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple


@dataclass(frozen=True, slots=True)
class Network:
    """Directed network topology with optional 2-cell faces and 3-cell tetrahedra.

    contract_id: urn:core:math:incidence_matrix:v1.0.0

    Accepts both list and tuple inputs; coerces to tuples internally.
    """
    nodes: Tuple[Any, ...]
    edges: Tuple[Tuple[Any, Any], ...]
    faces: Tuple[Tuple[Any, Any, Any], ...] = ()
    tetrahedra: Tuple[Tuple[Any, Any, Any, Any], ...] = ()
    four_simplices: Tuple[Tuple[Any, Any, Any, Any, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "edges", tuple(tuple(e) for e in self.edges))
        if self.faces:
            object.__setattr__(self, "faces", tuple(tuple(f) for f in self.faces))
        if self.tetrahedra:
            object.__setattr__(self, "tetrahedra", tuple(tuple(t) for t in self.tetrahedra))
        if self.four_simplices:
            object.__setattr__(self, "four_simplices", tuple(tuple(s) for s in self.four_simplices))
        node_set = set(self.nodes)
        for u, v in self.edges:
            if u not in node_set or v not in node_set:
                raise ValueError(
                    f"Edge ({u}, {v}) references node(s) not in node set"
                )


__all__ = ["Network"]
