"""Checker 1: Combinatorial Primal Verifier for Challenge C038.

Evaluates surface 2-manifold hypothesis via edge-triangle incidence counting,
link cycle traversal, and facet orientation BFS. Evaluates graph curvature via
BFS distance matrix, exact primal LP transport marginal checks, and non-negativity.

Shares ZERO code with Checker 2.
AuthorityEffect: None.
"""

from __future__ import annotations

import math
from collections import deque
from fractions import Fraction
from typing import Any, Mapping

# -------------------------------------------------------------------------
# Checker 1 Private Type Guards & Rational Validators
# -------------------------------------------------------------------------


def _c1_is_int(val: Any) -> bool:
    """Strict check for int, rejecting bool."""
    return type(val) is int and not isinstance(val, bool)


def _c1_is_integer_str(val: Any) -> bool:
    """Checks if val is an exact integer string without decimals."""
    if type(val) is not str:
        return False
    if "." in val or "e" in val.lower() or "/" in val:
        return False
    s = val.lstrip("-")
    return s.isdigit() and len(s) > 0


def _c1_is_reduced_rational_str(val: Any) -> bool:
    """Checks if val is a canonical reduced rational string 'p/q' or integer string."""
    if type(val) is not str:
        return False
    if "." in val or "e" in val.lower():
        return False
    if "/" in val:
        parts = val.split("/")
        if len(parts) != 2:
            return False
        num_s, den_s = parts
        if not _c1_is_integer_str(num_s) or not den_s.isdigit():
            return False
        den = int(den_s)
        if den <= 1:
            return False
        num = int(num_s)
        if math.gcd(abs(num), den) != 1:
            return False
        return True
    return _c1_is_integer_str(val)


