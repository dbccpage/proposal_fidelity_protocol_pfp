# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A load on the sides of a hosted complex splits exactly into a difference of
levels, a balanced part and a rim part, and every part is recomputed from the
complex's own incidence.

The complex: points, sides with a tail and a head (``tail``, ``head``), and
cells with a signed rim (``rim_with``: the side enters with its direction,
``rim_against``: against it).  The load is 1 on each marked side and 0
elsewhere.  The split is carried as exact values on the elements themselves:
a point's value is its level ``p``, a side's value is its balanced part
``h``, a cell's value is its rim weight ``q``.  With ``d0`` the side-by-point
table (``-1`` at the tail, ``+1`` at the head) and ``d1`` the cell-by-side
table of rim signs, the split recomputes ``d0 p`` and ``d1^T q`` itself; a
split whose parts merely sum to the load proves nothing.

Relational clauses, carried by derivability: ``tail_given``, ``one_tail``,
``head_given``, ``one_head``, ``tail_typed``, ``head_typed``, ``rim_typed``,
``marked_typed``.

Decoded clauses, decided over exact values outside the grammar:
``rims_close`` (``d1 d0 = 0``: every rim is a closed walk, or no split is
defined), ``balanced`` (``d0^T h = 0`` and ``d1 h = 0``) and ``rebuilds``
(``d0 p + h + d1^T q`` is the load).  The three parts are then pairwise
orthogonal.  Their Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO, Q, fmt_q
from operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure

CHALLENGE_ID = "three_way_split"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "ThreeWaySplit"
EXACT = ("py.exact.q",)
CLAUSES = ("rims_close", "balanced", "rebuilds")


@dataclass(frozen=True)
class Split:
    d0: tuple[tuple[Q, ...], ...]
    d1: tuple[tuple[Q, ...], ...]
    load: tuple[Q, ...]
    level: tuple[Q | None, ...]
    rim: tuple[Q | None, ...]
    part: tuple[Q | None, ...]


def _rows(fs: FiniteStructure, name: str) -> list[tuple[int, ...]]:
    return [a for n, a in fs.tuples if n == name]


def split(fs: FiniteStructure) -> Split:
    """The incidence tables and the values, in the declared orders."""
    points, sides, cells = fs.elements("point"), fs.elements("side"), fs.elements("cell")
    tails = {e: v for e, v in _rows(fs, "tail")}
    heads = {e: v for e, v in _rows(fs, "head")}
    d0 = tuple(tuple((ONE if heads.get(e) == v else ZERO) - (ONE if tails.get(e) == v else ZERO) for v in points)
               for e in sides)
    with_ = set(_rows(fs, "rim_with"))
    against = set(_rows(fs, "rim_against"))
    d1 = tuple(tuple((ONE if (c, e) in with_ else ZERO) - (ONE if (c, e) in against else ZERO) for e in sides)
               for c in cells)
    marked = {e for (e,) in _rows(fs, "marked")}
    return Split(d0, d1, tuple(ONE if e in marked else ZERO for e in sides),
                 tuple(fs.value(v) for v in points), tuple(fs.value(c) for c in cells),
                 tuple(fs.value(e) for e in sides))


def _dot(u: Sequence[Q], v: Sequence[Q]) -> Q:
    return sum((a * b for a, b in zip(u, v)), ZERO)


def _column(m: Sequence[Sequence[Q]], j: int) -> tuple[Q, ...]:
    return tuple(r[j] for r in m)


def rims_close(fs: FiniteStructure, _o: Oracle) -> bool:
    s = split(fs)
    return all(_dot(row, _column(s.d0, j)).is_zero() for row in s.d1 for j in range(len(s.level)))


def balanced(fs: FiniteStructure, _o: Oracle) -> bool:
    s = split(fs)
    if any(x is None for x in s.part):
        return False
    h = [x for x in s.part if x is not None]
    return (all(_dot(_column(s.d0, j), h).is_zero() for j in range(len(s.level)))
            and all(_dot(row, h).is_zero() for row in s.d1))


def rebuilt(s: Split) -> tuple[Q, ...] | None:
    if any(x is None for x in s.level + s.rim + s.part):
        return None
    p = [x for x in s.level if x is not None]
    q = [x for x in s.rim if x is not None]
    h = [x for x in s.part if x is not None]
    return tuple(_dot(s.d0[e], p) + h[e] + _dot(_column(s.d1, e), q) for e in range(len(h)))


def rebuilds(fs: FiniteStructure, _o: Oracle) -> bool:
    s = split(fs)
    return rebuilt(s) == s.load


