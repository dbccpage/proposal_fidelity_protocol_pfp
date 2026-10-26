"""Mutation-style boundary checks for strict greater-than thresholds."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from omega_engine_operads.application.python_development_office.quality_inventory import (
    PythonQualityInventoryGate,
    QualityInventoryDependencies,
)
from omega_engine_operads.application.python_development_office.test_receipt_verification import (
    ReceiptVerificationRequest,
    verify_test_execution_receipts,
)
from omega_engine_operads.domain.operad.errors import Ok
from omega_engine_operads.domain.python_development_office.quality_inventory import (
    TestTierRule as TierRule,
)
from omega_engine_operads.infrastructure.python_development_office.quality_adapters import (
    FileSystemPythonInventoryRepository,
)
from omega_engine_operads.tests.python_development_office.quality_test_support import (
    FixedUtcClock,
    StubComplexityAnalyzer,
    StubExecutionReceiptRepository,
    execution_receipt,
    file_record,
    policy,
)


def test_exact_limit_passes_and_one_over_limit_fails(tmp_path: Path) -> None:
    exact = tmp_path / "exact.py"
    exact.write_text("a = 1\nb = 2\n", encoding="utf-8")
    gate = PythonQualityInventoryGate(
        QualityInventoryDependencies(
            project_root=tmp_path,
            policy=policy(physical_loc=2),
            policy_bytes=b"test-policy",
            sources=FileSystemPythonInventoryRepository(),
            complexity=StubComplexityAnalyzer(),
            execution_receipts=StubExecutionReceiptRepository(),
            clock=FixedUtcClock(),
        )
    )
    exact_result = gate.run(exact)
    assert isinstance(exact_result, Ok)
    assert exact_result.value.status == "STRUCTURAL_PASS"

    exact.write_text("a = 1\nb = 2\nc = 3\n", encoding="utf-8")
    mutated_result = gate.run(exact)
    assert isinstance(mutated_result, Ok)
    assert mutated_result.value.status == "BLOCKED"
    assert [finding.code for finding in mutated_result.value.findings] == ["PHYSICAL_LOC"]


def test_mutation_score_threshold_kills_less_than_mutant() -> None:
    rule = TierRule("mutation_engine", ("tests/mutation/*.py",), "mutation_engine", 80.0)
    baseline = execution_receipt(
        tier="mutation_engine",
        execution_kind="mutation_engine",
        target_path="tests/mutation",
        mutation_score=80.0,
    )

    passing, passing_findings = _verify_mutation(rule, baseline)
    failing, failing_findings = _verify_mutation(rule, replace(baseline, mutation_score=79.99))

    assert passing[0].status == "MUTATION_ENGINE_VERIFIED"
    assert passing_findings == ()
    assert failing[0].status == "INVALID_RECEIPT"
    assert "below required" in failing_findings[0].detail


def test_mutation_style_cannot_claim_engine_score() -> None:
    rule = TierRule("mutation_style", ("tests/mutation/*.py",), "mutation_style")
    receipt = execution_receipt(
        tier="mutation_style",
        execution_kind="mutation_style",
        target_path="tests/mutation",
    )

    evidence, findings = _verify_mutation(rule, replace(receipt, mutation_score=100.0))

    assert evidence[0].status == "INVALID_RECEIPT"
    assert "non-engine receipt claims mutation score" in findings[0].detail


def _verify_mutation(rule: TierRule, receipt):
    return verify_test_execution_receipts(
        ReceiptVerificationRequest(
            rules=(rule,),
            files=(file_record("tests/mutation/test_mutation.py"),),
            receipts=(receipt,),
            source_sha256="a" * 64,
            policy_sha256="b" * 64,
            now=FixedUtcClock().now(),
            max_age_hours=168,
        )
    )
