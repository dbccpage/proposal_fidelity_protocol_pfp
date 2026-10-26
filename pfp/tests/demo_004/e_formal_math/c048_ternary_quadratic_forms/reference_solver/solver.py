"""Frozen reference solver for C048: Ternary Quadratic Forms.
Solves a x^2 + b y^2 + c z^2 = 0 or finds a local Hilbert obstruction.
"""

from typing import Any, Dict

from .factorization import prime_factors
from .hilbert_symbol import hilbert_symbol
from .legendre_solver import solve_ternary


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """Solve a C048 ternary quadratic form case."""
    case_id = case.get("case_id", "tq_unknown")
    raw_a = case.get("a")
    raw_b = case.get("b")
    raw_c = case.get("c")

    trace = ["C", "R"]

    # 1. Input parsing and validation
    try:
        a = int(str(raw_a))
        b = int(str(raw_b))
        c = int(str(raw_c))
    except (ValueError, TypeError):
        trace.append("M")
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {
                "reason": "MALFORMED_COEFFICIENT",
                "raw_values": [str(raw_a), str(raw_b), str(raw_c)],
            },
            "trace": trace,
        }

    # 2. Check for real obstruction at infinity
    if (a > 0 and b > 0 and c > 0) or (a < 0 and b < 0 and c < 0):
        trace.extend(["I", "E", "T"])
        return {
            "case_id": case_id,
            "status": "SOLVED",
            "kind": "LOCAL_OBSTRUCTION",
            "place": "inf",
            "trace": trace,
        }

    # 3. Direct fast search for rational points
    trace.append("I")
    point = solve_ternary(a, b, c)
    if point is not None:
        x, y, z = point
        trace.extend(["E", "T"])
        return {
            "case_id": case_id,
            "status": "SOLVED",
            "kind": "RATIONAL_POINT",
            "x": str(x),
            "y": str(y),
            "z": str(z),
            "trace": trace,
        }

    # 4. Local Hilbert symbol obstruction checks
    trace.append("D")
    u = -a * c
    w = -b * c

    # Check place 2 first
    if hilbert_symbol(u, w, 2) == -1:
        trace.extend(["E", "T"])
        return {
            "case_id": case_id,
            "status": "SOLVED",
            "kind": "LOCAL_OBSTRUCTION",
            "place": "2",
            "trace": trace,
        }

    # Check odd primes dividing 2 * a * b * c
    primes = sorted(prime_factors(2 * a * b * c))
    for p in primes:
        if p == 2:
            continue
        if hilbert_symbol(u, w, p) == -1:
            trace.extend(["E", "T"])
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "LOCAL_OBSTRUCTION",
                "place": str(p),
                "trace": trace,
            }

    # 5. Fallback to UNKNOWN if factoring or search exceeded
    trace.append("M")
    return {"case_id": case_id, "status": "UNKNOWN", "code": "FACTORING_LIMIT", "trace": trace}
