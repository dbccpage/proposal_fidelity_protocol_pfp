"""Independent Checker (Checker 2) for C018.

Self-contained (no reference-solver or checker-1 imports). It recomputes the
frustration index for |V| <= 20 by enumerating vertex 2-colourings as bit masks,
and it re-verifies UNKNOWN bounds: UNKNOWN is admissible only for |V| > 20, with
`upper` equal to the count of a locally optimal switching (no vertex has more
frustrated than satisfied incident edges) and `lower` certified by a maximal packing
of edge-disjoint negative closed walks. Counts must be canonical non-negative
integers; floats and booleans are rejected.
"""

from __future__ import annotations

from typing import Any

VERTEX_LIMIT = 20


def _count(value: Any) -> int | None:
    if type(value) is int:
        return value if value >= 0 else None
    if (
        type(value) is str
        and value.isascii()
        and value.isdigit()
        and (value == "0" or value[0] != "0")
    ):
        return int(value)
    return None


def _min_frustration(n: int, edges: list[tuple[int, int, int]]) -> int:
    """Minimum over masks of the number of edges (u, v, neg) with bit_u ^ bit_v ^ neg == 1."""
    best = len(edges)
    for mask in range(1 << max(n - 1, 0)):
        colouring = mask << 1  # vertex 0 is fixed to colour 0
        total = 0
        for u, v, neg in edges:
            total += ((colouring >> u) ^ (colouring >> v) ^ neg) & 1
            if total >= best:
                break
        else:
            best = total
            if best == 0:
                return 0
    return best


def _trail_packing(cycles: Any, sign_of: dict[frozenset[str], int]) -> set[frozenset[str]] | None:
    """Edge sets of pairwise edge-disjoint closed walks of odd negative parity."""
    if not isinstance(cycles, list):
        return None
    used: set[frozenset[str]] = set()
    for walk in cycles:
        if not isinstance(walk, list) or len(walk) < 3 or not all(type(x) is str for x in walk):
            return None
        closed = walk + [walk[0]]
        parity = 0
        mine: set[frozenset[str]] = set()
        for a, b in zip(closed, closed[1:]):
            key = frozenset((a, b))
            if len(key) != 2 or key not in sign_of or key in used:
                return None
            mine.add(key)
            parity ^= sign_of[key] == -1
        if parity != 1:
            return None
        used |= mine
    return used


def _residual_is_balanced(vertices: list[str], edges: list[tuple[str, str, int]]) -> bool:
    parent = {v: v for v in vertices}
    parity = {v: 0 for v in vertices}

    def find(x: str) -> tuple[str, int]:
        p = 0
        while parent[x] != x:
            p ^= parity[x]
            x = parent[x]
        return x, p

    for u, v, s in edges:
        ru, pu = find(u)
        rv, pv = find(v)
        want = 1 if s == -1 else 0
        if ru == rv:
            if pu ^ pv != want:
                return False
        else:
            parent[ru] = rv
            parity[ru] = pu ^ pv ^ want
    return True


