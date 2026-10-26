"""Adapter for level 065's research-tree replay: the replayed toggle, its
budget encodings in the passage, the map and the claim are the target
checker's source, target, map, back and claim as they stand.  Written
against the registered stage-65 checker.

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_065"
CLAUSES = (("C1", "R065_NO_MAP"), ("C2", "R065_NOT_A_MAP"), ("C3", "R065_STEP_SQUARE"),
           ("C4", "R065_OBSERVATION_SQUARE"), ("C5", "R065_NOT_EQUIVALENT"))
COEFFICIENT_DOMAIN = {"source": "finite step systems", "target": "finite step systems"}
SORTS = (("state", "source state"), ("encoding", "target state"), ("reading", "observation"))
UNMAPPED_SORTS = ("presentation token", "event label")
STRUCTURE_MAP_REASON = "the map is the claim's own datum; its squares are the clauses the checker decides"
LOSS_ROWS = (
    ("target.step", "the passage step under the register's translated event, one budget write per source step "
                    "(the event selection is supplied data, NB-15)",
     "one step table on the encoded states, computed by the tree's preplay", "WEAKENED"),
    ("target.observe", "the passage's native observation (zero relation, obstruction, refusals), a function of "
                       "the core, stated in the tree's Lean only",
     "the tree's Python core of each state as text, finer than the native observation", "WEAKENED"),
    ("source.observe", "a constant observation carried by the observation map to the native observation of "
                       "genesis (budgetSim_nobs)", "the carried reading written on each source state", "PRESERVED"),
    ("source.claim", "a one-way commuting translation (the tree's Sim); reading an injective commuting square as "
                     "the passage reproducing the source is refuted (NB-9)", "claim simulation", "PRESERVED"),
    ("source.target_native", "the target tables are checked against the tree's passage replay and core",
     "not a checker clause; the checker takes the target tables as given", "DROPPED"),
    ("source.lean", "the tree's Lean (budgetSim, toggle_encoding, budgetSim_nobs, toggle_no_faithful_obs)",
     "not cited; the replay rests on the tree's Python", "DROPPED"),
)
NEAR = (("own_neg", "R065_NO_MAP"), ("own_state_sight", "R065_OBSERVATION_SQUARE"),
        ("near_step", "R065_STEP_SQUARE"), ("near_equiv", "R065_NOT_EQUIVALENT"))
MUTATIONS = (("C1", "R065_NO_MAP", "map_withdrawn", "near_no_map"),
             ("C2", "R065_NOT_A_MAP", "image_missing", "near_partial"),
             ("C3", "R065_STEP_SQUARE", "step_not_carried", "near_step"),
             ("C4", "R065_OBSERVATION_SQUARE", "mut", "mut"),
             ("C5", "R065_NOT_EQUIVALENT", "one_way_only", "near_equiv"))


def packet_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    packet = obj["packet"]
    assert isinstance(packet, dict)
    return copy.deepcopy(dict(packet))


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": packet_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": packet_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": packet_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"state:{s}", f"source:{s}"] for s in positive["source"]["states"]] + \
        [[f"encoding:{t}", f"target:{t}"] for t in positive["target"]["states"]]
