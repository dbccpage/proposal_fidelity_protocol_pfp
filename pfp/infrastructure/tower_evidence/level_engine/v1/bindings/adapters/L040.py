"""Adapter for level 040: the engine's players, moves, payoffs and claimed
stable joint moves written as the target checker's game and equilibria.
Players and moves are named by their positions in the declared order; a
joint move is written first player first.  Written against the registered
stage-40 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_040"
CLAUSES = (("C1", "R040_TABLE_GAP"), ("C2", "R040_PROFITABLE_DEVIATION"), ("C3", "R040_UNDEFINED_PROFILE"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("player", "player"), ("move", "move"), ("val", "payoff"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.players", "two players", "any number of players", "WEAKENED"),
             ("target.names", "players and moves as elements", "their positions as names", "PRESERVED"))
NEAR = (("own_neg", "R040_PROFITABLE_DEVIATION"),)
MUTATIONS = (("C1", "R040_TABLE_GAP", "deviation_unpaid", "near_gap"),
             ("C2", "R040_PROFITABLE_DEVIATION", "gainful_claim", "near_gain"),
             ("C3", "R040_UNDEFINED_PROFILE", "undefined_claim", "near_undefined"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def game_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    players, moves = _sort(structure, "player"), _sort(structure, "move")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def m(e: int) -> str:
        return f"m{moves.index(e)}"

    return {"equilibria": [[m(a[0]), m(a[1])] for n, a in rel if n == "stable"],
            "moves": [[f"p{k}", [m(a[1]) for n, a in rel if n == "owns" and a[0] == p]] for k, p in enumerate(players)],
            "payoffs": [[[m(a[0]), m(a[1])], [value[a[2]], value[a[3]]]] for n, a in rel if n == "pays"],
            "players": [f"p{k}" for k in range(len(players))]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": game_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": game_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": game_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"player:{k}", f"player:{p}"] for k, p in enumerate(positive["players"])]
