# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A finite family of outcome weights, each a polynomial in k parameters with
exact rational coefficients, an interior point, and a declared information
table: the weights must sum to one identically and be positive at the
point, and the declared table must have no direction of negative value and
be the recomputed table.

The claim: outcomes, parameters and terms (each in declared order), numbers
(exact values), ``power(t, p, e)`` (term ``t`` carries parameter ``p`` to
the power ``e``), ``weight(o, t, c)`` (outcome ``o``'s polynomial has
coefficient ``c`` on term ``t``), ``at(p, v)`` (the point's value of
parameter ``p``) and ``declared(p, q, v)`` (the declared table's entry at
``p``, ``q``).

Relational clauses, carried by derivability over the hosted claim: every
term has one power for each parameter, every outcome one coefficient on each
term, the point one value for each parameter and the declared table one
entry for each pair of parameters, and each entry is typed.

Decoded clauses, decided over exact values outside the grammar:

* ``terms_well_formed``: powers are naturals and no two terms carry the same
  powers;
* ``weights_sum_to_one``: the outcome polynomials sum to one identically;
* ``positive_at_point``: every outcome's weight is positive at the point;
* ``no_negative_direction``: the declared table is symmetric and every
  principal minor is nonnegative (the refused case: a direction of negative
  value);
* ``table_recomputed``: the declared table is the sum over outcomes of the
  slope along ``p`` times the slope along ``q``, over the weight, at the
  point, with exact polynomial slopes.

