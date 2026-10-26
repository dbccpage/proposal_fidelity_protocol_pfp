# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Links between corners carry transports of a finite label set; a face is a
walk of steps, each along or against a link, and its claimed product is the
ordered product of the transports around it.

The claim: labels, corners, links and steps (each in declared order: the
steps are the face's walk, in order), ``from(e, v)`` and ``to(e, v)`` (the
ends of link ``e``), ``moves(e, x, y)`` (link ``e`` takes label ``x`` to
``y``), ``along(w, e)`` or ``against(w, e)`` (step ``w`` reads link ``e``
forward, or backward through its inverse) and ``product(x, y)`` (the claimed
product takes ``x`` to ``y``).

Relational clauses, carried by derivability over the hosted claim:
``ends_given``, ``one_from``, ``one_to``, ``moves_given``, ``one_move`` and
``claim_given`` and ``one_claim`` (the claimed product is a map on the
labels).

Decoded clauses, decided outside the grammar: ``links_permute`` (each
transport is a permutation of the labels), ``walk_closed`` (every step reads
exactly one link, consecutive steps meet, and the walk ends where it starts:
an open walk is not a face) and ``ordered_product`` (the claimed product is
the product of the step transports in walk order; with three labels it is
not a function of the unordered set of links).  Their Lean certificates are
re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "face_products"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "FaceProducts"
EXACT: tuple[str, ...] = ()
CLAUSES = ("links_permute", "walk_closed", "ordered_product")


def links(fs: FiniteStructure) -> list[tuple[int, int, list[int]]]:
    """Each link as (from, to, images), by positions; a missing image is -1."""
    out = []
    labels = fs.elements("label")
    for e in fs.elements("link"):
        src = [position(fs, "corner", v) for ee, v in rows(fs, "from") if ee == e]
        tgt = [position(fs, "corner", v) for ee, v in rows(fs, "to") if ee == e]
        img = {position(fs, "label", x): position(fs, "label", y) for ee, x, y in rows(fs, "moves") if ee == e}
        out.append((src[0] if src and src[0] is not None else -1, tgt[0] if tgt and tgt[0] is not None else -1,
                    [v if (v := img.get(k)) is not None else -1 for k in range(len(labels))]))
    return out


def steps(fs: FiniteStructure) -> list[list[tuple[int, bool]]]:
    """Each step's readings: (link, forward), by positions."""
    out = []
    for w in fs.elements("step"):
        got = [(position(fs, "link", e), True) for ww, e in rows(fs, "along") if ww == w]
        got += [(position(fs, "link", e), False) for ww, e in rows(fs, "against") if ww == w]
        out.append([(k, f) for k, f in got if k is not None])
    return out


def claimed(fs: FiniteStructure) -> list[int]:
    img = {position(fs, "label", x): position(fs, "label", y) for x, y in rows(fs, "product")}
    return [v if (v := img.get(k)) is not None else -1 for k in range(len(fs.elements("label")))]


def _inverse(p: list[int]) -> list[int]:
    out = [-1] * len(p)
    for x, y in enumerate(p):
        if 0 <= y < len(p):
            out[y] = x
    return out


def links_permute(fs: FiniteStructure, _o: Oracle) -> bool:
    n = len(fs.elements("label"))
    return all(sorted(img) == list(range(n)) for _, _, img in links(fs))


def walk_closed(fs: FiniteStructure, _o: Oracle) -> bool:
    ls, ws = links(fs), steps(fs)
    if not ws or any(len(w) != 1 for w in ws):
        return False
    ends = [(ls[k][0], ls[k][1]) if fwd else (ls[k][1], ls[k][0]) for (k, fwd), in ws]
    return all(a[1] == b[0] for a, b in zip(ends, ends[1:])) and ends[-1][1] == ends[0][0]


def ordered(fs: FiniteStructure) -> list[int]:
    ls = links(fs)
    out = list(range(len(fs.elements("label"))))
    for w in steps(fs):
        for k, fwd in w:
            t = ls[k][2] if fwd else _inverse(ls[k][2])
            out = [t[x] if 0 <= x < len(t) else -1 for x in out]
    return out


