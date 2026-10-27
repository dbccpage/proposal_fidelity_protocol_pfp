"""Surface Manifold Validation, Orientability, and Discrete Gauss-Bonnet Curvature for C038.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import defaultdict, deque
from fractions import Fraction
from typing import Any, Mapping

try:
    from .exact_transport import format_rational, is_exact_int
except (ImportError, ValueError):
    from exact_transport import format_rational, is_exact_int  # type: ignore


def solve_surface_case(
    case: Mapping[str, Any],
) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
    """Validates 2D closed triangulated surface and computes topological and curvature invariants.

    Returns:
      (status, extra, solution)
      - status == "UNKNOWN": extra={"refusal_code": ...}
      - status == "OUT_OF_SCOPE": extra={"witness": ...}
      - status == "SOLVED": solution={...}
    """
    if not isinstance(case, Mapping):
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    triangles_raw = case.get("triangles")
    if not isinstance(triangles_raw, list) or len(triangles_raw) == 0:
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    if len(triangles_raw) > 200:
        return "UNKNOWN", {"refusal_code": "TOO_MANY_TRIANGLES"}, None

    triangles: list[tuple[int, int, int]] = []
    norm_triangles: list[tuple[int, int, int]] = []
    for tri in triangles_raw:
        if not isinstance(tri, (list, tuple)) or len(tri) != 3:
            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
        for v in tri:
            if not is_exact_int(v):
                return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
        if len(set(tri)) != 3:
            # Degenerate triangle (duplicate vertex in same triangle)
            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
        triangles.append((tri[0], tri[1], tri[2]))
        norm_triangles.append(tuple(sorted([tri[0], tri[1], tri[2]])))

    # Duplicate triangle check
    if len(set(norm_triangles)) != len(norm_triangles):
        # In a closed manifold, each edge has count 2. Duplicating a triangle would violate edge count.
        # But if detected directly or via edge count:
        pass

    # 1. Edge-triangle incidence
    edge_triangles: dict[tuple[int, int], list[int]] = defaultdict(list)
    for idx, (u, v, w) in enumerate(triangles):
        e1 = tuple(sorted((u, v)))
        e2 = tuple(sorted((v, w)))
        e3 = tuple(sorted((w, u)))
        edge_triangles[e1].append(idx)
        edge_triangles[e2].append(idx)
        edge_triangles[e3].append(idx)

    for edge in sorted(edge_triangles.keys()):
        count = len(edge_triangles[edge])
        if count != 2:
            witness = {
                "kind": "edge_not_two_triangles",
                "edge": [edge[0], edge[1]],
                "count": count,
            }
            return "OUT_OF_SCOPE", {"witness": witness}, None

    # 2. Vertex link topology
    vertex_triangles: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    for tri in triangles:
        for v in tri:
            vertex_triangles[v].append(tri)

    for v in sorted(vertex_triangles.keys()):
        tris = vertex_triangles[v]
        link_adj: dict[int, set[int]] = defaultdict(set)
        for tri in tris:
            other = [u for u in tri if u != v]
            a, b = other[0], other[1]
            link_adj[a].add(b)
            link_adj[b].add(a)

        link_vertices = list(link_adj.keys())
        if len(link_vertices) < 3:
            witness = {"kind": "vertex_link_not_a_cycle", "vertex": v}
            return "OUT_OF_SCOPE", {"witness": witness}, None

        # Degree of every link vertex must be 2
        for u in link_vertices:
            if len(link_adj[u]) != 2:
                witness = {"kind": "vertex_link_not_a_cycle", "vertex": v}
                return "OUT_OF_SCOPE", {"witness": witness}, None

        # Link must be a single connected cycle
        visited: set[int] = set()
        start = link_vertices[0]
        q: deque[int] = deque([start])
        visited.add(start)
        while q:
            curr = q.popleft()
            for nbr in link_adj[curr]:
                if nbr not in visited:
                    visited.add(nbr)
                    q.append(nbr)

        if len(visited) != len(link_vertices):
            witness = {"kind": "vertex_link_not_a_cycle", "vertex": v}
            return "OUT_OF_SCOPE", {"witness": witness}, None

    # 3. Surface dual graph connectivity
    tri_adj: dict[int, set[int]] = defaultdict(set)
    for e, t_indices in edge_triangles.items():
        t1, t2 = t_indices
        tri_adj[t1].add(t2)
        tri_adj[t2].add(t1)

    visited_tris: set[int] = set()
    q_tri: deque[int] = deque([0])
    visited_tris.add(0)
    while q_tri:
        curr = q_tri.popleft()
        for nbr in tri_adj[curr]:
            if nbr not in visited_tris:
                visited_tris.add(nbr)
                q_tri.append(nbr)

    if len(visited_tris) != len(triangles):
        # Disconnected surface
        comp_count = 1
        unvisited = set(range(len(triangles))) - visited_tris
        while unvisited:
            comp_count += 1
            st = min(unvisited)
            q_c = deque([st])
            unvisited.remove(st)
            while q_c:
                c_curr = q_c.popleft()
                for nbr in tri_adj[c_curr]:
                    if nbr in unvisited:
                        unvisited.remove(nbr)
                        q_c.append(nbr)
        witness = {"kind": "surface_disconnected", "components": comp_count}
        return "OUT_OF_SCOPE", {"witness": witness}, None

    # 4. Orientability via BFS propagation
    oriented: dict[int, tuple[int, int, int]] = {}
    oriented[0] = triangles[0]
    q_orient: deque[int] = deque([0])
    orientable = True

    while q_orient and orientable:
        curr_idx = q_orient.popleft()
        c0, c1, c2 = oriented[curr_idx]
        curr_edges = {(c0, c1), (c1, c2), (c2, c0)}

        for nbr_idx in tri_adj[curr_idx]:
            nbr_tri = triangles[nbr_idx]
            shared = set(triangles[curr_idx]) & set(nbr_tri)
            if len(shared) != 2:
                continue
            u, v = tuple(shared)
            if (u, v) in curr_edges:
                required_nbr_dir = (v, u)
            else:
                required_nbr_dir = (u, v)

            o1 = (nbr_tri[0], nbr_tri[1], nbr_tri[2])
            o1_edges = {(o1[0], o1[1]), (o1[1], o1[2]), (o1[2], o1[0])}
            o2 = (nbr_tri[0], nbr_tri[2], nbr_tri[1])

            if nbr_idx not in oriented:
                if required_nbr_dir in o1_edges:
                    oriented[nbr_idx] = o1
                else:
                    oriented[nbr_idx] = o2
                q_orient.append(nbr_idx)
            else:
                actual_o = oriented[nbr_idx]
                actual_edges = {
                    (actual_o[0], actual_o[1]),
                    (actual_o[1], actual_o[2]),
                    (actual_o[2], actual_o[0]),
                }
                if required_nbr_dir not in actual_edges:
                    orientable = False
                    break

    # 5. Combinatorial topology and curvature
    V = len(vertex_triangles)
    E = len(edge_triangles)
    F = len(triangles)
    chi = V - E + F

    if orientable:
        g = (2 - chi) // 2
        classification = {"orientable_genus": g}
    else:
        h = 2 - chi
        classification = {"non_orientable_genus": h}

    vertex_curvature: dict[str, str] = {}
    gauss_bonnet_sum = Fraction(0)
    for v in sorted(vertex_triangles.keys()):
        deg_v = len(vertex_triangles[v])
        k_v = Fraction(6 - deg_v, 6)
        vertex_curvature[str(v)] = format_rational(k_v)
        gauss_bonnet_sum += k_v

    assert gauss_bonnet_sum == chi, f"Gauss-Bonnet sum {gauss_bonnet_sum} != Euler {chi}"

    solution = {
        "V": V,
        "E": E,
        "F": F,
        "euler": chi,
        "orientable": orientable,
        "classification": classification,
        "vertex_curvature": vertex_curvature,
    }
    return "SOLVED", None, solution
