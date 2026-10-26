# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 063: the engine's corners, patches, edges and claims
written as the target checker's triangles, lengths, terms and action.
Corners are named by their positions; triangles follow the declared patch
order, each its corners ascending; length rows are sorted; each corner's
term lists its patches ascending.  Written against the registered stage-63
checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_063"
CLAUSES = (("C1", "R063_DEGENERATE"), ("C2", "R063_ANGLE_NOT_EXACT"), ("C3", "R063_INCIDENCE"),
           ("C4", "R063_DEFICIT"), ("C5", "R063_ACTION"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("corner", "vertex"), ("patch", "triangle"), ("edge", "squared length"), ("total", "action"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.hinge_measure", "vertex hinges with measure one", "vertex hinges with measure one",
              "PRESERVED"),)
NEAR = (("own_neg", "R063_INCIDENCE"),)
MUTATIONS = (("C1", "R063_DEGENERATE", "edge_flattened", "near_flat"),
             ("C2", "R063_ANGLE_NOT_EXACT", "edge_skewed", "near_skew"),
             ("C3", "R063_INCIDENCE", "mut", "mut"),
             ("C4", "R063_DEFICIT", "deficit_changed", "near_deficit"),
             ("C5", "R063_ACTION", "total_changed", "near_total"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    corners, patches = _sort(structure, "corner"), _sort(structure, "patch")
    (tot,) = _sort(structure, "total")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    spans = {a[0]: sorted(corners.index(x) for x in a[1:]) for n, a in rel if n == "spans"}
    lengths = sorted([min(corners.index(a[1]), corners.index(a[2])), max(corners.index(a[1]), corners.index(a[2])),
                      value[a[0]]] for n, a in rel if n == "ends")
    terms = [[k, sorted(patches.index(a[1]) for n, a in rel if n == "uses" and a[0] == v), value[v]]
             for k, v in enumerate(corners)]
    return {"action": value[tot], "lengths": lengths, "terms": terms, "triangles": [spans[t] for t in patches]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"patch:{k}", "triangle:" + ",".join(str(v) for v in t)] for k, t in enumerate(positive["triangles"])]
