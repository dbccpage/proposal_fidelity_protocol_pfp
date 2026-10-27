"""Reference self-verifying certificate checker for Challenge C060.

Verifies exact weighted-L1 (Phi1) primal-dual certificates under total rational algebra.
Never raises an exception on any JSON input.
"""

import math
import re
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple

REJECTION_CODES = {
    "SCHEMA",
    "NONCANONICAL_RATIONAL",
    "DIMENSION",
    "NONPOSITIVE_WEIGHT",
    "RESIDUAL_MISMATCH",
    "PRIMAL_VALUE_MISMATCH",
    "DUAL_NOT_IN_COKERNEL",
    "DUAL_BOUND_VIOLATED",
    "DUAL_VALUE_MISMATCH",
}

INT_RE = re.compile(r"^(?:0|-?[1-9][0-9]*)$")
FRAC_RE = re.compile(r"^(-?[1-9][0-9]*)/([1-9][0-9]*)$")


def parse_canonical_rational(val: Any) -> Tuple[bool, Optional[Fraction]]:
    """Validates and parses a canonical rational string.

    Returns:
        (is_valid, fraction_obj)
    """
    if not isinstance(val, str) or isinstance(val, bool):
        return False, None

    # 1. Match integer
    m_int = INT_RE.match(val)
    if m_int:
        try:
            return True, Fraction(int(val), 1)
        except Exception:
            return False, None

    # 2. Match fraction p/q
    m_frac = FRAC_RE.match(val)
    if m_frac:
        p_str, q_str = m_frac.groups()
        try:
            p = int(p_str)
            q = int(q_str)
            # Denominator must be strictly > 1 (integers cannot have /1)
            if q <= 1:
                return False, None
            # Must be in lowest terms: gcd(|p|, q) == 1
            if math.gcd(abs(p), q) != 1:
                return False, None
            return True, Fraction(p, q)
        except Exception:
            return False, None

    return False, None


