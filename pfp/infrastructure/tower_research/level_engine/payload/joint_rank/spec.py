# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A joined row on a two-by-two frame, read as a table, and its claimed rank.

The claim: near slots and far slots (each in declared order), values,
``entry(i, j, a, b)`` (the entry at near slot ``i`` and far slot ``j`` is
the pair ``a + b i``) and ``rank(r)`` (the claimed rank of the table whose
row ``i``, column ``j`` is that entry).

Relational clauses, carried by derivability over the hosted claim:
``entries_given``, ``one_entry``, ``typed``, ``rank_given`` and
``one_rank``.

Decoded clauses, decided over exact values outside the grammar:
``unit_size`` (the row has size exactly one) and ``rank_exact`` (the claimed
rank is a natural number and equals the rank of the table, computed by exact
elimination over pairs, never read).  A row that splits into a product of a
near row and a far row has rank one; it cannot claim rank two.  Their Lean
certificates are re-decided by the kernel, which computes the rank of a two
by two table from its determinant and its entries.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO, Q, fmt_q
from operations.use_cases.level_engine.research_engine.exact.qi import QI
from operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import PAIR_DEFS, certificates, lean_list, lean_pair, lean_q, pair_of, render, rows

CHALLENGE_ID = "joint_rank"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "JointRank"
EXACT = ("py.exact.q", "py.exact.qi")
CLAUSES = ("unit_size", "rank_exact")


def table(fs: FiniteStructure) -> list[list[QI]] | None:
    got: dict[tuple[int, int], QI] = {}
    for i, j, a, b in rows(fs, "entry"):
        z = pair_of(fs, a, b)
        if z is None or (i, j) in got:
            return None
        got[(i, j)] = z
    near, far = fs.elements("near"), fs.elements("far")
    if any((i, j) not in got for i in near for j in far):
        return None
    return [[got[(i, j)] for j in far] for i in near]


def claimed(fs: FiniteStructure) -> Q | None:
    got = rows(fs, "rank")
    return fs.value(got[0][0]) if len(got) == 1 else None


def rank_of(t: list[list[QI]]) -> int:
    """The rank by exact elimination over pairs."""
    m = [list(r) for r in t]
    rank = 0
    for c in range(len(m[0]) if m else 0):
        pivot = next((r for r in range(rank, len(m)) if not m[r][c].is_zero()), None)
        if pivot is None:
            continue
        m[rank], m[pivot] = m[pivot], m[rank]
        inv = m[rank][c].inv()
        for r in range(len(m)):
            if r != rank and not m[r][c].is_zero():
                f = m[r][c] * inv
                m[r] = [x - f * y for x, y in zip(m[r], m[rank])]
        rank += 1
    return rank


def size(t: list[list[QI]]) -> Q:
    return sum((z.norm2() for r in t for z in r), ZERO)


def unit_size(fs: FiniteStructure, _o: Oracle) -> bool:
    t = table(fs)
    return t is not None and size(t) == ONE


def rank_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    t, r = table(fs), claimed(fs)
    return t is not None and r is not None and r.den == 1 and r.num == rank_of(t)


def describe(fs: FiniteStructure) -> dict[str, object]:
    t = table(fs)
    return {"rank": None if t is None else rank_of(t), "size": None if t is None else fmt_q(size(t))}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "unit_size")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    near, far, val = e.form("near"), e.form("far"), e.form("val")
    entry, rank = e.form("entry"), e.form("rank")
    return Compiled(
        (
            Total("entries_given", ((near, ("i",)), (far, ("j",))), ((entry, ("i", "j", "a", "b")),)),
            Functional("one_entry", entry, 2),
            Closure("typed", ((entry, ("i", "j", "a", "b")),),
                    ((near, ("i",)), (far, ("j",)), (val, ("a",)), (val, ("b",)))),
            Total("rank_given", (), ((rank, ("r",)),)),
            Functional("one_rank", rank, 0),
        ),
        decoded=(DecodedClause("unit_size", unit_size, EXACT), DecodedClause("rank_exact", rank_exact, EXACT)),
    )


LEAN_DEFS = PAIR_DEFS + (
    "/-- Entry `(i, j)` of a table of pairs. -/",
    "def pentry (t : List (List Pair)) (i j : Nat) : Pair := (t.getD i []).getD j (0, 0)",
    "",
    "/-- The determinant of a two by two table of pairs. -/",
    "def pdet2 (t : List (List Pair)) : Pair :=",
    "  padd (pmul (pentry t 0 0) (pentry t 1 1)) (pmul (-1, 0) (pmul (pentry t 0 1) (pentry t 1 0)))",
    "",
    "/-- The rank of a two by two table: two when the determinant is not zero,",
    "else one when some entry is not zero, else zero. -/",
    "def rank2 (t : List (List Pair)) : Nat :=",
    "  if pdet2 t = (0, 0) then (if t.all (fun r => r.all (fun z => z = (0, 0))) then 0 else 1) else 2",
    "",
    "def unitSize (t : List (List Pair)) : Bool := decide (rowSize t.flatten = 1)",
    "",
    "/-- The claimed rank is the natural number the rank of the table computes to. -/",
    "def rankExact (t : List (List Pair)) (r : QN) : Bool := decide (QN.ofInt (rank2 t) = r)",
    "",
)
LEAN_CALLS = {"unit_size": "unitSize table_{f}", "rank_exact": "rankExact table_{f} rank_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    t, r = table(fs), claimed(fs)
    assert t is not None and r is not None
    return [("table", "List (List Pair)", lean_list([lean_list([lean_pair(z) for z in row]) for row in t])),
            ("rank", "QN", lean_q(r))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clauses of `joint_rank`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
