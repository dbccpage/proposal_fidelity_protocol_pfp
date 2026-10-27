# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A unit row and two complete splits applied one after the other: the joint
weights depend on the order, the weights of the second outcome given the
first are the joint weights divided by the first weight, and a first
outcome of weight zero has no conditional weights.

One sort of two elements, ``bit``, indexes slots and outcomes.  The claim:
values, ``entry(i, a, b)`` (the row), ``first(o, i, j, a, b)`` and
``second(o, i, j, a, b)`` (the splits' tables), ``weight(p, q, v)`` (the
claimed weight of first outcome ``p`` then second outcome ``q``),
``given(p, q, v)`` (the claimed weight of ``q`` given ``p``; absent for a
first outcome with no conditional weights) and ``back(q, p, v)`` (the claimed
weight of ``q`` first, then ``p``).

Relational clauses, carried by derivability over the hosted claim:
``entries_given``, ``one_entry``, ``first_given``, ``one_first``,
``second_given``, ``one_second``, ``weights_given``, ``one_weight``,
``one_given``, ``back_given`` and ``one_back``.

Decoded clauses, decided over exact values outside the grammar:
``unit_size``, ``splits_valid`` (both splits are complete families of
self-mirrored idempotent tables), ``sequential_exact`` (each weight is the
size of the second table times the first table times the row: the product
of the two separate weights is refused where the splits do not commute),
``conditionals_exact`` (each conditional row is the weight row divided by
the first weight, and is absent where that weight is zero: zero is never
divided through) and ``reverse_exact`` (the weights in the other order).
Their Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.exact.q import ONE, Q, fmt_q
from operations.use_cases.level_engine.research_engine.exact.qi import QI
from operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import (NOUGHT, TABLE_DEFS, Table, certificates, grid, lean_list, lean_pair, lean_q,
                            lean_table, mirrored, render, rows, size_of, tadd, tapply, tmul, unit_table)

CHALLENGE_ID = "ordered_splits"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "OrderedSplits"
EXACT = ("py.exact.q", "py.exact.qi")
CLAUSES = ("unit_size", "splits_valid", "sequential_exact", "conditionals_exact", "reverse_exact")


def row(fs: FiniteStructure) -> list[QI] | None:
    bits = fs.elements("bit")
    g = grid(fs, "entry", (bits,))
    return None if g is None else [g[(i,)] for i in bits]


def split(fs: FiniteStructure, name: str) -> list[Table] | None:
    bits = fs.elements("bit")
    g = grid(fs, name, (bits, bits, bits))
    return None if g is None else [[[g[(o, i, j)] for j in bits] for i in bits] for o in bits]


def _values(fs: FiniteStructure, name: str) -> dict[tuple[int, int], Q | None]:
    return {(a, b): fs.value(v) for a, b, v in rows(fs, name)}


def claimed(fs: FiniteStructure, name: str) -> list[list[Q | None]]:
    got, bits = _values(fs, name), fs.elements("bit")
    return [[got.get((a, b)) for b in bits] for a in bits]


def conditionals(fs: FiniteStructure) -> list[list[Q | None] | None]:
    got, bits = _values(fs, "given"), fs.elements("bit")
    return [[got.get((a, b)) for b in bits] if any((a, b) in got for b in bits) else None for a in bits]


def _valid(ps: list[Table]) -> bool:
    n = len(ps[0])
    total = [[NOUGHT] * n for _ in range(n)]
    for p in ps:
        total = tadd(total, p)
    zero = [[NOUGHT] * n for _ in range(n)]
    return (all(mirrored(p) == p and tmul(p, p) == p for p in ps) and total == unit_table(n)
            and all(tmul(p, q) == zero for i, p in enumerate(ps) for j, q in enumerate(ps) if i != j))


def sequential(fs: FiniteStructure, one: str, two: str) -> list[list[Q]] | None:
    v, ps, es = row(fs), split(fs, one), split(fs, two)
    if v is None or ps is None or es is None:
        return None
    return [[size_of(tapply(e, tapply(p, v))) for e in es] for p in ps]


def unit_size(fs: FiniteStructure, _o: Oracle) -> bool:
    v = row(fs)
    return v is not None and size_of(v) == ONE


def splits_valid(fs: FiniteStructure, _o: Oracle) -> bool:
    ps, es = split(fs, "first"), split(fs, "second")
    return ps is not None and es is not None and _valid(ps) and _valid(es)


def sequential_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    s = sequential(fs, "first", "second")
    return s is not None and s == claimed(fs, "weight")


