"""A two-dimensional table of cells: vertices, edges with a tail and a head,
and faces as signed sums of edges.  Every reference names a declared cell
of the right kind, and the boundary of each face's boundary is zero: the
boundary maps are derived from the cells, never supplied.

The claim: cells (in declared order), ``vertex(v)``, ``edge(e, t, h)``
(edge ``e`` runs from tail ``t`` to head ``h``), ``face(f)``, ``plus(f,
e)`` and ``minus(f, e)`` (face ``f``'s boundary takes edge ``e`` with sign
``+`` or ``-``).

Relational clauses, carried by derivability over the hosted claim:
``ends_declared`` (an edge's tail and head are declared vertices: the
refused case is a dangling edge), ``plus_declared`` and ``minus_declared``
(a face's terms name declared edges), ``one_edge``, ``kinds_apart`` (no cell
is both a vertex and an edge) and the typing closures.

Decoded clause, decided outside the grammar: ``boundary_closed`` (for each
face, the signed sum of its edges' boundaries, head minus tail, is zero at
every vertex, with integer coefficients).  Its Lean certificate is
re-decided by the kernel.

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

CHALLENGE_ID = "signed_cells"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "SignedCells"
EXACT: tuple[str, ...] = ()
CLAUSES = ("boundary_closed",)


def faces(fs: FiniteStructure) -> list[list[tuple[int, int, int]]]:
    """Each face's terms as (tail, head, sign), by element."""
    ends = {e: (t, h) for e, t, h in rows(fs, "edge")}
    out = []
    for (f,) in rows(fs, "face"):
        terms = [(ends[e][0], ends[e][1], 1) for ff, e in rows(fs, "plus") if ff == f and e in ends]
        terms += [(ends[e][0], ends[e][1], -1) for ff, e in rows(fs, "minus") if ff == f and e in ends]
        out.append(sorted(terms))
    return out


def boundary_closed(fs: FiniteStructure, _o: Oracle) -> bool:
    for terms in faces(fs):
        total: dict[int, int] = {}
        for t, h, s in terms:
            total[h] = total.get(h, 0) + s
            total[t] = total.get(t, 0) - s
        if any(total.values()):
            return False
    return True


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"faces": [[list(x) for x in f] for f in faces(fs)]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "boundary_closed")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    cell, vertex, edge, face = e.form("cell"), e.form("vertex"), e.form("edge"), e.form("face")
    plus, minus = e.form("plus"), e.form("minus")
    return Compiled(
        (
            Closure("ends_declared", ((edge, ("e", "t", "h")),), ((vertex, ("t",)), (vertex, ("h",)))),
            Total("plus_declared", ((plus, ("f", "e")),), ((edge, ("e", "t", "h")),)),
            Total("minus_declared", ((minus, ("f", "e")),), ((edge, ("e", "t", "h")),)),
            Functional("one_edge", edge, 1),
            Forbid("kinds_apart", ((vertex, ("x",)), (edge, ("x", "t", "h")))),
            Closure("plus_typed", ((plus, ("f", "e")),), ((face, ("f",)), (cell, ("e",)))),
            Closure("minus_typed", ((minus, ("f", "e")),), ((face, ("f",)), (cell, ("e",)))),
        ),
        decoded=(DecodedClause("boundary_closed", boundary_closed, EXACT),),
    )


LEAN_DEFS = (
    "/-- A face's terms: tail, head and sign (true for plus). -/",
    "abbrev Term := Prod Nat (Prod Nat Bool)",
    "",
    "def coef (ts : List Term) (v : Nat) : Int :=",
    "  ts.foldl (fun acc t => acc + (if t.2.1 == v then (if t.2.2 then 1 else -1) else 0)",
    "    - (if t.1 == v then (if t.2.2 then 1 else -1) else 0)) 0",
    "",
    "def boundaryClosed (n : Nat) (fs : List (List Term)) : Bool :=",
    "  fs.all fun ts => (List.range n).all fun v => coef ts v == 0",
    "",
)
LEAN_CALLS = {"boundary_closed": "boundaryClosed n_{f} faces_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    return [("n", "Nat", str(fs.n())),
            ("faces", "List (List Term)",
             lean_list([lean_list([f"({t}, ({h}, {'true' if s > 0 else 'false'}))" for t, h, s in f])
                        for f in faces(fs)]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The boundary clause of `signed_cells`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