def _check_impl(case: Any, cert: Any) -> Dict[str, Any]:
    # 1. SCHEMA VALIDATION
    if not isinstance(case, dict) or not isinstance(cert, dict):
        return {"verdict": "REJECT", "code": "SCHEMA", "index": None}

    for req_k in ("d0", "omega", "w"):
        if req_k not in case:
            return {"verdict": "REJECT", "code": "SCHEMA", "index": None}

    for req_k in ("alpha", "r", "y", "value"):
        if req_k not in cert:
            return {"verdict": "REJECT", "code": "SCHEMA", "index": None}

    raw_d0 = case["d0"]
    raw_core = case["omega"]
    raw_w = case["w"]
    raw_alpha = cert["alpha"]
    raw_r = cert["r"]
    raw_y = cert["y"]
    raw_val = cert["value"]

    if (
        not isinstance(raw_d0, list)
        or not isinstance(raw_core, list)
        or not isinstance(raw_w, list)
    ):
        return {"verdict": "REJECT", "code": "SCHEMA", "index": None}
    if (
        not isinstance(raw_alpha, list)
        or not isinstance(raw_r, list)
        or not isinstance(raw_y, list)
    ):
        return {"verdict": "REJECT", "code": "SCHEMA", "index": None}
    if not isinstance(raw_val, str) or isinstance(raw_val, bool):
        return {"verdict": "REJECT", "code": "SCHEMA", "index": None}

    for row in raw_d0:
        if not isinstance(row, list):
            return {"verdict": "REJECT", "code": "SCHEMA", "index": None}

    # 2. CANONICAL RATIONAL PARSING
    # value
    ok, val_frac = parse_canonical_rational(raw_val)
    if not ok or val_frac is None:
        return {"verdict": "REJECT", "code": "NONCANONICAL_RATIONAL", "index": None}

    # omega
    core_fracs: List[Fraction] = []
    for item in raw_core:
        ok, fr = parse_canonical_rational(item)
        if not ok or fr is None:
            return {"verdict": "REJECT", "code": "NONCANONICAL_RATIONAL", "index": None}
        core_fracs.append(fr)

    # w
    w_fracs: List[Fraction] = []
    for item in raw_w:
        ok, fr = parse_canonical_rational(item)
        if not ok or fr is None:
            return {"verdict": "REJECT", "code": "NONCANONICAL_RATIONAL", "index": None}
        w_fracs.append(fr)

    # alpha
    alpha_fracs: List[Fraction] = []
    for item in raw_alpha:
        ok, fr = parse_canonical_rational(item)
        if not ok or fr is None:
            return {"verdict": "REJECT", "code": "NONCANONICAL_RATIONAL", "index": None}
        alpha_fracs.append(fr)

    # r
    r_fracs: List[Fraction] = []
    for item in raw_r:
        ok, fr = parse_canonical_rational(item)
        if not ok or fr is None:
            return {"verdict": "REJECT", "code": "NONCANONICAL_RATIONAL", "index": None}
        r_fracs.append(fr)

    # y
    y_fracs: List[Fraction] = []
    for item in raw_y:
        ok, fr = parse_canonical_rational(item)
        if not ok or fr is None:
            return {"verdict": "REJECT", "code": "NONCANONICAL_RATIONAL", "index": None}
        y_fracs.append(fr)

    # d0
    d0_fracs: List[List[Fraction]] = []
    for row in raw_d0:
        row_fracs = []
        for item in row:
            ok, fr = parse_canonical_rational(item)
            if not ok or fr is None:
                return {"verdict": "REJECT", "code": "NONCANONICAL_RATIONAL", "index": None}
            row_fracs.append(fr)
        d0_fracs.append(row_fracs)

    # 3. DIMENSION VALIDATION
    m = len(core_fracs)
    if m == 0:
        return {"verdict": "REJECT", "code": "DIMENSION", "index": None}
    if len(w_fracs) != m or len(r_fracs) != m or len(y_fracs) != m:
        return {"verdict": "REJECT", "code": "DIMENSION", "index": None}
    if len(d0_fracs) != m:
        return {"verdict": "REJECT", "code": "DIMENSION", "index": None}

    k = len(alpha_fracs)
    for i, row in enumerate(d0_fracs):
        if len(row) != k:
            return {"verdict": "REJECT", "code": "DIMENSION", "index": i}

    # 4. NONPOSITIVE_WEIGHT
    for i, w_e in enumerate(w_fracs):
        if w_e <= 0:
            return {"verdict": "REJECT", "code": "NONPOSITIVE_WEIGHT", "index": i}

    # 5. RESIDUAL_MISMATCH: r = omega - d0 * alpha
    for e in range(m):
        repair_e = sum((d0_fracs[e][j] * alpha_fracs[j] for j in range(k)), Fraction(0, 1))
        expected_r_e = core_fracs[e] - repair_e
        if r_fracs[e] != expected_r_e:
            return {"verdict": "REJECT", "code": "RESIDUAL_MISMATCH", "index": e}

    # 6. PRIMAL_VALUE_MISMATCH: sum(w_e * |r_e|) == value
    primal_val = sum((w_fracs[e] * abs(r_fracs[e]) for e in range(m)), Fraction(0, 1))
    if primal_val != val_frac:
        return {"verdict": "REJECT", "code": "PRIMAL_VALUE_MISMATCH", "index": None}

    # 7. DUAL_NOT_IN_COKERNEL: d0^T * y == 0 (for all columns j in 0..k-1)
    for j in range(k):
        col_dot = sum((d0_fracs[e][j] * y_fracs[e] for e in range(m)), Fraction(0, 1))
        if col_dot != 0:
            return {"verdict": "REJECT", "code": "DUAL_NOT_IN_COKERNEL", "index": j}

    # 8. DUAL_BOUND_VIOLATED: |y_e| <= w_e
    for e in range(m):
        if abs(y_fracs[e]) > w_fracs[e]:
            return {"verdict": "REJECT", "code": "DUAL_BOUND_VIOLATED", "index": e}

    # 9. DUAL_VALUE_MISMATCH: y^T * omega == value
    dual_val = sum((y_fracs[e] * core_fracs[e] for e in range(m)), Fraction(0, 1))
    if dual_val != val_frac:
        return {"verdict": "REJECT", "code": "DUAL_VALUE_MISMATCH", "index": None}

    # ALL INVARIANTS SATISFIED
    return {"verdict": "ACCEPT"}


def check(case: Any, cert: Any) -> Dict[str, Any]:
    """Total certificate verification function.

    Never raises an exception under any circumstances.
    """
    try:
        return _check_impl(case, cert)
    except Exception:
        return {"verdict": "REJECT", "code": "SCHEMA", "index": None}
