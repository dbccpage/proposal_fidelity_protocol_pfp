# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 092: the engine's claims, clauses, steps and models
written as the target checker's claims.  Variables are named ``v<k>`` by
position (``~v<k>`` negated); a claim's given clauses come first and its
steps after, in declared order, which is how the checker numbers them; an
unsatisfiable claim with no step is written with no proof object; a model
lists its literals in variable order.
Written against the registered stage-92 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_092"
CLAUSES = (("C1", "R092_FLAG_WITHOUT_PROOF"), ("C2", "R092_BAD_STEP"), ("C3", "R092_RESOLVENT_MISMATCH"),
           ("C4", "R092_NOT_REFUTATION"), ("C5", "R092_MODEL_FAILS"))
COEFFICIENT_DOMAIN = {"source": "propositional clauses", "target": "propositional clauses"}
SORTS = (("variable", "variable"), ("claim", "claim"), ("clause", "clause or step"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.lean_terms", "no Lean term is rebuilt", "no Lean term is rebuilt", "PRESERVED"),)
NEAR = (("own_neg", "R092_FLAG_WITHOUT_PROOF"), ("near_inconsistent", "R092_MODEL_FAILS"),
        ("mut", "R092_NOT_REFUTATION"))
MUTATIONS = (("C1", "R092_FLAG_WITHOUT_PROOF", "proof_dropped", "own_neg"),
             ("C2", "R092_BAD_STEP", "step_reads_ahead", "near_forward"),
             ("C3", "R092_RESOLVENT_MISMATCH", "resolvent_changed", "near_resolvent"),
             ("C4", "R092_NOT_REFUTATION", "proof_short", "near_short"),
             ("C5", "R092_MODEL_FAILS", "model_fails", "near_model"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    variables, clauses = _sort(structure, "variable"), _sort(structure, "clause")
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def lits(k: int) -> list[str]:
        return sorted([f"v{variables.index(a[1])}" for n, a in rel if n == "pos_in" and a[0] == k]
                      + [f"~v{variables.index(a[1])}" for n, a in rel if n == "neg_in" and a[0] == k])

    owner = {a[0]: a[1] for n, a in rel if n == "of_claim"}
    res = {a[0]: a[1:] for n, a in rel if n == "resolves"}
    unsat = {a[0] for n, a in rel if n == "unsat"}
    out = []
    for c in _sort(structure, "claim"):
        mine = [k for k in clauses if owner.get(k) == c]
        given = [k for k in mine if k not in res]
        steps = [k for k in mine if k in res]
        index = {k: i for i, k in enumerate(given + steps)}
        model = [f"{'' if n == 'true_in' else '~'}v{variables.index(v)}" for v in variables for n, a in rel
                 if n in ("true_in", "false_in") and a[0] == c and a[1] == v]
        out.append({"answer": "UNSAT" if c in unsat else "SAT", "cnf": [lits(k) for k in given],
                    "model": None if c in unsat else model,
                    "proof": ([{"clause": lits(k), "from": [index[res[k][0]], index[res[k][1]]],
                                "pivot": f"v{variables.index(res[k][2])}"} for k in steps] or None)
                    if c in unsat else None})
    return {"claims": out}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"claim:{k}", f"claim:{k}"] for k in range(len(positive["claims"]))]
