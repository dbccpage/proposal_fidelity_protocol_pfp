"""Adapter for level 000: the engine's packets are already the target
checker's input (``{"packet": str}``), so every fixture passes unchanged.

Written against the stage-0 target checker on ``claude/p2-checkers``
(``b697efad``); it takes effect only when that checker is registered of
record under ``CHECKER_ID``.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_000"
CLAUSES = (("C1", "R000_INTERIOR_GLYPH"), ("C2", "R000_NESTED_PACKET"))
COEFFICIENT_DOMAIN = {"source": "bytes", "target": "bytes"}
SORTS = (("packet", "packet"),)
UNMAPPED_SORTS: tuple[str, ...] = ()
STRUCTURE_MAP_REASON = "the obligation names no structure map"


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    return [
        {"id": "pos", "kind": "positive", "payload": by["pos"]},
        {"expected_code": "R000_INTERIOR_GLYPH", "id": "near_glyph", "kind": "near_miss", "payload": by["near_glyph"]},
        {"clause": "C1", "expected_code": "R000_INTERIOR_GLYPH", "id": "mut", "kind": "decisive_mutation",
         "payload": by["mut"], "repair": "pos"},
        {"clause": "C2", "expected_code": "R000_NESTED_PACKET", "id": "nested", "kind": "decisive_mutation",
         "payload": by["own_neg"], "repair": "pos"},
    ]


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"packet:{positive['packet']}", f"packet:{positive['packet']}"]]
