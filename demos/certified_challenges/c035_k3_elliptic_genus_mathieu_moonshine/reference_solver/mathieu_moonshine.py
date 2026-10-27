"""Mathieu Moonshine and K3 Elliptic Genus Mathematical Engine.

Pure Python stdlib: strictly zero external dependencies (no numpy, scipy, sympy, cvxpy).
Implements:
1. Laurent polynomial q-series arithmetic over Z[y, y^-1][[q]].
2. Jacobi theta expansions and Appell-Lerch massless character subtraction.
3. Exact Fourier coefficient extraction A_n (1 <= n <= 30) via polynomial series division.
4. M_24 sporadic simple group 26-class character table with exact algebraic surd arithmetic in Q(sqrt(-p)).
5. Exact rational Frobenius-Schur character inner product and decomposition.
6. Fail-closed refusal and witness mechanics.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from typing import Any, Mapping

# -------------------------------------------------------------------------
# Exact Boolean Guard
# -------------------------------------------------------------------------


def is_exact_int(val: Any) -> bool:
    """Returns True if and only if val is an int and strictly not a bool."""
    return type(val) is int and not isinstance(val, bool)


# -------------------------------------------------------------------------
# Laurent Polynomial Arithmetic: Z[y, y^-1] represented as dict[int, int]
# -------------------------------------------------------------------------

Poly = dict[int, int]


def poly_clean(p: Poly) -> Poly:
    """Removes terms with zero coefficients."""
    return {k: v for k, v in p.items() if v != 0}


def poly_add(p1: Poly, p2: Poly) -> Poly:
    """Sums two Laurent polynomials."""
    res = dict(p1)
    for k, v in p2.items():
        res[k] = res.get(k, 0) + v
    return poly_clean(res)


def poly_sub(p1: Poly, p2: Poly) -> Poly:
    """Subtracts p2 from p1."""
    res = dict(p1)
    for k, v in p2.items():
        res[k] = res.get(k, 0) - v
    return poly_clean(res)


def poly_mul_scalar(p: Poly, c: int) -> Poly:
    """Multiplies polynomial by integer scalar."""
    if c == 0:
        return {}
    return {k: v * c for k, v in p.items()}


def poly_mul(p1: Poly, p2: Poly) -> Poly:
    """Cauchy product of two Laurent polynomials."""
    res: defaultdict[int, int] = defaultdict(int)
    for k1, v1 in p1.items():
        for k2, v2 in p2.items():
            res[k1 + k2] += v1 * v2
    return {k: v for k, v in res.items() if v != 0}


def poly_eval(p: Poly, y: int) -> int:
    """Evaluates Laurent polynomial at integer y."""
    if y == 1:
        return sum(p.values())
    if y == -1:
        return sum(v if k % 2 == 0 else -v for k, v in p.items())
    return sum(v * (y**k) for k, v in p.items())


# -------------------------------------------------------------------------
# Formal Power Series: Z[y, y^-1][[q]] represented as dict[int, Poly]
# -------------------------------------------------------------------------

Series = dict[int, Poly]


def series_clean(s: Series) -> Series:
    """Cleans each coefficient polynomial and drops zero polynomials."""
    return {m: poly_clean(p) for m, p in s.items() if poly_clean(p)}


def series_add(s1: Series, s2: Series) -> Series:
    """Sums two power series."""
    res = {m: dict(p) for m, p in s1.items()}
    for m, p in s2.items():
        res[m] = poly_add(res.get(m, {}), p)
    return series_clean(res)


def series_sub(s1: Series, s2: Series) -> Series:
    """Subtracts s2 from s1."""
    res = {m: dict(p) for m, p in s1.items()}
    for m, p in s2.items():
        res[m] = poly_sub(res.get(m, {}), p)
    return series_clean(res)


def series_mul_scalar(s: Series, c: int) -> Series:
    """Scales power series by integer c."""
    if c == 0:
        return {}
    return {m: poly_mul_scalar(p, c) for m, p in s.items()}


def series_mul(s1: Series, s2: Series, max_q: int) -> Series:
    """Cauchy product of power series truncated at q^max_q."""
    res: defaultdict[int, defaultdict[int, int]] = defaultdict(lambda: defaultdict(int))
    for m1, p1 in s1.items():
        if m1 > max_q:
            continue
        for m2, p2 in s2.items():
            if m1 + m2 <= max_q:
                prod = poly_mul(p1, p2)
                for k, v in prod.items():
                    res[m1 + m2][k] += v
    return {q: {k: v for k, v in p.items() if v != 0} for q, p in res.items()}


def series_div_unit(num: Series, den: Series, max_q: int) -> Series:
    """Inverts unit power series (den[0] == {0: 1}) in Z[y, y^-1][[q]] up to max_q."""
    res: dict[int, Poly] = {}
    for n in range(max_q + 1):
        cur = dict(num.get(n, {}))
        for k in range(1, n + 1):
            if k in den and (n - k) in res:
                cur = poly_sub(cur, poly_mul(den[k], res[n - k]))
        if poly_clean(cur):
            res[n] = poly_clean(cur)
    return res


# -------------------------------------------------------------------------
# Jacobi Theta and Pre-factor Expansions
# -------------------------------------------------------------------------


def compute_theta2_sq_over_theta2_sq_0(max_q: int) -> Series:
    """Computes (theta_2(tau, z) / theta_2(tau, 0))^2 with exact 1/4 normalization."""
    num: Series = {0: {0: 1}}
    den: Series = {0: {0: 1}}
    for m in range(1, max_q + 1):
        f1: Series = {0: {0: 1}, m: {1: 2}, 2 * m: {2: 1}}
        f2: Series = {0: {0: 1}, m: {-1: 2}, 2 * m: {-2: 1}}
        num = series_mul(num, series_mul(f1, f2, max_q), max_q)
        f_den: Series = {0: {0: 1}, m: {0: 4}, 2 * m: {0: 6}, 3 * m: {0: 4}, 4 * m: {0: 1}}
        den = series_mul(den, f_den, max_q)

    quot = series_div_unit(num, den, max_q)
    # Correct normalization: (y^{1/2} + y^{-1/2})^2 / 4 = (y + 2 + y^{-1}) / 4
    # Multiplying by 8 yields: 2 * (y + 2 + y^{-1})
    lead: Poly = {-1: 2, 0: 4, 1: 2}
    res: Series = {}
    for m, p in quot.items():
        res[m] = poly_mul(lead, p)
    return res


def compute_theta3_and_theta4_sum(max_q: int) -> Series:
    """Computes 8 * [ (theta_3/theta_3(0))^2 + (theta_4/theta_4(0))^2 ] in integer powers of q."""
    max_h = 2 * max_q
    num3: Series = {0: {0: 1}}
    den3: Series = {0: {0: 1}}
    num4: Series = {0: {0: 1}}
    den4: Series = {0: {0: 1}}

    for k in range(1, max_h + 1, 2):  # odd k represents half-powers k/2
        f3_1: Series = {0: {0: 1}, k: {1: 2}, 2 * k: {2: 1}}
        f3_2: Series = {0: {0: 1}, k: {-1: 2}, 2 * k: {-2: 1}}
        num3 = series_mul(num3, series_mul(f3_1, f3_2, max_h), max_h)
        den3 = series_mul(
            den3, {0: {0: 1}, k: {0: 4}, 2 * k: {0: 6}, 3 * k: {0: 4}, 4 * k: {0: 1}}, max_h
        )

        f4_1: Series = {0: {0: 1}, k: {1: -2}, 2 * k: {2: 1}}
        f4_2: Series = {0: {0: 1}, k: {-1: -2}, 2 * k: {-2: 1}}
        num4 = series_mul(num4, series_mul(f4_1, f4_2, max_h), max_h)
        den4 = series_mul(
            den4, {0: {0: 1}, k: {0: -4}, 2 * k: {0: 6}, 3 * k: {0: -4}, 4 * k: {0: 1}}, max_h
        )

    q3 = series_div_unit(num3, den3, max_h)
    q4 = series_div_unit(num4, den4, max_h)

    res: Series = {}
    for h in range(0, max_h + 1, 2):
        sum_p = poly_add(q3.get(h, {}), q4.get(h, {}))
        if sum_p:
            res[h // 2] = {k: v * 8 for k, v in sum_p.items()}
    return res


def compute_k3_elliptic_genus(max_q: int) -> Series:
    """Computes Z(tau, z) = 8 * [ (theta_2/theta_2(0))^2 + (theta_3/theta_3(0))^2 + (theta_4/theta_4(0))^2 ]."""
    t2 = compute_theta2_sq_over_theta2_sq_0(max_q)
    t34 = compute_theta3_and_theta4_sum(max_q)
    res: Series = {}
    for n in range(max_q + 1):
        p = poly_add(t2.get(n, {}), t34.get(n, {}))
        if p:
            res[n] = p
    return res


def compute_prefactor_F(max_q: int) -> Series:
    """Computes F(tau, z) = -(y + y^-1 - 2) * prod_{m=1}^max_q (1 - y q^m)^2 (1 - y^-1 q^m)^2 / (1 - q^m)."""
    num: Series = {0: {0: 1}}
    den: Series = {0: {0: 1}}
    for m in range(1, max_q + 1):
        f1: Series = {0: {0: 1}, m: {1: -2}, 2 * m: {2: 1}}
        f2: Series = {0: {0: 1}, m: {-1: -2}, 2 * m: {-2: 1}}
        num = series_mul(num, series_mul(f1, f2, max_q), max_q)
        den = series_mul(den, {0: {0: 1}, m: {0: -1}}, max_q)

    quot = series_div_unit(num, den, max_q)
    lead: Poly = {-1: -1, 0: 2, 1: -1}
    res: Series = {}
    for m, p in quot.items():
        res[m] = poly_mul(lead, p)
    return res


def compute_ch_massless(max_q: int) -> Series:
    """Computes massless N=4 character ch_{h=1/4, l=0}(tau, z) = F(tau, z) * mu(tau, z).

    Decomposed as P(tau, z) * S(tau, z) where:
      P(tau, z) = prod_{m=1}^max_q (1 - y q^m)(1 - y^-1 q^m) / (1 - q^m)^2
      S(tau, z) = sum_{k in Z} (-1)^k q^{k(k+1)/2} y^k (1 - y)/(1 - y q^k)
    """
    numP: Series = {0: {0: 1}}
    denP: Series = {0: {0: 1}}
    for m in range(1, max_q + 1):
        numP = series_mul(
            numP, series_mul({0: {0: 1}, m: {1: -1}}, {0: {0: 1}, m: {-1: -1}}, max_q), max_q
        )
        denP = series_mul(denP, {0: {0: 1}, m: {0: -2}, 2 * m: {0: 1}}, max_q)
    P = series_div_unit(numP, denP, max_q)

    S: defaultdict[int, defaultdict[int, int]] = defaultdict(lambda: defaultdict(int))
    S[0][0] = 1
    for k in range(1, max_q + 1):
        q_pow = k * (k + 1) // 2
        if q_pow > max_q:
            break
        sign = (-1) ** k
        for j in range((max_q - q_pow) // k + 1):
            tot_q = q_pow + j * k
            S[tot_q][k + j] += sign
            S[tot_q][k + j + 1] -= sign

    for l in range(1, max_q + 1):
        q_pow = l * (l + 1) // 2
        if q_pow > max_q:
            break
        sign = (-1) ** l
        for j in range((max_q - q_pow) // l + 1):
            tot_q = q_pow + j * l
            S[tot_q][-l - j] += sign
            S[tot_q][-l - j - 1] -= sign

    S_series = {q: dict(p) for q, p in S.items()}
    return series_mul(P, S_series, max_q)


# -------------------------------------------------------------------------
# Dynamic Solver Series Engine & Zero-y-Residual Verification
# -------------------------------------------------------------------------

_SOLVER_DYNAMIC_CACHE: dict[int, int] = {}


def compute_mock_modular_H(max_n: int) -> dict[int, int]:
    """Computes exact mock modular form coefficients A_n for 1 <= n <= max_n.

    Divides (Z(tau, z) - 24 * ch_massless(tau, z)) / F(tau, z) over Z[y, y^-1][[q]],
    verifying zero y-dependent residual at every order.
    """
    missing = [n for n in range(1, max_n + 1) if n not in _SOLVER_DYNAMIC_CACHE]
    if missing:
        max_q = max(max_n, 30)
        Z = compute_k3_elliptic_genus(max_q)
        ch_massless = compute_ch_massless(max_q)
        F = compute_prefactor_F(max_q)

        # Numerator: Z - 24 * ch_massless
        Num: Series = {}
        for n in range(max_q + 1):
            ch24 = {k: v * 24 for k, v in ch_massless.get(n, {}).items()}
            Num[n] = poly_sub(Z.get(n, {}), ch24)

        # Exact polynomial division H(tau) = Num / F
        # F[0] = {-1: -1, 0: 2, 1: -1} = 2 - y - y^-1
        H: dict[int, int] = {}
        for n in range(max_q + 1):
            rem = dict(Num.get(n, {}))
            for k in range(1, n + 1):
                if k in F and (n - k) in H:
                    rem = poly_sub(rem, {yk: v * H[n - k] for yk, v in F[k].items()})
            if not rem:
                H[n] = 0
            else:
                hn = -rem.get(1, 0)
                # Mathematical Assertion: residual must be identically hn * F[0]
                if rem.get(-1, 0) != -hn or rem.get(0, 0) != 2 * hn:
                    raise ArithmeticError(f"Non-zero y residual in Laurent division at order n={n}")
                H[n] = hn
            if n >= 1:
                _SOLVER_DYNAMIC_CACHE[n] = H[n]

    return {n: _SOLVER_DYNAMIC_CACHE[n] for n in range(1, max_n + 1)}


def compute_coefficients_exact(max_n: int) -> dict[str, int]:
    """Returns exact coefficients A_n for 1 <= n <= max_n via dynamic Laurent series arithmetic."""
    h_dict = compute_mock_modular_H(max_n)
    return {str(n): h_dict[n] for n in range(1, max_n + 1)}


# -------------------------------------------------------------------------
# Mathieu Group M_24 Constants & Character Table
# -------------------------------------------------------------------------

G_ORDER: int = 244823040

CLASSES_M24: list[str] = [
    "1A",
    "2A",
    "3A",
    "5A",
    "4B",
    "7A",
    "7B",
    "8A",
    "6A",
    "11A",
    "15A",
    "15B",
    "14A",
    "14B",
    "23A",
    "23B",
    "12B",
    "6B",
    "4C",
    "3B",
    "2B",
    "10A",
    "21A",
    "21B",
    "4A",
    "12A",
]

IRREP_NAMES: list[str] = [
    "1",
    "23",
    "252",
    "253",
    "1771",
    "3520",
    "45",
    "45bar",
    "990",
    "990bar",
    "1035a",
    "1035abar",
    "1035b",
    "231",
    "231bar",
    "770",
    "770bar",
    "483",
    "1265",
    "2024",
    "2277",
    "3312",
    "5313",
    "5796",
    "5544",
    "10395",
]


def _I(n: int) -> tuple[int, int, int]:
    return (2 * n, 0, 0)


def _ep(p: int) -> tuple[int, int, int]:
    return (-1, 1, p)


def _em(p: int) -> tuple[int, int, int]:
    return (-1, -1, p)


def _2ep(p: int) -> tuple[int, int, int]:
    return (-2, 2, p)


def _2em(p: int) -> tuple[int, int, int]:
    return (-2, -2, p)


def _nep(p: int) -> tuple[int, int, int]:
    return (1, -1, p)


def _nem(p: int) -> tuple[int, int, int]:
    return (1, 1, p)


TABLE_M24: list[list[tuple[int, int, int]]] = [
    # 1: 1
    [_I(1)] * 26,
    # 2: 23
    [
        _I(23),
        _I(7),
        _I(5),
        _I(3),
        _I(3),
        _I(2),
        _I(2),
        _I(1),
        _I(1),
        _I(1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(-1),
        _I(-1),
        _I(-1),
        _I(-1),
        _I(-1),
        _I(-1),
        _I(-1),
        _I(-1),
        _I(-1),
        _I(-1),
    ],
    # 3: 252
    [
        _I(252),
        _I(28),
        _I(9),
        _I(2),
        _I(4),
        _I(0),
        _I(0),
        _I(0),
        _I(1),
        _I(-1),
        _I(-1),
        _I(-1),
        _I(0),
        _I(0),
        _I(-1),
        _I(-1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(12),
        _I(2),
        _I(0),
        _I(0),
        _I(4),
        _I(1),
    ],
    # 4: 253
    [
        _I(253),
        _I(13),
        _I(10),
        _I(3),
        _I(1),
        _I(1),
        _I(1),
        _I(-1),
        _I(-2),
        _I(0),
        _I(0),
        _I(0),
        _I(-1),
        _I(-1),
        _I(0),
        _I(0),
        _I(1),
        _I(1),
        _I(1),
        _I(1),
        _I(-11),
        _I(-1),
        _I(1),
        _I(1),
        _I(-3),
        _I(0),
    ],
    # 5: 1771
    [
        _I(1771),
        _I(-21),
        _I(16),
        _I(1),
        _I(-5),
        _I(0),
        _I(0),
        _I(-1),
        _I(0),
        _I(0),
        _I(1),
        _I(1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(-1),
        _I(-1),
        _I(-1),
        _I(7),
        _I(11),
        _I(1),
        _I(0),
        _I(0),
        _I(3),
        _I(0),
    ],
    # 6: 3520
    [
        _I(3520),
        _I(64),
        _I(10),
        _I(0),
        _I(0),
        _I(-1),
        _I(-1),
        _I(0),
        _I(-2),
        _I(0),
        _I(0),
        _I(0),
        _I(1),
        _I(1),
        _I(1),
        _I(1),
        _I(0),
        _I(0),
        _I(0),
        _I(-8),
        _I(0),
        _I(0),
        _I(-1),
        _I(-1),
        _I(0),
        _I(0),
    ],
    # 7: 45
    [
        _I(45),
        _I(-3),
        _I(0),
        _I(0),
        _I(1),
        _ep(7),
        _em(7),
        _I(-1),
        _I(0),
        _I(1),
        _I(0),
        _I(0),
        _nep(7),
        _nem(7),
        _I(-1),
        _I(-1),
        _I(1),
        _I(-1),
        _I(1),
        _I(3),
        _I(5),
        _I(0),
        _em(7),
        _ep(7),
        _I(-3),
        _I(0),
    ],
    # 8: 45bar
    [
        _I(45),
        _I(-3),
        _I(0),
        _I(0),
        _I(1),
        _em(7),
        _ep(7),
        _I(-1),
        _I(0),
        _I(1),
        _I(0),
        _I(0),
        _nem(7),
        _nep(7),
        _I(-1),
        _I(-1),
        _I(1),
        _I(-1),
        _I(1),
        _I(3),
        _I(5),
        _I(0),
        _ep(7),
        _em(7),
        _I(-3),
        _I(0),
    ],
    # 9: 990
    [
        _I(990),
        _I(-18),
        _I(0),
        _I(0),
        _I(2),
        _ep(7),
        _em(7),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _ep(7),
        _em(7),
        _I(1),
        _I(1),
        _I(1),
        _I(-1),
        _I(-2),
        _I(3),
        _I(-10),
        _I(0),
        _em(7),
        _ep(7),
        _I(6),
        _I(0),
    ],
    # 10: 990bar
    [
        _I(990),
        _I(-18),
        _I(0),
        _I(0),
        _I(2),
        _em(7),
        _ep(7),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _em(7),
        _ep(7),
        _I(1),
        _I(1),
        _I(1),
        _I(-1),
        _I(-2),
        _I(3),
        _I(-10),
        _I(0),
        _ep(7),
        _em(7),
        _I(6),
        _I(0),
    ],
    # 11: 1035a
    [
        _I(1035),
        _I(-21),
        _I(0),
        _I(0),
        _I(3),
        _2ep(7),
        _2em(7),
        _I(-1),
        _I(0),
        _I(1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(-1),
        _I(1),
        _I(-1),
        _I(-3),
        _I(-5),
        _I(0),
        _nem(7),
        _nep(7),
        _I(3),
        _I(0),
    ],
    # 12: 1035abar
    [
        _I(1035),
        _I(-21),
        _I(0),
        _I(0),
        _I(3),
        _2em(7),
        _2ep(7),
        _I(-1),
        _I(0),
        _I(1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(-1),
        _I(1),
        _I(-1),
        _I(-3),
        _I(-5),
        _I(0),
        _nep(7),
        _nem(7),
        _I(3),
        _I(0),
    ],
    # 13: 1035b
    [
        _I(1035),
        _I(27),
        _I(0),
        _I(0),
        _I(-1),
        _I(-1),
        _I(-1),
        _I(1),
        _I(0),
        _I(1),
        _I(0),
        _I(0),
        _I(-1),
        _I(-1),
        _I(0),
        _I(0),
        _I(0),
        _I(2),
        _I(3),
        _I(6),
        _I(35),
        _I(0),
        _I(-1),
        _I(-1),
        _I(3),
        _I(0),
    ],
    # 14: 231
    [
        _I(231),
        _I(7),
        _I(-3),
        _I(1),
        _I(-1),
        _I(0),
        _I(0),
        _I(-1),
        _I(1),
        _I(0),
        _ep(15),
        _em(15),
        _I(0),
        _I(0),
        _I(1),
        _I(1),
        _I(0),
        _I(0),
        _I(3),
        _I(0),
        _I(-9),
        _I(1),
        _I(0),
        _I(0),
        _I(-1),
        _I(-1),
    ],
    # 15: 231bar
    [
        _I(231),
        _I(7),
        _I(-3),
        _I(1),
        _I(-1),
        _I(0),
        _I(0),
        _I(-1),
        _I(1),
        _I(0),
        _em(15),
        _ep(15),
        _I(0),
        _I(0),
        _I(1),
        _I(1),
        _I(0),
        _I(0),
        _I(3),
        _I(0),
        _I(-9),
        _I(1),
        _I(0),
        _I(0),
        _I(-1),
        _I(-1),
    ],
    # 16: 770
    [
        _I(770),
        _I(-14),
        _I(5),
        _I(0),
        _I(-2),
        _I(0),
        _I(0),
        _I(0),
        _I(1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _ep(23),
        _em(23),
        _I(1),
        _I(1),
        _I(-2),
        _I(-7),
        _I(10),
        _I(0),
        _I(0),
        _I(0),
        _I(2),
        _I(-1),
    ],
    # 17: 770bar
    [
        _I(770),
        _I(-14),
        _I(5),
        _I(0),
        _I(-2),
        _I(0),
        _I(0),
        _I(0),
        _I(1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _em(23),
        _ep(23),
        _I(1),
        _I(1),
        _I(-2),
        _I(-7),
        _I(10),
        _I(0),
        _I(0),
        _I(0),
        _I(2),
        _I(-1),
    ],
    # 18: 483
    [
        _I(483),
        _I(35),
        _I(6),
        _I(-2),
        _I(3),
        _I(0),
        _I(0),
        _I(-1),
        _I(2),
        _I(-1),
        _I(1),
        _I(1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(3),
        _I(0),
        _I(3),
        _I(-2),
        _I(0),
        _I(0),
        _I(3),
        _I(0),
    ],
    # 19: 1265
    [
        _I(1265),
        _I(49),
        _I(5),
        _I(0),
        _I(1),
        _I(-2),
        _I(-2),
        _I(1),
        _I(1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(-3),
        _I(8),
        _I(-15),
        _I(0),
        _I(1),
        _I(1),
        _I(-7),
        _I(-1),
    ],
    # 20: 2024
    [
        _I(2024),
        _I(8),
        _I(-1),
        _I(-1),
        _I(0),
        _I(1),
        _I(1),
        _I(0),
        _I(-1),
        _I(0),
        _I(-1),
        _I(-1),
        _I(1),
        _I(1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(8),
        _I(24),
        _I(-1),
        _I(1),
        _I(1),
        _I(8),
        _I(-1),
    ],
    # 21: 2277
    [
        _I(2277),
        _I(21),
        _I(0),
        _I(-3),
        _I(1),
        _I(2),
        _I(2),
        _I(-1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(2),
        _I(-3),
        _I(6),
        _I(-19),
        _I(1),
        _I(-1),
        _I(-1),
        _I(-3),
        _I(0),
    ],
    # 22: 3312
    [
        _I(3312),
        _I(48),
        _I(0),
        _I(-3),
        _I(0),
        _I(1),
        _I(1),
        _I(0),
        _I(0),
        _I(1),
        _I(0),
        _I(0),
        _I(-1),
        _I(-1),
        _I(0),
        _I(0),
        _I(0),
        _I(-2),
        _I(0),
        _I(-6),
        _I(16),
        _I(1),
        _I(1),
        _I(1),
        _I(0),
        _I(0),
    ],
    # 23: 5313
    [
        _I(5313),
        _I(49),
        _I(-15),
        _I(3),
        _I(-3),
        _I(0),
        _I(0),
        _I(-1),
        _I(1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(-3),
        _I(0),
        _I(9),
        _I(-1),
        _I(0),
        _I(0),
        _I(1),
        _I(1),
    ],
    # 24: 5796
    [
        _I(5796),
        _I(-28),
        _I(-9),
        _I(1),
        _I(4),
        _I(0),
        _I(0),
        _I(0),
        _I(-1),
        _I(-1),
        _I(1),
        _I(1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(36),
        _I(1),
        _I(0),
        _I(0),
        _I(-4),
        _I(-1),
    ],
    # 25: 5544
    [
        _I(5544),
        _I(-56),
        _I(9),
        _I(-1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(1),
        _I(0),
        _I(-1),
        _I(-1),
        _I(0),
        _I(0),
        _I(1),
        _I(1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(24),
        _I(-1),
        _I(0),
        _I(0),
        _I(-8),
        _I(1),
    ],
    # 26: 10395
    [
        _I(10395),
        _I(-21),
        _I(0),
        _I(0),
        _I(-1),
        _I(0),
        _I(0),
        _I(1),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(0),
        _I(-1),
        _I(-1),
        _I(0),
        _I(0),
        _I(3),
        _I(0),
        _I(-45),
        _I(0),
        _I(0),
        _I(0),
        _I(3),
        _I(0),
    ],
]

CENTRALIZERS_M24: list[int] = [
    244823040,
    21504,
    1080,
    60,
    128,
    42,
    42,
    16,
    24,
    11,
    15,
    15,
    14,
    14,
    23,
    23,
    12,
    24,
    96,
    504,
    7680,
    20,
    21,
    21,
    384,
    12,
]

CLASS_SIZES_M24: list[int] = [G_ORDER // c for c in CENTRALIZERS_M24]
CLASS_INDEX_MAP: dict[str, int] = {c_name: i for i, c_name in enumerate(CLASSES_M24)}


def parse_character_value(val: Any) -> tuple[int, int, int]:
    """Parses input representation value into exact algebraic integer triple (a, b, p)."""
    if is_exact_int(val):
        return (2 * val, 0, 0)
    if isinstance(val, (list, tuple)) and len(val) == 3:
        if all(is_exact_int(x) for x in val):
            return (val[0], val[1], val[2])
    if isinstance(val, str):
        s = val.strip().replace(" ", "")
        surd_map = {
            "e7+": (-1, 1, 7),
            "e7-": (-1, -1, 7),
            "-e7+": (1, -1, 7),
            "-e7-": (1, 1, 7),
            "2e7+": (-2, 2, 7),
            "2e7-": (-2, -2, 7),
            "e15+": (-1, 1, 15),
            "e15-": (-1, -1, 15),
            "e23+": (-1, 1, 23),
            "e23-": (-1, -1, 23),
        }
        if s in surd_map:
            return surd_map[s]
        try:
            int_val = int(s)
            return (2 * int_val, 0, 0)
        except ValueError:
            pass
    raise ValueError(f"Unrecognized character value format: {val}")


def decompose_m24_character(
    class_order: list[str],
    values: list[Any],
) -> tuple[str, dict[str, Any] | None, dict[str, int] | None]:
    """Decomposes a class function on M_24 into irreducible characters.

    Returns:
        (verdict, witness_if_out_of_scope, multiplicities_if_solved)
    """
    canonical_values: list[tuple[int, int, int]] = [None] * 26  # type: ignore[list-item]
    for cls_name, val in zip(class_order, values):
        if cls_name not in CLASS_INDEX_MAP:
            raise KeyError(f"Unrecognized class name: {cls_name}")
        idx = CLASS_INDEX_MAP[cls_name]
        canonical_values[idx] = parse_character_value(val)

    multiplicities: dict[str, int] = {}

    for r_idx, irrep_row in enumerate(TABLE_M24):
        irrep_name = IRREP_NAMES[r_idx]
        tot_re4 = 0
        tot_im4 = {7: 0, 15: 0, 23: 0}

        for j in range(26):
            a1, b1, p1 = canonical_values[j]
            a2, b2, p2 = irrep_row[j]
            p = p1 if b1 != 0 else (p2 if b2 != 0 else 0)

            # (a1 + b1 sqrt(-p))/2 * (a2 - b2 sqrt(-p))/2
            re4 = a1 * a2 + b1 * b2 * p
            im4 = a2 * b1 - a1 * b2
            cj = CLASS_SIZES_M24[j]
            tot_re4 += cj * re4
            if p in tot_im4:
                tot_im4[p] += cj * im4

        # Check for non-zero imaginary residual
        for p, im_val in tot_im4.items():
            if im_val != 0:
                frac_im = Fraction(im_val, 4 * G_ORDER)
                return (
                    "OUT_OF_SCOPE",
                    {
                        "kind": "non_zero_imaginary",
                        "irrep": irrep_name,
                        "value": f"{frac_im}*sqrt(-{p})",
                    },
                    None,
                )

        # Check for non-integral projection
        if tot_re4 % (4 * G_ORDER) != 0:
            frac = Fraction(tot_re4, 4 * G_ORDER)
            return (
                "OUT_OF_SCOPE",
                {
                    "kind": "non_integral_multiplicity",
                    "irrep": irrep_name,
                    "value": str(frac),
                },
                None,
            )

        mult = tot_re4 // (4 * G_ORDER)
        if mult < 0:
            return (
                "OUT_OF_SCOPE",
                {
                    "kind": "negative_multiplicity",
                    "irrep": irrep_name,
                    "value": mult,
                },
                None,
            )

        if mult > 0:
            multiplicities[irrep_name] = mult

    return "SOLVED", None, multiplicities


# -------------------------------------------------------------------------
# Case Dispatcher & Input Validator
# -------------------------------------------------------------------------


def solve_mathieu_moonshine_case(case: Mapping[str, Any]) -> dict[str, Any]:
    """Validates case input and computes solution with fail-closed refusal semantics."""
    if not isinstance(case, Mapping):
        return {"id": "malformed", "status": "UNKNOWN", "refusal_code": "MALFORMED_CASE_STRUCTURE"}

    cid = str(case.get("case_id") or case.get("id") or "unknown_case")
    query = case.get("query")

    if query == "coefficients":
        max_n = case.get("max_n")
        if not is_exact_int(max_n) or max_n < 1 or max_n > 30:
            return {"id": cid, "status": "UNKNOWN", "refusal_code": "MAX_N_OUT_OF_BOUNDS"}

        a_coeffs = compute_coefficients_exact(max_n)
        return {"id": cid, "status": "SOLVED", "A": a_coeffs}

    elif query == "decompose":
        class_order = case.get("class_order")
        values = case.get("values")

        if not isinstance(class_order, list) or len(class_order) != 26:
            return {"id": cid, "status": "UNKNOWN", "refusal_code": "MALFORMED_CASE_STRUCTURE"}
        if not isinstance(values, list) or len(values) != 26:
            return {"id": cid, "status": "UNKNOWN", "refusal_code": "MALFORMED_CASE_STRUCTURE"}
        if len(set(class_order)) != 26:
            return {"id": cid, "status": "UNKNOWN", "refusal_code": "MALFORMED_CASE_STRUCTURE"}

        # Validate class names
        for c in class_order:
            if c not in CLASS_INDEX_MAP:
                return {"id": cid, "status": "UNKNOWN", "refusal_code": "UNRECOGNIZED_CLASS_NAME"}

        # Validate values (strict boolean rejection)
        for v in values:
            if isinstance(v, bool):
                return {"id": cid, "status": "UNKNOWN", "refusal_code": "MALFORMED_CASE_STRUCTURE"}

        try:
            verdict, witness, mults = decompose_m24_character(class_order, values)
        except Exception:
            return {"id": cid, "status": "UNKNOWN", "refusal_code": "MALFORMED_CASE_STRUCTURE"}

        if verdict == "OUT_OF_SCOPE":
            return {"id": cid, "status": "OUT_OF_SCOPE", "witness": witness}

        return {
            "id": cid,
            "status": "SOLVED",
            "multiplicities": mults or {},
            "zero_elsewhere": True,
        }

    elif query == "specialization_z0":
        # Dynamic topological evaluation of K3 elliptic genus at z=0 (y=1)
        # Evaluates Z(tau, z) at y=1 and verifies chi(K3) = 24 with vanishing higher q powers
        z_series = compute_k3_elliptic_genus(5)
        chi = poly_eval(z_series.get(0, {}), 1)
        if chi != 24:
            raise ArithmeticError(f"K3 elliptic genus normalization failure: chi = {chi} != 24")
        for m in range(1, 6):
            sum_m = poly_eval(z_series.get(m, {}), 1)
            if sum_m != 0:
                raise ArithmeticError(
                    f"K3 elliptic genus non-vanishing at order q^{m}: sum = {sum_m}"
                )
        return {"id": cid, "status": "SOLVED", "constant": chi}

    else:
        return {"id": cid, "status": "UNKNOWN", "refusal_code": "UNRECOGNIZED_QUERY"}
