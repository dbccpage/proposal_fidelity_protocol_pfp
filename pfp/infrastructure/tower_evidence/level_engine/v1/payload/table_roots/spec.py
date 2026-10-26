"""A claimed polynomial and claimed roots, accepted only with the square table
they come from: the polynomial must be ``det(xI - A)`` of that table and
each root a root of it.

The claim: slots (in declared order), values, ``entry(i, j, v)`` (the
table), ``coef(p, v)`` (the claimed coefficient of ``x`` to the power ``p``)
and ``root(v)`` (a claimed root).

Relational clauses, carried by derivability over the hosted claim:
``table_given`` (the table has at least one slot: roots claimed with no
table are refused), ``entries_complete``, ``one_entry``, ``entries_typed``,
``one_coef`` and ``coef_typed``.

Decoded clauses, decided over exact values outside the grammar:
``polynomial`` (the claimed coefficients are those of ``det(xI - A)``,
computed by the Faddeev-LeVerrier recurrence, never read) and
``roots_vanish`` (each claimed root is a root of the computed polynomial).
Both are the table polynomial level's own clauses; the kernel re-decides
them with its definitions.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from engine.encoding import Encoding
from engine.exact.poly import evaluate as value_at
from engine.exact.q import Q, fmt_q
from engine.kinds import Closure, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import certificates, lean_list, lean_q, render, rows
from payload.table_polynomial.spec import LEAN_DEFS as POLY_DEFS
from payload.table_polynomial.spec import computed, declared, polynomial, table

CHALLENGE_ID = "table_roots"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "TableRoots"
EXACT = ("py.exact.q", "py.exact.linalg")
CLAUSES = ("polynomial", "roots_vanish")


def roots(fs: FiniteStructure) -> list[Q | None]:
    return [fs.value(r) for (r,) in rows(fs, "root")]


def roots_vanish(fs: FiniteStructure, _o: Oracle) -> bool:
    c = computed(fs)
    return c is not None and all(r is not None and value_at(c, r).is_zero() for r in roots(fs))


def describe(fs: FiniteStructure) -> dict[str, object]:
    c = computed(fs)
    return {"polynomial_low_to_high": None if c is None else [fmt_q(x) for x in c]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "polynomial")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    slot, val, entry, coef = e.form("slot"), e.form("val"), e.form("entry"), e.form("coef")
    return Compiled(
        (
            Total("table_given", (), ((slot, ("s",)),)),
            Total("entries_complete", ((slot, ("i",)), (slot, ("j",))), ((entry, ("i", "j", "v")),)),
            Functional("one_entry", entry, 2),
            Closure("entries_typed", ((entry, ("i", "j", "v")),), ((slot, ("i",)), (slot, ("j",)), (val, ("v",)))),
            Functional("one_coef", coef, 1),
            Closure("coef_typed", ((coef, ("p", "v")),), ((val, ("p",)), (val, ("v",)))),
        ),
        decoded=(DecodedClause("polynomial", polynomial, EXACT), DecodedClause("roots_vanish", roots_vanish, EXACT)),
    )


LEAN_CALLS = {"polynomial": "polynomial table_{f} coefs_{f}", "roots_vanish": "rootsVanish table_{f} roots_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    from engine import lean_text as T

    a, d = table(fs), declared(fs)
    assert a is not None and d is not None
    return [("table", "Mat", T.mat(a)),
            ("coefs", "List QN", lean_list([lean_q(d[k]) for k in sorted(d, reverse=True)])),
            ("roots", "List QN", lean_list([lean_q(r) for r in roots(fs) if r is not None]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clauses of `table_roots`, decided by the kernel", POLY_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
