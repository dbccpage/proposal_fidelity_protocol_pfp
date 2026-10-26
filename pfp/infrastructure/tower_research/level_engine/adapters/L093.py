# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 093: the engine's source expression, program, inputs,
fuel and table written as the target checker's source, target, inputs,
fuel and outcomes.  The source is unfolded from its root, a shared node
written at each of its places (``reads_input`` as ``var``, ``constant`` as
``num`` with the node's value, ``plus`` as ``add``, ``minus`` as ``sub``,
``if_less`` as ``if_lt``); instructions are indexed by their declared
order (``jump_if_less`` as ``jlt``, ``jump`` as ``jmp``, a push with the
instruction's value), and a jump to an element that is not an instruction
is written past the program's end, so the checker sees it leave the
program; inputs and table rows are listed in the declared order of their
numbers.  Written against the registered stage-93 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_093"
CLAUSES = (("C1", "R093_BAD_TARGET"), ("C2", "R093_UNCOVERED_BRANCH"), ("C3", "R093_TARGET_DIVERGES"),
           ("C4", "R093_BRANCH_CHANGES_OUTCOME"), ("C5", "R093_OUTCOME_TABLE"))
COEFFICIENT_DOMAIN = {"source": "integers", "target": "integers"}
SORTS = (("node", "source expression"), ("number", "input, result or fuel"), ("instr", "instruction"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.sharing", "a subexpression may be one shared node", "a tree with the part repeated", "PRESERVED"),
    ("target.jumps", "a jump names an element", "a jump names an index; a non-instruction lies past the end",
     "PRESERVED"),
)
NEAR = (("own_neg", "R093_BRANCH_CHANGES_OUTCOME"), ("near_stuck", "R093_BAD_TARGET"),
        ("near_loop", "R093_TARGET_DIVERGES"))
MUTATIONS = (("C1", "R093_BAD_TARGET", "jump_off_program", "near_jump"),
             ("C2", "R093_UNCOVERED_BRANCH", "input_dropped", "near_uncovered"),
             ("C3", "R093_TARGET_DIVERGES", "fuel_short", "near_fuel"),
             ("C4", "R093_BRANCH_CHANGES_OUTCOME", "branch_moved", "mut"),
             ("C5", "R093_OUTCOME_TABLE", "table_changed", "near_table"))
WORDS = {"plus": "add", "minus": "sub", "if_less": "if_lt"}
OPS = {"push": "push", "load": "load", "add": "add", "sub": "sub", "jump_if_less": "jlt", "jump": "jmp",
       "halt": "halt"}


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    rel = [(str(n), [int(x) for x in a]) for n, a in structure["relations"]]
    value = {int(e): int(Fraction(str(v))) for e, v in structure["values"]}
    instrs, numbers = _sort(structure, "instr"), _sort(structure, "number")

    def expr(e: int) -> list[Any]:
        for n, a in rel:
            if a[0] != e:
                continue
            if n == "reads_input":
                return ["var"]
            if n == "constant":
                return ["num", value[e]]
            if n in WORDS:
                return [WORDS[n]] + [expr(c) for c in a[1:]]
        raise KeyError(e)

    def ip(e: int) -> int:
        return instrs.index(e) if e in instrs else len(instrs) + e

    target: list[list[Any]] = []
    for i in instrs:
        for n, a in rel:
            if a[0] == i and n in OPS:
                target.append([OPS[n]] + ([value[i]] if n == "push" else [ip(a[1])] if len(a) == 2 else []))
    root = next(a[0] for n, a in rel if n == "root")
    inputs = {a[0] for n, a in rel if n == "input"}
    rows = {a[0]: a[1] for n, a in rel if n == "table_row"}
    fuel = next(a[0] for n, a in rel if n == "fuel")
    return {"fuel": value[fuel], "inputs": [value[k] for k in numbers if k in inputs],
            "outcomes": [[value[k], value[rows[k]]] for k in numbers if k in rows],
            "source": expr(root), "target": target}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return ([["node:root", "source"]] + [[f"instr:{k}", f"target:{k}"] for k in range(len(positive["target"]))]
            + [[f"number:input:{v}", f"inputs:{v}"] for v in positive["inputs"]])
