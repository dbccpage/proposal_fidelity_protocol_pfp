"""Simple Graph Data Structure and Local Complementation for C024.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any


def validate_simple_graph(num_vertices: int, edges: Any) -> tuple[bool, dict[str, Any] | None]:
    """Validates that (num_vertices, edges) defines a valid simple undirected graph."""
    if not isinstance(num_vertices, int) or num_vertices < 2 or num_vertices > 16:
        return False, {
            "kind": "num_vertices_out_of_bounds",
            "num_vertices": num_vertices,
            "min_allowed": 2,
            "max_allowed": 16,
        }

    if not isinstance(edges, list):
        return False, {"kind": "invalid_edge_list", "reason": "edges must be a list"}

    seen_edges: set[tuple[int, int]] = set()
    for idx, e in enumerate(edges):
        if not isinstance(e, (list, tuple)) or len(e) != 2:
            return False, {"kind": "invalid_edge_format", "edge_index": idx, "edge": e}
        u, v = e[0], e[1]
        if not isinstance(u, int) or not isinstance(v, int):
            return False, {"kind": "invalid_vertex_type", "edge": [u, v]}
        if u < 0 or u >= num_vertices or v < 0 or v >= num_vertices:
            return False, {
                "kind": "vertex_out_of_bounds",
                "edge": [u, v],
                "num_vertices": num_vertices,
            }
        if u == v:
            return False, {"kind": "self_loop", "edge": [u, v]}

        can_e = (min(u, v), max(u, v))
        if can_e in seen_edges:
            return False, {"kind": "duplicate_edge", "edge": [u, v]}
        seen_edges.add(can_e)

    return True, None


class SimpleGraph:
    """Simple undirected graph on vertices 0..n-1 with local complementation."""

    def __init__(self, num_vertices: int, edges: list[list[int]] | None = None) -> None:
        self.n: int = num_vertices
        # Adjacency matrix over F_2
        self.adj: list[list[int]] = [[0] * num_vertices for _ in range(num_vertices)]
        if edges:
            for u, v in edges:
                self.adj[u][v] = 1
                self.adj[v][u] = 1

    def copy(self) -> SimpleGraph:
        g = SimpleGraph(self.n)
        g.adj = [row[:] for row in self.adj]
        return g

    def has_edge(self, u: int, v: int) -> bool:
        return self.adj[u][v] == 1

    def get_neighbors(self, v: int) -> list[int]:
        return [u for u in range(self.n) if self.adj[v][u] == 1]

    def local_complementation(self, v: int) -> SimpleGraph:
        """Applies local complementation at vertex v (G * v).

        Complements the induced subgraph on the neighborhood N(v).
        Leaves all other edges unchanged.
        """
        if v < 0 or v >= self.n:
            raise ValueError(f"Vertex {v} out of bounds for graph with {self.n} vertices")

        nbrs = self.get_neighbors(v)
        deg = len(nbrs)
        new_g = self.copy()

        for i in range(deg):
            u = nbrs[i]
            for j in range(i + 1, deg):
                w = nbrs[j]
                new_g.adj[u][w] ^= 1
                new_g.adj[w][u] ^= 1

        return new_g

    def to_edge_list(self) -> list[list[int]]:
        """Returns sorted canonical edge list."""
        edges: list[list[int]] = []
        for u in range(self.n):
            for v in range(u + 1, self.n):
                if self.adj[u][v] == 1:
                    edges.append([u, v])
        return edges

    def to_canonical_tuple(self) -> tuple[int, ...]:
        """Returns integer bitmask tuple representing adjacency matrix for fast hashing."""
        masks: list[int] = []
        for u in range(self.n):
            mask = 0
            for v in range(self.n):
                if self.adj[u][v]:
                    mask |= 1 << v
            masks.append(mask)
        return tuple(masks)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SimpleGraph):
            return False
        if self.n != other.n:
            return False
        return self.adj == other.adj

    def __hash__(self) -> int:
        return hash((self.n, self.to_canonical_tuple()))


__all__ = [
    "SimpleGraph",
    "validate_simple_graph",
]
