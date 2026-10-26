"""Adapter for level 021: the engine's hosted cell, turns and loops written as
the target checker's squared lengths, generators and loops.  Corners are
vertices 0 to 4 in the declared order; each squared length is written
``[u, v, value]``; each turn is a generator named by its token, whose 4 by 4
table has column ``a`` equal to the signed image of axis ``a`` and the fourth
axis fixed; a one-turn loop is the word ``[g]`` and a bracket loop the word
``[g, h, g-, h-]``; every loop takes the hinge's three corners; a loop
declared closed is written ``identity``, any other ``nontrivial``.  Written
against the registered stage-21 checker (``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_021"
CLAUSES = (("C1", "R021_GRAM_NOT_POSITIVE"), ("C2", "R021_NOT_ROTATION"), ("C3", "R021_SCALAR_SUM_CLOSURE"),
           ("C4", "R021_CLOSURE_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("corner", "vertex"), ("turn", "generator"), ("axis", "coordinate"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.fourth_axis", "turns of three axes, the fourth fixed", "4 by 4 rotations", "WEAKENED"),
    ("target.word_shapes", "one-turn loops and bracket loops", "any word of letters", "WEAKENED"),
    ("target.hinge", "one hinge for every loop", "a hinge per loop", "WEAKENED"),
)
NEAR = (("near_gram", "R021_GRAM_NOT_POSITIVE"), ("near_reflect", "R021_NOT_ROTATION"))
MUTATIONS = (("C1", "R021_GRAM_NOT_POSITIVE", "coincident_corners", "near_gram"),
             ("C2", "R021_NOT_ROTATION", "reflection", "near_reflect"),
             ("C3", "R021_SCALAR_SUM_CLOSURE", "bracket_declared_closed", "own_neg"),
             ("C4", "R021_CLOSURE_MISMATCH", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def cell_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    corners, axes, turns = _sort(structure, "corner"), _sort(structure, "axis"), _sort(structure, "turn")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(name, tuple(args)) for name, args in structure["relations"]]
    name = {g: f"turn{k}" for k, g in enumerate(turns)}

    def table(g: int) -> list[list[str]]:
        flips = {a[1] for n, a in rel if n == "flips" and a[0] == g}
        m = [["0/1"] * 4 for _ in range(4)]
        for n, a in rel:
            if n == "image" and a[0] == g:
                m[axes.index(a[2])][axes.index(a[1])] = "-1/1" if a[1] in flips else "1/1"
        m[3][3] = "1/1"
        return m

    hinge = [corners.index(a[0]) for n, a in rel if n == "hinge"]
    single_shut = {a[0] for n, a in rel if n == "single_shut"}
    bracket_shut = {a for n, a in rel if n == "bracket_shut"}
    loops = [{"closure": "identity" if a[0] in single_shut else "nontrivial", "hinge": hinge,
              "word": [name[a[0]]]} for n, a in rel if n == "single"]
    loops += [{"closure": "identity" if a in bracket_shut else "nontrivial", "hinge": hinge,
               "word": [name[a[0]], name[a[1]], name[a[0]] + "-", name[a[1]] + "-"]} for n, a in rel if n == "bracket"]
    return {
        "generators": [[name[g], table(g)] for g in turns],
        "loops": loops,
        "squared_lengths": sorted([corners.index(a[0]), corners.index(a[1]), value[a[2]]]
                                  for n, a in rel if n == "span"),
    }


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": cell_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": cell_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": cell_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"element:{k}", f"vertex:{k}"] for k in range(5)]
