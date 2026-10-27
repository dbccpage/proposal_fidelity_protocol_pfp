"""Dual Evaluator Consensus Engine for Challenge C040.

Coordinates Checker 1 (Field Reduction & Hodge Dualization) and
Checker 2 (Coset Group Theory & Root Systems), enforcing 100% agreement.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

try:
    from .coset_group_theory_checker import (
        verify_coset_group_theory_certificate,
    )
    from .field_reduction_checker import (
        verify_field_reduction_certificate,
    )
except (ImportError, ValueError):
    from coset_group_theory_checker import (  # type: ignore
        verify_coset_group_theory_certificate,
    )
    from field_reduction_checker import (  # type: ignore
        verify_field_reduction_certificate,
    )


class CheckerDisagreementError(Exception):
    """Raised when Checker 1 and Checker 2 produce divergent verdicts on a case."""


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    verdict: str  # "PASS" | "FAIL" | "CHECKER_DISAGREEMENT"
    agreed: bool
    checker1: dict[str, Any]  # {"ok": bool, "message": str}
    checker2: dict[str, Any]  # {"ok": bool, "message": str}


def evaluate_answer(
    case: Mapping[str, Any],
    answer: Mapping[str, Any],
) -> EvaluationResult:
    """Evaluates case and answer under both independent checkers."""
    ok1, msg1 = verify_field_reduction_certificate(case, answer)
    ok2, msg2 = verify_coset_group_theory_certificate(case, answer)

    agreed = ok1 == ok2
    if ok1 and ok2:
        verdict = "PASS"
    elif (not ok1) and (not ok2):
        verdict = "FAIL"
    else:
        verdict = "CHECKER_DISAGREEMENT"

    cid = (
        str(case.get("case_id") or case.get("id") or "unknown_case")
        if isinstance(case, Mapping)
        else "malformed"
    )
    return EvaluationResult(
        case_id=cid,
        verdict=verdict,
        agreed=agreed,
        checker1={"ok": ok1, "message": msg1},
        checker2={"ok": ok2, "message": msg2},
    )


def evaluate_dual(
    case: Mapping[str, Any],
    answer: Mapping[str, Any],
) -> dict[str, Any]:
    """Dict-based consensus interface for commit-reveal runner and test suites."""
    res = evaluate_answer(case, answer)
    return {
        "case_id": res.case_id,
        "verdict": res.verdict,
        "agreed": res.agreed,
        "checker1_field_reduction": res.checker1,
        "checker2_coset_group_theory": res.checker2,
    }


def assert_dual_agreement(
    case: Mapping[str, Any],
    answer: Mapping[str, Any],
) -> tuple[bool, str]:
    """Asserts that both checkers agree and accept the result.

    Raises CheckerDisagreementError on divergence.
    """
    res = evaluate_answer(case, answer)
    if not res.agreed:
        raise CheckerDisagreementError(
            f"Checker divergence on case {res.case_id}: "
            f"C1 ({res.checker1['ok']}): {res.checker1['message']} vs "
            f"C2 ({res.checker2['ok']}): {res.checker2['message']}"
        )
    if res.verdict != "PASS":
        return (
            False,
            f"Both checkers rejected result: {res.checker1['message']} | {res.checker2['message']}",
        )
    return True, "DUAL_PASS"
