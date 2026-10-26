# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A unit row, a complete split of the frame into self-mirrored idempotent
tables, and reported weights of the split's outcomes: each weight is
recomputed as the size of the split member applied to the row.

The claim: slots and outcomes (in declared order), values,
``entry(s, a, b)`` (the row), ``split(k, i, j, a, b)`` (outcome ``k``'s
table) and ``weight(k, v)`` (the reported weight of outcome ``k``).

Relational clauses, carried by derivability over the hosted claim:
``entries_given``, ``one_entry``, ``split_given``, ``one_split``,
``weights_given`` and ``one_weight``.

Decoded clauses, decided over exact values outside the grammar:
``unit_size`` (the row has size one), ``split_members`` (each table is
self-mirrored and idempotent), ``complete`` (the tables sum to the unit
table and are pairwise orthogonal) and ``weights_exact`` (each reported
weight is the size of the table applied to the row: a reported weight that
is not is refused).  Their Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import ONE, Q, fmt_q
from omega_engine_operations.use_cases.level_engine.research_engine.exact.qi import QI
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import (NOUGHT, TABLE_DEFS, Table, certificates, grid, lean_list, lean_pair, lean_q, lean_table,
                            mirrored, render, rows, size_of, tadd, tapply, tmul, unit_table)

CHALLENGE_ID = "split_weights"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "SplitWeights"
EXACT = ("py.exact.q", "py.exact.qi")
CLAUSES = ("unit_size", "split_members", "complete", "weights_exact")


def row(fs: FiniteStructure) -> list[QI] | None:
    slots = fs.elements("slot")
    g = grid(fs, "entry", (slots,))
    return None if g is None else [g[(s,)] for s in slots]


def members(fs: FiniteStructure) -> list[Table] | None:
    slots, outs = fs.elements("slot"), fs.elements("outcome")
    g = grid(fs, "split", (outs, slots, slots))
    return None if g is None else [[[g[(k, i, j)] for j in slots] for i in slots] for k in outs]


def weights(fs: FiniteStructure) -> list[Q | None]:
    got = {k: fs.value(v) for k, v in rows(fs, "weight")}
    return [got.get(k) for k in fs.elements("outcome")]


def unit_size(fs: FiniteStructure, _o: Oracle) -> bool:
    v = row(fs)
    return v is not None and size_of(v) == ONE


def split_members(fs: FiniteStructure, _o: Oracle) -> bool:
    ps = members(fs)
    return ps is not None and all(mirrored(p) == p and tmul(p, p) == p for p in ps)


def complete(fs: FiniteStructure, _o: Oracle) -> bool:
    ps = members(fs)
    if ps is None or not ps:
        return False
    n = len(ps[0])
    total = ps[0]
    for p in ps[1:]:
        total = tadd(total, p)
    zero = [[NOUGHT] * n for _ in range(n)]
    return total == unit_table(n) and all(tmul(p, q) == zero for i, p in enumerate(ps) for j, q in enumerate(ps) if i != j)


def recomputed(fs: FiniteStructure) -> list[Q] | None:
    v, ps = row(fs), members(fs)
    return None if v is None or ps is None else [size_of(tapply(p, v)) for p in ps]


def weights_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    w = recomputed(fs)
    return w is not None and w == weights(fs)


def describe(fs: FiniteStructure) -> dict[str, object]:
    w = recomputed(fs)
    return {"weights": None if w is None else [fmt_q(x) for x in w]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "weights_exact")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    slot, outcome = e.form("slot"), e.form("outcome")
    entry, split, weight = e.form("entry"), e.form("split"), e.form("weight")
    return Compiled(
        (
            Total("entries_given", ((slot, ("s",)),), ((entry, ("s", "a", "b")),)),
            Functional("one_entry", entry, 1),
            Total("split_given", ((outcome, ("k",)), (slot, ("i",)), (slot, ("j",))), ((split, ("k", "i", "j", "a", "b")),)),
            Functional("one_split", split, 3),
            Total("weights_given", ((outcome, ("k",)),), ((weight, ("k", "v")),)),
            Functional("one_weight", weight, 1),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("unit_size", unit_size), ("split_members", split_members), ("complete", complete),
            ("weights_exact", weights_exact))),
    )


LEAN_DEFS = TABLE_DEFS + (
    "def unitSize (v : List Pair) : Bool := decide (rowSize v = 1)",
    "",
    "def splitMembers (ps : List PTable) : Bool := ps.all isSplitMember",
    "",
    "/-- Each reported weight is the size of the table applied to the row. -/",
    "def weightsExact (v : List Pair) (ps : List PTable) (w : List QN) : Bool :=",
    "  decide (ps.map (fun p => rowSize (papply p v)) = w)",
    "",
)
LEAN_CALLS = {"unit_size": "unitSize row_{f}", "split_members": "splitMembers split_{f}",
              "complete": "isComplete row_{f}.length split_{f}", "weights_exact": "weightsExact row_{f} split_{f} weights_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    v, ps, w = row(fs), members(fs), weights(fs)
    assert v is not None and ps is not None and all(x is not None for x in w)
    return [("row", "List Pair", lean_list([lean_pair(z) for z in v])),
            ("split", "List PTable", lean_list([lean_table(p) for p in ps])),
            ("weights", "List QN", lean_list([lean_q(x) for x in w if x is not None]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clauses of `split_weights`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
