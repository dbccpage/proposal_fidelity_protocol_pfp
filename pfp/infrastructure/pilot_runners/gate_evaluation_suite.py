"""Demo 001 Runner: Round 00-99 Gate Evaluator Suite.

AuthorityEffect: None.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from ...domain.stages.demos import CheckResult, DemoRunReceipt, DemoSpec
from omega_engine_pfp.infrastructure.pilot_runners.gate_checks import evaluate_round_1
from omega_engine_pfp.infrastructure.pilot_runners.gate_checks import evaluate_round_2


def run_demo_001(spec: DemoSpec) -> DemoRunReceipt:
    start_time = time.perf_counter()
    checks: List[CheckResult] = []

    # Round 1 Evaluation (Negative control: typed refusal on underdetermined carrier)
    r1_payload = {
        "derived_under_policy": "SPK-001",
        "boundary_check": {
            "boundary_violation": True,
        },
        "numerical_result": {
            "selected_value": None,
            "decision": "refuse_missing_carrier",
        },
        "carrier_audit": [
            {"element": "carrier", "status": "missing"},
            {"element": "measure", "status": "undeclared"},
        ],
        "summary": "Round 1 typed refusal due to underdetermined carrier.",
    }
    res_r1 = evaluate_round_1(r1_payload)
    checks.append(
        CheckResult(
            name="demo_001_round_1_typed_refusal",
            passed=res_r1.passed,
            observed="PASS" if res_r1.passed else "FAIL",
            expected="PASS",
            error_message="; ".join(res_r1.failure_reasons) if not res_r1.passed else None,
        )
    )

    # Round 2 Evaluation (Positive control: admitted continuous on declared axioms)
    r2_payload = {
        "derived_under_policy": "SPK-001",
        "boundary_check": {
            "boundary_violation": False,
            "local_valid": True,
            "global_valid": True,
        },
        "numerical_result": {
            "selected_value": 50,
            "decision": "admit_continuous",
        },
        "carrier_audit": [
            {"element": "interval", "status": "declared"},
            {"element": "measure", "status": "declared"},
        ],
        "summary": "Round 2 admitted continuous definite integral.",
    }
    res_r2 = evaluate_round_2(r2_payload)
    checks.append(
        CheckResult(
            name="demo_001_round_2_admitted_continuous",
            passed=res_r2.passed,
            observed="PASS" if res_r2.passed else "FAIL",
            expected="PASS",
            error_message="; ".join(res_r2.failure_reasons) if not res_r2.passed else None,
        )
    )

    duration = time.perf_counter() - start_time
    all_passed = all(c.passed for c in checks)

    return DemoRunReceipt(
        demo_id=spec.id,
        runner_id="runner_001_rounds",
        all_passed=all_passed,
        checks=checks,
        duration_sec=duration,
        terminal_status="Exact" if all_passed else "Refused",
        receipt_sha256="",
        authority_effect="None",
    )
