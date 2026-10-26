# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Links between corners carry transports of a finite label set; a walk's
composite is the transports taken in walk order; a change of labels at
every corner moves each transport at both of its ends, and the walk's
composite at its two end corners.

The claim: labels, corners, links and strides (the walk's steps, in declared
order), ``from(e, v)``, ``to(e, v)``, ``moves(e, x, y)`` (link ``e`` takes
``x`` to ``y``), ``walks(w, e)`` (stride ``w`` goes along link ``e``),
``composite(x, y)`` (the claimed composite), ``regauge(v, x, y)`` (the
change of labels at corner ``v``), ``moved(e, x, y)`` (the claimed changed
transport of link ``e``) and ``recomposite(x, y)`` (the claimed changed
composite).

Relational clauses, carried by derivability over the hosted claim:
``ends_given``, ``one_from``, ``one_to``, ``moves_given``, ``one_move``,
``strides_given``, ``one_stride``, ``regauge_given``, ``one_regauge``,
``moved_given``, ``one_moved``, ``composite_given`` and
``recomposite_given``.

Decoded clauses, decided outside the grammar: ``walk_meets`` (consecutive
strides meet), ``composite_exact`` (the claimed composite is the product of
the transports in walk order), ``both_ends`` (each changed transport is the
old transport with the change undone at its first end and applied at its
second: a change applied at one end only is refused) and ``covariance``
(the changed composite is the composite with the change undone at the
walk's first corner and applied at its last).  Their Lean certificates are
re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Req, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "walk_transport"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "WalkTransport"
EXACT: tuple[str, ...] = ()
CLAUSES = ("walk_meets", "composite_exact", "both_ends", "covariance")


def _map(fs: FiniteStructure, name: str, owner: int | None = None) -> list[int]:
    """A label map as its list of images (a missing image is -1)."""
    n = len(fs.elements("label"))
    got: dict[int, int] = {}
    for args in rows(fs, name):
        if owner is not None and args[0] != owner:
            continue
        x, y = position(fs, "label", args[-2]), position(fs, "label", args[-1])
        if x is not None and y is not None:
            got[x] = y
    return [got.get(k, -1) for k in range(n)]


def _end(fs: FiniteStructure, name: str, e: int) -> int:
    got = [position(fs, "corner", v) for ee, v in rows(fs, name) if ee == e]
    return got[0] if got and got[0] is not None else -1


def then(p: list[int], q: list[int]) -> list[int]:
    """First ``p``, then ``q``."""
    return [q[x] if 0 <= x < len(q) else -1 for x in p]


def inverse(p: list[int]) -> list[int]:
    out = [-1] * len(p)
    for x, y in enumerate(p):
        if 0 <= y < len(p):
            out[y] = x
    return out


def walk(fs: FiniteStructure) -> list[int]:
    out = []
    for w in fs.elements("stride"):
        got = [position(fs, "link", e) for ww, e in rows(fs, "walks") if ww == w]
        out.append(got[0] if got and got[0] is not None else -1)
    return out


def along(fs: FiniteStructure) -> list[int]:
    links = fs.elements("link")
    out = list(range(len(fs.elements("label"))))
    for k in walk(fs):
        out = then(out, _map(fs, "moves", links[k]) if 0 <= k < len(links) else [])
    return out


def walk_meets(fs: FiniteStructure, _o: Oracle) -> bool:
    links = fs.elements("link")
    ks = walk(fs)
    if not ks or any(k < 0 for k in ks):
        return False
    return all(_end(fs, "to", links[a]) == _end(fs, "from", links[b]) for a, b in zip(ks, ks[1:]))


def composite_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    return _map(fs, "composite") == along(fs)


def _change(fs: FiniteStructure, v: int) -> list[int]:
    corners = fs.elements("corner")
    return _map(fs, "regauge", corners[v]) if 0 <= v < len(corners) else []


def both_ends(fs: FiniteStructure, _o: Oracle) -> bool:
    for e in fs.elements("link"):
        want = then(then(inverse(_change(fs, _end(fs, "from", e))), _map(fs, "moves", e)), _change(fs, _end(fs, "to", e)))
        if _map(fs, "moved", e) != want:
            return False
    return True


def covariance(fs: FiniteStructure, _o: Oracle) -> bool:
    links, ks = fs.elements("link"), walk(fs)
    if not ks or any(k < 0 for k in ks):
        return False
    start, end = _end(fs, "from", links[ks[0]]), _end(fs, "to", links[ks[-1]])
    want = then(then(inverse(_change(fs, start)), along(fs)), _change(fs, end))
    return _map(fs, "recomposite") == want


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"along": along(fs)}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "composite_exact")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    label, corner, link, stride = e.form("label"), e.form("corner"), e.form("link"), e.form("stride")
    reqs: list[Req] = [
        Total("ends_given", ((link, ("e",)),), ((e.form("from"), ("e", "u")), (e.form("to"), ("e", "v")))),
        Functional("one_from", e.form("from"), 1),
        Functional("one_to", e.form("to"), 1),
        Total("strides_given", ((stride, ("w",)),), ((e.form("walks"), ("w", "e")),)),
        Functional("one_stride", e.form("walks"), 1),
    ]
    for name, owner in (("moves", link), ("regauge", corner), ("moved", link)):
        reqs += [Total(f"{name}_given", ((owner, ("o",)), (label, ("x",))), ((e.form(name), ("o", "x", "y")),)),
                 Functional(f"one_{name}", e.form(name), 2)]
    for name in ("composite", "recomposite"):
        reqs.append(Total(f"{name}_given", ((label, ("x",)),), ((e.form(name), ("x", "y")),)))
    return Compiled(tuple(reqs), decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
        ("walk_meets", walk_meets), ("composite_exact", composite_exact), ("both_ends", both_ends),
        ("covariance", covariance))))


