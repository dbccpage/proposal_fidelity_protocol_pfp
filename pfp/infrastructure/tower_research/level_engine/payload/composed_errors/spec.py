# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Errors from several sources composed over a finite outcome space with
exact weights, under a declared rule: the algebraic sum (the bound covers
the sum of worst-case errors), independence (the sources must be pairwise
independent under the weights, decided from their joint law, and the
squared bound covers the sum of their variances) or justified dependence
(the squared bound covers the variance of the composed error, with every
covariance).  The composed error is the pointwise sum.

The claim: outcomes (each carrying its weight), sources, cells (each
carrying an error value) and one bound (carrying the bound), ``err(c, s,
o)`` (cell ``c`` is source ``s``'s error at outcome ``o``), ``total(c,
o)`` (cell ``c`` is the claimed composed error at ``o``) and the rule, one
of ``by_sum(b)``, ``by_independence(b)`` and ``by_dependence(b)``.

Relational clauses, carried by derivability over the hosted claim:
``errors_total``, ``one_error``, ``totals_given`` and ``one_total``.

Decoded clauses, decided outside the grammar: ``well_formed`` (positive
weights summing to one, one rule, a nonnegative bound),
``independence_justified`` (the refused case: two correlated sources
assumed independent), ``sum_bound``, ``variance_bound`` and
``composed_exact``.  No root is taken: bounds are compared through squares.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import ZERO, Q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import rows

CHALLENGE_ID = "composed_errors"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "independence_justified", "sum_bound", "variance_bound", "composed_exact")


def weights(fs: FiniteStructure) -> list[Q]:
    return [w if (w := fs.value(o)) is not None else ZERO for o in fs.elements("outcome")]


def errors(fs: FiniteStructure) -> list[list[Q]]:
    got = {(s, o): fs.value(c) for c, s, o in rows(fs, "err")}
    return [[v if (v := got.get((s, o))) is not None else ZERO for o in fs.elements("outcome")]
            for s in fs.elements("source")]


def composed(fs: FiniteStructure) -> list[Q]:
    got = {o: fs.value(c) for c, o in rows(fs, "total")}
    return [v if (v := got.get(o)) is not None else ZERO for o in fs.elements("outcome")]


def rule(fs: FiniteStructure) -> str | None:
    got = [r for name, r in (("by_sum", "sum"), ("by_independence", "independent"), ("by_dependence", "dependent"))
           for _ in rows(fs, name)]
    return got[0] if len(got) == 1 else None


def bound(fs: FiniteStructure) -> Q:
    b = [fs.value(e) for e in fs.elements("bound")]
    return b[0] if len(b) == 1 and b[0] is not None else ZERO


def _mean(values: list[Q], w: list[Q]) -> Q:
    return sum((v * x for v, x in zip(values, w)), ZERO)


def _variance(values: list[Q], w: list[Q]) -> Q:
    m = _mean(values, w)
    return _mean([(v - m) * (v - m) for v in values], w)


def _independent(xs: list[Q], ys: list[Q], w: list[Q]) -> bool:
    def law(values: list[object]) -> dict[object, Q]:
        out: dict[object, Q] = {}
        for v, x in zip(values, w):
            out[v] = out.get(v, ZERO) + x
        return out

    joint, px, py = law(list(zip(xs, ys))), law(list(xs)), law(list(ys))
    return all(joint.get((a, b), ZERO) == px[a] * py[b] for a in px for b in py)


def _abs(x: Q) -> Q:
    return -x if x.sign() < 0 else x


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    w = weights(fs)
    return (bool(w) and all(x.sign() > 0 for x in w) and sum(w, ZERO) == Q(1) and rule(fs) is not None
            and bound(fs).sign() >= 0)


def independence_justified(fs: FiniteStructure, _o: Oracle) -> bool:
    if rule(fs) != "independent":
        return True
    es, w = errors(fs), weights(fs)
    return all(_independent(a, b, w) for i, a in enumerate(es) for b in es[i + 1:])


def sum_bound(fs: FiniteStructure, _o: Oracle) -> bool:
    return rule(fs) != "sum" or bound(fs) >= sum((max(_abs(v) for v in xs) for xs in errors(fs)), ZERO)


def variance_bound(fs: FiniteStructure, _o: Oracle) -> bool:
    b, es, w = bound(fs), errors(fs), weights(fs)
    if rule(fs) == "independent":
        return b * b >= sum((_variance(xs, w) for xs in es), ZERO)
    if rule(fs) == "dependent":
        return b * b >= _variance([sum(col, ZERO) for col in zip(*es)], w)
    return True


def composed_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    return composed(fs) == [sum(col, ZERO) for col in zip(*errors(fs))]


def describe(fs: FiniteStructure) -> dict[str, object]:
    w, es = weights(fs), errors(fs)
    total = [sum(col, ZERO) for col in zip(*es)]
    return {"variance_of_total": str(_variance(total, w)) if total else None}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    outcome, source, err, total = e.form("outcome"), e.form("source"), e.form("err"), e.form("total")
    return Compiled(
        (
            Total("errors_total", ((source, ("s",)), (outcome, ("o",))), ((err, ("c", "s", "o")),)),
            Functional("one_error", err, 1),
            Total("totals_given", ((outcome, ("o",)),), ((total, ("c", "o")),)),
            Functional("one_total", total, 1),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("independence_justified", independence_justified),
            ("sum_bound", sum_bound), ("variance_bound", variance_bound), ("composed_exact", composed_exact))),
    )
