"""Adapter for level 082: the engine's body, sum, aim, keys, grants and marks
written as the target checker's artifact, manifest, chain and root.  The
root is the key the engine names root; the chain is the other keys in
declared order, each with its exponent, its grants (declared order) as the
scope list and its vouched mark as the signature; the manifest's signature
is the sum's mark, written null when the sum carries none.  Naturals are
written from their hosted ``n/1`` values, the digest and texts as hosted,
never recomputed here.  Written against the registered stage-82 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_082"
CLAUSES = (("C1", "R082_UNSIGNED_CHECKSUM"), ("C2", "R082_DIGEST_MISMATCH"), ("C3", "R082_UNTRUSTED_ROOT"),
           ("C4", "R082_SCOPE"), ("C5", "R082_BAD_SIGNATURE"))
COEFFICIENT_DOMAIN = {"source": "naturals, ASCII texts and SHA-256 digests",
                      "target": "naturals, ASCII texts and SHA-256 digests"}
SORTS = (("body", "artifact"), ("sum", "manifest digest"), ("aim", "manifest target"), ("key", "key modulus"),
         ("power", "key exponent"), ("grant", "scope entry"), ("mark", "signature"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.numbers", "exact rationals n/1", "JSON naturals", "PRESERVED"),
    ("target.chain_order", "root relation, then keys in declared order", "root field, then chain list", "PRESERVED"),
    ("target.root_scope", "pinned in the engine's spec", "pinned in the checker (TRUST_ROOTS)", "PRESERVED"),
    ("target.unsigned", "a sum with no marked tuple", "manifest signature null", "PRESERVED"),
)
NEAR = (("own_neg", "R082_UNSIGNED_CHECKSUM"), ("near_self", "R082_BAD_SIGNATURE"))
MUTATIONS = (("C1", "R082_UNSIGNED_CHECKSUM", "signature_dropped", "own_neg"),
             ("C2", "R082_DIGEST_MISMATCH", "body_changed", "near_body"),
             ("C3", "R082_UNTRUSTED_ROOT", "root_changed", "near_root"),
             ("C4", "R082_SCOPE", "grant_changed", "near_grant"),
             ("C5", "R082_BAD_SIGNATURE", "signature_changed", "near_mark"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    value = {int(e): int(Fraction(str(v))) for e, v in structure["values"]}
    digest = {int(e): str(d) for e, d in structure["digests"]}
    text = {int(e): str(t) for e, t in structure["texts"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def seconds(name: str, first: int) -> list[int]:
        return [a[1] for n, a in rel if n == name and a[0] == first]

    def one(name: str, first: int) -> int:
        got = seconds(name, first)
        assert len(got) == 1, (name, first)
        return got[0]

    s = _sort(structure, "sum")[0]
    root = next(a[0] for n, a in rel if n == "root")

    def key(k: int) -> dict[str, Any]:
        return {"e": value[one("raised", k)], "n": value[k]}

    marks = seconds("marked", s)
    return {
        "artifact": text[one("covers", s)],
        "chain": [dict(key(k), scope=[text[g] for g in _sort(structure, "grant") if g in seconds("may", k)],
                       signature=value[one("vouched", k)])
                  for k in _sort(structure, "key") if k != root],
        "manifest": {"digest": digest[s], "signature": value[marks[0]] if marks else None,
                     "target": text[one("aims", s)]},
        "root": key(root),
    }


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [["key:root", "root"], ["sum:0", "manifest"], ["body:0", "artifact"]] + [
        [f"key:{k + 1}", f"chain:{k}"] for k in range(len(positive["chain"]))]
