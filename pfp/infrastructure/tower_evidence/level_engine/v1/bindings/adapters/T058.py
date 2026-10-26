"""Adapter for level 058's research-tree replay: the replayed labels,
contexts and family are the target checker's labels, contexts and family as
they stand.  Written against the registered stage-58 checker.

The witness is natural_sections' two-label hop family (``holonomy_fixture``:
two hard-core particles on a site graph; objects are sorted occupied pairs,
the carrier is Bool, and a hop's transport is the swap when the mover passes
the stayer).  A context is one undirected hop (``representation.
undirected_hops``), rule ``differ`` for a flipping hop and ``equal`` otherwise;
a natural section is exactly a family that agrees on every overlap.  The
positive is ``budget_meter.instances()``'s ``chain_P4_r0_repres`` (the path
P4 with a pointwise re-presentation at its first object, section True), the
own negative its ``square_2x2_r0`` (Lean ``Hop.square_no_natural_section``),
the extra its ``triangle_C3_r0``.  ``family_exists`` is the tree's
``decide_section_steps``.

p208b (the Cabello 18-ray, 9-context valuation obstruction) is not used: its
per-context rule is "exactly one ray of four gets 1", which is neither of the
checker's two rules, and the tree proves that no valuation keeps it, so it
holds no positive family to state.

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_058"
CLAUSES = (("C1", "R058_CONTEXT"), ("C2", "R058_LOCAL_RULE"), ("C3", "R058_OVERLAP"))
COEFFICIENT_DOMAIN = {"source": "the tree's Bool carrier (False the smaller site, True the larger)",
                      "target": "labels 0 and 1"}
SORTS = (("configuration (sorted occupied pair)", "item"), ("undirected hop", "context"),
         ("flip bit", "rule"), ("section value", "label"))
UNMAPPED_SORTS = ("presentation token", "site", "hop direction")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.family", "the tree decides that the re-presented chain carries a natural section and does not list it",
     "the parity potential spread from the least object along a breadth-first tree, as the tree's decider builds "
     "it, read on each hop's two objects; computed by the replay", "PRESERVED"),
    ("target.own_negative_family", "the tree decides that the square carries no natural section",
     "each hop's choice is (potential at its first object, that value xor the flip bit): locally valid, "
     "disagreeing on the odd generators; computed by the replay", "PRESERVED"),
    ("target.rules", "the checker's rules over contexts of any size and any label set",
     "two-item contexts over two labels only", "WEAKENED"),
    ("source.lean", "the tree's Lean proves the chain and square fixtures (Hop.chain_has_natural_section, "
     "Hop.square_no_natural_section)", "not cited; the replay rests on the tree's Python", "DROPPED"),
    ("source.named_witness", "p208b's valuation obstruction on the 18-ray configuration",
     "not used: its rule is outside the checker's two rules and it has no agreeing family", "DROPPED"),
)
NEAR = (("own_neg", "R058_OVERLAP"), ("near_missing", "R058_CONTEXT"), ("near_rule", "R058_LOCAL_RULE"),
        ("near_turned", "R058_OVERLAP"))
MUTATIONS = (("C1", "R058_CONTEXT", "choice_missing", "near_missing"),
             ("C2", "R058_LOCAL_RULE", "rule_changed", "near_rule"),
             ("C3", "R058_OVERLAP", "mut", "mut"))


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
    items = sorted({x for _, xs, _ in positive["contexts"] for x in xs})
    return [[f"configuration:({x[0]}, {x[1]})", f"item:{x}"] for x in items]
