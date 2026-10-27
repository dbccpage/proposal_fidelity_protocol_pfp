"""Integration checks for versioned policy loading and filesystem inventory."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

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
from operads.infrastructure.python_development_office.quality_policy import (
    load_quality_policy,
)
from operads.infrastructure.python_development_office.test_execution_receipts import (
    FileSystemTestExecutionReceiptRepository,
)
from operads.tests.python_development_office.quality_test_support import (
    FixedUtcClock,
    StubComplexityAnalyzer,
    StubExecutionReceiptRepository,
    execution_receipt,
    file_record,
)


def test_default_policy_classifies_production_test_and_frozen_sources(tmp_path: Path) -> None:
    (tmp_path / "package").mkdir()
    (tmp_path / "package" / "service.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "package" / "tests").mkdir()
    (tmp_path / "package" / "tests" / "test_service.py").write_text(
        "def test_value():\n    assert 1 == 1\n", encoding="utf-8"
    )
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / "snapshot.py").write_text("value = 1\n", encoding="utf-8")
    loaded_policy, raw = load_quality_policy()
    gate = PythonQualityInventoryGate(
        QualityInventoryDependencies(
            project_root=tmp_path,
            policy=loaded_policy,
            policy_bytes=raw,
            sources=FileSystemPythonInventoryRepository(),
            complexity=StubComplexityAnalyzer(),
            execution_receipts=StubExecutionReceiptRepository(),
            clock=FixedUtcClock(),
        )
    )

    result = gate.run(tmp_path)

    assert isinstance(result, Ok)
    classes = {record.path: record.source_class for record in result.value.files}
    assert classes["package/service.py"] == "maintained"
    assert classes["package/tests/test_service.py"] == "test"
    assert classes["artifacts/snapshot.py"] == "frozen"
    assert len(result.value.policy_sha256) == 64


def test_filesystem_receipt_loader_refuses_tampered_digest(tmp_path: Path) -> None:
    receipt = {
        "schema": "core.python_test_execution_receipt.v1",
        "receipt_id": "tampered",
        "tier": "unit",
        "execution_kind": "pytest",
        "command": ["py", "-3.12", "-m", "pytest", "tests/unit"],
        "python_version": "3.12.12",
        "exit_code": 0,
        "test_count": 4,
        "target_paths": ["tests/unit"],
        "source_sha256": "not-a-digest",
        "policy_sha256": "b" * 64,
        "completed_at": "2026-10-16T11:00:00Z",
        "asserted_status": "PASS",
        "mutation_score": None,
    }
    (tmp_path / "unit.json").write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(ValueError, match="source_sha256"):
        FileSystemTestExecutionReceiptRepository().load(str(tmp_path))


def test_well_formed_but_source_transplanted_receipt_is_blocking() -> None:
    transplanted = replace(execution_receipt(), source_sha256="c" * 64)

    evidence, findings = verify_test_execution_receipts(
        ReceiptVerificationRequest(
            rules=(TierRule("unit", ("tests/unit/*.py",)),),
            files=(file_record("tests/unit/test_example.py"),),
            receipts=(transplanted,),
            source_sha256="a" * 64,
            policy_sha256="b" * 64,
            now=FixedUtcClock().now(),
            max_age_hours=168,
        )
    )

    assert evidence[0].status == "INVALID_RECEIPT"
    assert "source digest mismatch" in findings[0].detail
