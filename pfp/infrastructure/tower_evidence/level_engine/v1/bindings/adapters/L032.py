"""Adapter for level 032: the replayed reading is the target checker's input
as it stands (fine data by token, coarse classes, the block map, the
protected requirements, the ledger of inseparable pairs, no erasure record).
Written against the registered stage-32 checker (``b5a2c46c``).

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_032"
CLAUSES = (("C1", "R032_NOT_A_MAP"), ("C2", "R032_LEDGER_INCOMPLETE"), ("C3", "R032_LEDGER_PADDED"),
           ("C4", "R032_SILENT_PROTECTED_MERGE"))
COEFFICIENT_DOMAIN = {"source": "replayed regimes", "target": "finite carriers"}
SORTS = (("datum", "fine point"), ("profile class", "coarse point"))
UNMAPPED_SORTS = ("presentation token", "form", "instance")
STRUCTURE_MAP_REASON = ""
LOSS_ROWS = (
    ("target.coarse_reading", "the sealed observation", "a declared block map", "WEAKENED"),
    ("target.demand", "the demand the response answers", "one more protected pair", "PRESERVED"),
)
NEAR = (("own_neg", "R032_SILENT_PROTECTED_MERGE"), ("near_padded", "R032_LEDGER_PADDED"))
MUTATIONS = (("C1", "R032_NOT_A_MAP", "third_datum_unmapped", "near_partial"),
             ("C2", "R032_LEDGER_INCOMPLETE", "merge_unrecorded", "near_unrecorded"),
             ("C3", "R032_LEDGER_PADDED", "protected_pair_recorded", "near_padded"),
             ("C4", "R032_SILENT_PROTECTED_MERGE", "mut", "mut"))


def blocks_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    packet = obj["packet"]
    assert isinstance(packet, dict)
    return copy.deepcopy(dict(packet))


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": blocks_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": blocks_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": blocks_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"datum:{a}", f"fine:{a}"] for a in positive["fine"]]


def squares(source: object, positive: object) -> list[tuple[str, object, object]]:
    """The block map: each datum's profile class in the replay (left) against
    the positive's block map (right)."""
    assert isinstance(source, dict) and isinstance(positive, dict)
    return [("block_map", sorted(source["packet"]["block_map"]), sorted(positive["block_map"]))]
