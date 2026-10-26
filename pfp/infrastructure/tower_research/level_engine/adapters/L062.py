# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 062: the engine's corners, links, steps and claimed
product written as the target checker's objects, edges and one face.
Corners, links and labels are named by their positions in the declared
order; the face lists its steps in declared step order, each ``+`` along its
link or ``-`` against it (a step that reads no link contributes none).
Written against the registered stage-62 checker.

C1 (a step naming an undeclared edge) is not claimed: a hosted step reads a
hosted link, so no engine fixture can name an undeclared one.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_062"
CLAUSES = (("C2", "R062_OPEN_WALK"), ("C3", "R062_PRODUCT"))
COEFFICIENT_DOMAIN = {"source": "permutations of a finite label set", "target": "permutations of a finite label set"}
SORTS = (("label", "label"), ("corner", "object"), ("link", "edge"), ("step", "face step"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.faces", "one face per claim", "any number of faces", "WEAKENED"),
             ("target.edge_names", "steps read hosted links", "an undeclared edge refused by code", "WEAKENED"))
NEAR = (("own_neg", "R062_OPEN_WALK"), ("near_order", "R062_PRODUCT"))
MUTATIONS = (("C2", "R062_OPEN_WALK", "walk_left_open", "near_open"), ("C3", "R062_PRODUCT", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def face_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    labels, corners = _sort(structure, "label"), _sort(structure, "corner")
    links, steps = _sort(structure, "link"), _sort(structure, "step")
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def end(name: str, e: int) -> str:
        return next(str(corners.index(a[1])) for n, a in rel if n == name and a[0] == e)

    def images(e: int) -> list[int]:
        got = {labels.index(a[1]): labels.index(a[2]) for n, a in rel if n == "moves" and a[0] == e}
        return [got[k] for k in range(len(labels))]

    walk = [[f"e{links.index(a[1])}", "+" if n == "along" else "-"]
            for w in steps for n, a in rel if n in ("along", "against") and a[0] == w]
    claim = {labels.index(a[0]): labels.index(a[1]) for n, a in rel if n == "product"}
    return {"edges": [[f"e{k}", end("from", e), end("to", e), images(e)] for k, e in enumerate(links)],
            "faces": [[walk, [claim[k] for k in range(len(labels))]]], "labels": len(labels),
            "objects": [str(k) for k in range(len(corners))]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": face_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": face_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": face_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"link:{k}", f"edge:{e[0]}"] for k, e in enumerate(positive["edges"])]
