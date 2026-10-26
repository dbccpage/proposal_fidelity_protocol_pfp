"""Adapter for level 080: the engine's authority, grant table and decided
requests written as the target checker's authority, grants (sorted) and
requests (declared order).  Parties, resources and actions are named
``party<k>``, ``res<k>`` and ``act<k>`` by position; a name hosted as a
pattern is written with ``*`` (``res<k>/*``, ``act<k>*``).  Written against
the registered stage-80 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_080"
CLAUSES = (("C1", "R080_ESCALATION"), ("C2", "R080_INEXACT_GRANT"), ("C3", "R080_UNGRANTED_ALLOW"),
           ("C4", "R080_DECISION_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "exact names", "target": "exact strings"}
SORTS = (("party", "principal"), ("resource", "resource"), ("action", "action"), ("request", "request"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.authentication", "the authority is taken as given", "not authenticated here", "PRESERVED"),)
NEAR = (("own_neg", "R080_ESCALATION"),)
MUTATIONS = (("C1", "R080_ESCALATION", "self_issued", "near_escalation"),
             ("C2", "R080_INEXACT_GRANT", "pattern_granted", "near_pattern"),
             ("C3", "R080_UNGRANTED_ALLOW", "allowed_ungranted", "near_ungranted"),
             ("C4", "R080_DECISION_MISMATCH", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    rel = [(n, list(a)) for n, a in structure["relations"]]
    patterns = {a[0] for n, a in rel if n == "pattern"}
    names: dict[int, str] = {}
    for sort, prefix, star in (("party", "party", ""), ("resource", "res", "/*"), ("action", "act", "*")):
        for k, e in enumerate(_sort(structure, sort)):
            names[e] = f"{prefix}{k}" + (star if e in patterns else "")
    decision = {a[0]: n for n, a in rel if n in ("allow", "deny")}
    reqs = {a[0]: a[1:] for n, a in rel if n == "request_of"}
    return {"authority": names[next(a[0] for n, a in rel if n == "authority")],
            "grants": sorted([names[x] for x in a] for n, a in rel if n == "grants"),
            "requests": [[names[x] for x in reqs[q]] + [decision[q]] for q in _sort(structure, "request")
                         if q in reqs and q in decision]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"request:{k}", f"request_row:{k}"] for k in range(len(positive["requests"]))]
