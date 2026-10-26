# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A finite complex of cells, each with a degree, and its claimed pages: at
each page, the listed cells and the claimed steps between cells.

The claim: cells and pages (each in declared order), each cell carrying its
degree and each page its number as values, ``face(c, f)`` (cell ``f`` is a
facet of cell ``c``), ``listed(p, c)`` (page ``p`` lists cell ``c``) and
``step(p, s, t)`` (page ``p`` claims a step from cell ``s`` down to cell
``t``, with coefficient one over the two-element field).

Relational clauses, carried by derivability over the hosted claim:
``some_page``, ``faces_typed``, ``listed_typed`` and ``steps_typed``.

Decoded clauses, decided outside the grammar:

* ``well_formed``: degrees and page numbers are naturals, the pages are
  numbered 1, 2, ... in declared order, a step is claimed only on a page
  before the last, and each cell's facets are the facets of the simplex on
  its vertices (the cells with no facet), all present;
* ``degrees_kept``: no facet has a higher degree than its cell;
* ``steps_graded``: a step on page ``r`` lowers the degree by exactly ``r``
  and the dimension by one;
* ``square_zero``: on each page, a step followed by a step is zero over the
  two-element field;
* ``steps_recomputed``: on each page before the last, the correctly graded
  claimed steps are exactly the pairs of degree gap ``r`` the column
  reduction of the facet table finds (cells ordered by degree, dimension and
  declared position);
* ``no_return``: no page lists a cell a pair of smaller gap has already
  removed (the refused case: a removed class listed again);
* ``pages_recomputed``: apart from such cells, each page lists exactly the
  cells in no pair of gap below its number.

Their Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import Q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "filtered_pages"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "FilteredPages"
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "degrees_kept", "steps_graded", "square_zero", "steps_recomputed", "no_return",
           "pages_recomputed")
# ``well_formed`` stays computed: the kernel re-decides the other six.
LEAN_CLAUSES = CLAUSES[1:]


def _nat(x: Q | None) -> int | None:
    return x.num if x is not None and x.den == 1 and x.num >= 0 else None


def degrees(fs: FiniteStructure) -> list[int]:
    """Each cell's degree by position; -1 when it is not a natural."""
    return [d if (d := _nat(fs.value(c))) is not None else -1 for c in fs.elements("cell")]


def numbers(fs: FiniteStructure) -> list[int]:
    return [r if (r := _nat(fs.value(p))) is not None else -1 for p in fs.elements("page")]


def _cpos(fs: FiniteStructure, e: int) -> int:
    k = position(fs, "cell", e)
    return -1 if k is None else k


def facets(fs: FiniteStructure) -> list[list[int]]:
    """Each cell's facets, by position."""
    out: list[list[int]] = [[] for _ in fs.elements("cell")]
    for c, f in rows(fs, "face"):
        i = position(fs, "cell", c)
        if i is not None:
            out[i].append(_cpos(fs, f))
    return [sorted(x) for x in out]


def listed(fs: FiniteStructure) -> list[list[int]]:
    out: list[list[int]] = [[] for _ in fs.elements("page")]
    for p, c in rows(fs, "listed"):
        i = position(fs, "page", p)
        if i is not None:
            out[i].append(_cpos(fs, c))
    return [sorted(x) for x in out]


def steps(fs: FiniteStructure) -> list[tuple[int, int, int]]:
    """Claimed steps as (page position, source, target)."""
    out = []
    for p, s, t in rows(fs, "step"):
        i = position(fs, "page", p)
        out.append((-1 if i is None else i, _cpos(fs, s), _cpos(fs, t)))
    return sorted(out)


def vertex_sets(fs: FiniteStructure) -> list[frozenset[int]]:
    """Each cell's vertices: the cells with no facet below it, by position."""
    fa = facets(fs)
    memo: dict[int, frozenset[int]] = {}

    def go(c: int, depth: int) -> frozenset[int]:
        if c in memo:
            return memo[c]
        if depth > len(fa) or not 0 <= c < len(fa):
            return frozenset()
        got = frozenset({c}) if not fa[c] else frozenset().union(*(go(f, depth + 1) for f in fa[c]))
        memo[c] = got
        return got

    return [go(c, 0) for c in range(len(fa))]


