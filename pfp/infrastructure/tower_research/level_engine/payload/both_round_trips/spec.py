# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Two graded step systems over the rationals, a map each way between them,
and a declared lift on each side: both round trips must return to the
identity through their lifts.

The claim: degrees (each carrying its number), source and target units (the
basis of each side), numbers (exact values), ``next(m, n)`` (degree ``n``
follows degree ``m``), ``source_in(x, n)`` and ``target_in(y, n)`` (a unit
lies in a degree), and six coefficient tables, one entry for each pair of
units they relate: ``source_step(x, y, c)`` and ``target_step(x, y, c)``
(the step from a unit to a unit one degree lower), ``there(x, y, c)`` (the
map from a source unit to a target unit of the same degree), ``back(y, x,
c)`` (the map from a target unit to a source unit of the same degree), and
``source_lift(x, z, c)`` and ``target_lift(y, w, c)`` (the lift from a unit
to a unit one degree higher on the same side).  Units of a degree are read
in declared order; degrees in the order of their numbers.

Relational clauses, carried by derivability over the hosted claim: every
unit is placed in one degree; every table has exactly one entry for each
pair of units it relates, and no entry for any other pair.

Decoded clauses, decided over exact values outside the grammar:

* ``degrees_in_line``: the degree numbers, in declared order, are 0, 1, ...
  and ``next`` holds exactly for consecutive degrees;
* ``steps_square_zero``: on each side, a step followed by a step is zero;
* ``maps_commute``: both maps commute with the steps;
* ``source_return``: on the source, back after there, minus the identity,
  is step after lift plus lift after step in every degree;
* ``target_return``: the same on the target for there after back (the
  refused case: a round trip that returns on one side only).

The lifts are declared, never searched for.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.linalg import rank
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO, Q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Req, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import rows

CHALLENGE_ID = "both_round_trips"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q",)
CLAUSES = ("degrees_in_line", "steps_square_zero", "maps_commute", "source_return", "target_return")
SIDES = ("source", "target")

# A table: (rows, columns, entries by row).
Table = tuple[int, int, tuple[tuple[Q, ...], ...]]


def _nat(x: Q | None) -> int | None:
    return x.num if x is not None and x.den == 1 and x.num >= 0 else None


def degrees(fs: FiniteStructure) -> list[int] | None:
    """The degree elements in the order of their numbers; ``None`` when a
    number is missing, not a natural, or repeated."""
    got: list[tuple[int, int]] = []
    for d in fs.elements("degree"):
        n = _nat(fs.value(d))
        if n is None:
            return None
        got.append((n, d))
    if len({n for n, _ in got}) != len(got):
        return None
    return [d for _, d in sorted(got)]


def layers(fs: FiniteStructure, side: str) -> list[list[int]] | None:
    """Each degree's units on one side, in declared order; ``None`` when a
    unit is not placed in exactly one degree."""
    order = degrees(fs)
    if order is None:
        return None
    place: dict[int, list[int]] = {}
    for x, n in rows(fs, f"{side}_in"):
        place.setdefault(x, []).append(n)
    out: list[list[int]] = [[] for _ in order]
    for x in fs.elements(side):
        at = place.get(x, [])
        if len(at) != 1 or at[0] not in order:
            return None
        out[order.index(at[0])].append(x)
    return out


def table(fs: FiniteStructure, name: str, cols: Sequence[int], rws: Sequence[int]) -> Table | None:
    """The entries of ``name(col, row, c)`` as a table, rows by columns;
    ``None`` when an entry is missing, repeated or carries no value."""
    got: dict[tuple[int, int], Q] = {}
    for x, y, c in rows(fs, name):
        v = fs.value(c)
        if (x, y) in got or v is None:
            return None
        got[(x, y)] = v
    if any((x, y) not in got for x in cols for y in rws):
        return None
    return (len(rws), len(cols), tuple(tuple(got[(x, y)] for x in cols) for y in rws))


