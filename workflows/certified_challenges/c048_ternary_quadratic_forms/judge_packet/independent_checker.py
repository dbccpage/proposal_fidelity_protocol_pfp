"""Independent checker for C048: Ternary Quadratic Forms.
Uses independent prime factorization and Jacobi symbol recursion.
"""

import re
from typing import Any, Dict, Tuple


def independent_jacobi(a: int, n: int) -> int:
    """Compute Jacobi symbol (a/n) recursively for positive odd n."""
    a = a % n
    t = 1
    while a != 0:
        while a % 2 == 0:
            a //= 2
            r = n % 8
            if r in (3, 5):
                t = -t
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            t = -t
        a = a % n
    return t if n == 1 else 0


def independent_hilbert(u: int, w: int, p: int) -> int:
    """Independent calculation of Hilbert symbol (u, w)_p for odd prime p."""
    alpha = 0
    u0 = u
    while u0 % p == 0:
        u0 //= p
        alpha += 1

    beta = 0
    w0 = w
    while w0 % p == 0:
        w0 //= p
        beta += 1

    if p == 2:
        eps_u = ((u0 - 1) // 2) % 2
        eps_w = ((w0 - 1) // 2) % 2
        core_u = ((u0 * u0 - 1) // 8) % 2
        core_w = ((w0 * w0 - 1) // 8) % 2
        exp = (eps_u * eps_w + alpha * core_w + beta * core_u) % 2
        return -1 if exp == 1 else 1

    exp_sign = (alpha * beta * ((p - 1) // 2)) % 2
    s1 = -1 if exp_sign == 1 else 1
    leg_u = independent_jacobi(u0, p)
    leg_w = independent_jacobi(w0, p)

    term_u = (leg_u**beta) if beta % 2 == 1 else 1
    term_w = (leg_w**alpha) if alpha % 2 == 1 else 1
    return s1 * term_u * term_w


_INT_RE = re.compile(r"^-?\d+$")


def _exact_int(x: Any) -> int | None:
    """The integer for an int (not bool) or an integer string; None otherwise."""
    if type(x) is int:
        return x
    if isinstance(x, str) and _INT_RE.match(x.strip()):
        return int(x.strip())
    return None


def _independent_is_prime(p: int) -> bool:
    if p < 2:
        return False
    d = 2
    while d * d <= p:
        if p % d == 0:
            return False
        d += 1
    return True


def independent_check(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str]:
    """Independent pass for C048."""
    if not isinstance(result, dict) or not isinstance(case, dict):
        return False, "Case and result must be objects"
    if result.get("case_id") != case.get("case_id"):
        return (
            False,
            f"case_id mismatch: expected {case.get('case_id')!r}, got {result.get('case_id')!r}",
        )

    coeffs = [_exact_int(case.get(k)) for k in ("a", "b", "c")]
    status = result.get("status")
    if status == "OUT_OF_SCOPE":
        # OUT_OF_SCOPE is warranted only by a coefficient that is not an exact integer.
        if all(v is not None for v in coeffs):
            return False, "OUT_OF_SCOPE on a case whose coefficients are all integers"
        return True, "Independent OUT_OF_SCOPE verified: non-integer coefficient"

    if status != "SOLVED":
        return False, f"Status not SOLVED: {status}"
    if any(v is None for v in coeffs):
        return False, "SOLVED on a case with a non-integer coefficient"
    a, b, c = coeffs

    kind = result.get("kind")
    if kind == "RATIONAL_POINT":
        x, y, z = (
            _exact_int(result.get(k)) if isinstance(result.get(k), str) else None
            for k in ("x", "y", "z")
        )
        if x is None or y is None or z is None:
            return (
                False,
                f"Coordinates must be integer strings, got x={result.get('x')!r}, y={result.get('y')!r}, z={result.get('z')!r}",
            )
        if x == 0 and y == 0 and z == 0:
            return False, "All coordinates zero"
        val = a * x * x + b * y * y + c * z * z
        if val != 0:
            return False, f"Non-zero quadratic evaluation: {val}"
        return True, "Independent RATIONAL_POINT verified"

    if kind == "LOCAL_OBSTRUCTION":
        if a == 0 or b == 0 or c == 0:
            return False, "A form with a zero coefficient has a non-trivial zero; no obstruction"
        place_str = result.get("place")
        u = -a * c
        w = -b * c

        if place_str == "inf":
            if (a > 0 and b > 0 and c > 0) or (a < 0 and b < 0 and c < 0):
                return True, "Independent LOCAL_OBSTRUCTION at inf verified"
            return False, "Form is indefinite over R"

        p = _exact_int(place_str) if isinstance(place_str, str) else None
        if p is None:
            return False, f"Place must be 'inf' or a prime as a string, got {place_str!r}"
        if not _independent_is_prime(p):
            return False, f"Place {p} is not prime"

        sym = independent_hilbert(u, w, p)
        if sym != -1:
            return False, f"Independent Hilbert symbol is {sym}"
        return True, f"Independent LOCAL_OBSTRUCTION verified at {p}"

    return False, f"Unknown kind: {kind}"