def dims(fs: FiniteStructure) -> list[int]:
    return [len(v) - 1 for v in vertex_sets(fs)]


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    deg, num, fa, vs = degrees(fs), numbers(fs), facets(fs), vertex_sets(fs)
    if -1 in deg or num != list(range(1, len(num) + 1)):
        return False
    if any(not 0 <= p < len(num) - 1 for p, _, _ in steps(fs)):
        return False
    by_set = {v: c for c, v in enumerate(vs)}
    if len(by_set) != len(vs):
        return False
    for c, f in enumerate(fa):
        if not f:
            continue
        want = sorted(by_set.get(vs[c] - {x}, -1) for x in vs[c])
        if len(vs[c]) < 2 or want != f:
            return False
    return True


def degrees_kept(fs: FiniteStructure, _o: Oracle) -> bool:
    deg = degrees(fs)
    return all(deg[f] <= deg[c] for c, fl in enumerate(facets(fs)) for f in fl)


def _graded(fs: FiniteStructure, p: int, s: int, t: int) -> bool:
    deg, num, dim = degrees(fs), numbers(fs), dims(fs)
    return 0 <= p < len(num) and deg[s] - deg[t] == num[p] and dim[s] == dim[t] + 1


def steps_graded(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(_graded(fs, p, s, t) for p, s, t in steps(fs))


def square_zero(fs: FiniteStructure, _o: Oracle) -> bool:
    st = steps(fs)
    for p in {p for p, _, _ in st}:
        mine = [(s, t) for q, s, t in st if q == p]
        for x in {s for s, _ in mine}:
            hits: dict[int, int] = {}
            for s, m in mine:
                if s == x:
                    for m2, t in mine:
                        if m2 == m:
                            hits[t] = hits.get(t, 0) + 1
            if any(k % 2 for k in hits.values()):
                return False
    return True


def pairs(fs: FiniteStructure) -> list[tuple[int, int, int]]:
    """(lower, upper, gap) from the column reduction over the two-element
    field, cells ordered by degree, dimension and declared position."""
    deg, dim, fa = degrees(fs), dims(fs), facets(fs)
    order = sorted(range(len(deg)), key=lambda c: (deg[c], dim[c], c))
    rank = {c: i for i, c in enumerate(order)}
    owner: dict[int, set[int]] = {}
    out = []
    for c in order:
        col = {rank[f] for f in fa[c] if f in rank}
        while col and max(col) in owner:
            col ^= owner[max(col)]
        if col:
            owner[max(col)] = col
            low = order[max(col)]
            out.append((low, c, deg[c] - deg[low]))
    return out


def page_of(fs: FiniteStructure, r: int) -> list[int]:
    gone = {x for lo, up, g in pairs(fs) if g < r for x in (lo, up)}
    return [c for c in range(len(fs.elements("cell"))) if c not in gone]


def steps_recomputed(fs: FiniteStructure, _o: Oracle) -> bool:
    num, pr = numbers(fs), pairs(fs)
    for p in range(len(num) - 1):
        claimed = {(s, t) for q, s, t in steps(fs) if q == p and _graded(fs, q, s, t)}
        if claimed != {(up, lo) for lo, up, g in pr if g == num[p]}:
            return False
    return True


def no_return(fs: FiniteStructure, _o: Oracle) -> bool:
    """No page lists a cell that a pair of smaller gap has removed."""
    return all(set(ls) <= set(page_of(fs, r)) for r, ls in zip(numbers(fs), listed(fs)))


def pages_recomputed(fs: FiniteStructure, _o: Oracle) -> bool:
    """Every cell of the recomputed page is listed (a listed removed cell is
    ``no_return``'s refusal, not this one's)."""
    return all(set(page_of(fs, r)) <= set(ls) for r, ls in zip(numbers(fs), listed(fs)))


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"pages": {str(r): page_of(fs, r) for r in numbers(fs)},
            "pairs": [list(x) for x in pairs(fs)]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, LEAN_CLAUSES, verdicts, "degrees_kept")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    cell, page = e.form("cell"), e.form("page")
    face, lst, step = e.form("face"), e.form("listed"), e.form("step")
    return Compiled(
        (
            Total("some_page", (), ((page, ("p",)),)),
            Closure("faces_typed", ((face, ("c", "f")),), ((cell, ("c",)), (cell, ("f",)))),
            Closure("listed_typed", ((lst, ("p", "c")),), ((page, ("p",)), (cell, ("c",)))),
            Closure("steps_typed", ((step, ("p", "s", "t")),), ((page, ("p",)), (cell, ("s",)), (cell, ("t",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("degrees_kept", degrees_kept), ("steps_graded", steps_graded),
            ("square_zero", square_zero), ("steps_recomputed", steps_recomputed), ("no_return", no_return),
            ("pages_recomputed", pages_recomputed))),
    )


LEAN_DEFS = (
    "/-- A cell: its degree and its facets, by position. -/",
    "abbrev Cell := Prod Nat (List Nat)",
    "",
    "def deg (cs : List Cell) (c : Nat) : Nat := (cs.getD c (0, [])).1",
    "",
    "def facetsOf (cs : List Cell) (c : Nat) : List Nat := (cs.getD c (0, [])).2",
    "",
    "def dedup : List Nat -> List Nat",
    "  | [] => []",
    "  | x :: xs => if xs.contains x then dedup xs else x :: dedup xs",
    "",
    "/-- The vertices below a cell, with fuel bounding the depth. -/",
    "def verts (cs : List Cell) : Nat -> Nat -> List Nat",
    "  | 0, _ => []",
    "  | fuel + 1, c => if (facetsOf cs c).isEmpty then [c]",
    "      else dedup ((facetsOf cs c).flatMap (verts cs fuel))",
    "",
    "def dim (cs : List Cell) (c : Nat) : Nat := (verts cs (cs.length + 1) c).length - 1",
    "",
    "def degreesKept (cs : List Cell) : Bool :=",
    "  (List.range cs.length).all fun c => (facetsOf cs c).all fun f => deg cs f <= deg cs c",
    "",
    "def graded (cs : List Cell) (rs : List Nat) (s : Prod Nat (Prod Nat Nat)) : Bool :=",
    "  s.1 < rs.length && deg cs s.2.1 == deg cs s.2.2 + rs.getD s.1 0 && deg cs s.2.2 <= deg cs s.2.1 &&",
    "    dim cs s.2.1 == dim cs s.2.2 + 1",
    "",
    "def stepsGraded (cs : List Cell) (rs : List Nat) (ss : List (Prod Nat (Prod Nat Nat))) : Bool :=",
    "  ss.all (graded cs rs)",
    "",
    "/-- On each page, the two-step paths from a source to a target are even in number. -/",
    "def squareZero (ss : List (Prod Nat (Prod Nat Nat))) : Bool :=",
    "  ss.all fun a => ss.all fun b => !(a.1 == b.1) ||",
    "    (ss.filter fun m => m.1 == a.1 && m.2.1 == a.2.1 && ss.contains (a.1, (m.2.2, b.2.2))).length % 2 == 0",
    "",
    "/-- Symmetric difference of two lists read as sets. -/",
    "def xorL (a b : List Nat) : List Nat := (a.filter fun x => !b.contains x) ++ (b.filter fun x => !a.contains x)",
    "",
    "def maxL (a : List Nat) : Nat := a.foldl max 0",
    "",
    "/-- Reduce a column against the owners found so far; fuel bounds the steps. -/",
    "def reduce (owners : List (Prod Nat (List Nat))) : Nat -> List Nat -> List Nat",
    "  | 0, col => col",
    "  | fuel + 1, col => if col.isEmpty then col else",
    "      match owners.find? (fun o => o.1 == maxL col) with",
    "      | some o => reduce owners fuel (xorL col o.2)",
    "      | none => col",
    "",
    "/-- Cells ordered by degree, dimension and position. -/",
    "def key (cs : List Cell) (c : Nat) : Nat := (deg cs c * (cs.length + 1) + dim cs c) * (cs.length + 1) + c",
    "",
    "def insertBy (k : Nat -> Nat) (x : Nat) : List Nat -> List Nat",
    "  | [] => [x]",
    "  | y :: ys => if k x <= k y then x :: y :: ys else y :: insertBy k x ys",
    "",
    "def order (cs : List Cell) : List Nat := (List.range cs.length).foldr (insertBy (key cs)) []",
    "",
    "def rankOf (cs : List Cell) (c : Nat) : Nat := (order cs).idxOf c",
    "",
    "/-- The pairs (lower, upper) of the column reduction. -/",
    "def pairsOf (cs : List Cell) : List (Prod Nat Nat) :=",
    "  let step := fun (acc : Prod (List (Prod Nat (List Nat))) (List (Prod Nat Nat))) (c : Nat) =>",
    "    let col := reduce acc.1 (cs.length + 1) ((facetsOf cs c).map (rankOf cs))",
    "    if col.isEmpty then acc else ((maxL col, col) :: acc.1, ((order cs).getD (maxL col) 0, c) :: acc.2)",
    "  ((order cs).foldl step ([], [])).2",
    "",
    "def gap (cs : List Cell) (p : Prod Nat Nat) : Nat := deg cs p.2 - deg cs p.1",
    "",
    "def pageOf (cs : List Cell) (r : Nat) : List Nat :=",
    "  (List.range cs.length).filter fun c => !((pairsOf cs).any fun p => gap cs p < r && (p.1 == c || p.2 == c))",
    "",
    "def stepsRecomputed (cs : List Cell) (rs : List Nat) (ss : List (Prod Nat (Prod Nat Nat))) : Bool :=",
    "  (List.range (rs.length - 1)).all fun p =>",
    "    let claimed := (ss.filter fun s => s.1 == p && graded cs rs s).map fun s => (s.2.1, s.2.2)",
    "    let found := ((pairsOf cs).filter fun q => gap cs q == rs.getD p 0).map fun q => (q.2, q.1)",
    "    claimed.all (fun x => found.contains x) && found.all (fun x => claimed.contains x)",
    "",
    "def noReturn (cs : List Cell) (rs : List Nat) (ls : List (List Nat)) : Bool :=",
    "  (List.range rs.length).all fun p => (ls.getD p []).all fun c => (pageOf cs (rs.getD p 0)).contains c",
    "",
    "def pagesRecomputed (cs : List Cell) (rs : List Nat) (ls : List (List Nat)) : Bool :=",
    "  (List.range rs.length).all fun p => (pageOf cs (rs.getD p 0)).all fun c => (ls.getD p []).contains c",
    "",
)
LEAN_CALLS = {
    "degrees_kept": "degreesKept cells_{f}",
    "steps_graded": "stepsGraded cells_{f} pages_{f} steps_{f}",
    "square_zero": "squareZero steps_{f}",
    "steps_recomputed": "stepsRecomputed cells_{f} pages_{f} steps_{f}",
    "no_return": "noReturn cells_{f} pages_{f} listed_{f}",
    "pages_recomputed": "pagesRecomputed cells_{f} pages_{f} listed_{f}",
}


def _nats(xs: Sequence[int]) -> str:
    return lean_list([str(x) for x in xs])


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    deg, fa = degrees(fs), facets(fs)
    assert -1 not in deg and -1 not in numbers(fs) and all(p >= 0 and s >= 0 and t >= 0 for p, s, t in steps(fs))
    return [("cells", "List Cell", lean_list([f"({d}, {_nats(f)})" for d, f in zip(deg, fa)])),
            ("pages", "List Nat", _nats(numbers(fs))),
            ("listed", "List (List Nat)", lean_list([_nats(ls) for ls in listed(fs)])),
            ("steps", "List (Prod Nat (Prod Nat Nat))", lean_list([f"({p}, ({s}, {t}))" for p, s, t in steps(fs)]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `filtered_pages`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
