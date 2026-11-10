"""Reference self-consistency gate for C018.

AuthorityEffect: None.

Scores the frozen reference solver against this package's own judge packet. It
evaluates no model and is not a Woland verdict. Labels:
REFERENCE_SELF_CONSISTENT, REFERENCE_SELF_INCONSISTENT, OPEN_RESIDUAL.
Decisions use exact counts only; empty suites and missing counts are inconsistent.
"""

from __future__ import annotations

from typing import Any

TERMINAL_REFERENCE_SELF_CONSISTENT = "REFERENCE_SELF_CONSISTENT"
TERMINAL_REFUSE = "REFERENCE_SELF_INCONSISTENT"
TERMINAL_OPEN_RESIDUAL = "OPEN_RESIDUAL"
GATE_SCOPE = "REFERENCE_SOLVER_SELF_CHECK"


def _count(summary: dict[str, Any], key: str) -> int | None:
    value = summary.get(key)
    return value if type(value) is int and value >= 0 else None


def evaluate_woland_gate(
    evaluation_summary: dict[str, Any],
) -> dict[str, Any]:
    """Return {"verdict", "reason", "details"} for a reference self-consistency run."""
    passed_cases = _count(evaluation_summary, "passed_cases")
    total_cases = _count(evaluation_summary, "total_cases")
    mutations_total = _count(evaluation_summary, "mutations_total")
    mutations_killed = _count(evaluation_summary, "mutations_killed")
    budget_passed = evaluation_summary.get("budget_passed")
    details = {**evaluation_summary, "gate_scope": GATE_SCOPE}

    def refuse(reason: str) -> dict[str, Any]:
        return {"verdict": TERMINAL_REFUSE, "reason": reason, "details": details}

    if budget_passed is not True:
        return refuse("Budget gate did not pass")
    if total_cases is None or passed_cases is None:
        return refuse("Case counts missing or not non-negative ints")
    if total_cases == 0:
        return refuse("Empty judge suite: 0 cases scored")
    if passed_cases != total_cases:
        return refuse(f"Only {passed_cases}/{total_cases} cases passed")
    if mutations_total is None or mutations_killed is None:
        return refuse("Mutation counts missing or not non-negative ints")
    if mutations_total == 0:
        return refuse("Empty mutation suite: 0 mutations run")
    if mutations_killed != mutations_total:
        return refuse(
            f"{mutations_total - mutations_killed} of {mutations_total} mutations survived the checkers"
        )

    return {
        "verdict": TERMINAL_REFERENCE_SELF_CONSISTENT,
        "reason": (
            f"Reference outputs accepted on {passed_cases}/{total_cases} cases; "
            f"{mutations_killed}/{mutations_total} mutations rejected"
        ),
        "details": details,
    }
