"""Adapter for level 010: the engine's hosted table of steps and its claim
written as the target checker's evidence matrix and claim record.  The matrix
is the 0/1 table of arcs, rows and columns in the declared order of nodes;
the claim's value is the exact value it names; its reading is written
``reciprocal_pole`` for the first element of the ``kind`` sort and
``continuum_zero`` for the second; its scope is written ``finite_carrier``
for the first element of the ``reach`` sort and ``beyond_carrier`` for the
second.  Written against the registered stage-10 checker (``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_010"
CLAUSES = (("C1", "R010_CONTINUUM_CLAIM"), ("C2", "R010_SCOPE_ESCALATION"), ("C3", "R010_NOT_A_POLE"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("node", "row and column"), ("claim", "claim record"), ("val", "claimed value"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
KINDS = ("reciprocal_pole", "continuum_zero")
SCOPES = ("finite_carrier", "beyond_carrier")
LOSS_ROWS = (
    ("target.matrix_entries", "arcs as a relation", "a 0/1 matrix; multiple arcs are not presented", "WEAKENED"),
    ("target.claim_tags", "the reading and scope as elements of two sorts", "two strings", "PRESERVED"),
)


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def fence_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    nodes = _sort(structure, "node")
    kinds, reaches = _sort(structure, "kind"), _sort(structure, "reach")
    rel = [(name, list(args)) for name, args in structure["relations"]]
    arcs = {(a[0], a[1]) for name, a in rel if name == "arc"}
    value = {int(e): str(v) for e, v in structure["values"]}
    named = [a[1] for name, a in rel if name == "names"]
    kind = [a[1] for name, a in rel if name == "of_kind"]
    scope = [a[1] for name, a in rel if name == "in_scope"]
    return {
        "claim": {"kind": KINDS[kinds.index(kind[0])], "scope": SCOPES[reaches.index(scope[0])],
                  "value": value[named[0]]},
        "matrix": [[1 if (x, y) in arcs else 0 for y in nodes] for x in nodes],
    }


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    return [
        {"id": "pos", "kind": "positive", "payload": fence_of(by["pos"])},
        {"expected_code": "R010_NOT_A_POLE", "id": "near_value", "kind": "near_miss",
         "payload": fence_of(by["near_value"])},
        {"clause": "C1", "expected_code": "R010_CONTINUUM_CLAIM", "id": "relabelled", "kind": "decisive_mutation",
         "payload": fence_of(by["own_neg"]), "repair": "pos"},
        {"clause": "C2", "expected_code": "R010_SCOPE_ESCALATION", "id": "mut", "kind": "decisive_mutation",
         "payload": fence_of(by["mut"]), "repair": "pos"},
        {"clause": "C3", "expected_code": "R010_NOT_A_POLE", "id": "not_a_pole", "kind": "decisive_mutation",
         "payload": fence_of(by["near_value"]), "repair": "pos"},
    ]


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"element:{i}", f"row:{i}"] for i in range(len(positive["matrix"]))]
