"""A closed surface of triangular patches with exact squared edge lengths,
and its claimed deficit at every corner hinge and claimed total: every
angle is read exactly from a cosine table, every deficit is one turn less
the angles at its corner, recomputed from the patches that contain the
corner, and the total is the sum of the deficits.

The claim: corners, patches, edges and one total (each in declared order),
each corner carrying its claimed deficit (in turns), each edge its squared
length and the total its claimed sum as values, ``spans(t, a, b, c)``
(patch ``t`` spans corners ``a``, ``b``, ``c``), ``ends(e, u, v)`` (edge
``e`` joins corners ``u`` and ``v``) and ``uses(v, t)`` (corner ``v``'s
term is assembled from patch ``t``).

Relational clauses, carried by derivability over the hosted claim:
``spans_given``, ``one_span``, ``ends_given``, ``one_ends``, ``uses_given``
and ``uses_typed``.

Decoded clauses, decided outside the grammar: ``well_formed`` (every patch
spans three distinct corners; every side of every patch is exactly one
edge, of positive length, and each edge lies on exactly two patches: the
surface is closed), ``nondegenerate`` (each patch's value ``2(ab + bc + ca)
- (a^2 + b^2 + c^2)`` over its squared sides is positive), ``angles_exact``
(each angle is in the table: ``b + c - a = 0`` is a quarter turn, and
``(b + c - a)^2 = bc`` is a sixth of a turn when ``b + c - a > 0`` and a
third when it is negative; no square root is taken), ``incidence`` (each
corner's term uses exactly the patches that contain it: the refused case is
a term built from a patch without the hinge), ``deficits`` (each claimed
deficit is one less the angles at the corner) and ``total`` (the claimed
total is the sum of the recomputed deficits).  Every hinge is checked: the
claim is over the finite family of corners.  All but ``well_formed`` are
re-decided by the kernel over exact rationals.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from engine import lean_text as T
from engine.encoding import Encoding
from engine.exact.q import ONE, ZERO, Q, fmt_q
from engine.kinds import Closure, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "hinge_deficits"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "HingeDeficits"
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "nondegenerate", "angles_exact", "incidence", "deficits", "total")
LEAN_CLAUSES = CLAUSES[1:]
QUARTER, SIXTH, THIRD = Q(1, 4), Q(1, 6), Q(1, 3)


def _c(fs: FiniteStructure, e: int) -> int:
    k = position(fs, "corner", e)
    return -1 if k is None else k


def patches(fs: FiniteStructure) -> list[tuple[int, int, int]]:
    got = {t: (_c(fs, a), _c(fs, b), _c(fs, c)) for t, a, b, c in rows(fs, "spans")}
    return [got.get(t, (-1, -1, -1)) for t in fs.elements("patch")]


def lengths(fs: FiniteStructure) -> dict[tuple[int, int], list[Q | None]]:
    out: dict[tuple[int, int], list[Q | None]] = {}
    for e, u, v in rows(fs, "ends"):
        a, b = _c(fs, u), _c(fs, v)
        out.setdefault((min(a, b), max(a, b)), []).append(fs.value(e))
    return out


def side(fs: FiniteStructure, a: int, b: int) -> Q:
    got = lengths(fs).get((min(a, b), max(a, b)), [])
    return got[0] if len(got) == 1 and got[0] is not None else ZERO


def angle(opposite: Q, left: Q, right: Q) -> Q | None:
    """Turns of the angle between sides of squared lengths ``left`` and
    ``right``, opposite ``opposite``, from the exact table; None off it."""
    num = left + right - opposite
    if num.is_zero():
        return QUARTER
    if num * num == left * right:
        return SIXTH if num.sign() > 0 else THIRD
    return None


def corner_angles(fs: FiniteStructure) -> dict[tuple[int, int], Q | None]:
    """(patch, corner) to the angle there."""
    out: dict[tuple[int, int], Q | None] = {}
    for k, t in enumerate(patches(fs)):
        for i in range(3):
            v, p, q = t[i], t[(i + 1) % 3], t[(i + 2) % 3]
            out[(k, v)] = angle(side(fs, p, q), side(fs, v, p), side(fs, v, q))
    return out


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    ps, ls = patches(fs), lengths(fs)
    if any(len(set(t)) != 3 or -1 in t for t in ps) or any(-1 in k for k in ls):
        return False
    sides = [(min(t[i], t[j]), max(t[i], t[j])) for t in ps for i, j in ((0, 1), (0, 2), (1, 2))]
    if set(sides) != set(ls) or any(sides.count(s) != 2 for s in set(sides)):
        return False
    if any(len(v) != 1 or v[0] is None or v[0].sign() <= 0 for v in ls.values()):
        return False
    return all(fs.value(e) is not None for e in fs.elements("corner") + fs.elements("total"))


def cm(a: Q, b: Q, c: Q) -> Q:
    return Q(2, 1) * (a * b + b * c + c * a) - (a * a + b * b + c * c)


def nondegenerate(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(cm(side(fs, t[0], t[1]), side(fs, t[0], t[2]), side(fs, t[1], t[2])).sign() > 0
               for t in patches(fs))


def angles_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(x is not None for x in corner_angles(fs).values())


def uses(fs: FiniteStructure) -> list[list[int]]:
    out: list[list[int]] = [[] for _ in fs.elements("corner")]
    for v, t in rows(fs, "uses"):
        i, k = position(fs, "corner", v), position(fs, "patch", t)
        if i is not None:
            out[i].append(-1 if k is None else k)
    return [sorted(x) for x in out]


def incidence(fs: FiniteStructure, _o: Oracle) -> bool:
    ps = patches(fs)
    return all(u == [k for k, t in enumerate(ps) if v in t] for v, u in enumerate(uses(fs)))


def recomputed(fs: FiniteStructure) -> list[Q | None]:
    ang, ps = corner_angles(fs), patches(fs)
    out: list[Q | None] = []
    for v in range(len(fs.elements("corner"))):
        got = [ang.get((k, v)) for k, t in enumerate(ps) if v in t]
        out.append(None if any(x is None for x in got) else ONE - sum((x for x in got if x is not None), ZERO))
    return out


def deficits(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(r is not None and fs.value(c) == r for c, r in zip(fs.elements("corner"), recomputed(fs)))


def total(fs: FiniteStructure, _o: Oracle) -> bool:
    rs, ts = recomputed(fs), fs.elements("total")
    return (len(ts) == 1 and all(r is not None for r in rs)
            and fs.value(ts[0]) == sum((r for r in rs if r is not None), ZERO))


def describe(fs: FiniteStructure) -> dict[str, object]:
    rs = recomputed(fs)
    return {"deficits": [None if r is None else fmt_q(r) for r in rs],
            "total": None if None in rs else fmt_q(sum((r for r in rs if r is not None), ZERO))}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, LEAN_CLAUSES, verdicts, "deficits")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    corner, patch, edge = e.form("corner"), e.form("patch"), e.form("edge")
    spans, ends, use = e.form("spans"), e.form("ends"), e.form("uses")
    return Compiled(
        (
            Total("spans_given", ((patch, ("t",)),), ((spans, ("t", "a", "b", "c")),)),
            Functional("one_span", spans, 1),
            Total("ends_given", ((edge, ("e",)),), ((ends, ("e", "u", "v")),)),
            Functional("one_ends", ends, 1),
            Total("uses_given", ((corner, ("v",)),), ((use, ("v", "t")),)),
            Closure("uses_typed", ((use, ("v", "t")),), ((corner, ("v",)), (patch, ("t",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("nondegenerate", nondegenerate), ("angles_exact", angles_exact),
            ("incidence", incidence), ("deficits", deficits), ("total", total))),
    )


LEAN_DEFS = (
    "/-- The squared length of the side `a b`, from the edge table. -/",
    "def side (ls : List (Prod (Prod Nat Nat) QN)) (a b : Nat) : QN :=",
    "  ((ls.find? fun l => l.1 == (min a b, max a b)).map (fun l => l.2)).getD 0",
    "",
    "/-- Turns of the angle between sides `l` and `r`, opposite `o`, from the exact table. -/",
    "def angle (o l r : QN) : Option QN :=",
    "  let num := l + r - o",
    "  if num = 0 then some (QN.ofPair 1 4)",
    "  else if num * num = l * r then (if 0 < num then some (QN.ofPair 1 6) else some (QN.ofPair 1 3))",
    "  else none",
    "",
    "def cm (a b c : QN) : QN := 2 * (a * b + b * c + c * a) - (a * a + b * b + c * c)",
    "",
    "def nondegenerate (ps : List (List Nat)) (ls : List (Prod (Prod Nat Nat) QN)) : Bool :=",
    "  ps.all fun t => decide (0 < cm (side ls (t.getD 0 0) (t.getD 1 0)) (side ls (t.getD 0 0) (t.getD 2 0))",
    "    (side ls (t.getD 1 0) (t.getD 2 0)))",
    "",
    "/-- The angle of patch `t` at its `i`-th corner. -/",
    "def angleAt (ls : List (Prod (Prod Nat Nat) QN)) (t : List Nat) (i : Nat) : Option QN :=",
    "  let v := t.getD i 0",
    "  let p := t.getD ((i + 1) % 3) 0",
    "  let q := t.getD ((i + 2) % 3) 0",
    "  angle (side ls p q) (side ls v p) (side ls v q)",
    "",
    "def anglesExact (ps : List (List Nat)) (ls : List (Prod (Prod Nat Nat) QN)) : Bool :=",
    "  ps.all fun t => (List.range 3).all fun i => (angleAt ls t i).isSome",
    "",
    "def incidence (n : Nat) (ps : List (List Nat)) (us : List (List Nat)) : Bool :=",
    "  (List.range n).all fun v => decide (us.getD v [] = (List.range ps.length).filter fun k => (ps.getD k []).contains v)",
    "",
    "/-- One turn less the angles at corner `v`, over the patches containing it. -/",
    "def deficit (ps : List (List Nat)) (ls : List (Prod (Prod Nat Nat) QN)) (v : Nat) : Option QN :=",
    "  ps.foldl (fun acc t => match acc with",
    "    | none => none",
    "    | some s => if t.contains v then (angleAt ls t (t.idxOf v)).map (fun a => s - a) else some s) (some 1)",
    "",
    "def deficits (ps : List (List Nat)) (ls : List (Prod (Prod Nat Nat) QN)) (claimed : List QN) : Bool :=",
    "  (List.range claimed.length).all fun v => decide (deficit ps ls v = some (claimed.getD v 0))",
    "",
    "def total (ps : List (List Nat)) (ls : List (Prod (Prod Nat Nat) QN)) (n : Nat) (t : QN) : Bool :=",
    "  match (List.range n).foldl (fun acc v => match acc, deficit ps ls v with",
    "    | some s, some d => some (s + d)",
    "    | _, _ => none) (some 0) with",
    "  | some s => decide (s = t)",
    "  | none => false",
    "",
)
LEAN_CALLS = {"nondegenerate": "nondegenerate patches_{f} sides_{f}",
              "angles_exact": "anglesExact patches_{f} sides_{f}",
              "incidence": "incidence ncorners_{f} patches_{f} uses_{f}",
              "deficits": "deficits patches_{f} sides_{f} claimed_{f}",
              "total": "total patches_{f} sides_{f} ncorners_{f} claimedTotal_{f}"}


def _nats(xs: Sequence[int]) -> str:
    return lean_list([str(x) for x in xs])


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    ls = lengths(fs)
    vals = [fs.value(c) for c in fs.elements("corner")]
    tv = fs.value(fs.elements("total")[0])
    assert all(v is not None for v in vals) and tv is not None and all(len(v) == 1 and v[0] for v in ls.values())
    return [("ncorners", "Nat", str(len(vals))),
            ("patches", "List (List Nat)", lean_list([_nats(t) for t in patches(fs)])),
            ("sides", "List (Prod (Prod Nat Nat) QN)",
             lean_list([f"(({a}, {b}), {T.q(v[0])})" for (a, b), v in sorted(ls.items()) if v[0] is not None])),
            ("uses", "List (List Nat)", lean_list([_nats(u) for u in uses(fs)])),
            ("claimed", "List QN", lean_list([T.q(v) for v in vals if v is not None])),
            ("claimedTotal", "QN", T.q(tv))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `hinge_deficits`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
