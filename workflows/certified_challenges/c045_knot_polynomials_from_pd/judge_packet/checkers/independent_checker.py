# AuthorityEffect: None.
"""
Independent Checker for C045.

Recomputes everything it checks from the PD code, without the reference solver:

1. PD validity: crossing tuples, edge labels 1..2n each used twice, under-strand
   succession k = i + 1 (mod 2n), over-strand adjacency, and planarity by counting
   the faces of the rotation system (F = n + 2). A refusal passes only when the input
   has a problem of the claimed kind.
2. Writhe from the over-strand direction of each crossing.
3. Kauffman bracket by the state sum (A-smoothing X[a,b,c,d] -> (a,b)(c,d), B-smoothing
   -> (a,d)(b,c), loop value -A^2 - A^-2), and the Jones polynomial
   V(t) = (-A^3)^(-w) <K> at A = t^(-1/4).
4. Alexander polynomial from the abelianized Wirtinger (Fox) matrix, a fraction-free
   Bareiss determinant over Z[t], normalized to be symmetric with Delta(1) = 1.
5. Knot identification from its own table of Alexander polynomials (Rolfsen table,
   knots up to 7_1), and amphichirality from the symmetry of the Jones polynomial.

An empty object, an unknown status or a refusal on a valid diagram never passes.
"""

from __future__ import annotations

import re
from itertools import product
from typing import Any

MAX_CROSSINGS = 12  # TASK.md: INVALID_CROSSING_COUNT when n > 12

_INT_KEY = re.compile(r"^-?\d+$")

REFUSAL_REASONS = frozenset(
    {
        "INVALID_CROSSING_COUNT",
        "MALFORMED_CROSSING_TUPLE",
        "EDGE_LABEL_MULTIPLICITY",
        "NON_PLANAR",
        "ORIENTATION_INCONSISTENT",
        "TWO_COMPONENTS",
    }
)

# Normalized Alexander polynomials (symmetric, Delta(1) = 1) of the catalog knots.
_ALEXANDER_TABLE: dict[str, dict[int, int]] = {
    "0_1": {0: 1},
    "3_1": {-1: 1, 0: -1, 1: 1},
    "4_1": {-1: -1, 0: 3, 1: -1},
    "5_1": {-2: 1, -1: -1, 0: 1, 1: -1, 2: 1},
    "5_2": {-1: 2, 0: -3, 1: 2},
    "6_1": {-1: -2, 0: 5, 1: -2},
    "6_2": {-2: -1, -1: 3, 0: -3, 1: 3, 2: -1},
    "6_3": {-2: 1, -1: -3, 0: 5, 1: -3, 2: 1},
    "7_1": {-3: 1, -2: -1, -1: 1, 0: -1, 1: 1, 2: -1, 3: 1},
}
_AMPHICHIRAL = frozenset({"0_1", "4_1", "6_3"})

Laurent = dict[int, int]


def _clean(poly: Laurent) -> Laurent:
    return {k: v for k, v in poly.items() if v != 0}


def _add_into(acc: Laurent, poly: Laurent, scale: int = 1, shift: int = 0) -> None:
    for k, v in poly.items():
        acc[k + shift] = acc.get(k + shift, 0) + scale * v


def _mul(p: Laurent, q: Laurent) -> Laurent:
    out: Laurent = {}
    for a, x in p.items():
        for b, y in q.items():
            out[a + b] = out.get(a + b, 0) + x * y
    return _clean(out)


def _parse_laurent(obj: Any) -> Laurent | None:
    """Parses {"power": coeff} with integer-string keys and exact int coefficients."""
    if not isinstance(obj, dict) or not obj:
        return None
    out: Laurent = {}
    for k, v in obj.items():
        if not isinstance(k, str) or not _INT_KEY.match(k):
            return None
        if type(v) is not int:
            return None
        out[int(k)] = out.get(int(k), 0) + v
    return _clean(out)