def _c1_to_reduced_str(frac: Fraction) -> str:
    """Formats a Fraction as a canonical reduced string."""
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def _c1_verify_refusal_warranted(case: Mapping[str, Any], refusal_code: str) -> tuple[bool, str]:
    """Validates that a claimed UNKNOWN refusal code is defect-grounded and warranted."""
    valid_codes = frozenset(
        {
            "TOO_MANY_TRIANGLES",
            "GRAPH_TOO_LARGE",
            "INVALID_ALPHA",
            "MALFORMED_CASE_STRUCTURE",
        }
    )
    if refusal_code not in valid_codes:
        return False, f"FAIL (C1): unrecognized refusal code {refusal_code!r}"

    if not isinstance(case, Mapping):
        if refusal_code == "MALFORMED_CASE_STRUCTURE":
            return True, "PASS (C1): valid UNKNOWN refusal for non-Mapping case"
        return (
            False,
            f"FAIL (C1): non-Mapping case requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
        )

    query = case.get("query")
    if query not in ("surface", "graph"):
        if refusal_code == "MALFORMED_CASE_STRUCTURE":
            return True, "PASS (C1): valid UNKNOWN refusal for invalid query"
        return (
            False,
            f"FAIL (C1): invalid query requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
        )

    if query == "surface":
        triangles = case.get("triangles")
        if not isinstance(triangles, list) or len(triangles) == 0:
            if refusal_code == "MALFORMED_CASE_STRUCTURE":
                return True, "PASS (C1): valid UNKNOWN refusal for malformed/empty triangles list"
            return (
                False,
                f"FAIL (C1): malformed triangles requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
            )

        if len(triangles) > 200:
            if refusal_code == "TOO_MANY_TRIANGLES":
                return True, "PASS (C1): valid UNKNOWN refusal for TOO_MANY_TRIANGLES"
            return (
                False,
                f"FAIL (C1): > 200 triangles requires TOO_MANY_TRIANGLES, got {refusal_code}",
            )

        for t in triangles:
            if not (isinstance(t, (list, tuple)) and len(t) == 3):
                if refusal_code == "MALFORMED_CASE_STRUCTURE":
                    return True, "PASS (C1): valid UNKNOWN refusal for malformed triangle length"
                return (
                    False,
                    f"FAIL (C1): malformed triangle length requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
                )
            for v in t:
                if not _c1_is_int(v):
                    if refusal_code == "MALFORMED_CASE_STRUCTURE":
                        return True, "PASS (C1): valid UNKNOWN refusal for non-integer vertex"
                    return (
                        False,
                        f"FAIL (C1): non-integer vertex requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
                    )
            u, v, w = t[0], t[1], t[2]
            if u == v or v == w or w == u:
                if refusal_code == "MALFORMED_CASE_STRUCTURE":
                    return True, "PASS (C1): valid UNKNOWN refusal for degenerate triangle"
                return (
                    False,
                    f"FAIL (C1): degenerate triangle requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
                )

        return (
            False,
            f"FAIL (C1): unwarranted UNKNOWN refusal ({refusal_code}) on syntactically valid surface",
        )

    if query == "graph":
        if "alpha" not in case:
            if refusal_code == "MALFORMED_CASE_STRUCTURE":
                return True, "PASS (C1): valid UNKNOWN refusal for missing alpha"
            return (
                False,
                f"FAIL (C1): missing alpha requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
            )

        alpha_raw = case["alpha"]
        alpha_str = str(alpha_raw) if alpha_raw is not None else ""
        if not _c1_is_reduced_rational_str(alpha_str):
            if refusal_code == "INVALID_ALPHA":
                return True, "PASS (C1): valid UNKNOWN refusal for non-rational alpha"
            return (
                False,
                f"FAIL (C1): non-rational alpha requires INVALID_ALPHA, got {refusal_code}",
            )

        alpha_val = Fraction(alpha_str)
        if alpha_val < 0 or alpha_val >= 1:
            if refusal_code == "INVALID_ALPHA":
                return True, "PASS (C1): valid UNKNOWN refusal for alpha out of [0, 1) bounds"
            return (
                False,
                f"FAIL (C1): out of bounds alpha requires INVALID_ALPHA, got {refusal_code}",
            )

        edges_raw = case.get("edges")
        if not isinstance(edges_raw, list) or len(edges_raw) == 0:
            if refusal_code == "MALFORMED_CASE_STRUCTURE":
                return True, "PASS (C1): valid UNKNOWN refusal for malformed/empty edges list"
            return (
                False,
                f"FAIL (C1): malformed edges requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
            )

        cleaned_edges: set[tuple[int, int]] = set()
        vertex_set: set[int] = set()
        for e in edges_raw:
            if not (isinstance(e, (list, tuple)) and len(e) == 2):
                if refusal_code == "MALFORMED_CASE_STRUCTURE":
                    return True, "PASS (C1): valid UNKNOWN refusal for malformed edge length"
                return (
                    False,
                    f"FAIL (C1): malformed edge length requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
                )
            u, v = e[0], e[1]
            if not (_c1_is_int(u) and _c1_is_int(v)):
                if refusal_code == "MALFORMED_CASE_STRUCTURE":
                    return True, "PASS (C1): valid UNKNOWN refusal for non-integer edge vertices"
                return (
                    False,
                    f"FAIL (C1): non-integer edge vertices requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
                )

            if u != v:
                cleaned_edges.add((min(u, v), max(u, v)))
                vertex_set.add(u)
                vertex_set.add(v)

        if len(vertex_set) > 60 or len(cleaned_edges) > 200:
            if refusal_code == "GRAPH_TOO_LARGE":
                return True, "PASS (C1): valid UNKNOWN refusal for GRAPH_TOO_LARGE"
            return (
                False,
                f"FAIL (C1): graph size bounds exceeded requires GRAPH_TOO_LARGE, got {refusal_code}",
            )

        return (
            False,
            f"FAIL (C1): unwarranted UNKNOWN refusal ({refusal_code}) on syntactically valid graph within bounds",
        )

    return False, "FAIL (C1): refusal verification fell through"


# -------------------------------------------------------------------------
# Checker 1 Surface Verification Logic
# -------------------------------------------------------------------------


