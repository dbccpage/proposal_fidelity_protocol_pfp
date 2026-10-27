"""Independent Second Checker for C024 (Local Clifford Graph State Equivalence).

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import deque
from typing import Any

import numpy as np

from ...reference_solver.graph import validate_simple_graph
from .schema_guard import validate_certificate


def independent_rank_f2(submat: np.ndarray) -> int:
    """Computes row-rank over F_2 using independent matrix echelonization."""
    A = submat.copy() % 2
    nrows, ncols = A.shape
    r = 0
    c = 0
    while r < nrows and c < ncols:
        pivot_rows = np.where(A[r:, c] == 1)[0]
        if len(pivot_rows) == 0:
            c += 1
            continue
        p = r + pivot_rows[0]
        if p != r:
            A[[r, p]] = A[[p, r]]
        for i in range(r + 1, nrows):
            if A[i, c] == 1:
                A[i] = (A[i] ^ A[r]) % 2
        r += 1
        c += 1
    return r


def _adjacency_state(num_vertices: int, edges: list[list[int]]) -> tuple[int, ...]:
    state = [0] * (num_vertices * num_vertices)
    for u, v in edges:
        state[u * num_vertices + v] = 1
        state[v * num_vertices + u] = 1
    return tuple(state)


def _local_complement_state(
    state: tuple[int, ...], num_vertices: int, vertex: int
) -> tuple[int, ...]:
    updated = list(state)
    neighbors = [u for u in range(num_vertices) if state[vertex * num_vertices + u] == 1]
    for i, u in enumerate(neighbors):
        for w in neighbors[i + 1 :]:
            uw = u * num_vertices + w
            wu = w * num_vertices + u
            updated[uw] ^= 1
            updated[wu] ^= 1
    return tuple(updated)


def _independently_exhaust_orbit(
    start: tuple[int, ...],
    target: tuple[int, ...],
    num_vertices: int,
    *,
    max_states: int = 25000,
) -> tuple[bool, bool, int]:
    """Return (contains_target, fully_exhausted, state_count)."""
    queue: deque[tuple[int, ...]] = deque([start])
    seen = {start}
    while queue:
        current = queue.popleft()
        for vertex in range(num_vertices):
            if not any(current[vertex * num_vertices + u] for u in range(num_vertices)):
                continue
            nxt = _local_complement_state(current, num_vertices, vertex)
            if nxt == target:
                return True, False, len(seen)
            if nxt not in seen:
                seen.add(nxt)
                if len(seen) > max_states:
                    return False, False, len(seen)
                queue.append(nxt)
    return False, True, len(seen)


def independent_check_certificate(case: dict[str, Any], cert: dict[str, Any]) -> dict[str, Any]:
    """Independent second checker for C024 certificates."""
    schema_error = validate_certificate(case, cert)
    if schema_error:
        return {"verdict": "FAIL", "reason": schema_error}
    status = cert.get("status")

    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return {"verdict": "FAIL", "reason": f"Invalid status: {status}"}

    num_v = case.get("num_vertices")
    if not isinstance(num_v, int) or num_v < 2 or num_v > 16:
        if (
            status == "UNKNOWN"
            and cert.get("refusal_code") == "NUM_VERTICES_OUT_OF_BOUNDS"
            and "equivalent" not in cert
        ):
            return {
                "verdict": "PASS",
                "details": "Out of bounds num_vertices confirmed by second checker",
            }
        return {"verdict": "FAIL", "reason": "Expected UNKNOWN for num_vertices out of bounds"}

    edges_g = case.get("g")
    edges_gp = case.get("g_prime")
    vg, _ = validate_simple_graph(num_v, edges_g)
    vgp, _ = validate_simple_graph(num_v, edges_gp)

    if not vg or not vgp:
        if status == "OUT_OF_SCOPE":
            return {"verdict": "PASS", "details": "Defect confirmed by second checker"}
        return {"verdict": "FAIL", "reason": "Expected OUT_OF_SCOPE for invalid graph structure"}

    if status == "OUT_OF_SCOPE":
        return {
            "verdict": "FAIL",
            "reason": "Second checker found both graphs to be valid simple graphs",
        }

    if status == "UNKNOWN":
        witness = cert.get("witness")
        if cert.get("refusal_code") != "ORBIT_SEARCH_BUDGET_EXHAUSTED":
            return {"verdict": "FAIL", "reason": "Unexpected UNKNOWN refusal code for valid graphs"}
        if "equivalent" in cert:
            return {"verdict": "FAIL", "reason": "UNKNOWN must not assert an equivalence decision"}
        if not isinstance(witness, dict) or witness.get("kind") != "orbit_search_budget_exhausted":
            return {"verdict": "FAIL", "reason": "Missing typed orbit budget witness"}
        states_visited = witness.get("states_visited")
        max_states = witness.get("max_orbit_states")
        if not isinstance(max_states, int) or max_states <= 0 or states_visited != max_states:
            return {"verdict": "FAIL", "reason": "Malformed orbit budget counters"}
        return {"verdict": "PASS", "details": "Typed orbit-search budget exhaustion verified"}

    equiv = cert.get("equivalent")
    if equiv is True:
        seq = cert.get("sequence")
        if not isinstance(seq, list):
            return {"verdict": "FAIL", "reason": "Sequence must be a list for equivalent=True"}

        # Independent simulation via numpy adjacency matrix
        adj = np.zeros((num_v, num_v), dtype=int)
        for u, v in edges_g:
            adj[u, v] = 1
            adj[v, u] = 1

        for idx, v in enumerate(seq):
            if not isinstance(v, int) or v < 0 or v >= num_v:
                return {
                    "verdict": "FAIL",
                    "reason": f"Invalid vertex index in sequence at step {idx}: {v}",
                }
            nbrs = np.where(adj[v] == 1)[0]
            # Complement induced subgraph on N(v)
            for i in range(len(nbrs)):
                u = nbrs[i]
                for j in range(i + 1, len(nbrs)):
                    w = nbrs[j]
                    adj[u, w] ^= 1
                    adj[w, u] ^= 1

        # Build target adjacency matrix
        target_adj = np.zeros((num_v, num_v), dtype=int)
        for u, v in edges_gp:
            target_adj[u, v] = 1
            target_adj[v, u] = 1

        if not np.array_equal(adj, target_adj):
            return {
                "verdict": "FAIL",
                "reason": "Independent simulation: final graph does not match G'",
            }

        return {"verdict": "PASS", "details": "Independent simulation verified sequence to G'"}

    elif equiv is False:
        witness = cert.get("witness")
        if not isinstance(witness, dict):
            return {"verdict": "FAIL", "reason": "Witness must be a dict for equivalent=False"}

        kind = witness.get("kind")
        if kind == "cut_rank":
            subset = witness.get("subset")
            if not isinstance(subset, list) or not subset:
                return {"verdict": "FAIL", "reason": "Subset must be non-empty list"}

            for u in subset:
                if not isinstance(u, int) or u < 0 or u >= num_v:
                    return {
                        "verdict": "FAIL",
                        "reason": f"Invalid or out-of-bounds vertex in subset: {u}",
                    }

            set_a = set(subset)
            set_b = [v for v in range(num_v) if v not in set_a]
            if not set_b:
                return {"verdict": "FAIL", "reason": "Subset cannot be full vertex set"}

            adj_g = np.zeros((num_v, num_v), dtype=int)
            for u, v in edges_g:
                adj_g[u, v] = 1
                adj_g[v, u] = 1

            adj_gp = np.zeros((num_v, num_v), dtype=int)
            for u, v in edges_gp:
                adj_gp[u, v] = 1
                adj_gp[v, u] = 1

            submat_g = adj_g[np.ix_(sorted(set_a), set_b)]
            submat_gp = adj_gp[np.ix_(sorted(set_a), set_b)]

            rg = independent_rank_f2(submat_g)
            rgp = independent_rank_f2(submat_gp)

            if rg == rgp:
                return {
                    "verdict": "FAIL",
                    "reason": f"Cut-ranks equal ({rg}) on subset in second checker",
                }

            if witness.get("rank_g") != rg or witness.get("rank_g_prime") != rgp:
                return {
                    "verdict": "FAIL",
                    "reason": "Reported ranks do not match independently computed ranks",
                }

            return {
                "verdict": "PASS",
                "details": "Independent checker verified cut-rank separation",
            }
        elif kind == "orbit_exhaustion":
            exhausted_side = witness.get("exhausted_side")
            reported_states = witness.get("orbit_states")
            if exhausted_side not in ("g", "g_prime") or not isinstance(reported_states, int):
                return {"verdict": "FAIL", "reason": "Malformed orbit exhaustion witness"}
            g_state = _adjacency_state(num_v, edges_g)
            gp_state = _adjacency_state(num_v, edges_gp)
            start, target = (g_state, gp_state) if exhausted_side == "g" else (gp_state, g_state)
            contains_target, fully_exhausted, observed_states = _independently_exhaust_orbit(
                start, target, num_v
            )
            if contains_target:
                return {
                    "verdict": "FAIL",
                    "reason": "Independent orbit replay found the target graph",
                }
            if not fully_exhausted:
                return {
                    "verdict": "FAIL",
                    "reason": "Independent orbit replay did not exhaust within the bound",
                }
            if observed_states != reported_states:
                return {
                    "verdict": "FAIL",
                    "reason": "Reported orbit size does not match independent replay",
                }
            return {"verdict": "PASS", "details": "Independent checker confirmed orbit exhaustion"}
        else:
            return {"verdict": "FAIL", "reason": f"Unknown witness kind: {kind}"}

    return {"verdict": "FAIL", "reason": f"Invalid equivalent boolean: {equiv}"}


__all__ = [
    "independent_check_certificate",
    "independent_rank_f2",
]
