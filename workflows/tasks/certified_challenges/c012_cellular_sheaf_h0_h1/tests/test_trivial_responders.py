"""C012 judge: a BUDGET_EXHAUSTED refusal is never a valid answer.

Found by the 2026-09-29 trivial-responder sweep: `_verify_refusal_warranted`
returned VALID for BUDGET_EXHAUSTED unconditionally, so the constant answer
{"status": "UNKNOWN", "refusal": "BUDGET_EXHAUSTED"} passed on all 68 judge cases.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from c012_cellular_sheaf_h0_h1.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c012_cellular_sheaf_h0_h1.reference_solver.solver import (
    solve,
)

JUDGE_CASES = sorted(
    (Path(sys.modules[evaluate_dual.__module__].__file__).resolve().parents[1] / "cases").rglob(
        "*.json"
    )
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_judge_cases_are_present() -> None:
    assert len(JUDGE_CASES) >= 60


@pytest.mark.parametrize("keys", [("refusal",), ("refusal_code",), ("refusal", "refusal_code")])
def test_budget_exhausted_refusal_fails_on_every_judge_case(keys: tuple[str, ...]) -> None:
    passes = []
    for path in JUDGE_CASES:
        case = _load(path)
        answer = {
            "id": case.get("id"),
            "status": "UNKNOWN",
            **{k: "BUDGET_EXHAUSTED" for k in keys},
        }
        if evaluate_dual(case, answer)["verdict"] == "PASS":
            passes.append(path.name)
    assert passes == []


def test_reference_answers_pass_every_judge_case() -> None:
    failures = [
        p.name for p in JUDGE_CASES if evaluate_dual(_load(p), solve(_load(p)))["verdict"] != "PASS"
    ]
    assert failures == []
