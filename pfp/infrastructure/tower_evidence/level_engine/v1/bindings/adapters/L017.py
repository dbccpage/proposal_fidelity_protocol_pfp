"""Adapter for level 017: the replayed containers are the target checker's
input as they stand (tags ``t0`` and ``t1``, sealed bodies, canonical
SHA-256 digests).  Written against the registered stage-17 checker
(``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_017"
CLAUSES = (("C1", "R017_DIGEST_MISMATCH"), ("C2", "R017_UNKNOWN_TAG"), ("C3", "R017_DECODE_FAILED"))
COEFFICIENT_DOMAIN = {"source": "sealed class counts and signatures", "target": "tagged containers"}
SORTS = (("class count", "t0 body"), ("signature", "t1 body"))
UNMAPPED_SORTS = ("presentation token", "question family")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.dialects", "sealed answers", "the target's two tag dialects", "WEAKENED"),
    ("target.family", "the question family", "not presented; only its counts and signatures", "DROPPED"),
)
NEAR = (("own_neg", "R017_DIGEST_MISMATCH"), ("near_word", "R017_DECODE_FAILED"))
MUTATIONS = (("C1", "R017_DIGEST_MISMATCH", "count_changed_under_digest", "own_neg"),
             ("C2", "R017_UNKNOWN_TAG", "mut", "mut"),
             ("C3", "R017_DECODE_FAILED", "word_not_binary", "near_word"))


def containers_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    packet = obj["packet"]
    assert isinstance(packet, dict)
    return copy.deepcopy(dict(packet))


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": containers_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": containers_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": containers_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"answer:{k}", f"container:{k}"] for k in range(len(positive["containers"]))]
