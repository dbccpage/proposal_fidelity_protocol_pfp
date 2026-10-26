# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 014: the replayed obstruction claim is the target
checker's input as it stands (a formula tree over the sealed menu, its mask,
its budget and its value).  Written against the registered stage-14 checker
(``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_014"
CLAUSES = (("C1", "R014_UNBOUNDED"), ("C2", "R014_MASK_MISMATCH"), ("C3", "R014_BUDGET_EXCEEDED"),
           ("C4", "R014_VALUE_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "sealed response menu", "target": "bounded formula"}
SORTS = (("menu position", "bound variable value"),)
UNMAPPED_SORTS = ("presentation token", "view", "requirement")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.atoms", "the sealed repair check", "the repairing positions written as atoms", "WEAKENED"),
    ("target.domain", "the whole sealed menu", "any declared bound; the truncated claim passes the target",
     "WEAKENED"),
)
NEAR = (("own_neg", "R014_UNBOUNDED"), ("near_mask", "R014_MASK_MISMATCH"))
MUTATIONS = (("C1", "R014_UNBOUNDED", "unbounded_menu", "own_neg"),
             ("C2", "R014_MASK_MISMATCH", "existential_mask", "near_mask"),
             ("C3", "R014_BUDGET_EXCEEDED", "budget_one_short", "near_budget"),
             ("C4", "R014_VALUE_MISMATCH", "mut", "mut"))


def claim_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    packet = obj["packet"]
    assert isinstance(packet, dict)
    return copy.deepcopy(dict(packet))


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"position:{k}", f"value:{k}"] for k in range(int(positive["formula"][2]))]
