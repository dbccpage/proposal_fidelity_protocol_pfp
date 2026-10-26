# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 015: the replayed claim written as the target checker's
host receipt.  The claim and its terminal are copied; the scope is copied;
the verifier ``host`` is written as the digest of the target's pinned host
verifier and ``candidate`` as the digest of the target's candidate
self-check; the recorded output is written as its canonical SHA-256.
Written against the registered stage-15 checker (``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_015"
CLAUSES = (("C1", "R015_VERIFIER_UNBOUND"), ("C2", "R015_SCOPE_ESCALATION"), ("C3", "R015_TERMINAL_NOT_EARNED"),
           ("C4", "R015_OUTPUT_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "sealed class counts", "target": "a sum claim"}
SORTS = (("reading", "claim item"),)
UNMAPPED_SORTS = ("presentation token", "delta")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.verifier", "the host verifier named as host", "the target's pinned verifier digest", "PRESERVED"),
    ("target.claim", "tied classes per reading", "a sum of naturals", "WEAKENED"),
)
HOST_VERIFIER = b"the_symbol_game stage-015 host verifier: sum/v1"
CANDIDATE_SCRIPT = b"candidate self-check: return GREEN"
NEAR = (("own_neg", "R015_VERIFIER_UNBOUND"), ("near_scope", "R015_SCOPE_ESCALATION"))
MUTATIONS = (("C1", "R015_VERIFIER_UNBOUND", "candidate_verifier", "own_neg"),
             ("C2", "R015_SCOPE_ESCALATION", "widened_scope", "near_scope"),
             ("C3", "R015_TERMINAL_NOT_EARNED", "unearned_terminal", "near_terminal"),
             ("C4", "R015_OUTPUT_MISMATCH", "mut", "mut"))


def _digest_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _digest_obj(obj: object) -> str:
    return _digest_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii"))


def receipt_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    pk = obj["packet"]
    assert isinstance(pk, dict)
    verifier = HOST_VERIFIER if pk["verifier"] == "host" else CANDIDATE_SCRIPT
    return {"claim": copy.deepcopy(pk["claim"]), "claim_value": pk["claim_value"],
            "output_sha256": _digest_obj(pk["output"]), "scope": pk["scope"],
            "verifier_sha256": _digest_bytes(verifier)}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": receipt_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": receipt_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": receipt_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"reading:{k}", f"item:{k}"] for k in range(len(positive["claim"]["items"]))]
