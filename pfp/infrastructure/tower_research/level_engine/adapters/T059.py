# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 059's research-tree replay: the replayed near rows, far
rows, entries, total, bound and margin are the target checker's near, far,
correlations, total, bound and excess as they stand.  Written against the
registered stage-59 checker.

The witness is p208b's rational Bell-CHSH model: Alice's vectors ALICE_VEC_0
= (1, 0) and ALICE_VEC_1 = (0, 1) as the near rows, Bob's vectors BOB_VEC_0 =
(4/5, 3/5) and BOB_VEC_1 = (4/5, -3/5) as the far rows (the spec reads them as
the module's ``*_VEC_0``/``*_VEC_1`` constants in name order), the correlators
E_xy = dot_product_2d(a_x, b_y), the CHSH value S = 14/5 of
``pythagorean_model`` (recomputed through ``make_correlation_table(...)
.chsh_correlator()``, the one ``*_correlator`` method the spec looks up), and
the local-hidden-variable bound 2 as the largest ``correlator()`` over
``generate_all_deterministic_strategies()``.  The own negative writes the
first deterministic strategy (Alice and Bob answer +1 to both inputs) as
one-coordinate rows and keeps the label S = 14/5.

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_059"
CLAUSES = (("C1", "R059_NOT_UNIT"), ("C2", "R059_CORRELATION"), ("C3", "R059_TOTAL"), ("C4", "R059_BOUND"),
           ("C5", "R059_EXCESS"))
COEFFICIENT_DOMAIN = {"source": "exact rationals (fractions.Fraction)", "target": "canonical rational strings"}
SORTS = (("Alice vector", "near row"), ("Bob vector", "far row"), ("correlator E_xy", "correlation"),
         ("CHSH value S", "total"), ("LHV bound", "bound"))
UNMAPPED_SORTS = ("presentation token", "joint probability table P(a, b | x, y)")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("source.table", "the tree's no-signaling table P(a, b | x, y) = (1 + ab E_xy) / 4",
     "not stated; read only for its CHSH value", "DROPPED"),
    ("target.excess", "the tree states S > 2 (pythagorean_exceeds_lhv)",
     "S - B, computed by the replay from the tree's S and bound", "PRESERVED"),
    ("target.own_negative_rows", "the tree's deterministic strategy A = (1, 1), B = (1, 1)",
     "one-coordinate rows (A(x), 0) and (B(y), 0), so E_xy = A(x) B(y); computed by the replay", "PRESERVED"),
    ("source.mixtures", "the tree's convex mixtures of strategies (ConvexLHVModel)", "not stated", "DROPPED"),
    ("source.lean", "the tree's Lean enters E_xy as literals and proves 2 < S < 4",
     "not cited; the replay rests on the tree's Python", "DROPPED"),
)
NEAR = (("own_neg", "R059_TOTAL"), ("near_stretched", "R059_NOT_UNIT"), ("near_entry", "R059_CORRELATION"),
        ("near_ceiling", "R059_BOUND"), ("near_margin", "R059_EXCESS"))
MUTATIONS = (("C1", "R059_NOT_UNIT", "row_doubled", "row_stretched"),
             ("C2", "R059_CORRELATION", "entry_wrong", "near_entry"),
             ("C3", "R059_TOTAL", "mut", "mut"),
             ("C4", "R059_BOUND", "bound_algebraic", "near_ceiling"),
             ("C5", "R059_EXCESS", "margin_zero", "near_margin"))


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
    return [["ALICE_VEC_0", "near:0"], ["ALICE_VEC_1", "near:1"], ["BOB_VEC_0", "far:0"], ["BOB_VEC_1", "far:1"]]
