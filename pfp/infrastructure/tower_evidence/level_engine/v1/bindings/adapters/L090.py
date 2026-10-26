"""Adapter for level 090: the engine's source and records written as the
target checker's source and clause records, in declared order.  A record's
span is its begin and end offsets' values, its digest is its digest as
hosted (never recomputed here), and its tag is written as ``link`` when
the tag is a link element and as ``exception`` when it is an exception
element, the other written null.  Written against the registered stage-90
checker, whose splitter and quantifier word list the engine restates as
supplied data.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_090"
CLAUSES = (("C1", "R090_SPAN"), ("C2", "R090_SPAN_DIGEST"), ("C3", "R090_QUANTIFIED_CLAUSE_MISSING"),
           ("C4", "R090_COVERAGE_GAP"), ("C5", "R090_UNACCOUNTED"))
COEFFICIENT_DOMAIN = {"source": "ASCII texts, naturals and SHA-256 digests",
                      "target": "ASCII texts, naturals and SHA-256 digests"}
SORTS = (("source", "source text"), ("record", "clause record"), ("offset", "span offset"), ("link", "link"),
         ("exception", "scope exception"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.tags", "one tagged relation, its kind by the tag's sort", "link and exception fields, the other null",
     "PRESERVED"),
    ("target.numbers", "exact rationals n/1", "JSON naturals", "PRESERVED"),
)
NEAR = (("own_neg", "R090_QUANTIFIED_CLAUSE_MISSING"), ("near_both", "R090_UNACCOUNTED"))
MUTATIONS = (("C1", "R090_SPAN", "recorded_twice", "near_twice"),
             ("C2", "R090_SPAN_DIGEST", "digest_changed", "near_digest"),
             ("C3", "R090_QUANTIFIED_CLAUSE_MISSING", "quantified_dropped", "own_neg"),
             ("C4", "R090_COVERAGE_GAP", "clause_dropped", "near_gap"),
             ("C5", "R090_UNACCOUNTED", "tag_dropped", "near_untagged"))


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
    links, exceptions = _sort(structure, "link"), _sort(structure, "exception")

    def seconds(name: str, first: int) -> list[int]:
        return sorted(a[1] for n, a in rel if n == name and a[0] == first)

    def tag(r: int, kind: list[int]) -> str | None:
        got = [text[t] for t in seconds("tagged", r) if t in kind]
        return got[0] if got else None

    return {"clauses": [{"digest": digest[r], "exception": tag(r, exceptions), "link": tag(r, links),
                         "span": [value[seconds("begins", r)[0]], value[seconds("ends", r)[0]]]}
                        for r in _sort(structure, "record")],
            "source": text[_sort(structure, "source")[0]]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [["source:0", "source"]] + [[f"record:{k}", f"clause:{k}"] for k in range(len(positive["clauses"]))]
