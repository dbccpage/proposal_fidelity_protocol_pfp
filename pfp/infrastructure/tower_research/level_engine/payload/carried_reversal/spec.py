# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Replay of sealed evidence: the reversal of typed arrows, carried by the
sealed transpose on the two-point carrier.

The arrows are the composition closure of the sealed symmetric datum ``S2``
on the two-point carrier (every ordered pair of points, loops included),
each named by its endpoints.  Composition is relational: the arrow from the
first source to the second target.  The dagger of an arrow is the arrow of
its transposed pair (the sealed ``transpose``); applied twice it restores the
arrow (the sealed swap twice restores ``D2``).  An arrow is marked when it
carries an obstruction: it collides under the identity map of the carrier
(the sealed ``collision``), which is to say it is a loop.  Collision is
invariant under transposition (sealed ``collision_transpose_invariant``), so
the dagger keeps every mark.  On the directed datum ``D2`` alone the
reversal is not an arrow at all (sealed ``swap_auto_of_S2_not_of_D2``).

Clauses, each decided on the replayed sealed facts:

* ``arrows_replayed``: the objects are the carrier and the arrows are the
  closure of ``S2``, with the marks the sealed collision gives;
* ``dagger_is_transpose``: each arrow's dagger is the arrow of its
  transposed pair, and every arrow has one;
* ``composites_replayed``: the composites are exactly the relational
  composites of the arrows.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.level import LevelResult
from omega_engine_operations.use_cases.level_engine.research_engine.replay import Packet, Row, packets as replay_packets, result
from derivation.primdiff import CARRIER_ID, D2, S2, collision, transpose

CHALLENGE_ID = "carried_reversal"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
LEAN = ("PrimDiff.swap_carries_D2_to_D2rev", "PrimDiff.swap_auto_of_S2_not_of_D2",
        "PrimDiff.collision_transpose_invariant", "PrimDiff.swap_twice_restores_D2")
SOURCES = ("code/derivation/primdiff.py",)
CLAUSES = ("arrows_replayed", "dagger_is_transpose", "composites_replayed")


def name(pair: tuple[int, int]) -> str:
    return f"a{pair[0]}{pair[1]}"


def closure(rel: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    out = set(rel)
    while True:
        more = {(a, d) for a, b in out for c, d in out if b == c} - out
        if not more:
            return frozenset(out)
        out |= more


def mark(pair: tuple[int, int]) -> str:
    return "marked" if collision(frozenset({pair}), CARRIER_ID) else "plain"


def arrows_of(rel: frozenset[tuple[int, int]]) -> list[list[object]]:
    return [[name(p), p[0], p[1], mark(p)] for p in sorted(closure(rel))]


def dagger_of(rel: frozenset[tuple[int, int]]) -> list[list[str]]:
    arrows = closure(rel)
    return [[name(p), name(q)] for p in sorted(arrows) for q in sorted(transpose(frozenset({p}))) if q in arrows]


def composites_of(rel: frozenset[tuple[int, int]]) -> list[list[str]]:
    arrows = sorted(closure(rel))
    return [[name(f), name(g), name((f[0], g[1]))] for f in arrows for g in arrows if f[1] == g[0]]


def positive() -> Packet:
    return {"arrows": arrows_of(S2.rel), "composites": composites_of(S2.rel), "dagger": dagger_of(S2.rel),
            "objects": list(range(S2.n))}


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def decide(pk: Packet) -> tuple[str, ...]:
    failed: list[str] = []
    if pk["objects"] != list(range(S2.n)) or pk["arrows"] != arrows_of(S2.rel):
        failed.append("arrows_replayed")
    ends = {str(a[0]): (int(a[1]), int(a[2])) for a in pk["arrows"]}  # type: ignore[attr-defined]
    dag = {str(a): str(b) for a, b in pk["dagger"]}  # type: ignore[attr-defined]
    by_pair = {p: n for n, p in ends.items()}
    if set(dag) != set(ends) or any(by_pair.get((ends[f][1], ends[f][0])) != g for f, g in dag.items()):
        failed.append("dagger_is_transpose")
    listed = sorted(tuple(c) for c in pk["composites"])  # type: ignore[attr-defined]
    wanted = sorted((by_pair[f], by_pair[g], by_pair[(f[0], g[1])]) for f in ends.values() for g in ends.values()
                    if f[1] == g[0] and (f[0], g[1]) in by_pair)
    if listed != wanted:
        failed.append("composites_replayed")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    extra = {"closure_of_directed": [name(p) for p in sorted(closure(D2.rel))],
             "dagger_on_directed": dagger_of(D2.rel)}
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, LEAN, SOURCES, extra)
