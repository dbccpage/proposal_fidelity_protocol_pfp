"""Adapter for level 038: the engine's model, observation, forcing, question,
twins and answer written as the target checker's exogenous variable,
equations, observation, intervention, query, twins and answer.  Variables
are named by their positions in the declared order (``V0`` is the
background); each equation's table lists the variable's value for its
parent's values 0 and 1.  Written against the registered stage-38 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_038"
CLAUSES = (("C1", "R038_REDRAWN_BACKGROUND"), ("C2", "R038_ABDUCTION_MISMATCH"), ("C3", "R038_ANSWER_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "two-valued variables", "target": "two-valued variables"}
SORTS = (("variable", "variable"), ("bit", "value"), ("twin", "twin"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.parents", "one background variable, one parent per variable", "any parents, any backgrounds",
              "WEAKENED"),)
NEAR = (("own_neg", "R038_REDRAWN_BACKGROUND"),)
MUTATIONS = (("C1", "R038_REDRAWN_BACKGROUND", "background_redrawn", "own_neg"),
             ("C2", "R038_ABDUCTION_MISMATCH", "twin_inconsistent", "near_abduction"), ("C3", "R038_ANSWER_MISMATCH", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def model_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    vs, bits, twins = _sort(structure, "variable"), _sort(structure, "bit"), _sort(structure, "twin")
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def name(v: int) -> str:
        return f"V{vs.index(v)}"

    parent = {a[0]: a[1] for n, a in rel if n == "parent"}
    table = {(a[0], bits.index(a[1])): bits.index(a[2]) for n, a in rel if n == "table"}
    factual = {a[0]: bits.index(a[1]) for n, a in rel if n == "factual"}
    counter = {a[0]: bits.index(a[1]) for n, a in rel if n == "counter"}
    forced = next([name(a[0]), bits.index(a[1])] for n, a in rel if n == "forced")
    return {"answer": sorted(bits.index(a[0]) for n, a in rel if n == "answer"),
            "equations": [[name(v), [name(parent[v])], [table[(v, 0)], table[(v, 1)]]] for v in vs[1:]],
            "exogenous": [name(vs[0])], "intervention": forced,
            "observation": [[name(a[0]), bits.index(a[1])] for n, a in rel if n == "observed"],
            "query": next(name(a[0]) for n, a in rel if n == "asked"),
            "twins": [[[factual[t]], [counter[t]]] for t in twins]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": model_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": model_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": model_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [["variable:0", f"exogenous:{positive['exogenous'][0]}"]] + \
        [[f"variable:{k + 1}", f"equation:{e[0]}"] for k, e in enumerate(positive["equations"])]
