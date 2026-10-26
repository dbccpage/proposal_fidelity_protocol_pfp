"""Adapter for level 005: the engine's hosted squared-distance table written
as the target checker's one cell with its squared lengths.  Vertices are the
point elements; the cell is all of them; each entry ``sq(u, v, x)`` with
``u < v`` becomes ``[u, v, value(x)]``; the hinge list is empty.

The target keys a length by ``u < v``, so the diagonal and the lower
triangle have no image: the engine's symmetry and zero-diagonal clauses are
not stated, nor are the two fixtures that alone bite them.  Written against
the registered stage-5 checker (``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_005"
CLAUSES = (("C1", "R005_INCOMPLETE_LENGTHS"), ("C2", "R005_NONPOSITIVE_LENGTH"), ("C3", "R005_INDEFINITE_GRAM"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("pt", "vertex"), ("val", "squared length"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("clause.diagonal_zero.image", "a zero diagonal", "no diagonal in the target input", "DROPPED"),
    ("clause.symmetric", "a symmetric table", "lengths keyed by u < v", "DROPPED"),
    ("target.hinges", "no hinge is hosted", "an empty hinge list; the curvature clauses are not claimed",
     "WEAKENED"),
)
NEAR = (("own_neg", "R005_NONPOSITIVE_LENGTH"), ("near_complete", "R005_INCOMPLETE_LENGTHS"),
        ("near_one_value", "R_SCHEMA"), ("near_typed", "R_SCHEMA"))


def cell_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    off, points = 0, []
    for name, count in structure["sorts"]:
        if name == "pt":
            points = list(range(off, off + count))
        off += count
    value = {int(e): str(v) for e, v in structure["values"]}
    lengths = sorted([args[0], args[1], value[args[2]]] for name, args in structure["relations"]
                     if name == "sq" and args[0] < args[1])
    return {"cells": [list(points)], "hinges": [], "squared_lengths": lengths, "vertices": points}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": cell_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": cell_of(by[fid])} for fid, code in NEAR]
    out += [
        {"clause": "C1", "expected_code": "R005_INCOMPLETE_LENGTHS", "id": "missing", "kind": "decisive_mutation",
         "payload": cell_of(by["near_complete"]), "repair": "pos"},
        {"clause": "C2", "expected_code": "R005_NONPOSITIVE_LENGTH", "id": "coincident", "kind": "decisive_mutation",
         "payload": cell_of(by["near_degenerate"]), "repair": "pos"},
        {"clause": "C3", "expected_code": "R005_INDEFINITE_GRAM", "id": "mut", "kind": "decisive_mutation",
         "payload": cell_of(by["mut"]), "repair": "pos"},
    ]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"element:{v}", f"vertex:{v}"] for v in positive["vertices"]]