def describe(fs: FiniteStructure) -> dict[str, object]:
    s = split(fs)
    r = rebuilt(s)
    return {"load": [fmt_q(x) for x in s.load], "rebuilt": None if r is None else [fmt_q(x) for x in r]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    out = []
    for v in verdicts:
        if dict(v.decoded).get("rebuilds") in ("PASS", "FAIL"):
            out += [(f"{LEAN_MODULE}.{v.fid}_{c}", v.fid, c) for c in CLAUSES]
    return out


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    point, side, cell = e.form("point"), e.form("side"), e.form("cell")
    tail, head, marked = e.form("tail"), e.form("head"), e.form("marked")
    rim_with, rim_against = e.form("rim_with"), e.form("rim_against")
    return Compiled(
        (
            Total("tail_given", ((side, ("e",)),), ((tail, ("e", "v")),)),
            Functional("one_tail", tail, 1),
            Total("head_given", ((side, ("e",)),), ((head, ("e", "v")),)),
            Functional("one_head", head, 1),
            Closure("tail_typed", ((tail, ("e", "v")),), ((side, ("e",)), (point, ("v",)))),
            Closure("head_typed", ((head, ("e", "v")),), ((side, ("e",)), (point, ("v",)))),
            Closure("rim_typed", ((rim_with, ("c", "e")),), ((cell, ("c",)), (side, ("e",)))),
            Closure("marked_typed", ((marked, ("e",)),), ((side, ("e",)),)),
            Closure("rim_against_typed", ((rim_against, ("c", "e")),), ((cell, ("c",)), (side, ("e",)))),
        ),
        decoded=(
            DecodedClause("rims_close", rims_close, EXACT),
            DecodedClause("balanced", balanced, EXACT),
            DecodedClause("rebuilds", rebuilds, EXACT),
        ),
    )


LEAN_DEFS = (
    "/-- Entry `(i, j)` of a table, and entry `i` of a vector. -/",
    "def entry (a : Mat) (i j : Nat) : QN := (a.getD i []).getD j 0",
    "def pick (xs : List QN) (i : Nat) : QN := xs.getD i 0",
    "",
    "/-- The sum of `f k` for `k < n`. -/",
    "def sumTo (n : Nat) (f : Nat -> QN) : QN := (List.range n).foldl (fun acc k => acc + f k) 0",
    "",
    "/-- A split: `d0` is sides by points, `d1` cells by sides; the load `c`, the levels `p`,",
    "the rim weights `q` and the balanced part `h`. -/",
    "structure SplitData where",
    "  points : Nat",
    "  sides : Nat",
    "  cells : Nat",
    "  d0 : Mat",
    "  d1 : Mat",
    "  c : List QN",
    "  p : List QN",
    "  q : List QN",
    "  h : List QN",
    "",
    "/-- `d1 d0 = 0`. -/",
    "def rimsClose (s : SplitData) : Bool :=",
    "  (List.range s.cells).all fun c => (List.range s.points).all fun v =>",
    "    decide (sumTo s.sides (fun e => entry s.d1 c e * entry s.d0 e v) = 0)",
    "",
    "/-- `d0^T h = 0` and `d1 h = 0`. -/",
    "def balanced (s : SplitData) : Bool :=",
    "  ((List.range s.points).all fun v => decide (sumTo s.sides (fun e => entry s.d0 e v * pick s.h e) = 0)) &&",
    "  ((List.range s.cells).all fun c => decide (sumTo s.sides (fun e => entry s.d1 c e * pick s.h e) = 0))",
    "",
    "/-- `d0 p + h + d1^T q = c`. -/",
    "def rebuilds (s : SplitData) : Bool :=",
    "  (List.range s.sides).all fun e =>",
    "    decide (sumTo s.points (fun v => entry s.d0 e v * pick s.p v) + pick s.h e",
    "      + sumTo s.cells (fun c => entry s.d1 c e * pick s.q c) = pick s.c e)",
    "",
)
LEAN_CALLS = {"rims_close": "rimsClose", "balanced": "balanced", "rebuilds": "rebuilds"}


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    """One split per evaluated fixture; the kernel re-decides each value clause."""
    from operations.use_cases.level_engine.research_engine import lean_text as T

    by = {f.fid: f for f in fixtures}
    lines = T.header(LEAN_MODULE, "The value clauses of `three_way_split`, decided by the kernel", LEAN_DEFS)
    certs = lean_certificates(verdicts)
    fids = sorted({fid for _, fid, _ in certs}, key=[v.fid for v in verdicts].index)
    for fid in fids:
        s = split(by[fid].structure)
        vals = [x for x in s.level + s.rim + s.part if x is not None]
        assert len(vals) == len(s.level) + len(s.rim) + len(s.part)
        p, q, h = vals[:len(s.level)], vals[len(s.level):len(s.level) + len(s.rim)], vals[len(s.level) + len(s.rim):]
        lines += [f"def split_{fid} : SplitData :=",
                  f"  {{ points := {len(s.level)}, sides := {len(s.part)}, cells := {len(s.rim)},",
                  f"    d0 := {T.mat(s.d0)},",
                  f"    d1 := {T.mat(s.d1)},",
                  f"    c := {T.row(s.load)}, p := {T.row(p)},",
                  f"    q := {T.row(q)}, h := {T.row(h)} }}", ""]
    for name, fid, clause in certs:
        verdict = "true" if dict(next(v for v in verdicts if v.fid == fid).decoded)[clause] == "PASS" else "false"
        lines += [f"theorem {name.split('.', 1)[1]} : {LEAN_CALLS[clause]} split_{fid} = {verdict} := by decide", ""]
    lines += [f"end {LEAN_MODULE}", ""]
    return "\n".join(lines)
