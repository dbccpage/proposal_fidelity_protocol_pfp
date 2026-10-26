# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A joined unit row on a two-by-two frame, and its claimed one-side
reduction: the near table obtained by summing over the far slots.

The claim: near and far slots (in declared order), values,
``joint(i, k, a, b)`` (the row's entry at near slot ``i`` and far slot
``k``) and ``reduced(i, j, a, b)`` (the claimed reduction's entry).  The
reduction of the row ``s`` is ``R[i][j] = sum over k of s[i, k] times the
mirror of s[j, k]``.

Relational clauses, carried by derivability over the hosted claim:
``joint_given``, ``one_joint``, ``reduced_given`` and ``one_reduced``.

Decoded clauses, decided over exact values outside the grammar:
``unit_size`` (the row has size one), ``trace_one`` (the claimed reduction
has trace exactly one: a reduction that changes the trace is refused),
``nonnegative`` (the claimed reduction is self-mirrored with nonnegative
diagonal and determinant, so it never gives a negative weight) and
``reduced_exact`` (it is the recomputed reduction).  Their Lean certificates
are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import (NOUGHT, TABLE_DEFS, Table, certificates, grid, lean_table, mirrored, render,
                            size_of)

CHALLENGE_ID = "side_reduction"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "SideReduction"
EXACT = ("py.exact.q", "py.exact.qi")
CLAUSES = ("unit_size", "trace_one", "nonnegative", "reduced_exact")


def joint(fs: FiniteStructure) -> Table | None:
    near, far = fs.elements("near"), fs.elements("far")
    g = grid(fs, "joint", (near, far))
    return None if g is None else [[g[(i, k)] for k in far] for i in near]


def claimed(fs: FiniteStructure) -> Table | None:
    near = fs.elements("near")
    g = grid(fs, "reduced", (near, near))
    return None if g is None else [[g[(i, j)] for j in near] for i in near]


def reduction(s: Table) -> Table:
    out = []
    for i in range(len(s)):
        row = []
        for j in range(len(s)):
            acc = NOUGHT
            for k in range(len(s[0])):
                acc = acc + s[i][k] * s[j][k].conj()
            row.append(acc)
        out.append(row)
    return out


def unit_size(fs: FiniteStructure, _o: Oracle) -> bool:
    s = joint(fs)
    return s is not None and size_of([z for r in s for z in r]) == ONE


def trace_one(fs: FiniteStructure, _o: Oracle) -> bool:
    r = claimed(fs)
    return r is not None and sum((r[i][i].re for i in range(len(r))), ZERO) == ONE


def nonnegative(fs: FiniteStructure, _o: Oracle) -> bool:
    r = claimed(fs)
    if r is None or mirrored(r) != r:
        return False
    det = r[0][0] * r[1][1] - r[0][1] * r[1][0]
    return r[0][0].re.sign() >= 0 and r[1][1].re.sign() >= 0 and det.re.sign() >= 0


def reduced_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    s, r = joint(fs), claimed(fs)
    return s is not None and r is not None and reduction(s) == r


def describe(fs: FiniteStructure) -> dict[str, object]:
    s = joint(fs)
    return {"reduction": None if s is None else [[[str(z.re), str(z.im)] for z in r] for r in reduction(s)]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "reduced_exact")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    near, far = e.form("near"), e.form("far")
    j, r = e.form("joint"), e.form("reduced")
    return Compiled(
        (
            Total("joint_given", ((near, ("i",)), (far, ("k",))), ((j, ("i", "k", "a", "b")),)),
            Functional("one_joint", j, 2),
            Total("reduced_given", ((near, ("i",)), (near, ("j",))), ((r, ("i", "j", "a", "b")),)),
            Functional("one_reduced", r, 2),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("unit_size", unit_size), ("trace_one", trace_one), ("nonnegative", nonnegative),
            ("reduced_exact", reduced_exact))),
    )


LEAN_DEFS = TABLE_DEFS + (
    "/-- The one-side reduction of a joined row read as a near-by-far table. -/",
    "def reduce (s : PTable) : PTable :=",
    "  (List.range s.length).map fun i => (List.range s.length).map fun j =>",
    "    psum (List.zipWith (fun x y => pmul x (mirror y)) (s.getD i []) (s.getD j []))",
    "",
    "def unitSize (s : PTable) : Bool := decide (rowSize s.flatten = 1)",
    "",
    "def traceOne (r : PTable) : Bool := decide ((pentry r 0 0).1 + (pentry r 1 1).1 = 1)",
    "",
    "/-- Self-mirrored, with nonnegative diagonal and determinant (two by two). -/",
    "def nonnegative (r : PTable) : Bool :=",
    "  let d := padd (pmul (pentry r 0 0) (pentry r 1 1)) (pmul (-1, 0) (pmul (pentry r 0 1) (pentry r 1 0)))",
    "  decide (mirrorT r 2 = r) && !QN.pos (-(pentry r 0 0).1) && !QN.pos (-(pentry r 1 1).1) && !QN.pos (-d.1)",
    "",
    "def reducedExact (s r : PTable) : Bool := decide (reduce s = r)",
    "",
)
LEAN_CALLS = {"unit_size": "unitSize joint_{f}", "trace_one": "traceOne reduced_{f}",
              "nonnegative": "nonnegative reduced_{f}", "reduced_exact": "reducedExact joint_{f} reduced_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    s, r = joint(fs), claimed(fs)
    assert s is not None and r is not None
    return [("joint", "PTable", lean_table(s)), ("reduced", "PTable", lean_table(r))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clauses of `side_reduction`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)

