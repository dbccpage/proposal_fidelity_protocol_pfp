"""Trace coefficients of C032 derived from representation weight systems.

This module is the independent route used by Checker 2. It does not read the
reference solver's coefficient table. For each supported gauge factor it
builds the weight system of the representation as linear forms on a Cartan
subalgebra, forms the power sums

    p2_R(h) = sum_w (w . h)^2,    p4_R(h) = sum_w (w . h)^4

as exact integer polynomials, and solves

    p2_R = A^R p2_F,    p4_R = B^R p4_F + C^R (p2_F)^2

where F is the pinned reference representation of the factor (fundamental for
SU(N) and Sp(N), vector for SO(N), 7, 26, 27 and 56 for G2, F4, E6 and E7, and
the adjoint for E8). When p4_F is proportional to (p2_F)^2 the factor has no
independent quartic Casimir; then B^R = 0 and the whole quartic trace is
carried by C^R (for SU(2): tr_fund F^4 = 1/2 (tr F^2)^2, so C_fund = 1/2).
The normalization lambda is derived as 2 h_dual / A_adj, with h_dual the dual
Coxeter number.

The exceptional weight systems are cut out of the E8 root system: the E7
Cartan is the orthogonal complement of one E8 root, and the E6 Cartan the
orthogonal complement of an A2 pair of roots.

Every weight is scaled by 2 so that all arithmetic is over the integers; the
ratios A, B, C are unchanged by a common scale.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from itertools import combinations, product

Poly = dict[tuple[int, ...], int]

SUPPORTED_GROUPS: frozenset[str] = frozenset(
    [f"SU({n})" for n in range(2, 9)]
    + [f"SO({n})" for n in (7, 9, 10, 11, 12, 13, 14)]
    + [f"Sp({n})" for n in range(1, 5)]
    + ["G2", "F4", "E6", "E7", "E8"]
)

_DUAL_COXETER_EXCEPTIONAL = {"G2": 4, "F4": 9, "E6": 12, "E7": 18, "E8": 30}

_PSEUDOREAL: frozenset[tuple[str, str]] = frozenset(
    [("SU(2)", "fund")]
    + [(f"Sp({n})", "fund") for n in range(1, 5)]
    + [("E7", "fund")]
    + [(f"SO({n})", "spinor") for n in (11, 12, 13)]
)


class WeightDerivationError(ValueError):
    """Raised when a group or representation is outside the supported set."""


def _family_rank(group: str) -> tuple[str, int]:
    if group not in SUPPORTED_GROUPS:
        raise WeightDerivationError(f"unsupported group {group!r}")
    if group[:3] in ("SU(", "SO(", "Sp("):
        return group[:2], int(group[3:-1])
    return group, 0


def canonical_rep(group: str, rep: str) -> str:
    """Maps an accepted representation name to fund, antisym, sym, spinor or adj."""
    if not isinstance(rep, str):
        raise WeightDerivationError(f"representation must be a string, got {rep!r}")
    family, n = _family_rank(group)
    if rep == "adj":
        return "adj"
    if family == "SU":
        if rep in ("fund", str(n)):
            return "fund"
        if rep in ("antisym", f"AS_{n * (n - 1) // 2}"):
            return "antisym"
        if rep in ("sym", f"S_{n * (n + 1) // 2}"):
            return "sym"
    elif family == "SO":
        if rep in ("vect", "fund", str(n)):
            return "fund"
        if rep in ("spinor", "spin"):
            return "spinor"
    elif family == "Sp":
        if rep in ("fund", str(2 * n)):
            return "fund"
        if rep in ("antisym", f"AS_{n * (2 * n - 1) - 1}"):
            return "antisym"
    else:
        names = {"G2": "7", "F4": "26", "E6": "27", "E7": "56"}
        if family in names and rep in ("fund", names[family]):
            return "fund"
    raise WeightDerivationError(f"unsupported representation {rep!r} of {group}")


def _unit(r: int, i: int, scale: int = 2) -> tuple[int, ...]:
    return tuple(scale if k == i else 0 for k in range(r))


def _add(*forms: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sum(c) for c in zip(*forms))


def _neg(form: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(-c for c in form)


def _combine(coeffs: tuple[int, ...], basis: list[tuple[int, ...]]) -> tuple[int, ...]:
    """Returns sum_i coeffs[i] * basis[i] as a linear form (coefficients are integers)."""
    r = len(basis[0])
    return tuple(sum(c * b[k] for c, b in zip(coeffs, basis)) for k in range(r))


def _su_coordinates(n: int) -> list[tuple[int, ...]]:
    """Coordinates h_1..h_n on the SU(n) Cartan, with h_n = -(h_1 + ... + h_{n-1})."""
    r = n - 1
    coords = [_unit(r, i) for i in range(r)]
    coords.append(_neg(_add(*coords)))
    return coords


def _su_weights(n: int, rep: str) -> list[tuple[int, ...]]:
    h = _su_coordinates(n)
    zero = tuple(0 for _ in range(n - 1))
    if rep == "fund":
        return list(h)
    if rep == "antisym":
        return [_add(h[i], h[j]) for i, j in combinations(range(n), 2)]
    if rep == "sym":
        return [_add(h[i], h[j]) for i in range(n) for j in range(i, n)]
    if rep == "adj":
        roots = [_add(h[i], _neg(h[j])) for i in range(n) for j in range(n) if i != j]
        return roots + [zero] * (n - 1)
    raise WeightDerivationError(f"unsupported SU({n}) representation {rep!r}")


def _so_weights(n: int, rep: str) -> list[tuple[int, ...]]:
    r = n // 2
    h = [_unit(r, i) for i in range(r)]
    zero = tuple(0 for _ in range(r))
    odd = n % 2 == 1
    if rep == "fund":
        return [s for i in range(r) for s in (h[i], _neg(h[i]))] + ([zero] if odd else [])
    if rep == "spinor":
        out = []
        for signs in product((1, -1), repeat=r):
            if not odd and signs.count(-1) % 2 == 1:
                continue
            out.append(tuple(s for s in signs))
        return out
    if rep == "adj":
        roots = [
            _add(a, b)
            for i, j in combinations(range(r), 2)
            for a in (h[i], _neg(h[i]))
            for b in (h[j], _neg(h[j]))
        ]
        if odd:
            roots += [s for i in range(r) for s in (h[i], _neg(h[i]))]
        return roots + [zero] * r
    raise WeightDerivationError(f"unsupported SO({n}) representation {rep!r}")


def _sp_weights(n: int, rep: str) -> list[tuple[int, ...]]:
    h = [_unit(n, i) for i in range(n)]
    zero = tuple(0 for _ in range(n))
    pairs = [
        _add(a, b)
        for i, j in combinations(range(n), 2)
        for a in (h[i], _neg(h[i]))
        for b in (h[j], _neg(h[j]))
    ]
    if rep == "fund":
        return [s for i in range(n) for s in (h[i], _neg(h[i]))]
    if rep == "antisym":
        return pairs + [zero] * (n - 1)
    if rep == "adj":
        longs = [s for i in range(n) for s in (_add(h[i], h[i]), _neg(_add(h[i], h[i])))]
        return pairs + longs + [zero] * n
    raise WeightDerivationError(f"unsupported Sp({n}) representation {rep!r}")


def _g2_weights(rep: str) -> list[tuple[int, ...]]:
    h = _su_coordinates(3)
    zero = (0, 0)
    short = [s for i in range(3) for s in (h[i], _neg(h[i]))]
    if rep == "fund":
        return short + [zero]
    if rep == "adj":
        long_roots = [_add(h[i], _neg(h[j])) for i in range(3) for j in range(3) if i != j]
        return long_roots + short + [zero, zero]
    raise WeightDerivationError(f"unsupported G2 representation {rep!r}")


def _f4_weights(rep: str) -> list[tuple[int, ...]]:
    h = [_unit(4, i) for i in range(4)]
    zero = (0, 0, 0, 0)
    short = [s for i in range(4) for s in (h[i], _neg(h[i]))]
    short += [tuple(signs) for signs in product((1, -1), repeat=4)]
    if rep == "fund":
        return short + [zero, zero]
    if rep == "adj":
        long_roots = [
            _add(a, b)
            for i, j in combinations(range(4), 2)
            for a in (h[i], _neg(h[i]))
            for b in (h[j], _neg(h[j]))
        ]
        return long_roots + short + [zero] * 4
    raise WeightDerivationError(f"unsupported F4 representation {rep!r}")


def _e8_roots_doubled() -> list[tuple[int, ...]]:
    """E8 roots in R^8, scaled by 2: 2(+-e_i +- e_j) and (+-1)^8 with an even number of minus signs."""
    roots: list[tuple[int, ...]] = []
    for i, j in combinations(range(8), 2):
        for si in (2, -2):
            for sj in (2, -2):
                v = [0] * 8
                v[i], v[j] = si, sj
                roots.append(tuple(v))
    for signs in product((1, -1), repeat=8):
        if signs.count(-1) % 2 == 0:
            roots.append(tuple(signs))
    return roots


def _dot(u: tuple[int, ...], v: tuple[int, ...]) -> int:
    return sum(a * b for a, b in zip(u, v))


def _exceptional_from_e8(group: str, rep: str) -> list[tuple[int, ...]]:
    roots = _e8_roots_doubled()
    if group == "E8":
        if rep != "adj":
            raise WeightDerivationError(f"unsupported E8 representation {rep!r}")
        basis = [tuple(2 if k == i else 0 for k in range(8)) for i in range(8)]
        return [_restrict(beta, basis) for beta in roots] + [tuple([0] * 8)] * 8

    alpha1 = (1,) * 8  # 2 * (1/2, ..., 1/2)
    if group == "E7":
        # Cartan: sum h = 0; free coordinates t_1..t_7, h_8 = -(t_1 + ... + t_7).
        basis = [tuple(2 if k == i else (-2 if k == 7 else 0) for k in range(8)) for i in range(7)]
        if rep == "adj":
            picked = [b for b in roots if _dot(b, alpha1) == 0]
            zeros = 7
        elif rep == "fund":
            # (56, 2) in 248 = (133, 1) + (1, 3) + (56, 2): roots with beta.alpha1 = 1.
            picked = [b for b in roots if _dot(b, alpha1) == 4]
            zeros = 0
        else:
            raise WeightDerivationError(f"unsupported E7 representation {rep!r}")
        return [_restrict(b, basis) for b in picked] + [tuple([0] * 7)] * zeros

    if group == "E6":
        alpha2 = (-2, -2, 0, 0, 0, 0, 0, 0)  # 2 * (-e_1 - e_2); alpha1.alpha2 = -1
        # Cartan: sum h = 0 and h_1 + h_2 = 0; free t_1..t_6.
        basis = [(2, -2, 0, 0, 0, 0, 0, 0)]
        for i in range(2, 7):
            basis.append(tuple(2 if k == i else (-2 if k == 7 else 0) for k in range(8)))
        if rep == "adj":
            picked = [b for b in roots if _dot(b, alpha1) == 0 and _dot(b, alpha2) == 0]
            zeros = 6
        elif rep == "fund":
            # (27, 3) in 248: roots whose A2 labels are those of the highest weight of 3.
            picked = [b for b in roots if _dot(b, alpha1) == 4 and _dot(b, alpha2) == 0]
            zeros = 0
        else:
            raise WeightDerivationError(f"unsupported E6 representation {rep!r}")
        return [_restrict(b, basis) for b in picked] + [tuple([0] * 6)] * zeros

    raise WeightDerivationError(f"unsupported group {group!r}")


def _restrict(beta: tuple[int, ...], basis: list[tuple[int, ...]]) -> tuple[int, ...]:
    """Linear form t -> beta . (sum_k t_k basis_k) / 4, kept integral up to a common factor.

    beta and every basis vector carry a factor 2, so beta . basis_k carries 4;
    dividing by 2 leaves the uniform weight scale 2 used everywhere else.
    """
    out = []
    for b in basis:
        d = _dot(beta, b)
        if d % 2:
            raise WeightDerivationError("non-integral restricted weight")
        out.append(d // 2)
    return tuple(out)


@lru_cache(maxsize=None)
def weights(group: str, rep: str) -> tuple[tuple[int, ...], ...]:
    """Weight system (with multiplicity) of rep, as doubled integer linear forms."""
    family, n = _family_rank(group)
    key = canonical_rep(group, rep)
    if family == "SU":
        out = _su_weights(n, key)
    elif family == "SO":
        out = _so_weights(n, key)
    elif family == "Sp":
        out = _sp_weights(n, key)
    elif family == "G2":
        out = _g2_weights(key)
    elif family == "F4":
        out = _f4_weights(key)
    else:
        out = _exceptional_from_e8(family, key)
    return tuple(out)


def rep_dim(group: str, rep: str) -> int:
    """Dimension of rep, counted as the number of weights."""
    return len(weights(group, rep))


def group_dim(group: str) -> int:
    return rep_dim(group, "adj")


def is_pseudoreal(group: str, rep: str) -> bool:
    return (group, canonical_rep(group, rep)) in _PSEUDOREAL


def _power_sum(forms: tuple[tuple[int, ...], ...], degree: int) -> Poly:
    poly: Poly = {}
    for form in forms:
        _accumulate_power(poly, form, degree)
    return {k: v for k, v in poly.items() if v != 0}


def _accumulate_power(poly: Poly, form: tuple[int, ...], degree: int) -> None:
    support = [i for i, c in enumerate(form) if c != 0]
    if not support:
        return
    r = len(form)
    for exps in _compositions(degree, len(support)):
        coeff = _multinomial(degree, exps)
        for idx, e in zip(support, exps):
            coeff *= form[idx] ** e
        key = [0] * r
        for idx, e in zip(support, exps):
            key[idx] = e
        k = tuple(key)
        poly[k] = poly.get(k, 0) + coeff


@lru_cache(maxsize=None)
def _compositions(total: int, parts: int) -> tuple[tuple[int, ...], ...]:
    if parts == 1:
        return ((total,),)
    out = []
    for first in range(total + 1):
        for rest in _compositions(total - first, parts - 1):
            out.append((first,) + rest)
    return tuple(out)


def _multinomial(total: int, exps: tuple[int, ...]) -> int:
    result = 1
    remaining = total
    for e in exps:
        result *= _binom(remaining, e)
        remaining -= e
    return result


def _binom(n: int, k: int) -> int:
    num, den = 1, 1
    for i in range(k):
        num *= n - i
        den *= i + 1
    return num // den


def _poly_mul(p: Poly, q: Poly) -> Poly:
    out: Poly = {}
    for kp, vp in p.items():
        for kq, vq in q.items():
            k = tuple(a + b for a, b in zip(kp, kq))
            out[k] = out.get(k, 0) + vp * vq
    return {k: v for k, v in out.items() if v != 0}


def _proportional(target: Poly, base: Poly) -> Fraction | None:
    """Returns c with target == c * base exactly, or None."""
    if not base:
        return None
    k0 = next(iter(base))
    c = Fraction(target.get(k0, 0), base[k0])
    keys = set(target) | set(base)
    for k in keys:
        if Fraction(target.get(k, 0)) != c * base.get(k, 0):
            return None
    return c


def reference_rep(group: str) -> str:
    """The representation whose trace defines tr in TASK.md."""
    return "adj" if group == "E8" else "fund"


@lru_cache(maxsize=None)
def _reference_polys(group: str) -> tuple[Poly, Poly, Poly]:
    ref = weights(group, reference_rep(group))
    p2 = _power_sum(ref, 2)
    p4 = _power_sum(ref, 4)
    return p2, p4, _poly_mul(p2, p2)


def has_independent_quartic(group: str) -> bool:
    """True when p4 of the reference representation is not a multiple of (p2)^2."""
    _, p4, p2sq = _reference_polys(group)
    return _proportional(p4, p2sq) is None


@lru_cache(maxsize=None)
def trace_coefficients(group: str, rep: str) -> tuple[Fraction, Fraction, Fraction]:
    """Exact (A^R, B^R, C^R) derived from the weight system of rep."""
    p2f, p4f, p2sq = _reference_polys(group)
    ws = weights(group, rep)
    p2r = _power_sum(ws, 2)
    p4r = _power_sum(ws, 4)

    if not p2r:
        a_coef = Fraction(0)
    else:
        found = _proportional(p2r, p2f)
        if found is None:
            raise WeightDerivationError(
                f"p2 of {rep} is not a multiple of p2 of the reference for {group}"
            )
        a_coef = found

    if not has_independent_quartic(group):
        if not p4r:
            return a_coef, Fraction(0), Fraction(0)
        c_only = _proportional(p4r, p2sq)
        if c_only is None:
            raise WeightDerivationError(f"p4 of {rep} is not a multiple of (p2)^2 for {group}")
        return a_coef, Fraction(0), c_only

    b_coef, c_coef = _solve_two(p4r, p4f, p2sq)
    return a_coef, b_coef, c_coef


def _solve_two(target: Poly, u: Poly, v: Poly) -> tuple[Fraction, Fraction]:
    """Solves target == b*u + c*v exactly and verifies it on every monomial."""
    keys = sorted(set(u) | set(v) | set(target))
    for i, k1 in enumerate(keys):
        for k2 in keys[i + 1 :]:
            det = u.get(k1, 0) * v.get(k2, 0) - u.get(k2, 0) * v.get(k1, 0)
            if det == 0:
                continue
            t1, t2 = target.get(k1, 0), target.get(k2, 0)
            b = Fraction(t1 * v.get(k2, 0) - t2 * v.get(k1, 0), det)
            c = Fraction(u.get(k1, 0) * t2 - u.get(k2, 0) * t1, det)
            for k in keys:
                if Fraction(target.get(k, 0)) != b * u.get(k, 0) + c * v.get(k, 0):
                    raise WeightDerivationError(
                        "quartic trace is not in the span of tr F^4 and (tr F^2)^2"
                    )
            return b, c
    raise WeightDerivationError("reference quartic polynomials are dependent")


def dual_coxeter(group: str) -> int:
    family, n = _family_rank(group)
    if family == "SU":
        return n
    if family == "SO":
        return n - 2
    if family == "Sp":
        return n + 1
    return _DUAL_COXETER_EXCEPTIONAL[family]


@lru_cache(maxsize=None)
def normalization_lambda(group: str) -> int:
    """lambda = 2 h_dual / A_adj, the Dynkin index of the reference representation."""
    a_adj, _, _ = trace_coefficients(group, "adj")
    lam = Fraction(2 * dual_coxeter(group)) / a_adj
    if lam.denominator != 1:
        raise WeightDerivationError(f"non-integral normalization for {group}: {lam}")
    return int(lam)