def mul(a: Table, b: Table) -> Table:
    ra, inner, ea = a
    _, cb, eb = b
    return (ra, cb, tuple(tuple(sum((ea[i][t] * eb[t][j] for t in range(inner)), ZERO) for j in range(cb))
                          for i in range(ra)))


def add(a: Table, b: Table) -> Table:
    return (a[0], a[1], tuple(tuple(x + y for x, y in zip(r, s)) for r, s in zip(a[2], b[2])))


def unit_less(a: Table) -> Table:
    """The table minus the identity."""
    return (a[0], a[1], tuple(tuple(x - (ONE if i == j else ZERO) for j, x in enumerate(r))
                              for i, r in enumerate(a[2])))


def zero(r: int, c: int) -> Table:
    return (r, c, tuple(tuple(ZERO for _ in range(c)) for _ in range(r)))


class Reading:
    """Every table the clauses read, by degree; built only when every
    entry is there."""

    def __init__(self, src: list[list[int]], tgt: list[list[int]], steps: dict[str, list[Table]],
                 there: list[Table], back: list[Table], lifts: dict[str, list[Table]]) -> None:
        self.layers = {"source": src, "target": tgt}
        self.steps, self.there, self.back, self.lifts = steps, there, back, lifts


def reading(fs: FiniteStructure) -> Reading | None:
    src, tgt = layers(fs, "source"), layers(fs, "target")
    if src is None or tgt is None:
        return None
    top = len(src) - 1
    steps: dict[str, list[Table]] = {}
    lifts: dict[str, list[Table]] = {}
    for side, ls in (("source", src), ("target", tgt)):
        st = [table(fs, f"{side}_step", ls[i + 1], ls[i]) for i in range(top)]
        li = [table(fs, f"{side}_lift", ls[i], ls[i + 1]) for i in range(top)]
        if any(t is None for t in st + li):
            return None
        steps[side] = [t for t in st if t is not None]
        lifts[side] = [t for t in li if t is not None]
    there = [table(fs, "there", src[i], tgt[i]) for i in range(top + 1)]
    back = [table(fs, "back", tgt[i], src[i]) for i in range(top + 1)]
    if any(t is None for t in there + back):
        return None
    return Reading(src, tgt, steps, [t for t in there if t is not None], [t for t in back if t is not None], lifts)


def degrees_in_line(fs: FiniteStructure, _o: Oracle) -> bool:
    els = fs.elements("degree")
    if [_nat(fs.value(d)) for d in els] != list(range(len(els))):
        return False
    return set(rows(fs, "next")) == {(els[i], els[i + 1]) for i in range(len(els) - 1)}


def _square_zero(r: Reading) -> bool:
    for side in SIDES:
        d, ls = r.steps[side], r.layers[side]
        for i in range(1, len(d)):
            if mul(d[i - 1], d[i]) != zero(len(ls[i - 1]), len(ls[i + 1])):
                return False
    return True


def steps_square_zero(fs: FiniteStructure, _o: Oracle) -> bool:
    r = reading(fs)
    return r is not None and _square_zero(r)


def maps_commute(fs: FiniteStructure, _o: Oracle) -> bool:
    r = reading(fs)
    if r is None:
        return False
    ds, dt = r.steps["source"], r.steps["target"]
    for i in range(1, len(r.there)):
        if mul(dt[i - 1], r.there[i]) != mul(r.there[i - 1], ds[i - 1]):
            return False
        if mul(ds[i - 1], r.back[i]) != mul(r.back[i - 1], dt[i - 1]):
            return False
    return True


def _returns(r: Reading, side: str) -> bool:
    """Round trip minus the identity is step after lift plus lift after
    step, in every degree of ``side``."""
    first, then = (r.there, r.back) if side == "source" else (r.back, r.there)
    d, h, ls = r.steps[side], r.lifts[side], r.layers[side]
    top = len(ls) - 1
    for i in range(top + 1):
        n = len(ls[i])
        total = zero(n, n)
        if i < top:
            total = add(total, mul(d[i], h[i]))
        if i > 0:
            total = add(total, mul(h[i - 1], d[i - 1]))
        if unit_less(mul(then[i], first[i])) != total:
            return False
    return True


