"""Adapter for level 045: the engine's terms, bound axioms, lines and seal
written as the target checker's axioms, axiom digest, proof and conclusion.
An atom is written ``p<k>`` by its place among the atoms, an implication as
``["->", a, b]``; the axiom digest is the seal's digest as hosted, never
recomputed here; a line resting on its own report is written with the
justification ``["self-reported"]``.  Written against the registered
stage-45 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_045"
CLAUSES = (("C1", "R045_UNBOUND_AXIOMS"), ("C2", "R045_UNKNOWN_RULE"), ("C3", "R045_FORWARD_REFERENCE"),
           ("C4", "R045_STEP_MISMATCH"), ("C5", "R045_CONCLUSION_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "SHA-256 digests as exact 32-byte values",
                      "target": "SHA-256 digests as exact 32-byte values"}
SORTS = (("term", "formula"), ("axiom", "axiom"), ("line", "proof line"), ("seal", "axiom digest"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.atom_names", "atoms by place", "strings p0, p1, ...", "PRESERVED"),)
NEAR = (("own_neg", "R045_UNKNOWN_RULE"),)
MUTATIONS = (("C1", "R045_UNBOUND_AXIOMS", "digest_changed", "near_digest"),
             ("C2", "R045_UNKNOWN_RULE", "line_self_reported", "near_report"),
             ("C3", "R045_FORWARD_REFERENCE", "detach_forward", "near_forward"),
             ("C4", "R045_STEP_MISMATCH", "mut", "mut"),
             ("C5", "R045_CONCLUSION_MISMATCH", "conclusion_changed", "near_conclusion"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    terms, axioms = _sort(structure, "term"), _sort(structure, "axiom")
    lines, (seal,) = _sort(structure, "line"), _sort(structure, "seal")
    rel = [(n, list(a)) for n, a in structure["relations"]]
    imp = {a[0]: (a[1], a[2]) for n, a in rel if n == "imp"}
    atoms = [t for t in terms if t not in imp]

    def w(t: int) -> Any:
        return ["->", w(imp[t][0]), w(imp[t][1])] if t in imp else f"p{atoms.index(t)}"

    def one(name: str, key: int) -> int:
        return next(a[1] for n, a in rel if n == name and a[0] == key)

    def just(line: int) -> list[Any]:
        for n, a in rel:
            if n == "cites" and a[0] == line:
                return ["axiom", axioms.index(a[1])]
            if n == "detaches" and a[0] == line:
                return ["mp", lines.index(a[1]), lines.index(a[2])]
        return ["self-reported"]

    digest = dict((int(e), str(d)) for e, d in structure["digests"])[seal]
    return {"axiom_digest": digest, "axioms": [w(one("states", k)) for k in axioms],
            "conclusion": w(next(a[0] for n, a in rel if n == "concludes")),
            "proof": [[w(one("claims", line)), just(line)] for line in lines]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"line:{k}", f"proof:{k}"] for k in range(len(positive["proof"]))]
