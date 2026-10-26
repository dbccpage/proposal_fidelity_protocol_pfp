"""Adapter for level 033: the engine's reading, steps and jumps written as the
target checker's reading, steps and jumps.  Points and blocks follow the
declared order; the near jump runs from scale 0 to scale 1 and the far jump
from scale 0 to scale 2; a jump with no loss bound is written with the bound
``null``.  Written against the registered stage-33 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_033"
CLAUSES = (("C1", "R033_NOT_COMPOSITE"), ("C2", "R033_UNBOUNDED_JUMP"), ("C3", "R033_BOUND_TOO_SMALL"),
           ("C4", "R033_BOUND_NOT_COMPOSED"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("point", "scale 0 point"), ("first_block", "scale 1 block"), ("second_block", "scale 2 block"),
         ("val", "rational"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.scales", "two steps and two jumps", "any chain of steps and any jumps", "WEAKENED"),)
NEAR = (("near_small", "R033_BOUND_TOO_SMALL"),)
MUTATIONS = (("C1", "R033_NOT_COMPOSITE", "jump_map_off", "near_composite"),
             ("C2", "R033_UNBOUNDED_JUMP", "jump_unbounded", "own_neg"), ("C3", "R033_BOUND_TOO_SMALL", "mut", "mut"),
             ("C4", "R033_BOUND_NOT_COMPOSED", "jump_bound_loose", "near_loose"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def scales_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    points, first, second = _sort(structure, "point"), _sort(structure, "first_block"), _sort(structure, "second_block")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def mapping(name: str, source: list[int], target: list[int]) -> list[int]:
        got = {a[0]: target.index(a[1]) for n, a in rel if n == name}
        return [got[s] for s in source]

    def one(name: str) -> str | None:
        return next((value[a[0]] for n, a in rel if n == name), None)

    reads = {a[0]: value[a[1]] for n, a in rel if n == "reads"}
    return {"jumps": [[0, 1, mapping("near_jump", points, first), one("near_jump_bound")],
                      [0, 2, mapping("far_jump", points, second), one("far_jump_bound")]],
            "reading": [reads[p] for p in points],
            "steps": [[mapping("first", points, first), one("first_bound")],
                      [mapping("second", first, second), one("second_bound")]]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": scales_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": scales_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": scales_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"point:{k}", f"scale0:{k}"] for k in range(len(positive["reading"]))]
