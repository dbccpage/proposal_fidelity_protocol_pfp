"""A finite base of objects and arrows, a fibre of terms over each object, and
for each arrow a reindexing table taking the fibre over its target to the
fibre over its source (contravariantly): the tables land in the right
fibres, identities reindex as the identity, and each declared composite
reindexes as the composite of the tables.

The claim: objects, terms and arrows (each in declared order),
``over(x, o)`` (term ``x`` lies over object ``o``), ``runs(a, s, t)``
(arrow ``a`` runs from ``s`` to ``t``), ``sends(a, x, y)`` (arrow ``a``'s
table sends ``x`` to ``y``), ``identity(o, a)`` and ``composite(f, g,
h)`` (``h`` is ``g`` after ``f``, so its table is ``f``'s after ``g``'s).

Relational clauses, carried by derivability over the hosted claim:
``over_given``, ``one_over`` (fibres are disjoint), ``runs_given``,
``one_runs``, ``table_total`` and ``table_within`` (each table is a map on
the fibre over its arrow's target), ``one_image``, ``right_fibre`` (every
image lies over the arrow's source: the refused case is a term reindexed
into the wrong fibre), ``identity_given``, ``identity_endo``,
``identity_fixes``, ``chain_middle`` and ``chain_ends`` (a composite's
arrows chain), ``functorial`` (the composite's table is the tables
composed) and the typing closures.

Decoded clause, decided outside the grammar: ``base_closed`` (every
composable pair of non-identity arrows has a declared composite).  Its Lean
certificate is re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from engine.encoding import Encoding
from engine.kinds import Closure, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "reindexed_fibres"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "ReindexedFibres"
EXACT: tuple[str, ...] = ()
CLAUSES = ("base_closed",)


def _a(fs: FiniteStructure, e: int) -> int:
    k = position(fs, "arrow", e)
    return -1 if k is None else k


def arrows(fs: FiniteStructure) -> list[tuple[int, int]]:
    """Each arrow's (source, target) by object positions; -1 when unknown."""
    got: dict[int, tuple[int | None, int | None]] = {}
    for a, src, tgt in rows(fs, "runs"):
        got[a] = (position(fs, "object", src), position(fs, "object", tgt))
    out = []
    for a in fs.elements("arrow"):
        s, t = got.get(a, (None, None))
        out.append((-1 if s is None else s, -1 if t is None else t))
    return out


def identities(fs: FiniteStructure) -> list[int]:
    return sorted(_a(fs, a) for _, a in rows(fs, "identity"))


def composites(fs: FiniteStructure) -> list[tuple[int, int]]:
    return sorted((_a(fs, f), _a(fs, g)) for f, g, _ in rows(fs, "composite"))


def base_closed(fs: FiniteStructure, _o: Oracle) -> bool:
    ar, ids, comp = arrows(fs), set(identities(fs)), set(composites(fs))
    return all((f, g) in comp for f, (_, ft) in enumerate(ar) for g, (gs, _) in enumerate(ar)
               if f not in ids and g not in ids and ft == gs and ft != -1)


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"composites": [list(c) for c in composites(fs)]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "base_closed")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    obj, term, arrow = e.form("object"), e.form("term"), e.form("arrow")
    over, runs, sends, ident, comp = e.form("over"), e.form("runs"), e.form("sends"), e.form("identity"), e.form(
        "composite")
    return Compiled(
        (
            Total("over_given", ((term, ("x",)),), ((over, ("x", "o")),)),
            Functional("one_over", over, 1),
            Total("runs_given", ((arrow, ("a",)),), ((runs, ("a", "s", "t")),)),
            Functional("one_runs", runs, 1),
            Total("table_total", ((runs, ("a", "s", "t")), (over, ("x", "t"))), ((sends, ("a", "x", "y")),)),
            Closure("table_within", ((sends, ("a", "x", "y")), (runs, ("a", "s", "t"))), ((over, ("x", "t")),)),
            Functional("one_image", sends, 2),
            Closure("right_fibre", ((sends, ("a", "x", "y")), (runs, ("a", "s", "t"))), ((over, ("y", "s")),)),
            Total("identity_given", ((obj, ("o",)),), ((ident, ("o", "a")),)),
            Closure("identity_endo", ((ident, ("o", "a")),), ((runs, ("a", "o", "o")),)),
            Closure("identity_fixes", ((ident, ("o", "a")), (over, ("x", "o"))), ((sends, ("a", "x", "x")),)),
            Total("chain_middle", ((comp, ("f", "g", "h")), (runs, ("f", "a", "b"))), ((runs, ("g", "b", "c")),)),
            Closure("chain_ends", ((comp, ("f", "g", "h")), (runs, ("f", "a", "b")), (runs, ("g", "b", "c"))),
                    ((runs, ("h", "a", "c")),)),
            Closure("functorial", ((comp, ("f", "g", "h")), (sends, ("g", "x", "y")), (sends, ("f", "y", "z"))),
                    ((sends, ("h", "x", "z")),)),
            Closure("over_typed", ((over, ("x", "o")),), ((term, ("x",)), (obj, ("o",)))),
            Closure("sends_typed", ((sends, ("a", "x", "y")),), ((arrow, ("a",)), (term, ("x",)), (term, ("y",)))),
        ),
        decoded=(DecodedClause("base_closed", base_closed, EXACT),),
    )


LEAN_DEFS = (
    "/-- Every composable pair of non-identity arrows has a declared composite. -/",
    "def baseClosed (ar : List (Prod Nat Nat)) (ids : List Nat) (comp : List (Prod Nat Nat)) : Bool :=",
    "  (List.range ar.length).all fun f => (List.range ar.length).all fun g =>",
    "    ids.contains f || ids.contains g || (ar.getD f (0, 0)).2 != (ar.getD g (0, 0)).1 || comp.contains (f, g)",
    "",
)
LEAN_CALLS = {"base_closed": "baseClosed arrows_{f} ids_{f} comps_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    ar = arrows(fs)
    assert all(s >= 0 and t >= 0 for s, t in ar)
    return [("arrows", "List (Prod Nat Nat)", lean_list([f"({s}, {t})" for s, t in ar])),
            ("ids", "List Nat", lean_list([str(i) for i in identities(fs)])),
            ("comps", "List (Prod Nat Nat)", lean_list([f"({f}, {g})" for f, g in composites(fs)]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The closure clause of `reindexed_fibres`, decided by the kernel", LEAN_DEFS,
                  fixtures, verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
