"""Adapter for level 001: the engine's packet (a source kept first, then the
two generators in order) written in the target checker's wire form
``op<`` opcode, operands ``>``, with the fixed opcode ``<0>``.

The engine's own negative (the source dropped) serializes to the target's own
negative exactly.  Written against the stage-1 target checker on
``claude/p2-checkers`` (``b697efad``); it takes effect only when that checker
is registered of record under ``CHECKER_ID``.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_001"
CLAUSES = (("C1", "R001_SOURCE_OMITTED"), ("C3", "R001_GENERATORS"))
COEFFICIENT_DOMAIN = {"source": "packet", "target": "wire string"}
SORTS = (("source", "first operand"), ("generator", "operand after the source"))
UNMAPPED_SORTS: tuple[str, ...] = ()
STRUCTURE_MAP_REASON = "the obligation names no structure map"
OPCODE = "<0>"


def wire(packet: object) -> dict[str, str]:
    assert isinstance(packet, dict)
    source = packet["source"]
    items = [] if source is None else [source if str(source).startswith("<") else f"<{source}>"]
    items += [f"<{g}>" for g in packet["generators"]]
    return {"lift": "op<" + OPCODE + "".join(items) + ">", "source": "<>"}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}

    def w(fid: str) -> dict[str, str]:
        obj = by[fid]
        assert isinstance(obj, dict)
        return wire(obj["packet"])

    return [
        {"id": "pos", "kind": "positive", "payload": w("pos")},
        {"expected_code": "R001_GENERATORS", "id": "near_swap", "kind": "near_miss", "payload": w("near_swap")},
        {"clause": "C1", "expected_code": "R001_SOURCE_OMITTED", "id": "mut", "kind": "decisive_mutation",
         "payload": w("mut"), "repair": "pos"},
        {"clause": "C3", "expected_code": "R001_GENERATORS", "id": "swap", "kind": "decisive_mutation",
         "payload": w("near_swap"), "repair": "pos"},
    ]


def pairs(positive: object) -> list[list[str]]:
    return [["source:<>", "operand:0"], ["generator:0", "operand:1"], ["generator:1", "operand:2"]]
