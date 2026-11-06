"""Mirror Symmetry and Calabi-Yau Hypergeometric Period Engine.

Pure Python stdlib: strictly zero external dependencies (no numpy, scipy, sympy, cvxpy).
Implements:
1. Exact rational power series arithmetic over Q[[z]] and Q[[q]].
2. Hypergeometric period integration for 1-parameter CY hypersurfaces in WP(w1..w5).
3. Mirror map computation q(z) and exact series reversion z(q).
4. Yukawa coupling coordinate transformation to flat coordinates.
5. Möbius inversion for integer Gopakumar-Vafa invariants and rational Gromov-Witten invariants.
6. Fail-closed refusal and Calabi-Yau witness mechanics.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping

# -------------------------------------------------------------------------
# Exact Boolean Guard
# -------------------------------------------------------------------------


def is_exact_int(val: Any) -> bool:
    """Returns True if and only if val is an int and strictly not a bool."""
    return type(val) is int and not isinstance(val, bool)


# -------------------------------------------------------------------------
# Pinned 1-Parameter Calabi-Yau Hypersurface Families (h11 = 1)
# -------------------------------------------------------------------------

# Maps sorted weight tuple (w1 <= w2 <= w3 <= w4 <= w5) to degree d = sum(w)
PINNED_FAMILIES: dict[tuple[int, int, int, int, int], int] = {
    (1, 1, 1, 1, 1): 5,  # Quintic threefold in P4: kappa = 5/1 = 5
    (1, 1, 1, 1, 2): 6,  # Sextic in WP(1,1,1,1,2): kappa = 6/2 = 3
    (1, 1, 1, 1, 4): 8,  # Octic in WP(1,1,1,1,4): kappa = 8/4 = 2
    (1, 1, 1, 2, 5): 10,  # Decic in WP(1,1,1,2,5): kappa = 10/10 = 1
}


# -------------------------------------------------------------------------
# Exact Number Theory & Combinatorics
# -------------------------------------------------------------------------


def harmonic_number(m: int) -> Fraction:
    """Computes exact harmonic number H_m = sum_{j=1}^m 1/j with H_0 = 0."""
    if m <= 0:
        return Fraction(0)
    return sum(Fraction(1, j) for j in range(1, m + 1))


def mobius(n: int) -> int:
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
# Exact Rational Power Series Arithmetic: Q[[z]] as list[Fraction]
# -------------------------------------------------------------------------


def series_mul(A: list[Fraction], B: list[Fraction], deg: int) -> list[Fraction]:
    """Cauchy product of power series truncated to degree deg."""
    res = [Fraction(0)] * (deg + 1)
    len_a = min(len(A), deg + 1)
    len_b = min(len(B), deg + 1)
    for i in range(len_a):
        ai = A[i]
        if ai == 0:
            continue
        max_j = min(len_b, deg + 1 - i)
        for j in range(max_j):
            res[i + j] += ai * B[j]
    return res


def series_div(A: list[Fraction], B: list[Fraction], deg: int) -> list[Fraction]:
    """Quotient A(z) / B(z) truncated to degree deg with B[0] != 0."""
    if not B or B[0] == 0:
        raise ZeroDivisionError("Cannot divide power series with zero constant term")
    C = [Fraction(0)] * (deg + 1)
    b0 = B[0]
    len_a = len(A)
    len_b = len(B)
    for n in range(deg + 1):
        rem = A[n] if n < len_a else Fraction(0)
        for i in range(1, min(len_b, n + 1)):
            rem -= B[i] * C[n - i]
        C[n] = rem / b0
    return C


def series_exp(S: list[Fraction], deg: int) -> list[Fraction]:
    """Computes exp(S(z)) truncated to degree deg where S[0] == 0.

    Uses differential relation E' = S' * E => n E_n = sum_{k=1}^n k S_k E_{n-k}.
    """
    if S and S[0] != 0:
        raise ValueError("series_exp requires power series with zero constant term S(0) = 0")
    E = [Fraction(0)] * (deg + 1)
    E[0] = Fraction(1)
    len_s = len(S)
    for n in range(1, deg + 1):
        s_val = sum(k * S[k] * E[n - k] for k in range(1, min(len_s, n + 1)))
        E[n] = s_val / n
    return E


def series_revert(Q: list[Fraction], deg: int) -> list[Fraction]:
    """Computes functional inverse Z(q) such that Q(Z(q)) = q up to degree deg.

    Requires Q[0] == 0 and Q[1] != 0.
    Output satisfies Z[0] == 0, Z[1] = 1 / Q[1].
    """
    if not Q or len(Q) < 2 or Q[0] != 0 or Q[1] == 0:
        raise ValueError("series_revert requires Q[0] == 0 and Q[1] != 0")

    Z = [Fraction(0)] * (deg + 1)
    Z[1] = Fraction(1) / Q[1]

    # Z_pows[k][n] stores [q^n](Z(q)^k)
    Z_pows = [[Fraction(0)] * (deg + 1) for _ in range(deg + 1)]
    Z_pows[0][0] = Fraction(1)
    Z_pows[1][1] = Z[1]

    len_q = len(Q)
    for n in range(2, deg + 1):
        sum_k = Fraction(0)
        for k in range(2, min(len_q, n + 1)):
            term_kn = sum(Z[j] * Z_pows[k - 1][n - j] for j in range(1, n))
            Z_pows[k][n] = term_kn
            sum_k += Q[k] * term_kn
        Z[n] = -sum_k / Q[1]
        Z_pows[1][n] = Z[n]

    return Z


def series_compose(P: list[Fraction], Z: list[Fraction], deg: int) -> list[Fraction]:
    """Evaluates P(Z(q)) up to degree deg where Z[0] == 0."""
    res = [Fraction(0)] * (deg + 1)
    res[0] = P[0] if P else Fraction(0)
    Z_pow = [Fraction(0)] * (deg + 1)
    Z_pow[0] = Fraction(1)
    len_p = len(P)
    for k in range(1, min(len_p, deg + 1)):
        Z_pow = series_mul(Z_pow, Z, deg)
        pk = P[k]
        if pk == 0:
            continue
        for m in range(deg + 1):
            res[m] += pk * Z_pow[m]
    return res


# -------------------------------------------------------------------------
# Hypergeometric Periods, Mirror Map & Yukawa Transformation
# -------------------------------------------------------------------------


def compute_periods_and_invariants(
    weights: list[int],
    degree: int,
    max_curve_degree: int,
) -> dict[str, Any]:
    """Computes exact genus-zero Gromov-Witten and Gopakumar-Vafa invariants via mirror symmetry."""
    d = degree
    calc_deg = max_curve_degree + 2

    # Canonicalize weights
    w_sorted = sorted(weights)

    # Classical triple intersection number: kappa = d / prod(w_i)
    prod_w = 1
    for w in w_sorted:
        prod_w *= w
    kappa = Fraction(d, prod_w)

    # Scaling constant for Picard-Fuchs singular point: mu = d^d / prod(w_i^{w_i})
    prod_w_w = 1
    for w in w_sorted:
        prod_w_w *= w**w
    mu = Fraction(d**d, prod_w_w)

    # Fundamental period varpi_0(z) and Frobenius logarithmic period varpi_tilde_1(z)
    c0: list[Fraction] = []
    c1: list[Fraction] = []
    for n in range(calc_deg + 1):
        num = math.factorial(d * n)
        den = 1
        for w in w_sorted:
            den *= math.factorial(w * n)
        coeff = Fraction(num, den)
        c0.append(coeff)

        harm = d * harmonic_number(d * n) - sum(w * harmonic_number(w * n) for w in w_sorted)
        c1.append(coeff * harm)

    # Period ratio S(z) = varpi_tilde_1(z) / varpi_0(z) in Q[[z]] with S(0) = 0
    S = series_div(c1, c0, calc_deg)

    # Mirror map q(z) = z * exp(S(z)) in Q[[z]]
    E = series_exp(S, calc_deg)
    Q = [Fraction(0)] + E[:calc_deg]

    # Series reversion: z(q) in Q[[q]] such that q(z(q)) = q
    Z = series_revert(Q, calc_deg)

    # Classical Yukawa coupling in z-variable:
    # C_{zzz}(z) = kappa / (1 - mu*z) / varpi_0(z)^2
    inv_1_minus_mu_z = [Fraction(mu**n) for n in range(calc_deg + 1)]
    varpi0_sq = series_mul(c0, c0, calc_deg)
    C_z = series_div(
        series_mul([kappa] + [Fraction(0)] * calc_deg, inv_1_minus_mu_z, calc_deg),
        varpi0_sq,
        calc_deg,
    )

    # Composition C_{zzz}(z(q))
    C_of_Z = series_compose(C_z, Z, calc_deg)

    # Flat coordinate transformation factor: (q/z * dz/dq)^3 = (d log z / d log q)^3
    # Z(q) = q * (Z[1] + Z[2] q + ... + Z[calc_deg] q^{calc_deg-1})
    Z_over_q = Z[1:]
    inv_Z_over_q = series_div([Fraction(1)] + [Fraction(0)] * calc_deg, Z_over_q, calc_deg)
    dz_dq = [n * Z[n] for n in range(1, calc_deg + 1)]
    dlogz_dlogq = series_mul(inv_Z_over_q, dz_dq, calc_deg)
    factor_cubed = series_mul(series_mul(dlogz_dlogq, dlogz_dlogq, calc_deg), dlogz_dlogq, calc_deg)

    # Yukawa coupling in q-variable: K(q) = kappa + sum_{k >= 1} c_k q^k
    K = series_mul(C_of_Z, factor_cubed, calc_deg)

    # Invariants extraction via Mobius inversion:
    # n_k * k^3 = sum_{j | k} mu(j) c_{k/j}
    gv: dict[str, str] = {}
    gv_ints: dict[int, int] = {}
    for k in range(1, max_curve_degree + 1):
        val = sum(mobius(j) * K[k // j] for j in range(1, k + 1) if k % j == 0)
        nk = val / (k**3)
        if nk.denominator != 1:
            raise ArithmeticError(f"Integrality failure for GV invariant n_{k}: {nk}")
        int_nk = int(nk)
        gv_ints[k] = int_nk
        gv[str(k)] = str(int_nk)

    # Genus-zero rational Gromov-Witten invariants:
    # N_k = sum_{j | k} n_{k/j} / j^3
    gw: dict[str, str] = {}
    for k in range(1, max_curve_degree + 1):
        Nk = sum(Fraction(gv_ints[k // j], j**3) for j in range(1, k + 1) if k % j == 0)
        gw[str(k)] = (
            f"{Nk.numerator}/{Nk.denominator}" if Nk.denominator != 1 else str(Nk.numerator)
        )

    # Mirror map coefficients of z(q) = sum_{k=1}^D z_k q^k
    mirror_map_coeffs = [
        f"{Z[k].numerator}/{Z[k].denominator}" if Z[k].denominator != 1 else str(Z[k].numerator)
        for k in range(1, max_curve_degree + 1)
    ]

    kappa_str = (
        f"{kappa.numerator}/{kappa.denominator}" if kappa.denominator != 1 else str(kappa.numerator)
    )

    return {
        "kappa": kappa_str,
        "gv": gv,
        "gw": gw,
        "mirror_map_coeffs": mirror_map_coeffs,
    }


# -------------------------------------------------------------------------
# Fail-Closed Case Validation and Refusal Semantics
# -------------------------------------------------------------------------


def solve_quintic_mirror_case(
    case: Mapping[str, Any],
) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
    """Validates input case with fail-closed refusal semantics.

    Returns: (status, refusal_or_witness_dict, result_dict)
    """
    if not isinstance(case, Mapping):
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    weights = case.get("weights")
    degree = case.get("degree")
    max_curve_degree = case.get("max_curve_degree")

    # Strict structural validation with boolean rejection
    if not isinstance(weights, list) or len(weights) != 5:
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None
    for w in weights:
        if not is_exact_int(w) or w <= 0:
            return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    if not is_exact_int(degree) or degree <= 0:
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    if not is_exact_int(max_curve_degree):
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    # Curve degree bound check: 1 <= D <= 10
    if max_curve_degree < 1 or max_curve_degree > 10:
        return "UNKNOWN", {"refusal_code": "MAX_CURVE_DEGREE_OUT_OF_BOUNDS"}, None

    # Calabi-Yau condition check: d == sum(w)
    weight_sum = sum(weights)
    if degree != weight_sum:
        return (
            "OUT_OF_SCOPE",
            {
                "kind": "not_calabi_yau",
                "degree": degree,
                "weight_sum": weight_sum,
            },
            None,
        )

    # Pinned family membership check (canonicalized by sorting weights)
    sorted_weights = tuple(sorted(weights))
    if sorted_weights not in PINNED_FAMILIES or PINNED_FAMILIES[sorted_weights] != degree:
        return "UNKNOWN", {"refusal_code": "FAMILY_NOT_IN_PINNED_LIST"}, None

    # Compute exact mirror symmetry invariants
    try:
        solution = compute_periods_and_invariants(weights, degree, max_curve_degree)
    except Exception:
        return "UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None

    return "SOLVED", None, solution