# --------------------------------------------------------------------------- PD checks


def _pd_problems(pd: Any) -> set[str]:
    """All problems of the diagram (empty set for a valid knot diagram or the unknot [])."""
    if not isinstance(pd, list):
        return {"MALFORMED_CROSSING_TUPLE"}
    n = len(pd)
    if n == 0:
        return set()
    problems: set[str] = set()
    if n > MAX_CROSSINGS:
        problems.add("INVALID_CROSSING_COUNT")
    for c in pd:
        if not isinstance(c, list) or len(c) != 4 or any(type(e) is not int for e in c):
            problems.add("MALFORMED_CROSSING_TUPLE")
            return problems
    labels = [e for c in pd for e in c]
    n2 = 2 * n
    if sorted(labels) != sorted(list(range(1, n2 + 1)) * 2):
        problems.add("EDGE_LABEL_MULTIPLICITY")
        return problems
    for i, j, k, m in pd:
        if k != i % n2 + 1:
            problems.add("ORIENTATION_INCONSISTENT")
        elif j != m % n2 + 1 and m != j % n2 + 1:
            problems.add("ORIENTATION_INCONSISTENT")
    if _face_count(pd) != n + 2:
        problems.add("NON_PLANAR")
    return problems


def _face_count(pd: list[list[int]]) -> int:
    """Faces of the rotation system, traced turning clockwise (dart -> partner -> previous slot)."""
    where: dict[int, list[tuple[int, int]]] = {}
    for c_idx, cross in enumerate(pd):
        for pos, e in enumerate(cross):
            where.setdefault(e, []).append((c_idx, pos))
    partner = {}
    for darts in where.values():
        a, b = darts
        partner[a], partner[b] = b, a
    seen: set[tuple[int, int]] = set()
    faces = 0
    for start in partner:
        if start in seen:
            continue
        faces += 1
        d = start
        while d not in seen:
            seen.add(d)
            c, p = partner[d]
            d = (c, (p - 1) % 4)
    return faces


def _signs(pd: list[list[int]]) -> list[int]:
    n2 = 2 * len(pd)
    return [1 if j == m % n2 + 1 else -1 for _i, j, _k, m in pd]


# --------------------------------------------------------------------------- invariants


def _bracket(pd: list[list[int]]) -> Laurent:
    """Kauffman bracket <K> in A, normalized so that the unknot has bracket 1."""
    if not pd:
        return {0: 1}
    loop = {2: -1, -2: -1}  # d = -A^2 - A^-2
    total: Laurent = {}
    labels = sorted({e for c in pd for e in c})
    for state in product((0, 1), repeat=len(pd)):
        parent = {e: e for e in labels}

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            parent[find(x)] = find(y)

        exponent = 0
        for (a, b, c, d), s in zip(pd, state):
            if s == 0:
                # A-smoothing: with slots i, j, k, l counterclockwise, turning the over-strand
                # counterclockwise sweeps the regions (j,k) and (l,i); joining them leaves the
                # arcs i-j and k-l.
                union(a, b)
                union(c, d)
                exponent += 1
            else:
                union(a, d)
                union(b, c)
                exponent -= 1
        loops = len({find(e) for e in labels})
        term: Laurent = {exponent: 1}
        for _ in range(loops - 1):
            term = _mul(term, loop)
        _add_into(total, term)
    return _clean(total)


def _jones_from_bracket(bracket: Laurent, writhe: int) -> Laurent | None:
    """V(t) = (-A^3)^(-w) <K> with A = t^(-1/4); None if a power is not integral in t."""
    sign = -1 if writhe % 2 else 1
    out: Laurent = {}
    for e, c in bracket.items():
        a_power = e - 3 * writhe
        if a_power % 4:
            return None
        t_power = -a_power // 4
        out[t_power] = out.get(t_power, 0) + sign * c
    return _clean(out)


