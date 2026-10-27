"""Regression tests for the C017 epistemic immune transfer harness."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from pfp.tests.demo_004.b_cohomology.c017_nonabelian_lattice_holonomy.eval_epistemic_immune_transfer import (
    NONABELIAN_ANTIBODIES,
    BudgetExceededError,
    BudgetGuard,
    build_c017_prompt,
    run_transfer_benchmark,
)

CHALLENGE_DIR = Path(__file__).resolve().parents[1]


def test_antibody_prompt_contains_every_typed_guard() -> None:
    case_path = CHALLENGE_DIR / "judge_packet" / "cases" / "base" / "base_01.json"
    case = json.loads(case_path.read_text(encoding="utf-8"))

    prompt = build_c017_prompt(case, include_antibodies=True)

    for antibody in NONABELIAN_ANTIBODIES:
        assert antibody["code"] in prompt


def test_budget_guard_refuses_before_network_request() -> None:
    guard = BudgetGuard(ceiling_usd=0.000001)

    with pytest.raises(BudgetExceededError, match="refusing request"):
        guard.reserve_call(
            model="meta-llama/llama-3.3-70b-instruct",
            prompt="x" * 100,
            max_output_tokens=2000,
        )


def test_dry_run_needs_no_provider_and_binds_exact_report_bytes(tmp_path: Path) -> None:
    output = tmp_path / "new-run"
    result = run_transfer_benchmark(dry_run=True, output_dir=output)

    assert result["total_cost_usd"] == 0.0
    assert result["evidence_grade"] == "HOST_REFERENCE_SELF_CONSISTENCY"
    assert all(case["baseline"]["passed"] for case in result["cases_evaluated"])
    assert all(case["immune_assisted"]["passed"] for case in result["cases_evaluated"])

    report_bytes = (output / "immune_transfer_report.json").read_bytes()
    receipt = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["sha256"] == hashlib.sha256(report_bytes).hexdigest()
    assert receipt["status"] == "PASS"
    assert receipt["status_scope"] == "harness_execution"
    assert receipt["evidence_grade"] == "HOST_REFERENCE_SELF_CONSISTENCY"
    assert b"\r\n" not in report_bytes
