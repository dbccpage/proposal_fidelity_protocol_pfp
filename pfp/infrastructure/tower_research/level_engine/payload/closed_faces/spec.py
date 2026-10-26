# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A solid cell on four corners, its four faces as closed walks with
connectors from a base corner, a value for each face (a permutation of a
finite label set), and, optionally, transports on the six edges: the
faces' values, multiplied in their declared order, must close to the unit,
read as ordered products, never through a parity or other unordered shadow.

The claim: corners, labels, faces and slots (each in declared order; the
first corner is the base), each face carrying its place in the product and
each slot its index as values, ``joins(f, i, v)`` (face ``f``'s connector
has corner ``v`` at slot ``i``), ``runs(f, i, v)`` (face ``f``'s boundary
walk has corner ``v`` at slot ``i``), ``sends(f, x, y)`` (face ``f``'s value
takes label ``x`` to ``y``) and ``link(u, v, x, y)`` (the transport on the
edge from ``u`` to a later corner ``v`` takes ``x`` to ``y``; read backward
through its inverse).

Relational clauses, carried by derivability over the hosted claim:
``sends_given``, ``one_send``, ``one_join``, ``one_run``, ``one_link``,
``joins_typed``, ``runs_typed`` and ``links_typed``.

Decoded clauses, decided outside the grammar:

* ``well_formed``: slot indices are 0, 1, ... in declared order, face places
  are distinct naturals, every walk fills an initial run of slots, every
  value and transport is a permutation, and the transports are given on no
  edge or on all six;
* ``walks_ok``: each connector runs from the base to its boundary walk's
  start, each boundary walk is closed, and no walk repeats a corner in
  place;
* ``boundary_ok``: the boundary walks are four triangles using every
  ordered edge of the cell exactly once;
* ``faces_match``: with transports given, each face's value is the ordered
  product along its connector, its boundary walk and its connector reversed;
* ``closed``: the face values multiplied in declared place order are the
  unit (the refused case: values whose parity balances while their ordered
  product is a three-cycle).

Their Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import Q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "closed_faces"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "ClosedFaces"
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "walks_ok", "boundary_ok", "faces_match", "closed")
LEAN_CLAUSES = ("walks_ok", "boundary_ok", "faces_match", "closed")
Perm = list[int]


def _nat(x: Q | None) -> int:
    return x.num if x is not None and x.den == 1 and x.num >= 0 else -1


def _p(fs: FiniteStructure, sort: str, e: int) -> int:
    k = position(fs, sort, e)
    return -1 if k is None else k


def places(fs: FiniteStructure) -> list[int]:
    return [_nat(fs.value(f)) for f in fs.elements("face")]


def _walk(fs: FiniteStructure, name: str, f: int) -> list[int]:
    got = {_nat(fs.value(i)): _p(fs, "corner", v) for ff, i, v in rows(fs, name) if ff == f}
    return [got[k] for k in range(len(got)) if k in got] if set(got) == set(range(len(got))) else [-1]


def connectors(fs: FiniteStructure) -> list[list[int]]:
    return [_walk(fs, "joins", f) for f in fs.elements("face")]


def cycles(fs: FiniteStructure) -> list[list[int]]:
    return [_walk(fs, "runs", f) for f in fs.elements("face")]


def values(fs: FiniteStructure) -> list[Perm]:
    n = len(fs.elements("label"))
    out = []
    for f in fs.elements("face"):
        img = {_p(fs, "label", x): _p(fs, "label", y) for ff, x, y in rows(fs, "sends") if ff == f}
        out.append([img.get(k, -1) for k in range(n)])
    return out


def links(fs: FiniteStructure) -> dict[tuple[int, int], Perm]:
    n = len(fs.elements("label"))
    got: dict[tuple[int, int], dict[int, int]] = {}
    for u, v, x, y in rows(fs, "link"):
        got.setdefault((_p(fs, "corner", u), _p(fs, "corner", v)), {})[_p(fs, "label", x)] = _p(fs, "label", y)
    return {k: [m.get(i, -1) for i in range(n)] for k, m in got.items()}


def _is_perm(p: Perm, n: int) -> bool:
    return sorted(p) == list(range(n))


def _then(p: Perm, q: Perm) -> Perm:
    return [q[x] if 0 <= x < len(q) else -1 for x in p]


