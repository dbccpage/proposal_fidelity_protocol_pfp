"""Adapter for level 060's research-tree replay: the replayed sites, checks,
errors and readings are the target checker's sites, checks, errors and
readings as they stand.  Written against the registered stage-60 checker.

The witness is p209c's bit-flip code [[3, 1, 1]] (``BitFlipCode3``): its
stabilizers S1 = ZZI and S2 = IZZ as the checks, its single bit-flip errors
XII, IXI, IIX as the errors, and its syndrome table's entries (10, 11, 01) as
the readings (``syndrome_table_single_bitflips``, which the spec looks up as
the code's one ``*_single_bitflips`` method; its no-error entry III -> 00 is
left out).  Every commutation is the tree's ``PauliString.commutes_with``
and each reading bit is ``anticommutes_with``, as in the tree's ``syndrome``.
The own negative is the code's logical pair X_L = XXX and Z_L = ZZZ, which the
tree's test and its Lean (``bitflip_xl_anticomm_zl``) find anticommute.  The
extras are the tree's undetected sign flip ZII (``test_bitflip_code_does_not_
correct_a_sign_flip``) and its [[4, 2, 2]] torus code, whose syndromes name
the Pauli type and not the site.  p209d (``stabilizer_self_commutes``, n <= 2)
is not used: its Python works in floating complex numbers.

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_060"
CLAUSES = (("C1", "R060_LENGTH"), ("C2", "R060_ANTICOMMUTING"), ("C3", "R060_NOT_DISTINCT"),
           ("C4", "R060_READING"))
COEFFICIENT_DOMAIN = {"source": "the tree's Pauli strings, read as binary symplectic vectors",
                      "target": "bit strings over GF(2)"}
SORTS = (("site", "site"), ("check", "check"), ("error", "error"), ("reading", "reading"))
UNMAPPED_SORTS = ("presentation token", "phase power", "site letter")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("source.phase", "the tree's strings carry a phase i^k", "not stated; a word is its (x | z) pair", "DROPPED"),
    ("target.words", "the tree's strings over I, X, Y, Z", "(x | z) bit pairs by the tree's own symplectic_vector",
     "PRESERVED"),
    ("target.readings", "the tree's syndrome table (10, 11, 01, and 00 for no error)",
     "the three nonzero entries, in table order; the no-error entry is left out", "WEAKENED"),
    ("source.lean", "the tree's Lean states the fixture commutations and syndromes over a declared table",
     "not cited; the replay rests on the tree's Python", "DROPPED"),
    ("source.second_tree", "p209d's self-commutation for n <= 2", "not used", "DROPPED"),
)
NEAR = (("own_neg", "R060_ANTICOMMUTING"), ("near_short", "R060_LENGTH"), ("near_odd", "R060_ANTICOMMUTING"),
        ("near_quiet", "R060_NOT_DISTINCT"))
MUTATIONS = (("C1", "R060_LENGTH", "half_short", "near_short"),
             ("C2", "R060_ANTICOMMUTING", "checks_meet_once", "near_odd"),
             ("C3", "R060_NOT_DISTINCT", "sign_unread", "quiet_unread"),
             ("C4", "R060_READING", "mut", "mut"))


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
    return [[f"carrier:{k}", f"site:{k}"] for k in range(positive["sites"])]
