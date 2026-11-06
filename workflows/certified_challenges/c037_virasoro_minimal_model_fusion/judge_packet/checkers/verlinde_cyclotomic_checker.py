"""Checker 1: Verlinde Cyclotomic Algebraic Verifier.

Evaluates fusion coefficients directly from the Verlinde formula using exact
cyclotomic arithmetic over Q(zeta_N). Certifies that N_{ij}^k in Z_{>=0},
verifies central charge and conformal weights as reduced rational strings,
and validates canonical Kac label identification.

Shares ZERO code with Checker 2.
AuthorityEffect: None.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping

# -------------------------------------------------------------------------
# Checker 1 Private Type Guards
# -------------------------------------------------------------------------


def _c1_is_int(val: Any) -> bool:
    """Strict check for int, rejecting bool."""
    return type(val) is int and not isinstance(val, bool)


def _c1_is_integer_str(val: Any) -> bool:
    """Checks if val is an exact integer string without decimals."""
    if type(val) is not str:
        return False
    if "." in val or "e" in val.lower() or "/" in val:
        return False
    s = val.lstrip("-")
    return s.isdigit() and len(s) > 0


def _c1_is_reduced_rational_str(val: Any) -> bool:
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
        if not _c1_is_integer_str(num_s) or not den_s.isdigit():
            return False
        den = int(den_s)
        if den <= 1:
            return False
        num = int(num_s)
        if math.gcd(abs(num), den) != 1:
            return False
        return True
    return _c1_is_integer_str(val)


def _c1_to_reduced_str(frac: Fraction) -> str:
    """Formats a Fraction as a canonical reduced string."""
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


# -------------------------------------------------------------------------
# Checker 1 Exact Cyclotomic Polynomial Engine
# -------------------------------------------------------------------------


def _c1_poly_div(p: list[int], q: list[int]) -> list[int]:
    """Exact division of monic polynomial q into p over Z[x]."""
    rem = list(p)
    deg_p = len(p) - 1
    deg_q = len(q) - 1
    quot = [0] * (deg_p - deg_q + 1)
    for i in range(deg_p - deg_q, -1, -1):
        c = rem[i + deg_q]
        quot[i] = c
        for j in range(deg_q + 1):
            rem[i + j] -= c * q[j]
    while len(quot) > 1 and quot[-1] == 0:
        quot.pop()
    return quot


def _c1_poly_mul(p: list[int], q: list[int]) -> list[int]:
    """Multiplication of polynomials over Z[x]."""
    res = [0] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            res[i + j] += a * b
    return res


_C1_CYCLOTOMIC_CACHE: dict[int, list[int]] = {}


def _c1_get_cyclotomic_poly(n: int) -> list[int]:
    """Computes the n-th cyclotomic polynomial Phi_n(x)."""
    if n in _C1_CYCLOTOMIC_CACHE:
        return _C1_CYCLOTOMIC_CACHE[n]
    num = [-1] + [0] * (n - 1) + [1]
    denom = [1]
    for d in range(1, n):
        if n % d == 0:
            denom = _c1_poly_mul(denom, _c1_get_cyclotomic_poly(d))
    phi = _c1_poly_div(num, denom)
    _C1_CYCLOTOMIC_CACHE[n] = phi
    return phi


def _c1_reduce_cyclotomic(poly: list[Fraction], phi: list[int]) -> list[Fraction]:
    """Reduces a polynomial in Fraction over Q[x] modulo monic Phi(x)."""
    deg_phi = len(phi) - 1
    deg_p = len(poly) - 1
    if deg_p < deg_phi:
        res = [Fraction(c) for c in poly] + [Fraction(0)] * (deg_phi - len(poly))
        return res[:deg_phi]
    rem = [Fraction(c) for c in poly]
    for i in range(deg_p - deg_phi, -1, -1):
        c = rem[i + deg_phi]
        if c != 0:
            for j in range(deg_phi + 1):
                rem[i + j] -= c * phi[j]
    return rem[:deg_phi]


def _c1_canonical_kac_label(p: int, p_prime: int, r: int, s: int) -> tuple[int, int]:
    """Applies canonical selection rule (s, r) <= (p - s, p' - r) for Kac label identification."""
    if (s, r) <= (p - s, p_prime - r):
        return (r, s)
    return (p_prime - r, p - s)


# -------------------------------------------------------------------------
# Checker 1 Verlinde Exact Solvers with Caching
# -------------------------------------------------------------------------

_C1_SU2_CACHE: dict[int, tuple[str, list[dict[str, Any]], list[list[Any]]]] = {}
_C1_MINIMAL_CACHE: dict[tuple[int, int], tuple[str, list[dict[str, Any]], list[list[Any]]]] = {}


def _c1_compute_su2_verlinde(
    k: int,
) -> tuple[str, list[dict[str, Any]], list[list[Any]]]:
    """Computes ground-truth SU(2)_k data via exact cyclotomic Verlinde evaluation."""
    if k in _C1_SU2_CACHE:
        return _C1_SU2_CACHE[k]

    K = k + 2
    N = 2 * K
    phi = _c1_get_cyclotomic_poly(N)

    c_str = _c1_to_reduced_str(Fraction(3 * k, k + 2))
    primaries = []
    for a in range(k + 1):
        h_frac = Fraction(a * (a + 2), 4 * (k + 2))
        primaries.append({"label": [a], "h": _c1_to_reduced_str(h_frac)})

    fusion = []
    pref = Fraction(1, 4 * K)
    for a in range(k + 1):
        for b in range(a, k + 1):
            for c in range(k + 1):
                poly = [Fraction(0)] * N
                for m in range(k + 1):
                    for j in range(a + 1):
                        A = (a - 2 * j) * (m + 1)
                        B = (b - c) * (m + 1)
                        C_ang = (b + c + 2) * (m + 1)
                        for sign, X in [
                            (1, A - B),
                            (1, A + B),
                            (-1, A - C_ang),
                            (-1, A + C_ang),
                        ]:
                            poly[X % N] += sign * pref
                            poly[(-X) % N] += sign * pref

                rem = _c1_reduce_cyclotomic(poly, phi)
                for idx in range(1, len(rem)):
                    if rem[idx] != 0:
                        raise ValueError(f"Non-zero cyclotomic coordinate at index {idx}")
                val = rem[0]
                if val.denominator != 1 or val < 0:
                    raise ValueError(f"Non-integer Verlinde result: {val}")
                n_int = int(val)
                if n_int > 0:
                    fusion.append([[a], [b], [c], n_int])

    res = (c_str, primaries, fusion)
    _C1_SU2_CACHE[k] = res
    return res


def _c1_compute_minimal_verlinde(
    p: int, p_prime: int
) -> tuple[str, list[dict[str, Any]], list[list[Any]]]:
    """Computes ground-truth minimal model data via exact cyclotomic Verlinde evaluation."""
    key = (p, p_prime)
    if key in _C1_MINIMAL_CACHE:
        return _C1_MINIMAL_CACHE[key]

    N = 2 * p * p_prime
    phi = _c1_get_cyclotomic_poly(N)

    c_frac = Fraction(1) - Fraction(6 * (p - p_prime) ** 2, p * p_prime)
    c_str = _c1_to_reduced_str(c_frac)

    # Physical primaries with canonical representative
    prim_reps = []
    for r in range(1, p_prime):
        for s in range(1, p):
            rep = _c1_canonical_kac_label(p, p_prime, r, s)
            if rep not in prim_reps:
                prim_reps.append(rep)
    prim_reps.sort()

    primaries = []
    for r, s in prim_reps:
        h_frac = Fraction((p * r - p_prime * s) ** 2 - (p - p_prime) ** 2, 4 * p * p_prime)
        primaries.append({"label": [r, s], "h": _c1_to_reduced_str(h_frac)})

    fusion = []
    pref_base = Fraction(8, p * p_prime) * Fraction(1, 16)  # = 1 / (2 * p * p_prime)

    for i_idx, i_pair in enumerate(prim_reps):
        for j_idx in range(i_idx, len(prim_reps)):
            j_pair = prim_reps[j_idx]
            for l_pair in prim_reps:
                poly = [Fraction(0)] * N
                for rho, sigma in prim_reps:
                    sign_val = (-1) ** (
                        (i_pair[1] + j_pair[1] + l_pair[1] - 1) * rho
                        + (i_pair[0] + j_pair[0] + l_pair[0] - 1) * sigma
                    )
                    theta_r = (p * p * rho) % N
                    theta_s = (p_prime * p_prime * sigma) % N

                    r_cosines = []
                    for a in range(i_pair[0]):
                        A = (i_pair[0] - 1 - 2 * a) * theta_r
                        for sign_r, D in [
                            (1, (j_pair[0] - l_pair[0]) * theta_r),
                            (-1, (j_pair[0] + l_pair[0]) * theta_r),
                        ]:
                            r_cosines.append((sign_r, A - D))
                            r_cosines.append((sign_r, A + D))

                    s_cosines = []
                    for b in range(i_pair[1]):
                        B = (i_pair[1] - 1 - 2 * b) * theta_s
                        for sign_s, E in [
                            (1, (j_pair[1] - l_pair[1]) * theta_s),
                            (-1, (j_pair[1] + l_pair[1]) * theta_s),
                        ]:
                            s_cosines.append((sign_s, B - E))
                            s_cosines.append((sign_s, B + E))

                    factor = pref_base * Fraction(sign_val, 1) * Fraction(1, 4)
                    for sign_r, ang_r in r_cosines:
                        for sign_s, ang_s in s_cosines:
                            final_factor = factor * sign_r * sign_s
                            for X in [ang_r - ang_s, ang_r + ang_s]:
                                poly[X % N] += final_factor
                                poly[(-X) % N] += final_factor

                rem = _c1_reduce_cyclotomic(poly, phi)
                for idx in range(1, len(rem)):
                    if rem[idx] != 0:
                        raise ValueError(f"Non-zero cyclotomic coordinate at index {idx}")
                val = rem[0]
                if val.denominator != 1 or val < 0:
                    raise ValueError(f"Non-integer Verlinde result: {val}")
                n_int = int(val)
                if n_int > 0:
                    fusion.append([list(i_pair), list(j_pair), list(l_pair), n_int])

    res = (c_str, primaries, fusion)
    _C1_MINIMAL_CACHE[key] = res
    return res


# -------------------------------------------------------------------------
# Checker 1 Certificate Verifier
# -------------------------------------------------------------------------


def verify_verlinde_cyclotomic_certificate(
    case: Mapping[str, Any],
    answer: Mapping[str, Any],
) -> tuple[bool, str]:
    """Verifies candidate answer using Checker 1 (exact cyclotomic Verlinde pipeline)."""
    if not isinstance(case, Mapping) or not isinstance(answer, Mapping):
        return False, "FAIL (C1): case and answer must be Mappings"

    status = answer.get("status")
    if type(status) is not str or status not in {"SOLVED", "OUT_OF_SCOPE", "UNKNOWN"}:
        return False, f"FAIL (C1): invalid status '{status}'"

    # Anti-bypass: boolean injection guards on case
    for k_field in ("k", "p", "p_prime", "model", "case_id", "id"):
        if k_field in case and isinstance(case[k_field], bool):
            if status != "UNKNOWN":
                return False, "FAIL (C1): boolean injection in case must be refused with UNKNOWN"
            return True, "PASS (C1): boolean injection correctly refused"

    # Schema Whitelist
    answer_keys = set(answer.keys())
    if "id" not in answer_keys and "case_id" not in answer_keys:
        return False, "FAIL (C1): missing mandatory id field"

    if status == "SOLVED":
        allowed = {"id", "case_id", "status", "central_charge", "primaries", "fusion"}
        if not answer_keys.issubset(allowed):
            return (
                False,
                f"FAIL (C1): phantom keys in SOLVED answer: {answer_keys - allowed}",
            )
        if not {"status", "central_charge", "primaries", "fusion"}.issubset(answer_keys):
            return False, "FAIL (C1): missing mandatory SOLVED keys"
    elif status == "OUT_OF_SCOPE":
        allowed = {"id", "case_id", "status", "witness"}
        if not answer_keys.issubset(allowed):
            return (
                False,
                f"FAIL (C1): phantom keys in OUT_OF_SCOPE answer: {answer_keys - allowed}",
            )
        if "witness" not in answer:
            return False, "FAIL (C1): witness missing in OUT_OF_SCOPE answer"
    elif status == "UNKNOWN":
        allowed = {"id", "case_id", "status", "refusal_code", "refusal"}
        if not answer_keys.issubset(allowed):
            return (
                False,
                f"FAIL (C1): phantom keys in UNKNOWN answer: {answer_keys - allowed}",
            )
        if "refusal_code" not in answer and "refusal" not in answer:
            return False, "FAIL (C1): refusal_code missing in UNKNOWN answer"

    model = case.get("model")
    if model not in {"su2", "minimal"}:
        if status != "UNKNOWN":
            return False, "FAIL (C1): invalid model must be refused with UNKNOWN"
        return True, "PASS (C1): invalid model refused"

    if model == "su2":
        k = case.get("k")
        if not _c1_is_int(k):
            if status != "UNKNOWN":
                return False, "FAIL (C1): non-int level must be refused"
            return True, "PASS (C1): non-int level refused"
        if k < 1 or k > 20:
            if status != "UNKNOWN":
                return False, "FAIL (C1): level out of bounds must be refused with UNKNOWN"
            ref = answer.get("refusal_code") or answer.get("refusal")
            if ref != "LEVEL_OUT_OF_BOUNDS":
                return False, f"FAIL (C1): expected LEVEL_OUT_OF_BOUNDS, got '{ref}'"
            return True, "PASS (C1): out-of-bounds level correctly refused"

        if status != "SOLVED":
            return False, f"FAIL (C1): unwarranted refusal on valid SU(2)_{k} case"

        # Compute ground truth
        exp_c, exp_prim, exp_fus = _c1_compute_su2_verlinde(k)

        # Validate central charge
        act_c = answer.get("central_charge")
        if not _c1_is_reduced_rational_str(act_c):
            return False, f"FAIL (C1): central_charge is not a reduced rational string: {act_c}"
        if act_c != exp_c:
            return False, f"FAIL (C1): central_charge mismatch: expected '{exp_c}', got '{act_c}'"

        # Validate primaries
        act_prim = answer.get("primaries")
        if not isinstance(act_prim, list) or len(act_prim) != len(exp_prim):
            return (
                False,
                f"FAIL (C1): primaries count mismatch: expected {len(exp_prim)}, got {len(act_prim) if isinstance(act_prim, list) else None}",
            )
        seen_prim_labels = set()
        for idx, (exp_p, act_p) in enumerate(zip(exp_prim, act_prim)):
            if not isinstance(act_p, Mapping):
                return False, f"FAIL (C1): primary at {idx} must be a Mapping"
            if set(act_p.keys()) != {"label", "h"}:
                return False, f"FAIL (C1): primary {idx} has invalid keys: {set(act_p.keys())}"
            lbl = act_p.get("label")
            if not isinstance(lbl, list) or len(lbl) != 1 or not _c1_is_int(lbl[0]):
                return False, f"FAIL (C1): primary {idx} label must be a 1-element integer list"
            tup_lbl = tuple(lbl)
            if tup_lbl in seen_prim_labels:
                return False, f"FAIL (C1): duplicate primary label {lbl}"
            seen_prim_labels.add(tup_lbl)

            if lbl != exp_p["label"]:
                return (
                    False,
                    f"FAIL (C1): primary {idx} label mismatch: expected {exp_p['label']}, got {lbl}",
                )
            h_val = act_p.get("h")
            if not _c1_is_reduced_rational_str(h_val):
                return False, f"FAIL (C1): primary {idx} h is not reduced rational string: {h_val}"
            if h_val != exp_p["h"]:
                return (
                    False,
                    f"FAIL (C1): primary {idx} h mismatch: expected '{exp_p['h']}', got '{h_val}'",
                )

        # Validate fusion rules
        act_fus = answer.get("fusion")
        if not isinstance(act_fus, list):
            return False, "FAIL (C1): fusion must be a list"
        if len(act_fus) != len(exp_fus):
            return (
                False,
                f"FAIL (C1): fusion rules count mismatch: expected {len(exp_fus)}, got {len(act_fus)}",
            )

        def _to_su2_tuple(item: list[Any]) -> tuple:
            return (tuple(item[0]), tuple(item[1]), tuple(item[2]), item[3])

        exp_fus_set = {_to_su2_tuple(item) for item in exp_fus}
        act_fus_set = set()
        for idx, item in enumerate(act_fus):
            if not isinstance(item, list) or len(item) != 4:
                return False, f"FAIL (C1): fusion rule at {idx} must be a 4-element list"
            p1, p2, p3, n = item
            if (
                not (isinstance(p1, list) and len(p1) == 1 and _c1_is_int(p1[0]))
                or not (isinstance(p2, list) and len(p2) == 1 and _c1_is_int(p2[0]))
                or not (isinstance(p3, list) and len(p3) == 1 and _c1_is_int(p3[0]))
                or not _c1_is_int(n)
            ):
                return False, "FAIL (C1): fusion rule elements must be integer lists and int coeff"
            if p1[0] > p2[0]:
                return (
                    False,
                    f"FAIL (C1): fusion rule [{p1}, {p2}, {p3}, {n}] violates canonical ordering a <= b",
                )
            if n <= 0:
                return False, "FAIL (C1): fusion coefficient must be strictly positive"
            tup = (tuple(p1), tuple(p2), tuple(p3), n)
            if tup in act_fus_set:
                return False, f"FAIL (C1): duplicate fusion rule: {item}"
            act_fus_set.add(tup)

        if act_fus_set != exp_fus_set:
            diff_missing = exp_fus_set - act_fus_set
            diff_spurious = act_fus_set - exp_fus_set
            return (
                False,
                f"FAIL (C1): fusion mismatch. Missing: {diff_missing}, Spurious: {diff_spurious}",
            )

        return True, "PASS (C1): valid SU(2)_k Verlinde certificate"

    elif model == "minimal":
        p = case.get("p")
        p_prime = case.get("p_prime")
        if not (_c1_is_int(p) and _c1_is_int(p_prime)):
            if status != "UNKNOWN":
                return False, "FAIL (C1): non-int p/p_prime must be refused"
            return True, "PASS (C1): non-int parameters refused"

        # Out-of-scope validation: non-coprime or p_prime < 2
        if p_prime < 2:
            if status != "OUT_OF_SCOPE":
                return False, "FAIL (C1): p_prime < 2 must be refused with OUT_OF_SCOPE"
            wit = answer.get("witness")
            if not isinstance(wit, Mapping) or wit.get("kind") != "invalid_p_prime":
                return False, f"FAIL (C1): expected invalid_p_prime witness: {wit}"
            return True, "PASS (C1): valid OUT_OF_SCOPE invalid_p_prime witness"

        gcd_val = math.gcd(p, p_prime)
        if gcd_val != 1:
            if status != "OUT_OF_SCOPE":
                return False, "FAIL (C1): non-coprime (p, p') must be refused with OUT_OF_SCOPE"
            wit = answer.get("witness")
            if not isinstance(wit, Mapping):
                return False, "FAIL (C1): witness must be a Mapping"
            if wit.get("kind") != "not_coprime" or wit.get("gcd") != gcd_val:
                return False, f"FAIL (C1): invalid not_coprime witness: {wit}"
            return True, "PASS (C1): valid OUT_OF_SCOPE witness"

        # Bounds check: p <= p_prime or p > 13
        if p <= p_prime or p > 13:
            if status != "UNKNOWN":
                return (
                    False,
                    f"FAIL (C1): p={p}, p_prime={p_prime} out of bounds must be refused with UNKNOWN",
                )
            ref = answer.get("refusal_code") or answer.get("refusal")
            if ref not in ("LEVEL_OUT_OF_BOUNDS", "P_OUT_OF_BOUNDS"):
                return False, f"FAIL (C1): expected LEVEL_OUT_OF_BOUNDS, got '{ref}'"
            return True, "PASS (C1): parameters out of bounds correctly refused"

        if status != "SOLVED":
            return False, f"FAIL (C1): unwarranted refusal on valid minimal model M({p}, {p_prime})"

        # Compute ground truth
        exp_c, exp_prim, exp_fus = _c1_compute_minimal_verlinde(p, p_prime)

        # Validate central charge
        act_c = answer.get("central_charge")
        if not _c1_is_reduced_rational_str(act_c):
            return False, f"FAIL (C1): central_charge is not a reduced rational string: {act_c}"
        if act_c != exp_c:
            return False, f"FAIL (C1): central_charge mismatch: expected '{exp_c}', got '{act_c}'"

        # Validate primaries
        act_prim = answer.get("primaries")
        if not isinstance(act_prim, list) or len(act_prim) != len(exp_prim):
            return (
                False,
                f"FAIL (C1): primaries count mismatch: expected {len(exp_prim)}, got {len(act_prim) if isinstance(act_prim, list) else None}",
            )

        # Kac table double counting and canonical representative checks
        seen_labels = set()
        for idx, (exp_p, act_p) in enumerate(zip(exp_prim, act_prim)):
            if not isinstance(act_p, Mapping):
                return False, f"FAIL (C1): primary at {idx} must be a Mapping"
            if set(act_p.keys()) != {"label", "h"}:
                return False, f"FAIL (C1): primary {idx} has invalid keys: {set(act_p.keys())}"
            lbl = act_p.get("label")
            if not (
                isinstance(lbl, list)
                and len(lbl) == 2
                and _c1_is_int(lbl[0])
                and _c1_is_int(lbl[1])
            ):
                return False, f"FAIL (C1): primary {idx} label must be a 2-element integer list"
            r, s = lbl
            rep = _c1_canonical_kac_label(p, p_prime, r, s)
            if (r, s) != rep:
                return (
                    False,
                    f"FAIL (C1): primary label [{r}, {s}] is not canonical representative (expected [{rep[0]}, {rep[1]}])",
                )
            if tuple(lbl) in seen_labels:
                return False, f"FAIL (C1): duplicate primary label [{r}, {s}]"
            seen_labels.add(tuple(lbl))

            if lbl != exp_p["label"]:
                return (
                    False,
                    f"FAIL (C1): primary {idx} label mismatch: expected {exp_p['label']}, got {lbl}",
                )
            h_val = act_p.get("h")
            if not _c1_is_reduced_rational_str(h_val):
                return False, f"FAIL (C1): primary {idx} h is not reduced rational string: {h_val}"
            if h_val != exp_p["h"]:
                return (
                    False,
                    f"FAIL (C1): primary {idx} h mismatch: expected '{exp_p['h']}', got '{h_val}'",
                )

        # Validate fusion rules
        act_fus = answer.get("fusion")
        if not isinstance(act_fus, list):
            return False, "FAIL (C1): fusion must be a list"
        if len(act_fus) != len(exp_fus):
            return (
                False,
                f"FAIL (C1): fusion rules count mismatch: expected {len(exp_fus)}, got {len(act_fus)}",
            )

        def _to_tuple_fus(item: list[Any]) -> tuple:
            return (tuple(item[0]), tuple(item[1]), tuple(item[2]), item[3])

        exp_fus_set = {_to_tuple_fus(item) for item in exp_fus}
        act_fus_set = set()
        for idx, item in enumerate(act_fus):
            if not isinstance(item, list) or len(item) != 4:
                return False, f"FAIL (C1): fusion rule at {idx} must be a 4-element list"
            p1, p2, p3, n = item
            if not (
                isinstance(p1, list)
                and len(p1) == 2
                and _c1_is_int(p1[0])
                and _c1_is_int(p1[1])
                and isinstance(p2, list)
                and len(p2) == 2
                and _c1_is_int(p2[0])
                and _c1_is_int(p2[1])
                and isinstance(p3, list)
                and len(p3) == 2
                and _c1_is_int(p3[0])
                and _c1_is_int(p3[1])
                and _c1_is_int(n)
            ):
                return False, f"FAIL (C1): malformed fusion rule structure: {item}"
            if p1 > p2:
                return (
                    False,
                    f"FAIL (C1): fusion rule violates canonical ordering {p1} <= {p2}",
                )
            if n <= 0:
                return False, "FAIL (C1): fusion coefficient must be strictly positive"
            tup = (tuple(p1), tuple(p2), tuple(p3), n)
            if tup in act_fus_set:
                return False, f"FAIL (C1): duplicate fusion entry {item}"
            act_fus_set.add(tup)

        if act_fus_set != exp_fus_set:
            diff_missing = exp_fus_set - act_fus_set
            diff_spurious = act_fus_set - exp_fus_set
            return (
                False,
                f"FAIL (C1): fusion mismatch. Missing: {diff_missing}, Spurious: {diff_spurious}",
            )

        return True, "PASS (C1): valid minimal model Verlinde certificate"

    return False, "FAIL (C1): unreachable model branch"


# Alias for backward compatibility
verify_verlinde_cyclotomic_checker = verify_verlinde_cyclotomic_certificate
