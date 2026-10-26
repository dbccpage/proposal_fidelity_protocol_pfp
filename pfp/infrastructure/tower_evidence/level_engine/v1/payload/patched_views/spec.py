"""A selection view kept up to date by a delta: the old view is the view of
the old table, the delta applies to the old table and yields the new one
(every removed row is recorded as deleted), and the patched view is the
view recomputed on the new table, never the producer's patch arithmetic.

The claim: columns, tokens and rows (each in declared order; a row is its
cells), ``holds(r, c, t)`` (row ``r`` holds token ``t`` in column ``c``),
``old(r)``, ``new(r)`` (the two tables), ``inserted(r)``, ``deleted(r)``
(the delta), ``old_view(r)``, ``patched(r)`` (the two views),
``view_on(c)`` and ``view_is(t)`` (the view selects the rows holding ``t``
in column ``c``).

Relational clauses, carried by derivability over the hosted claim: the
view's selection (``view_given``, ``one_view_column``, ``one_view_token``),
``cells_total`` and ``one_cell``, the old view as the view of the old table
(``old_view_complete``, ``old_view_within``, ``old_view_selected``), the
delta's applicability (``deleted_were_there``, ``inserted_were_not``,
``delta_disjoint``, ``inserted_arrive``) and the patched view as the view of
the new table (``patched_complete``, ``patched_within``,
``patched_selected``).

Decoded clauses, decided outside the grammar: ``rows_distinct`` (no two
rows hold the same cells: tables are sets), ``deletions_recorded`` (every
row of the old table missing from the new one is recorded as deleted: the
refused case) and ``delta_exact`` (the old table less the deletions, with
the insertions, is the new table).  Both need "not in", which the grammar
cannot state; the kernel re-decides them.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from engine.encoding import Encoding
from engine.kinds import Closure, Forbid, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import certificates, lean_list, render, rows

CHALLENGE_ID = "patched_views"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "PatchedViews"
EXACT: tuple[str, ...] = ()
CLAUSES = ("rows_distinct", "deletions_recorded", "delta_exact")
LEAN_CLAUSES = ("deletions_recorded", "delta_exact")


def _set(fs: FiniteStructure, name: str) -> set[int]:
    return {r for (r,) in rows(fs, name)}


def rows_distinct(fs: FiniteStructure, _o: Oracle) -> bool:
    cells: dict[int, list[tuple[int, int]]] = {}
    for r, c, t in rows(fs, "holds"):
        cells.setdefault(r, []).append((c, t))
    keys = [tuple(sorted(cells.get(r, []))) for r in fs.elements("row")]
    return len(set(keys)) == len(keys)


def deletions_recorded(fs: FiniteStructure, _o: Oracle) -> bool:
    return _set(fs, "old") - _set(fs, "new") <= _set(fs, "deleted")


def delta_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    return (_set(fs, "old") - _set(fs, "deleted")) | _set(fs, "inserted") == _set(fs, "new")


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"new_from_delta": sorted((_set(fs, "old") - _set(fs, "deleted")) | _set(fs, "inserted"))}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, LEAN_CLAUSES, verdicts, "delta_exact")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    column, row = e.form("column"), e.form("row")
    holds, old, new, ins, dele = e.form("holds"), e.form("old"), e.form("new"), e.form("inserted"), e.form("deleted")
    oview, patched, von, vis = e.form("old_view"), e.form("patched"), e.form("view_on"), e.form("view_is")
    selected = ((von, ("c",)), (vis, ("v",)), (holds, ("r", "c", "v")))
    return Compiled(
        (
            Total("view_given", (), ((von, ("c",)), (vis, ("v",)))),
            Functional("one_view_column", von, 0),
            Functional("one_view_token", vis, 0),
            Total("cells_total", ((row, ("r",)), (column, ("c",))), ((holds, ("r", "c", "v")),)),
            Functional("one_cell", holds, 2),
            Closure("old_view_complete", ((old, ("r",)),) + selected, ((oview, ("r",)),)),
            Closure("old_view_within", ((oview, ("r",)),), ((old, ("r",)),)),
            Closure("old_view_selected", ((oview, ("r",)), (von, ("c",)), (vis, ("v",))), ((holds, ("r", "c", "v")),)),
            Closure("deleted_were_there", ((dele, ("r",)),), ((old, ("r",)),)),
            Forbid("inserted_were_not", ((ins, ("r",)), (old, ("r",)))),
            Forbid("delta_disjoint", ((ins, ("r",)), (dele, ("r",)))),
            Closure("inserted_arrive", ((ins, ("r",)),), ((new, ("r",)),)),
            Closure("patched_complete", ((new, ("r",)),) + selected, ((patched, ("r",)),)),
            Closure("patched_within", ((patched, ("r",)),), ((new, ("r",)),)),
            Closure("patched_selected", ((patched, ("r",)), (von, ("c",)), (vis, ("v",))), ((holds, ("r", "c", "v")),)),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("rows_distinct", rows_distinct), ("deletions_recorded", deletions_recorded),
            ("delta_exact", delta_exact))),
    )


LEAN_DEFS = (
    "def subset (a b : List Nat) : Bool := a.all fun x => b.contains x",
    "",
    "def deletionsRecorded (old new del : List Nat) : Bool := subset (old.filter fun r => !new.contains r) del",
    "",
    "def deltaExact (old new del ins : List Nat) : Bool :=",
    "  let got := (old.filter fun r => !del.contains r) ++ ins",
    "  subset got new && subset new got",
    "",
)
LEAN_CALLS = {"deletions_recorded": "deletionsRecorded old_{f} new_{f} del_{f}",
              "delta_exact": "deltaExact old_{f} new_{f} del_{f} ins_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    def ls(name: str) -> str:
        return lean_list([str(r) for r in sorted(_set(fs, name))])

    return [("old", "List Nat", ls("old")), ("new", "List Nat", ls("new")), ("del", "List Nat", ls("deleted")),
            ("ins", "List Nat", ls("inserted"))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The delta clauses of `patched_views`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
