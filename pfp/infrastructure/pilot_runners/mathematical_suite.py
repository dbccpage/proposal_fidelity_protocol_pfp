"""Retain the unmet obligations of the retired Demo 003 aggregate.

AuthorityEffect: None.
"""

from __future__ import annotations

import time

from ...domain.stages.demos import CheckResult, DemoRunReceipt, DemoSpec


def run_demo_003(spec: DemoSpec) -> DemoRunReceipt:
    start_time = time.perf_counter()
    checks = [
        CheckResult(
            name="sub_demo_census",
            passed=False,
            expected="12 demos indexed",
            error_message=(
                "DEMO_003_AGGREGATE_RETIRED: the original 12-demo aggregate has no "
                "current executable census. Select a current named scenario explicitly; "
                "its result does not close this aggregate."
            ),
        ),
        CheckResult(
            name="mub6_regge_triangulation",
            passed=False,
            expected="Deficit angle < 1e-9",
            error_message=(
                "ILLUSTRATION_ONLY: the retained demo_mub6_regge fixture is not "
                "promotable and supplies no measured hinge deficit or MUB/Regge evidence."
            ),
        ),
        CheckResult(
            name="cohomology_battery",
            passed=False,
            expected="Nilpotency holds",
            error_message=(
                "SCENARIO_RETIRED: the original cohomology battery is unavailable; "
                "no boundary matrices were executed and no d1 @ d0 result is claimed."
            ),
        ),
    ]

    duration = time.perf_counter() - start_time

    return DemoRunReceipt(
        demo_id=spec.id,
        runner_id="runner_003_master",
        all_passed=False,
        checks=checks,
        duration_sec=duration,
        terminal_status="Refused",
        receipt_sha256="",
        authority_effect="None",
    )
