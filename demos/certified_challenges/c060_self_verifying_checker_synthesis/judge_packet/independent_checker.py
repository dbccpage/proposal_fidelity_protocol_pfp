"""Independent checker for Challenge C060: Checker Synthesis Scored by Mutation Kill Rate.

Independent clean-room evaluator of Phi1 primal-dual certificates.
Compares candidate output against independently computed ground truth.
"""

import math
from fractions import Fraction
from typing import Any, Callable, Dict, Optional, Tuple, Union


def _parse_canonical_rat(v: Any) -> Optional[Fraction]:
    if not isinstance(v, str) or isinstance(v, bool):
        return None
    if not v:
        return None
    if "/" in v:
        parts = v.split("/")
        if len(parts) != 2:
            return None
        p_str, q_str = parts
        # Must not have leading '+' or extra spaces
        if not (p_str.isdigit() or (p_str.startswith("-") and p_str[1:].isdigit())):
            return None
        if not q_str.isdigit():
            return None
        p = int(p_str)
        q = int(q_str)
        if q <= 1:
            return None
        # Canonical lowest terms
        if math.gcd(abs(p), q) != 1:
            return None
        # Re-stringify to forbid leading zeroes like '01'
        if str(p) != p_str or str(q) != q_str:
            return None
        return Fraction(p, q)
    else:
        # Integer string
        if not (v.isdigit() or (v.startswith("-") and v[1:].isdigit())):
            return None
        val = int(v)
        if str(val) != v:
            return None
        return Fraction(val, 1)


def evaluate_phi1_independent(case: Any, cert: Any) -> Tuple[str, Optional[str]]:
    """Clean-room independent mathematical certificate evaluator.

    Returns:
        (verdict, code)
    """
    if not isinstance(case, dict) or not isinstance(cert, dict):
        return "REJECT", "SCHEMA"

    for k in ("d0", "omega", "w"):
        if k not in case:
            return "REJECT", "SCHEMA"
    for k in ("alpha", "r", "y", "value"):
        if k not in cert:
            return "REJECT", "SCHEMA"

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
        return "REJECT", "SCHEMA"
    if (
        not isinstance(raw_alpha, list)
        or not isinstance(raw_r, list)
        or not isinstance(raw_y, list)
    ):
        return "REJECT", "SCHEMA"

    val_f = _parse_canonical_rat(raw_val)
    if val_f is None:
        return "REJECT", "NONCANONICAL_RATIONAL"

    core_f = []
    for x in raw_core:
        xf = _parse_canonical_rat(x)
        if xf is None:
            return "REJECT", "NONCANONICAL_RATIONAL"
        core_f.append(xf)

    w_f = []
    for x in raw_w:
        xf = _parse_canonical_rat(x)
        if xf is None:
            return "REJECT", "NONCANONICAL_RATIONAL"
        w_f.append(xf)

    alpha_f = []
    for x in raw_alpha:
        xf = _parse_canonical_rat(x)
        if xf is None:
            return "REJECT", "NONCANONICAL_RATIONAL"
        alpha_f.append(xf)

    r_f = []
    for x in raw_r:
        xf = _parse_canonical_rat(x)
        if xf is None:
            return "REJECT", "NONCANONICAL_RATIONAL"
        r_f.append(xf)

    y_f = []
    for x in raw_y:
        xf = _parse_canonical_rat(x)
        if xf is None:
            return "REJECT", "NONCANONICAL_RATIONAL"
        y_f.append(xf)

    d0_f = []
    for row in raw_d0:
        if not isinstance(row, list):
            return "REJECT", "SCHEMA"
        rf = []
        for x in row:
            xf = _parse_canonical_rat(x)
            if xf is None:
                return "REJECT", "NONCANONICAL_RATIONAL"
            rf.append(xf)
        d0_f.append(rf)

    m = len(core_f)
    if m == 0 or len(w_f) != m or len(r_f) != m or len(y_f) != m or len(d0_f) != m:
        return "REJECT", "DIMENSION"

    k = len(alpha_f)
    for row in d0_f:
        if len(row) != k:
            return "REJECT", "DIMENSION"

    for w_i in w_f:
        if w_i <= 0:
            return "REJECT", "NONPOSITIVE_WEIGHT"

    # r == omega - d0 * alpha
    for i in range(m):
        rec_i = sum(d0_f[i][j] * alpha_f[j] for j in range(k))
        if r_f[i] != core_f[i] - rec_i:
            return "REJECT", "RESIDUAL_MISMATCH"

    # sum w_e |r_e| == value
    primal_sum = sum(w_f[i] * abs(r_f[i]) for i in range(m))
    if primal_sum != val_f:
        return "REJECT", "PRIMAL_VALUE_MISMATCH"

    # d0^T * y == 0
    for j in range(k):
        col_dot = sum(d0_f[i][j] * y_f[i] for i in range(m))
        if col_dot != 0:
            return "REJECT", "DUAL_NOT_IN_COKERNEL"

    # |y_e| <= w_e
    for i in range(m):
        if abs(y_f[i]) > w_f[i]:
            return "REJECT", "DUAL_BOUND_VIOLATED"

    # y^T * omega == value
    dual_sum = sum(y_f[i] * core_f[i] for i in range(m))
    if dual_sum != val_f:
        return "REJECT", "DUAL_VALUE_MISMATCH"

    return "ACCEPT", None


def independent_check(
    case_item: Dict[str, Any],
    candidate_or_result: Union[Dict[str, Any], Callable[[Any, Any], Dict[str, Any]]],
) -> Tuple[bool, str]:
    """Independently verifies candidate checker output against clean-room evaluation."""
    if not isinstance(case_item, dict):
        return False, "INDEP_INVALID_TEST_CASE"

    c_case = case_item.get("case")
    c_cert = case_item.get("cert")
    expected_verdict, expected_code = evaluate_phi1_independent(c_case, c_cert)

    if callable(candidate_or_result):
        try:
            res = candidate_or_result(c_case, c_cert)
        except Exception as e:
            return False, f"INDEP_CHECKER_CRASHED: {type(e).__name__}: {str(e)}"
    elif isinstance(candidate_or_result, dict):
        res = candidate_or_result
    else:
        return False, "INDEP_CANDIDATE_NOT_A_DICT"

    if not isinstance(res, dict):
        return False, f"INDEP_RESPONSE_NOT_A_DICT: got {type(res).__name__}"

    cand_verdict = res.get("verdict")
    if cand_verdict != expected_verdict:
        return (
            False,
            f"INDEP_VERDICT_MISMATCH: expected {expected_verdict} ({expected_code}), candidate got {cand_verdict} ({res.get('code')})",
        )

    if expected_verdict == "REJECT" and expected_code and res.get("code") != expected_code:
        return False, f"INDEP_CODE_MISMATCH: expected {expected_code}, got {res.get('code')}"

    return True, "INDEPENDENT_CHECK_PASSED"
