"""Adapter for level 051: the engine's row, split and reported weights
written as the target checker's row, family and weights.  Slots and
outcomes follow the declared order.  Written against the registered
stage-51 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_051"
CLAUSES = (("C1", "R051_NOT_UNIT"), ("C2", "R051_PROJECTOR"), ("C3", "R051_INCOMPLETE"), ("C4", "R051_WEIGHT_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "exact pairs of rationals", "target": "exact pairs of rationals"}
SORTS = (("slot", "frame slot"), ("outcome", "outcome"), ("val", "rational"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.frame_size", "two-slot frames", "frames of any size", "WEAKENED"),)
NEAR = (("own_neg", "R051_WEIGHT_MISMATCH"),)
MUTATIONS = (("C1", "R051_NOT_UNIT", "row_not_unit", "near_unit"), ("C2", "R051_PROJECTOR", "member_not_self_mirrored", "near_member"),
             ("C3", "R051_INCOMPLETE", "split_incomplete", "near_incomplete"), ("C4", "R051_WEIGHT_MISMATCH", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def split_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    slots, outs = _sort(structure, "slot"), _sort(structure, "outcome")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    entry = {a[0]: [value[a[1]], value[a[2]]] for n, a in rel if n == "entry"}
    split = {(a[0], a[1], a[2]): [value[a[3]], value[a[4]]] for n, a in rel if n == "split"}
    weight = {a[0]: value[a[1]] for n, a in rel if n == "weight"}
    return {"family": [[[split[(k, i, j)] for j in slots] for i in slots] for k in outs],
            "row": [entry[s] for s in slots], "weights": [weight[k] for k in outs]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": split_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": split_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": split_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"outcome:{k}", f"member:{k}"] for k in range(len(positive["family"]))]
