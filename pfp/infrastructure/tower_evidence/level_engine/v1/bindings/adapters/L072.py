"""Adapter for level 072: the engine's cells, claimed tables, rim and cells
off the rim written as the target checker's complex, tables, rim and
relative counts.  Vertices, edges and faces are named by their positions in
the declared order; each claimed table entry is one, minus one or zero; the
relative counts are the numbers of cells declared off the rim.  Written
against the registered stage-72 checker.

C3 (tables that compose to zero but differ from the cells) is not claimed:
every single edit of a claimed table breaks the composite first, so no
decisive mutation reaches it; the near-miss with both tables empty shows the
checker refusing it.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_072"
CLAUSES = (("C1", "R072_NOT_A_COMPLEX"), ("C2", "R072_NOT_NILPOTENT"), ("C4", "R072_RIM"), ("C5", "R072_RELATIVE_COUNT"))
COEFFICIENT_DOMAIN = {"source": "integer incidence", "target": "exact rationals"}
SORTS = (("vertex", "vertex"), ("edge", "edge"), ("face", "face"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.relative", "the cells declared off the rim", "their counts", "WEAKENED"),)
NEAR = (("own_neg", "R072_RIM"), ("near_tables", "R072_INCIDENCE"))
MUTATIONS = (("C1", "R072_NOT_A_COMPLEX", "face_repeats_vertex", "near_complex"),
             ("C2", "R072_NOT_NILPOTENT", "edge_table_loses_an_end", "near_nil"),
             ("C4", "R072_RIM", "diagonal_on_rim", "own_neg"), ("C5", "R072_RELATIVE_COUNT", "mut", "mut"))
TEXT = {1: "1/1", -1: "-1/1", 0: "0/1"}


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def cochains_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    vs, es, fs = _sort(structure, "vertex"), _sort(structure, "edge"), _sort(structure, "face")
    rel = {(n, tuple(a)) for n, a in structure["relations"]}
    ends = {a[0]: [vs.index(a[1]), vs.index(a[2])] for n, a in rel if n == "ends"}
    faces = {a[0]: [vs.index(x) for x in a[1:]] for n, a in rel if n == "face_of"}

    def table(name: str, rows: list[int], cols: list[int]) -> list[list[str]]:
        return [[TEXT[int((f"{name}_plus", (r, c)) in rel) - int((f"{name}_minus", (r, c)) in rel)] for c in cols]
                for r in rows]

    def marked(name: str, sort: list[int]) -> list[int]:
        return sorted(sort.index(a[0]) for n, a in rel if n == name)

    return {"d0": table("d0", es, vs), "d1": table("d1", fs, es), "edges": [ends[e] for e in es],
            "faces": [faces[f] for f in fs],
            "relative": [len(marked("inner_vertex", vs)), len(marked("inner_edge", es)), len(marked("inner_face", fs))],
            "rim_edges": marked("rim_edge", es), "rim_vertices": marked("rim_vertex", vs),
            "vertices": list(range(len(vs)))}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": cochains_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": cochains_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": cochains_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"vertex:{v}", f"vertex:{v}"] for v in positive["vertices"]]
