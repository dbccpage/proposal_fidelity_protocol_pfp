"""Dual Evaluator Consensus Engine for C033.

Runs Checker 1 (Freudenthal) and Checker 2 (Kostant), asserting 100% agreement.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from omega_engine_pfp.tests.demo_004.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.judge_packet.checkers.freudenthal_checker import (
    verify_freudenthal_certificate,
)
from omega_engine_pfp.tests.demo_004.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.judge_packet.checkers.kostant_checker import (
    verify_kostant_certificate,
)


def evaluate_dual(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluates case and result under both independent checkers."""
    ok1, msg1 = verify_freudenthal_certificate(case, result)
    ok2, msg2 = verify_kostant_certificate(case, result)

    agreed = ok1 == ok2
    verdict = "PASS" if (ok1 and ok2) else ("FAIL" if (not ok1 and not ok2) else "DISAGREEMENT")

    return {
        "case_id": case.get("case_id") or case.get("id"),
        "checker1_freudenthal": {"ok": ok1, "message": msg1},
        "checker2_kostant": {"ok": ok2, "message": msg2},
        "agreed": agreed,
        "verdict": verdict,
    }


def assert_dual_agreement(
    case: Mapping[str, Any],
    result: Mapping[str, Any],
) -> tuple[bool, str]:
    """Asserts that both checkers agree and accept the result."""
    eval_res = evaluate_dual(case, result)
    if not eval_res["agreed"]:
        return (
            False,
            f"Checkers disagreed: C1={eval_res['checker1_freudenthal']['message']}, C2={eval_res['checker2_kostant']['message']}",
        )
    if eval_res["verdict"] != "PASS":
        return (
            False,
            f"Both checkers rejected result: C1={eval_res['checker1_freudenthal']['message']}",
        )
    return True, "DUAL_PASS"
