# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A two-by-two table of exact pairs that is self-mirrored and squares to the
unit table, with its split into tables for its eigenvalues.

The claim: slots and outcomes (in declared order), values,
``cell(i, j, a, b)`` (the table), ``eigen(k, v)`` (outcome ``k``'s claimed
eigenvalue, a rational) and ``split(k, i, j, a, b)`` (outcome ``k``'s
table).

Relational clauses, carried by derivability over the hosted claim:
``cells_given``, ``one_cell``, ``eigen_given``, ``one_eigen``,
``split_given`` and ``one_split``.

Decoded clauses, decided over exact values outside the grammar:
``real_split`` (the trace and determinant are real and the discriminant
``tr^2 - 4 det`` is not negative: a table with eigenvalues off the real line,
such as the quarter turn with discriminant -4, is refused), ``self_mirrored``,
``square_one`` (the table times itself is the unit table), ``split_members``
(each split table is self-mirrored and idempotent), ``complete`` (they sum to
the unit table and are pairwise orthogonal) and ``spectral`` (the table is
the sum of each eigenvalue times its split table).  Their Lean certificates
are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import ZERO, Q
from omega_engine_operations.use_cases.level_engine.research_engine.exact.qi import QI
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import (NOUGHT, TABLE_DEFS, Table, certificates, grid, lean_list, lean_q, lean_table,
                            mirrored, render, rows, tadd, tmul, unit_table)

CHALLENGE_ID = "square_one"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "SquareOne"
EXACT = ("py.exact.q", "py.exact.qi")
CLAUSES = ("real_split", "self_mirrored", "square_one", "split_members", "complete", "spectral")


def table(fs: FiniteStructure) -> Table | None:
    slots = fs.elements("slot")
    g = grid(fs, "cell", (slots, slots))
    return None if g is None else [[g[(i, j)] for j in slots] for i in slots]


def members(fs: FiniteStructure) -> list[Table] | None:
    slots, outs = fs.elements("slot"), fs.elements("outcome")
    g = grid(fs, "split", (outs, slots, slots))
    return None if g is None else [[[g[(k, i, j)] for j in slots] for i in slots] for k in outs]


def eigens(fs: FiniteStructure) -> list[Q | None]:
    got = {k: fs.value(v) for k, v in rows(fs, "eigen")}
    return [got.get(k) for k in fs.elements("outcome")]


def real_split(fs: FiniteStructure, _o: Oracle) -> bool:
    m = table(fs)
    if m is None:
        return False
    tr = m[0][0] + m[1][1]
    det = m[0][0] * m[1][1] - m[0][1] * m[1][0]
    disc = tr * tr - QI(Q(4), ZERO) * det
    return tr.im.is_zero() and det.im.is_zero() and disc.re.sign() >= 0


def self_mirrored(fs: FiniteStructure, _o: Oracle) -> bool:
    m = table(fs)
    return m is not None and mirrored(m) == m


def square_one(fs: FiniteStructure, _o: Oracle) -> bool:
    m = table(fs)
    return m is not None and tmul(m, m) == unit_table(len(m))


def split_members(fs: FiniteStructure, _o: Oracle) -> bool:
    ps = members(fs)
    return ps is not None and all(mirrored(p) == p and tmul(p, p) == p for p in ps)


def complete(fs: FiniteStructure, _o: Oracle) -> bool:
    ps = members(fs)
    if not ps:
        return False
    n = len(ps[0])
    total = [[NOUGHT] * n for _ in range(n)]
    for p in ps:
        total = tadd(total, p)
    zero = [[NOUGHT] * n for _ in range(n)]
    return total == unit_table(n) and all(tmul(p, q) == zero for i, p in enumerate(ps) for j, q in enumerate(ps) if i != j)


def spectral(fs: FiniteStructure, _o: Oracle) -> bool:
    m, ps, ls = table(fs), members(fs), eigens(fs)
    if m is None or ps is None or any(x is None for x in ls):
        return False
    n = len(m)
    total = [[NOUGHT] * n for _ in range(n)]
    for lam, p in zip(ls, ps):
        assert lam is not None
        total = tadd(total, [[QI(lam, ZERO) * z for z in r] for r in p])
    return total == m


def describe(fs: FiniteStructure) -> dict[str, object]:
    m = table(fs)
    if m is None:
        return {"discriminant": None}
    tr = m[0][0] + m[1][1]
    det = m[0][0] * m[1][1] - m[0][1] * m[1][0]
    disc = tr * tr - QI(Q(4), ZERO) * det
    return {"discriminant": [str(disc.re), str(disc.im)]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "spectral")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    slot, outcome = e.form("slot"), e.form("outcome")
    cell, eigen, split = e.form("cell"), e.form("eigen"), e.form("split")
    return Compiled(
        (
            Total("cells_given", ((slot, ("i",)), (slot, ("j",))), ((cell, ("i", "j", "a", "b")),)),
            Functional("one_cell", cell, 2),
            Total("eigen_given", ((outcome, ("k",)),), ((eigen, ("k", "v")),)),
            Functional("one_eigen", eigen, 1),
            Total("split_given", ((outcome, ("k",)), (slot, ("i",)), (slot, ("j",))), ((split, ("k", "i", "j", "a", "b")),)),
            Functional("one_split", split, 3),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("real_split", real_split), ("self_mirrored", self_mirrored), ("square_one", square_one),
            ("split_members", split_members), ("complete", complete), ("spectral", spectral))),
    )


LEAN_DEFS = TABLE_DEFS + (
    "/-- Real trace and determinant, and a discriminant that is not negative. -/",
    "def realSplit (m : PTable) : Bool :=",
    "  let tr := padd (pentry m 0 0) (pentry m 1 1)",
    "  let det := padd (pmul (pentry m 0 0) (pentry m 1 1)) (pmul (-1, 0) (pmul (pentry m 0 1) (pentry m 1 0)))",
    "  let disc := padd (pmul tr tr) (pmul (-4, 0) det)",
    "  decide (tr.2 = 0) && decide (det.2 = 0) && !QN.pos (-disc.1)",
    "",
    "def selfMirrored (m : PTable) : Bool := decide (mirrorT m m.length = m)",
    "",
    "def squareOne (m : PTable) : Bool := decide (pmm m m m.length = unitT m.length)",
    "",
    "def splitMembers (ps : List PTable) : Bool := ps.all isSplitMember",
    "",
    "/-- The table is the sum of each eigenvalue times its split table. -/",
    "def spectral (m : PTable) (ls : List QN) (ps : List PTable) : Bool :=",
    "  decide ((List.zipWith (fun l p => p.map (fun r => r.map (fun z => pmul (l, 0) z))) ls ps).foldl ptadd",
    "    (zeroT m.length) = m)",
    "",
)
LEAN_CALLS = {"real_split": "realSplit table_{f}", "self_mirrored": "selfMirrored table_{f}",
              "square_one": "squareOne table_{f}", "split_members": "splitMembers split_{f}",
              "complete": "isComplete table_{f}.length split_{f}", "spectral": "spectral table_{f} eigen_{f} split_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    m, ps, ls = table(fs), members(fs), eigens(fs)
    assert m is not None and ps is not None
    return [("table", "PTable", lean_table(m)), ("split", "List PTable", lean_list([lean_table(p) for p in ps])),
            ("eigen", "List QN", lean_list([lean_q(x) for x in ls if x is not None]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clauses of `square_one`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
