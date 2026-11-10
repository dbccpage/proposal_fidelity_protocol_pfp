"""Reference self-consistency gate for C015: Persistent Homology Barcodes.

AuthorityEffect: None.

Scores the frozen reference solver against this package's own judge packet. It
evaluates no model and is not a Woland verdict. Labels:
REFERENCE_SELF_CONSISTENT, REFERENCE_SELF_INCONSISTENT, OPEN_RESIDUAL.

Decisions use exact counts only. An empty judge suite, an empty mutation suite,
or missing counts are inconsistent.
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


def evaluate_woland_terminal_gate(
    eval_summary: dict[str, Any],
    budget_passed: bool,
) -> tuple[str, str, dict[str, Any]]:
    """Return (label, reason, details) for a reference self-consistency run."""
    total_cases = _count(eval_summary, "total_cases")
    passed_cases = _count(eval_summary, "passed_cases")
    mutations_total = _count(eval_summary, "mutations_total")
    mutations_killed = _count(eval_summary, "mutations_killed")

    details = {
        "budget_passed": budget_passed,
        "gate_scope": GATE_SCOPE,
        "mutations_killed": mutations_killed,
        "mutations_total": mutations_total,
        "passed_cases": passed_cases,
        "total_cases": total_cases,
    }

    if budget_passed is not True:
        return TERMINAL_REFUSE, "Budget gate did not pass", details
    if total_cases is None or passed_cases is None:
        return TERMINAL_REFUSE, "Case counts missing or not non-negative ints", details
    if total_cases == 0:
        return TERMINAL_REFUSE, "Empty judge suite: 0 cases scored", details
    if mutations_total is None or mutations_killed is None:
        return TERMINAL_REFUSE, "Mutation counts missing or not non-negative ints", details
    if mutations_total == 0:
        return TERMINAL_REFUSE, "Empty mutation suite: 0 mutations run", details
    if mutations_killed != mutations_total:
        return (
            TERMINAL_REFUSE,
            f"{mutations_total - mutations_killed} of {mutations_total} mutations survived the checkers",
            details,
        )
    if passed_cases != total_cases:
        return (
            TERMINAL_REFUSE,
            f"{total_cases - passed_cases} of {total_cases} cases failed",
            details,
        )

    return (
        TERMINAL_REFERENCE_SELF_CONSISTENT,
        f"Reference outputs accepted on {passed_cases}/{total_cases} cases; "
        f"{mutations_killed}/{mutations_total} mutations rejected",
        details,
    )
