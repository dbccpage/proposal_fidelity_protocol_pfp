"""Forman and Ollivier-Ricci Curvature on Graphs for C038.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import defaultdict, deque
from fractions import Fraction
from typing import Any, Mapping

try:
    from .exact_transport import (
        compute_kantorovich_potential_on_graph,
        exact_optimal_transport_primal_dual,
        format_rational,
        is_exact_int,
        parse_rational,
    )
except (ImportError, ValueError):
    from exact_transport import (  # type: ignore
        compute_kantorovich_potential_on_graph,
        exact_optimal_transport_primal_dual,
        format_rational,
        is_exact_int,
        parse_rational,
    )


def solve_graph_case(
    case: Mapping[str, Any],
) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
    """Computes exact Forman and Ollivier-Ricci curvature on a graph with transport certificates.

    Returns:
      (status, extra, solution)
      - status == "UNKNOWN": extra={"refusal_code": ...}
      - status == "OUT_OF_SCOPE": extra={"witness": ...}
      - status == "SOLVED": solution={...}
    """
    if not isinstance(case, Mapping):
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    # Parse and validate alpha
    if "alpha" not in case:
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
    alpha_raw = case["alpha"]
    try:
        alpha = parse_rational(alpha_raw)
    except (TypeError, ValueError, ZeroDivisionError):
        return "UNKNOWN", {"refusal_code": "INVALID_ALPHA"}, None

    if alpha < Fraction(0) or alpha >= Fraction(1):
        return "UNKNOWN", {"refusal_code": "INVALID_ALPHA"}, None

    # Parse and validate edges
    edges_raw = case.get("edges")
    if not isinstance(edges_raw, list) or len(edges_raw) == 0:
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    seen_edges: set[tuple[int, int]] = set()
    cleaned_edges: list[tuple[int, int]] = []
    vertex_set: set[int] = set()

    for item in edges_raw:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
        u, v = item[0], item[1]
        if not is_exact_int(u) or not is_exact_int(v):
            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

        # Check self-loop
        if u == v:
            witness = {"kind": "self_loop", "vertex": u}
            return "OUT_OF_SCOPE", {"witness": witness}, None

        canon_edge = (min(u, v), max(u, v))
        if canon_edge in seen_edges:
            witness = {"kind": "multigraph", "edge": [canon_edge[0], canon_edge[1]]}
            return "OUT_OF_SCOPE", {"witness": witness}, None

        seen_edges.add(canon_edge)
        cleaned_edges.append(canon_edge)
        vertex_set.add(u)
        vertex_set.add(v)

    # Size bounds
    all_vertices = sorted(vertex_set)
    V_count = len(all_vertices)
    E_count = len(cleaned_edges)

    if V_count > 60 or E_count > 200:
        return "UNKNOWN", {"refusal_code": "GRAPH_TOO_LARGE"}, None

    # Build adjacency
    adj: dict[int, list[int]] = defaultdict(list)
    for u, v in cleaned_edges:
        adj[u].append(v)
        adj[v].append(u)

    # Connectedness check
    visited: set[int] = set()
    q: deque[int] = deque([all_vertices[0]])
    visited.add(all_vertices[0])
    while q:
        curr = q.popleft()
        for nbr in adj[curr]:
            if nbr not in visited:
                visited.add(nbr)
                q.append(nbr)

    if len(visited) != V_count:
        # Count connected components
        components = 1
        unvisited = set(all_vertices) - visited
        while unvisited:
            components += 1
            st = min(unvisited)
            q_c = deque([st])
            unvisited.remove(st)
            while q_c:
                c_curr = q_c.popleft()
                for nbr in adj[c_curr]:
                    if nbr in unvisited:
                        unvisited.remove(nbr)
                        q_c.append(nbr)
        witness = {"kind": "graph_disconnected", "components": components}
        return "OUT_OF_SCOPE", {"witness": witness}, None

    # Compute all-pairs shortest paths via BFS
    distances: dict[int, dict[int, int]] = {}
    for s in all_vertices:
        d = {v: 999999 for v in all_vertices}
        d[s] = 0
        q_bfs = deque([s])
        while q_bfs:
            curr = q_bfs.popleft()
            for nbr in adj[curr]:
                if d[nbr] == 999999:
                    d[nbr] = d[curr] + 1
                    q_bfs.append(nbr)
        distances[s] = d

    deg = {v: len(adj[v]) for v in all_vertices}

    # Process all edges in canonical sorted order
    sorted_edges = sorted(cleaned_edges)
    edge_results: list[dict[str, Any]] = []

    for u, v in sorted_edges:
        # Forman curvature: 4 - deg(u) - deg(v)
        forman = 4 - deg[u] - deg[v]

        # Probability measures m_u and m_v
        m_u = {u: alpha}
        for nbr in adj[u]:
            m_u[nbr] = (Fraction(1) - alpha) / deg[u]

        m_v = {v: alpha}
        for nbr in adj[v]:
            m_v[nbr] = (Fraction(1) - alpha) / deg[v]

        sources = sorted(m_u.keys())
        sinks = sorted(m_v.keys())
        costs = {(i, j): distances[i][j] for i in sources for j in sinks}

        w1, active_plan, _, _ = exact_optimal_transport_primal_dual(sources, sinks, m_u, m_v, costs)

        d_uv = distances[u][v]  # Always 1 for adjacent vertices
        ollivier = Fraction(1) - (w1 / d_uv)

        # Dual Kantorovich potential
        phi = compute_kantorovich_potential_on_graph(
            all_vertices, cleaned_edges, active_plan, distances
        )

        # Strong duality assertion
        dual_val = sum(
            phi[w] * (m_u.get(w, Fraction(0)) - m_v.get(w, Fraction(0))) for w in all_vertices
        )
        assert dual_val == w1, f"Duality gap! dual={dual_val} != primal={w1}"

        # 1-Lipschitz assertion
        for a, b in cleaned_edges:
            assert abs(phi[a] - phi[b]) <= 1, f"Slope violation on edge ({a}, {b})"

        # Format plan
        plan_list = [
            {"from": i, "to": j, "mass": format_rational(mass)}
            for (i, j), mass in sorted(active_plan.items())
        ]

        # Format potential
        potential_dict = {str(w): str(phi[w]) for w in all_vertices}

        edge_results.append(
            {
                "edge": [u, v],
                "forman": forman,
                "ollivier": format_rational(ollivier),
                "plan": plan_list,
                "potential": potential_dict,
            }
        )

    solution = {
        "edges": edge_results,
    }
    return "SOLVED", None, solution
