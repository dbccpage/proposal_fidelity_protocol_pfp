"""Demo 002 Runner: Generalization & Problem Declaration Suite.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Dict, List

from ...domain.stages.demos import CheckResult, DemoRunReceipt, DemoSpec
from omega_engine_pfp.infrastructure.pilot_runners.declaration_checks import (
    evaluate_generalization_antibodies,
)
from omega_engine_pfp.infrastructure.pilot_runners.declaration_checks import (
    test_bivariate_mixed_derivative_oracle,
)
from omega_engine_pfp.infrastructure.pilot_runners.declaration_checks import (
    test_refusal_payload_masking_oracle,
)


def run_demo_002(spec: DemoSpec) -> DemoRunReceipt:
    start_time = time.perf_counter()
    checks: List[CheckResult] = []

    # 1. Oracle: Bivariate non-polynomial mixed derivative
    fake_primitive = "(1/2) * x * y / ln(2)"
    exact_primitive = "(-1/2) * (x^2) * exp(-y)"
    fake_rejected = not test_bivariate_mixed_derivative_oracle(fake_primitive, "x * exp(-y)")
    exact_admitted = test_bivariate_mixed_derivative_oracle(exact_primitive, "x * exp(-y)")
    checks.append(
        CheckResult(
            name="bivariate_mixed_derivative_oracle",
            passed=(fake_rejected and exact_admitted),
            observed=f"fake_rejected={fake_rejected}, exact_admitted={exact_admitted}",
            expected="True",
        )
    )

    # 2. Oracle: Refusal payload candidate scalar leakage
    leaked_payload = {"status": "refuse_missing_boundary", "candidate_scalar_value": "1/4"}
    masked_payload = {
        "status": "refuse_missing_boundary",
        "candidate_scalar_value": None,
        "reason": "undeclared domain",
    }
    leak_rejected = not test_refusal_payload_masking_oracle(leaked_payload)
    mask_admitted = test_refusal_payload_masking_oracle(masked_payload)
    checks.append(
        CheckResult(
            name="refusal_payload_masking_oracle",
            passed=(leak_rejected and mask_admitted),
            observed=f"leak_rejected={leak_rejected}, mask_admitted={mask_admitted}",
            expected="True",
        )
    )

    # 3. Load golden generalization result and evaluate antibodies against spec
    repo_root = next(
        (p for p in Path(__file__).resolve().parents if (p / ".git").exists()),
        None,
    )
    if repo_root is None:
        checks.append(CheckResult(
            name="generalization_source_context", passed=False,
            error_message="HISTORICAL_SOURCE_CONTEXT_UNAVAILABLE: repository required",
        ))
    demo_002_dir = (
        repo_root
        / "omega_engine_education"
        / "documentation"
        / "030_the_symbol_game_proposal_fidelity_protocol_pfp"
        / "pilots"
        / "demo_002"
    ) if repo_root is not None else None
    res_path = demo_002_dir / "generalization" / "result.json" if demo_002_dir is not None else None
    spec_path = demo_002_dir / "problem_declaration.json" if demo_002_dir is not None else None

    if res_path is not None and spec_path is not None and res_path.exists() and spec_path.exists():
        gen_data = json.loads(res_path.read_text(encoding="utf-8"))
        spec_data = json.loads(spec_path.read_text(encoding="utf-8"))
        antibodies = gen_data.get("generalized_antibodies", [])
        gate_res = evaluate_generalization_antibodies(antibodies, spec_data)

        for assertion in gate_res.assertions:
            checks.append(
                CheckResult(
                    name=assertion.name,
                    passed=assertion.passed,
                    observed=assertion.detail,
                    expected="Pass",
                    error_message=None if assertion.passed else assertion.detail,
                )
            )
    elif repo_root is not None:
        checks.append(CheckResult(
            name="generalization_source_bytes", passed=False,
            error_message="HISTORICAL_SOURCE_BYTES_UNAVAILABLE: golden result or declaration missing",
        ))

    duration = time.perf_counter() - start_time
    all_passed = all(c.passed for c in checks)

    return DemoRunReceipt(
        demo_id=spec.id,
        runner_id="runner_002_generalization",
        all_passed=all_passed,
        checks=checks,
        duration_sec=duration,
        terminal_status="Exact" if all_passed else "Refused",
        receipt_sha256="",
        authority_effect="None",
    )
