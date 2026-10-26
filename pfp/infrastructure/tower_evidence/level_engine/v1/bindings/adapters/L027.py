"""Adapter for level 027: the engine's objects, self-maps, rebracketing
values and class mark written as the target checker's objects,
automorphisms, associator rows (sorted) and class.  Residues are positions
in declared order; the mark 0 is written "coboundary" and 1 "nontrivial".
Written against the registered stage-27 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_027"
CLAUSES = (("C1", "R027_TABLE_GAP"), ("C2", "R027_INCOHERENT"), ("C3", "R027_CLASS_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "integers mod m", "target": "integers mod m"}
SORTS = (("object", "object"), ("selfmap", "automorphism"), ("mark", "class"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.action", "trivial action", "trivial action", "PRESERVED"),)
NEAR = (("own_neg", "R027_INCOHERENT"),)
MUTATIONS = (("C1", "R027_TABLE_GAP", "row_dropped", "near_gap"),
             ("C2", "R027_INCOHERENT", "mut", "mut"),
             ("C3", "R027_CLASS_MISMATCH", "class_flipped", "near_class"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    objs, sms, (mk,) = _sort(structure, "object"), _sort(structure, "selfmap"), _sort(structure, "mark")
    value = {int(e): str(v) for e, v in structure["values"]}
    rows = sorted([objs.index(a[0]), objs.index(a[1]), objs.index(a[2]), sms.index(a[3])]
                  for n, a in structure["relations"] if n == "value")
    return {"associator": rows, "automorphisms": len(sms),
            "class": "coboundary" if value[mk] == "0/1" else "nontrivial", "objects": len(objs)}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"object:{k}", f"residue:{k}"] for k in range(positive["objects"])]
