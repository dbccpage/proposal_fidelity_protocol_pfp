# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 062's research-tree replay: the replayed objects, edges
and faces (natural_sections' chord square at its separating assignment, and
its three-occupant run on the square with the recorded closed walk) are the
target checker's objects, edges and faces as they stand.  The chord square's
edge phases in Z_3 enter as the translations they act by (the tree's edge
equation: a flat section's value at the target is the source value plus the
phase); the run's hop transports are already permutations of sorted indices,
and its holonomy witness is a face with its claimed ordered product.
Written against the registered stage-62 checker.

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_062"
CLAUSES = (("C1", "R062_UNDECLARED_EDGE"), ("C2", "R062_OPEN_WALK"), ("C3", "R062_PRODUCT"))
COEFFICIENT_DOMAIN = {"source": "Z_3 edge phases (as translations) and permutations of three sorted indices",
                      "target": "permutations of a finite label set"}
SORTS = (("residue mod 3 / sorted index", "label"), ("corner / occupation", "object"), ("edge / hop", "edge"),
         ("face / closed walk", "face"))
UNMAPPED_SORTS = ("presentation token", "site", "corner potential")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.edge_transport", "a chord-square edge phase w in Z_3 (the tree's edge equation: target value = "
     "source value + w)", "the translation x -> x + w mod 3 of labels 0..2", "PRESERVED"),
    ("target.square_faces", "the faces 0-1-3 and 0-3-2 of the tree's receipt, each step's direction the sign "
     "of its edge in the tree's face sums", "two faces of ordered steps", "PRESERVED"),
    ("target.square_products", "the tree's face sums (flux_t1, flux_t2) at the separating assignment, 1 and 2",
     "the translations by those values, computed by the replay", "PRESERVED"),
    ("target.run_edges", "the run's hops in both directions, the reverse carrying the inverse (checked through "
     "the tree's hop_perm)", "one edge per hop, from the smaller occupation; the reverse read as a '-' step",
     "PRESERVED"),
    ("target.packet", "two separate witnesses of the tree, each on three labels",
     "one packet: their disjoint union on one label set", "PRESERVED"),
    ("target.run_face", "the receipt's recorded closed walk (a holonomy witness, not a face of a two-complex)",
     "a face of the checker", "WEAKENED"),
    ("source.abelian_square", "the chord square's transports commute", "ordered products; order is exercised by "
     "the run's walk only", "WEAKENED"),
    ("source.section_verdicts", "the tree's section verdicts: no corner values at the separating assignment, "
     "outer walk sum zero; the run's group of order 3 with no fixed pair", "not decided by the checker; "
     "reported beside the record", "DROPPED"),
    ("source.lean", "natural_sections' Lean (section_iff_faces_zero, outer_zero_but_obstructed, the closed-walk "
     "criterion)", "not cited; the replay rests on the tree's Python", "DROPPED"),
)
NEAR = (("own_neg", "R062_OPEN_WALK"), ("near_open", "R062_OPEN_WALK"), ("near_undeclared", "R062_UNDECLARED_EDGE"),
        ("near_order", "R062_PRODUCT"))
MUTATIONS = (("C1", "R062_UNDECLARED_EDGE", "edge_renamed", "near_undeclared"),
             ("C2", "R062_OPEN_WALK", "chord_dropped", "own_neg"),
             ("C3", "R062_PRODUCT", "mut", "mut"))


def packet_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    packet = obj["packet"]
    assert isinstance(packet, dict)
    return copy.deepcopy(dict(packet))


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": packet_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": packet_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": packet_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"edge:{e[0]}", f"edge:{e[0]}"] for e in positive["edges"]]
