"""Tests for PharmacyCatalogRepository corruption prevention and fail-closed loading.

Verifies:
1. Malformed JSON raises ValueError instead of resetting to an empty catalog.
2. Atomic updates preserve existing antibodies.
3. Rolling backup (.bak) is created on update.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from eis.infrastructure.pharmacy_writer import (
    filesystem_byte_writer,
    filesystem_catalog_bytes,
)
from eis.domain.pharmacy_catalog import (
    PharmacyCatalogRepository,
)
from eis.domain.pharmacy_models import (
    Antibody,
    PharmacyStatus,
)


def test_corrupt_catalog_raises_fail_closed(tmp_path: Path) -> None:
    repo = PharmacyCatalogRepository(tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    # Write corrupt JSON to catalog file
    repo.catalog_file.parent.mkdir(parents=True, exist_ok=True)
    repo.catalog_file.write_text("{ unclosed invalid json ...", encoding="utf-8")

    with pytest.raises(ValueError, match="Corrupt or unreadable pharmacy catalog detected"):
        repo.load_catalog()


def test_atomic_update_and_backup(tmp_path: Path) -> None:
    repo = PharmacyCatalogRepository(tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    ab1 = Antibody(
        antibody_id="ab_test_001",
        failure_class="HALLUCINATION",
        target_pattern="test_pattern_1",
        constraint_type="ProjectOut",
        operatorizability="fatal",
        action="abort",
        severity="P1",
        description="Test antibody 1",
        negative_fixture="negative",
        positive_fixture="positive",
        pharmacy_status="admitted",
    )
    repo.update_catalog([ab1], run_id="run_1", task_id="task_1")

    # Verify catalog contains ab1
    cat1 = repo.load_catalog()
    assert "ab_test_001" in cat1["antibodies"]

    # Update with second antibody
    ab2 = Antibody(
        antibody_id="ab_test_002",
        failure_class="SYNTAX",
        target_pattern="test_pattern_2",
        constraint_type="ProjectOut",
        operatorizability="fatal",
        action="abort",
        severity="P2",
        description="Test antibody 2",
        negative_fixture="negative",
        positive_fixture="positive",
        pharmacy_status="admitted",
    )
    repo.update_catalog([ab2], run_id="run_2", task_id="task_2")

    cat2 = repo.load_catalog()
    assert "ab_test_001" in cat2["antibodies"]
    assert "ab_test_002" in cat2["antibodies"]

    # Verify .bak exists and matches previous state
    bak_file = repo.catalog_file.with_suffix(".json.bak")
    assert bak_file.is_file()
    bak_data = json.loads(bak_file.read_text(encoding="utf-8"))
    assert "ab_test_001" in bak_data["antibodies"]
