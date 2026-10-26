"""A hosted cell on five corners carries squared side lengths whose form is
positive, and quarter turns of three axes; a loop of turns closes exactly
when its ordered product is the identity.  A summary that forgets the order
(the signed count of each turn) does not decide closure.

The cell: five corners, a squared length for each pair of corners taken in
the declared order (``span(u, v, x)`` with ``u`` before ``v``), and a hinge
(``hinge``: three corners).  The form is based at the first corner:
``G[i][j] = (d(0,i) + d(0,j) - d(i,j)) / 2``; it must have positive leading
minors.

The turns: each turn sends every axis to one axis (``image(g, a, b)``), with
a sign (``flips(g, a)``: the image is negated).  A fourth axis, fixed by
every turn, completes each turn to a four by four table; each turn must be a
rotation (its table is orthogonal with determinant one).

The loops: ``single(g)`` is the loop of the one turn ``g``; ``bracket(g, h)``
is the loop ``g, h, g back, h back``.  ``single_shut`` and ``bracket_shut``
declare a loop closed; a loop not so declared is declared open.  The ordered
product of a loop multiplies the tables in its order (a turn taken back is
its transpose).

Relational clauses, carried by derivability: ``spans_typed``, ``one_span``,
``image_given``, ``one_image``, ``image_typed``, ``flips_typed``,
``hinge_typed``, ``single_typed``, ``loops_typed``, ``shut_is_loop``,
``single_shut_is_loop``.

Decoded clauses, decided over exact values outside the grammar:
``gram_positive``, ``turns_rotate``, ``ordered_closure`` (a loop declared
closed has the identity as its ordered product) and ``open_stays_open`` (a
loop declared open does not).  Their Lean certificates are re-decided by the
kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from engine.encoding import Encoding
from engine.exact.linalg import det, first_nonpositive_minor, leading_minors
from engine.exact.q import ONE, ZERO, Q, fmt_q
from engine.kinds import Closure, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure

CHALLENGE_ID = "loop_products"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "LoopProducts"
EXACT = ("py.exact.q", "py.exact.linalg")
CLAUSES = ("gram_positive", "turns_rotate", "ordered_closure", "open_stays_open")
Table = tuple[tuple[Q, ...], ...]


def _rows(fs: FiniteStructure, name: str) -> list[tuple[int, ...]]:
    return [a for n, a in fs.tuples if n == name]


def lengths(fs: FiniteStructure) -> dict[tuple[int, int], Q] | None:
    """Squared lengths by pair of corner positions; ``None`` unless every pair
    in the declared order has exactly one exact value and nothing else is given."""
    corners = fs.elements("corner")
    got: dict[tuple[int, int], Q] = {}
    for u, v, x in _rows(fs, "span"):
        val = fs.value(x)
        if u not in corners or v not in corners or val is None:
            return None
        key = (corners.index(u), corners.index(v))
        if key in got or key[0] >= key[1]:
            return None
        got[key] = val
    n = len(corners)
    return got if set(got) == {(i, j) for i in range(n) for j in range(i + 1, n)} else None


def gram(fs: FiniteStructure) -> list[list[Q]] | None:
    d = lengths(fs)
    if d is None:
        return None
    n = len(fs.elements("corner"))

    def sq(i: int, j: int) -> Q:
        return ZERO if i == j else d[(min(i, j), max(i, j))]

    two = Q(2)
    return [[(sq(0, i) + sq(0, j) - sq(i, j)) / two for j in range(1, n)] for i in range(1, n)]


def turn_table(fs: FiniteStructure, g: int) -> Table:
    """The four by four table of a turn: column ``a`` is the image of axis
    ``a`` (negated when flipped); the fourth axis is fixed."""
    axes = fs.elements("axis")
    flips = {a for gg, a in _rows(fs, "flips") if gg == g}
    m = [[ZERO] * 4 for _ in range(4)]
    for gg, a, b in _rows(fs, "image"):
        if gg == g and a in axes and b in axes:
            m[axes.index(b)][axes.index(a)] = -ONE if a in flips else ONE
    m[3][3] = ONE
    return tuple(tuple(r) for r in m)


def mul(a: Table, b: Table) -> Table:
    return tuple(tuple(sum((a[i][t] * b[t][j] for t in range(4)), ZERO) for j in range(4)) for i in range(4))


def transpose(a: Table) -> Table:
    return tuple(tuple(a[j][i] for j in range(4)) for i in range(4))


IDENTITY: Table = tuple(tuple(ONE if i == j else ZERO for j in range(4)) for i in range(4))


def loops(fs: FiniteStructure) -> list[tuple[str, list[tuple[int, bool]], bool]]:
    """(name, word, declared closed) per loop; a word lists (turn, taken back)."""
    shut_single = {g for (g,) in _rows(fs, "single_shut")}
    shut_bracket = set(_rows(fs, "bracket_shut"))
    out = [(f"single:{g}", [(g, False)], g in shut_single) for (g,) in _rows(fs, "single")]
    out += [(f"bracket:{g}:{h}", [(g, False), (h, False), (g, True), (h, True)], (g, h) in shut_bracket)
            for g, h in _rows(fs, "bracket")]
    return out


def product(fs: FiniteStructure, word: list[tuple[int, bool]]) -> Table:
    out = IDENTITY
    for g, back in word:
        t = turn_table(fs, g)
        out = mul(out, transpose(t) if back else t)
    return out


def gram_positive(fs: FiniteStructure, _o: Oracle) -> bool:
    g = gram(fs)
    return g is not None and first_nonpositive_minor(g) is None


def turns_rotate(fs: FiniteStructure, _o: Oracle) -> bool:
    for g in fs.elements("turn"):
        t = turn_table(fs, g)
        if mul(t, transpose(t)) != IDENTITY or det([list(r) for r in t]) != ONE:
            return False
    return True


def ordered_closure(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(product(fs, word) == IDENTITY for _, word, shut in loops(fs) if shut)


def open_stays_open(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(product(fs, word) != IDENTITY for _, word, shut in loops(fs) if not shut)


def describe(fs: FiniteStructure) -> dict[str, object]:
    g = gram(fs)
    return {
        "leading_minors": None if g is None else [fmt_q(x) for x in leading_minors(g)],
        "loops": {name: {"declared_closed": shut, "ordered_product_is_identity": product(fs, word) == IDENTITY,
                         "signed_count": {str(t): sum((-1 if b else 1) for tt, b in word if tt == t)
                                          for t in sorted({t for t, _ in word})}}
                  for name, word, shut in loops(fs)},
    }


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    out = []
    for v in verdicts:
        if dict(v.decoded).get("gram_positive") in ("PASS", "FAIL"):
            out += [(f"{LEAN_MODULE}.{v.fid}_{c}", v.fid, c) for c in CLAUSES]
    return out


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    corner, length, axis, turn = e.form("corner"), e.form("len"), e.form("axis"), e.form("turn")
    span, hinge, image, flips = e.form("span"), e.form("hinge"), e.form("image"), e.form("flips")
    single, bracket = e.form("single"), e.form("bracket")
    single_shut, bracket_shut = e.form("single_shut"), e.form("bracket_shut")
    return Compiled(
        (
            Closure("spans_typed", ((span, ("u", "v", "x")),),
                    ((corner, ("u",)), (corner, ("v",)), (length, ("x",)))),
            Functional("one_span", span, 2),
            Total("image_given", ((turn, ("g",)), (axis, ("a",))), ((image, ("g", "a", "b")),)),
            Functional("one_image", image, 2),
            Closure("image_typed", ((image, ("g", "a", "b")),), ((turn, ("g",)), (axis, ("a",)), (axis, ("b",)))),
            Closure("flips_typed", ((flips, ("g", "a")),), ((turn, ("g",)), (axis, ("a",)))),
            Closure("hinge_typed", ((hinge, ("c",)),), ((corner, ("c",)),)),
            Closure("single_typed", ((single, ("g",)),), ((turn, ("g",)),)),
            Closure("loops_typed", ((bracket, ("g", "h")),), ((turn, ("g",)), (turn, ("h",)))),
            Closure("shut_is_loop", ((bracket_shut, ("g", "h")),), ((bracket, ("g", "h")),)),
            Closure("single_shut_is_loop", ((single_shut, ("g",)),), ((single, ("g",)),)),
        ),
        decoded=tuple(DecodedClause(c, f, EXACT) for c, f in (
            ("gram_positive", gram_positive), ("turns_rotate", turns_rotate),
            ("ordered_closure", ordered_closure), ("open_stays_open", open_stays_open))),
    )


LEAN_DEFS = (
    "/-- Entry `(i, j)` of a table. -/",
    "def entry (a : Mat) (i j : Nat) : QN := (a.getD i []).getD j 0",
    "",
    "/-- The form of a table of squared lengths, based at the first corner. -/",
    "def form (d : Mat) : Mat :=",
    "  (List.range (d.length - 1)).map fun i =>",
    "    (List.range (d.length - 1)).map fun j =>",
    "      (entry d 0 (i + 1) + entry d 0 (j + 1) - entry d (i + 1) (j + 1)) * QN.ofPair 1 2",
    "",
    "def gramPositive (d : Mat) : Bool := minorsPositive (form d)",
    "",
    "def mul4 (a b : Mat) : Mat :=",
    "  (List.range 4).map fun i => (List.range 4).map fun j =>",
    "    (List.range 4).foldl (fun acc t => acc + entry a i t * entry b t j) 0",
    "",
    "def tr4 (a : Mat) : Mat := (List.range 4).map fun i => (List.range 4).map fun j => entry a j i",
    "",
    "def id4 : Mat := (List.range 4).map fun i => (List.range 4).map fun j => if i = j then 1 else 0",
    "",
    "/-- Each table is orthogonal with determinant one. -/",
    "def turnsRotate (ts : List Mat) : Bool := ts.all fun t => decide (mul4 t (tr4 t) = id4) && decide (det t = 1)",
    "",
    "/-- The ordered product of a word: a turn taken back is its transpose. -/",
    "def product (ts : List Mat) (w : List (Prod Nat Bool)) : Mat :=",
    "  w.foldl (fun acc s => mul4 acc (if s.2 then tr4 (ts.getD s.1 []) else ts.getD s.1 [])) id4",
    "",
    "/-- Every loop declared closed has the identity as its ordered product. -/",
    "def orderedClosure (ts : List Mat) (ls : List (Prod (List (Prod Nat Bool)) Bool)) : Bool :=",
    "  ls.all fun l => !l.2 || decide (product ts l.1 = id4)",
    "",
    "/-- No loop declared open has the identity as its ordered product. -/",
    "def openStaysOpen (ts : List Mat) (ls : List (Prod (List (Prod Nat Bool)) Bool)) : Bool :=",
    "  ls.all fun l => l.2 || !decide (product ts l.1 = id4)",
    "",
)
LEAN_CALLS = {"gram_positive": "gramPositive lengths_{f}", "turns_rotate": "turnsRotate turns_{f}",
              "ordered_closure": "orderedClosure turns_{f} loops_{f}",
              "open_stays_open": "openStaysOpen turns_{f} loops_{f}"}


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    """One cell with its turns and loops per evaluated fixture; the kernel
    re-decides each value clause."""
    from engine import lean_text as T

    by = {f.fid: f for f in fixtures}
    lines = T.header(LEAN_MODULE, "The value clauses of `loop_products`, decided by the kernel", LEAN_DEFS)
    certs = lean_certificates(verdicts)
    fids = sorted({fid for _, fid, _ in certs}, key=[v.fid for v in verdicts].index)
    for fid in fids:
        fs = by[fid].structure
        d = lengths(fs)
        assert d is not None
        n = len(fs.elements("corner"))
        table = [[ZERO if i == j else d[(min(i, j), max(i, j))] for j in range(n)] for i in range(n)]
        turns = fs.elements("turn")
        words = []
        for _, word, shut in loops(fs):
            steps = ", ".join(f"({turns.index(g)}, {'true' if back else 'false'})" for g, back in word)
            words.append(f"([{steps}], {'true' if shut else 'false'})")
        lines += [f"def lengths_{fid} : Mat :=", f"  {T.mat(table)}", "",
                  f"def turns_{fid} : List Mat :=",
                  "  [" + ",\n   ".join(T.mat(turn_table(fs, g)) for g in turns) + "]", "",
                  f"def loops_{fid} : List (Prod (List (Prod Nat Bool)) Bool) :=",
                  "  [" + ", ".join(words) + "]", ""]
    for name, fid, clause in certs:
        verdict = "true" if dict(next(v for v in verdicts if v.fid == fid).decoded)[clause] == "PASS" else "false"
        lines += [f"theorem {name.split('.', 1)[1]} : {LEAN_CALLS[clause].format(f=fid)} = {verdict} := by decide", ""]
    lines += [f"end {LEAN_MODULE}", ""]
    return "\n".join(lines)
