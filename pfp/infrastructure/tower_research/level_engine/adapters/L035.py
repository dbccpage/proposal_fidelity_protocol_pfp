# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 035: the engine's hosted step weights written as the
target checker's states and kernel.  States are named by their position in
the declared order; the kernel's rows and columns follow that order.
Written against the registered stage-35 checker (``b5a2c46c``).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_035"
CLAUSES = (("C1", "R035_ROW_SUM"), ("C2", "R035_NEGATIVE_ENTRY"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("state", "state"), ("val", "kernel entry"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.state_names", "states as elements", "their positions as names", "PRESERVED"),)
NEAR = (("near_negative", "R035_NEGATIVE_ENTRY"),)
MUTATIONS = (("C1", "R035_ROW_SUM", "mut", "mut"), ("C2", "R035_NEGATIVE_ENTRY", "negative_weight", "near_negative"))


def kernel_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    off, states = 0, []
    for name, count in structure["sorts"]:
        if name == "state":
            states = list(range(off, off + count))
        off += count
    value = {int(e): str(v) for e, v in structure["values"]}
    w = {(a[0], a[1]): value[a[2]] for name, a in structure["relations"] if name == "weight"}
    return {"kernel": [[w[(s, t)] for t in states] for s in states], "states": [str(k) for k in range(len(states))]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": kernel_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": kernel_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": kernel_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"element:{s}", f"state:{s}"] for s in positive["states"]]