def _inverse(p: Perm) -> Perm:
    out = [-1] * len(p)
    for x, y in enumerate(p):
        if 0 <= y < len(p):
            out[y] = x
    return out


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    n, corners = len(fs.elements("label")), len(fs.elements("corner"))
    slots = [_nat(fs.value(s)) for s in fs.elements("slot")]
    pl = places(fs)
    if slots != list(range(len(slots))) or -1 in pl or len(set(pl)) != len(pl) or corners != 4:
        return False
    if any(w == [-1] for w in connectors(fs) + cycles(fs)):
        return False
    ls = links(fs)
    if ls and set(ls) != {(u, v) for u in range(4) for v in range(u + 1, 4)}:
        return False
    return all(_is_perm(p, n) for p in values(fs) + list(ls.values()))


def walks_ok(fs: FiniteStructure, _o: Oracle) -> bool:
    for conn, cyc in zip(connectors(fs), cycles(fs)):
        if not conn or conn[0] != 0 or not cyc or conn[-1] != cyc[0]:
            return False
        if len(cyc) < 2 or cyc[-1] != cyc[0]:
            return False
        if any(a == b for w in (conn, cyc) for a, b in zip(w, w[1:])):
            return False
    return True


def boundary_ok(fs: FiniteStructure, _o: Oracle) -> bool:
    used: dict[tuple[int, int], int] = {}
    for cyc in cycles(fs):
        if len(cyc) != 4 or len(set(cyc[:3])) != 3:
            return False
        for a, b in zip(cyc, cyc[1:]):
            used[(a, b)] = used.get((a, b), 0) + 1
    want = {(a, b) for a in range(4) for b in range(4) if a != b}
    return set(used) == want and all(k == 1 for k in used.values())


def walk_product(fs: FiniteStructure, conn: list[int], cyc: list[int]) -> Perm:
    ls, n = links(fs), len(fs.elements("label"))
    walk = conn + cyc[1:] + list(reversed(conn))[1:]
    out = list(range(n))
    for a, b in zip(walk, walk[1:]):
        t = ls.get((a, b)) if a < b else (_inverse(ls[(b, a)]) if (b, a) in ls else None)
        out = _then(out, t if t is not None else [-1] * n)
    return out


def faces_match(fs: FiniteStructure, _o: Oracle) -> bool:
    if not links(fs):
        return True
    return all(v == walk_product(fs, c, y) for c, y, v in zip(connectors(fs), cycles(fs), values(fs)))


def closure(fs: FiniteStructure) -> Perm:
    out = list(range(len(fs.elements("label"))))
    for _, v in sorted(zip(places(fs), values(fs))):
        out = _then(out, v)
    return out


