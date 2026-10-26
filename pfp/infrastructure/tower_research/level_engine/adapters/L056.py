# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 056: the engine's joined row and claimed reduction
written as the target checker's shape, row and reduced table.  The entry at
near slot ``i`` and far slot ``k`` is written at index ``n * i + k``;
slots follow the declared order.  Written against the registered stage-56
checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_056"
CLAUSES = (("C1", "R056_NOT_UNIT"), ("C2", "R056_TRACE"), ("C3", "R056_NOT_PSD"), ("C4", "R056_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "exact pairs of rationals", "target": "exact pairs of rationals"}
SORTS = (("near", "near slot"), ("far", "far slot"), ("val", "rational"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.frame_sizes", "two by two joined frames", "m by n joined frames", "WEAKENED"),)
NEAR = (("own_neg", "R056_TRACE"),)
MUTATIONS = (("C1", "R056_NOT_UNIT", "row_not_unit", "near_unit"), ("C2", "R056_TRACE", "trace_changed", "near_trace"),
             ("C3", "R056_NOT_PSD", "not_self_mirrored", "near_mirror"), ("C4", "R056_MISMATCH", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def reduced_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    near, far = _sort(structure, "near"), _sort(structure, "far")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def grid(name: str) -> dict[tuple[int, int], list[str]]:
        return {(a[0], a[1]): [value[a[2]], value[a[3]]] for n, a in rel if n == name}

    joint, reduced = grid("joint"), grid("reduced")
    return {"reduced": [[reduced[(i, j)] for j in near] for i in near],
            "row": [joint[(i, k)] for i in near for k in far], "shape": [len(near), len(far)]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": reduced_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": reduced_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": reduced_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    m, n = positive["shape"]
    return [[f"joint:{i},{k}", f"index:{n * i + k}"] for i in range(m) for k in range(n)]