def _c1_verify_surface_manifold(
    triangles: list[Any],
) -> tuple[bool, str, dict[str, Any] | None]:
    """Validates 2-manifold hypothesis via edge incidence, link cycles, and connectedness."""
    if len(triangles) == 0:
        return False, "MALFORMED_CASE_STRUCTURE", None
    if len(triangles) > 200:
        return False, "TOO_MANY_TRIANGLES", None

    norm_triangles = []
    vertices = set()
    edge_counts: dict[tuple[int, int], int] = {}
    v_to_triangles: dict[int, list[list[int]]] = {}

    for t in triangles:
        if not (isinstance(t, (list, tuple)) and len(t) == 3):
            return False, "MALFORMED_CASE_STRUCTURE", None
        for v in t:
            if not _c1_is_int(v):
                return False, "MALFORMED_CASE_STRUCTURE", None
            vertices.add(v)
        u, v, w = t[0], t[1], t[2]
        if u == v or v == w or w == u:
            return False, "MALFORMED_CASE_STRUCTURE", None
        t_sorted = tuple(sorted([u, v, w]))
        norm_triangles.append(t_sorted)

        for a, b in [(u, v), (v, w), (w, u)]:
            e = (min(a, b), max(a, b))
            edge_counts[e] = edge_counts.get(e, 0) + 1

        for vert in (u, v, w):
            if vert not in v_to_triangles:
                v_to_triangles[vert] = []
            v_to_triangles[vert].append(list(t))

    # 1. Edge incidence: every edge must lie in exactly 2 triangles
    for e, count in edge_counts.items():
        if count != 2:
            return (
                False,
                "NON_MANIFOLD_EDGE",
                {
                    "kind": "edge_not_two_triangles",
                    "edge": list(e),
                    "count": count,
                },
            )

    # 2. Vertex links: link of every vertex must be a single cycle
    for v in vertices:
        incident_triangles = v_to_triangles.get(v, [])
        link_adj: dict[int, list[int]] = {}
        for t_item in incident_triangles:
            other = [x for x in t_item if x != v]
            if len(other) != 2:
                continue
            for nbr, peer in [(other[0], other[1]), (other[1], other[0])]:
                if nbr not in link_adj:
                    link_adj[nbr] = []
                link_adj[nbr].append(peer)

        if len(link_adj) < 3:
            return (
                False,
                "NON_CYCLE_LINK",
                {
                    "kind": "vertex_link_not_a_cycle",
                    "vertex": v,
                },
            )

        # In a 2-manifold, degree of every node in link must be 2
        for l_node, peers in link_adj.items():
            if len(peers) != 2:
                return (
                    False,
                    "NON_CYCLE_LINK",
                    {
                        "kind": "vertex_link_not_a_cycle",
                        "vertex": v,
                    },
                )

        # Check that link is connected (single cycle)
        start_node = next(iter(link_adj.keys()))
        visited = set()
        curr = start_node
        prev = None
        while curr not in visited:
            visited.add(curr)
            peers = link_adj[curr]
            next_node = peers[0] if peers[0] != prev else peers[1]
            prev = curr
            curr = next_node
        if len(visited) != len(link_adj):
            return (
                False,
                "DISCONNECTED_LINK",
                {
                    "kind": "vertex_link_not_a_cycle",
                    "vertex": v,
                },
            )

    # 3. Connectedness of the surface
    adj: dict[int, set[int]] = {v: set() for v in vertices}
    for e in edge_counts.keys():
        adj[e[0]].add(e[1])
        adj[e[1]].add(e[0])

    start_v = next(iter(vertices))
    visited_v = set()
    q = deque([start_v])
    while q:
        curr = q.popleft()
        if curr in visited_v:
            continue
        visited_v.add(curr)
        for nbr in adj[curr]:
            if nbr not in visited_v:
                q.append(nbr)

    if len(visited_v) != len(vertices):
        return False, "DISCONNECTED_SURFACE", {"kind": "surface_disconnected"}

    return True, "OK", None


def _c1_determine_orientability_bfs(
    triangles: list[Any],
) -> tuple[bool, str]:
    """Determines orientability via facet orientation propagation BFS."""
    edge_to_t: dict[tuple[int, int], list[int]] = {}
    for i, t in enumerate(triangles):
        u, v, w = t[0], t[1], t[2]
        for a, b in [(u, v), (v, w), (w, u)]:
            e = (min(a, b), max(a, b))
            if e not in edge_to_t:
                edge_to_t[e] = []
            edge_to_t[e].append(i)

    t_adj: dict[int, list[tuple[int, tuple[int, int]]]] = {i: [] for i in range(len(triangles))}
    for e, t_indices in edge_to_t.items():
        if len(t_indices) == 2:
            t1, t2 = t_indices
            t_adj[t1].append((t2, e))
            t_adj[t2].append((t1, e))

    t0 = triangles[0]
    orientations: dict[int, tuple[int, int, int]] = {0: (t0[0], t0[1], t0[2])}
    q = deque([0])

    while q:
        curr = q.popleft()
        curr_t = orientations[curr]
        curr_directed_edges = {
            (curr_t[0], curr_t[1]),
            (curr_t[1], curr_t[2]),
            (curr_t[2], curr_t[0]),
        }

        for nbr, shared_edge in t_adj[curr]:
            u, v = shared_edge
            dir_e = (u, v) if (u, v) in curr_directed_edges else (v, u)
            rev_e = (dir_e[1], dir_e[0])

            nbr_verts = list(triangles[nbr])
            pos1 = (nbr_verts[0], nbr_verts[1], nbr_verts[2])
            pos2 = (nbr_verts[0], nbr_verts[2], nbr_verts[1])

            edges1 = {(pos1[0], pos1[1]), (pos1[1], pos1[2]), (pos1[2], pos1[0])}
            {(pos2[0], pos2[1]), (pos2[1], pos2[2]), (pos2[2], pos2[0])}

            req_orient = pos1 if rev_e in edges1 else pos2

            if nbr in orientations:
                if orientations[nbr] != req_orient:
                    return False, "NON_ORIENTABLE"
            else:
                orientations[nbr] = req_orient
                q.append(nbr)

    return True, "ORIENTABLE"


