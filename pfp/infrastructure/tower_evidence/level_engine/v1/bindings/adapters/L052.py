"""Adapter for level 052: the engine's row, splits and claimed weights written
as the target checker's row, first, second, table, conditionals and reverse.
Every index follows the declared order of ``bit``; a first outcome with no
conditional weights is written ``null``.  Written against the registered
stage-52 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_052"
CLAUSES = (("C1", "R052_NOT_UNIT"), ("C2", "R052_PROJECTOR"), ("C3", "R052_INCOMPLETE"), ("C4", "R052_NOT_SEQUENTIAL"),
           ("C5", "R052_CONDITIONAL"), ("C6", "R052_REVERSE"))
COEFFICIENT_DOMAIN = {"source": "exact pairs of rationals", "target": "exact pairs of rationals"}
SORTS = (("bit", "slot and outcome index"),)
UNMAPPED_SORTS = ("presentation token", "witness form", "val")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.frame_size", "two-slot frames, two-member splits", "frames and splits of any size", "WEAKENED"),)
NEAR = (("own_neg", "R052_NOT_SEQUENTIAL"), ("near_divided", "R052_CONDITIONAL"))
MUTATIONS = (("C1", "R052_NOT_UNIT", "row_not_unit", "near_unit"), ("C2", "R052_PROJECTOR", "member_not_self_mirrored", "near_member"),
             ("C3", "R052_INCOMPLETE", "split_incomplete", "near_incomplete"), ("C4", "R052_NOT_SEQUENTIAL", "mut", "mut"),
             ("C5", "R052_CONDITIONAL", "conditional_off", "near_conditional"), ("C6", "R052_REVERSE", "reverse_off", "near_reverse"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def splits_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    bits = _sort(structure, "bit")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def pairs_of(name: str) -> dict[tuple[int, ...], list[str]]:
        return {tuple(a[:-2]): [value[a[-2]], value[a[-1]]] for n, a in rel if n == name}

    def weights(name: str) -> dict[tuple[int, int], str]:
        return {(a[0], a[1]): value[a[2]] for n, a in rel if n == name}

    entry, first, second = pairs_of("entry"), pairs_of("first"), pairs_of("second")
    weight, given, back = weights("weight"), weights("given"), weights("back")
    return {"conditionals": [[given[(p, q)] for q in bits] if any((p, q) in given for q in bits) else None for p in bits],
            "first": [[[first[(o, i, j)] for j in bits] for i in bits] for o in bits],
            "reverse": [[back[(q, p)] for p in bits] for q in bits], "row": [entry[(i,)] for i in bits],
            "second": [[[second[(o, i, j)] for j in bits] for i in bits] for o in bits],
            "table": [[weight[(p, q)] for q in bits] for p in bits]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": splits_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": splits_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": splits_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"bit:{k}", f"index:{k}"] for k in range(len(positive["row"]))]
