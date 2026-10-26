"""Adapter for level 088: the engine's program, registers, bounds and capture
written as the target checker's program, registers, limits and captured
exit.  Instructions and registers are indexed by position; a jump to an
element that is not an instruction is written past the program's end, so
the checker sees it as a bad jump.  Written against the registered
stage-88 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_088"
CLAUSES = (("C1", "R088_BAD_JUMP"), ("C2", "R088_TIMEOUT_AS_COMPLETION"), ("C3", "R088_EXIT_MISMATCH"),
           ("C4", "R088_STATE_MISMATCH"), ("C5", "R088_STEPS_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "naturals", "target": "naturals"}
SORTS = (("instr", "instruction"), ("register", "register"), ("bound", "limit"), ("final", "captured register"),
         ("capture", "captured exit"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.completion", "only a halt completes", "only a halt completes", "PRESERVED"),)
NEAR = (("own_neg", "R088_TIMEOUT_AS_COMPLETION"), ("mut", "R088_TIMEOUT_AS_COMPLETION"))
MUTATIONS = (("C1", "R088_BAD_JUMP", "jump_off_program", "near_jump"),
             ("C2", "R088_TIMEOUT_AS_COMPLETION", "timeout_captured_halted", "near_timeout"),
             ("C3", "R088_EXIT_MISMATCH", "exit_changed", "near_exit"),
             ("C4", "R088_STATE_MISMATCH", "register_changed", "near_state"),
             ("C5", "R088_STEPS_MISMATCH", "steps_changed", "near_steps"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    instrs, regs = _sort(structure, "instr"), _sort(structure, "register")
    value = {int(e): int(Fraction(str(v))) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def ip(e: int) -> int:
        return instrs.index(e) if e in instrs else len(instrs) + e

    def rp(e: int) -> int:
        return regs.index(e) if e in regs else len(regs) + e

    program: list[list[Any]] = []
    for i in instrs:
        for n, a in rel:
            if a[0] == i and n == "inc":
                program.append(["inc", rp(a[1]), ip(a[2])])
            elif a[0] == i and n == "dec":
                program.append(["dec", rp(a[1]), ip(a[2]), ip(a[3])])
            elif a[0] == i and n == "halt":
                program.append(["halt"])
    finals = {a[1]: value[a[0]] for n, a in rel if n == "final_of"}
    bounds = _sort(structure, "bound")
    kind = next(k for n, k in (("halted", "HALTED"), ("timed_out", "TIMEOUT"), ("at_limit", "LIMIT"))
                if any(m == n for m, _ in rel))
    return {"exit": kind, "max_steps": value[bounds[0]], "max_value": value[bounds[1]], "program": program,
            "registers": [value[r] for r in regs], "state": [finals[r] for r in regs],
            "steps": value[_sort(structure, "capture")[0]]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"instr:{k}", f"instruction:{k}"] for k in range(len(positive["program"]))]
