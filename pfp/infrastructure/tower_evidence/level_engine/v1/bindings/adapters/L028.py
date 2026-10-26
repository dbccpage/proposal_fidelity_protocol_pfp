"""Adapter for level 028: the engine's degrees, units, steps, maps and lifts
written as the target checker's source and target complexes, chain maps f
and g, and homotopies h and k.  Degrees are indexed by their hosted numbers
(the engine's ``degrees_in_line`` requires them to be 0, 1, ... in declared
order); within a degree, basis vectors are the side's units in declared
order.  Every matrix entry is a hosted entry: the engine hosts one entry,
zeros included, for every pair of units a table relates (``*_given`` and
``one_*``), so no entry is filled in here.  ``there`` is f, ``back`` is g,
``source_lift`` is h and ``target_lift`` is k; a step or lift ``(x, y, c)``
is the entry at row y, column x.  Written against the registered stage-28
checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_028"
CLAUSES = (("C1", "R028_NOT_A_COMPLEX"), ("C2", "R028_NOT_A_CHAIN_MAP"), ("C3", "R028_LEFT_HOMOTOPY"),
           ("C4", "R028_RIGHT_HOMOTOPY"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("degree", "degree index"), ("source", "source basis vector"), ("target", "target basis vector"))
UNMAPPED_SORTS = ("presentation token", "witness form", "number")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.degrees", "one numbered list of degrees shared by both sides",
     "two dimension lists of equal length; unequal top degrees cannot be hosted", "WEAKENED"),
    ("target.basis_order", "units of a degree in declared order", "matrix rows and columns in that order",
     "PRESERVED"),
    ("target.entries", "one hosted entry per related pair of units, zeros included",
     "dense matrices of canonical rationals", "PRESERVED"),
    ("clause.graded", "no entry between units of the wrong degrees", "no cell for such an entry in the target input",
     "DROPPED"),
)
NEAR = (("own_neg", "R028_RIGHT_HOMOTOPY"),)
MUTATIONS = (("C1", "R028_NOT_A_COMPLEX", "step_after_step", "near_not_square"),
             ("C2", "R028_NOT_A_CHAIN_MAP", "back_not_commuting", "near_not_commuting"),
             ("C3", "R028_LEFT_HOMOTOPY", "source_lift_dropped", "near_source_lift"),
             ("C4", "R028_RIGHT_HOMOTOPY", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    # Degrees in the order of their hosted numbers.
    degrees = sorted(_sort(structure, "degree"), key=lambda d: Fraction(value[d]))

    def layers(side: str) -> list[list[int]]:
        place = {a[0]: a[1] for n, a in rel if n == f"{side}_in"}
        return [[x for x in _sort(structure, side) if place[x] == d] for d in degrees]

    src, tgt = layers("source"), layers("target")

    def matrix(name: str, cols: list[int], rows: list[int]) -> list[list[str]]:
        entry = {(a[0], a[1]): value[a[2]] for n, a in rel if n == name}
        return [[entry[(x, y)] for x in cols] for y in rows]

    top = len(degrees) - 1

    def complex_of(side: str, ls: list[list[int]]) -> dict[str, Any]:
        return {"d": [matrix(f"{side}_step", ls[i + 1], ls[i]) for i in range(top)], "dims": [len(x) for x in ls]}

    return {"f": [matrix("there", src[i], tgt[i]) for i in range(top + 1)],
            "g": [matrix("back", tgt[i], src[i]) for i in range(top + 1)],
            "h": [matrix("source_lift", src[i], src[i + 1]) for i in range(top)],
            "k": [matrix("target_lift", tgt[i], tgt[i + 1]) for i in range(top)],
            "source": complex_of("source", src), "target": complex_of("target", tgt)}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    out = [[f"degree:{i}", f"degree:{i}"] for i in range(len(positive["source"]["dims"]))]
    for side in ("source", "target"):
        k = 0
        for i, n in enumerate(positive[side]["dims"]):
            for j in range(n):
                out.append([f"{side}:{k}", f"{side}.basis:{i}.{j}"])
                k += 1
    return out
