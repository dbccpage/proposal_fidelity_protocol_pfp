"""Adapter for level 054: the engine's joined row written as the target
checker's shape, row and claimed rank.  The shape is the number of near and
far slots; the entry at near slot ``i`` and far slot ``j`` is written at
index ``n * i + j`` as ``[a, b]``, and a missing entry contributes none; the
claimed rank is written as a natural number.  Written against the registered
stage-54 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_054"
CLAUSES = (("C1", "R054_SHAPE"), ("C2", "R054_NOT_UNIT"), ("C3", "R054_RANK"))
COEFFICIENT_DOMAIN = {"source": "exact pairs of rationals", "target": "exact pairs of rationals"}
SORTS = (("near", "first factor slot"), ("far", "second factor slot"), ("val", "rational"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.frame_sizes", "two by two joined frames", "m by n joined frames", "WEAKENED"),)
NEAR = (("own_neg", "R054_RANK"),)
MUTATIONS = (("C1", "R054_SHAPE", "entry_missing", "near_gap"), ("C2", "R054_NOT_UNIT", "size_off", "near_unit"),
             ("C3", "R054_RANK", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def joined_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    near, far = _sort(structure, "near"), _sort(structure, "far")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    got = {(a[0], a[1]): [value[a[2]], value[a[3]]] for n, a in rel if n == "entry"}
    rank = Fraction(next(value[a[0]] for n, a in rel if n == "rank"))
    return {"rank": int(rank), "row": [got[(i, j)] for i in near for j in far if (i, j) in got],
            "shape": [len(near), len(far)]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": joined_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": joined_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": joined_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    m, n = positive["shape"]
    return [[f"entry:{i},{j}", f"index:{n * i + j}"] for i in range(m) for j in range(n)]