def _c1_verify_surface_answer(
    case: Mapping[str, Any], answer: Mapping[str, Any]
) -> tuple[bool, str]:
    """Verifies surface query answer against Checker 1 combinatorial criteria."""
    status = answer.get("status")
    triangles = case.get("triangles")
    if not isinstance(triangles, list):
        return False, "FAIL (C1): triangles must be a list"

    # Closed schema whitelist for surface answers
    if status == "SOLVED":
        allowed_keys = {
            "id",
            "case_id",
            "status",
            "V",
            "E",
            "F",
            "euler",
            "orientable",
            "classification",
            "vertex_curvature",
        }
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C1): unexpected key '{k}' in SOLVED answer"
    elif status == "OUT_OF_SCOPE":
        allowed_keys = {"id", "case_id", "status", "witness"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C1): unexpected key '{k}' in OUT_OF_SCOPE answer"
    elif status == "UNKNOWN":
        allowed_keys = {"id", "case_id", "status", "refusal_code", "refusal"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C1): unexpected key '{k}' in UNKNOWN answer"

    is_manifold, err_code, witness = _c1_verify_surface_manifold(triangles)

    if not is_manifold:
        if err_code in ("MALFORMED_CASE_STRUCTURE", "TOO_MANY_TRIANGLES"):
            if status != "UNKNOWN":
                return False, f"FAIL (C1): expected UNKNOWN for {err_code}, got {status}"
            ref_code = answer.get("refusal_code") or answer.get("refusal")
            if ref_code != err_code:
                return False, f"FAIL (C1): expected refusal_code '{err_code}', got '{ref_code}'"
            return True, f"PASS (C1): valid UNKNOWN refusal for {err_code}"
        else:
            if status != "OUT_OF_SCOPE":
                return (
                    False,
                    f"FAIL (C1): non-manifold surface must be refused with OUT_OF_SCOPE, got {status}",
                )
            act_wit = answer.get("witness")
            if not isinstance(act_wit, Mapping):
                return False, "FAIL (C1): witness must be a Mapping"
            if act_wit.get("kind") != witness.get("kind"):
                return (
                    False,
                    f"FAIL (C1): witness kind mismatch: expected {witness.get('kind')}, got {act_wit.get('kind')}",
                )
            return True, "PASS (C1): valid OUT_OF_SCOPE witness for non-manifold"

    if status != "SOLVED":
        return False, f"FAIL (C1): unwarranted refusal on valid 2-manifold surface: {status}"

    # Verify Strict Integer Types (Reject Booleans)
    for int_field in ["V", "E", "F", "euler"]:
        val = answer.get(int_field)
        if not _c1_is_int(val):
            return False, f"FAIL (C1): field '{int_field}' must be strict int, got {type(val)}"

    if type(answer.get("orientable")) is not bool:
        return False, "FAIL (C1): orientable must be a boolean"

    # Compute ground truth metrics
    vertices = set()
    edges = set()
    deg_map: dict[int, int] = {}
    for t in triangles:
        for v in t:
            vertices.add(v)
            deg_map[v] = deg_map.get(v, 0) + 1
        edges.add((min(t[0], t[1]), max(t[0], t[1])))
        edges.add((min(t[1], t[2]), max(t[1], t[2])))
        edges.add((min(t[2], t[0]), max(t[2], t[0])))

    V = len(vertices)
    E = len(edges)
    F = len(triangles)
    chi = V - E + F

    if answer.get("V") != V or answer.get("E") != E or answer.get("F") != F:
        return (
            False,
            f"FAIL (C1): V/E/F mismatch: expected ({V}, {E}, {F}), got ({answer.get('V')}, {answer.get('E')}, {answer.get('F')})",
        )
    if answer.get("euler") != chi:
        return False, f"FAIL (C1): euler mismatch: expected {chi}, got {answer.get('euler')}"

    is_orientable, _ = _c1_determine_orientability_bfs(triangles)
    if answer.get("orientable") is not is_orientable:
        return (
            False,
            f"FAIL (C1): orientable mismatch: expected {is_orientable}, got {answer.get('orientable')}",
        )

    # Verify Classification
    classif = answer.get("classification")
    if not isinstance(classif, Mapping):
        return False, "FAIL (C1): classification must be a Mapping"
    if is_orientable:
        g = (2 - chi) // 2
        g_val = classif.get("orientable_genus")
        if not _c1_is_int(g_val) or g_val != g or "non_orientable_genus" in classif or g < 0:
            return (
                False,
                f"FAIL (C1): classification mismatch for orientable genus: expected {g}, got {g_val}",
            )
    else:
        h = 2 - chi
        h_val = classif.get("non_orientable_genus")
        if not _c1_is_int(h_val) or h_val != h or "orientable_genus" in classif or h < 1:
            return (
                False,
                f"FAIL (C1): classification mismatch for non-orientable genus: expected {h}, got {h_val}",
            )

    # Verify Vertex Combinatorial Curvature
    act_curv = answer.get("vertex_curvature")
    if not isinstance(act_curv, Mapping):
        return False, "FAIL (C1): vertex_curvature must be a Mapping"
    if len(act_curv) != V:
        return (
            False,
            f"FAIL (C1): vertex_curvature length mismatch: expected {V}, got {len(act_curv)}",
        )

    sum_curv = Fraction(0)
    for v in vertices:
        v_str = str(v)
        if v_str not in act_curv:
            return False, f"FAIL (C1): missing curvature for vertex {v}"
        c_val = act_curv[v_str]
        if not _c1_is_reduced_rational_str(c_val):
            return False, f"FAIL (C1): vertex {v} curvature not reduced rational string: {c_val}"
        deg_v = deg_map[v]
        exp_frac = Fraction(6 - deg_v, 6)
        if Fraction(c_val) != exp_frac:
            return (
                False,
                f"FAIL (C1): vertex {v} curvature mismatch: expected {_c1_to_reduced_str(exp_frac)}, got {c_val}",
            )
        sum_curv += Fraction(c_val)

    if sum_curv != Fraction(chi):
        return (
            False,
            f"FAIL (C1): Discrete Gauss-Bonnet sum violation: sum(k_v)={sum_curv} != euler={chi}",
        )

    return True, "PASS (C1): valid combinatorial surface certificate"


