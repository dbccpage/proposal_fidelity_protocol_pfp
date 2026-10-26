"""Exact two-end bounds on quantities, and straight-line steps whose claimed
result bounds must enclose the exact result bound of their operands and
have ends on a declared grid.

The claim: quantities (inputs first, then step results, in declared order),
values, ``bound(q, lo, hi)`` (the bound of ``q``: given for an input,
claimed for a step), ``add(q, a, b)``, ``sub(q, a, b)``, ``mul(q, a, b)`` and
``div(q, a, b)`` (step ``q`` applies the operation to ``a`` and ``b``) and
``grid(g)`` (claimed ends have denominators dividing ``g``).

Relational clauses, carried by derivability over the hosted claim:
``bounds_given`` (every quantity has a bound: an approximation with no bound
is refused), ``one_bound``, ``grid_given`` and ``one_grid``.

Decoded clauses, decided over exact values outside the grammar:
``bounds_ordered`` (no bound is empty), ``divisors_clear`` (a divisor's
bound excludes zero), ``enclosed`` (each step's claimed bound contains the
exact bound computed from the operands' bounds: rounding inward, or to the
nearest grid point, fails) and ``on_grid`` (each step's claimed ends lie on
the grid).  Later steps use the claimed bounds of earlier ones.  Their Lean
certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from engine.encoding import Encoding
from engine.exact.q import ONE, ZERO, Q, fmt_q
from engine.kinds import Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "outward_bounds"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "OutwardBounds"
EXACT = ("py.exact.q",)
CLAUSES = ("bounds_ordered", "divisors_clear", "enclosed", "on_grid")
OPS = ("add", "sub", "mul", "div")
Bound = tuple[Q, Q]


def bounds(fs: FiniteStructure) -> list[Bound | None]:
    got: dict[int, Bound] = {}
    for q, lo, hi in rows(fs, "bound"):
        a, b = fs.value(lo), fs.value(hi)
        if a is not None and b is not None:
            got[q] = (a, b)
    return [got.get(q) for q in fs.elements("quantity")]


def steps(fs: FiniteStructure) -> list[tuple[int, str, int, int]]:
    """(result, operation, first operand, second operand), by positions."""
    out = []
    for op in OPS:
        for q, a, b in rows(fs, op):
            i, j, k = position(fs, "quantity", q), position(fs, "quantity", a), position(fs, "quantity", b)
            if i is not None and j is not None and k is not None:
                out.append((i, op, j, k))
    return sorted(out)


def grid(fs: FiniteStructure) -> Q | None:
    got = rows(fs, "grid")
    return fs.value(got[0][0]) if len(got) == 1 else None


def exact(op: str, a: Bound, b: Bound) -> Bound:
    if op == "add":
        return (a[0] + b[0], a[1] + b[1])
    if op == "sub":
        return (a[0] - b[1], a[1] - b[0])
    if op == "div":
        b = (ONE / b[1], ONE / b[0])
    products = [x * y for x in a for y in b]
    return (min(products), max(products))


def bounds_ordered(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(b is not None and b[0] <= b[1] for b in bounds(fs))


def _clear(b: Bound | None) -> bool:
    return b is not None and not (b[0] <= ZERO <= b[1])


def divisors_clear(fs: FiniteStructure, _o: Oracle) -> bool:
    bs = bounds(fs)
    return all(op != "div" or _clear(bs[k]) for _, op, _, k in steps(fs))


def enclosed(fs: FiniteStructure, _o: Oracle) -> bool:
    bs = bounds(fs)
    for q, op, a, b in steps(fs):
        ba, bb, bq = bs[a], bs[b], bs[q]
        if ba is None or bb is None or bq is None or (op == "div" and not _clear(bb)):
            return False
        lo, hi = exact(op, ba, bb)
        if not (bq[0] <= lo and hi <= bq[1]):
            return False
    return True


def on_grid(fs: FiniteStructure, _o: Oracle) -> bool:
    g, bs = grid(fs), bounds(fs)
    if g is None or g.den != 1 or g.num < 1:
        return False
    return all((b := bs[q]) is not None and all(g.num % end.den == 0 for end in b) for q, _, _, _ in steps(fs))


def describe(fs: FiniteStructure) -> dict[str, object]:
    bs = bounds(fs)
    out: dict[str, object] = {}
    for q, op, a, b in steps(fs):
        ba, bb = bs[a], bs[b]
        if ba is not None and bb is not None and (op != "div" or _clear(bb)):
            lo, hi = exact(op, ba, bb)
            out[str(q)] = [fmt_q(lo), fmt_q(hi)]
    return {"exact": out}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "enclosed")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    quantity, bound, grid_f = e.form("quantity"), e.form("bound"), e.form("grid")
    return Compiled(
        (
            Total("bounds_given", ((quantity, ("q",)),), ((bound, ("q", "lo", "hi")),)),
            Functional("one_bound", bound, 1),
            Total("grid_given", (), ((grid_f, ("g",)),)),
            Functional("one_grid", grid_f, 0),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("bounds_ordered", bounds_ordered), ("divisors_clear", divisors_clear), ("enclosed", enclosed),
            ("on_grid", on_grid))),
    )


LEAN_DEFS = (
    "/-- A bound: two exact ends, each as a numerator and a denominator. -/",
    "abbrev End := Prod Int Nat",
    "",
    "def val (e : End) : QN := QN.ofPair e.1 e.2",
    "",
    "def le (x y : QN) : Bool := !QN.pos (x - y)",
    "",
    "def qmin (x y : QN) : QN := if le x y then x else y",
    "",
    "def qmax (x y : QN) : QN := if le x y then y else x",
    "",
    "/-- The exact result bound of a step: operation 0 add, 1 sub, 2 mul, 3 div. -/",
    "def exact (op : Nat) (a b : Prod QN QN) : Prod QN QN :=",
    "  if op == 0 then (a.1 + b.1, a.2 + b.2)",
    "  else if op == 1 then (a.1 - b.2, a.2 - b.1)",
    "  else",
    "    let b := if op == 3 then (1 / b.2, 1 / b.1) else b",
    "    let ps := [a.1 * b.1, a.1 * b.2, a.2 * b.1, a.2 * b.2]",
    "    (ps.foldl qmin (a.1 * b.1), ps.foldl qmax (a.1 * b.1))",
    "",
    "def bnd (bs : List (Prod End End)) (k : Nat) : Prod QN QN :=",
    "  let e := bs.getD k ((0, 1), (0, 1))",
    "  (val e.1, val e.2)",
    "",
    "/-- A step: result, operation, first operand, second operand. -/",
    "abbrev Step := Prod Nat (Prod Nat (Prod Nat Nat))",
    "",
    "def boundsOrdered (bs : List (Prod End End)) : Bool := bs.all fun e => le (val e.1) (val e.2)",
    "",
    "def clear (b : Prod QN QN) : Bool := !(le b.1 0 && le 0 b.2)",
    "",
    "def divisorsClear (bs : List (Prod End End)) (ss : List Step) : Bool :=",
    "  ss.all fun s => s.2.1 != 3 || clear (bnd bs s.2.2.2)",
    "",
    "def enclosed (bs : List (Prod End End)) (ss : List Step) : Bool :=",
    "  ss.all fun s =>",
    "    let x := exact s.2.1 (bnd bs s.2.2.1) (bnd bs s.2.2.2)",
    "    (s.2.1 != 3 || clear (bnd bs s.2.2.2)) && le (bnd bs s.1).1 x.1 && le x.2 (bnd bs s.1).2",
    "",
    "/-- Each step's claimed ends have denominators dividing the grid (ends are in lowest terms). -/",
    "def onGrid (g : Nat) (bs : List (Prod End End)) (ss : List Step) : Bool :=",
    "  ss.all fun s => let e := bs.getD s.1 ((0, 1), (0, 1)); g % e.1.2 == 0 && g % e.2.2 == 0",
    "",
)
LEAN_CALLS = {"bounds_ordered": "boundsOrdered bounds_{f}", "divisors_clear": "divisorsClear bounds_{f} steps_{f}",
              "enclosed": "enclosed bounds_{f} steps_{f}", "on_grid": "onGrid grid_{f} bounds_{f} steps_{f}"}


def _end(x: Q) -> str:
    return f"({x.num}, {x.den})"


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    bs, g = bounds(fs), grid(fs)
    assert g is not None and all(b is not None for b in bs)
    return [("bounds", "List (Prod End End)", lean_list([f"({_end(b[0])}, {_end(b[1])})" for b in bs if b is not None])),
            ("steps", "List Step", lean_list([f"({q}, ({OPS.index(op)}, ({a}, {b})))" for q, op, a, b in steps(fs)])),
            ("grid", "Nat", str(g.num))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clauses of `outward_bounds`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)

