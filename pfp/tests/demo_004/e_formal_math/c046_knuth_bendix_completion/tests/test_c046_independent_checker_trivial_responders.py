"""C046 second checker: trivial responders must fail; values are rechecked independently.

Counterexamples named by these tests (all passed the old independent checker):
- the empty object {};
- a refuse-all responder {"status": "REFUSED", "reason": <any code>, "witness": {}} on a
  solvable case;
- a COMPLETE answer with an empty rule list, and a flipped is_confluent verdict.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from omega_engine_pfp.tests.demo_004.e_formal_math.c046_knuth_bendix_completion.judge_packet.checkers.independent_checker import (
    check_independent,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c046_knuth_bendix_completion.reference_solver.solver import (
    solve,
)

PKG = Path(__file__).resolve().parent.parent
HIDDEN = json.loads(
    next((PKG / "judge_packet" / "hidden_cases").glob("*.json")).read_text(encoding="utf-8")
)
SOLVABLE = [c for c in HIDDEN if c.get("category") != "poisoned"]
REASONS = (
    "ORDER_FAILURE",
    "MALFORMED_TERM",
    "MAX_STEPS_EXCEEDED",
    "MALFORMED_INPUT",
    "UNKNOWN_TASK",
)


@pytest.mark.parametrize("case", HIDDEN, ids=lambda c: c["case_id"])
def test_reference_answers_pass(case: dict) -> None:
    ok, msg = check_independent(case, solve(case))
    assert ok, msg


@pytest.mark.parametrize("case", SOLVABLE, ids=lambda c: c["case_id"])
def test_trivial_responders_fail_on_solvable_cases(case: dict) -> None:
    cid = case["case_id"]
    responders = [{}, {"case_id": cid}, {"case_id": cid, "status": "UNKNOWN"}]
    for reason in REASONS:
        witness = {"unorientable_equation": ["f(x)", "x"]} if reason == "ORDER_FAILURE" else {}
        responders.append(
            {"case_id": cid, "status": "REFUSED", "reason": reason, "witness": witness}
        )
    for ans in responders:
        ok, msg = check_independent(case, ans)
        assert ok is False, f"{ans} accepted: {msg}"


def test_empty_rule_set_fails_on_completion() -> None:
    case = next(c for c in SOLVABLE if c["task"] == "COMPLETE")
    ans = {
        "case_id": case["case_id"],
        "status": "SOLVED",
        "task": "COMPLETE",
        "converged": True,
        "rules_count": 0,
        "rules": [],
        "joinability_certificates_count": 0,
    }
    ok, msg = check_independent(case, ans)
    assert ok is False, msg


@pytest.mark.parametrize(
    "case", [c for c in SOLVABLE if c["task"] == "CHECK_CONFLUENCE"], ids=lambda c: c["case_id"]
)
def test_flipped_confluence_verdict_fails(case: dict) -> None:
    ans = solve(case)
    ans["is_confluent"] = not ans["is_confluent"]
    ok, msg = check_independent(case, ans)
    assert ok is False, msg


def test_unreachable_normal_form_fails() -> None:
    case = next(c for c in SOLVABLE if c["task"] == "REDUCE")
    ans = solve(case)
    ans["normal_form"] = "zz_not_reachable"
    ok, msg = check_independent(case, ans)
    assert ok is False, msg