# -------------------------------------------------------------------------
# Checker 1 Graph Verification Logic
# -------------------------------------------------------------------------


def _c1_bfs_distance_matrix(
    nodes: list[int], adj: dict[int, list[int]]
) -> dict[tuple[int, int], int]:
    """Computes all-pairs shortest path distances via unweighted BFS."""
    dist: dict[tuple[int, int], int] = {}
    for s in nodes:
        q = deque([s])
        d_map = {s: 0}
        while q:
            u = q.popleft()
            d_u = d_map[u]
            for v in adj.get(u, []):
                if v not in d_map:
                    d_map[v] = d_u + 1
                    q.append(v)
        for t, d_val in d_map.items():
            dist[(s, t)] = d_val
    return dist


def _c1_check_lipschitz_potential(
    phi: Mapping[int, Fraction], edges_set: set[tuple[int, int]]
) -> tuple[bool, str | None]:
    """Validates 1-Lipschitz condition on all graph edges: |phi(u) - phi(v)| <= 1."""
    for u, v in edges_set:
        slope = abs(phi[u] - phi[v])
        if slope > 1:
            return False, f"potential violates 1-Lipschitz on edge ({u}, {v}): slope={slope} > 1"
    return True, None


def _c1_compute_dual_objective(
    phi: Mapping[int, Fraction],
    m_u: Mapping[int, Fraction],
    m_v: Mapping[int, Fraction],
    vertices: set[int],
) -> Fraction:
    """Computes Kantorovich dual objective D = sum_w phi(w) * (m_u(w) - m_v(w))."""
    dual_obj = Fraction(0)
    for w in vertices:
        net_mass = m_u.get(w, Fraction(0)) - m_v.get(w, Fraction(0))
        dual_obj += phi[w] * net_mass
    return dual_obj


