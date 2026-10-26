# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A closed complex of triangular patches over the two-element field, an
operation from edge cochains to patch cochains given by a quadratic formula,
declared test cochains and declared self-maps: the operation's value class
must not depend on the chosen representative, and must commute with the
maps.

The claim: corners, patches, test cochains and maps (each in declared
order), ``spans(t, a, b, c)`` (patch ``t`` spans corners ``a``, ``b``,
``c``), ``term(t, a, b, c, d)`` (the formula adds, at patch ``t``, the
product of the cochain's values on the edges ``ab`` and ``cd``),
``constant(t)`` (the formula adds one at patch ``t``), ``carries(k, a, b)``
(test cochain ``k`` is one on edge ``ab``) and ``sends(m, a, b)`` (map ``m``
sends corner ``a`` to ``b``).  An edge is an unordered pair of corners of
one patch.

Relational clauses, carried by derivability over the hosted claim:
``spans_given``, ``one_span``, ``sends_given``, ``one_image``,
``carries_typed``, ``terms_typed`` and ``constant_typed``.

Decoded clauses, decided outside the grammar: ``complex_ok`` (each patch
spans three distinct corners, no two patches the same, every corner used,
every named edge an edge of a patch, and each map sends each patch onto a
corner, an edge or a patch), ``test_cocycles`` (each test cochain has zero
coboundary), ``class_kept`` (for every test cochain ``a`` and every corner
cochain ``f`` (all of them), the operation's values at ``a + df`` and at
``a`` differ by a coboundary: the refused case is an operation whose class
moves with the representative) and ``natural`` (for every map ``g`` and test
cochain ``a``, the operation of the pulled-back cochain and the pull-back of
the operation's value differ by a coboundary).  Coboundaries are decided by
exact elimination over the two-element field.  Their Lean certificates are
re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "class_operations"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "ClassOperations"
EXACT: tuple[str, ...] = ()
CLAUSES = ("complex_ok", "test_cocycles", "class_kept", "natural")
LEAN_CLAUSES = ("test_cocycles", "class_kept", "natural")
Edge = tuple[int, int]


def _c(fs: FiniteStructure, e: int) -> int:
    k = position(fs, "corner", e)
    return -1 if k is None else k


def patches(fs: FiniteStructure) -> list[tuple[int, int, int]]:
    """Each patch's corners by position, ascending; (-1, -1, -1) when unspanned."""
    got = {t: tuple(sorted((_c(fs, a), _c(fs, b), _c(fs, c)))) for t, a, b, c in rows(fs, "spans")}
    return [got.get(t, (-1, -1, -1)) for t in fs.elements("patch")]  # type: ignore[misc]


def edges(fs: FiniteStructure) -> list[Edge]:
    return sorted({(t[i], t[j]) for t in patches(fs) if -1 not in t for i in range(3) for j in range(i + 1, 3)})


def _edge(a: int, b: int) -> Edge:
    return (min(a, b), max(a, b))


def terms(fs: FiniteStructure) -> list[tuple[int, Edge, Edge]]:
    out = []
    for t, a, b, c, d in rows(fs, "term"):
        k = position(fs, "patch", t)
        out.append((-1 if k is None else k, _edge(_c(fs, a), _c(fs, b)), _edge(_c(fs, c), _c(fs, d))))
    return sorted(out)


def constant(fs: FiniteStructure) -> list[int]:
    return sorted(k for (t,) in rows(fs, "constant") if (k := position(fs, "patch", t)) is not None)


def tests(fs: FiniteStructure) -> list[list[Edge]]:
    out: list[list[Edge]] = [[] for _ in fs.elements("cochain")]
    for k, a, b in rows(fs, "carries"):
        i = position(fs, "cochain", k)
        if i is not None:
            out[i].append(_edge(_c(fs, a), _c(fs, b)))
    return [sorted(x) for x in out]


def maps(fs: FiniteStructure) -> list[list[int]]:
    n = len(fs.elements("corner"))
    out = []
    for m in fs.elements("map"):
        img = {_c(fs, a): _c(fs, b) for mm, a, b in rows(fs, "sends") if mm == m}
        out.append([img.get(v, -1) for v in range(n)])
    return out


class Field2:
    """The operation, coboundaries and pull-backs over the two-element field,
    cochains as bit masks (edge ``i`` is bit ``i``; patch ``t`` is bit ``t``)."""

    def __init__(self, fs: FiniteStructure) -> None:
        self.n = len(fs.elements("corner"))
        self.patches = patches(fs)
        self.edges = edges(fs)
        self.index = {e: i for i, e in enumerate(self.edges)}
        self.faces = [[self.index.get(_edge(t[i], t[j]), -1) for i, j in ((0, 1), (0, 2), (1, 2))]
                      for t in self.patches]
        self.terms = [(t, self.index.get(e1, -1), self.index.get(e2, -1)) for t, e1, e2 in terms(fs)]
        self.constant = sum(1 << t for t in constant(fs) if t >= 0)
        self.basis: dict[int, int] = {}
        for i in range(len(self.edges)):
            v = self.reduce(self.delta1(1 << i))
            if v:
                self.basis[v.bit_length() - 1] = v

    def delta1(self, a: int) -> int:
        return sum(1 << t for t, f in enumerate(self.faces) if sum(a >> e & 1 for e in f if e >= 0) % 2)

    def delta0(self, f: int) -> int:
        return sum(1 << i for i, (u, v) in enumerate(self.edges) if (f >> u & 1) != (f >> v & 1))

    def op(self, a: int) -> int:
        out = self.constant
        for t, e1, e2 in self.terms:
            if t >= 0 and e1 >= 0 and e2 >= 0 and a >> e1 & 1 and a >> e2 & 1:
                out ^= 1 << t
        return out

    def reduce(self, v: int) -> int:
        while v:
            top = v.bit_length() - 1
            if top not in self.basis:
                return v
            v ^= self.basis[top]
        return 0

    def mask(self, support: list[Edge]) -> int:
        return sum(1 << self.index[e] for e in support if e in self.index)

    def pull1(self, g: list[int], a: int) -> int:
        out = 0
        for i, (u, v) in enumerate(self.edges):
            img = _edge(g[u], g[v])
            if img[0] != img[1] and img in self.index and a >> self.index[img] & 1:
                out |= 1 << i
        return out

    def pull2(self, g: list[int], c: int) -> int:
        where = {t: k for k, t in enumerate(self.patches)}
        out = 0
        for k, t in enumerate(self.patches):
            img = tuple(sorted({g[v] for v in t}))
            if len(img) == 3 and img in where and c >> where[img] & 1:
                out |= 1 << k
        return out


def complex_ok(fs: FiniteStructure, _o: Oracle) -> bool:
    ps = patches(fs)
    if any(len(set(t)) != 3 or -1 in t for t in ps) or len(set(ps)) != len(ps):
        return False
    if {v for t in ps for v in t} != set(range(len(fs.elements("corner")))):
        return False
    es = set(edges(fs))
    if any(e1 not in es or e2 not in es or t < 0 for t, e1, e2 in terms(fs)):
        return False
    if any(e not in es for s in tests(fs) for e in s):
        return False
    simplices = {(v,) for t in ps for v in t} | es | set(ps)
    return all(-1 not in g and all(tuple(sorted({g[v] for v in t})) in simplices for t in ps) for g in maps(fs))


def test_cocycles(fs: FiniteStructure, _o: Oracle) -> bool:
    f2 = Field2(fs)
    return all(f2.delta1(f2.mask(s)) == 0 for s in tests(fs))


def class_kept(fs: FiniteStructure, _o: Oracle) -> bool:
    f2 = Field2(fs)
    for s in tests(fs):
        a = f2.mask(s)
        base = f2.op(a)
        if any(f2.reduce(f2.op(a ^ f2.delta0(f)) ^ base) for f in range(1 << f2.n)):
            return False
    return True


def natural(fs: FiniteStructure, _o: Oracle) -> bool:
    f2 = Field2(fs)
    for g in maps(fs):
        if -1 in g:
            return False
        for s in tests(fs):
            a = f2.mask(s)
            if f2.reduce(f2.op(f2.pull1(g, a)) ^ f2.pull2(g, f2.op(a))):
                return False
    return True


def describe(fs: FiniteStructure) -> dict[str, object]:
    f2 = Field2(fs)
    return {"coboundary_rank": len(f2.basis), "edges": len(f2.edges),
            "value_class_nonzero": [f2.reduce(f2.op(f2.mask(s))) != 0 for s in tests(fs)]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, LEAN_CLAUSES, verdicts, "class_kept")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    corner, patch, cochain, mp = e.form("corner"), e.form("patch"), e.form("cochain"), e.form("map")
    spans, term, const = e.form("spans"), e.form("term"), e.form("constant")
    carries, sends = e.form("carries"), e.form("sends")
    return Compiled(
        (
            Total("spans_given", ((patch, ("t",)),), ((spans, ("t", "a", "b", "c")),)),
            Functional("one_span", spans, 1),
            Total("sends_given", ((mp, ("m",)), (corner, ("a",))), ((sends, ("m", "a", "b")),)),
            Functional("one_image", sends, 2),
            Closure("carries_typed", ((carries, ("k", "a", "b")),),
                    ((cochain, ("k",)), (corner, ("a",)), (corner, ("b",)))),
            Closure("terms_typed", ((term, ("t", "a", "b", "c", "d")),),
                    ((patch, ("t",)), (corner, ("a",)), (corner, ("b",)), (corner, ("c",)), (corner, ("d",)))),
            Closure("constant_typed", ((const, ("t",)),), ((patch, ("t",)),)),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("complex_ok", complex_ok), ("test_cocycles", test_cocycles), ("class_kept", class_kept),
            ("natural", natural))),
    )


LEAN_DEFS = (
    "def bit (x i : Nat) : Bool := (x >>> i) % 2 == 1",
    "",
    "/-- The highest set bit below `n`, or `n` when there is none. -/",
    "def topBit (n x : Nat) : Nat := (List.range n).foldl (fun acc i => if bit x i then i else acc) n",
    "",
    "/-- The complex: corners, edges (pairs), and each patch's three edge indices. -/",
    "structure Cx where",
    "  corners : Nat",
    "  edges : List (Prod Nat Nat)",
    "  faces : List (List Nat)",
    "",
    "def delta1 (c : Cx) (a : Nat) : Nat :=",
    "  (List.range c.faces.length).foldl (fun acc t =>",
    "    if ((c.faces.getD t []).filter fun e => bit a e).length % 2 == 1 then acc + 2 ^ t else acc) 0",
    "",
    "def delta0 (c : Cx) (f : Nat) : Nat :=",
    "  (List.range c.edges.length).foldl (fun acc i =>",
    "    let e := c.edges.getD i (0, 0)",
    "    if bit f e.1 != bit f e.2 then acc + 2 ^ i else acc) 0",
    "",
    "/-- The formula: a constant mask and terms (patch, edge, edge). -/",
    "def op (cst : Nat) (ts : List (Prod Nat (Prod Nat Nat))) (a : Nat) : Nat :=",
    "  ts.foldl (fun acc x => if bit a x.2.1 && bit a x.2.2 then acc ^^^ 2 ^ x.1 else acc) cst",
    "",
    "/-- Reduce against a basis keyed by top bit; fuel bounds the steps. -/",
    "def reduceB (w : Nat) (basis : List (Prod Nat Nat)) : Nat -> Nat -> Nat",
    "  | 0, v => v",
    "  | fuel + 1, v => if v == 0 then 0 else",
    "      match basis.find? (fun b => b.1 == topBit w v) with",
    "      | some b => reduceB w basis fuel (v ^^^ b.2)",
    "      | none => v",
    "",
    "/-- A basis of the coboundaries of edge cochains. -/",
    "def basisOf (c : Cx) : List (Prod Nat Nat) :=",
    "  let w := c.faces.length",
    "  (List.range c.edges.length).foldl (fun b i =>",
    "    let v := reduceB w b (w + 1) (delta1 c (2 ^ i))",
    "    if v == 0 then b else (topBit w v, v) :: b) []",
    "",
    "def isCoboundary (c : Cx) (v : Nat) : Bool := reduceB c.faces.length (basisOf c) (c.faces.length + 1) v == 0",
    "",
    "def testCocycles (c : Cx) (tests : List Nat) : Bool := tests.all fun a => delta1 c a == 0",
    "",
    "def classKept (c : Cx) (cst : Nat) (ts : List (Prod Nat (Prod Nat Nat))) (tests : List Nat) : Bool :=",
    "  tests.all fun a => (List.range (2 ^ c.corners)).all fun f =>",
    "    isCoboundary c (op cst ts (a ^^^ delta0 c f) ^^^ op cst ts a)",
    "",
    "def pair (a b : Nat) : Prod Nat Nat := if a <= b then (a, b) else (b, a)",
    "",
    "def pull1 (c : Cx) (g : List Nat) (a : Nat) : Nat :=",
    "  (List.range c.edges.length).foldl (fun acc i =>",
    "    let e := c.edges.getD i (0, 0)",
    "    let img := pair (g.getD e.1 0) (g.getD e.2 0)",
    "    if img.1 != img.2 && c.edges.contains img && bit a (c.edges.idxOf img) then acc + 2 ^ i else acc) 0",
    "",
    "def sort3 (a b c : Nat) : List Nat :=",
    "  let lo := min a (min b c)",
    "  let hi := max a (max b c)",
    "  [lo, a + b + c - lo - hi, hi]",
    "",
    "def pull2 (c : Cx) (ps : List (List Nat)) (g : List Nat) (v : Nat) : Nat :=",
    "  (List.range ps.length).foldl (fun acc k =>",
    "    let t := ps.getD k []",
    "    let img := sort3 (g.getD (t.getD 0 0) 0) (g.getD (t.getD 1 0) 0) (g.getD (t.getD 2 0) 0)",
    "    if img.getD 0 0 != img.getD 1 0 && img.getD 1 0 != img.getD 2 0 && ps.contains img &&",
    "      bit v (ps.idxOf img) then acc + 2 ^ k else acc) 0",
    "",
    "def natural (c : Cx) (ps : List (List Nat)) (cst : Nat) (ts : List (Prod Nat (Prod Nat Nat)))",
    "    (gs : List (List Nat)) (tests : List Nat) : Bool :=",
    "  gs.all fun g => tests.all fun a =>",
    "    isCoboundary c (op cst ts (pull1 c g a) ^^^ pull2 c ps g (op cst ts a))",
    "",
)
LEAN_CALLS = {"test_cocycles": "testCocycles cx_{f} tests_{f}",
              "class_kept": "classKept cx_{f} cst_{f} terms_{f} tests_{f}",
              "natural": "natural cx_{f} patches_{f} cst_{f} terms_{f} maps_{f} tests_{f}"}


def _nats(xs: Sequence[int]) -> str:
    return lean_list([str(x) for x in xs])


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    f2 = Field2(fs)
    assert all(e >= 0 for f in f2.faces for e in f) and all(e1 >= 0 and e2 >= 0 for _, e1, e2 in f2.terms)
    cx = (f"{{ corners := {f2.n}, edges := {lean_list([f'({u}, {v})' for u, v in f2.edges])},\n"
          f"    faces := {lean_list([_nats(f) for f in f2.faces])} }}")
    return [("cx", "Cx", cx),
            ("patches", "List (List Nat)", lean_list([_nats(t) for t in f2.patches])),
            ("cst", "Nat", str(f2.constant)),
            ("terms", "List (Prod Nat (Prod Nat Nat))", lean_list([f"({t}, ({a}, {b}))" for t, a, b in f2.terms])),
            ("maps", "List (List Nat)", lean_list([_nats(g) for g in maps(fs)])),
            ("tests", "List Nat", _nats([f2.mask(s) for s in tests(fs)]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `class_operations`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