def _poly_mul_z(p: list[int], q: list[int]) -> list[int]:
    if not p or not q:
        return []
    out = [0] * (len(p) + len(q) - 1)
    for i, x in enumerate(p):
        if x:
            for j, y in enumerate(q):
                out[i + j] += x * y
    return _trim(out)


def _poly_sub_z(p: list[int], q: list[int]) -> list[int]:
    out = [0] * max(len(p), len(q))
    for i, x in enumerate(p):
        out[i] += x
    for i, y in enumerate(q):
        out[i] -= y
    return _trim(out)


def _trim(p: list[int]) -> list[int]:
    while p and p[-1] == 0:
        p = p[:-1]
    return p


def _poly_divexact_z(p: list[int], q: list[int]) -> list[int]:
    """Exact division in Z[t] (Bareiss guarantees exactness)."""
    p = list(p)
    q = _trim(q)
    if not q:
        raise ZeroDivisionError("division by zero polynomial")
    if not p:
        return []
    out = [0] * (len(p) - len(q) + 1)
    for i in range(len(out) - 1, -1, -1):
        coeff, rem = divmod(p[i + len(q) - 1], q[-1])
        if rem:
            raise ArithmeticError("inexact polynomial division")
        out[i] = coeff
        for j, y in enumerate(q):
            p[i + j] -= coeff * y
    if any(p):
        raise ArithmeticError("inexact polynomial division")
    return _trim(out)


def _det_z(matrix: list[list[list[int]]]) -> list[int]:
    """Fraction-free Bareiss determinant over Z[t]."""
    m = [row[:] for row in matrix]
    n = len(m)
    if n == 0:
        return [1]
    sign = 1
    prev: list[int] = [1]
    for k in range(n - 1):
        if not m[k][k]:
            swap = next((r for r in range(k + 1, n) if m[r][k]), None)
            if swap is None:
                return []
            m[k], m[swap] = m[swap], m[k]
            sign = -sign
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                num = _poly_sub_z(_poly_mul_z(m[i][j], m[k][k]), _poly_mul_z(m[i][k], m[k][j]))
                m[i][j] = _poly_divexact_z(num, prev)
            m[i][k] = []
        prev = m[k][k]
    det = m[n - 1][n - 1]
    return [sign * c for c in det]


def _alexander(pd: list[list[int]]) -> Laurent:
    """Normalized Alexander polynomial from the abelianized Wirtinger presentation."""
    n = len(pd)
    if n == 0:
        return {0: 1}
    labels = sorted({e for c in pd for e in c})
    parent = {e: e for e in labels}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for _i, j, _k, m in pd:
        parent[find(j)] = find(m)
    arcs = sorted({find(e) for e in labels})
    arc_index = {a: idx for idx, a in enumerate(arcs)}
    if len(arcs) != n:
        raise ValueError("arc count differs from crossing count")
    rows: list[list[list[int]]] = []
    for (i, j, k, _l), s in zip(pd, _signs(pd)):
        row: list[list[int]] = [[] for _ in range(n)]
        over, inc, out = arc_index[find(j)], arc_index[find(i)], arc_index[find(k)]
        if s > 0:
            entries = ((over, [1, -1]), (inc, [0, 1]), (out, [-1]))
        else:
            entries = ((over, [-1, 1]), (inc, [1]), (out, [0, -1]))
        for col, poly in entries:
            row[col] = _trim([a + b for a, b in _zip_longest(row[col], poly)])
        rows.append(row)
    minor = [r[1:] for r in rows[1:]]
    det = _det_z(minor)
    if not det:
        return {}
    return _normalize_alexander({p: c for p, c in enumerate(det) if c})


def _zip_longest(p: list[int], q: list[int]) -> list[tuple[int, int]]:
    size = max(len(p), len(q))
    return [(p[i] if i < len(p) else 0, q[i] if i < len(q) else 0) for i in range(size)]


