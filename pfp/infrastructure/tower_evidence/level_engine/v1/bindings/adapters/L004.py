"""Adapter for level 004: the engine's hosted cells and sides written as the
target checker's oriented complex.  Vertices are the point elements; each
face becomes the cell of its points; each side ``(u, v)`` becomes the arc
``u>v``; the order is the declared order of elements, which is the typed
map's orientation convention (never derived, as the target itself records).

The engine's sign witness (``apart``, ``flip``, ``named``) has no image in
the target's input, so the fixture it alone refuses (three cells on one side)
is not stated.  Only the missing-edge clause is claimed.  Written against the
registered stage-4 checker (``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_004"
CLAUSES = (("C1", "R004_MISSING_EDGE"),)
COEFFICIENT_DOMAIN = {"source": "finite structure", "target": "oriented simplicial complex"}
SORTS = (("pt", "vertex"), ("cell", "cell"), ("side", "edge"))
UNMAPPED_SORTS = ("sgn", "presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("clause.sign_witness", "a sign choice witness with its tie structure", "no sign in the target input",
     "DROPPED"),
    ("target.order", "sides directed as hosted", "the declared order of elements, a convention", "WEAKENED"),
)
NEAR = ("near_side_first", "near_side_last", "own_neg")


def complex_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    off, points = 0, []
    for name, count in structure["sorts"]:
        if name == "pt":
            points = list(range(off, off + count))
        off += count
    cells = sorted(sorted(args[1:]) for name, args in structure["relations"] if name == "face")
    edges = [f"{args[0]}>{args[1]}" for name, args in structure["relations"] if name == "side"]
    return {"cells": cells, "edges": edges, "order": list(points), "vertices": points}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": complex_of(by["pos"])}]
    out += [{"expected_code": "R004_MISSING_EDGE", "id": fid, "kind": "near_miss", "payload": complex_of(by[fid])}
            for fid in NEAR]
    out.append({"clause": "C1", "expected_code": "R004_MISSING_EDGE", "id": "mut", "kind": "decisive_mutation",
                "payload": complex_of(by["mut"]), "repair": "pos"})
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"element:{v}", f"vertex:{v}"] for v in positive["vertices"]]
