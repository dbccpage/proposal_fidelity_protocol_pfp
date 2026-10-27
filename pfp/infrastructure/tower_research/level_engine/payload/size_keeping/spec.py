# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A square table of exact pairs claimed to keep size, with test rows and
their claimed images.

The claim: slots (in declared order), probes, values, ``cell(i, j, a, b)``
(the table's entry at row ``i``, column ``j`` is ``a + b i``),
``test(p, s, a, b)`` (probe ``p``'s entry at slot ``s``) and
``image(p, s, a, b)`` (the claimed entry of the table times probe ``p``).

Relational clauses, carried by derivability over the hosted claim:
``cells_given``, ``one_cell``, ``tests_given``, ``one_test``,
``images_given``, ``one_image`` and ``typed``.

Decoded clauses, decided over exact values outside the grammar:
``size_keeping`` (the mirrored transpose of the table times the table is the
unit table, and so is the table times its mirrored transpose: decided on the
whole table, never by sampling rows) and ``image_exact`` (each claimed image
is the table times its probe).  Their Lean certificates are re-decided by
the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO
from operations.use_cases.level_engine.research_engine.exact.qi import QI
from operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import PAIR_DEFS, certificates, lean_list, lean_pair, pair_of, render, rows

CHALLENGE_ID = "size_keeping"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "SizeKeeping"
EXACT = ("py.exact.q", "py.exact.qi")
CLAUSES = ("size_keeping", "image_exact")
NOUGHT, UNIT = QI(ZERO, ZERO), QI(ONE, ZERO)
Table = list[list[QI]]


def _grid(fs: FiniteStructure, name: str, first: str) -> dict[int, list[QI]] | None:
    """``name``'s rows keyed by their first argument, in slot order; ``None``
    when an entry is missing, repeated or undecodable."""
    got: dict[tuple[int, int], QI] = {}
    for k, s, a, b in rows(fs, name):
        z = pair_of(fs, a, b)
        if z is None or (k, s) in got:
            return None
        got[(k, s)] = z
    slots = fs.elements("slot")
    keys = fs.elements(first)
    if any((k, s) not in got for k in keys for s in slots):
        return None
    return {k: [got[(k, s)] for s in slots] for k in keys}


def table(fs: FiniteStructure) -> Table | None:
    g = _grid(fs, "cell", "slot")
    return None if g is None else [g[k] for k in fs.elements("slot")]


def probes(fs: FiniteStructure) -> list[tuple[list[QI], list[QI]]] | None:
    t, i = _grid(fs, "test", "probe"), _grid(fs, "image", "probe")
    return None if t is None or i is None else [(t[p], i[p]) for p in fs.elements("probe")]


def _mul(a: Table, b: Table) -> Table:
    n = len(a)
    out = []
    for i in range(n):
        row = []
        for j in range(n):
            acc = NOUGHT
            for t in range(n):
                acc = acc + a[i][t] * b[t][j]
            row.append(acc)
        out.append(row)
    return out


def mirrored(a: Table) -> Table:
    return [[a[j][i].conj() for j in range(len(a))] for i in range(len(a))]


def apply(a: Table, v: list[QI]) -> list[QI]:
    out = []
    for r in a:
        acc = NOUGHT
        for x, y in zip(r, v):
            acc = acc + x * y
        out.append(acc)
    return out


def size_keeping(fs: FiniteStructure, _o: Oracle) -> bool:
    u = table(fs)
    if u is None:
        return False
    unit = [[UNIT if i == j else NOUGHT for j in range(len(u))] for i in range(len(u))]
    return _mul(mirrored(u), u) == unit and _mul(u, mirrored(u)) == unit


def image_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    u, ps = table(fs), probes(fs)
    return u is not None and ps is not None and all(apply(u, v) == w for v, w in ps)


def describe(fs: FiniteStructure) -> dict[str, object]:
    u = table(fs)
    return {"slots": len(fs.elements("slot")), "table_given": u is not None}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "size_keeping")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    slot, probe, val = e.form("slot"), e.form("probe"), e.form("val")
    cell, test, image = e.form("cell"), e.form("test"), e.form("image")
    return Compiled(
        (
            Total("cells_given", ((slot, ("i",)), (slot, ("j",))), ((cell, ("i", "j", "a", "b")),)),
            Functional("one_cell", cell, 2),
            Total("tests_given", ((probe, ("p",)), (slot, ("s",))), ((test, ("p", "s", "a", "b")),)),
            Functional("one_test", test, 2),
            Total("images_given", ((probe, ("p",)), (slot, ("s",))), ((image, ("p", "s", "a", "b")),)),
            Functional("one_image", image, 2),
            Closure("typed", ((cell, ("i", "j", "a", "b")),),
                    ((slot, ("i",)), (slot, ("j",)), (val, ("a",)), (val, ("b",)))),
        ),
        decoded=(DecodedClause("size_keeping", size_keeping, EXACT),
                 DecodedClause("image_exact", image_exact, EXACT)),
    )


LEAN_DEFS = PAIR_DEFS + (
    "abbrev PTable := List (List Pair)",
    "",
    "def pentry (t : PTable) (i j : Nat) : Pair := (t.getD i []).getD j (0, 0)",
    "",
    "/-- The product of two `n` by `n` tables of pairs. -/",
    "def pmm (a b : PTable) (n : Nat) : PTable :=",
    "  (List.range n).map fun i => (List.range n).map fun j =>",
    "    psum ((List.range n).map fun t => pmul (pentry a i t) (pentry b t j))",
    "",
    "/-- The mirrored transpose. -/",
    "def mirrorT (a : PTable) (n : Nat) : PTable :=",
    "  (List.range n).map fun i => (List.range n).map fun j => mirror (pentry a j i)",
    "",
    "def unitT (n : Nat) : PTable :=",
    "  (List.range n).map fun i => (List.range n).map fun j => if i = j then (1, 0) else (0, 0)",
    "",
    "/-- Size-keeping on the whole table, both ways round. -/",
    "def sizeKeeping (u : PTable) : Bool :=",
    "  decide (pmm (mirrorT u u.length) u u.length = unitT u.length) &&",
    "    decide (pmm u (mirrorT u u.length) u.length = unitT u.length)",
    "",
    "/-- The table times a row. -/",
    "def apply (u : PTable) (v : List Pair) : List Pair := u.map fun r => psum (List.zipWith pmul r v)",
    "",
    "def imageExact (u : PTable) (ps : List (Prod (List Pair) (List Pair))) : Bool :=",
    "  ps.all fun p => decide (apply u p.1 = p.2)",
    "",
)
LEAN_CALLS = {"size_keeping": "sizeKeeping table_{f}", "image_exact": "imageExact table_{f} probes_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    u, ps = table(fs), probes(fs)
    assert u is not None and ps is not None
    def row(v: list[QI]) -> str:
        return lean_list([lean_pair(z) for z in v])

    return [("table", "PTable", lean_list([row(r) for r in u])),
            ("probes", "List (Prod (List Pair) (List Pair))", lean_list([f"({row(v)}, {row(w)})" for v, w in ps]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clauses of `size_keeping`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
