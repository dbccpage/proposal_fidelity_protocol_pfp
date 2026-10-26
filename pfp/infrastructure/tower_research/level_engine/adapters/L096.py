# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 096: the engine's items, seal, trials and estimate
written as the target checker's corpus, corpus digest, trials and estimate.
Items are named ``c<k>`` by place (the names the seal is computed over); a
trial that draws an element that is no item names it ``x<e>``; a trial is
written ``success`` when it is marked succeeded and not failed, otherwise
``failure``; a missing trial count is written ``null``.  Digests and values
are written as hosted, never recomputed here.  Written against the
registered stage-96 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_096"
CLAUSES = (("C1", "R096_POINT_ESTIMATE_WITHOUT_COUNT"), ("C2", "R096_CORPUS_DIGEST"), ("C3", "R096_TRIAL_ITEM"),
           ("C4", "R096_COUNT_MISMATCH"), ("C5", "R096_INTERVAL"))
COEFFICIENT_DOMAIN = {"source": "exact rationals, SHA-256 digests and texts",
                      "target": "exact rationals, SHA-256 digests and texts"}
SORTS = (("item", "corpus item"), ("seal", "corpus digest"), ("trial", "trial"), ("successes", "estimate.successes"),
         ("count", "estimate.count"), ("point", "estimate.point"), ("half_width", "estimate.half_width"),
         ("alpha", "estimate.alpha"), ("low", "estimate.interval[0]"), ("high", "estimate.interval[1]"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.names", "items by place", "strings c<k>", "PRESERVED"),
    ("target.results", "succeeded(t) or failed(t)", "the strings success and failure", "PRESERVED"),
    ("target.count", "no count element", "null", "PRESERVED"),
)
NEAR = (("own_neg", "R096_POINT_ESTIMATE_WITHOUT_COUNT"), ("near_foreign", "R096_TRIAL_ITEM"),
        ("near_successes", "R096_COUNT_MISMATCH"), ("near_alpha", "R096_INTERVAL"))
MUTATIONS = (("C1", "R096_POINT_ESTIMATE_WITHOUT_COUNT", "count_dropped", "near_uncounted"),
             ("C2", "R096_CORPUS_DIGEST", "content_changed", "near_content"),
             ("C3", "R096_TRIAL_ITEM", "mut", "mut"),
             ("C4", "R096_COUNT_MISMATCH", "count_changed", "near_count"),
             ("C5", "R096_INTERVAL", "end_changed", "near_interval"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    value = {int(e): str(v) for e, v in structure["values"]}
    digest = {int(e): str(d) for e, d in structure["digests"]}
    text = {int(e): str(t) for e, t in structure["texts"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    items, trials = _sort(structure, "item"), _sort(structure, "trial")
    (seal,) = _sort(structure, "seal")
    draw = {a[0]: a[1] for n, a in rel if n == "draws"}
    wins = {a[0] for n, a in rel if n == "succeeded"}
    losses = {a[0] for n, a in rel if n == "failed"}

    def name(e: int) -> str:
        return f"c{items.index(e)}" if e in items else f"x{e}"

    def one(sort: str) -> str:
        (e,) = _sort(structure, sort)
        return value[e]

    counts = _sort(structure, "count")
    return {"corpus": [[name(i), text[i]] for i in items], "corpus_digest": digest[seal],
            "estimate": {"alpha": one("alpha"), "count": int(Fraction(value[counts[0]])) if counts else None,
                         "half_width": one("half_width"), "interval": [one("low"), one("high")],
                         "point": one("point"), "successes": int(Fraction(one("successes")))},
            "trials": [[name(draw[t]), "success" if t in wins and t not in losses else "failure"] for t in trials]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return ([[f"item:{k}", f"corpus:{e[0]}"] for k, e in enumerate(positive["corpus"])] + [["seal:0", "corpus_digest"]]
            + [[f"trial:{k}", f"trials:{k}"] for k in range(len(positive["trials"]))])
