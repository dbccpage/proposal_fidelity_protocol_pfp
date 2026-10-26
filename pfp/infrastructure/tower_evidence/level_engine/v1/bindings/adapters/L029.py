"""Adapter for level 029: the replayed cells and boundary maps are the target
checker's input as they stand (cells as ascending point lists, maps as
matrices of exact rationals).  Written against the registered stage-29
checker (``b5a2c46c``).

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_029"
CLAUSES = (("C1", "R029_DEGREE"), ("C2", "R029_NONZERO_COMPOSITE"), ("C3", "R029_NOT_THE_BOUNDARY"),
           ("C4", "R029_NOT_CLOSED"))
COEFFICIENT_DOMAIN = {"source": "integer chains", "target": "exact rationals"}
SORTS = (("cell", "cell"),)
UNMAPPED_SORTS = ("presentation token",)
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.sign_convention", "the declared alternating sign", "the same convention, recomputed", "PRESERVED"),
    ("target.derived_limit", "not computed", "not decided by the target either", "PRESERVED"),
)
NEAR = (("own_neg", "R029_NONZERO_COMPOSITE"), ("near_tail", "R029_NOT_THE_BOUNDARY"))
MUTATIONS = (("C1", "R029_DEGREE", "mut", "mut"),
             ("C2", "R029_NONZERO_COMPOSITE", "shared_side_sign_flipped", "near_sign"),
             ("C3", "R029_NOT_THE_BOUNDARY", "tail_coefficient_doubled", "near_tail"),
             ("C4", "R029_NOT_CLOSED", "last_point_undeclared", "near_open"))


def chain_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    packet = obj["packet"]
    assert isinstance(packet, dict)
    return copy.deepcopy(dict(packet))


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": chain_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": chain_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": chain_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"cell:{c}", f"cell:{c}"] for c in positive["cells"]]
