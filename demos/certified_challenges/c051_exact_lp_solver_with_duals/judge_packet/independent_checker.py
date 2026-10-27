"""Independent checker for C051: Exact LP Solver with Duals.

Correction, 2026-09-29: a case with a non-numeric entry (for example "abc",
a float or a Boolean) is now out of scope here as in the exact checker; before,
the entry became None and the arithmetic raised TypeError. Canonical answer
strings are matched in full (no surrounding whitespace, ASCII digits only).
"""

import re
from fractions import Fraction
from typing import Any, Dict, Optional, Tuple

CANON_RE = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?")


def indep_parse_canonical(val: Any) -> Tuple[bool, Optional[Fraction], str]:
    if isinstance(val, bool) or not isinstance(val, str):
        return False, None, "Type error"
    if not CANON_RE.fullmatch(val) or val == "-0":
        return False, None, "Regex mismatch"
    if "/" in val:
        ns, ds = val.split("/")
        n, d = int(ns), int(ds)
        if d <= 1:
            return False, None, "d <= 1"
        f = Fraction(n, d)
        if f.numerator != n or f.denominator != d:
            return False, None, "Unreduced"
        return True, f, "OK"
    return True, Fraction(int(val), 1), "OK"


def indep_parse_input(val: Any) -> Tuple[bool, Optional[Fraction], str]:
    if isinstance(val, bool):
        return False, None, "Bool error"
    if type(val) is int:
        return True, Fraction(val, 1), "OK"
    if isinstance(val, str):
        val = val.strip()
        if "." in val:
            return False, None, "Decimal error"
        if "/" in val:
            parts = val.split("/")
            if len(parts) != 2:
                return False, None, "Bad frac"
            try:
                n, d = int(parts[0]), int(parts[1])
                if d == 0:
                    return False, None, "Zero den"
                return True, Fraction(n, d), "OK"
            except Exception:
                return False, None, "Parse error"
        try:
            return True, Fraction(int(val), 1), "OK"
        except Exception:
            return False, None, "Parse error"
    return False, None, "Type error"


def check_solution(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result not a dict"
    cid = case.get("case_id") if isinstance(case, dict) else None
    if result.get("case_id") != cid:
        return False, "Case ID mismatch"
    status = result.get("status")
    for k in ("A", "b", "c"):
        if not isinstance(case.get(k), list):
            return (
                (True, "Out of scope verified")
                if status == "OUT_OF_SCOPE"
                else (False, "Expected OUT_OF_SCOPE")
            )
    m, n = len(case["b"]), len(case["c"])
    if m < 1 or n < 1 or len(case["A"]) != m:
        return (
            (True, "Out of scope verified")
            if status == "OUT_OF_SCOPE"
            else (False, "Expected OUT_OF_SCOPE")
        )
    for r in case["A"]:
        if not isinstance(r, list) or len(r) != n:
            return (
                (True, "Out of scope verified")
                if status == "OUT_OF_SCOPE"
                else (False, "Expected OUT_OF_SCOPE")
            )
    entries = [v for row in case["A"] for v in row] + list(case["b"]) + list(case["c"])
    if not all(indep_parse_input(v)[0] for v in entries):
        return (
            (True, "Out of scope verified")
            if status == "OUT_OF_SCOPE"
            else (False, "Expected OUT_OF_SCOPE: non-numeric entry")
        )
    if status == "OUT_OF_SCOPE":
        return False, "Valid case cannot be OUT_OF_SCOPE"
    if status != "SOLVED":
        return False, f"Status {status}"

    kind = result.get("kind")
    A = [[indep_parse_input(v)[1] for v in row] for row in case["A"]]
    b = [indep_parse_input(v)[1] for v in case["b"]]
    c = [indep_parse_input(v)[1] for v in case["c"]]

    if kind == "OPTIMAL":
        xr, yr, vr = result.get("x"), result.get("y"), result.get("value")
        if not isinstance(xr, list) or len(xr) != n or not isinstance(yr, list) or len(yr) != m:
            return False, "Length mismatch"
        ok_v, val, _ = indep_parse_canonical(vr)
        if not ok_v:
            return False, "Value non-canonical"
        x, y = [], []
        for elem in xr:
            ok, f, _ = indep_parse_canonical(elem)
            if not ok or f < 0:
                return False, "x non-canonical or negative"
            x.append(f)
        for elem in yr:
            ok, f, _ = indep_parse_canonical(elem)
            if not ok or f < 0:
                return False, "y non-canonical or negative"
            y.append(f)
        for i in range(m):
            if sum(A[i][j] * x[j] for j in range(n)) > b[i]:
                return False, "Primal infeasible"
        for j in range(n):
            if sum(A[i][j] * y[i] for i in range(m)) < c[j]:
                return False, "Dual infeasible"
        cx = sum(c[j] * x[j] for j in range(n))
        by = sum(b[i] * y[i] for i in range(m))
        if cx != by or cx != val:
            return False, "Duality gap mismatch"
        return True, "Independent checker: OPTIMAL OK"

    elif kind == "INFEASIBLE":
        yr = result.get("farkas_y")
        if not isinstance(yr, list) or len(yr) != m:
            return False, "farkas_y length mismatch"
        y = []
        for elem in yr:
            ok, f, _ = indep_parse_canonical(elem)
            if not ok or f < 0:
                return False, "farkas_y non-canonical or negative"
            y.append(f)
        for j in range(n):
            if sum(A[i][j] * y[i] for i in range(m)) < 0:
                return False, "A^T y < 0"
        if sum(b[i] * y[i] for i in range(m)) >= 0:
            return False, "b.y >= 0"
        return True, "Independent checker: INFEASIBLE OK"

    elif kind == "UNBOUNDED":
        xr, rr = result.get("x"), result.get("ray")
        if not isinstance(xr, list) or len(xr) != n or not isinstance(rr, list) or len(rr) != n:
            return False, "Length mismatch"
        x, d = [], []
        for elem in xr:
            ok, f, _ = indep_parse_canonical(elem)
            if not ok or f < 0:
                return False, "x error"
            x.append(f)
        for elem in rr:
            ok, f, _ = indep_parse_canonical(elem)
            if not ok or f < 0:
                return False, "ray error"
            d.append(f)
        for i in range(m):
            if sum(A[i][j] * x[j] for j in range(n)) > b[i]:
                return False, "Ax <= b violated"
            if sum(A[i][j] * d[j] for j in range(n)) > 0:
                return False, "Ad <= 0 violated"
        if sum(c[j] * d[j] for j in range(n)) <= 0:
            return False, "c.d <= 0"
        return True, "Independent checker: UNBOUNDED OK"

    return False, f"Unknown kind {kind}"
