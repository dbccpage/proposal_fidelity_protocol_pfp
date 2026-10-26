"""A finite two-dimensional complex of oriented edges and triangular faces,
its claimed incidence tables, a claimed rim, and the claimed cells off the
rim.

The claim: vertices, edges and faces (in declared order),
``ends(e, u, w)`` (edge ``e`` runs from ``u`` to ``w``),
``face_of(f, a, b, c)`` (face ``f``'s boundary runs ``a``, ``b``, ``c``, back to
``a``), the claimed tables as their nonzero entries (``d0_plus(e, v)`` and
``d0_minus(e, v)``: edge by vertex; ``d1_plus(f, e)`` and ``d1_minus(f, e)``:
face by edge), the claimed rim (``rim_edge``, ``rim_vertex``) and the
claimed cells off the rim (``inner_vertex``, ``inner_edge``,
``inner_face``).

Relational clauses, carried by derivability over the hosted claim:
``ends_given``, ``one_ends``, ``face_given`` and ``one_face``.

Decoded clauses, decided outside the grammar: ``complex_ok`` (each face has
three distinct vertices and its boundary edges are declared),
``nilpotent`` (the claimed face table times the claimed edge table is zero),
``incidence_exact`` (each claimed table is the one derived from the cells:
minus one at an edge's first vertex and one at its second; one or minus one
where a face's boundary runs along or against an edge; supplied tables that
compose to zero are not enough), ``rim_exact`` (the rim is exactly the edges
with one incident face and their end vertices: an invalid rim is refused)
and ``relative_exact`` (the cells off the rim are exactly the cells not on
it).  Their Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from engine.encoding import Encoding
from engine.kinds import Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "rim_cochains"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "RimCochains"
EXACT: tuple[str, ...] = ()
CLAUSES = ("complex_ok", "nilpotent", "incidence_exact", "rim_exact", "relative_exact")
Grid = list[list[int]]


def _pos(fs: FiniteStructure, sort: str, e: int) -> int:
    k = position(fs, sort, e)
    return -1 if k is None else k


def edges(fs: FiniteStructure) -> list[tuple[int, int]]:
    got = {e: (_pos(fs, "vertex", u), _pos(fs, "vertex", w)) for e, u, w in rows(fs, "ends")}
    return [got.get(e, (-1, -1)) for e in fs.elements("edge")]


def faces(fs: FiniteStructure) -> list[tuple[int, int, int]]:
    got = {f: (_pos(fs, "vertex", a), _pos(fs, "vertex", b), _pos(fs, "vertex", c)) for f, a, b, c in rows(fs, "face_of")}
    return [got.get(f, (-1, -1, -1)) for f in fs.elements("face")]


def _claimed(fs: FiniteStructure, name: str, rows_sort: str, cols_sort: str) -> Grid:
    ri, ci = fs.elements(rows_sort), fs.elements(cols_sort)
    out = [[0] * len(ci) for _ in ri]
    for sign, suffix in ((1, "plus"), (-1, "minus")):
        for r, c in rows(fs, f"{name}_{suffix}"):
            i, j = position(fs, rows_sort, r), position(fs, cols_sort, c)
            if i is not None and j is not None:
                out[i][j] += sign
    return out


def claimed_d0(fs: FiniteStructure) -> Grid:
    return _claimed(fs, "d0", "edge", "vertex")


def claimed_d1(fs: FiniteStructure) -> Grid:
    return _claimed(fs, "d1", "face", "edge")


def derived_d0(fs: FiniteStructure) -> Grid:
    n = len(fs.elements("vertex"))
    out = []
    for u, w in edges(fs):
        row = [0] * n
        if 0 <= u < n and 0 <= w < n:
            row[u] -= 1
            row[w] += 1
        out.append(row)
    return out


def derived_d1(fs: FiniteStructure) -> Grid:
    es = edges(fs)
    out = []
    for a, b, c in faces(fs):
        row = [0] * len(es)
        for x, y in ((a, b), (b, c), (c, a)):
            for k, (u, w) in enumerate(es):
                if (u, w) == (x, y):
                    row[k] += 1
                elif (u, w) == (y, x):
                    row[k] -= 1
        out.append(row)
    return out


def complex_ok(fs: FiniteStructure, _o: Oracle) -> bool:
    es = {frozenset(e) for e in edges(fs)}
    return all(len({a, b, c}) == 3 and all(frozenset(p) in es for p in ((a, b), (b, c), (c, a)))
               for a, b, c in faces(fs))


def nilpotent(fs: FiniteStructure, _o: Oracle) -> bool:
    d0, d1 = claimed_d0(fs), claimed_d1(fs)
    return all(sum(d1[f][e] * d0[e][v] for e in range(len(d0))) == 0 for f in range(len(d1)) for v in range(len(d0[0]) if d0 else 0))


def incidence_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    return claimed_d0(fs) == derived_d0(fs) and claimed_d1(fs) == derived_d1(fs)


def rim(fs: FiniteStructure) -> tuple[list[int], list[int]]:
    d1 = derived_d1(fs)
    es = edges(fs)
    rim_edges = [k for k in range(len(es)) if sum(1 for f in d1 if f[k] != 0) == 1]
    rim_vertices = sorted({v for k in rim_edges for v in es[k]})
    return rim_edges, rim_vertices


def _marked(fs: FiniteStructure, name: str, sort: str) -> list[int]:
    return sorted(k for (x,) in rows(fs, name) if (k := position(fs, sort, x)) is not None)


def rim_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    re, rv = rim(fs)
    return _marked(fs, "rim_edge", "edge") == re and _marked(fs, "rim_vertex", "vertex") == rv


def relative_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    re, rv = rim(fs)
    n_v, n_e, n_f = len(fs.elements("vertex")), len(fs.elements("edge")), len(fs.elements("face"))
    return (_marked(fs, "inner_vertex", "vertex") == [v for v in range(n_v) if v not in rv]
            and _marked(fs, "inner_edge", "edge") == [e for e in range(n_e) if e not in re]
            and _marked(fs, "inner_face", "face") == list(range(n_f)))


def describe(fs: FiniteStructure) -> dict[str, object]:
    re, rv = rim(fs)
    return {"rim_edges": re, "rim_vertices": rv}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "rim_exact")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    edge, face = e.form("edge"), e.form("face")
    ends, face_f = e.form("ends"), e.form("face_of")
    return Compiled(
        (
            Total("ends_given", ((edge, ("e",)),), ((ends, ("e", "u", "w")),)),
            Functional("one_ends", ends, 1),
            Total("face_given", ((face, ("f",)),), ((face_f, ("f", "a", "b", "c")),)),
            Functional("one_face", face_f, 1),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("complex_ok", complex_ok), ("nilpotent", nilpotent), ("incidence_exact", incidence_exact),
            ("rim_exact", rim_exact), ("relative_exact", relative_exact))),
    )


LEAN_DEFS = (
    "abbrev Edge := Prod Nat Nat",
    "",
    "abbrev Face := Prod Nat (Prod Nat Nat)",
    "",
    "def sides (f : Face) : List Edge := [(f.1, f.2.1), (f.2.1, f.2.2), (f.2.2, f.1)]",
    "",
    "def complexOk (es : List Edge) (fs : List Face) : Bool :=",
    "  fs.all fun f => f.1 != f.2.1 && f.2.1 != f.2.2 && f.2.2 != f.1 &&",
    "    (sides f).all fun s => es.any fun e => (e.1 == s.1 && e.2 == s.2) || (e.1 == s.2 && e.2 == s.1)",
    "",
    "/-- The edge table derived from the cells. -/",
    "def dZero (n : Nat) (es : List Edge) : List (List Int) :=",
    "  es.map fun e => (List.range n).map fun v => (if v == e.2 then 1 else 0) - (if v == e.1 then 1 else 0)",
    "",
    "/-- The face table derived from the cells. -/",
    "def dOne (es : List Edge) (fs : List Face) : List (List Int) :=",
    "  fs.map fun f => es.map fun e => (sides f).foldl (fun acc s =>",
    "    acc + (if e.1 == s.1 && e.2 == s.2 then 1 else 0) - (if e.1 == s.2 && e.2 == s.1 then 1 else 0)) 0",
    "",
    "def entry (t : List (List Int)) (i j : Nat) : Int := (t.getD i []).getD j 0",
    "",
    "def nilpotent (n : Nat) (d0 d1 : List (List Int)) : Bool :=",
    "  (List.range d1.length).all fun f => (List.range n).all fun v =>",
    "    (List.range d0.length).foldl (fun acc e => acc + entry d1 f e * entry d0 e v) 0 == 0",
    "",
    "def incidenceExact (n : Nat) (es : List Edge) (fs : List Face) (d0 d1 : List (List Int)) : Bool :=",
    "  decide (d0 = dZero n es) && decide (d1 = dOne es fs)",
    "",
    "/-- The rim: edges with exactly one incident face, and their end vertices, in order. -/",
    "def rimEdges (es : List Edge) (fs : List Face) : List Nat :=",
    "  (List.range es.length).filter fun k => ((dOne es fs).filter fun r => r.getD k 0 != 0).length == 1",
    "",
    "def rimVertices (n : Nat) (es : List Edge) (fs : List Face) : List Nat :=",
    "  (List.range n).filter fun v => (rimEdges es fs).any fun k => let e := es.getD k (0, 0); e.1 == v || e.2 == v",
    "",
    "def rimExact (n : Nat) (es : List Edge) (fs : List Face) (re rv : List Nat) : Bool :=",
    "  decide (re = rimEdges es fs) && decide (rv = rimVertices n es fs)",
    "",
    "def relativeExact (n : Nat) (es : List Edge) (fs : List Face) (iv ie ifc : List Nat) : Bool :=",
    "  decide (iv = (List.range n).filter (fun v => !(rimVertices n es fs).contains v)) &&",
    "    decide (ie = (List.range es.length).filter (fun k => !(rimEdges es fs).contains k)) &&",
    "    decide (ifc = List.range fs.length)",
    "",
)
LEAN_CALLS = {"complex_ok": "complexOk edges_{f} faces_{f}", "nilpotent": "nilpotent n_{f} d0_{f} d1_{f}",
              "incidence_exact": "incidenceExact n_{f} edges_{f} faces_{f} d0_{f} d1_{f}",
              "rim_exact": "rimExact n_{f} edges_{f} faces_{f} rimE_{f} rimV_{f}",
              "relative_exact": "relativeExact n_{f} edges_{f} faces_{f} innerV_{f} innerE_{f} innerF_{f}"}


def _ints(xs: Sequence[int]) -> str:
    return lean_list([f"({x})" for x in xs])


def _nats(xs: Sequence[int]) -> str:
    return lean_list([str(x) for x in xs])


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    es, fcs = edges(fs), faces(fs)
    assert all(x >= 0 for e in es for x in e) and all(x >= 0 for f in fcs for x in f)
    return [("n", "Nat", str(len(fs.elements("vertex")))),
            ("edges", "List Edge", lean_list([f"({u}, {w})" for u, w in es])),
            ("faces", "List Face", lean_list([f"({a}, ({b}, {c}))" for a, b, c in fcs])),
            ("d0", "List (List Int)", lean_list([_ints(r) for r in claimed_d0(fs)])),
            ("d1", "List (List Int)", lean_list([_ints(r) for r in claimed_d1(fs)])),
            ("rimE", "List Nat", _nats(_marked(fs, "rim_edge", "edge"))),
            ("rimV", "List Nat", _nats(_marked(fs, "rim_vertex", "vertex"))),
            ("innerV", "List Nat", _nats(_marked(fs, "inner_vertex", "vertex"))),
            ("innerE", "List Nat", _nats(_marked(fs, "inner_edge", "edge"))),
            ("innerF", "List Nat", _nats(_marked(fs, "inner_face", "face")))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `rim_cochains`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
