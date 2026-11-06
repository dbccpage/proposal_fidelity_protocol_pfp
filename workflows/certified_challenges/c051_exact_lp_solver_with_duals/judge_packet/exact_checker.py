"""Exact checker for C051: Exact LP Solver with Duals.

Correction, 2026-09-29: answer strings must be canonical in full; surrounding
whitespace, a '+' sign, leading zeros and "-0" are refused (they were accepted
through int()).
"""

import math
import re
from fractions import Fraction
from typing import Any, Dict, Optional, Tuple

_CANONICAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?")


def parse_canonical_fraction(s: Any) -> Tuple[bool, Optional[Fraction], str]:
    if isinstance(s, bool) or not isinstance(s, str):
        return False, None, "Must be string, not bool"
    if not _CANONICAL.fullmatch(s) or s == "-0":
        return False, None, "Not a canonical rational string"
    if "." in s:
        return False, None, "Decimals not allowed"
    if "/" in s:
        parts = s.split("/")
        if len(parts) != 2:
            return False, None, "Bad fraction"
        try:
            num, den = int(parts[0]), int(parts[1])
        except Exception:
            return False, None, "Integer parse error"
        if den <= 1:
            return False, None, "Denominator must be > 1"
        if math.gcd(abs(num), den) != 1:
            return False, None, "Not in lowest terms"
        return True, Fraction(num, den), "OK"
    try:
        return True, Fraction(int(s), 1), "OK"
    except Exception:
        return False, None, "Integer parse error"


def parse_input_fraction(s: Any) -> Tuple[bool, Optional[Fraction], str]:
    if isinstance(s, bool):
        return False, None, "Bool not allowed"
    if type(s) is int:
        return True, Fraction(s, 1), "OK"
    if isinstance(s, str):
        s = s.strip()
        if "." in s:
            return False, None, "Decimals not allowed"
        if "/" in s:
            parts = s.split("/")
            if len(parts) != 2:
                return False, None, "Bad fraction"
            try:
                n, d = int(parts[0]), int(parts[1])
                if d == 0:
                    return False, None, "Zero denominator"
                return True, Fraction(n, d), "OK"
            except Exception:
                return False, None, "Integer parse error"
        try:
            return True, Fraction(int(s), 1), "OK"
        except Exception:
            return False, None, "Integer parse error"
    return False, None, "Unsupported type"


def is_malformed_case(case: Any) -> Tuple[bool, str]:
    if not isinstance(case, dict):
        return True, "Not a dict"
    for k in ("A", "b", "c"):
        if k not in case or not isinstance(case[k], list):
            return True, f"Missing or non-list {k}"
    m, n = len(case["b"]), len(case["c"])
    if m < 1 or n < 1 or len(case["A"]) != m:
        return True, "Dimension mismatch"
    for i, row in enumerate(case["A"]):
        if not isinstance(row, list) or len(row) != n:
            return True, f"Row {i} length mismatch"
        for j, v in enumerate(row):
            if not parse_input_fraction(v)[0]:
                return True, f"Bad A[{i}][{j}]"
    for i, v in enumerate(case["b"]):
        if not parse_input_fraction(v)[0]:
            return True, f"Bad b[{i}]"
    for j, v in enumerate(case["c"]):
        if not parse_input_fraction(v)[0]:
            return True, f"Bad c[{j}]"
    return False, "Valid"


def check_solution(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result must be a dict"
    expected_cid = case.get("case_id") if isinstance(case, dict) else None
    if result.get("case_id") != expected_cid:
        return False, "Case ID mismatch"
    status = result.get("status")
    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return False, f"Invalid status {status}"
    malformed, msg = is_malformed_case(case)
    if status == "OUT_OF_SCOPE":
        return (
            (True, "Valid OUT_OF_SCOPE")
            if malformed
            else (False, "Valid case cannot be OUT_OF_SCOPE")
        )
    if malformed:
        return False, f"Case is malformed: {msg}"
    if status != "SOLVED":
        return False, f"Status is {status}"

    kind = result.get("kind")
    A = [[parse_input_fraction(v)[1] for v in row] for row in case["A"]]
    b = [parse_input_fraction(v)[1] for v in case["b"]]
    c = [parse_input_fraction(v)[1] for v in case["c"]]
    m, n = len(b), len(c)

    if kind == "OPTIMAL":
        xr, yr, vr = result.get("x"), result.get("y"), result.get("value")
        if not isinstance(xr, list) or len(xr) != n:
            return False, "x length mismatch"
        if not isinstance(yr, list) or len(yr) != m:
            return False, "y length mismatch"
        ok_v, val, _ = parse_canonical_fraction(vr)
        if not ok_v:
            return False, "Non-canonical value"
        x, y = [], []
        for v in xr:
            ok, f, _ = parse_canonical_fraction(v)
            if not ok or f < 0:
                return False, "Bad x entry"
            x.append(f)
        for v in yr:
            ok, f, _ = parse_canonical_fraction(v)
            if not ok or f < 0:
                return False, "Bad y entry"
            y.append(f)
        for i in range(m):
            if sum(A[i][j] * x[j] for j in range(n)) > b[i]:
                return False, "Ax <= b violated"
        for j in range(n):
            if sum(A[i][j] * y[i] for i in range(m)) < c[j]:
                return False, "A^T y >= c violated"
        cx = sum(c[j] * x[j] for j in range(n))
        by = sum(b[i] * y[i] for i in range(m))
        if cx != by or cx != val:
            return False, "Duality gap or value mismatch"
        return True, "OPTIMAL verified"

    elif kind == "INFEASIBLE":
        yr = result.get("farkas_y")
        if not isinstance(yr, list) or len(yr) != m:
            return False, "farkas_y length mismatch"
        y = []
        for v in yr:
            ok, f, _ = parse_canonical_fraction(v)
            if not ok or f < 0:
                return False, "Bad farkas_y entry"
            y.append(f)
        for j in range(n):
            if sum(A[i][j] * y[i] for i in range(m)) < 0:
                return False, "A^T y >= 0 violated"
        if sum(b[i] * y[i] for i in range(m)) >= 0:
            return False, "b.y < 0 violated"
        return True, "INFEASIBLE verified"

    elif kind == "UNBOUNDED":
        xr, rr = result.get("x"), result.get("ray")
        if not isinstance(xr, list) or len(xr) != n:
            return False, "x length mismatch"
        if not isinstance(rr, list) or len(rr) != n:
            return False, "ray length mismatch"
        x, d = [], []
        for v in xr:
            ok, f, _ = parse_canonical_fraction(v)
            if not ok or f < 0:
                return False, "Bad x entry"
            x.append(f)
        for v in rr:
            ok, f, _ = parse_canonical_fraction(v)
            if not ok or f < 0:
                return False, "Bad ray entry"
            d.append(f)
        for i in range(m):
            if sum(A[i][j] * x[j] for j in range(n)) > b[i]:
                return False, "Ax <= b violated"
            if sum(A[i][j] * d[j] for j in range(n)) > 0:
                return False, "Ad <= 0 violated"
        if sum(c[j] * d[j] for j in range(n)) <= 0:
            return False, "c.d > 0 violated"
        return True, "UNBOUNDED verified"

    return False, f"Unknown kind {kind}"
