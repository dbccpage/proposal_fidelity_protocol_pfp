"""Adapter for level 019: the engine's hosted table and its record written as
the target checker's matrix, coefficients, roots, enclosures and scope.  The
matrix is the table in the declared order of slots; the coefficients are the
declared ones, highest power first; the roots and enclosures are the claimed
ones in the declared order of tuples; the scope is written ``finite_matrix``
for the first element of the ``reach`` sort and ``beyond_matrix`` for the
second.  Written against the registered stage-19 checker (``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_019"
CLAUSES = (("C1", "R019_POLYNOMIAL_MISMATCH"), ("C2", "R019_ROUNDED_ROOT"), ("C3", "R019_ENCLOSURE_INVALID"),
           ("C4", "R019_SCOPE_ESCALATION"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("slot", "row and column"), ("num", "exact value"), ("record", "polynomial record"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
SCOPES = ("finite_matrix", "beyond_matrix")
LOSS_ROWS = (
    ("target.coefficient_order", "coefficients keyed by power", "a list, highest power first", "PRESERVED"),
    ("target.scope_tag", "the scope as an element of a sort", "a string", "PRESERVED"),
)
NEAR = (("near_coef", "R019_POLYNOMIAL_MISMATCH"), ("near_root", "R019_ROUNDED_ROOT"),
        ("near_fence", "R019_ENCLOSURE_INVALID"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def record_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    slots, reaches = _sort(structure, "slot"), _sort(structure, "reach")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(name, list(args)) for name, args in structure["relations"]]
    entry = {(a[0], a[1]): value[a[2]] for name, a in rel if name == "entry"}
    coef = sorted(((int(value[a[0]].split("/")[0]), value[a[1]]) for name, a in rel if name == "coef"), reverse=True)
    scope = [a[1] for name, a in rel if name == "in_scope"]
    return {
        "coefficients": [v for _, v in coef],
        "enclosures": [[value[a[1]], value[a[2]]] for name, a in rel if name == "fence"],
        "matrix": [[entry[(i, j)] for j in slots] for i in slots],
        "roots": [value[a[1]] for name, a in rel if name == "root"],
        "scope": SCOPES[reaches.index(scope[0])],
    }


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": record_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": record_of(by[fid])}
            for fid, code in NEAR]
    out += [
        {"clause": "C1", "expected_code": "R019_POLYNOMIAL_MISMATCH", "id": "wrong_constant",
         "kind": "decisive_mutation", "payload": record_of(by["near_coef"]), "repair": "pos"},
        {"clause": "C2", "expected_code": "R019_ROUNDED_ROOT", "id": "false_root", "kind": "decisive_mutation",
         "payload": record_of(by["near_root"]), "repair": "pos"},
        {"clause": "C3", "expected_code": "R019_ENCLOSURE_INVALID", "id": "no_sign_change",
         "kind": "decisive_mutation", "payload": record_of(by["near_fence"]), "repair": "pos"},
        {"clause": "C4", "expected_code": "R019_SCOPE_ESCALATION", "id": "mut", "kind": "decisive_mutation",
         "payload": record_of(by["mut"]), "repair": "pos"},
    ]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"element:{i}", f"row:{i}"] for i in range(len(positive["matrix"]))]
