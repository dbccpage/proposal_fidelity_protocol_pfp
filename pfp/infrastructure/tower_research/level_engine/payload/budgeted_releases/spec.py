# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Releases of a finite table composed two ways, both decided exactly: the
budget composes in sequence (no release costs more than what remains before
it, and each claimed remainder is the budget less the costs so far), and
the releases compose jointly (grouping the records by every released
column together, every class holds at least ``k`` records).

The claim: columns, records, tokens, releases (in declared order), ledger
entries, one budget and one threshold, each release carrying its cost, each
ledger entry its claimed remainder, the budget and the threshold their
values; ``cell(r, c, v)`` (record ``r`` holds token ``v`` in column
``c``), ``reveals(q, c)`` (release ``q`` reveals column ``c``) and
``after(q, l)`` (ledger entry ``l`` is the claimed remainder after release
``q``).

Relational clauses, carried by derivability over the hosted claim:
``cells_total``, ``one_cell``, ``reveals_something``, ``reveals_typed``,
``ledger_given`` and ``one_ledger``.

Decoded clauses, decided outside the grammar: ``well_formed`` (one budget,
nonnegative; one threshold, a positive natural; positive costs),
``within_budget`` (no release costs more than the budget remaining before
it: the refused case), ``ledger_exact`` (each claimed remainder is the
budget less the costs so far) and ``joint_classes`` (every class of the
joint partition by all released columns holds at least ``k`` records).
The last three are re-decided by the kernel over ExactRat.  No noise
mechanism is modelled.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine import lean_text as T
from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import ZERO, Q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "budgeted_releases"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "BudgetedReleases"
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "within_budget", "ledger_exact", "joint_classes")
LEAN_CLAUSES = CLAUSES[1:]


def _one(fs: FiniteStructure, sort: str) -> Q | None:
    got = [fs.value(e) for e in fs.elements(sort)]
    return got[0] if len(got) == 1 else None


def releases(fs: FiniteStructure) -> list[tuple[Q, Q | None]]:
    """(cost, claimed remainder) per release, in declared order."""
    after = {q: fs.value(l) for q, l in rows(fs, "after")}
    return [(c if (c := fs.value(q)) is not None else ZERO, after.get(q)) for q in fs.elements("release")]


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    b, k = _one(fs, "budget"), _one(fs, "threshold")
    return (b is not None and b.sign() >= 0 and k is not None and k.den == 1 and k.num >= 1
            and all(c.sign() > 0 for c, _ in releases(fs)))


def within_budget(fs: FiniteStructure, _o: Oracle) -> bool:
    left = _one(fs, "budget") or ZERO
    for c, _ in releases(fs):
        if c > left:
            return False
        left = left - c
    return True


def ledger_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    left = _one(fs, "budget") or ZERO
    for c, r in releases(fs):
        left = left - c
        if r != left:
            return False
    return True


def classes(fs: FiniteStructure) -> list[int]:
    cols = fs.elements("column")
    shown = sorted({position(fs, "column", c) for _, c in rows(fs, "reveals") if c in cols}, key=lambda x: x or 0)
    cell = {(r, position(fs, "column", c)): v for r, c, v in rows(fs, "cell")}
    got: dict[tuple[int, ...], int] = {}
    for r in fs.elements("record"):
        key = tuple(cell.get((r, i), -1) for i in shown)
        got[key] = got.get(key, 0) + 1
    return sorted(got.values())


def joint_classes(fs: FiniteStructure, _o: Oracle) -> bool:
    k = _one(fs, "threshold")
    return k is not None and bool(classes(fs)) and min(classes(fs)) >= k.num


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"class_sizes": classes(fs)}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, LEAN_CLAUSES, verdicts, "joint_classes")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    column, record, release = e.form("column"), e.form("record"), e.form("release")
    cell, reveals, after = e.form("cell"), e.form("reveals"), e.form("after")
    return Compiled(
        (
            Total("cells_total", ((record, ("r",)), (column, ("c",))), ((cell, ("r", "c", "v")),)),
            Functional("one_cell", cell, 2),
            Total("reveals_something", ((release, ("q",)),), ((reveals, ("q", "c")),)),
            Closure("reveals_typed", ((reveals, ("q", "c")),), ((release, ("q",)), (column, ("c",)))),
            Total("ledger_given", ((release, ("q",)),), ((after, ("q", "l")),)),
            Functional("one_ledger", after, 1),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("within_budget", within_budget), ("ledger_exact", ledger_exact),
            ("joint_classes", joint_classes))),
    )


LEAN_DEFS = (
    "/-- Releases as (cost, claimed remainder). -/",
    "def withinBudget (b : QN) (rs : List (Prod QN QN)) : Bool :=",
    "  (rs.foldl (fun acc r => (acc.1 && decide (r.1 <= acc.2), acc.2 - r.1)) (true, b)).1",
    "",
    "def ledgerExact (b : QN) (rs : List (Prod QN QN)) : Bool :=",
    "  (rs.foldl (fun acc r => (acc.1 && decide (r.2 = acc.2 - r.1), acc.2 - r.1)) (true, b)).1",
    "",
    "/-- Records as token lists over the released columns: every class has at least `k` members. -/",
    "def jointClasses (k : Nat) (keys : List (List Nat)) : Bool :=",
    "  !keys.isEmpty && keys.all fun key => k <= keys.count key",
    "",
)
LEAN_CALLS = {"within_budget": "withinBudget budget_{f} releases_{f}",
              "ledger_exact": "ledgerExact budget_{f} releases_{f}",
              "joint_classes": "jointClasses k_{f} keys_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    b, k = _one(fs, "budget"), _one(fs, "threshold")
    assert b is not None and k is not None and all(r is not None for _, r in releases(fs))
    cols = fs.elements("column")
    shown = sorted({position(fs, "column", c) or 0 for _, c in rows(fs, "reveals") if c in cols})
    cell = {(r, position(fs, "column", c)): v for r, c, v in rows(fs, "cell")}
    keys = [[cell.get((r, i), 0) for i in shown] for r in fs.elements("record")]
    return [("budget", "QN", T.q(b)), ("k", "Nat", str(k.num)),
            ("releases", "List (Prod QN QN)",
             lean_list([f"({T.q(c)}, {T.q(r)})" for c, r in releases(fs) if r is not None])),
            ("keys", "List (List Nat)", lean_list([lean_list([str(x) for x in key]) for key in keys]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The composition clauses of `budgeted_releases`, decided by the kernel", LEAN_DEFS,
                  fixtures, verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
