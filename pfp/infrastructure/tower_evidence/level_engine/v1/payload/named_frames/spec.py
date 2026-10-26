"""A two-slot row given by its coordinates in a named frame: the frame is one
of several declared size-keeping tables, and the row in the standard frame
is the named table times the coordinates.

The claim: frames and slots (in declared order), values,
``cell(f, i, j, a, b)`` (frame ``f``'s table has ``a + b i`` at row ``i``,
column ``j``: its columns are the frame's slots written in the standard
frame), ``named(f)`` (the coordinates are taken in frame ``f``),
``coord(s, a, b)`` and ``row(s, a, b)`` (the claimed row in the standard
frame).

Relational clauses, carried by derivability over the hosted claim:
``named_given`` (the coordinates name their frame: the same coordinates
denote different rows in different frames), ``one_named``, ``cells_given``,
``one_cell``, ``coords_given``, ``one_coord``, ``row_given`` and
``one_row``.

Decoded clauses, decided over exact values outside the grammar:
``frames_size_keeping`` (each declared table's mirrored transpose times the
table is the unit table), ``unit_coordinates`` (the coordinates have size
one) and ``row_exact`` (the claimed row is the named table times the
coordinates).  Their Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from engine.encoding import Encoding
from engine.exact.q import ONE, ZERO
from engine.exact.qi import QI
from engine.kinds import Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import PAIR_DEFS, certificates, lean_list, lean_pair, pair_of, position, render, rows

CHALLENGE_ID = "named_frames"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "NamedFrames"
EXACT = ("py.exact.q", "py.exact.qi")
CLAUSES = ("frames_size_keeping", "unit_coordinates", "row_exact")
NOUGHT, UNIT = QI(ZERO, ZERO), QI(ONE, ZERO)
Table = list[list[QI]]


def tables(fs: FiniteStructure) -> list[Table] | None:
    got: dict[tuple[int, int, int], QI] = {}
    for f, i, j, a, b in rows(fs, "cell"):
        z = pair_of(fs, a, b)
        if z is None or (f, i, j) in got:
            return None
        got[(f, i, j)] = z
    slots = fs.elements("slot")
    out = []
    for f in fs.elements("frame"):
        if any((f, i, j) not in got for i in slots for j in slots):
            return None
        out.append([[got[(f, i, j)] for j in slots] for i in slots])
    return out


def _vector(fs: FiniteStructure, name: str) -> list[QI] | None:
    got: dict[int, QI] = {}
    for s, a, b in rows(fs, name):
        z = pair_of(fs, a, b)
        if z is None or s in got:
            return None
        got[s] = z
    slots = fs.elements("slot")
    return [got[s] for s in slots] if all(s in got for s in slots) else None


def named(fs: FiniteStructure) -> int | None:
    got = rows(fs, "named")
    return position(fs, "frame", got[0][0]) if len(got) == 1 else None


def keeps_size(t: Table) -> bool:
    n = len(t)
    for i in range(n):
        for j in range(n):
            acc = NOUGHT
            for k in range(n):
                acc = acc + t[k][i].conj() * t[k][j]
            if acc != (UNIT if i == j else NOUGHT):
                return False
    return True


def frames_size_keeping(fs: FiniteStructure, _o: Oracle) -> bool:
    ts = tables(fs)
    return ts is not None and all(keeps_size(t) for t in ts)


def unit_coordinates(fs: FiniteStructure, _o: Oracle) -> bool:
    c = _vector(fs, "coord")
    return c is not None and sum((z.norm2() for z in c), ZERO) == ONE


def standard(fs: FiniteStructure) -> list[QI] | None:
    ts, c, k = tables(fs), _vector(fs, "coord"), named(fs)
    if ts is None or c is None or k is None:
        return None
    out = []
    for r in ts[k]:
        acc = NOUGHT
        for x, y in zip(r, c):
            acc = acc + x * y
        out.append(acc)
    return out


def row_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    s, r = standard(fs), _vector(fs, "row")
    return s is not None and s == r


def describe(fs: FiniteStructure) -> dict[str, object]:
    s = standard(fs)
    return {"standard_row": None if s is None else [[str(z.re), str(z.im)] for z in s]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "row_exact")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    frame, slot = e.form("frame"), e.form("slot")
    cell, named_f, coord, row = e.form("cell"), e.form("named"), e.form("coord"), e.form("row")
    return Compiled(
        (
            Total("named_given", (), ((named_f, ("f",)),)),
            Functional("one_named", named_f, 0),
            Total("cells_given", ((frame, ("f",)), (slot, ("i",)), (slot, ("j",))), ((cell, ("f", "i", "j", "a", "b")),)),
            Functional("one_cell", cell, 3),
            Total("coords_given", ((slot, ("s",)),), ((coord, ("s", "a", "b")),)),
            Functional("one_coord", coord, 1),
            Total("row_given", ((slot, ("s",)),), ((row, ("s", "a", "b")),)),
            Functional("one_row", row, 1),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("frames_size_keeping", frames_size_keeping), ("unit_coordinates", unit_coordinates),
            ("row_exact", row_exact))),
    )


LEAN_DEFS = PAIR_DEFS + (
    "abbrev PTable := List (List Pair)",
    "",
    "def pentry (t : PTable) (i j : Nat) : Pair := (t.getD i []).getD j (0, 0)",
    "",
    "/-- The mirrored transpose of a table times the table is the unit table. -/",
    "def keepsSize (t : PTable) : Bool :=",
    "  (List.range t.length).all fun i => (List.range t.length).all fun j =>",
    "    decide (psum ((List.range t.length).map fun k => pmul (mirror (pentry t k i)) (pentry t k j)) =",
    "      if i = j then (1, 0) else (0, 0))",
    "",
    "def framesSizeKeeping (ts : List PTable) : Bool := ts.all keepsSize",
    "",
    "def unitCoordinates (c : List Pair) : Bool := decide (rowSize c = 1)",
    "",
    "/-- The named table times the coordinates is the claimed row. -/",
    "def rowExact (ts : List PTable) (k : Nat) (c r : List Pair) : Bool :=",
    "  decide ((ts.getD k []).map (fun t => psum (List.zipWith pmul t c)) = r)",
    "",
)
LEAN_CALLS = {"frames_size_keeping": "framesSizeKeeping frames_{f}", "unit_coordinates": "unitCoordinates coords_{f}",
              "row_exact": "rowExact frames_{f} named_{f} coords_{f} row_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    ts, c, r, k = tables(fs), _vector(fs, "coord"), _vector(fs, "row"), named(fs)
    assert ts is not None and c is not None and r is not None and k is not None

    def vec(v: list[QI]) -> str:
        return lean_list([lean_pair(z) for z in v])

    return [("frames", "List PTable", lean_list([lean_list([vec(row) for row in t]) for t in ts])),
            ("named", "Nat", str(k)), ("coords", "List Pair", vec(c)), ("row", "List Pair", vec(r))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clauses of `named_frames`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
