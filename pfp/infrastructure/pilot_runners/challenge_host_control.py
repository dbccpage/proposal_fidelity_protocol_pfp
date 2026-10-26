"""Execute one source-bound Demo 004 host control, not a synthetic suite PASS.

AuthorityEffect: None. NO_LLM fixture verification is not a neural result.
"""

from __future__ import annotations

import json
import time

from ...domain.stages.demos import CheckResult, DemoRunReceipt, DemoSpec
from omega_engine_pfp.infrastructure.challenge_execution import isolated
from omega_engine_pfp.infrastructure.challenge_live import choose_case


def run_demo_004(spec: DemoSpec) -> DemoRunReceipt:
    start = time.perf_counter()
    try:
        challenge = spec.expectations.get("challenge_id", "C039")
        split = spec.expectations.get("split", "development")
        ordinal = int(spec.expectations.get("ordinal", "0"))
        row = choose_case(challenge, split, ordinal)
        outcome = isolated(dict(kind="NO_LLM", row=row), timeout=20)
        observed = dict(
            challenge=challenge,
            case_id=row["case_id"],
            source_sha256=row["sha256"],
            execution_mode="NO_LLM",
            provider_calls=0,
            result=outcome,
        )
    except (ValueError, IndexError, KeyError, OSError) as exc:
        outcome = dict(status="REFUSED", reason=str(exc))
        observed = dict(execution_mode="NO_LLM", provider_calls=0, result=outcome)
    passed = outcome.get("status") == "FIXTURE_VERIFIED"
    return DemoRunReceipt(
        demo_id=spec.id,
        runner_id="runner_004_finite_control",
        all_passed=passed,
        checks=[
            CheckResult(
                name="source_bound_finite_control",
                passed=passed,
                observed=json.dumps(observed, sort_keys=True),
                expected="FIXTURE_VERIFIED for the selected case only; no whole-suite or model claim",
                error_message=None
                if passed
                else outcome.get("reason", outcome.get("failure_class")),
            )
        ],
        duration_sec=time.perf_counter() - start,
        terminal_status=outcome["status"],
        authority_effect="None",
    )
