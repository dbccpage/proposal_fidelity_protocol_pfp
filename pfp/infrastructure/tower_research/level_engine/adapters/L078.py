# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 078: the engine's logged entries, nodes, clocks and
parents written as the target checker's events, in log order.  Entries and
nodes are named ``e<k>`` and ``n<k>`` by their positions; parents are
sorted.  Written against the registered stage-78 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_078"
CLAUSES = (("C1", "R078_MISSING_PARENT"), ("C2", "R078_FUTURE_PARENT"), ("C3", "R078_CLOCK_NOT_MONOTONE"),
           ("C4", "R078_NODE_ORDER"))
COEFFICIENT_DOMAIN = {"source": "natural clocks", "target": "natural clocks"}
SORTS = (("entry", "event"), ("node", "node"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.clocks", "scalar clocks", "scalar clocks", "PRESERVED"),)
NEAR = (("own_neg", "R078_FUTURE_PARENT"),)
MUTATIONS = (("C1", "R078_MISSING_PARENT", "parent_off_log", "near_missing"),
             ("C2", "R078_FUTURE_PARENT", "mut", "mut"),
             ("C3", "R078_CLOCK_NOT_MONOTONE", "clock_stalls", "near_clock"),
             ("C4", "R078_NODE_ORDER", "node_repeats_clock", "near_node"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    entries, nodes = _sort(structure, "entry"), _sort(structure, "node")
    value = {int(e): int(Fraction(str(v))) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    logged = [e for e in entries if ["logged", [e]] in [[n, a] for n, a in rel]]
    at = {a[0]: a[1] for n, a in rel if n == "at"}
    return {"events": [[f"e{entries.index(e)}", f"n{nodes.index(at[e])}", value[e],
                        sorted(f"e{entries.index(a[1])}" for n, a in rel if n == "parent" and a[0] == e)]
                       for e in logged]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"entry:{k}", f"event:{e[0]}"] for k, e in enumerate(positive["events"])]