def source_return(fs: FiniteStructure, _o: Oracle) -> bool:
    r = reading(fs)
    return r is not None and _returns(r, "source")


def target_return(fs: FiniteStructure, _o: Oracle) -> bool:
    """The refused case: a round trip that returns on the source only."""
    r = reading(fs)
    return r is not None and _returns(r, "target")


def describe(fs: FiniteStructure) -> dict[str, object]:
    """What each side keeps in each degree: units, less the rank of the step
    out, less the rank of the step in (read only where steps square to
    zero)."""
    r = reading(fs)
    if r is None or not _square_zero(r):
        return {"kept": None}
    out: dict[str, list[int]] = {}
    for side in SIDES:
        d, ls = r.steps[side], r.layers[side]
        top = len(ls) - 1
        out[side] = [len(ls[i]) - (rank(d[i - 1][2]) if i > 0 else 0) - (rank(d[i][2]) if i < top else 0)
                     for i in range(top + 1)]
    return {"kept": out}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    deg, num, nxt = e.form("degree"), e.form("number"), e.form("next")
    src, tgt = e.form("source"), e.form("target")
    s_in, t_in = e.form("source_in"), e.form("target_in")
    s_step, t_step = e.form("source_step"), e.form("target_step")
    there, back = e.form("there"), e.form("back")
    s_lift, t_lift = e.form("source_lift"), e.form("target_lift")
    reqs: list[Req] = [
        Total("source_placed", ((src, ("x",)),), ((s_in, ("x", "n")), (deg, ("n",)))),
        Functional("one_source_place", s_in, 1),
        Total("target_placed", ((tgt, ("x",)),), ((t_in, ("x", "n")), (deg, ("n",)))),
        Functional("one_target_place", t_in, 1),
    ]
    for side, place, step, lift in (("source", s_in, s_step, s_lift), ("target", t_in, t_step, t_lift)):
        reqs += [
            Total(f"{side}_steps_given", ((place, ("x", "n")), (nxt, ("m", "n")), (place, ("y", "m"))),
                  ((step, ("x", "y", "c")), (num, ("c",)))),
            Functional(f"one_{side}_step", step, 2),
            Total(f"{side}_steps_graded", ((step, ("x", "y", "c")),),
                  ((place, ("x", "n")), (nxt, ("m", "n")), (place, ("y", "m")), (num, ("c",)))),
            Total(f"{side}_lifts_given", ((place, ("x", "m")), (nxt, ("m", "n")), (place, ("z", "n"))),
                  ((lift, ("x", "z", "c")), (num, ("c",)))),
            Functional(f"one_{side}_lift", lift, 2),
            Total(f"{side}_lifts_graded", ((lift, ("x", "z", "c")),),
                  ((place, ("x", "m")), (nxt, ("m", "n")), (place, ("z", "n")), (num, ("c",)))),
        ]
    for name, rel, a, b in (("there", there, s_in, t_in), ("back", back, t_in, s_in)):
        reqs += [
            Total(f"{name}_given", ((a, ("x", "n")), (b, ("y", "n"))), ((rel, ("x", "y", "c")), (num, ("c",)))),
            Functional(f"one_{name}", rel, 2),
            Total(f"{name}_graded", ((rel, ("x", "y", "c")),), ((a, ("x", "n")), (b, ("y", "n")), (num, ("c",)))),
        ]
    return Compiled(
        tuple(reqs),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("degrees_in_line", degrees_in_line), ("steps_square_zero", steps_square_zero),
            ("maps_commute", maps_commute), ("source_return", source_return), ("target_return", target_return))),
    )
