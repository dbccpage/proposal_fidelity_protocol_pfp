"""Test-only adapter: the arc challenge's fixtures stated for the draft
checker beside it (the draft schema is the harness's own, so the payloads
are the draft inputs).  Never an adapter of record.

AuthorityEffect: None
"""
from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "draft_edge_endpoints"
CLAUSES = (("C1", "R002D_ABSENT"), ("C2", "R002D_COLLAPSED"))
COEFFICIENT_DOMAIN = {"source": "boolean-derivability+nat-costs", "target": "draft input"}
SORTS = (("element", "element index"), ("claim form", "relation"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
NEAR = {"near_source": "R002D_SOURCE", "near_target": "R002D_TARGET", "near_protect": "R002D_COLLAPSED"}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    pos = by["pos"]
    assert isinstance(pos, dict)
    absent = copy.deepcopy(pos)
    absent["relations"][0][1][1] = 3
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": pos}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": by[fid]} for fid, code in NEAR.items()]
    out.append({"clause": "C2", "expected_code": "R002D_COLLAPSED", "id": "mut", "kind": "decisive_mutation",
                "payload": by["mut"], "repair": "pos"})
    out.append({"clause": "C1", "expected_code": "R002D_ABSENT", "id": "mut_absent", "kind": "decisive_mutation",
                "payload": absent, "repair": "pos"})
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    n = sum(count for _, count in positive["sorts"])
    return [[f"element:{i}", f"node:{i}"] for i in range(n)]
