"""Adapter for level 049: the engine's frames, named frame, coordinates and
row written as the target checker's frames, frame name, coordinates and
row.  Frames are named by their positions in the declared order; a claim
that names no frame is written with the frame ``null``; the carrier is
always ``mirror_pairs``.  Written against the registered stage-49 checker.

C2 (a carrier tag contradicted by the entries) is not claimed: the engine
hosts one carrier, exact pairs, and states no tag.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_049"
CLAUSES = (("C1", "R049_UNNAMED_FRAME"), ("C3", "R049_FRAME_NOT_SIZE_KEEPING"), ("C4", "R049_NOT_UNIT"),
           ("C5", "R049_ROW_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "exact pairs of rationals", "target": "exact pairs of rationals"}
SORTS = (("frame", "frame name"), ("slot", "frame slot"), ("val", "rational"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.carrier_tag", "one carrier, exact pairs", "a declared carrier tag", "WEAKENED"),)
NEAR = (("near_other_frame", "R049_ROW_MISMATCH"),)
MUTATIONS = (("C1", "R049_UNNAMED_FRAME", "frame_unnamed", "own_neg"),
             ("C3", "R049_FRAME_NOT_SIZE_KEEPING", "frame_stretched", "near_frame"),
             ("C4", "R049_NOT_UNIT", "coordinates_off", "near_unit"), ("C5", "R049_ROW_MISMATCH", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def framed_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    frames, slots = _sort(structure, "frame"), _sort(structure, "slot")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    cell = {(a[0], a[1], a[2]): [value[a[3]], value[a[4]]] for n, a in rel if n == "cell"}

    def vec(name: str) -> list[list[str]]:
        got = {a[0]: [value[a[1]], value[a[2]]] for n, a in rel if n == name}
        return [got[s] for s in slots]

    name = [f"b{frames.index(a[0])}" for n, a in rel if n == "named"]
    return {"carrier": "mirror_pairs", "coordinates": vec("coord"), "frame": name[0] if name else None,
            "frames": [[f"b{k}", [[cell[(f, i, j)] for j in slots] for i in slots]] for k, f in enumerate(frames)],
            "row": vec("row")}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": framed_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": framed_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": framed_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"frame:{k}", f"frame:{f[0]}"] for k, f in enumerate(positive["frames"])]
