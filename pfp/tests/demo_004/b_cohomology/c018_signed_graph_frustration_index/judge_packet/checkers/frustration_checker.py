"""Checker 1 for C018: exact verification of frustration-index certificates.

Self-contained (no reference-solver imports). Rules, from TASK.md:

- A self loop or an edge sign outside {+1, -1} makes the case OUT_OF_SCOPE; the
  witness reason must name a defect the case actually has.
- SOLVED: `l` equals the number of negative edges under the submitted switching,
  `deleted` is exactly that edge set, and the lower bound is certified either by
  exhaustive replay (|V| <= 20 only) or by `l` edge-disjoint negative closed walks.
- UNKNOWN (refusal OPTIMALITY_UNCERTIFIED) is admissible only for |V| > 20, since
  for |V| <= 20 exhaustive search always certifies the optimum. `upper` must equal
  the switching's negative-edge count, and the switching must be locally optimal
  (no single-vertex flip lowers the count); `lower` must be certified by a packing of
  exactly `lower` edge-disjoint negative closed walks that is maximal (the edges
  outside the packing form a balanced signed graph) and `lower < upper`.
- Counts are canonical non-negative integers (plain int or decimal string);
  floats and booleans are rejected.
"""

from __future__ import annotations

import re
from typing import Any

EXHAUSTIVE_VERTEX_LIMIT = 20
_NATURAL = re.compile(r"0|[1-9][0-9]*")


def _natural(value: Any) -> int | None:
    if type(value) is int and value >= 0:
        return value
    if type(value) is str and _NATURAL.fullmatch(value):
        return int(value)
    return None


def _sign(value: Any) -> int | None:
    if type(value) is int and value in (1, -1):
        return value
    if value == "+1" and type(value) is str:
        return 1
    if value == "-1" and type(value) is str:
        return -1
    return None


def _case_graph(case: dict[str, Any]) -> tuple[list[str], list[tuple[str, str, Any]]]:
    vertices = [str(v) for v in case.get("vertices", [])]
    edges = []
    for e in case.get("edges", []):
        if not isinstance(e, list) or len(e) not in (2, 3):
            raise ValueError(f"malformed edge {e!r}")
        edges.append((str(e[0]), str(e[1]), e[2] if len(e) == 3 else 1))
    return vertices, edges


def _balanced(vertices: list[str], edges: list[tuple[str, str, int]]) -> bool:
    adj: dict[str, list[tuple[str, int]]] = {v: [] for v in vertices}
    for u, v, s in edges:
        adj.setdefault(u, []).append((v, s))
        adj.setdefault(v, []).append((u, s))
    colour: dict[str, int] = {}
    for root in adj:
        if root in colour:
            continue
        colour[root] = 1
        stack = [root]
        while stack:
            u = stack.pop()
            for w, s in adj[u]:
                want = colour[u] * s
                if w not in colour:
                    colour[w] = want
                    stack.append(w)
                elif colour[w] != want:
                    return False
    return True


def _exhaustive_optimum(vertices: list[str], edges: list[tuple[str, str, int]]) -> int:
    """Minimum negative-edge count over all switchings (Gray-code enumeration)."""
    if not vertices:
        return 0
    index = {v: i for i, v in enumerate(vertices)}
    adj: list[list[tuple[int, int]]] = [[] for _ in vertices]
    for u, v, s in edges:
        adj[index[u]].append((index[v], s))
        adj[index[v]].append((index[u], s))
    signs = [1] * len(vertices)
    count = sum(1 for _, _, s in edges if s == -1)
    best = count
    free = len(vertices) - 1
    for step in range(1, 1 << free):
        bit = (step & -step).bit_length() - 1
        x = bit + 1
        delta = sum(signs[x] * s * signs[w] for w, s in adj[x])
        signs[x] = -signs[x]
        count += delta
        if count < best:
            best = count
            if best == 0:
                break
    return best


