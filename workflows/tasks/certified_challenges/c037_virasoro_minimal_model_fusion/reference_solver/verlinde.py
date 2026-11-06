"""Pure Python stdlib implementation of exact Verlinde fusion rules for C037.

Covers:
- SU(2)_k WZW models (1 <= k <= 20)
- Virasoro minimal models M(p, p') (coprime p > p' >= 2, p <= 13)

Strictly zero numpy/scipy/sympy/cvxpy dependencies.
Exact rational arithmetic via fractions.Fraction.
Zero float-rounding shortcuts.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping


def is_exact_int(val: Any) -> bool:
    """Strict check for int, rejecting bool."""
    return type(val) is int and not isinstance(val, bool)


def format_rational(frac: Fraction) -> str:
    """Formats a Fraction into canonical reduced rational string format ('int' or 'num/den')."""
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def verlinde_su2_exact(k: int, a: int, b: int, c: int) -> int:
    """Evaluates the Verlinde formula for SU(2)_k in exact algebraic rational arithmetic.

    The modular S-matrix entry is S_{ab} = sqrt(2/(k+2)) * sin(pi * (a + 1)(b + 1) / (k + 2)).
    In the Verlinde sum N_{ab}^c = sum_{m=0}^k (S_{am} S_{bm} S_{cm}) / S_{0m},
    the normalization prefactor simplifies to 2/(k+2), and the summand is
    sin((a+1)theta_m) * sin((b+1)theta_m) * (sin((c+1)theta_m) / sin(theta_m)),
    where theta_m = (m+1)*pi / (k+2).

    Using the Chebyshev identity sin((c+1)theta)/sin(theta) = sum_{l=0}^c cos((c-2l)theta)
    and product-to-sum expansions, the summand reduces to a linear combination of cosines
    cos(nu * theta_m). Over j = m + 1 in 1..(k+1), sum_{j=1}^{K-1} cos(nu * pi * j / K) evaluates
    to exact integers:
      = K - 1 if nu == 0 mod 2K
      = -1    if nu != 0 mod 2K and nu is even
      = 0     if nu is odd.
    """
    if (a + b + c) % 2 != 0:
        return 0
    if a < 0 or b < 0 or c < 0 or a > k or b > k or c > k:
        return 0

    K = k + 2
    freq_counts: dict[int, int] = {}
    for l in range(c + 1):
        diff = c - 2 * l
        for nu, sgn in (
            ((a - b) + diff, 1),
            ((a - b) - diff, 1),
            ((a + b + 2) + diff, -1),
            ((a + b + 2) - diff, -1),
        ):
            nu_abs = abs(nu)
            freq_counts[nu_abs] = freq_counts.get(nu_abs, 0) + sgn

    total = Fraction(0, 1)
    two_k = 2 * K
    for nu, count in freq_counts.items():
        if count == 0:
            continue
        if nu % two_k == 0:
            s = K - 1
        elif nu % 2 == 0:
            s = -1
        else:
            s = 0
        total += Fraction(count * s, 4)

    res = Fraction(2, K) * total
    assert res.denominator == 1, f"Verlinde coefficient not integral: {res}"
    return int(res)


def combinatorial_su2(k: int, a: int, b: int, c: int) -> int:
    """Independent truncated Clebsch-Gordan rule for SU(2)_k fusion."""
    if (a + b + c) % 2 != 0:
        return 0
    if abs(a - b) <= c <= min(a + b, 2 * k - a - b):
        return 1
    return 0


def get_canonical_kac_label(p: int, p_prime: int, r: int, s: int) -> tuple[int, int]:
    """Applies canonical selection rule (s, r) <= (p - s, p' - r) for Kac label identification."""
    r_alt = p_prime - r
    s_alt = p - s
    if (s, r) <= (s_alt, r_alt):
        return (r, s)
    return (r_alt, s_alt)


def get_minimal_model_primaries(p: int, p_prime: int) -> list[tuple[tuple[int, int], str]]:
    """Computes canonical physical primaries for Virasoro minimal model M(p, p').

    Each primary is identified under (r, s) ~ (p' - r, p - s).
    Canonical representative chosen such that (s, r) <= (p - s, p' - r).
    Primaries are ordered canonically by (r, s).
    Returns list of ((r, s), h_str).
    """
    seen: set[tuple[int, int]] = set()
    primaries: list[tuple[tuple[int, int], Fraction]] = []

    for r in range(1, p_prime):
        for s in range(1, p):
            canonical = get_canonical_kac_label(p, p_prime, r, s)
            if canonical not in seen:
                seen.add(canonical)
                num = (p * canonical[0] - p_prime * canonical[1]) ** 2 - (p - p_prime) ** 2
                den = 4 * p * p_prime
                h_frac = Fraction(num, den)
                primaries.append((canonical, h_frac))

    primaries.sort(key=lambda item: (item[0][0], item[0][1]))
    return [(pair, format_rational(h)) for pair, h in primaries]


def compute_fusion_su2(k: int) -> list[list[Any]]:
    """Computes canonical fusion list for SU(2)_k.

    Formatted as [[a], [b], [c], N_{ab}^c] with a <= b.
    """
    fusion = []
    for a in range(k + 1):
        for b in range(a, k + 1):
            c_min = abs(a - b)
            c_max = min(a + b, 2 * k - a - b)
            for c in range(c_min, c_max + 1, 2):
                val = verlinde_su2_exact(k, a, b, c)
                if val > 0:
                    fusion.append([[a], [b], [c], val])
    return fusion


def compute_fusion_minimal(
    p: int, p_prime: int, prim_labels: list[tuple[int, int]]
) -> list[list[Any]]:
    """Computes canonical fusion list for Virasoro minimal model M(p, p').

    Lifts to product of two SU(2) factors at levels k1 = p' - 2 and k2 = p - 2
    with Kac identification (r, s) ~ (p' - r, p - s).
    Formatted as [[r_i, s_i], [r_j, s_j], [r_k, s_k], N_{ij}^k] with i <= j in primary order.
    """
    k1 = p_prime - 2
    k2 = p - 2
    prim_idx = {lbl: idx for idx, lbl in enumerate(prim_labels)}
    fusion = []

    for i, p1 in enumerate(prim_labels):
        a1, b1 = p1[0] - 1, p1[1] - 1
        for j in range(i, len(prim_labels)):
            p2 = prim_labels[j]
            a2, b2 = p2[0] - 1, p2[1] - 1

            out_primaries: list[tuple[int, tuple[int, int]]] = []
            a3_min = abs(a1 - a2)
            a3_max = min(a1 + a2, 2 * k1 - a1 - a2)
            b3_min = abs(b1 - b2)
            b3_max = min(b1 + b2, 2 * k2 - b1 - b2)

            for a3 in range(a3_min, a3_max + 1, 2):
                r3 = a3 + 1
                for b3 in range(b3_min, b3_max + 1, 2):
                    s3 = b3 + 1
                    canon_p3 = get_canonical_kac_label(p, p_prime, r3, s3)
                    idx = prim_idx[canon_p3]
                    out_primaries.append((idx, canon_p3))

            out_primaries.sort(key=lambda item: item[0])
            for _, canon_p3 in out_primaries:
                fusion.append([list(p1), list(p2), list(canon_p3), 1])

    return fusion


def solve_c037_case(
    case: Mapping[str, Any],
) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
    """Validates and solves a C037 challenge case.

    Returns (status, extra, solution) where:
    - status is "SOLVED", "OUT_OF_SCOPE", or "UNKNOWN"
    - extra contains refusal metadata ("witness" or "refusal_code")
    - solution contains the solved payload
    """
    if not isinstance(case, Mapping):
        return ("UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None)

    for k_field in ("k", "p", "p_prime", "model", "case_id", "id"):
        if k_field in case and isinstance(case[k_field], bool):
            return ("UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None)

    model = case.get("model")
    if not isinstance(model, str) or model not in ("su2", "minimal"):
        return ("UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None)

    if model == "su2":
        k_val = case.get("k")
        if not is_exact_int(k_val):
            return ("UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None)

        if k_val < 1 or k_val > 20:
            return ("UNKNOWN", {"refusal_code": "LEVEL_OUT_OF_BOUNDS"}, None)

        c_frac = Fraction(3 * k_val, k_val + 2)
        central_charge = format_rational(c_frac)

        primaries = []
        for a in range(k_val + 1):
            h_frac = Fraction(a * (a + 2), 4 * (k_val + 2))
            primaries.append({"label": [a], "h": format_rational(h_frac)})

        fusion = compute_fusion_su2(k_val)

        solution = {
            "central_charge": central_charge,
            "primaries": primaries,
            "fusion": fusion,
        }
        return ("SOLVED", None, solution)

    # model == "minimal"
    p_val = case.get("p")
    p_prime_val = case.get("p_prime")

    if not is_exact_int(p_val) or not is_exact_int(p_prime_val):
        return ("UNKNOWN", {"refusal_code": "MALFORMED_CASE_STRUCTURE"}, None)

    if p_prime_val < 2:
        return (
            "OUT_OF_SCOPE",
            {"kind": "invalid_p_prime", "p_prime": p_prime_val},
            None,
        )

    g = math.gcd(p_val, p_prime_val)
    if g != 1:
        return (
            "OUT_OF_SCOPE",
            {"kind": "not_coprime", "gcd": g},
            None,
        )

    if p_val <= p_prime_val or p_val > 13:
        return ("UNKNOWN", {"refusal_code": "LEVEL_OUT_OF_BOUNDS"}, None)

    c_frac = Fraction(1) - Fraction(6 * (p_val - p_prime_val) ** 2, p_val * p_prime_val)
    central_charge = format_rational(c_frac)

    prim_info = get_minimal_model_primaries(p_val, p_prime_val)
    primaries = [{"label": list(pair), "h": h_str} for pair, h_str in prim_info]
    prim_labels = [pair for pair, _ in prim_info]

    fusion = compute_fusion_minimal(p_val, p_prime_val, prim_labels)

    solution = {
        "central_charge": central_charge,
        "primaries": primaries,
        "fusion": fusion,
    }
    return ("SOLVED", None, solution)
