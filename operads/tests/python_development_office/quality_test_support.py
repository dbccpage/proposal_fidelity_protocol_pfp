"""Test builders and substitutes for Python quality inventory tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from omega_engine_operads.domain.python_development_office.quality_inventory import (
    ClassificationRule,
    FileQualityRecord,
    PythonQualityPolicy,
    PythonSourceClass,
    QualityThresholds,
    TestTierRule,
)
from omega_engine_operads.domain.python_development_office.test_execution_receipt import (
    TestExecutionReceipt,
)


@dataclass(frozen=True)
class StubComplexityAnalyzer:
    findings: tuple[tuple[str, int, str], ...] = ()

    def c901_findings(self, target: str, maximum: int) -> tuple[tuple[str, int, str], ...]:
        del target, maximum
        return self.findings


@dataclass(frozen=True)
class StubExecutionReceiptRepository:
    receipts: tuple[TestExecutionReceipt, ...] = ()

    def load(self, receipt_directory: str) -> tuple[TestExecutionReceipt, ...]:
        del receipt_directory
        return self.receipts


@dataclass(frozen=True)
class FixedUtcClock:
    value: datetime = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.value


def policy(
    *,
    patterns: tuple[str, ...] = ("*.py", "**/*.py"),
    physical_loc: int = 1000,
    function_span: int = 50,
    arguments: int = 5,
    nesting_depth: int = 3,
    test_tiers: tuple[TestTierRule, ...] = (),
) -> PythonQualityPolicy:
    return PythonQualityPolicy(
        schema="omega.python_quality_policy.v1",
        version="test-v1",
        classifications=(
            ClassificationRule(
                source_class=PythonSourceClass.MAINTAINED,
                patterns=patterns,
                rationale="test-owned maintained source",
                enforce_metrics=True,
            ),
        ),
        thresholds=QualityThresholds(
            physical_loc=physical_loc,
            cyclomatic_complexity=10,
            nesting_depth=nesting_depth,
            function_span=function_span,
            arguments=arguments,
        ),
        test_tiers=test_tiers,
        excluded_directories=("__pycache__",),
    )


def file_record(path: str) -> FileQualityRecord:
    return FileQualityRecord(
        path=path,
        source_class="test",
        classification_rationale="test fixture",
        enforce_metrics=True,
        physical_loc=1,
        source_sha256="f" * 64,
        functions=(),
    )


def execution_receipt(
    *,
    tier: str = "unit",
    execution_kind: str = "pytest",
    target_path: str = "tests/unit/test_example.py",
    mutation_score: float | None = None,
) -> TestExecutionReceipt:
    return TestExecutionReceipt(
        receipt_id=f"receipt-{tier}",
        tier=tier,
        execution_kind=execution_kind,
        command=("py", "-3.12", "-m", "pytest", target_path),
        python_version="3.12.12",
        exit_code=0,
        test_count=1,
        target_paths=(target_path,),
        source_sha256="a" * 64,
        policy_sha256="b" * 64,
        completed_at=datetime(2026, 10, 16, 11, 0, tzinfo=timezone.utc),
        asserted_status="PASS",
        mutation_score=mutation_score,
    )
