# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Replay of sealed evidence: repair routes over a complex whose incidence is
the sealed alternating boundary, each route replayed with its witness.

The complex is two triangles on a shared side, the first filled and the
second hollow.  Both incidence tables come from the sealed ``bd_n`` (read
from the pinned clone): the side-by-point table is the boundary of each side,
and the cell-by-side table the boundary of each filled cell.  A load takes one
of three routes: *exact* (a potential ``s`` with ``d0 s`` equal to the load),
*closed but not exact* (``d1`` of the load is zero, and a balanced ``y``
pairs with it to a nonzero number), or *open* (``d1`` of the load is not
zero).  The balanced witness of the closed route is the sealed boundary of
the hollow triangle: the sealed ``d2_zero_unrestricted`` is exactly the
statement that it is balanced.  The trace visits the three cases and returns
to the first; replay is deterministic, so the revisited state is the same.

Clauses, each decided on the replayed sealed facts:

* ``board_replayed``: both tables are the sealed boundaries of the complex;
* ``route_is_class``: each case's route is its computed class (exact when
  the load lies in the image of ``d0``, closed when ``d1`` kills it, open
  otherwise);
* ``exact_replayed``: an exact case carries a potential that rebuilds its load;
* ``dual_replayed``: a closed case carries the sealed boundary of a hollow
  triangle, and it pairs with the load to a nonzero number;
* ``open_replayed``: an open case carries no witness;
* ``repeat_replayed``: the trace names each case with its route, and the
  declared cycle joins two equal states.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.exact.linalg import rank
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO, Q, fmt_q, parse_q
from omega_engine_operations.use_cases.level_engine.research_engine.level import LevelResult
from omega_engine_operations.use_cases.level_engine.research_engine.replay import Packet, Row, packets as replay_packets, result
from derivation.boundary_cancellation import bd_n, facets

CHALLENGE_ID = "route_replay"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
LEAN = ("BoundaryCancellation.d2_zero_unrestricted", "BoundaryCancellation.d2_zero_facets",
        "PrimitivePassage.two_rule")
SOURCES = ("code/derivation/boundary_cancellation.py",)
CLAUSES = ("board_replayed", "route_is_class", "exact_replayed", "dual_replayed", "open_replayed",
           "repeat_replayed")
FILLED: tuple[tuple[int, ...], ...] = ((0, 1, 2),)
HOLLOW: tuple[tuple[int, ...], ...] = ((1, 2, 3),)
POINTS = 4
Vec = list[Q]


def sides() -> list[tuple[int, ...]]:
    return sorted({f for t in FILLED + HOLLOW for f in facets(t)})


def row(chain: list[tuple[int, tuple[int, ...]]], cells: Sequence[tuple[int, ...]]) -> Vec:
    return [Q(sum(c for c, t in chain if t == cell)) for cell in cells]


def tables() -> tuple[list[Vec], list[Vec]]:
    points = [(v,) for v in range(POINTS)]
    return [row(bd_n(e), points) for e in sides()], [row(bd_n(t), sides()) for t in FILLED]


def text(v: Vec) -> list[str]:
    return [fmt_q(x) for x in v]


def indicator(side: tuple[int, int]) -> Vec:
    return [ONE if e == side else ZERO for e in sides()]


def apply(m: list[Vec], v: Vec) -> Vec:
    return [sum((a * b for a, b in zip(r, v)), ZERO) for r in m]


def transpose(m: list[Vec], columns: int) -> list[Vec]:
    return [[r[j] for r in m] for j in range(columns)]


def positive() -> Packet:
    d0, d1 = tables()
    potential: Vec = [Q(v) for v in range(POINTS)]
    hollow_rim = row(bd_n(HOLLOW[0]), sides())
    cases = [
        {"cochain": text(apply(d0, potential)), "route": "exact", "witness": text(potential)},
        {"cochain": text(indicator((2, 3))), "route": "residual_closed", "witness": text(hollow_rim)},
        {"cochain": text(indicator((0, 1))), "route": "open", "witness": None},
    ]
    return {"cases": cases, "cycle": [0, 3], "d0": [text(r) for r in d0], "d1": [text(r) for r in d1],
            "trace": [[0, "exact"], [1, "residual_closed"], [2, "open"], [0, "exact"]]}


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def _vec(x: object) -> Vec:
    assert isinstance(x, list)
    return [parse_q(v) for v in x]


def route_of(d0: list[Vec], d1: list[Vec], omega: Vec) -> str:
    if rank(d0) == rank([r + [w] for r, w in zip(d0, omega)]):
        return "exact"
    return "residual_closed" if all(x.is_zero() for x in apply(d1, omega)) else "open"


def decide(pk: Packet) -> tuple[str, ...]:
    failed: set[str] = set()
    d0, d1 = tables()
    if pk["d0"] != [text(r) for r in d0] or pk["d1"] != [text(r) for r in d1]:
        failed.add("board_replayed")
    rims = [row(bd_n(t), sides()) for t in HOLLOW]
    cases = pk["cases"]
    assert isinstance(cases, list)
    states: list[tuple[tuple[str, ...], str]] = []
    for case in cases:
        omega, route, witness = _vec(case["cochain"]), str(case["route"]), case["witness"]
        states.append((tuple(case["cochain"]), route))
        if route != route_of(d0, d1, omega):
            failed.add("route_is_class")
        if route == "exact" and (witness is None or apply(d0, _vec(witness)) != omega):
            failed.add("exact_replayed")
        if route == "residual_closed":
            y = None if witness is None else _vec(witness)
            pairing = ZERO if y is None else sum((a * b for a, b in zip(y, omega)), ZERO)
            if y not in rims or pairing.is_zero():
                failed.add("dual_replayed")
        if route == "open" and witness is not None:
            failed.add("open_replayed")
    trace = pk["trace"]
    assert isinstance(trace, list)
    ok = all(0 <= int(i) < len(states) and states[int(i)][1] == r for i, r in trace)
    first, second = (int(x) for x in pk["cycle"])  # type: ignore[attr-defined]
    if not ok or not 0 <= first < second < len(trace) or \
            states[int(trace[first][0])] != states[int(trace[second][0])]:
        failed.add("repeat_replayed")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    d0, d1 = tables()
    extra = {"balanced": [fmt_q(x) for x in apply(transpose(d0, POINTS), row(bd_n(HOLLOW[0]), sides()))],
             "sides": [list(e) for e in sides()]}
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, LEAN, SOURCES, extra)
