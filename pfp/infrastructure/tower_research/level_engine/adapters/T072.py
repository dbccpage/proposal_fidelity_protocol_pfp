# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 072's research-tree replay: the replayed corners, oriented
edges, faces, edge rows, face rows, rim and counts off the rim are the target
checker's vertices, edges, faces, d0, d1, rim edges, rim vertices and relative
counts.  Each row entry (minus one, zero or one) is written as a canonical
rational.  Written against the registered stage-72 checker.

The witness is natural_sections' chord square (two_complex.py and its
committed receipt).  The registry's named witness, native_structure's NS-6,
is not used: its two-cells are four-sided two-step squares on the sealed
step, read only through cochain pairings, and it has no rim.

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_072"
CLAUSES = (("C1", "R072_NOT_A_COMPLEX"), ("C2", "R072_NOT_NILPOTENT"), ("C3", "R072_INCIDENCE"),
           ("C4", "R072_RIM"), ("C5", "R072_RELATIVE_COUNT"))
COEFFICIENT_DOMAIN = {"source": "the tree's face sums over the integers mod 2, 3 and 4",
                      "target": "exact rationals"}
SORTS = (("corner", "vertex"), ("edge", "edge"), ("face", "face"))
UNMAPPED_SORTS = ("presentation token", "edge-value assignment", "modulus")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("source.faces", "the faces named in the tree's committed receipt (T1=0-1-3, T2=0-3-2)",
     "faces [0, 1, 3] and [0, 3, 2]", "PRESERVED"),
    ("target.d0", "the tree's edge equation theta[a] + w = theta[b] over its DIRECTED orientations",
     "edge rows computed by the replay: -1 at the source vertex, +1 at the target", "PRESERVED"),
    ("target.d1", "the tree's face sums flux_t1, flux_t2 on single-edge assignments, mod 2, 3 and 4",
     "face rows lifted by the replay to -1, 0, 1 (read at modulus 4) and written as rationals", "WEAKENED"),
    ("target.rim_edges", "edges with exactly one nonzero face sum, equal to the support of flux_outer",
     "rim edges [0, 1, 2, 3] computed by the replay", "PRESERVED"),
    ("target.rim_vertices", "not stated by the tree", "the ends of the rim edges, computed by the replay: all four",
     "PRESERVED"),
    ("target.relative", "not stated by the tree", "counts off the rim computed by the replay: [0, 1, 2]",
     "WEAKENED"),
    ("source.lean_two_complex", "the tree's Lean (TwoComplex) works over any abelian group of edge phases",
     "not cited; the replay rests on the tree's Python", "DROPPED"),
    ("source.named_witness", "the registry's named witness, native_structure NS-6 (boundary_boundary, "
     "boundary_zero_iff_commutes): four-sided squares on the sealed step, no rim",
     "not used; the replay uses natural_sections' chord square", "DROPPED"),
)
NEAR = (("own_neg", "R072_RIM"), ("near_face", "R072_NOT_A_COMPLEX"), ("near_row_dropped", "R072_INCIDENCE"),
        ("near_turned", "R072_INCIDENCE"), ("near_rim_corner", "R072_RIM"), ("near_counts", "R072_RELATIVE_COUNT"))
MUTATIONS = (("C1", "R072_NOT_A_COMPLEX", "face_repeats_corner", "near_face"),
             ("C2", "R072_NOT_NILPOTENT", "mut", "mut"),
             ("C3", "R072_INCIDENCE", "face_row_dropped", "near_row_dropped"),
             ("C4", "R072_RIM", "chord_on_rim", "own_neg"),
             ("C5", "R072_RELATIVE_COUNT", "chord_not_counted", "near_counts"))
TEXT = {1: "1/1", -1: "-1/1", 0: "0/1"}


def packet_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    packet = obj["packet"]
    assert isinstance(packet, dict)
    return copy.deepcopy(dict(packet))


def payload_of(obj: object) -> dict[str, Any]:
    pk = packet_of(obj)
    return {"d0": [[TEXT[x] for x in row] for row in pk["edge_rows"]],
            "d1": [[TEXT[x] for x in row] for row in pk["face_rows"]],
            "edges": pk["edges"], "faces": pk["faces"], "relative": pk["off_rim"],
            "rim_edges": pk["rim_edges"], "rim_vertices": pk["rim_corners"], "vertices": pk["corners"]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": payload_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": payload_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": payload_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"corner:{v}", f"vertex:{v}"] for v in positive["vertices"]]
