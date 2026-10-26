"""Demo SN 000 Runner: S(n) Adversarial Machine Gate Benchmark Suite.

AuthorityEffect: None.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from ...domain.stages.demos import CheckResult, DemoRunReceipt, DemoSpec
from ...domain.sn_tower.sn_core import (
    S0Ground,
    S1Supply,
    S2Collapse,
    S3Separation,
    S4Orbit,
    S5Lift,
    S6Retraction,
)


def run_demo_sn_000(spec: DemoSpec) -> DemoRunReceipt:
    start_time = time.perf_counter()
    checks: List[CheckResult] = []

    # S(0) Ground check
    s0 = S0Ground()
    checks.append(
        CheckResult(
            name="stage_s0_ground_inertia",
            passed=s0.verify_inertia(),
            observed=str(s0.verify_inertia()),
            expected="True",
        )
    )

    # S(1) Supply subsingleton check
    s1 = S1Supply()
    checks.append(
        CheckResult(
            name="stage_s1_subsingleton",
            passed=s1.verify_subsingleton("token_alpha"),
            observed=str(s1.verify_subsingleton("token_alpha")),
            expected="True",
        )
    )

    # S(2) S_2 permutation collapse check
    s2 = S2Collapse()
    checks.append(
        CheckResult(
            name="stage_s2_collapse",
            passed=s2.verify_set_equivalence("a", "b"),
            observed=str(s2.verify_set_equivalence("a", "b")),
            expected="True",
        )
    )

    # S(3) Directed separation check
    s3 = S3Separation()
    checks.append(
        CheckResult(
            name="stage_s3_separation",
            passed=s3.verify_separation("u", "v"),
            observed=str(s3.verify_separation("u", "v")),
            expected="True",
        )
    )

    # S(4) Complete graph orbit closure check
    s4 = S4Orbit()
    checks.append(
        CheckResult(
            name="stage_s4_orbit_closure",
            passed=s4.verify_orbit_closure(["v1", "v2", "v3", "v4"]),
            observed=str(s4.verify_orbit_closure(["v1", "v2", "v3", "v4"])),
            expected="True",
        )
    )

    # S(5) Oriented triangle boundary check
    s5 = S5Lift()
    checks.append(
        CheckResult(
            name="stage_s5_oriented_lift",
            passed=s5.verify_lift_orientation("u", "v", "w"),
            observed=str(s5.verify_lift_orientation("u", "v", "w")),
            expected="True",
        )
    )

    # S(6) Retraction identity check
    s6 = S6Retraction()
    checks.append(
        CheckResult(
            name="stage_s6_retraction_identity",
            passed=s6.verify_retraction_identity(42),
            observed=str(s6.verify_retraction_identity(42)),
            expected="True",
        )
    )

    duration = time.perf_counter() - start_time
    all_passed = all(c.passed for c in checks)

    return DemoRunReceipt(
        demo_id=spec.id,
        runner_id="runner_sn_000_adversarial",
        all_passed=all_passed,
        checks=checks,
        duration_sec=duration,
        terminal_status="Exact" if all_passed else "Refused",
        receipt_sha256="",
        authority_effect="None",
    )
