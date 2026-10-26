"""Adapter for level 094: the engine's components, ports, types and wires
written as the target checker's components (declared order, each with its
ports in declared order) and wires (declared order, ends as hosted).
Components, ports and types are named ``c<k>``, ``p<k>`` and ``T<k>`` by
position; a port no component owns is written under the component name
``none``.  Written against the registered stage-94 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_094"
CLAUSES = (("C1", "R094_UNKNOWN_PORT"), ("C2", "R094_OUTPUT_TO_OUTPUT"), ("C3", "R094_INPUT_TO_INPUT"),
           ("C4", "R094_TYPE_MISMATCH"), ("C5", "R094_ONE_WAY"))
COEFFICIENT_DOMAIN = {"source": "nominal message types", "target": "nominal message types"}
SORTS = (("component", "component"), ("port", "port"), ("msgtype", "message type"), ("wire", "wire"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.subtyping", "type equality is name equality", "no subtyping", "PRESERVED"),)
NEAR = (("own_neg", "R094_OUTPUT_TO_OUTPUT"),)
MUTATIONS = (("C1", "R094_UNKNOWN_PORT", "port_unknown", "near_unknown"),
             ("C2", "R094_OUTPUT_TO_OUTPUT", "outputs_joined", "near_outputs"),
             ("C3", "R094_INPUT_TO_INPUT", "inputs_joined", "near_inputs"),
             ("C4", "R094_TYPE_MISMATCH", "type_changed", "near_type"),
             ("C5", "R094_ONE_WAY", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    comps, ports, types = _sort(structure, "component"), _sort(structure, "port"), _sort(structure, "msgtype")
    rel = [(n, list(a)) for n, a in structure["relations"]]
    owner = {a[0]: a[1] for n, a in rel if n == "port_of"}
    sends = {a[0] for n, a in rel if n == "sends"}
    carries = {a[0]: a[1] for n, a in rel if n == "carries"}

    def end(p: int) -> str:
        c = f"c{comps.index(owner[p])}" if p in owner else "none"
        return f"{c}.p{ports.index(p)}"

    return {"components": [[f"c{k}", [[f"p{ports.index(p)}", "out" if p in sends else "in",
                                       f"T{types.index(carries[p])}"] for p in ports if owner.get(p) == c]]
                           for k, c in enumerate(comps)],
            "wires": [[end(a[1]), end(a[2])] for w in _sort(structure, "wire") for n, a in rel
                      if n == "joins" and a[0] == w]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"component:{k}", f"component:{c[0]}"] for k, c in enumerate(positive["components"])]
