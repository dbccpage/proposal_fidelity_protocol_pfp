"""Adapter for level 085: the engine's principal, scope, handoffs and routed
tasks written as the target checker's principal, principal scope,
handoffs (declared order) and tasks (declared order).  Agents and
permissions are named ``a<k>`` and ``p<k>`` by position; permission lists
are sorted.  Written against the registered stage-85 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_085"
CLAUSES = (("C1", "R085_AUTHORITY_EXPANSION"), ("C2", "R085_UNROOTED_DELEGATOR"), ("C3", "R085_TASK_OUTSIDE_SCOPE"))
COEFFICIENT_DOMAIN = {"source": "finite permission sets", "target": "finite permission sets"}
SORTS = (("agent", "agent"), ("perm", "permission"), ("handoff", "handoff"), ("task", "task"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.hierarchy", "exact permission names", "exact permission names", "PRESERVED"),)
NEAR = (("own_neg", "R085_AUTHORITY_EXPANSION"), ("mut", "R085_TASK_OUTSIDE_SCOPE"))
MUTATIONS = (("C1", "R085_AUTHORITY_EXPANSION", "scope_widened", "near_expand"),
             ("C2", "R085_UNROOTED_DELEGATOR", "delegator_unrooted", "near_unrooted"),
             ("C3", "R085_TASK_OUTSIDE_SCOPE", "task_outside", "near_task"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    agents, perms = _sort(structure, "agent"), _sort(structure, "perm")
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def ag(e: int) -> str:
        return f"a{agents.index(e)}"

    def pm(e: int) -> str:
        return f"p{perms.index(e)}"

    frm = {a[0]: a[1] for n, a in rel if n == "from"}
    to = {a[0]: a[1] for n, a in rel if n == "to"}
    return {"handoffs": [[ag(frm[h]), ag(to[h]), sorted(pm(a[1]) for n, a in rel if n == "hands" and a[0] == h)]
                         for h in _sort(structure, "handoff")],
            "principal": ag(next(a[0] for n, a in rel if n == "principal")),
            "principal_scope": sorted(pm(a[0]) for n, a in rel if n == "starts_with"),
            "tasks": [[ag(a[1]), pm(a[2])] for t in _sort(structure, "task") for n, a in rel
                      if n == "routes" and a[0] == t]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"handoff:{k}", f"handoff:{k}"] for k in range(len(positive["handoffs"]))]
