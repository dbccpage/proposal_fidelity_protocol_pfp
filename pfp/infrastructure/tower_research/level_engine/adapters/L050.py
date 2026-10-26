# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 050: the engine's table, eigenvalues and split written as
the target checker's table and projectors.  Slots and outcomes follow the
declared order; each projector is written ``[eigenvalue, table]``.  Written
against the registered stage-50 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_050"
CLAUSES = (("C1", "R050_NONREAL_EIGENVALUES"), ("C2", "R050_NOT_SELF_MIRRORED"), ("C3", "R050_SQUARE"),
           ("C4", "R050_PROJECTOR"), ("C5", "R050_INCOMPLETE"), ("C6", "R050_SPECTRAL"))
COEFFICIENT_DOMAIN = {"source": "exact pairs of rationals", "target": "exact pairs of rationals"}
SORTS = (("slot", "frame slot"), ("outcome", "projector"), ("val", "rational"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.names", "outcomes as elements", "the projector list's order", "PRESERVED"),)
NEAR = (("own_neg", "R050_NONREAL_EIGENVALUES"),)
MUTATIONS = (("C1", "R050_NONREAL_EIGENVALUES", "quarter_turn", "own_neg"),
             ("C2", "R050_NOT_SELF_MIRRORED", "not_self_mirrored", "near_mirror"),
             ("C3", "R050_SQUARE", "square_not_unit", "near_square"),
             ("C4", "R050_PROJECTOR", "member_not_self_mirrored", "near_member"),
             ("C5", "R050_INCOMPLETE", "member_repeated", "near_extra_member"), ("C6", "R050_SPECTRAL", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def square_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    slots, outs = _sort(structure, "slot"), _sort(structure, "outcome")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    cell = {(a[0], a[1]): [value[a[2]], value[a[3]]] for n, a in rel if n == "cell"}
    split = {(a[0], a[1], a[2]): [value[a[3]], value[a[4]]] for n, a in rel if n == "split"}
    eigen = {a[0]: value[a[1]] for n, a in rel if n == "eigen"}
    return {"projectors": [[eigen[k], [[split[(k, i, j)] for j in slots] for i in slots]] for k in outs],
            "table": [[cell[(i, j)] for j in slots] for i in slots]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": square_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": square_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": square_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"outcome:{k}", f"projector:{k}"] for k in range(len(positive["projectors"]))]