def _normalize_alexander(poly: Laurent) -> Laurent:
    lo, hi = min(poly), max(poly)
    if (lo + hi) % 2:
        return {}
    shift = (lo + hi) // 2
    out = {p - shift: c for p, c in poly.items()}
    if sum(out.values()) < 0:
        out = {p: -c for p, c in out.items()}
    return out


def _invariants(pd: list[list[int]]) -> dict[str, Any]:
    writhe = sum(_signs(pd)) if pd else 0
    bracket = _bracket(pd)
    jones = _jones_from_bracket(bracket, writhe)
    return {
        "writhe": writhe,
        "kauffman_bracket": bracket,
        "jones_polynomial": jones,
        "alexander_polynomial": _alexander(pd),
    }


def _identify(alexander: Laurent) -> str | None:
    for name, poly in _ALEXANDER_TABLE.items():
        if poly == alexander:
            return name
    return None


# --------------------------------------------------------------------------- checker


def _check_refusal(case: dict[str, Any], ans: dict[str, Any], task: str) -> tuple[bool, str]:
    reason = ans.get("reason")
    if not isinstance(reason, str) or not reason:
        return False, "Refusal lacks a reason"
    if not isinstance(ans.get("witness"), dict):
        return False, "Refusal lacks a witness object"
    if task in ("COMPUTE_POLYNOMIALS", "IDENTIFY"):
        if "pd" not in case:
            return (reason == "MALFORMED_INPUT"), f"Refusal of a case without pd: {reason}"
        problems = _pd_problems(case["pd"])
        if not problems:
            return False, f"Refusal {reason} on a valid diagram"
        if reason not in problems:
            return (
                False,
                f"Refusal reason {reason} not among independently found problems {sorted(problems)}",
            )
        return True, f"Independent audit confirmed refusal: {reason}"
    if task == "COMPARE":
        if "pd_1" not in case or "pd_2" not in case:
            return (reason == "MALFORMED_INPUT"), f"Refusal of a case without pd_1/pd_2: {reason}"
        for tag in ("1", "2"):
            prefix = f"PD_{tag}_"
            if reason.startswith(prefix):
                problems = _pd_problems(case[f"pd_{tag}"])
                if reason[len(prefix) :] in problems:
                    return True, f"Independent audit confirmed refusal: {reason}"
                return (
                    False,
                    f"Refusal {reason} not supported: pd_{tag} problems {sorted(problems)}",
                )
        return False, f"Refusal reason {reason} does not name pd_1 or pd_2"
    return True, f"Refusal of unknown task {task!r}"


