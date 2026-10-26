# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 076: the engine's cells written as the target checker's
vertices, edges and faces.  Cells are named ``c<k>`` by their positions;
vertices, edges and faces follow the declared order; a face's terms are
sorted by edge name, each ``+`` or ``-``.  Written against the registered
stage-76 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_076"
CLAUSES = (("C1", "R076_DANGLING_EDGE"), ("C2", "R076_DANGLING_FACE"), ("C3", "R076_BOUNDARY_NOT_CLOSED"))
COEFFICIENT_DOMAIN = {"source": "integers", "target": "integers"}
SORTS = (("cell", "cell id"),)
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.boundary_maps", "derived from the cells", "derived from the cells", "PRESERVED"),)
NEAR = (("own_neg", "R076_DANGLING_EDGE"),)
MUTATIONS = (("C1", "R076_DANGLING_EDGE", "edge_dangles", "own_neg"),
             ("C2", "R076_DANGLING_FACE", "face_dangles", "near_face"),
             ("C3", "R076_BOUNDARY_NOT_CLOSED", "mut", "mut"))


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    rel = [(n, list(a)) for n, a in structure["relations"]]
    n_cells = sum(c for _, c in structure["sorts"])

    def nm(e: int) -> str:
        return f"c{e}"

    vertices = [c for c in range(n_cells) if ["vertex", [c]] in [[n, a] for n, a in rel]]
    edges = {a[0]: a for n, a in rel if n == "edge"}
    faces = [a[0] for n, a in rel if n == "face"]
    return {"edges": [[nm(e), nm(edges[e][1]), nm(edges[e][2])] for e in sorted(edges)],
            "faces": [[nm(f), sorted([nm(a[1]), "+" if n == "plus" else "-"] for n, a in rel
                                     if n in ("plus", "minus") and a[0] == f)] for f in faces],
            "vertices": [nm(v) for v in vertices]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"cell:{v}", f"vertex:{v}"] for v in positive["vertices"]]