def _c1_verify_graph_answer(case: Mapping[str, Any], answer: Mapping[str, Any]) -> tuple[bool, str]:
    """Verifies graph query answer against Checker 1 primal transport criteria."""
    status = answer.get("status")
    edges_raw = case.get("edges")
    alpha_raw = case.get("alpha")

    # Closed schema whitelist for graph answers
    if status == "SOLVED":
        allowed_keys = {"id", "case_id", "status", "edges"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C1): unexpected key '{k}' in SOLVED graph answer"
    elif status == "OUT_OF_SCOPE":
        allowed_keys = {"id", "case_id", "status", "witness"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C1): unexpected key '{k}' in OUT_OF_SCOPE graph answer"
    elif status == "UNKNOWN":
        allowed_keys = {"id", "case_id", "status", "refusal_code", "refusal"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C1): unexpected key '{k}' in UNKNOWN graph answer"

    if not isinstance(edges_raw, list):
        if status == "UNKNOWN":
            ref_code = answer.get("refusal_code") or answer.get("refusal")
            if ref_code == "MALFORMED_CASE_STRUCTURE":
                return True, "PASS (C1): valid UNKNOWN refusal for non-list edges"
            return (
                False,
                f"FAIL (C1): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
            )
        return False, "FAIL (C1): edges must be a list"

    # Validate alpha
    if "alpha" not in case:
        if status == "UNKNOWN":
            ref_code = answer.get("refusal_code") or answer.get("refusal")
            if ref_code == "MALFORMED_CASE_STRUCTURE":
                return True, "PASS (C1): valid UNKNOWN refusal for missing alpha"
            return (
                False,
                f"FAIL (C1): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
            )
        return False, "FAIL (C1): missing alpha must be refused with UNKNOWN"

    alpha_str = str(alpha_raw) if alpha_raw is not None else ""
    if not _c1_is_reduced_rational_str(alpha_str):
        if status != "UNKNOWN":
            return False, "FAIL (C1): invalid alpha must be refused with UNKNOWN"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if ref_code != "INVALID_ALPHA":
            return False, f"FAIL (C1): expected refusal_code 'INVALID_ALPHA', got '{ref_code}'"
        return True, "PASS (C1): invalid alpha refused"
    alpha = Fraction(alpha_str)
    if alpha < 0 or alpha >= 1:
        if status != "UNKNOWN":
            return False, "FAIL (C1): alpha out of bounds must be refused with UNKNOWN"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if ref_code != "INVALID_ALPHA":
            return False, f"FAIL (C1): expected refusal_code 'INVALID_ALPHA', got '{ref_code}'"
        return True, "PASS (C1): alpha out of bounds refused"

    if len(edges_raw) == 0:
        if status != "UNKNOWN":
            return False, "FAIL (C1): empty graph must be UNKNOWN"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if ref_code != "MALFORMED_CASE_STRUCTURE":
            return (
                False,
                f"FAIL (C1): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
            )
        return True, "PASS (C1): empty graph refused"

    # Validate edges & build graph
    vertices = set()
    adj: dict[int, list[int]] = {}
    edges_set = set()

    for e in edges_raw:
        if not (isinstance(e, (list, tuple)) and len(e) == 2):
            if status == "UNKNOWN":
                ref_code = answer.get("refusal_code") or answer.get("refusal")
                if ref_code == "MALFORMED_CASE_STRUCTURE":
                    return True, "PASS (C1): valid UNKNOWN refusal for malformed edge length"
                return (
                    False,
                    f"FAIL (C1): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
                )
            return False, "FAIL (C1): malformed edge list must be refused with UNKNOWN"
        u, v = e[0], e[1]
        if not (_c1_is_int(u) and _c1_is_int(v)):
            if status == "UNKNOWN":
                ref_code = answer.get("refusal_code") or answer.get("refusal")
                if ref_code == "MALFORMED_CASE_STRUCTURE":
                    return True, "PASS (C1): valid UNKNOWN refusal for non-integer edge vertices"
                return (
                    False,
                    f"FAIL (C1): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
                )
            return False, "FAIL (C1): edge vertices must be ints"
        if u == v:
            if status != "OUT_OF_SCOPE":
                return False, "FAIL (C1): self loop must be OUT_OF_SCOPE"
            wit = answer.get("witness")
            if not isinstance(wit, Mapping) or wit.get("kind") != "self_loop":
                return False, f"FAIL (C1): invalid self_loop witness: {wit}"
            return True, "PASS (C1): self loop refused"
        e_norm = (min(u, v), max(u, v))
        if e_norm in edges_set:
            if status != "OUT_OF_SCOPE":
                return False, "FAIL (C1): duplicate edge must be OUT_OF_SCOPE"
            wit = answer.get("witness")
            if not isinstance(wit, Mapping) or wit.get("kind") != "multigraph":
                return False, f"FAIL (C1): invalid multigraph witness: {wit}"
            return True, "PASS (C1): duplicate edge refused"
        edges_set.add(e_norm)
        vertices.add(u)
        vertices.add(v)
        for a, b in [(u, v), (v, u)]:
            if a not in adj:
                adj[a] = []
            adj[a].append(b)

    n = len(vertices)
    if n > 60 or len(edges_set) > 200:
        if status != "UNKNOWN":
            return False, "FAIL (C1): graph size bounds exceeded must be UNKNOWN"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if ref_code != "GRAPH_TOO_LARGE":
            return False, f"FAIL (C1): expected refusal_code 'GRAPH_TOO_LARGE', got '{ref_code}'"
        return True, "PASS (C1): graph size bounds exceeded refused"

    # Check graph connectedness
    start_v = next(iter(vertices))
    visited = set()
    q = deque([start_v])
    while q:
        curr = q.popleft()
        if curr in visited:
            continue
        visited.add(curr)
        for nbr in adj.get(curr, []):
            if nbr not in visited:
                q.append(nbr)

    if len(visited) != n:
        if status != "OUT_OF_SCOPE":
            return False, "FAIL (C1): disconnected graph must be OUT_OF_SCOPE"
        wit = answer.get("witness")
        if not isinstance(wit, Mapping) or wit.get("kind") != "graph_disconnected":
            return False, f"FAIL (C1): invalid disconnected_graph witness: {wit}"
        return True, "PASS (C1): valid disconnected graph witness"

    if status != "SOLVED":
        return False, f"FAIL (C1): unwarranted refusal on valid connected graph: {status}"

    sorted_nodes = sorted(list(vertices))
    dist = _c1_bfs_distance_matrix(sorted_nodes, adj)

    act_edges = answer.get("edges")
    if not isinstance(act_edges, list) or len(act_edges) != len(edges_set):
        return (
            False,
            f"FAIL (C1): edges count mismatch: expected {len(edges_set)}, got {len(act_edges) if isinstance(act_edges, list) else None}",
        )

    seen_edges = set()
    for idx, e_item in enumerate(act_edges):
        if not isinstance(e_item, Mapping):
            return False, f"FAIL (C1): edge item at {idx} must be a Mapping"
        e_pair = e_item.get("edge")
        if not (isinstance(e_pair, (list, tuple)) and len(e_pair) == 2):
            return False, f"FAIL (C1): malformed edge pair at {idx}"
        u, v = e_pair[0], e_pair[1]
        if not (_c1_is_int(u) and _c1_is_int(v)):
            return False, f"FAIL (C1): edge vertices at {idx} must be strict ints"
        e_norm = (min(u, v), max(u, v))
        if e_norm not in edges_set:
            return False, f"FAIL (C1): edge {e_norm} not in graph"
        if e_norm in seen_edges:
            return False, f"FAIL (C1): duplicate edge item {e_norm}"
        seen_edges.add(e_norm)

        # Verify potential schema and 1-Lipschitz condition in Checker 1
        potential = e_item.get("potential")
        if not isinstance(potential, Mapping):
            return False, f"FAIL (C1): edge {e_norm} potential must be a Mapping"
        phi: dict[int, Fraction] = {}
        for node in vertices:
            node_s = str(node)
            if node_s not in potential:
                return False, f"FAIL (C1): edge {e_norm} missing potential for node {node}"
            val_s = potential[node_s]
            if not _c1_is_reduced_rational_str(val_s):
                return (
                    False,
                    f"FAIL (C1): edge {e_norm} potential value not reduced rational: {val_s}",
                )
            phi[node] = Fraction(val_s)

        is_lip, lip_err = _c1_check_lipschitz_potential(phi, edges_set)
        if not is_lip:
            return False, f"FAIL (C1): edge {e_norm} {lip_err}"

        # Verify Forman curvature
        deg_u = len(adj[u])
        deg_v = len(adj[v])
        exp_forman = 4 - deg_u - deg_v
        act_forman = e_item.get("forman")
        if not _c1_is_int(act_forman):
            return (
                False,
                f"FAIL (C1): edge {e_norm} forman must be strict int, got {type(act_forman)}",
            )
        if act_forman != exp_forman:
            return (
                False,
                f"FAIL (C1): edge {e_norm} Forman mismatch: expected {exp_forman}, got {act_forman}",
            )

        # Calculate exact probability measures
        m_u: dict[int, Fraction] = {u: alpha}
        for z in adj[u]:
            m_u[z] = m_u.get(z, Fraction(0)) + Fraction(1 - alpha, deg_u)

        m_v: dict[int, Fraction] = {v: alpha}
        for z in adj[v]:
            m_v[z] = m_v.get(z, Fraction(0)) + Fraction(1 - alpha, deg_v)

        # Verify Transport Plan Marginals
        plan = e_item.get("plan")
        if not isinstance(plan, list):
            return False, f"FAIL (C1): edge {e_norm} plan must be a list"

        row_sums: dict[int, Fraction] = {}
        col_sums: dict[int, Fraction] = {}
        plan_cost = Fraction(0)

        for p_entry in plan:
            if not isinstance(p_entry, Mapping):
                return False, f"FAIL (C1): edge {e_norm} plan entry must be a Mapping"
            p_from = p_entry.get("from")
            if p_from is None:
                p_from = p_entry.get("source")
            p_to = p_entry.get("to")
            if p_to is None:
                p_to = p_entry.get("target")
            p_mass_s = p_entry.get("mass")

            if not (_c1_is_int(p_from) and _c1_is_int(p_to)):
                return False, "FAIL (C1): plan from/to must be ints"
            if p_from not in vertices or p_to not in vertices:
                return False, "FAIL (C1): plan contains vertex not in graph"
            if not _c1_is_reduced_rational_str(p_mass_s):
                return False, f"FAIL (C1): plan mass not reduced rational: {p_mass_s}"
            mass_f = Fraction(p_mass_s)
            if mass_f <= 0:
                return False, "FAIL (C1): plan mass must be positive"

            row_sums[p_from] = row_sums.get(p_from, Fraction(0)) + mass_f
            col_sums[p_to] = col_sums.get(p_to, Fraction(0)) + mass_f

            d_val = dist.get((p_from, p_to))
            if d_val is None:
                return False, f"FAIL (C1): unreachable pair ({p_from}, {p_to})"
            plan_cost += mass_f * d_val

        # Verify marginal source matches m_u
        all_sources = set(m_u.keys()) | set(row_sums.keys())
        for s_node in all_sources:
            if row_sums.get(s_node, Fraction(0)) != m_u.get(s_node, Fraction(0)):
                return (
                    False,
                    f"FAIL (C1): edge {e_norm} source marginal violation at {s_node}: plan={row_sums.get(s_node, 0)} != m_u={m_u.get(s_node, 0)}",
                )

        # Verify marginal target matches m_v
        all_targets = set(m_v.keys()) | set(col_sums.keys())
        for t_node in all_targets:
            if col_sums.get(t_node, Fraction(0)) != m_v.get(t_node, Fraction(0)):
                return (
                    False,
                    f"FAIL (C1): edge {e_norm} target marginal violation at {t_node}: plan={col_sums.get(t_node, 0)} != m_v={m_v.get(t_node, 0)}",
                )

        # Dual objective evaluation & zero duality gap check in Checker 1
        dual_obj = _c1_compute_dual_objective(phi, m_u, m_v, vertices)
        if dual_obj != plan_cost:
            return (
                False,
                f"FAIL (C1): edge {e_norm} duality gap non-zero: dual_obj={dual_obj} != plan_cost={plan_cost}",
            )

        # Verify Ollivier curvature matches 1 - plan_cost
        act_ollivier = e_item.get("ollivier")
        if not _c1_is_reduced_rational_str(act_ollivier):
            return False, f"FAIL (C1): edge {e_norm} ollivier not reduced rational: {act_ollivier}"
        exp_kappa = Fraction(1) - plan_cost
        if Fraction(act_ollivier) != exp_kappa:
            return (
                False,
                f"FAIL (C1): edge {e_norm} ollivier mismatch with plan: expected {_c1_to_reduced_str(exp_kappa)}, got {act_ollivier}",
            )

    return True, "PASS (C1): valid primal graph transport certificate"


