"""Demo 000 Runner: catalog inventory and two finite host controls.

AuthorityEffect: None.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from ...domain.stages.demos import CheckResult, DemoRunReceipt, DemoSpec
from omega_engine_pfp.infrastructure.pilot_runners.mssn_checks import evaluate_demo_n02
from omega_engine_pfp.infrastructure.pilot_runners.mssn_checks import evaluate_demo_n03
from omega_engine_pfp.infrastructure.pilot_runners.mssn_seeds import (
    MSSN_SEEDS_CATALOG as SEEDS_MSSN50,
)


def run_demo_000(spec: DemoSpec) -> DemoRunReceipt:
    start_time = time.perf_counter()
    checks: List[CheckResult] = []

    # 1. Verify seeds count
    seed_count = len(SEEDS_MSSN50)
    checks.append(
        CheckResult(
            name="mssn50_seed_count",
            passed=(seed_count >= 50),
            observed=str(seed_count),
            expected=">=50",
            error_message=None if seed_count >= 50 else f"Expected >=50 seeds, got {seed_count}",
        )
    )

    # These are explicit host fixtures, not executions of fifty model tasks.
    sample_payload_n02 = {
        "pair_decoded": ["a", "b"], "edge_decoded": {"source":"a","target":"b"},
        "reports":[0,0], "tagged_reports":[[0,0],[0,1]],
        "endpoint_support":["a","b"], "occurrence_counts":[1,2,3],
    }
    res_n02 = evaluate_demo_n02(sample_payload_n02)
    checks.append(
        CheckResult(
            name="eval_seed_demo_n02",
            passed=res_n02.passed,
            observed="PASS" if res_n02.passed else "FAIL",
            expected="PASS",
            error_message="; ".join(res_n02.failure_reasons) if not res_n02.passed else None,
        )
    )

    sample_payload_n03 = {
        "boundary_1":[[-1,-1,0],[1,0,-1],[0,1,1]], "boundary_2":[[1],[-1],[1]],
        "cycle":[1,-1,1], "cycle_boundary":[0,0,0], "h1_before":1,"h1_after":0,
        "retraction_obstruction":"nonzero old cycle becomes a boundary",
    }
    res_n03 = evaluate_demo_n03(sample_payload_n03)
    checks.append(
        CheckResult(
            name="eval_seed_demo_n03",
            passed=res_n03.passed,
            observed="PASS" if res_n03.passed else "FAIL",
            expected="PASS",
            error_message="; ".join(res_n03.failure_reasons) if not res_n03.passed else None,
        )
    )

    for name, evaluator, candidate, field in (
        ("n02_missing_tagged_report_refused", evaluate_demo_n02, sample_payload_n02, "tagged_reports"),
        ("n03_wrong_boundary_refused", evaluate_demo_n03, sample_payload_n03, "boundary_2"),
    ):
        mutation=dict(candidate)
        mutation.pop(field)
        refused=not evaluator(mutation).passed
        checks.append(CheckResult(name=name,passed=refused,observed=str(refused),expected="True"))

    duration = time.perf_counter() - start_time
    all_passed = all(c.passed for c in checks)

    return DemoRunReceipt(
        demo_id=spec.id,
        runner_id="runner_000_mssn50",
        all_passed=all_passed,
        checks=checks,
        duration_sec=duration,
        terminal_status="Exact" if all_passed else "Refused",
        receipt_sha256="",
        authority_effect="None",
    )
