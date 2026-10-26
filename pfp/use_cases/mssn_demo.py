"""Evaluate the declared controls through an injected research checker."""

from __future__ import annotations

import copy
from typing import Any

from omega_engine_pfp.domain.demos import CheckerPort, DemoRefusal


def evaluate_cases(
    checker: CheckerPort,
    cases: list[dict[str, Any]],
    *,
    raise_on_mismatch: bool = False,
) -> list[dict[str, Any]]:
    """Evaluate candidate cases with optional typed refusal on expectation mismatch (Prompt 53)."""
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise DemoRefusal("INVALID_CASE_CATALOG")
    outcomes = []
    for case in cases:
        observed = checker.check(copy.deepcopy(case["payload"]))
        if not (
            type(observed) is tuple and len(observed) == 2 and observed[0] in ("PASS", "REFUSED")
        ):
            raise DemoRefusal("INVALID_CHECKER_RESULT", case["id"])
        matches = list(observed) == case["expected"]
        if not matches and raise_on_mismatch:
            raise DemoRefusal("EXPECTATION_MISMATCH", case["id"])
        outcomes.append(
            {
                "case_id": case["id"],
                "outcome": observed[0],
                "code": observed[1],
                "expected": case["expected"],
                "matches_expectation": matches,
            }
        )
    return outcomes


def assert_expectations_match(outcomes: list[dict[str, Any]]) -> None:
    """Ensure that all evaluated case outcomes match their expected outcomes, raising a typed error if not."""
    for out in outcomes:
        if not out.get("matches_expectation", False):
            raise DemoRefusal("EXPECTATION_MISMATCH", str(out.get("case_id")))


__all__ = [
    "assert_expectations_match",
    "evaluate_cases",
]
