"""Adapter for level 047: the engine's stated pairs written as the target
checker's operands and claimed results.  A pair ``left(a, b)`` is written
``[a, b]``; ``left`` and ``right`` are the operands ``x`` and ``y``, and each
stated result is the claim of the same name.  Written against the
registered stage-47 checker.

C1 (a decimal scalar) is not claimed: exact intake refuses a decimal before
anything is hosted, so no engine fixture can state one.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_047"
CLAUSES = (("C2", "R047_SUM"), ("C3", "R047_PRODUCT"), ("C4", "R047_MIRROR"))
COEFFICIENT_DOMAIN = {"source": "exact pairs of rationals", "target": "exact pairs of rationals"}
SORTS = (("val", "rational"),)
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.decimal_refusal", "exact values only; a decimal never enters", "a decimal is refused by code",
              "WEAKENED"),)
NAMES = (("left", "x"), ("right", "y"), ("sum", "sum"), ("product", "product"), ("left_mirror", "mirror_x"),
         ("right_mirror", "mirror_y"))
NEAR = (("own_neg", "R047_PRODUCT"), ("near_sum", "R047_SUM"))
MUTATIONS = (("C2", "R047_SUM", "sum_off", "near_sum"), ("C3", "R047_PRODUCT", "mut", "mut"),
             ("C4", "R047_MIRROR", "mirror_off", "near_mirror"))


def claims_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    value = {int(e): str(v) for e, v in structure["values"]}
    got = {n: [value[a[0]], value[a[1]]] for n, a in structure["relations"]}
    return {target: got[source] for source, target in NAMES}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claims_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claims_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claims_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"pair:{source}", f"field:{target}"] for source, target in NAMES]