AuthorityEffect: None
"""

from __future__ import annotations

from itertools import combinations
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.linalg import det
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO, Q, fmt_q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import rows

CHALLENGE_ID = "weight_slopes"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q", "py.exact.linalg")
CLAUSES = ("terms_well_formed", "weights_sum_to_one", "positive_at_point", "no_negative_direction",
           "table_recomputed")

# A polynomial: coefficient by power tuple (one power per parameter).
Poly = dict[tuple[int, ...], Q]


def _nat(x: Q | None) -> int | None:
    return x.num if x is not None and x.den == 1 and x.num >= 0 else None


def powers(fs: FiniteStructure) -> list[tuple[int, ...]] | None:
    """Each term's powers, by parameter in declared order; ``None`` when a
    power is missing, repeated or not a natural."""
    got: dict[tuple[int, int], int] = {}
    for t, p, e in rows(fs, "power"):
        n = _nat(fs.value(e))
        if n is None or (t, p) in got:
            return None
        got[(t, p)] = n
    params = fs.elements("parameter")
    if any((t, p) not in got for t in fs.elements("term") for p in params):
        return None
    return [tuple(got[(t, p)] for p in params) for t in fs.elements("term")]


def family(fs: FiniteStructure) -> list[Poly] | None:
    """Each outcome's polynomial; ``None`` when the terms are not well
    formed or a coefficient is missing, repeated or has no value."""
    pw = powers(fs)
    if pw is None or len(set(pw)) != len(pw):
        return None
    got: dict[tuple[int, int], Q] = {}
    for o, t, c in rows(fs, "weight"):
        v = fs.value(c)
        if v is None or (o, t) in got:
            return None
        got[(o, t)] = v
    terms = fs.elements("term")
    if any((o, t) not in got for o in fs.elements("outcome") for t in terms):
        return None
    return [{pw[k]: got[(o, t)] for k, t in enumerate(terms)} for o in fs.elements("outcome")]


def point(fs: FiniteStructure) -> list[Q] | None:
    got: dict[int, Q] = {}
    for p, v in rows(fs, "at"):
        x = fs.value(v)
        if x is None or p in got:
            return None
        got[p] = x
    params = fs.elements("parameter")
    return [got[p] for p in params] if all(p in got for p in params) else None


def declared(fs: FiniteStructure) -> list[list[Q]] | None:
    got: dict[tuple[int, int], Q] = {}
    for p, q, v in rows(fs, "declared"):
        x = fs.value(v)
        if x is None or (p, q) in got:
            return None
        got[(p, q)] = x
    params = fs.elements("parameter")
    if any((p, q) not in got for p in params for q in params):
        return None
    return [[got[(p, q)] for q in params] for p in params]


def value_at(poly: Poly, at: list[Q]) -> Q:
    total = ZERO
    for pw, c in poly.items():
        term = c
        for x, e in zip(at, pw):
            for _ in range(e):
                term = term * x
        total = total + term
    return total


def slope(poly: Poly, i: int) -> Poly:
    """The exact slope of a polynomial along parameter ``i``."""
    out: Poly = {}
    for pw, c in poly.items():
        if pw[i]:
            lower = pw[:i] + (pw[i] - 1,) + pw[i + 1:]
            out[lower] = out.get(lower, ZERO) + c * Q(pw[i])
    return out


def terms_well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    pw = powers(fs)
    return pw is not None and len(set(pw)) == len(pw)


def weights_sum_to_one(fs: FiniteStructure, _o: Oracle) -> bool:
    fam = family(fs)
    if fam is None:
        return False
    total: Poly = {}
    for poly in fam:
        for pw, c in poly.items():
            total[pw] = total.get(pw, ZERO) + c
    k = len(fs.elements("parameter"))
    return {pw: c for pw, c in total.items() if not c.is_zero()} == {(0,) * k: ONE}


def positive_at_point(fs: FiniteStructure, _o: Oracle) -> bool:
    fam, at = family(fs), point(fs)
    return fam is not None and at is not None and all(value_at(p, at).sign() > 0 for p in fam)


def minors(m: list[list[Q]]) -> list[Q]:
    """Every principal minor, by size and then by rows chosen."""
    k = len(m)
    return [det([[m[i][j] for j in pick] for i in pick]) for size in range(1, k + 1)
            for pick in combinations(range(k), size)]


def no_negative_direction(fs: FiniteStructure, _o: Oracle) -> bool:
    """The refused case: a declared table with a direction of negative value."""
    m = declared(fs)
    if m is None:
        return False
    k = len(m)
    if any(m[i][j] != m[j][i] for i in range(k) for j in range(k)):
        return False
    return all(x.sign() >= 0 for x in minors(m))


def recomputed(fs: FiniteStructure) -> list[list[Q]] | None:
    fam, at = family(fs), point(fs)
    if fam is None or at is None:
        return None
    k = len(at)
    values = [value_at(p, at) for p in fam]
    if any(v.is_zero() for v in values):
        return None
    slopes = [[value_at(slope(p, i), at) for i in range(k)] for p in fam]
    return [[sum((s[i] * s[j] / v for s, v in zip(slopes, values)), ZERO) for j in range(k)] for i in range(k)]


def table_recomputed(fs: FiniteStructure, _o: Oracle) -> bool:
    r = recomputed(fs)
    return r is not None and r == declared(fs)


def describe(fs: FiniteStructure) -> dict[str, object]:
    r = recomputed(fs)
    return {"recomputed": None if r is None else [[fmt_q(x) for x in row] for row in r],
            "recomputed_minors": None if r is None else [fmt_q(x) for x in minors(r)]}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    out, par, term, num = e.form("outcome"), e.form("parameter"), e.form("term"), e.form("number")
    power, weight, at, dec = e.form("power"), e.form("weight"), e.form("at"), e.form("declared")
    return Compiled(
        (
            Total("powers_given", ((term, ("t",)), (par, ("p",))), ((power, ("t", "p", "e")), (num, ("e",)))),
            Functional("one_power", power, 2),
            Closure("powers_typed", ((power, ("t", "p", "e")),), ((term, ("t",)), (par, ("p",)), (num, ("e",)))),
            Total("coefficients_given", ((out, ("o",)), (term, ("t",))), ((weight, ("o", "t", "c")), (num, ("c",)))),
            Functional("one_coefficient", weight, 2),
            Closure("coefficients_typed", ((weight, ("o", "t", "c")),),
                    ((out, ("o",)), (term, ("t",)), (num, ("c",)))),
            Total("point_given", ((par, ("p",)),), ((at, ("p", "v")), (num, ("v",)))),
            Functional("one_point", at, 1),
            Closure("point_typed", ((at, ("p", "v")),), ((par, ("p",)), (num, ("v",)))),
            Total("table_given", ((par, ("p",)), (par, ("q",))), ((dec, ("p", "q", "v")), (num, ("v",)))),
            Functional("one_table_entry", dec, 2),
            Closure("table_typed", ((dec, ("p", "q", "v")),), ((par, ("p",)), (par, ("q",)), (num, ("v",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("terms_well_formed", terms_well_formed), ("weights_sum_to_one", weights_sum_to_one),
            ("positive_at_point", positive_at_point), ("no_negative_direction", no_negative_direction),
            ("table_recomputed", table_recomputed))),
    )
