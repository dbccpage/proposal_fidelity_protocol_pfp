"""Adapter for level 077: the engine's base, schedule and receipts written as
the target checker's base, schedule and receipts.  Transactions, keys and
tokens are named ``t<i>``, ``k<i>`` and ``v<i>`` by position (the names the
engine's state digests are computed over); operations and receipts follow
the declared order; stamps are written as their hosted digests, never
recomputed here.  Written against the registered stage-77 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_077"
CLAUSES = (("C1", "R077_UNCOMMITTED_CONFLICT"), ("C2", "R077_CONFLICT_CYCLE"), ("C3", "R077_ORDER"),
           ("C4", "R077_PARENT_DIGEST"), ("C5", "R077_STATE_DIGEST"))
COEFFICIENT_DOMAIN = {"source": "SHA-256 digests as exact 32-byte values",
                      "target": "SHA-256 digests as exact 32-byte values"}
SORTS = (("txn", "transaction"), ("key", "key"), ("token", "value"), ("op", "operation"), ("receipt", "receipt"),
         ("stamp", "digest"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.names", "transactions, keys and tokens by position", "strings t<i>, k<i>, v<i>",
              "PRESERVED"),)
NEAR = (("own_neg", "R077_UNCOMMITTED_CONFLICT"), ("mut", "R077_ORDER"))
MUTATIONS = (("C1", "R077_UNCOMMITTED_CONFLICT", "dirty_write", "near_dirty"),
             ("C2", "R077_CONFLICT_CYCLE", "conflicts_cycle", "near_cycle"),
             ("C3", "R077_ORDER", "receipt_repeats", "near_order"),
             ("C4", "R077_PARENT_DIGEST", "parent_changed", "near_parent"),
             ("C5", "R077_STATE_DIGEST", "state_changed", "near_state"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    txns, keys, tokens = _sort(structure, "txn"), _sort(structure, "key"), _sort(structure, "token")
    digest = {int(e): str(d) for e, d in structure["digests"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    acts = {a[0]: f"t{txns.index(a[1])}" for n, a in rel if n == "acts"}
    schedule = []
    for o in _sort(structure, "op"):
        for n, a in rel:
            if a[0] != o:
                continue
            if n == "reads":
                schedule.append([acts[o], "r", f"k{keys.index(a[1])}"])
            elif n == "writes":
                schedule.append([acts[o], "w", f"k{keys.index(a[1])}", f"v{tokens.index(a[2])}"])
            elif n == "commits":
                schedule.append([acts[o], "c"])
            elif n == "aborts":
                schedule.append([acts[o], "a"])
    rfor = {a[0]: f"t{txns.index(a[1])}" for n, a in rel if n == "receipt_for"}
    par = {a[0]: digest[a[1]] for n, a in rel if n == "parent_stamp"}
    sta = {a[0]: digest[a[1]] for n, a in rel if n == "state_stamp"}
    return {"base": {f"k{keys.index(a[0])}": f"v{tokens.index(a[1])}" for n, a in rel if n == "base"},
            "receipts": [{"digest": sta[r], "parent_digest": par[r], "txn": rfor[r]}
                         for r in _sort(structure, "receipt")],
            "schedule": schedule}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"receipt:{k}", f"receipt:{k}"] for k in range(len(positive["receipts"]))]
