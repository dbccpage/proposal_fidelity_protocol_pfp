"""Adapter for level 025: the engine's objects, arrows, composition table,
weak class and roofs written as the target checker's objects, arrows,
identities, compose rows, weak list and roofs.  Objects and arrows are
named ``o<k>`` and ``a<k>`` by their positions; every row is written once
per hosted tuple, in the order of its element indices.  Written against
the registered stage-25 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_025"
CLAUSES = (("C1", "R025_NOT_A_CATEGORY"), ("C2", "R025_WEQ_NOT_CLOSED"), ("C3", "R025_UNTYPED_INVERSE"),
           ("C4", "R025_ROOF_TYPE"))
COEFFICIENT_DOMAIN = {"source": "finite composition tables", "target": "finite composition tables"}
SORTS = (("object", "object"), ("arrow", "arrow"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.names", "objects and arrows as elements", "their positions as names o<k>, a<k>", "PRESERVED"),
             ("target.localization", "classes of roofs and their composites not decided", "not decided",
              "PRESERVED"))
NEAR = (("own_neg", "R025_UNTYPED_INVERSE"), ("near_assoc", "R025_NOT_A_CATEGORY"),
        ("near_weak", "R025_WEQ_NOT_CLOSED"), ("near_roof_start", "R025_ROOF_TYPE"))
MUTATIONS = (("C1", "R025_NOT_A_CATEGORY", "composite_missing", "near_gap"),
             ("C2", "R025_WEQ_NOT_CLOSED", "mut", "mut"),
             ("C3", "R025_UNTYPED_INVERSE", "inverse_outside", "own_neg"),
             ("C4", "R025_ROOF_TYPE", "roof_end_moved", "near_roof"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def _names(structure: dict[str, Any]) -> dict[int, str]:
    out = {}
    for sort, prefix in (("object", "o"), ("arrow", "a")):
        for k, e in enumerate(_sort(structure, sort)):
            out[e] = f"{prefix}{k}"
    return out


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    nm = _names(structure)
    rel = sorted((n, list(a)) for n, a in structure["relations"])

    def rows(name: str) -> list[list[str]]:
        return [[nm[x] for x in a] for n, a in rel if n == name]

    return {
        "arrows": rows("runs"),
        "compose": rows("compose"),
        "identities": rows("identity"),
        "objects": [nm[o] for o in _sort(structure, "object")],
        "roofs": rows("roof"),
        "weak": [r[0] for r in rows("weak")],
    }


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"arrow:{k}", f"arrow:{a[0]}"] for k, a in enumerate(positive["arrows"])]