def conditionals_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    v, ps, s = row(fs), split(fs, "first"), sequential(fs, "first", "second")
    if v is None or ps is None or s is None:
        return False
    for p, line, got in zip(ps, s, conditionals(fs)):
        w = size_of(tapply(p, v))
        if w.is_zero():
            if got is not None:
                return False
        elif got != [x / w for x in line]:
            return False
    return True


def reverse_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    s = sequential(fs, "second", "first")
    return s is not None and s == claimed(fs, "back")


def describe(fs: FiniteStructure) -> dict[str, object]:
    s = sequential(fs, "first", "second")
    return {"sequential": None if s is None else [[fmt_q(x) for x in r] for r in s]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "sequential_exact")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    bit = e.form("bit")
    b = [(bit, (v,)) for v in ("o", "i", "j")]
    entry, first, second = e.form("entry"), e.form("first"), e.form("second")
    weight, given, back = e.form("weight"), e.form("given"), e.form("back")
    return Compiled(
        (
            Total("entries_given", (b[1],), ((entry, ("i", "a", "b")),)),
            Functional("one_entry", entry, 1),
            Total("first_given", tuple(b), ((first, ("o", "i", "j", "a", "b")),)),
            Functional("one_first", first, 3),
            Total("second_given", tuple(b), ((second, ("o", "i", "j", "a", "b")),)),
            Functional("one_second", second, 3),
            Total("weights_given", (b[0], b[1]), ((weight, ("o", "i", "v")),)),
            Functional("one_weight", weight, 2),
            Functional("one_given", given, 2),
            Total("back_given", (b[0], b[1]), ((back, ("o", "i", "v")),)),
            Functional("one_back", back, 2),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("unit_size", unit_size), ("splits_valid", splits_valid), ("sequential_exact", sequential_exact),
            ("conditionals_exact", conditionals_exact), ("reverse_exact", reverse_exact))),
    )


LEAN_DEFS = TABLE_DEFS + (
    "def unitSize (v : List Pair) : Bool := decide (rowSize v = 1)",
    "",
    "def splitsValid (ps es : List PTable) : Bool :=",
    "  ps.all isSplitMember && isComplete 2 ps && es.all isSplitMember && isComplete 2 es",
    "",
    "/-- The weights of one split's outcome, then the other's. -/",
    "def sequential (v : List Pair) (ps es : List PTable) : List (List QN) :=",
    "  ps.map fun p => es.map fun e => rowSize (papply e (papply p v))",
    "",
    "def sequentialExact (v : List Pair) (ps es : List PTable) (w : List (List QN)) : Bool :=",
    "  decide (sequential v ps es = w)",
    "",
    "/-- Each conditional row is the weight row over the first weight, absent where that weight is zero. -/",
    "def conditionalsExact (v : List Pair) (ps es : List PTable) (c : List (Option (List QN))) : Bool :=",
    "  decide ((List.zipWith (fun p line =>",
    "    let w := rowSize (papply p v)",
    "    if w = 0 then none else some (line.map fun x => x / w)) ps (sequential v ps es)) = c)",
    "",
    "def reverseExact (v : List Pair) (ps es : List PTable) (r : List (List QN)) : Bool :=",
    "  decide (sequential v es ps = r)",
    "",
)
LEAN_CALLS = {"unit_size": "unitSize row_{f}", "splits_valid": "splitsValid first_{f} second_{f}",
              "sequential_exact": "sequentialExact row_{f} first_{f} second_{f} weights_{f}",
              "conditionals_exact": "conditionalsExact row_{f} first_{f} second_{f} given_{f}",
              "reverse_exact": "reverseExact row_{f} first_{f} second_{f} back_{f}"}


def _grid_text(g: list[list[Q | None]]) -> str:
    return lean_list([lean_list([lean_q(x) for x in r if x is not None]) for r in g])


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    v, ps, es = row(fs), split(fs, "first"), split(fs, "second")
    assert v is not None and ps is not None and es is not None
    cond = lean_list(["none" if c is None else f"some {lean_list([lean_q(x) for x in c if x is not None])}"
                      for c in conditionals(fs)])
    return [("row", "List Pair", lean_list([lean_pair(z) for z in v])),
            ("first", "List PTable", lean_list([lean_table(p) for p in ps])),
            ("second", "List PTable", lean_list([lean_table(p) for p in es])),
            ("weights", "List (List QN)", _grid_text(claimed(fs, "weight"))),
            ("given", "List (Option (List QN))", cond), ("back", "List (List QN)", _grid_text(claimed(fs, "back")))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clauses of `ordered_splits`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
