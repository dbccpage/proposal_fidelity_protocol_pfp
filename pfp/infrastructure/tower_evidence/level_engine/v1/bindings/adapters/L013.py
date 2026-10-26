"""Adapter for level 013: the replayed board, cases and trace are the target
checker's input as they stand (the tables are the sealed alternating
boundary; loads and witnesses are exact rationals).  Written against the
registered stage-13 checker (``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_013"
CLAUSES = (("C1", "R013_BOARD_INVALID"), ("C2", "R013_MISSING_WITNESS"), ("C3", "R013_EXACT_NOT_REPLAYED"),
           ("C4", "R013_DUAL_NOT_REPLAYED"), ("C5", "R013_OPEN_NOT_REPLAYED"), ("C6", "R013_NO_REPEAT"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("point", "vertex"), ("side", "edge"), ("cell", "2-cell"))
UNMAPPED_SORTS = ("presentation token",)
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.trace", "a declared return to the first case", "a trace with a cycle", "WEAKENED"),
    ("target.routes", "three route classes", "three route codes", "PRESERVED"),
)
NEAR = (("own_neg", "R013_MISSING_WITNESS"), ("near_dual", "R013_DUAL_NOT_REPLAYED"))
MUTATIONS = (("C1", "R013_BOARD_INVALID", "rim_sign_flipped", "near_board"),
             ("C2", "R013_MISSING_WITNESS", "potential_withheld", "near_unwitnessed"),
             ("C3", "R013_EXACT_NOT_REPLAYED", "potential_off_by_one", "near_exact"),
             ("C4", "R013_DUAL_NOT_REPLAYED", "witness_unbalanced", "near_dual"),
             ("C5", "R013_OPEN_NOT_REPLAYED", "open_load_zeroed", "near_open"),
             ("C6", "R013_NO_REPEAT", "mut", "mut"))


def board_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    packet = obj["packet"]
    assert isinstance(packet, dict)
    return copy.deepcopy(dict(packet))


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": board_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": board_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": board_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"point:{v}", f"vertex:{v}"] for v in range(len(positive["d0"][0]))]
