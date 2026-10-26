# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 018: the engine's hosted complex and its split written as
the target checker's incidence matrices and vectors.  ``d0`` has one row per
side in the declared order of sides and one column per point (``-1`` at the
tail, ``+1`` at the head); ``d1`` has one row per cell (``+1`` for
``rim_with``, ``-1`` for ``rim_against``); the cochain is 1 on each marked
side and 0 elsewhere; the potential, copotential and harmonic parts are the
exact values of the points, cells and sides.  A complex that states no tail
and no head at all has no ``d0``: it is written ``null``.  Written against
the registered stage-18 checker (``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_018"
CLAUSES = (("C1", "R018_NO_MATRICES"), ("C2", "R018_BOARD_INVALID"), ("C3", "R018_NOT_HARMONIC"),
           ("C4", "R018_RECONSTRUCTION"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("point", "vertex"), ("side", "edge"), ("cell", "2-cell"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.cochain", "a load of 1 on marked sides", "a rational cochain; only 0/1 loads are stated", "WEAKENED"),
    ("target.absent_incidence", "no tail and no head stated", "d0 written null", "PRESERVED"),
)
NEAR = (("near_mark", "R018_RECONSTRUCTION"), ("near_rim", "R018_BOARD_INVALID"))
MUTATIONS = (("C1", "R018_NO_MATRICES", "mut", "mut"),
             ("C2", "R018_BOARD_INVALID", "open_rim", "near_rim"),
             ("C3", "R018_NOT_HARMONIC", "unbalanced_part", "near_balance"),
             ("C4", "R018_RECONSTRUCTION", "second_mark", "near_mark"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def _sign(x: int) -> str:
    return f"{x}/1"


def split_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    points, sides, cells = _sort(structure, "point"), _sort(structure, "side"), _sort(structure, "cell")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(name, tuple(args)) for name, args in structure["relations"]]
    tails = {a[0]: a[1] for n, a in rel if n == "tail"}
    heads = {a[0]: a[1] for n, a in rel if n == "head"}
    with_ = {a for n, a in rel if n == "rim_with"}
    against = {a for n, a in rel if n == "rim_against"}
    marked = {a[0] for n, a in rel if n == "marked"}
    d0 = None if not tails and not heads else [
        [_sign((heads.get(e) == v) - (tails.get(e) == v)) for v in points] for e in sides]
    return {
        "cochain": ["1/1" if e in marked else "0/1" for e in sides],
        "copotential": [value[c] for c in cells],
        "d0": d0,
        "d1": [[_sign(((c, e) in with_) - ((c, e) in against)) for e in sides] for c in cells],
        "harmonic": [value[e] for e in sides],
        "potential": [value[v] for v in points],
    }


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": split_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": split_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": split_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"element:{v}", f"vertex:{v}"] for v in range(len(positive["potential"]))]
