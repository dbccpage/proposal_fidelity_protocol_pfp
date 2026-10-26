"""Replay of sealed evidence: the boundary maps of a complex, computed by the
sealed alternating boundary, compose to zero in every degree; the sealed
signless boundary does not.

The complex is the filled tetrahedron on the points 0 to 3, with every face,
and one more side from 3 to 4 that bounds nothing.  Its cells are listed by
degree, and within a degree in ascending order.  Each boundary map is the
sealed ``bd_n`` (read from the pinned clone), one row per cell of the lower
degree and one column per cell of the higher.  The sealed
``d2_zero_unrestricted`` says every composite of consecutive maps vanishes,
in every degree; the sealed ``signless_countermodel`` says the same cells
with every sign dropped do not.

Clauses, each decided on the replayed sealed facts:

* ``cells_replayed``: the cells are the declared complex, every face present;
* ``chained``: one map per degree above zero, each of the right shape;
* ``composites_zero``: every composite of consecutive declared maps is zero;
* ``boundary_replayed``: every declared map is the sealed signed boundary.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from engine.exact.q import ZERO, Q, fmt_q, parse_q
from engine.level import LevelResult
from engine.replay import Packet, Row, packets as replay_packets, result
from derivation.boundary_cancellation import bd_n, bd_no_sign, facets

CHALLENGE_ID = "boundary_chain"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
LEAN = ("BoundaryCancellation.d2_zero_unrestricted", "BoundaryCancellation.d2_zero_facets",
        "BoundaryCancellation.signless_countermodel")
SOURCES = ("code/derivation/boundary_cancellation.py",)
CLAUSES = ("cells_replayed", "chained", "composites_zero", "boundary_replayed")
TOP: tuple[tuple[int, ...], ...] = ((0, 1, 2, 3), (3, 4))
Cell = tuple[int, ...]


def cells() -> list[Cell]:
    out: set[Cell] = set()
    todo = list(TOP)
    while todo:
        c = todo.pop()
        if c not in out:
            out.add(c)
            if len(c) > 1:
                todo += facets(c)
    return sorted(out, key=lambda c: (len(c), c))


def matrix(boundary: object, lower: list[Cell], upper: list[Cell]) -> list[list[str]]:
    cols = [boundary(c) for c in upper]  # type: ignore[operator]
    return [[fmt_q(Q(sum(k for k, t in col if t == row))) for col in cols] for row in lower]


def maps(boundary: object) -> list[list[list[str]]]:
    cs = cells()
    top = max(len(c) for c in cs) - 1
    by = [[c for c in cs if len(c) == k + 1] for k in range(top + 1)]
    return [matrix(boundary, by[k - 1], by[k]) for k in range(1, top + 1)]


def positive() -> Packet:
    return {"cells": [list(c) for c in cells()], "differentials": maps(bd_n)}


def signless() -> Packet:
    return {"cells": [list(c) for c in cells()], "differentials": maps(bd_no_sign)}


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def _mat(m: object) -> list[list[Q]]:
    assert isinstance(m, list)
    return [[parse_q(x) for x in r] for r in m]


def decide(pk: Packet) -> tuple[str, ...]:
    failed: list[str] = []
    declared_cells = [tuple(c) for c in pk["cells"]]  # type: ignore[attr-defined]
    if declared_cells != cells():
        failed.append("cells_replayed")
    cs = [c for c in declared_cells]
    top = max(len(c) for c in cs) - 1
    by = [[c for c in cs if len(c) == k + 1] for k in range(top + 1)]
    ds = pk["differentials"]
    assert isinstance(ds, list)
    shaped = len(ds) == top and all(
        len(ds[k - 1]) == len(by[k - 1]) and all(len(r) == len(by[k]) for r in ds[k - 1]) for k in range(1, top + 1))
    if not shaped:
        failed.append("chained")
    else:
        ms = [_mat(m) for m in ds]
        for k in range(1, top):
            lower, upper = ms[k - 1], ms[k]
            if any(sum((lower[i][t] * upper[t][j] for t in range(len(by[k]))), ZERO) != ZERO
                   for i in range(len(by[k - 1])) for j in range(len(by[k + 1]))):
                failed.append("composites_zero")
                break
    if ds != maps(bd_n):
        failed.append("boundary_replayed")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    cs = cells()
    extra = {"cells_by_degree": [sum(1 for c in cs if len(c) == k + 1) for k in range(4)],
             "signless_composites_vanish": not decide(signless()).count("composites_zero")}
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, LEAN, SOURCES, extra)
