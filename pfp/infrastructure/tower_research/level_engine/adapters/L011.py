# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 011: the replayed sealed peak, already stated over
letters, is the target checker's input as it stands (source, rules, the two
peak steps, the two arms, the join).  The typed map is the writing of each
event of the sealed rewrite alphabet as one letter.  Written against the
registered stage-11 checker (``b697efad``).

The empty-join clause (C2) fires only when both arms are empty.  A single
edit empties at most one arm, so it could bite only a positive with an empty
arm, and no peak of the stated sealed steps has one: the replay searches the
sealed battery up to length 4 and finds none (``peaks_with_an_empty_arm`` in
its evidence).  C2 is vacuous on this carrier and is not claimed.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_011"
CLAUSES = (("C1", "R011_BAD_REDEX"), ("C3", "R011_ARMS_DISAGREE"), ("C4", "R011_JOIN_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "event lists", "target": "words"}
SORTS = (("event", "letter"), ("rule", "rule"))
UNMAPPED_SORTS = ("presentation token",)
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.absorption", "terminal absorption erases the whole tail in one step",
     "per-letter rules that erase one following letter; only steps that are sealed reducts are stated",
     "WEAKENED"),
    ("target.empty_join", "no stated sealed peak has an empty arm (battery up to length 4)",
     "clause C2 vacuous, not claimed", "WEAKENED"),
)
NEAR = (("near_join", "R011_JOIN_MISMATCH"),)
MUTATIONS = (("C1", "R011_BAD_REDEX", "misplaced_step", "near_redex"),
             ("C3", "R011_ARMS_DISAGREE", "mut", "mut"),
             ("C4", "R011_JOIN_MISMATCH", "peak_term_as_join", "near_join"))


def peak_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    packet = obj["packet"]
    assert isinstance(packet, dict)
    return dict(packet)


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": peak_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": peak_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": peak_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"event:{k}", f"letter:{c}"] for k, c in enumerate("abch")]
