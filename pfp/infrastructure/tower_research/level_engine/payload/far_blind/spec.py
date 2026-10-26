# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A joined unit row on a two-by-two frame, one split of the near factor, a
split of the far factor for each far choice, and a claimed table of joint
weights: the near weights must not depend on the far choice.

One sort of two elements, ``bit``, indexes everything: near and far slots,
near and far outcomes, and far choices.  The claim: values,
``joint(i, k, a, b)`` (the row's entry at near slot ``i`` and far slot
``k``), ``near(o, i, j, a, b)`` (near outcome ``o``'s table),
``far(y, o, i, j, a, b)`` (far choice ``y``'s table for outcome ``o``) and
``weight(y, p, q, v)`` (the claimed weight of near outcome ``p`` and far
outcome ``q`` under far choice ``y``).

Relational clauses, carried by derivability over the hosted claim:
``joint_given``, ``one_joint``, ``near_given``, ``one_near``,
``far_given``, ``one_far``, ``weights_given`` and ``one_weight``.

Decoded clauses, decided over exact values outside the grammar:
``splits_valid`` (every split is a complete family of self-mirrored
idempotent tables), ``far_choice_blind`` (the claimed table's near weights,
summed over the far outcomes, are the same under every far choice: a table
whose near weights move with the far choice is refused, and no selection of
far outcomes is in the declared class) and ``table_exact`` (each claimed
weight is the size of the near table times the row times the far table,
transposed).  Their Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import ZERO, Q, fmt_q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import (NOUGHT, TABLE_DEFS, Table, certificates, grid, lean_list, lean_q, lean_table,
                            mirrored, render, rows, size_of, tadd, tmul, unit_table)

CHALLENGE_ID = "far_blind"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "FarBlind"
EXACT = ("py.exact.q", "py.exact.qi")
CLAUSES = ("splits_valid", "far_choice_blind", "table_exact")


def joint(fs: FiniteStructure) -> Table | None:
    bits = fs.elements("bit")
    g = grid(fs, "joint", (bits, bits))
    return None if g is None else [[g[(i, k)] for k in bits] for i in bits]


def near_split(fs: FiniteStructure) -> list[Table] | None:
    bits = fs.elements("bit")
    g = grid(fs, "near", (bits, bits, bits))
    return None if g is None else [[[g[(o, i, j)] for j in bits] for i in bits] for o in bits]


def far_splits(fs: FiniteStructure) -> list[list[Table]] | None:
    bits = fs.elements("bit")
    g = grid(fs, "far", (bits, bits, bits, bits))
    return None if g is None else [[[[g[(y, o, i, j)] for j in bits] for i in bits] for o in bits] for y in bits]


def claimed(fs: FiniteStructure) -> list[list[list[Q | None]]]:
    got = {(y, p, q): fs.value(v) for y, p, q, v in rows(fs, "weight")}
    bits = fs.elements("bit")
    return [[[got.get((y, p, q)) for q in bits] for p in bits] for y in bits]


def _valid(ps: list[Table]) -> bool:
    n = len(ps[0])
    total = [[NOUGHT] * n for _ in range(n)]
    for p in ps:
        total = tadd(total, p)
    zero = [[NOUGHT] * n for _ in range(n)]
    return (all(mirrored(p) == p and tmul(p, p) == p for p in ps) and total == unit_table(n)
            and all(tmul(p, q) == zero for i, p in enumerate(ps) for j, q in enumerate(ps) if i != j))


def recomputed(fs: FiniteStructure) -> list[list[list[Q]]] | None:
    s, es, fss = joint(fs), near_split(fs), far_splits(fs)
    if s is None or es is None or fss is None:
        return None
    out = []
    for fy in fss:
        out.append([[size_of([z for r in tmul(tmul(e, s), [list(c) for c in zip(*f)]) for z in r]) for f in fy]
                    for e in es])
    return out


def splits_valid(fs: FiniteStructure, _o: Oracle) -> bool:
    es, fss = near_split(fs), far_splits(fs)
    return es is not None and fss is not None and _valid(es) and all(_valid(fy) for fy in fss)


def far_choice_blind(fs: FiniteStructure, _o: Oracle) -> bool:
    t = claimed(fs)
    if any(x is None for ty in t for r in ty for x in r):
        return False
    marg = [[sum((x for x in r if x is not None), ZERO) for r in ty] for ty in t]
    return all(m == marg[0] for m in marg)


def table_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    return recomputed(fs) == claimed(fs)


def describe(fs: FiniteStructure) -> dict[str, object]:
    t = recomputed(fs)
    return {"table": None if t is None else [[[fmt_q(x) for x in r] for r in ty] for ty in t]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "table_exact")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    bit = e.form("bit")
    j, n, f, w = e.form("joint"), e.form("near"), e.form("far"), e.form("weight")
    b = [(bit, (v,)) for v in ("y", "o", "i", "k")]
    return Compiled(
        (
            Total("joint_given", (b[2], b[3]), ((j, ("i", "k", "a", "b")),)),
            Functional("one_joint", j, 2),
            Total("near_given", (b[1], b[2], b[3]), ((n, ("o", "i", "k", "a", "b")),)),
            Functional("one_near", n, 3),
            Total("far_given", (b[0], b[1], b[2], b[3]), ((f, ("y", "o", "i", "k", "a", "b")),)),
            Functional("one_far", f, 4),
            Total("weights_given", (b[0], b[1], b[2]), ((w, ("y", "o", "i", "v")),)),
            Functional("one_weight", w, 3),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("splits_valid", splits_valid), ("far_choice_blind", far_choice_blind), ("table_exact", table_exact))),
    )


LEAN_DEFS = TABLE_DEFS + (
    "def transposeT (a : PTable) (n : Nat) : PTable :=",
    "  (List.range n).map fun i => (List.range n).map fun j => pentry a j i",
    "",
    "def splitsValid (es : List PTable) (fss : List (List PTable)) : Bool :=",
    "  es.all isSplitMember && isComplete 2 es && fss.all (fun fy => fy.all isSplitMember && isComplete 2 fy)",
    "",
    "/-- The recomputed weights: the size of the near table times the row times the far table, transposed. -/",
    "def table (s : PTable) (es : List PTable) (fss : List (List PTable)) : List (List (List QN)) :=",
    "  fss.map fun fy => es.map fun e => fy.map fun f => rowSize (pmm (pmm e s 2) (transposeT f 2) 2).flatten",
    "",
    "def total (xs : List QN) : QN := xs.foldl (fun acc x => acc + x) 0",
    "",
    "/-- The claimed near weights are the same under every far choice. -/",
    "def farChoiceBlind (w : List (List (List QN))) : Bool :=",
    "  w.all fun ty => decide (ty.map total = (w.headD []).map total)",
    "",
    "def tableExact (s : PTable) (es : List PTable) (fss : List (List PTable)) (w : List (List (List QN))) : Bool :=",
    "  decide (table s es fss = w)",
    "",
)
LEAN_CALLS = {"splits_valid": "splitsValid near_{f} far_{f}", "far_choice_blind": "farChoiceBlind weights_{f}",
              "table_exact": "tableExact joint_{f} near_{f} far_{f} weights_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    s, es, fss, t = joint(fs), near_split(fs), far_splits(fs), claimed(fs)
    assert s is not None and es is not None and fss is not None
    w = lean_list([lean_list([lean_list([lean_q(x) for x in r if x is not None]) for r in ty]) for ty in t])
    return [("joint", "PTable", lean_table(s)), ("near", "List PTable", lean_list([lean_table(e) for e in es])),
            ("far", "List (List PTable)", lean_list([lean_list([lean_table(f) for f in fy]) for fy in fss])),
            ("weights", "List (List (List QN))", w)]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clauses of `far_blind`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