LEAN_DEFS = (
    "/-- A link: its two ends and the images of the labels. -/",
    "abbrev Link := Prod (Prod Nat Nat) (List Nat)",
    "",
    "/-- First `p`, then `q`. -/",
    "def andThen (p q : List Nat) : List Nat := p.map fun x => q.getD x q.length",
    "",
    "def inverse (p : List Nat) : List Nat := (List.range p.length).map fun y => p.idxOf y",
    "",
    "def link (ls : List Link) (k : Nat) : Link := ls.getD k ((0, 0), [])",
    "",
    "def walkMeets (ls : List Link) (ws : List Nat) : Bool :=",
    "  !ws.isEmpty && (List.range (ws.length - 1)).all fun i =>",
    "    (link ls (ws.getD i 0)).1.2 == (link ls (ws.getD (i + 1) 0)).1.1",
    "",
    "def along (n : Nat) (ls : List Link) (ws : List Nat) : List Nat :=",
    "  ws.foldl (fun acc k => andThen acc (link ls k).2) (List.range n)",
    "",
    "def compositeExact (n : Nat) (ls : List Link) (ws c : List Nat) : Bool := decide (along n ls ws = c)",
    "",
    "/-- Each changed transport is the change undone at its first end and applied at its second. -/",
    "def bothEnds (ls : List Link) (gs : List (List Nat)) (ms : List (List Nat)) : Bool :=",
    "  (List.range ls.length).all fun k =>",
    "    let l := link ls k",
    "    decide (ms.getD k [] = andThen (andThen (inverse (gs.getD l.1.1 [])) l.2) (gs.getD l.1.2 []))",
    "",
    "def covariance (n : Nat) (ls : List Link) (ws : List Nat) (gs : List (List Nat)) (rc : List Nat) : Bool :=",
    "  let s := (link ls (ws.headD 0)).1.1",
    "  let t := (link ls (ws.getLastD 0)).1.2",
    "  decide (rc = andThen (andThen (inverse (gs.getD s [])) (along n ls ws)) (gs.getD t []))",
    "",
)
LEAN_CALLS = {"walk_meets": "walkMeets links_{f} walk_{f}",
              "composite_exact": "compositeExact n_{f} links_{f} walk_{f} composite_{f}",
              "both_ends": "bothEnds links_{f} regauge_{f} moved_{f}",
              "covariance": "covariance n_{f} links_{f} walk_{f} regauge_{f} recomposite_{f}"}


def _nats(xs: Sequence[int]) -> str:
    assert all(x >= 0 for x in xs)
    return lean_list([str(x) for x in xs])


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    links, corners = fs.elements("link"), fs.elements("corner")
    ls = [f"(({_end(fs, 'from', e)}, {_end(fs, 'to', e)}), {_nats(_map(fs, 'moves', e))})" for e in links]
    return [("n", "Nat", str(len(fs.elements("label")))), ("links", "List Link", lean_list(ls)),
            ("walk", "List Nat", _nats(walk(fs))), ("composite", "List Nat", _nats(_map(fs, "composite"))),
            ("regauge", "List (List Nat)", lean_list([_nats(_map(fs, "regauge", v)) for v in corners])),
            ("moved", "List (List Nat)", lean_list([_nats(_map(fs, "moved", e)) for e in links])),
            ("recomposite", "List Nat", _nats(_map(fs, "recomposite")))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `walk_transport`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