def check_independent(case: dict[str, Any], ans: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(ans, dict):
        return False, "Answer must be a dictionary"
    if not isinstance(case, dict):
        return False, "Case must be a dictionary"
    if ans.get("case_id") != case.get("case_id"):
        return (
            False,
            f"case_id mismatch: expected {case.get('case_id')!r}, got {ans.get('case_id')!r}",
        )

    trace = ans.get("ddc_trace")
    if trace:
        steps = trace.get("steps", []) if isinstance(trace, dict) else None
        if not isinstance(steps, list):
            return False, "Malformed DDC trace"
        valid_ops = {"E", "R", "C", "I", "Lambda", "D", "M", "T"}
        for s in steps:
            if not isinstance(s, dict) or s.get("op") not in valid_ops:
                return False, f"Invalid DDC operation in trace: {s!r}"

    status = ans.get("status")
    task = case.get("task", "COMPUTE_POLYNOMIALS")
    if status == "REFUSED":
        return _check_refusal(case, ans, task)
    if status != "SOLVED":
        return False, f"Invalid status: {status!r}"

    try:
        if task in ("COMPUTE_POLYNOMIALS", "IDENTIFY"):
            pd = case.get("pd")
            problems = _pd_problems(pd)
            if problems:
                return False, f"SOLVED on an invalid diagram {sorted(problems)}"
            inv = _invariants(pd)
            knot = _identify(inv["alexander_polynomial"])
            if task == "COMPUTE_POLYNOMIALS":
                return _check_compute(ans, inv, knot)
            return _check_identify(ans, inv, knot)
        if task == "COMPARE":
            return _check_compare(case, ans)
    except (ValueError, ArithmeticError, ZeroDivisionError, KeyError, TypeError) as exc:
        return False, f"Independent recomputation failed: {type(exc).__name__}: {exc}"
    return False, f"Unknown task: {task!r}"


def _check_compute(ans: dict[str, Any], inv: dict[str, Any], knot: str | None) -> tuple[bool, str]:
    if type(ans.get("writhe")) is not int or ans["writhe"] != inv["writhe"]:
        return False, f"Writhe {ans.get('writhe')!r} != independent {inv['writhe']}"
    for field in ("kauffman_bracket", "jones_polynomial", "alexander_polynomial"):
        got = _parse_laurent(ans.get(field))
        if got is None:
            return False, f"{field} missing or not a non-empty {{int-string: int}} map"
        if got != inv[field]:
            return False, f"{field} {ans.get(field)} != independent value"
    if knot is None or ans.get("identified_knot") != knot:
        return False, f"identified_knot {ans.get('identified_knot')!r} != independent {knot!r}"
    return True, f"Independent recomputation agrees ({knot}, writhe {inv['writhe']})"


def _check_identify(ans: dict[str, Any], inv: dict[str, Any], knot: str | None) -> tuple[bool, str]:
    if knot is None or ans.get("identified_knot") != knot:
        return False, f"identified_knot {ans.get('identified_knot')!r} != independent {knot!r}"
    chir = ans.get("chirality")
    if knot in _AMPHICHIRAL:
        if chir != "ACHIRAL":
            return False, f"{knot} is amphichiral but chirality is {chir!r}"
    elif chir not in ("RIGHT_HANDED", "LEFT_HANDED"):
        return False, f"{knot} is chiral but chirality is {chir!r}"
    invariants = ans.get("invariants")
    if not isinstance(invariants, dict):
        return False, "invariants must be an object"
    if "writhe" in invariants and invariants["writhe"] != inv["writhe"]:
        return False, f"invariants.writhe {invariants['writhe']!r} != independent {inv['writhe']}"
    for field in ("jones_polynomial", "alexander_polynomial"):
        if field in invariants and _parse_laurent(invariants[field]) != inv[field]:
            return False, f"invariants.{field} disagrees with the independent value"
    return True, f"Independent identification agrees ({knot}, {chir})"


def _check_compare(case: dict[str, Any], ans: dict[str, Any]) -> tuple[bool, str]:
    pds = (case.get("pd_1"), case.get("pd_2"))
    for pd in pds:
        if _pd_problems(pd):
            return False, "SOLVED on an invalid diagram"
    inv1, inv2 = (_invariants(pd) for pd in pds)
    keys = ("jones_polynomial", "alexander_polynomial")
    same = all(inv1[k] == inv2[k] for k in keys)
    kind = ans.get("kind")
    if kind == "SAME_INVARIANTS":
        if not same:
            return False, "Claimed SAME_INVARIANTS but the independent invariants differ"
        return True, "Independent comparison agrees: same invariants"
    if kind == "DIFFERENT_INVARIANTS":
        if same:
            return False, "Claimed DIFFERENT_INVARIANTS but the independent invariants agree"
        sep = ans.get("separating_invariant")
        if sep not in keys:
            return False, f"separating_invariant {sep!r} is not one of {keys}"
        v1, v2 = _parse_laurent(ans.get("val_1")), _parse_laurent(ans.get("val_2"))
        if v1 != inv1[sep] or v2 != inv2[sep]:
            return False, f"val_1/val_2 disagree with the independent {sep}"
        if v1 == v2:
            return False, "Separating invariant values are identical"
        return True, f"Independent comparison agrees: {sep} separates"
    return False, f"Invalid compare kind: {kind!r}"
