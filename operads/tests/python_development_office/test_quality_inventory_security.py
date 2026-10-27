"""Security checks for repository boundary enforcement."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from operads.application.python_development_office.quality_inventory import (
    PythonQualityInventoryGate,
    QualityInventoryDependencies,
)
from operads.application.python_development_office.test_receipt_verification import (
    ReceiptVerificationRequest,
    verify_test_execution_receipts,
)
from operads.domain.operad.errors import Err
from operads.domain.python_development_office.quality_inventory import (
    TestTierRule as TierRule,
)
from operads.infrastructure.python_development_office.quality_adapters import (
    FileSystemPythonInventoryRepository,
)
from operads.tests.python_development_office.quality_test_support import (
    FixedUtcClock,
    StubComplexityAnalyzer,
    StubExecutionReceiptRepository,
    execution_receipt,
    file_record,
    policy,
)


def test_target_escape_returns_typed_refusal(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("secret = 1\n", encoding="utf-8")
    gate = PythonQualityInventoryGate(
        QualityInventoryDependencies(
            project_root=project,
            policy=policy(),
            policy_bytes=b"test-policy",
            sources=FileSystemPythonInventoryRepository(),
            complexity=StubComplexityAnalyzer(),
            execution_receipts=StubExecutionReceiptRepository(),
            clock=FixedUtcClock(),
        )
    )

    result = gate.run(outside)

    assert isinstance(result, Err)
    assert result.error.code == "INVENTORY_EXECUTION_ERROR"
    assert "escapes project root" in result.error.detail


def test_receipt_directory_escape_returns_typed_refusal(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "module.py").write_text("value = 1\n", encoding="utf-8")
    gate = PythonQualityInventoryGate(
        QualityInventoryDependencies(
            project_root=project,
            policy=policy(),
            policy_bytes=b"test-policy",
            sources=FileSystemPythonInventoryRepository(),
            complexity=StubComplexityAnalyzer(),
            execution_receipts=StubExecutionReceiptRepository(),
            clock=FixedUtcClock(),
        )
    )

    result = gate.run(project, receipt_directory=tmp_path / "outside-receipts")

    assert isinstance(result, Err)
    assert "receipt directory escapes project root" in result.error.detail


def test_receipt_target_escape_is_blocking() -> None:
    escaped = execution_receipt(target_path="../outside/test_example.py")
    evidence, findings = _verify(escaped)

    assert evidence[0].status == "INVALID_RECEIPT"
    assert "escapes repository" in findings[0].detail


def test_forged_pass_with_nonzero_exit_is_blocking() -> None:
    forged = replace(execution_receipt(), exit_code=1, asserted_status="PASS")
    evidence, findings = _verify(forged)

    assert evidence[0].status == "INVALID_RECEIPT"
    assert "PASS requires exit code zero" in findings[0].detail


def _verify(receipt):
    return verify_test_execution_receipts(
        ReceiptVerificationRequest(
            rules=(TierRule("unit", ("tests/unit/*.py",)),),
            files=(file_record("tests/unit/test_example.py"),),
            receipts=(receipt,),
            source_sha256="a" * 64,
            policy_sha256="b" * 64,
            now=FixedUtcClock().now(),
            max_age_hours=168,
        )
    )
