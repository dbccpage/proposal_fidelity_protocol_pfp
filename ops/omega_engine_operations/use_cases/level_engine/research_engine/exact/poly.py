# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Polynomials over Q (coefficients low to high degree) and Sturm counting.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence

from ..errors import ExactError
from .q import ONE, ZERO, Q

Poly = tuple[Q, ...]


def trim(p: Sequence[Q]) -> Poly:
    out = list(p)
    while out and out[-1].is_zero():
        out.pop()
    return tuple(out)


def degree(p: Poly) -> int:
    return len(trim(p)) - 1


def add(p: Poly, r: Poly) -> Poly:
    n = max(len(p), len(r))
    return trim(
        [(p[k] if k < len(p) else ZERO) + (r[k] if k < len(r) else ZERO) for k in range(n)]
    )


def neg(p: Poly) -> Poly:
    return tuple(-c for c in p)


def sub(p: Poly, r: Poly) -> Poly:
    return add(p, neg(r))


def mul(p: Poly, r: Poly) -> Poly:
    if not p or not r:
        return ()
    out = [ZERO] * (len(p) + len(r) - 1)
    for i, a in enumerate(p):
        for j, b in enumerate(r):
            out[i + j] = out[i + j] + a * b
    return trim(out)


def divmod_poly(p: Poly, d: Poly) -> tuple[Poly, Poly]:
    d = trim(d)
    if not d:
        raise ExactError("RR-DIVISION-BY-ZERO", "division by the zero polynomial")
    rem = list(trim(p))
    quo = [ZERO] * max(len(rem) - len(d) + 1, 1)
    lead = d[-1]
    while len(rem) >= len(d) and rem:
        shift = len(rem) - len(d)
        c = rem[-1] / lead
        quo[shift] = c
        for k, dk in enumerate(d):
            rem[shift + k] = rem[shift + k] - c * dk
        rem = list(trim(rem))
    return trim(quo), trim(rem)


def deriv(p: Poly) -> Poly:
    return trim([Q(k) * p[k] for k in range(1, len(p))])


def monic(p: Poly) -> Poly:
    p = trim(p)
    if not p:
        return ()
    lead = p[-1]
    return tuple(c / lead for c in p)


def gcd_poly(p: Poly, r: Poly) -> Poly:
    a, b = trim(p), trim(r)
    while b:
        a, b = b, divmod_poly(a, b)[1]
    return monic(a)


def evaluate(p: Poly, x: Q) -> Q:
    acc = ZERO
    for c in reversed(p):
        acc = acc * x + c
    return acc


def squarefree(p: Poly) -> Poly:
    p = trim(p)
    if degree(p) < 1:
        return monic(p)
    g = gcd_poly(p, deriv(p))
    return monic(divmod_poly(p, g)[0])


def sturm_sequence(p: Poly) -> tuple[Poly, ...]:
    seq = [trim(p), deriv(trim(p))]
    while seq[-1]:
        r = divmod_poly(seq[-2], seq[-1])[1]
        if not r:
            break
        seq.append(neg(r))
    return tuple(s for s in seq if s)


def _sign_changes(seq: Sequence[Poly], x: Q) -> int:
    signs = [evaluate(s, x).sign() for s in seq]
    signs = [s for s in signs if s != 0]
    return sum(1 for a, b in zip(signs, signs[1:]) if a != b)


def root_count(p: Poly, lo: Q, hi: Q) -> int:
    """Distinct real roots of ``p`` in ``(lo, hi]`` (Sturm's theorem)."""
    if hi < lo:
        raise ExactError("RR-INTERVAL", "empty interval")
    p = trim(p)
    if not p:
        raise ExactError("RR-ZERO-POLY", "the zero polynomial has every root")
    seq = sturm_sequence(p)
    return _sign_changes(seq, lo) - _sign_changes(seq, hi)


def cauchy_bound(p: Poly) -> Q:
    """Every real root lies strictly inside ``(-B, B)``."""
    p = monic(p)
    if degree(p) < 1:
        return ONE
    m = ZERO
    for c in p[:-1]:
        a = c if c.sign() >= 0 else -c
        if a > m:
            m = a
    return ONE + m + ONE