def closed(fs: FiniteStructure, _o: Oracle) -> bool:
    return closure(fs) == list(range(len(fs.elements("label"))))


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"closure": closure(fs), "values": values(fs)}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, LEAN_CLAUSES, verdicts, "closed")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    corner, label, face, slot = e.form("corner"), e.form("label"), e.form("face"), e.form("slot")
    joins, runs, sends, link = e.form("joins"), e.form("runs"), e.form("sends"), e.form("link")
    return Compiled(
        (
            Total("sends_given", ((face, ("f",)), (label, ("x",))), ((sends, ("f", "x", "y")),)),
            Functional("one_send", sends, 2),
            Functional("one_join", joins, 2),
            Functional("one_run", runs, 2),
            Functional("one_link", link, 3),
            Closure("joins_typed", ((joins, ("f", "i", "v")),), ((face, ("f",)), (slot, ("i",)), (corner, ("v",)))),
            Closure("runs_typed", ((runs, ("f", "i", "v")),), ((face, ("f",)), (slot, ("i",)), (corner, ("v",)))),
            Closure("links_typed", ((link, ("u", "v", "x", "y")),),
                    ((corner, ("u",)), (corner, ("v",)), (label, ("x",)), (label, ("y",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("walks_ok", walks_ok), ("boundary_ok", boundary_ok),
            ("faces_match", faces_match), ("closed", closed))),
    )


LEAN_DEFS = (
    "abbrev Perm := List Nat",
    "",
    "/-- Apply `p`, then `q`. -/",
    "def andThen (p q : Perm) : Perm := p.map fun x => q.getD x 0",
    "",
    "def inverse (p : Perm) : Perm := (List.range p.length).map fun y => p.idxOf y",
    "",
    "def walksOk (conns cycs : List (List Nat)) : Bool :=",
    "  (conns.zip cycs).all fun w =>",
    "    let c := w.1",
    "    let y := w.2",
    "    !c.isEmpty && c.headD 9 == 0 && !y.isEmpty && c.getLastD 9 == y.headD 8 && 2 <= y.length &&",
    "      y.getLastD 9 == y.headD 8 &&",
    "      (List.range (c.length - 1)).all (fun i => c.getD i 0 != c.getD (i + 1) 0) &&",
    "      (List.range (y.length - 1)).all (fun i => y.getD i 0 != y.getD (i + 1) 0)",
    "",
    "def steps (y : List Nat) : List (Prod Nat Nat) := (List.range (y.length - 1)).map fun i => (y.getD i 0, y.getD (i + 1) 0)",
    "",
    "def boundaryOk (cycs : List (List Nat)) : Bool :=",
    "  let used := cycs.flatMap steps",
    "  cycs.all (fun y => y.length == 4 && y.getD 0 0 != y.getD 1 0 && y.getD 1 0 != y.getD 2 0 &&",
    "    y.getD 0 0 != y.getD 2 0) &&",
    "  (List.range 4).all fun a => (List.range 4).all fun b => a == b || used.count (a, b) == 1",
    "",
    "/-- Transports on the edges `u < v`, keyed by the pair. -/",
    "def linkOf (ls : List (Prod (Prod Nat Nat) Perm)) (a b : Nat) : Perm :=",
    "  if a < b then ((ls.find? fun l => l.1 == (a, b)).map (fun l => l.2)).getD []",
    "  else inverse (((ls.find? fun l => l.1 == (b, a)).map (fun l => l.2)).getD [])",
    "",
    "def walkProduct (n : Nat) (ls : List (Prod (Prod Nat Nat) Perm)) (c y : List Nat) : Perm :=",
    "  let w := c ++ y.drop 1 ++ (c.reverse.drop 1)",
    "  (steps w).foldl (fun acc s => andThen acc (linkOf ls s.1 s.2)) (List.range n)",
    "",
    "def facesMatch (n : Nat) (ls : List (Prod (Prod Nat Nat) Perm)) (conns cycs : List (List Nat))",
    "    (vals : List Perm) : Bool :=",
    "  ls.isEmpty || (List.range vals.length).all fun i =>",
    "    decide (vals.getD i [] = walkProduct n ls (conns.getD i []) (cycs.getD i []))",
    "",
    "def insertBy (k : Nat -> Nat) (x : Nat) : List Nat -> List Nat",
    "  | [] => [x]",
    "  | y :: ys => if k x <= k y then x :: y :: ys else y :: insertBy k x ys",
    "",
    "/-- The values multiplied in the order of their places. -/",
    "def closedIn (n : Nat) (places : List Nat) (vals : List Perm) : Bool :=",
    "  let order := (List.range places.length).foldr (insertBy fun i => places.getD i 0) []",
    "  decide (order.foldl (fun acc i => andThen acc (vals.getD i [])) (List.range n) = List.range n)",
    "",
)
LEAN_CALLS = {"walks_ok": "walksOk conns_{f} cycs_{f}", "boundary_ok": "boundaryOk cycs_{f}",
              "faces_match": "facesMatch n_{f} links_{f} conns_{f} cycs_{f} vals_{f}",
              "closed": "closedIn n_{f} places_{f} vals_{f}"}


def _nats(xs: Sequence[int]) -> str:
    return lean_list([str(x) for x in xs])


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    assert -1 not in places(fs)
    return [("n", "Nat", str(len(fs.elements("label")))),
            ("conns", "List (List Nat)", lean_list([_nats(c) for c in connectors(fs)])),
            ("cycs", "List (List Nat)", lean_list([_nats(c) for c in cycles(fs)])),
            ("vals", "List Perm", lean_list([_nats(v) for v in values(fs)])),
            ("links", "List (Prod (Prod Nat Nat) Perm)",
             lean_list([f"(({u}, {v}), {_nats(p)})" for (u, v), p in sorted(links(fs).items())])),
            ("places", "List Nat", _nats(places(fs)))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `closed_faces`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
