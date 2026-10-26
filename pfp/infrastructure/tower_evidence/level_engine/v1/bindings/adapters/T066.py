"""Adapter for level 066's research-tree replay: the replayed terms and
cancellation certificate (natural_sections' pinned sign-repair witness,
and fresh_characters' smallest refusing row as the refused case) are the
target checker's terms, pairs, rest and total as they stand.  The trees'
integer weights enter as exact rationals n/1; a pair or a rest term is
written by its index.  Written against the registered stage-66 checker.

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_066"
CLAUSES = (("C1", "R066_NOT_A_PARTITION"), ("C2", "R066_NOT_OPPOSITE"), ("C3", "R066_UNPAIRED_REST"),
           ("C4", "R066_TOTAL"))
COEFFICIENT_DOMAIN = {"source": "integers", "target": "exact rationals"}
SORTS = (("term", "term index"), ("weight", "rational"))
UNMAPPED_SORTS = ("presentation token", "configuration point", "part count")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.terms", "natural_sections' pinned witness weights (1, 2, -1, -2, 1, 1) as integers",
     "exact rationals n/1 in the tree's order", "PRESERVED"),
    ("target.pairs_rest", "the tree's decomposition of its witness: exact-opposite pairs of magnitudes 1 and 2, "
     "residual (1, 1) (its Lean decomposition, matched by its test as multisets)",
     "index pairs (0, 2), (1, 3) and rest (4, 5), placed first-come by the replay", "PRESERVED"),
    ("target.total", "the certificate's residual total, 2", "the claimed total 2/1, computed by the replay",
     "PRESERVED"),
    ("source.points", "each weight sits at a configuration point (m, f) of the tree's product carrier",
     "a bare index", "DROPPED"),
    ("source.criterion", "both trees' certificate criteria (per-magnitude domination and brute-force search): "
     "the positive certified, the refused row and the wedge not", "not decided by the checker as clauses; "
     "reported beside the record", "DROPPED"),
    ("source.lean", "natural_sections' Lean (certificate_iff_dominated, wedge_no_certificate, "
     "witness_certificate)", "not cited; the replay rests on the trees' Python", "DROPPED"),
)
NEAR = (("own_neg", "R066_UNPAIRED_REST"), ("near_wedge", "R066_UNPAIRED_REST"),
        ("near_partition", "R066_NOT_A_PARTITION"), ("near_opposite", "R066_NOT_OPPOSITE"))
MUTATIONS = (("C1", "R066_NOT_A_PARTITION", "term_unplaced", "near_partition"),
             ("C2", "R066_NOT_OPPOSITE", "pair_not_opposite", "pair_off"),
             ("C3", "R066_UNPAIRED_REST", "rest_both_signs", "rest_mixed"),
             ("C4", "R066_TOTAL", "mut", "mut"))


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
    return [[f"term:{k}", f"index:{k}"] for k in range(len(positive["terms"]))]
