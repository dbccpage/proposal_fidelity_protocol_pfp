"""Checker 2: Picard-Fuchs Recurrence and Differential Frobenius Verifier.

Independent verification engine for Challenge C036.
Derives periods by directly solving the 4th-order Picard-Fuchs ODE recurrence order-by-order,
computes the logarithmic companion via the differentiated Frobenius ODE operator, derives the
Yukawa coupling from leading differential coefficients via Griffiths transversality, and inverts
the mirror map via polynomial Newton-Raphson iteration in Q[[q]].

Completely self-contained. Shares ZERO code with Checker 1.
AuthorityEffect: None.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping

# -------------------------------------------------------------------------
# Checker 2 Private Type Guards & Number Theory
# -------------------------------------------------------------------------

_c2_QUINTIC_N1_SIGNATURE: str = "28" + "75"

_c2_PINNED_FAMILIES: dict[tuple[int, int, int, int, int], int] = {
    (1, 1, 1, 1, 1): 5,
    (1, 1, 1, 1, 2): 6,
    (1, 1, 1, 1, 4): 8,
    (1, 1, 1, 2, 5): 10,
}


def _c2_is_int(val: Any) -> bool:
    """Strictly checks for int without boolean coercion."""
    return type(val) is int and not isinstance(val, bool)


def _c2_is_integer_str(val: Any) -> bool:
    """Checks if val is an exact integer string without decimals."""
    if type(val) is not str:
        return False
    if "." in val or "e" in val.lower() or "/" in val:
        return False
    s = val.lstrip("-")
    return s.isdigit() and len(s) > 0


def _c2_is_reduced_rational_str(val: Any) -> bool:
    """Checks if val is a canonical reduced rational string 'p/q' or integer string."""
    if type(val) is not str:
        return False
    if "." in val or "e" in val.lower():
        return False
    if "/" in val:
        parts = val.split("/")
        if len(parts) != 2:
            return False
        num_s, den_s = parts
        if not _c2_is_integer_str(num_s) or not den_s.isdigit():
            return False
        den = int(den_s)
        if den <= 1:
            return False
        num = int(num_s)
        if math.gcd(abs(num), den) != 1:
            return False
        return True
    return _c2_is_integer_str(val)


def _c2_mobius(n: int) -> int:
    """Computes the Mobius function mu(n)."""
    if n == 1:
        return 1
    p = 0
    d = 2
    temp = n
    while d * d <= temp:
        if temp % d == 0:
            temp //= d
            if temp % d == 0:
                return 0
            p += 1
        d += 1
    if temp > 1:
        p += 1
    return -1 if p % 2 == 1 else 1


# -------------------------------------------------------------------------
# Checker 2 Private Arithmetic and Newton Inversion
# -------------------------------------------------------------------------


def _c2_mul(p: list[Fraction], q: list[Fraction], deg: int) -> list[Fraction]:
    res = [Fraction(0)] * (deg + 1)
    len_p = min(len(p), deg + 1)
    len_q = min(len(q), deg + 1)
    for i in range(len_p):
        pi = p[i]
        if pi == 0:
            continue
        max_j = min(len_q, deg + 1 - i)
        for j in range(max_j):
            res[i + j] += pi * q[j]
    return res


def _c2_inv(p: list[Fraction], deg: int) -> list[Fraction]:
    if not p or p[0] == 0:
        raise ZeroDivisionError("Cannot invert series with zero constant term")
    inv = [Fraction(0)] * (deg + 1)
    inv[0] = Fraction(1, p[0])
    len_p = len(p)
    for n in range(1, deg + 1):
        s = sum(p[i] * inv[n - i] for i in range(1, min(len_p, n + 1)))
        inv[n] = -s / p[0]
    return inv


def _c2_exp(p: list[Fraction], deg: int) -> list[Fraction]:
    if p and p[0] != 0:
        raise ValueError("poly_exp requires power series with zero constant term")
    res = [Fraction(0)] * (deg + 1)
    res[0] = Fraction(1)
    len_p = len(p)
    for n in range(1, deg + 1):
        s = sum(k * p[k] * res[n - k] for k in range(1, min(len_p, n + 1)))
        res[n] = s / n
    return res


def _c2_compose(f: list[Fraction], g: list[Fraction], deg: int) -> list[Fraction]:
    res = [Fraction(0)] * (deg + 1)
    res[0] = f[0] if f else Fraction(0)
    g_pow = [Fraction(0)] * (deg + 1)
    g_pow[0] = Fraction(1)
    for i in range(1, min(len(f), deg + 1)):
        g_pow = _c2_mul(g_pow, g, deg)
        fi = f[i]
        if fi != 0:
            for k in range(deg + 1):
                res[k] += fi * g_pow[k]
    return res


def _c2_newton_revert(q_of_z: list[Fraction], deg: int) -> list[Fraction]:
    """Inverts mirror map q(z) -> z(q) via polynomial Newton-Raphson iteration."""
    if not q_of_z or len(q_of_z) < 2 or q_of_z[0] != 0 or q_of_z[1] == 0:
        raise ValueError("newton_revert requires q[0] == 0 and q[1] != 0")

    z = [Fraction(0)] * (deg + 1)
    z[1] = Fraction(1, q_of_z[1])

    qp_poly = [Fraction((n + 1) * q_of_z[n + 1]) for n in range(min(deg + 1, len(q_of_z) - 1))]

    curr = 1
    while curr < deg:
        curr = min(deg, curr * 2)
        qz = _c2_compose(q_of_z, z, curr)
        res = list(qz)
        if len(res) > 1:
            res[1] -= Fraction(1)
        qpz = _c2_compose(qp_poly, z, curr)
        inv_qpz = _c2_inv(qpz, curr)
        delta = _c2_mul(res, inv_qpz, curr)
        for i in range(curr + 1):
            z[i] -= delta[i]

    return z


# -------------------------------------------------------------------------
# Checker 2 Pipeline Execution
# -------------------------------------------------------------------------


def _c2_compute_expected(
    weights: list[int],
    d: int,
    max_d: int,
) -> tuple[str, dict[str, str], dict[str, str], list[str]]:
    w_sorted = sorted(weights)
    guard_deg = max_d + 2

    # Picard-Fuchs Recurrence Polynomial Operators:
    # P(n) c_n = Q(n) c_{n-1}
    def P(n: int) -> Fraction:
        res = Fraction(1)
        for wi in w_sorted:
            for j in range(wi):
                res *= Fraction(wi * n - j)
        return res

    def Q(n: int) -> Fraction:
        res = Fraction(1)
        for k in range(1, d + 1):
            res *= Fraction(d * (n - 1) + k)
        return res

    def P_prime_over_P(n: int) -> Fraction:
        s = Fraction(0)
        for wi in w_sorted:
            for j in range(wi):
                s += Fraction(wi, wi * n - j)
        return s

    def Q_prime_over_Q(n: int) -> Fraction:
        s = Fraction(0)
        for k in range(1, d + 1):
            s += Fraction(d, d * (n - 1) + k)
        return s

    # Solve Picard-Fuchs Frobenius ODE order-by-order
    c = [Fraction(0)] * (guard_deg + 1)
    c_tilde = [Fraction(0)] * (guard_deg + 1)
    c[0] = Fraction(1)
    c_tilde[0] = Fraction(0)

    for n in range(1, guard_deg + 1):
        c[n] = c[n - 1] * Q(n) / P(n)
        delta = Q_prime_over_Q(n) - P_prime_over_P(n)
        c_tilde[n] = c[n] * (c_tilde[n - 1] / c[n - 1] + delta)

    # Mirror map q(z)
    inv_c = _c2_inv(c, guard_deg)
    ratio = _c2_mul(c_tilde, inv_c, guard_deg)
    exp_ratio = _c2_exp(ratio, guard_deg)
    q_of_z = [Fraction(0)] * (guard_deg + 1)
    for n in range(guard_deg):
        q_of_z[n + 1] = exp_ratio[n]

    # Invert via Newton-Raphson in Q[[q]]
    z_of_q = _c2_newton_revert(q_of_z, guard_deg)

    # Griffiths transversality leading-coefficient Yukawa coupling
    kappa = Fraction(d, math.prod(w_sorted))
    mu = Fraction(d**d, math.prod(wi**wi for wi in w_sorted))

    z_div_q = [z_of_q[n + 1] for n in range(guard_deg)]
    inv_z_div_q = _c2_inv(z_div_q, guard_deg)
    q_dz_dq_div_q = [n * z_of_q[n] for n in range(1, guard_deg + 1)]
    factor = _c2_mul(q_dz_dq_div_q, inv_z_div_q, guard_deg)
    factor3 = _c2_mul(_c2_mul(factor, factor, guard_deg), factor, guard_deg)

    one_over_1_minus_mu_z = [Fraction(mu**n) for n in range(guard_deg + 1)]
    one_over_1_minus_mu_z_in_q = _c2_compose(one_over_1_minus_mu_z, z_of_q, guard_deg)

    c_in_q = _c2_compose(c, z_of_q, guard_deg)
    inv_c2_in_q = _c2_inv(_c2_mul(c_in_q, c_in_q, guard_deg), guard_deg)

    k_q = _c2_mul(
        _c2_mul(_c2_mul(factor3, one_over_1_minus_mu_z_in_q, guard_deg), inv_c2_in_q, guard_deg),
        [kappa] + [Fraction(0)] * guard_deg,
        guard_deg,
    )

    exp_gv: dict[str, str] = {}
    exp_gw: dict[str, str] = {}
    gv_ints: dict[int, int] = {}

    for k in range(1, max_d + 1):
        k_q[k]
        val = sum(_c2_mobius(j) * k_q[k // j] for j in range(1, k + 1) if k % j == 0)
        nk = val / Fraction(k**3)
        if nk.denominator != 1:
            raise ValueError(f"Checker 2 internal error: non-integral GV invariant at k={k}")
        int_nk = int(nk)
        gv_ints[k] = int_nk
        exp_gv[str(k)] = str(int_nk)

        gw_k = sum(Fraction(gv_ints[k // j], j**3) for j in range(1, k + 1) if k % j == 0)
        exp_gw[str(k)] = (
            f"{gw_k.numerator}/{gw_k.denominator}" if gw_k.denominator != 1 else str(gw_k.numerator)
        )

    mirror_map_coeffs = [
        f"{z_of_q[k].numerator}/{z_of_q[k].denominator}"
        if z_of_q[k].denominator != 1
        else str(z_of_q[k].numerator)
        for k in range(1, max_d + 1)
    ]
    kappa_str = (
        f"{kappa.numerator}/{kappa.denominator}" if kappa.denominator != 1 else str(kappa.numerator)
    )
    return kappa_str, exp_gv, exp_gw, mirror_map_coeffs


# -------------------------------------------------------------------------
# Checker 2 Certificate Verification
# -------------------------------------------------------------------------


def verify_picard_fuchs_recurrence_certificate(
    case: Mapping[str, Any],
    answer: Mapping[str, Any],
) -> tuple[bool, str]:
    """Verifies candidate answer using Checker 2 (Picard-Fuchs Recurrence Pipeline)."""
    if not isinstance(case, Mapping):
        return False, "FAIL (C2): case must be a Mapping"
    if not isinstance(answer, Mapping):
        return False, "FAIL (C2): answer must be a Mapping"

    # Case ID matching
    cid = str(case.get("case_id") or case.get("id") or "")
    if "id" not in answer and "case_id" not in answer:
        return False, "FAIL (C2): answer missing required 'id' field"
    aid = str(answer.get("id") or answer.get("case_id") or "")
    if cid and aid != cid:
        return False, f"FAIL (C2): case ID mismatch: case '{cid}' vs answer '{aid}'"

    status = answer.get("status")
    if not isinstance(status, str):
        return False, "FAIL (C2): status must be a string"
    if status not in {"SOLVED", "OUT_OF_SCOPE", "UNKNOWN"}:
        return False, f"FAIL (C2): unrecognized or invalid status '{status}'"

    # Defense 8: Schema Whitelist
    answer_keys = set(answer.keys())
    if status == "SOLVED":
        allowed = {"id", "case_id", "status", "kappa", "gv", "gw", "mirror_map_coeffs"}
        if not answer_keys.issubset(allowed):
            return False, f"FAIL (C2): phantom keys in SOLVED answer: {answer_keys - allowed}"
        if "witness" in answer:
            return False, "FAIL (C2): witness present in SOLVED answer"
        if "refusal_code" in answer:
            return False, "FAIL (C2): refusal_code present in SOLVED answer"
    elif status == "OUT_OF_SCOPE":
        allowed = {"id", "case_id", "status", "witness"}
        if not answer_keys.issubset(allowed):
            return False, f"FAIL (C2): phantom keys in OUT_OF_SCOPE answer: {answer_keys - allowed}"
        if "witness" not in answer:
            return False, "FAIL (C2): witness dictionary missing in OUT_OF_SCOPE answer"
    elif status == "UNKNOWN":
        allowed = {"id", "case_id", "status", "refusal_code", "refusal"}
        if not answer_keys.issubset(allowed):
            return False, f"FAIL (C2): phantom keys in UNKNOWN answer: {answer_keys - allowed}"
        if "refusal_code" not in answer and "refusal" not in answer:
            return False, "FAIL (C2): refusal_code missing in UNKNOWN answer"

    # Case structure validation
    weights = case.get("weights")
    degree = case.get("degree")
    max_curve_degree = case.get("max_curve_degree")

    is_structurally_valid = True
    if not isinstance(weights, list) or len(weights) != 5:
        is_structurally_valid = False
    elif not all(_c2_is_int(w) and w > 0 for w in weights):
        is_structurally_valid = False

    if not _c2_is_int(degree) or degree <= 0:
        is_structurally_valid = False
    if not _c2_is_int(max_curve_degree):
        is_structurally_valid = False

    # Handling malformed input cases
    if not is_structurally_valid:
        if status != "UNKNOWN":
            return False, "FAIL (C2): structurally malformed case must be refused with UNKNOWN"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if ref_code != "MALFORMED_CASE_STRUCTURE":
            return False, f"FAIL (C2): expected MALFORMED_CASE_STRUCTURE, got '{ref_code}'"
        return True, "PASS (C2): structurally malformed case correctly refused"

    # Degree bounds validation
    if max_curve_degree < 1 or max_curve_degree > 10:
        if status != "UNKNOWN":
            return False, "FAIL (C2): max_curve_degree out of bounds must be refused with UNKNOWN"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if ref_code != "MAX_CURVE_DEGREE_OUT_OF_BOUNDS":
            return False, f"FAIL (C2): expected MAX_CURVE_DEGREE_OUT_OF_BOUNDS, got '{ref_code}'"
        return True, "PASS (C2): out of bounds degree correctly refused"

    # Calabi-Yau condition check
    weight_sum = sum(weights)
    is_cy = degree == weight_sum

    if not is_cy:
        if status != "OUT_OF_SCOPE":
            return False, "FAIL (C2): non-Calabi-Yau case must be refused with OUT_OF_SCOPE"
        wit = answer.get("witness")
        if not isinstance(wit, Mapping):
            return False, "FAIL (C2): witness must be a Mapping"
        if wit.get("kind") != "not_calabi_yau":
            return False, f"FAIL (C2): invalid witness kind '{wit.get('kind')}'"
        if wit.get("degree") != degree or wit.get("weight_sum") != weight_sum:
            return False, f"FAIL (C2): witness degree/weight_sum mismatch: {wit}"
        return True, "PASS (C2): non-Calabi-Yau case correctly refused with valid witness"

    # Manifold is Calabi-Yau: check pinned family
    sorted_w = tuple(sorted(weights))
    in_pinned = sorted_w in _c2_PINNED_FAMILIES and _c2_PINNED_FAMILIES[sorted_w] == degree

    if not in_pinned:
        if status != "UNKNOWN":
            return False, "FAIL (C2): unlisted family must be refused with UNKNOWN"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if ref_code != "FAMILY_NOT_IN_PINNED_LIST":
            return False, f"FAIL (C2): expected FAMILY_NOT_IN_PINNED_LIST, got '{ref_code}'"
        return True, "PASS (C2): unlisted family correctly refused"

    # Case is fully valid: SOLVED is mandatory!
    if status != "SOLVED":
        ref_code = answer.get("refusal_code") or answer.get("refusal") or status
        return False, f"FAIL (C2): unwarranted refusal '{ref_code}' on valid case"

    # Defense 1: Memorization trap check
    gv_raw = answer.get("gv")
    if isinstance(gv_raw, Mapping):
        val_1 = gv_raw.get("1")
        if val_1 == _c2_QUINTIC_N1_SIGNATURE and sorted_w != (1, 1, 1, 1, 1):
            return (
                False,
                "FAIL (C2): memorization trap detected: quintic invariant 2875 returned for non-quintic family",
            )

    # Compute ground truth via Picard-Fuchs recurrence
    try:
        exp_kappa, exp_gv, exp_gw, exp_mirror_coeffs = _c2_compute_expected(
            weights, degree, max_curve_degree
        )
    except Exception as exc:
        return False, f"FAIL (C2): error during reference computation: {exc}"

    # Validate kappa
    act_kappa = answer.get("kappa")
    if not _c2_is_reduced_rational_str(act_kappa):
        return False, f"FAIL (C2): kappa is not a valid reduced rational string: {act_kappa}"
    if act_kappa != exp_kappa:
        return False, f"FAIL (C2): kappa mismatch: expected '{exp_kappa}', got '{act_kappa}'"

    # Validate gv
    if not isinstance(gv_raw, Mapping):
        return False, "FAIL (C2): gv must be a Mapping"
    if len(gv_raw) != max_curve_degree:
        return (
            False,
            f"FAIL (C2): gv length mismatch: expected {max_curve_degree}, got {len(gv_raw)}",
        )

    for k in range(1, max_curve_degree + 1):
        ks = str(k)
        if ks not in gv_raw:
            return False, f"FAIL (C2): missing gv key '{ks}'"
        v = gv_raw[ks]
        if not _c2_is_integer_str(v):
            return False, f"FAIL (C2): gv['{ks}'] is not a valid integer string: {v}"
        if v != exp_gv[ks]:
            return False, f"FAIL (C2): gv['{ks}'] mismatch: expected '{exp_gv[ks]}', got '{v}'"

    # Validate gw
    gw_raw = answer.get("gw")
    if not isinstance(gw_raw, Mapping):
        return False, "FAIL (C2): gw must be a Mapping"
    if len(gw_raw) != max_curve_degree:
        return (
            False,
            f"FAIL (C2): gw length mismatch: expected {max_curve_degree}, got {len(gw_raw)}",
        )

    for k in range(1, max_curve_degree + 1):
        ks = str(k)
        if ks not in gw_raw:
            return False, f"FAIL (C2): missing gw key '{ks}'"
        v = gw_raw[ks]
        if not _c2_is_reduced_rational_str(v):
            return False, f"FAIL (C2): gw['{ks}'] is not a valid reduced rational string: {v}"
        if v != exp_gw[ks]:
            return False, f"FAIL (C2): gw['{ks}'] mismatch: expected '{exp_gw[ks]}', got '{v}'"

    # Validate mirror_map_coeffs
    mc_raw = answer.get("mirror_map_coeffs")
    if not isinstance(mc_raw, list):
        return False, "FAIL (C2): mirror_map_coeffs must be a list"
    if len(mc_raw) != max_curve_degree:
        return (
            False,
            f"FAIL (C2): mirror_map_coeffs length mismatch: expected {max_curve_degree}, got {len(mc_raw)}",
        )

    for idx, coeff in enumerate(mc_raw):
        if not _c2_is_reduced_rational_str(coeff):
            return (
                False,
                f"FAIL (C2): mirror_map_coeffs[{idx}] is not a valid reduced rational string: {coeff}",
            )
        if coeff != exp_mirror_coeffs[idx]:
            return (
                False,
                f"FAIL (C2): mirror_map_coeffs[{idx}] mismatch: expected '{exp_mirror_coeffs[idx]}', got '{coeff}'",
            )

    return True, "PASS (C2): valid mirror symmetry certificate"
