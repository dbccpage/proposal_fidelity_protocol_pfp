"""Unit checks for quality metric extraction and fail-closed classification."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from operads.application.python_development_office.quality_inventory import (
    PythonQualityInventoryGate,
    QualityInventoryDependencies,
)
from operads.application.python_development_office.test_receipt_verification import (
    ReceiptVerificationRequest,
    verify_test_execution_receipts,
)
from operads.domain.operad.errors import Ok
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


def _run(root: Path, configured_policy=None):
    gate = PythonQualityInventoryGate(
        QualityInventoryDependencies(
            project_root=root,
            policy=configured_policy or policy(),
            policy_bytes=b"test-policy",
            sources=FileSystemPythonInventoryRepository(),
            complexity=StubComplexityAnalyzer(),
            execution_receipts=StubExecutionReceiptRepository(),
            clock=FixedUtcClock(),
        )
    )
    result = gate.run(root)
    assert isinstance(result, Ok)
    return result.value


def test_reports_loc_span_nesting_and_argument_obstructions(tmp_path: Path) -> None:
    source = """def over(a, b, c):
    if a:
        for item in b:
            while item:
                if c:
                    return item
    return None
"""
    (tmp_path / "module.py").write_text(source, encoding="utf-8")
    receipt = _run(
        tmp_path,
        policy(physical_loc=3, function_span=5, arguments=2, nesting_depth=3),
    )

    assert receipt.status == "BLOCKED"
    assert {finding.code for finding in receipt.findings} == {
        "ARGUMENT_COUNT",
        "FUNCTION_SPAN",
        "NESTING_DEPTH",
        "PHYSICAL_LOC",
    }
    assert receipt.files[0].source_class == "maintained"
    assert "does not certify semantic DDD" in receipt.claim_ceiling


def test_unclassified_python_is_a_blocking_finding(tmp_path: Path) -> None:
    (tmp_path / "unowned.py").write_text("value = 1\n", encoding="utf-8")
    receipt = _run(tmp_path, policy(patterns=("owned/**/*.py",)))

    assert receipt.status == "BLOCKED"
    assert receipt.files == ()
    assert [finding.code for finding in receipt.findings] == ["UNCLASSIFIED_PYTHON"]


def test_ruff_complexity_value_is_retained_in_machine_receipt(tmp_path: Path) -> None:
    source = tmp_path / "complex.py"
    source.write_text("def complex_value():\n    return 1\n", encoding="utf-8")
    gate = PythonQualityInventoryGate(
        QualityInventoryDependencies(
            project_root=tmp_path,
            policy=policy(),
            policy_bytes=b"test-policy",
            sources=FileSystemPythonInventoryRepository(),
            complexity=StubComplexityAnalyzer(
                ((str(source), 1, "`complex_value` is too complex (12 > 10)"),)
            ),
            execution_receipts=StubExecutionReceiptRepository(),
            clock=FixedUtcClock(),
        )
    )

    result = gate.run(source)

    assert isinstance(result, Ok)
    finding = result.value.findings[0]
    assert finding.code == "C901_COMPLEXITY"
    assert finding.actual == 12
    assert finding.limit == 10


def test_valid_receipts_keep_mutation_style_distinct_from_engine_score() -> None:
    rules = (
        TierRule("unit", ("tests/unit/*.py",), "pytest"),
        TierRule("mutation_style", ("tests/mutation/*.py",), "mutation_style"),
        TierRule("mutation_engine", ("tests/mutation/*.py",), "mutation_engine", 80.0),
    )
    files = (
        file_record("tests/unit/test_example.py"),
        file_record("tests/mutation/test_mutation.py"),
    )
    receipts = (
        execution_receipt(),
        execution_receipt(
            tier="mutation_style",
            execution_kind="mutation_style",
            target_path="tests/mutation",
        ),
        execution_receipt(
            tier="mutation_engine",
            execution_kind="mutation_engine",
            target_path="tests/mutation",
            mutation_score=83.5,
        ),
    )

    evidence, findings = verify_test_execution_receipts(
        ReceiptVerificationRequest(
            rules=rules,
            files=files,
            receipts=receipts,
            source_sha256="a" * 64,
            policy_sha256="b" * 64,
            now=FixedUtcClock().now(),
            max_age_hours=168,
        )
    )

    assert not findings, "\n".join(
        f"{finding.code} {finding.path}:{finding.line} actual={finding.actual}"
        for finding in findings
    )
    assert [item.status for item in evidence] == [
        "VERIFIED_EXECUTION",
        "MUTATION_STYLE_VERIFIED",
        "MUTATION_ENGINE_VERIFIED",
    ]
    assert evidence[1].mutation_score is None
    assert evidence[2].mutation_score == 83.5


def test_stale_receipt_is_blocking() -> None:
    receipt = replace(
        execution_receipt(),
        completed_at=FixedUtcClock().now() - timedelta(hours=169),
    )
    evidence, findings = verify_test_execution_receipts(
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

    assert evidence[0].status == "INVALID_RECEIPT"
    assert findings[0].code == "INVALID_TEST_EXECUTION_RECEIPT"
    assert "stale" in findings[0].detail


def test_owned_production_files_meet_ast_metric_thresholds() -> None:
    root = Path(__file__).resolve().parents[3]
    paths = (
        "operads/domain/python_development_office/quality_errors.py",
        "operads/domain/python_development_office/quality_inventory.py",
        "operads/domain/python_development_office/quality_ports.py",
        "operads/domain/python_development_office/test_execution_receipt.py",
        "operads/application/python_development_office/quality_inventory.py",
        "operads/application/python_development_office/test_receipt_verification.py",
        "operads/infrastructure/python_development_office/quality_policy.py",
        "operads/infrastructure/python_development_office/quality_adapters.py",
        "operads/infrastructure/python_development_office/test_execution_receipts.py",
        "operads/infrastructure/python_development_office/output/quality_json_output.py",
        "operads/controllers/python_development_office_controller.py",
        "operads/frontend/cli/python_dev_cli.py",
    )
    gate = PythonQualityInventoryGate(
        QualityInventoryDependencies(
            project_root=root,
            policy=policy(),
            policy_bytes=b"test-policy",
            sources=FileSystemPythonInventoryRepository(),
            complexity=StubComplexityAnalyzer(),
            execution_receipts=StubExecutionReceiptRepository(),
            clock=FixedUtcClock(),
        )
    )

    findings = tuple(
        finding
        for path in paths
        for finding in gate.run(path).unwrap().findings
        if finding.code in {"PHYSICAL_LOC", "NESTING_DEPTH", "FUNCTION_SPAN", "ARGUMENT_COUNT"}
    )

    assert not findings, "\n".join(
        f"{finding.code} {finding.path}:{finding.line} actual={finding.actual}"
        for finding in findings
    )