def _verify_packing(
    cycles: Any,
    edge_sign: dict[tuple[str, str], int],
) -> tuple[bool, str, set[tuple[str, str]]]:
    """Closed walks that pairwise share no edge, each traversing negative edges an odd
    number of times (with multiplicity). The edges of odd multiplicity in such a walk
    form an even subgraph with an odd number of negative edges, hence contain a negative
    cycle; disjoint walks therefore certify that many edge-disjoint negative cycles."""
    if not isinstance(cycles, list):
        return False, "packing cycles must be a list", set()
    used: set[tuple[str, str]] = set()
    for c_nodes in cycles:
        if (
            not isinstance(c_nodes, list)
            or len(c_nodes) < 3
            or any(type(x) is not str for x in c_nodes)
        ):
            return False, f"cycle {c_nodes!r} must list at least 3 vertex strings", used
        negatives = 0
        walk_edges: set[tuple[str, str]] = set()
        for i, u in enumerate(c_nodes):
            v = c_nodes[(i + 1) % len(c_nodes)]
            key = (u, v) if u < v else (v, u)
            if key not in edge_sign:
                return False, f"edge {key} in cycle does not exist in graph", used
            if key in used:
                return False, f"packing cycles are not edge-disjoint: edge {key} shared", used
            walk_edges.add(key)
            negatives += edge_sign[key] == -1
        if negatives % 2 == 0:
            return (
                False,
                f"cycle {c_nodes} traverses negative edges an even number ({negatives}) of times",
                used,
            )
        used |= walk_edges
    return True, "packing verified", used


