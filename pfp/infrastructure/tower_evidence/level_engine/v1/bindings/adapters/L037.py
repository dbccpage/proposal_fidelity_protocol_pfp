"""Adapter for level 037: the engine's sources, variables, parents, firing
indices, treatment, outcome and claimed differences written as the target
checker's exogenous bits, equations (parents in declared order, sources
first; truth tables in binary order) and report.  Sources and variables are
named ``u<k>`` and ``v<k>`` by their positions.  Written against the
registered stage-37 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_037"
CLAUSES = (("C1", "R037_CYCLIC"), ("C2", "R037_OBSERVATION_MISMATCH"), ("C3", "R037_OBSERVATION_AS_FORCED"),
           ("C4", "R037_FORCED_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("source", "exogenous bit"), ("variable", "variable"), ("pattern", "truth-table index"),
         ("observed", "observed difference"), ("forced", "forced difference"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.difference_measure", "risk differences only", "risk differences only", "PRESERVED"),)
NEAR = (("own_neg", "R037_OBSERVATION_AS_FORCED"), ("mut", "R037_OBSERVATION_MISMATCH"))
MUTATIONS = (("C1", "R037_CYCLIC", "parent_looped", "near_cycle"),
             ("C2", "R037_OBSERVATION_MISMATCH", "observed_changed", "near_observed"),
             ("C3", "R037_OBSERVATION_AS_FORCED", "observation_relabelled", "own_neg"),
             ("C4", "R037_FORCED_MISMATCH", "forced_changed", "near_forced"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    src, var = _sort(structure, "source"), _sort(structure, "variable")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    nodes = src + var

    def nm(e: int) -> str:
        return f"u{src.index(e)}" if e in src else f"v{var.index(e)}"

    eqs = []
    for v in var:
        parents = sorted((a[1] for n, a in rel if n == "parent" and a[0] == v), key=nodes.index)
        fired = {int(value[a[1]].split("/")[0]) for n, a in rel if n == "fires" and a[0] == v}
        eqs.append([nm(v), [nm(p) for p in parents], [1 if k in fired else 0 for k in range(2 ** len(parents))]])
    obs = _sort(structure, "observed")
    return {"equations": eqs, "exogenous": [nm(u) for u in src],
            "report": [nm(next(a[0] for n, a in rel if n == "treatment")),
                       nm(next(a[0] for n, a in rel if n == "outcome")),
                       value[obs[0]] if obs else None, value[_sort(structure, "forced")[0]]]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"variable:{k}", f"variable:{e[0]}"] for k, e in enumerate(positive["equations"])]