def ordered_product(fs: FiniteStructure, _o: Oracle) -> bool:
    return claimed(fs) == ordered(fs)


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"ordered_product": ordered(fs)}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "walk_closed")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    label, link = e.form("label"), e.form("link")
    frm, to, moves, product = e.form("from"), e.form("to"), e.form("moves"), e.form("product")
    return Compiled(
        (
            Total("ends_given", ((link, ("e",)),), ((frm, ("e", "u")), (to, ("e", "v")))),
            Functional("one_from", frm, 1),
            Functional("one_to", to, 1),
            Total("moves_given", ((link, ("e",)), (label, ("x",))), ((moves, ("e", "x", "y")),)),
            Functional("one_move", moves, 2),
            Total("claim_given", ((label, ("x",)),), ((product, ("x", "y")),)),
            Functional("one_claim", product, 1),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("links_permute", links_permute), ("walk_closed", walk_closed), ("ordered_product", ordered_product))),
    )


LEAN_DEFS = (
    "/-- A link: its two ends and the images of the labels. -/",
    "abbrev Link := Prod (Prod Nat Nat) (List Nat)",
    "",
    "def isPerm (n : Nat) (p : List Nat) : Bool := p.length == n && (List.range n).all (fun x => p.count x == 1)",
    "",
    "def linksPermute (n : Nat) (ls : List Link) : Bool := ls.all fun l => isPerm n l.2",
    "",
    "/-- The inverse of a permutation of `0, ..., n - 1`. -/",
    "def inverse (p : List Nat) : List Nat := (List.range p.length).map fun y => p.idxOf y",
    "",
    "def ends (ls : List Link) (s : Prod Nat Bool) : Prod Nat Nat :=",
    "  let e := (ls.getD s.1 ((0, 0), [])).1",
    "  if s.2 then e else (e.2, e.1)",
    "",
    "/-- Consecutive steps meet and the walk ends where it starts. -/",
    "def walkClosed (ls : List Link) (ws : List (List (Prod Nat Bool))) : Bool :=",
    "  ws.all (fun w => w.length == 1) && !ws.isEmpty &&",
    "    (let es := ws.map (fun w => ends ls (w.headD (0, true)))",
    "     (List.range (es.length - 1)).all (fun i => (es.getD i (0, 0)).2 == (es.getD (i + 1) (0, 0)).1) &&",
    "       (es.getLastD (0, 0)).2 == (es.headD (0, 0)).1)",
    "",
    "/-- The product of the step transports in walk order. -/",
    "def ordered (n : Nat) (ls : List Link) (ws : List (List (Prod Nat Bool))) : List Nat :=",
    "  ws.foldl (fun acc w => w.foldl (fun acc s =>",
    "    let t := (ls.getD s.1 ((0, 0), [])).2",
    "    let t := if s.2 then t else inverse t",
    "    acc.map (fun x => t.getD x n)) acc) (List.range n)",
    "",
    "def orderedProduct (n : Nat) (ls : List Link) (ws : List (List (Prod Nat Bool))) (c : List Nat) : Bool :=",
    "  decide (ordered n ls ws = c)",
    "",
)
LEAN_CALLS = {"links_permute": "linksPermute n_{f} links_{f}", "walk_closed": "walkClosed links_{f} steps_{f}",
              "ordered_product": "orderedProduct n_{f} links_{f} steps_{f} claimed_{f}"}


def _nats(xs: Sequence[int]) -> str:
    return lean_list([str(x) for x in xs])


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    ls, ws = links(fs), steps(fs)
    assert all(x >= 0 for s, t, img in ls for x in [s, t] + img) and all(x >= 0 for x in claimed(fs))
    return [("n", "Nat", str(len(fs.elements("label")))),
            ("links", "List Link", lean_list([f"(({s}, {t}), {_nats(img)})" for s, t, img in ls])),
            ("steps", "List (List (Prod Nat Bool))",
             lean_list([lean_list([f"({k}, {'true' if f else 'false'})" for k, f in w]) for w in ws])),
            ("claimed", "List Nat", _nats(claimed(fs)))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `face_products`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
