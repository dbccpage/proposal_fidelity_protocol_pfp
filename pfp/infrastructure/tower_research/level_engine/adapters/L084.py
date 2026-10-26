# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 084: the engine's calls written as the target checker's
calls, in declared order.  A call's tool is its tool's name as hosted; its
arguments are its ``arg_<name>`` relations, each named ``<name>``, a list
argument (``items``, ``terms``) with its entries in declared order; its
result digest is the call's digest as hosted, never recomputed here.
Numbers are written from their hosted values: ``terms`` entries as
canonical rational texts (the tool's contract reads them so), every other
number as a JSON integer when it is a natural and as its canonical text
otherwise (the receiving side refuses a negative JSON integer).
Written against the registered stage-84 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_084"
CLAUSES = (("C1", "R084_UNKNOWN_TOOL"), ("C2", "R084_ARGUMENTS"), ("C3", "R084_GUESSED_RESULT"))
COEFFICIENT_DOMAIN = {"source": "exact rationals, ASCII texts and SHA-256 digests",
                      "target": "exact rationals, ASCII texts and SHA-256 digests"}
SORTS = (("call", "call"), ("tool", "tool name"), ("number", "numeric argument"), ("word", "text argument"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.argument_names", "relations arg_<name>", "argument keys <name>", "PRESERVED"),
    ("target.numbers", "exact rationals p/q", "JSON integers for naturals, else canonical p/q texts; terms always texts",
     "PRESERVED"),
)
NEAR = (("own_neg", "R084_GUESSED_RESULT"), ("near_needle", "R084_ARGUMENTS"))
MUTATIONS = (("C1", "R084_UNKNOWN_TOOL", "tool_renamed", "near_tool"),
             ("C2", "R084_ARGUMENTS", "argument_negative", "near_args"),
             ("C3", "R084_GUESSED_RESULT", "result_guessed", "near_sum"))
ARGS = ("a", "b", "items", "terms", "text", "needle")
LISTS = ("items", "terms")


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def _number(v: str, as_text: bool) -> int | str:
    x = Fraction(v)
    return v if as_text or x.denominator != 1 or x < 0 else int(x)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    value = {int(e): str(v) for e, v in structure["values"]}
    digest = {int(e): str(d) for e, d in structure["digests"]}
    text = {int(e): str(t) for e, t in structure["texts"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def entry(name: str, v: int) -> int | str:
        return _number(value[v], name == "terms") if v in value else text[v]

    def args(c: int) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for name in ARGS:
            got = sorted(a[1] for n, a in rel if n == "arg_" + name and a[0] == c)
            if got:
                out[name] = [entry(name, v) for v in got] if name in LISTS else entry(name, got[0])
        return out

    tool = {a[0]: text[a[1]] for n, a in rel if n == "uses"}
    return {"calls": [{"args": args(c), "result_digest": digest[c], "tool": tool[c]}
                      for c in _sort(structure, "call")]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"call:{k}", f"call:{k}"] for k in range(len(positive["calls"]))]
