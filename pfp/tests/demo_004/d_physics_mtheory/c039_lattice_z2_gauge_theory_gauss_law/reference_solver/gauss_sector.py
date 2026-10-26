"""Gauss-Law Sector Dimension Solver for C039.

Computes the exact Hilbert space dimension of Z2 Gauss-law sectors on finite graphs:
- Empty sector (dim = 0) with witness {"charge_product": -1} if prod(c_v) = -1.
- Exact dimension 2^{E - V + 1} if prod(c_v) = +1.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Mapping


def solve_gauss_law_sector(
    case: Mapping[str, Any],
) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
    """Evaluates Gauss-law sector dimension on a connected graph.

    Returns:
        (status, extra, solution)
    """
    if not isinstance(case, Mapping):
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    graph_raw = case.get("graph")
    if isinstance(graph_raw, Mapping):
        vertices_raw = graph_raw.get("vertices")
        edges_raw = graph_raw.get("edges")
    else:
        vertices_raw = case.get("vertices")
        edges_raw = case.get("edges")

    charges_raw = case.get("charges")

    if edges_raw is None or not isinstance(edges_raw, list):
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    # Parse vertices
    vertex_map: dict[Any, int] = {}
    if vertices_raw is not None:
        if not isinstance(vertices_raw, list):
            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
        for v in vertices_raw:
            if isinstance(v, bool):
                return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
            if v not in vertex_map:
                vertex_map[v] = len(vertex_map)

    # Parse edges
    edge_list: list[tuple[int, int]] = []
    for idx, e in enumerate(edges_raw):
        if isinstance(e, (list, tuple)) and len(e) == 2:
            u_raw, v_raw = e[0], e[1]
        elif isinstance(e, dict):
            if (
                "endpoints" in e
                and isinstance(e["endpoints"], (list, tuple))
                and len(e["endpoints"]) == 2
            ):
                u_raw, v_raw = e["endpoints"][0], e["endpoints"][1]
            elif "u" in e and "v" in e:
                u_raw, v_raw = e["u"], e["v"]
            else:
                return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
        else:
            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

        if isinstance(u_raw, bool) or isinstance(v_raw, bool):
            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

        if u_raw not in vertex_map:
            vertex_map[u_raw] = len(vertex_map)
        if v_raw not in vertex_map:
            vertex_map[v_raw] = len(vertex_map)

        u = vertex_map[u_raw]
        v = vertex_map[v_raw]
        edge_list.append((u, v))

    V = len(vertex_map)
    E = len(edge_list)

    if E > 300:
        return "UNKNOWN", {"refusal_code": "TOO_MANY_EDGES"}, None

    if V == 0:
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    # Check graph connectivity
    adj: dict[int, list[int]] = defaultdict(list)
    for u, v in edge_list:
        adj[u].append(v)
        adj[v].append(u)

    visited: set[int] = set()
    q = deque([0])
    visited.add(0)
    while q:
        curr = q.popleft()
        for nbr in adj[curr]:
            if nbr not in visited:
                visited.add(nbr)
                q.append(nbr)

    if len(visited) != V:
        comp_count = 1
        unvisited = set(range(V)) - visited
        while unvisited:
            comp_count += 1
            st = min(unvisited)
            q_c = deque([st])
            unvisited.remove(st)
            while q_c:
                c_curr = q_c.popleft()
                for nbr in adj[c_curr]:
                    if nbr in unvisited:
                        unvisited.remove(nbr)
                        q_c.append(nbr)
        witness = {"kind": "graph_disconnected", "components": comp_count}
        return "OUT_OF_SCOPE", {"witness": witness}, None

    # Parse and validate charges
    # Charges can be dict {v: +/-1} or list [+/-1, ...]
    if charges_raw is None:
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    charge_values: list[int] = []
    if isinstance(charges_raw, dict):
        for v_raw, v_idx in vertex_map.items():
            if (
                v_raw not in charges_raw
                and str(v_raw) not in charges_raw
                and v_idx not in charges_raw
            ):
                return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
            val = (
                charges_raw.get(v_raw)
                if v_raw in charges_raw
                else charges_raw.get(str(v_raw), charges_raw.get(v_idx))
            )
            if isinstance(val, bool) or type(val) is not int or val not in (1, -1):
                return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
            charge_values.append(val)
    elif isinstance(charges_raw, list):
        if len(charges_raw) != V:
            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
        for val in charges_raw:
            if isinstance(val, bool) or type(val) is not int or val not in (1, -1):
                return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
            charge_values.append(val)
    else:
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    # Compute total charge product
    charge_prod = 1
    for c in charge_values:
        charge_prod *= c

    if charge_prod == -1:
        return (
            "SOLVED",
            None,
            {
                "sector_dimension": 0,
                "witness": {"charge_product": -1},
            },
        )
    elif charge_prod == 1:
        dim = 1 << (E - V + 1)
        return (
            "SOLVED",
            None,
            {
                "sector_dimension": dim,
            },
        )
    else:
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
