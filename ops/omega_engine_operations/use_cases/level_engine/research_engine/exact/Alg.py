# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Real algebraic numbers by isolating intervals, and rational intervals.

``Alg(poly, lo, hi)`` names the unique real root of the squarefree monic
``poly`` in the half-open interval ``(lo, hi]``.  Construction checks the root
count exactly with a Sturm sequence.

Equality is exact: two such numbers are equal exactly when the gcd of their
polynomials has a root in the intersection of their intervals (a root of the
gcd inside an isolating interval is that interval's root).  Order refines
until the intervals are disjoint.

AuthorityEffect: None
"""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import ExactError
from . import poly as P
from .q import Q

REFINE_BUDGET = 4096


@dataclass(frozen=True)
class Interval:
    """A closed rational interval ``[lo, hi]`` with exact operations."""

    lo: Q
    hi: Q

    def __post_init__(self) -> None:
        if not isinstance(self.lo, Q) or not isinstance(self.hi, Q):
            raise ExactError("RR-FLOAT", "interval ends must be exact rationals")
        if self.hi < self.lo:
            raise ExactError("RR-INTERVAL", "empty interval")

    def __add__(self, o: "Interval") -> "Interval":
        return Interval(self.lo + o.lo, self.hi + o.hi)

    def __mul__(self, o: "Interval") -> "Interval":
        ends = [self.lo * o.lo, self.lo * o.hi, self.hi * o.lo, self.hi * o.hi]
        return Interval(min(ends), max(ends))

    def contains(self, x: Q) -> bool:
        return self.lo <= x <= self.hi

    def width(self) -> Q:
        return self.hi - self.lo


@dataclass(frozen=True)
class Alg:
    poly: P.Poly
    lo: Q
    hi: Q

    def __post_init__(self) -> None:
        p = P.trim(self.poly)
        if P.degree(p) < 1:
            raise ExactError("RR-ALG", "needs a polynomial of degree at least 1")
        if p != P.monic(p) or p != tuple(self.poly):
            raise ExactError("RR-ALG", "polynomial must be trimmed and monic")
        if P.degree(P.gcd_poly(p, P.deriv(p))) > 0:
            raise ExactError("RR-ALG", "polynomial must be squarefree")
        if P.root_count(p, self.lo, self.hi) != 1:
            raise ExactError("RR-ALG", "interval does not isolate exactly one root")

    def refine(self) -> "Alg":
        mid = (self.lo + self.hi) / Q(2)
        if P.root_count(self.poly, self.lo, mid) == 1:
            return Alg(self.poly, self.lo, mid)
        return Alg(self.poly, mid, self.hi)

    def enclosure(self) -> Interval:
        return Interval(self.lo, self.hi)


def isolate(poly: P.Poly) -> tuple[Alg, ...]:
    """Every real root of ``poly``, each isolated, in increasing order."""
    sf = P.squarefree(poly)
    if P.degree(sf) < 1:
        return ()
    b = P.cauchy_bound(sf)
    todo = [(-b, b)]
    out: list[Alg] = []
    while todo:
        lo, hi = todo.pop()
        n = P.root_count(sf, lo, hi)
        if n == 1:
            out.append(Alg(sf, lo, hi))
        elif n > 1:
            mid = (lo + hi) / Q(2)
            todo.append((lo, mid))
            todo.append((mid, hi))
    return tuple(sorted(out, key=lambda a: a.lo))


def alg_equal(a: Alg, b: Alg) -> bool:
    lo = max(a.lo, b.lo)
    hi = min(a.hi, b.hi)
    if not lo < hi:
        return False
    g = P.gcd_poly(a.poly, b.poly)
    return P.degree(g) >= 1 and P.root_count(g, lo, hi) >= 1


def alg_cmp(a: Alg, b: Alg) -> int:
    """-1, 0 or 1, exactly."""
    if alg_equal(a, b):
        return 0
    x, y = a, b
    for _ in range(REFINE_BUDGET):
        if x.hi <= y.lo:
            return -1
        if y.hi <= x.lo:
            return 1
        x, y = x.refine(), y.refine()
    raise ExactError("RR-ALG", "refinement budget exhausted")  # pragma: no cover


def alg_sign_of(a: Alg, p: P.Poly) -> int:
    """The sign of the polynomial ``p`` at the algebraic number ``a``."""
    p = P.trim(p)
    if not p:
        return 0
    g = P.gcd_poly(a.poly, p)
    if P.degree(g) >= 1 and P.root_count(g, a.lo, a.hi) >= 1:
        return 0
    x = a
    for _ in range(REFINE_BUDGET):
        if P.root_count(p, x.lo, x.hi) == 0 and not P.evaluate(p, x.lo).is_zero():
            return P.evaluate(p, x.hi).sign()
        x = x.refine()
    raise ExactError("RR-ALG", "refinement budget exhausted")  # pragma: no cover