def check_independent_frustration(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result is not a dict"

    status = result.get("status")
    vertices = [str(v) for v in case.get("vertices", [])]
    raw_edges = case.get("edges", [])
    if not isinstance(raw_edges, list) or any(
        not isinstance(e, list) or len(e) not in (2, 3) for e in raw_edges
    ):
        return False, "Independent checker: malformed case edges"
    triples = [(str(e[0]), str(e[1]), e[2] if len(e) == 3 else 1) for e in raw_edges]
    loops = [t for t in triples if t[0] == t[1]]
    bad_signs = [t for t in triples if type(t[2]) is not int or t[2] not in (1, -1)]

    if loops or bad_signs:
        if status != "OUT_OF_SCOPE":
            return False, "Independent checker expected OUT_OF_SCOPE"
        witness = result.get("witness") if isinstance(result.get("witness"), dict) else {}
        if witness.get("reason") == "SELF_LOOP" and loops:
            edge = witness.get("edge")
            if (
                isinstance(edge, list)
                and len(edge) == 2
                and edge[0] == edge[1]
                and any(t[0] == edge[0] for t in loops)
            ):
                return True, "Independent checker confirms SELF_LOOP"
            return False, "Independent checker: SELF_LOOP witness edge is not a loop of the case"
        if witness.get("reason") == "INVALID_SIGN" and bad_signs:
            return True, "Independent checker confirms INVALID_SIGN"
        return False, "Independent checker: OUT_OF_SCOPE witness names no defect of the case"

    if status not in ("SOLVED", "UNKNOWN"):
        return False, f"Unexpected status: {status}"

    position = {v: i for i, v in enumerate(vertices)}
    if any(u not in position or v not in position for u, v, _ in triples):
        return False, "Independent checker: edge cites unknown vertex"
    sign_of = {frozenset((u, v)): s for u, v, s in triples}

    raw_switching = result.get("switching", {})
    if not isinstance(raw_switching, dict) or any(k not in position for k in raw_switching):
        return False, "Independent checker: switching cites unknown vertices"
    flip = {}
    for v in vertices:
        value = raw_switching.get(v, "+1")
        if (type(value) is str and value == "-1") or (type(value) is int and value == -1):
            flip[v] = 1
        elif (type(value) is str and value == "+1") or (type(value) is int and value == 1):
            flip[v] = 0
        else:
            return False, f"Independent checker: invalid switching value {value!r}"
    neg_count = sum(1 for u, v, s in triples if (flip[u] ^ flip[v] ^ (s == -1)))

    if status == "SOLVED":
        l_val = _count(result.get("l"))
        if l_val is None:
            return False, f"Independent checker: l is not a canonical count: {result.get('l')!r}"
        if l_val != neg_count:
            return False, "Independent checker: switching count mismatch"
        if len(vertices) <= VERTEX_LIMIT:
            index_edges = [(position[u], position[v], 1 if s == -1 else 0) for u, v, s in triples]
            opt_l = _min_frustration(len(vertices), index_edges)
            if opt_l != l_val:
                return False, f"Independent exhaustive solve gave {opt_l} != {l_val}"
            return True, "Independent checker confirms SOLVED"
        lb = result.get("lower_bound")
        if not isinstance(lb, dict) or lb.get("kind") != "packing":
            return False, "Independent checker: |V| > 20 requires a packing certificate"
        used = _trail_packing(lb.get("cycles"), sign_of)
        if used is None or len(lb["cycles"]) != l_val:
            return False, "Independent checker: packing does not certify l"
        return True, "Independent checker confirms SOLVED via packing"

    if result.get("refusal") != "OPTIMALITY_UNCERTIFIED":
        return False, "Independent checker: UNKNOWN requires refusal OPTIMALITY_UNCERTIFIED"
    if len(vertices) <= VERTEX_LIMIT:
        return False, "Independent checker: UNKNOWN is inadmissible for |V| <= 20"
    upper = _count(result.get("upper"))
    lower = _count(result.get("lower"))
    if upper is None or lower is None:
        return False, "Independent checker: upper/lower are not canonical counts"
    if upper != neg_count:
        return False, "Independent checker: upper bound mismatch"
    frustrated: dict[str, int] = {v: 0 for v in vertices}
    satisfied: dict[str, int] = {v: 0 for v in vertices}
    for u, v, s in triples:
        tally = frustrated if (flip[u] ^ flip[v] ^ (s == -1)) else satisfied
        tally[u] += 1
        tally[v] += 1
    if any(frustrated[v] > satisfied[v] for v in vertices):
        return (
            False,
            "Independent checker: a single-vertex flip lowers the upper bound (switching not locally optimal)",
        )
    lb = result.get("lower_bound")
    if not isinstance(lb, dict) or lb.get("kind") != "packing":
        return False, "Independent checker: lower bound is not certified by a packing"
    used = _trail_packing(lb.get("cycles"), sign_of)
    if used is None or len(lb["cycles"]) != lower:
        return False, "Independent checker: packing does not certify lower"
    residual = [t for t in triples if frozenset((t[0], t[1])) not in used]
    if not _residual_is_balanced(vertices, residual):
        return False, "Independent checker: packing is not maximal"
    if lower >= upper:
        return False, "Independent checker: lower >= upper, SOLVED required"
    return True, "Independent checker confirms UNKNOWN bounds"