def check_frustration_certificate(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result is not a dict"
    try:
        vertices, raw_edges = _case_graph(case)
    except (TypeError, ValueError) as exc:
        return False, f"Case is malformed: {exc}"

    status = result.get("status")
    self_loops = {(u, v) for u, v, _ in raw_edges if u == v}
    invalid_signs = [(u, v, s) for u, v, s in raw_edges if not (type(s) is int and s in (1, -1))]

    if self_loops or invalid_signs:
        if status != "OUT_OF_SCOPE":
            return False, "Case has a self loop or an invalid sign; OUT_OF_SCOPE expected"
        witness = result.get("witness")
        if not isinstance(witness, dict):
            return False, "OUT_OF_SCOPE witness must be an object"
        reason = witness.get("reason")
        if reason == "SELF_LOOP" and self_loops:
            edge = witness.get("edge")
            if not (isinstance(edge, list) and len(edge) == 2 and tuple(edge) in self_loops):
                return False, f"SELF_LOOP witness edge {edge!r} is not a self loop of the case"
            return True, "Valid OUT_OF_SCOPE verified for self loop"
        if reason == "INVALID_SIGN" and invalid_signs:
            return True, "Valid OUT_OF_SCOPE verified for invalid sign"
        return False, f"OUT_OF_SCOPE reason {reason!r} names no defect of this case"

    if status not in ("SOLVED", "UNKNOWN"):
        return False, f"Unexpected status: {status}"

    edges = [((u, v) if u < v else (v, u)) + (s,) for u, v, s in raw_edges]
    edge_sign = {(u, v): s for u, v, s in edges}
    vertex_set = set(vertices)
    if any(u not in vertex_set or v not in vertex_set for u, v, _ in edges):
        return False, "Case edge cites an unknown vertex"

    raw_switching = result.get("switching", {})
    if not isinstance(raw_switching, dict) or set(raw_switching) - vertex_set:
        return False, "switching must map known vertices to +1/-1"
    switching: dict[str, int] = {}
    for v in vertices:
        sign = _sign(raw_switching.get(v, "+1"))
        if sign is None:
            return False, f"switching value for {v!r} is not +1/-1: {raw_switching.get(v)!r}"
        switching[v] = sign
    negative = {(u, v) for u, v, s in edges if switching[u] * s * switching[v] == -1}
    neg_count = sum(1 for u, v, s in edges if switching[u] * s * switching[v] == -1)

    if status == "SOLVED":
        l_claimed = _natural(result.get("l"))
        if l_claimed is None:
            return False, f"l must be a canonical non-negative integer, got {result.get('l')!r}"
        if l_claimed != neg_count:
            return (
                False,
                f"Claimed l={l_claimed} does not match switched negative count {neg_count}",
            )
        claimed_deleted = result.get("deleted", [])
        if not isinstance(claimed_deleted, list) or any(
            not (isinstance(e, list) and len(e) == 2 and all(type(x) is str for x in e))
            for e in claimed_deleted
        ):
            return False, "deleted must be a list of [u, v] vertex-string pairs"
        claimed_set = {(e[0], e[1]) if e[0] < e[1] else (e[1], e[0]) for e in claimed_deleted}
        if claimed_set != negative or len(claimed_deleted) != len(claimed_set):
            return (
                False,
                f"Deleted edges mismatch: claimed {sorted(claimed_set)} != actual {sorted(negative)}",
            )

        lb = result.get("lower_bound")
        kind = lb.get("kind") if isinstance(lb, dict) else None
        if kind == "exhaustive":
            if len(vertices) > EXHAUSTIVE_VERTEX_LIMIT:
                return (
                    False,
                    f"Exhaustive certificate invalid for |V| = {len(vertices)} > {EXHAUSTIVE_VERTEX_LIMIT}",
                )
            opt_l = _exhaustive_optimum(vertices, edges)
            if opt_l != l_claimed:
                return False, f"Exhaustive replay gave {opt_l} != claimed {l_claimed}"
            return True, "SOLVED certificate verified via exhaustive search"
        if kind == "packing":
            cycles = lb.get("cycles")
            if not isinstance(cycles, list) or len(cycles) != l_claimed:
                return False, f"Packing cycle count must equal claimed l {l_claimed}"
            ok, msg, _ = _verify_packing(cycles, edge_sign)
            if not ok:
                return False, msg
            return True, "SOLVED certificate verified via negative cycle packing"
        return False, f"Unknown lower bound kind: {kind!r}"

    # UNKNOWN
    if result.get("refusal") != "OPTIMALITY_UNCERTIFIED":
        return False, f"Expected refusal OPTIMALITY_UNCERTIFIED, got {result.get('refusal')!r}"
    if len(vertices) <= EXHAUSTIVE_VERTEX_LIMIT:
        return False, (
            f"UNKNOWN is not admissible for |V| = {len(vertices)} <= {EXHAUSTIVE_VERTEX_LIMIT}: "
            "exhaustive search certifies the optimum"
        )
    upper = _natural(result.get("upper"))
    lower = _natural(result.get("lower"))
    if upper is None or lower is None:
        return False, "upper and lower must be canonical non-negative integers"
    if upper != neg_count:
        return False, f"Claimed upper {upper} does not match switching count {neg_count}"
    # Local optimality: flipping v changes the count by (#positive - #negative) of
    # its incident edges under the switching, so no single flip may help. Summed over
    # vertices this also gives upper <= |E| / 2.
    incident_balance = {v: 0 for v in vertices}
    for u, v, s in edges:
        switched = switching[u] * s * switching[v]
        incident_balance[u] += switched
        incident_balance[v] += switched
    improvable = sorted(v for v, balance in incident_balance.items() if balance < 0)
    if improvable:
        return (
            False,
            f"switching is not locally optimal: flipping {improvable[0]!r} lowers the upper bound",
        )
    lb = result.get("lower_bound")
    if not isinstance(lb, dict) or lb.get("kind") != "packing":
        return False, "UNKNOWN requires a packing lower_bound certificate for `lower`"
    cycles = lb.get("cycles")
    if not isinstance(cycles, list) or len(cycles) != lower:
        return False, f"Packing cycle count must equal claimed lower {lower}"
    ok, msg, used = _verify_packing(cycles, edge_sign)
    if not ok:
        return False, msg
    if not _balanced(vertices, [e for e in edges if (e[0], e[1]) not in used]):
        return False, "Packing is not maximal: the edges outside it still contain a negative cycle"
    if lower >= upper:
        return (
            False,
            f"lower {lower} >= upper {upper}: the optimum is certified, so SOLVED is required",
        )
    return True, "UNKNOWN with certified bounds verified"
