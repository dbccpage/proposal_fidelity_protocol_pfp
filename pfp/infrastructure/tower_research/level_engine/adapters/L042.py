# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 042: the engine's two endpoints written as the target
checker's left and right endpoints.  States and kinds are named by their
positions in the declared order; each endpoint's moves are listed by state,
then kind, then action.  Written against the registered stage-42 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_042"
CLAUSES = (("C1", "R042_BOTH_RECEIVE"), ("C2", "R042_UNMATCHED_SEND"), ("C3", "R042_STUCK"), ("C4", "R042_NO_END"))
COEFFICIENT_DOMAIN = {"source": "finite endpoint automata", "target": "finite endpoint automata"}
SORTS = (("here", "left state"), ("there", "right state"), ("kind", "message kind"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.names", "states and kinds as elements", "their positions as names", "PRESERVED"),)
NEAR = (("own_neg", "R042_BOTH_RECEIVE"),)
MUTATIONS = (("C1", "R042_BOTH_RECEIVE", "both_wait", "own_neg"), ("C2", "R042_UNMATCHED_SEND", "send_unmatched", "near_unmatched"),
             ("C3", "R042_STUCK", "stuck_state", "near_stuck"), ("C4", "R042_NO_END", "no_end", "near_no_end"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def endpoints_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    kinds = _sort(structure, "kind")
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def side(name: str, letter: str) -> dict[str, Any]:
        states = _sort(structure, name)

        def s(e: int) -> str:
            return f"{letter}{states.index(e)}"

        moves = sorted((states.index(a[0]), kinds.index(a[1]), action, s(a[2]))
                       for action in ("send", "receive") for n, a in rel if n == f"{name}_{action}")
        return {"final": [s(a[0]) for n, a in rel if n == f"{name}_final"],
                "moves": [[f"{letter}{st}", action, f"k{k}", nxt] for st, k, action, nxt in moves],
                "start": next(s(a[0]) for n, a in rel if n == f"{name}_start")}

    return {"left": side("here", "s"), "right": side("there", "t")}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": endpoints_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": endpoints_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": endpoints_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [["here:start", f"left:{positive['left']['start']}"], ["there:start", f"right:{positive['right']['start']}"]]
