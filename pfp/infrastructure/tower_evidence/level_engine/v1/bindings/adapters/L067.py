"""Adapter for level 067: the engine's questions, instances, map and offered
counts written as the target checker's families, bound, reduction and
evidence.  The question "is a multiple of 2" is the family ``even`` and "is
a multiple of 3" is ``multiple_of_3``; the bound is the largest instance;
the map is written in instance order, or ``null`` when there is none; each
offered count is written ``["count", v]``, or ``null`` when none is offered.
Written against the registered stage-67 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_067"
CLAUSES = (("C1", "R067_SURROGATE_EVIDENCE"), ("C2", "R067_NO_REDUCTION"), ("C3", "R067_NOT_TOTAL"),
           ("C4", "R067_NOT_PRESERVING"))
COEFFICIENT_DOMAIN = {"source": "natural numbers as exact values", "target": "natural numbers"}
SORTS = (("num", "instance"),)
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the reduction is the claim's own datum; its answers are what the checker decides"
LOSS_ROWS = (("target.families", "multiples of 2 or 3", "five named families", "WEAKENED"),
             ("target.evidence", "offered counts", "any offered keys, labels, counts or timings", "WEAKENED"))
FAMILY = {2: "even", 3: "multiple_of_3"}
NEAR = (("own_neg", "R067_SURROGATE_EVIDENCE"),)
MUTATIONS = (("C1", "R067_SURROGATE_EVIDENCE", "count_offered", "near_offered"),
             ("C2", "R067_NO_REDUCTION", "map_withdrawn", "near_no_map"),
             ("C3", "R067_NOT_TOTAL", "image_missing", "near_partial"), ("C4", "R067_NOT_PRESERVING", "mut", "mut"))


def fence_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    value = {int(e): int(Fraction(v)) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    insts = sorted(value[a[0]] for n, a in rel if n == "instance")
    sends = sorted([value[a[0]], value[a[1]]] for n, a in rel if n == "sends")
    offered = [["count", str(value[a[0]])] for n, a in rel if n == "offered"]
    source = next(value[a[0]] for n, a in rel if n == "source_mod")
    target = next(value[a[0]] for n, a in rel if n == "target_mod")
    return {"bound": insts[-1], "evidence": offered or None, "reduction": sends or None,
            "source": FAMILY[source], "target": FAMILY[target]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": fence_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": fence_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": fence_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"instance:{k}", f"instance:{k}"] for k in range(positive["bound"] + 1)]