# -------------------------------------------------------------------------
# Checker 1 Entry Point
# -------------------------------------------------------------------------


def verify_combinatorial_primal_certificate(
    case: Mapping[str, Any], answer: Mapping[str, Any]
) -> tuple[bool, str]:
    """Top-level verification entry point for Checker 1."""
    if not isinstance(case, Mapping) or not isinstance(answer, Mapping):
        return False, "FAIL (C1): case and answer must be Mappings"

    status = answer.get("status")
    if type(status) is not str or status not in {"SOLVED", "OUT_OF_SCOPE", "UNKNOWN"}:
        return False, f"FAIL (C1): invalid status '{status}'"

    # Schema checks & Case ID Parity
    c_id = case.get("case_id") or case.get("id")
    a_id = answer.get("id") or answer.get("case_id")
    if c_id != a_id:
        return False, f"FAIL (C1): case ID mismatch: case={c_id} vs answer={a_id}"

    if status == "UNKNOWN":
        allowed_keys = {"id", "case_id", "status", "refusal_code", "refusal"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C1): unexpected key '{k}' in UNKNOWN answer"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if not isinstance(ref_code, str):
            return False, "FAIL (C1): UNKNOWN answer missing refusal_code"
        return _c1_verify_refusal_warranted(case, ref_code)

    query = case.get("query")
    if query == "surface":
        return _c1_verify_surface_answer(case, answer)
    elif query == "graph":
        return _c1_verify_graph_answer(case, answer)
    else:
        return False, f"FAIL (C1): unknown query '{query}'"
