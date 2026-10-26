"""Independent checker for C047: Recurrence and Generating-Function Discovery.

Uses its own exact-integer parsing, Fraction-based Gaussian elimination and direct residual
evaluation; it does not import the reference solver. An empty object, an UNKNOWN, an empty
or all-zero recurrence, and an empty or non-square absence minor never pass.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Any

_INT_RE = re.compile(r"^-?\d+$")


def _exact_int(x: Any) -> int | None:
    """Returns the integer for an int (not bool) or an integer string; None otherwise."""
    if type(x) is int:
        return x
    if isinstance(x, str) and _INT_RE.match(x.strip()):
        return int(x.strip())
    return None


def independent_det(matrix: list[list[Fraction]]) -> Fraction:
    """Determinant of a square matrix by Gaussian elimination over Q."""
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("determinant of a non-square matrix")
    A = [[Fraction(val) for val in row] for row in matrix]
    det = Fraction(1)
    for i in range(n):
        pivot = next((j for j in range(i, n) if A[j][i] != 0), None)
        if pivot is None:
            return Fraction(0)
        if pivot != i:
            A[i], A[pivot] = A[pivot], A[i]
            det = -det
        det *= A[i][i]
        p_val = A[i][i]
        for j in range(i + 1, n):
            factor = A[j][i] / p_val
            for k in range(i + 1, n):
                A[j][k] -= factor * A[i][k]
    return det


def _poly_value(coeffs: list[int], n: int) -> int:
    return sum(c * n**j for j, c in enumerate(coeffs))


def _sign(x: int) -> int:
    return (x > 0) - (x < 0)


def _trim(coeffs: list[int]) -> list[int]:
    out = list(coeffs)
    while out and out[-1] == 0:
        out.pop()
    return out


def _derivative(coeffs: list[int]) -> list[int]:
    return _trim([j * c for j, c in enumerate(coeffs)][1:])


def _cauchy_bound(coeffs: list[int]) -> int:
    """An integer B with |x| <= B for every complex root x (Cauchy: 1 + max |a_i / a_d|)."""
    lead = abs(coeffs[-1])
    top = max((abs(c) for c in coeffs[:-1]), default=0)
    return 1 + -(-top // lead)


def _monotone_breakpoints(coeffs: list[int], lo: int, hi: int) -> list[int]:
    """Sorted integers lo = b_0 < ... < b_k = hi such that on each [b_i, b_{i+1}] the
    polynomial is monotone, or the interval has length 1.

    The derivative's sign changes are located to integer resolution by bisection on the
    derivative's own monotone pieces (recursion on the degree), so no step enumerates the
    integers between the bounds.
    """
    if hi - lo <= 1 or len(coeffs) <= 2:
        return sorted({lo, hi})
    deriv = _derivative(coeffs)
    points = {lo, hi}
    pieces = _monotone_breakpoints(deriv, lo, hi)
    for a, b in zip(pieces, pieces[1:]):
        points.update((a, b))
        if b - a <= 1:
            continue
        sa, sb = _sign(_poly_value(deriv, a)), _sign(_poly_value(deriv, b))
        if sa * sb >= 0:
            # deriv is strictly monotone on [a, b]; with no sign change inside, or its only
            # zero at an endpoint, the polynomial is monotone on [a, b].
            continue
        # deriv changes sign once inside (a, b): bracket that point to integer resolution.
        left, right = a, b
        zero_at = None
        while right - left > 1:
            mid = (left + right) // 2
            sm = _sign(_poly_value(deriv, mid))
            if sm == 0:
                zero_at = mid
                break
            if sm == sa:
                left = mid
            else:
                right = mid
        if zero_at is None:
            points.update((left, right))
        else:
            points.update(p for p in (zero_at - 1, zero_at, zero_at + 1) if a <= p <= b)
    return sorted(points)


def _integer_roots_in(coeffs: list[int], lo: int, hi: int) -> list[int]:
    """All integer roots of a nonzero integer polynomial in [lo, hi], found exactly."""
    coeffs = _trim(coeffs)
    if lo > hi or not coeffs:
        return []
    if len(coeffs) == 1:
        return []
    if len(coeffs) == 2:
        c0, c1 = coeffs
        if c0 % c1:
            return []
        root = -c0 // c1
        return [root] if lo <= root <= hi else []
    roots: set[int] = set()
    pieces = _monotone_breakpoints(coeffs, lo, hi)
    for a, b in zip(pieces, pieces[1:]):
        va, vb = _poly_value(coeffs, a), _poly_value(coeffs, b)
        if va == 0:
            roots.add(a)
        if vb == 0:
            roots.add(b)
        if b - a <= 1 or va == 0 or vb == 0 or _sign(va) == _sign(vb):
            continue
        left, right = a, b
        while right - left > 1:
            mid = (left + right) // 2
            vm = _poly_value(coeffs, mid)
            if vm == 0:
                roots.add(mid)
                break
            if _sign(vm) == _sign(va):
                left = mid
            else:
                right = mid
    return sorted(roots)


def _has_integer_root_at_or_after(coeffs: list[int], start: int) -> bool:
    """True if the integer polynomial has an integer root n >= start.

    Degree 1 is a divisibility test. Higher degrees search [max(start, -B), B], B the Cauchy
    bound, by integer bisection on monotone pieces; the cost grows with log B, not with B.
    """
    coeffs = _trim(coeffs)
    if not coeffs:
        return True  # the zero polynomial vanishes everywhere
    bound = _cauchy_bound(coeffs) if len(coeffs) > 1 else 0
    return bool(_integer_roots_in(coeffs, max(start, -bound), bound))


def _check_out_of_scope(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, str]:
    witness = result.get("witness")
    if not isinstance(witness, dict) or witness.get("reason") != "NON_INTEGER_TERM":
        return False, "OUT_OF_SCOPE needs a NON_INTEGER_TERM witness"
    idx = witness.get("index")
    raw_terms = case.get("terms", [])
    if type(idx) is not int or not 0 <= idx < len(raw_terms):
        return False, "Invalid OUT_OF_SCOPE index"
    if _exact_int(raw_terms[idx]) is not None:
        return False, "Reported non-integer term is actually an integer"
    return True, "Independent OUT_OF_SCOPE verified"


def independent_check(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, str]:
    """Independent verification pass."""
    if not isinstance(result, dict) or not isinstance(case, dict):
        return False, "Case and result must be objects"
    if result.get("case_id") != case.get("case_id"):
        return (
            False,
            f"case_id mismatch: expected {case.get('case_id')!r}, got {result.get('case_id')!r}",
        )

    status = result.get("status")
    if status == "OUT_OF_SCOPE":
        return _check_out_of_scope(case, result)
    if status != "SOLVED":
        return False, f"Status not SOLVED: {status!r}"

    terms = [_exact_int(x) for x in case.get("terms", [])]
    held = [_exact_int(x) for x in case.get("held_out_terms", [])]
    if any(t is None for t in terms + held):
        return False, "Case has a non-integer term; SOLVED is not admissible"
    r_max = _exact_int(case.get("r_max", 8))
    d_max = _exact_int(case.get("d_max", 3))
    if r_max is None or d_max is None:
        return False, "Case bounds are not integers"

    kind = result.get("kind")
    if kind == "RECURRENCE":
        return _check_recurrence(result, terms + held, r_max, d_max)
    if kind == "NONE_WITHIN_BOUNDS":
        return _check_absence(result, terms, r_max, d_max)
    return False, f"Unknown kind: {kind!r}"


def _check_recurrence(
    result: dict[str, Any], all_terms: list[int], r_max: int, d_max: int
) -> tuple[bool, str]:
    polys_raw = result.get("polys")
    if not isinstance(polys_raw, list) or len(polys_raw) < 2:
        return False, "polys must list at least two polynomials (order >= 1)"
    r = len(polys_raw) - 1
    if r > r_max:
        return False, f"Recurrence order {r} exceeds r_max {r_max}"
    polys: list[list[int]] = []
    for p in polys_raw:
        if not isinstance(p, list) or not p or len(p) - 1 > d_max:
            return False, "Each polynomial must be a non-empty coefficient list of degree <= d_max"
        coeffs = [_exact_int(c) if isinstance(c, str) else None for c in p]
        if any(c is None for c in coeffs):
            return False, "Polynomial coefficients must be integer strings"
        polys.append(coeffs)
    if all(c == 0 for c in polys[-1]):
        return False, "Leading polynomial is identically zero"
    start = result.get("start", 0)
    if type(start) is not int or start < 0:
        return False, f"Invalid start index: {start!r}"
    if _has_integer_root_at_or_after(polys[-1], start):
        return False, "Leading polynomial vanishes at an integer n >= start"
    last = len(all_terms) - r
    if last <= start:
        return False, "The recurrence is not checked on any index (vacuous replay)"
    for n in range(start, last):
        res = sum(_poly_value(p, n) * all_terms[n + i] for i, p in enumerate(polys))
        if res != 0:
            return False, f"Independent checker failed at n={n}: residual={res}"
    return True, f"Independent RECURRENCE verified on {last - start} indices"


def _check_absence(
    result: dict[str, Any], terms: list[int], r_max: int, d_max: int
) -> tuple[bool, str]:
    if result.get("order") != r_max or result.get("degree") != d_max:
        return False, "Absence proof must certify the case bounds (order = r_max, degree = d_max)"
    minor_rows = result.get("minor_rows")
    size = (r_max + 1) * (d_max + 1)
    if not isinstance(minor_rows, list) or len(minor_rows) != size:
        return False, f"minor_rows must list exactly {size} row indices"
    if any(type(x) is not int for x in minor_rows) or len(set(minor_rows)) != size:
        return False, "minor_rows must be distinct integer indices"
    start_range = result.get("start_range", [0, 0])
    max_start = (
        start_range[1]
        if isinstance(start_range, list) and len(start_range) >= 2 and type(start_range[1]) is int
        else 0
    )
    matrix = []
    for n in minor_rows:
        if n < max(0, max_start) or n + r_max >= len(terms):
            return False, f"Row index {n} is outside the admissible range"
        matrix.append(
            [Fraction(n**j * terms[n + i]) for i in range(r_max + 1) for j in range(d_max + 1)]
        )
    det = independent_det(matrix)
    if det == 0:
        return False, "Independent determinant is 0"
    return True, f"Independent NONE_WITHIN_BOUNDS verified (det={det})"
