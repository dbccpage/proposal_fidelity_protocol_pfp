"""Dual Evaluator for C032 (Six-Dimensional Supergravity Anomaly Cancellation).

Compares Checker 1 (Exact Algebraic Weight Certifier) and Checker 2 (Independent Matrix Certifier),
enforcing 100% concordance between independent verification routes.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping

from omega_engine_pfp.tests.demo_004.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.judge_packet.checkers.sugra_matrix_checker import (
    verify_sugra_matrix_certificate,
)
from omega_engine_pfp.tests.demo_004.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.judge_packet.checkers.sugra_weight_checker import (
    verify_sugra_weight_certificate,
)


class CheckerDisagreementError(Exception):
    """Raised when Checker 1 and Checker 2 disagree on a candidate certificate."""


def evaluate_dual(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluates case result with both independent checkers and returns consensus record."""
    ok1, msg1 = verify_sugra_weight_certificate(case, result)
    ok2, msg2 = verify_sugra_matrix_certificate(case, result)

    agreement = ok1 == ok2
    verdict = "PASS" if (ok1 and ok2) else "FAIL"

    return {
        "case_id": case.get("id", "unnamed"),
        "verdict": verdict,
        "agreement": agreement,
        "checker1": {"passed": ok1, "message": msg1},
        "checker2": {"passed": ok2, "message": msg2},
    }


def assert_dual_agreement(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Asserts that both checkers agree completely; raises CheckerDisagreementError if not."""
    res = evaluate_dual(case, result)
    if not res["agreement"]:
        raise CheckerDisagreementError(
            f"Checker disagreement on case {res['case_id']}: "
            f"Checker1: {res['checker1']['passed']} ({res['checker1']['message']}) vs "
            f"Checker2: {res['checker2']['passed']} ({res['checker2']['message']})"
        )
    return res
