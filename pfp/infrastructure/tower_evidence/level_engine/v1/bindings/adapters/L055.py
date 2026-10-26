"""Adapter for level 055: the engine's joined row, near split, far splits and
claimed weights written as the target checker's shape, row, near, far, table
and selection.  Every index follows the declared order of ``bit``; the entry
at near slot ``i`` and far slot ``k`` is written at index ``2 i + k``; no
selection is declared, so it is written ``null``.  Written against the
registered stage-55 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_055"
CLAUSES = (("C1", "R055_SPLIT"), ("C2", "R055_SIGNALLING"), ("C3", "R055_TABLE_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "exact pairs of rationals", "target": "exact pairs of rationals"}
SORTS = (("bit", "slot, outcome and far choice index"),)
UNMAPPED_SORTS = ("presentation token", "witness form", "val")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.selection", "no selection of far outcomes", "a declared selection, renormalised", "DROPPED"),
             ("target.frame_sizes", "two by two joined frames, two far choices", "any sizes and choices", "WEAKENED"))
NEAR = (("own_neg", "R055_SIGNALLING"),)
MUTATIONS = (("C1", "R055_SPLIT", "near_table_not_self_mirrored", "near_split"),
             ("C2", "R055_SIGNALLING", "near_weight_moves", "near_signal"), ("C3", "R055_TABLE_MISMATCH", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def blind_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    bits = _sort(structure, "bit")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def pairs_of(name: str) -> dict[tuple[int, ...], list[str]]:
        return {tuple(a[:-2]): [value[a[-2]], value[a[-1]]] for n, a in rel if n == name}

    joint, near, far = pairs_of("joint"), pairs_of("near"), pairs_of("far")
    weight = {tuple(a[:3]): value[a[3]] for n, a in rel if n == "weight"}
    return {"far": [[[[far[(y, o, i, j)] for j in bits] for i in bits] for o in bits] for y in bits],
            "near": [[[near[(o, i, j)] for j in bits] for i in bits] for o in bits],
            "row": [joint[(i, k)] for i in bits for k in bits], "selection": None, "shape": [len(bits), len(bits)],
            "table": [[[weight[(y, p, q)] for q in bits] for p in bits] for y in bits]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": blind_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": blind_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": blind_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"bit:{k}", f"index:{k}"] for k in range(positive["shape"][0])]
