# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 036: the engine's hosted update written as the target
checker's hypotheses, prior, observations and posteriors.  Alternatives are
named by their position in the declared order; each observation's
likelihoods and declared weights follow that order.  Written against the
registered stage-36 checker (``b5a2c46c``).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_036"
CLAUSES = (("C1", "R036_PRIOR_NOT_NORMALISED"), ("C2", "R036_LIKELIHOOD_RANGE"), ("C3", "R036_ZERO_EVIDENCE"),
           ("C4", "R036_POSTERIOR_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("alt", "hypothesis"), ("obs", "observation"), ("val", "weight"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.names", "alternatives as elements", "their positions as names", "PRESERVED"),)
NEAR = (("own_neg", "R036_ZERO_EVIDENCE"), ("near_range", "R036_LIKELIHOOD_RANGE"))
MUTATIONS = (("C1", "R036_PRIOR_NOT_NORMALISED", "prior_over_one", "near_prior"),
             ("C2", "R036_LIKELIHOOD_RANGE", "likelihood_over_one", "near_range"),
             ("C3", "R036_ZERO_EVIDENCE", "later_zero_evidence", "near_zero_later"),
             ("C4", "R036_POSTERIOR_MISMATCH", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def update_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    hs, os = _sort(structure, "alt"), _sort(structure, "obs")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    prior = {a[0]: value[a[1]] for n, a in rel if n == "prior"}
    likely = {(a[0], a[1]): value[a[2]] for n, a in rel if n == "likely"}
    after = {(a[0], a[1]): value[a[2]] for n, a in rel if n == "after"}
    return {"hypotheses": [f"h{k}" for k in range(len(hs))], "observations": [[likely[(o, h)] for h in hs] for o in os],
            "posteriors": [[after[(o, h)] for h in hs] for o in os], "prior": [prior[h] for h in hs]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": update_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": update_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": update_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"alt:{k}", f"hypothesis:{h}"] for k, h in enumerate(positive["hypotheses"])]
