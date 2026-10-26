# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 058: the engine's contexts, rules and choices written as
the target checker's labels, contexts and family.  Items, contexts and
labels are named by their positions in the declared order; a context lists
its items in declared item order, and its choice gives their labels in that
order (a member with no label contributes none).  Written against the
registered stage-58 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_058"
CLAUSES = (("C1", "R058_CONTEXT"), ("C2", "R058_LOCAL_RULE"), ("C3", "R058_OVERLAP"))
COEFFICIENT_DOMAIN = {"source": "finite labels", "target": "finite labels"}
SORTS = (("item", "item"), ("context", "context"), ("label", "label"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.names", "items, contexts and labels as elements", "their positions as names", "PRESERVED"),)
NEAR = (("own_neg", "R058_OVERLAP"),)
MUTATIONS = (("C1", "R058_CONTEXT", "member_unlabelled", "near_gap"),
             ("C2", "R058_LOCAL_RULE", "rule_broken", "near_rule"), ("C3", "R058_OVERLAP", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def scenario_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    items, ctxs, labels = _sort(structure, "item"), _sort(structure, "context"), _sort(structure, "label")
    rel = [(n, list(a)) for n, a in structure["relations"]]
    rule = {a[0]: n for n, a in rel if n in ("differ", "equal")}
    got = {(a[0], a[1]): labels.index(a[2]) for n, a in rel if n == "chooses"}
    members = {c: sorted(a[1] for n, a in rel if n == "member" and a[0] == c) for c in ctxs}
    return {"contexts": [[f"k{i}", [f"x{items.index(x)}" for x in members[c]], rule[c]] for i, c in enumerate(ctxs)],
            "family": [[f"k{i}", [got[(c, x)] for x in members[c] if (c, x) in got]] for i, c in enumerate(ctxs)],
            "labels": list(range(len(labels)))}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": scenario_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": scenario_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": scenario_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"context:{k}", f"context:{c[0]}"] for k, c in enumerate(positive["contexts"])]
