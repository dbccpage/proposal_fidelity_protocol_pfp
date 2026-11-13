"""Recompute the Section 7.1 catalog facts from the audited commit.

These checks prefer `_intelligence/_antibodies/pharmacy_catalog.json` from Git
at the audited commit. If that object is unavailable, they use the identical,
SHA-256-bound snapshot included under code/fixtures. Neither source is executed.
The checks describe one data file; they say nothing about detector effectiveness.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[2]
BASELINE = "52cb5457f6c485ba548cfd292f6012a941ed22cf"
CATALOG = "_intelligence/_antibodies/pharmacy_catalog.json"
CATALOG_SHA256 = "b95ce7c1338867cc680abffcc3f2fb9da634c7a7ec2f4c00e0d67391e91b4acb"

EXPECTED_CLASSES = {
    "defect:defect:0": 9,
    "defect:defect:1": 9,
    "defect:defect:2": 9,
    "defect:defect:3": 9,
    "defect:defect:4": 9,
    "defect:h_boundary": 4,
    "general_obstruction": 3,
    "architecture:clean_arch_inward_dependency_violation": 3,
    "architecture:circular_dependency": 1,
    "algebraic_defect:energy_projector_sign_inversion": 1,
    "algebraic_defect:minimizer_bitmask_convention_inversion": 1,
    "resource_exhaustion:reasoning_trace_exceeds_completion_window": 1,
    "syntax_error:unterminated_string_literal": 1,
    "type_error:unsupported_operand_int_and_list": 1,
}
ACTIVE_CLASSES = {
    "algebraic_defect:energy_projector_sign_inversion",
    "algebraic_defect:minimizer_bitmask_convention_inversion",
    "resource_exhaustion:reasoning_trace_exceeds_completion_window",
    "syntax_error:unterminated_string_literal",
    "type_error:unsupported_operand_int_and_list",
}
# Run and task identifiers that appear in files retained at the audited commit:
# the three run folders under _intelligence/symbol_game/runs/ and the run
# records in _intelligence/unified_oe_trace.jsonl.
RUN_TASKS = (
    ("09232026_042645_code_refactoring_packet_clean_ar", "code_refactoring_packet_clean_arch"),
    ("09232026_052200_code_refactoring_packet_clean_ar", "code_refactoring_packet_clean_arch"),
    ("09232026_060218_code_refactoring_packet_clean_ar", "code_refactoring_packet_clean_arch"),
    ("09252026_135548_code_refactoring_packet_clean_ar", "code_refactoring_packet_clean_arch"),
    ("09252026_135548_specimen_mt000_reduction", "specimen_mt000_reduction"),
    ("09252026_135755_code_refactoring_packet_clean_ar", "code_refactoring_packet_clean_arch"),
    ("09252026_135755_specimen_mt000_reduction", "specimen_mt000_reduction"),
)


def _git_catalog_bytes() -> bytes | None:
    if shutil.which("git") is None:
        return None
    root = next((p for p in PACKAGE.parents if (p / ".git").exists()), None)
    if root is None:
        return None
    result = subprocess.run(
        ["git", "cat-file", "-p", f"{BASELINE}:{CATALOG}"],
        cwd=root,
        capture_output=True,
        timeout=60,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


@pytest.fixture(scope="module")
def catalog() -> dict:
    data = _git_catalog_bytes()
    if data is None:
        data = (PACKAGE / "code/fixtures/pharmacy_catalog_52cb5457f6c4.json").read_bytes()
    assert hashlib.sha256(data).hexdigest() == CATALOG_SHA256
    return json.loads(data.decode("utf-8"))


def test_catalog_entry_class_and_status_counts(catalog: dict) -> None:
    entries = catalog["antibodies"]
    assert len(entries) == 61
    assert Counter(entry["failure_class"] for entry in entries.values()) == EXPECTED_CLASSES
    assert Counter(entry["pharmacy_status"] for entry in entries.values()) == {
        "candidate": 56,
        "active": 5,
    }
    for entry in entries.values():
        expected = "active" if entry["failure_class"] in ACTIVE_CLASSES else "candidate"
        assert entry["pharmacy_status"] == expected


def test_catalog_fields_and_placeholder_fixtures(catalog: dict) -> None:
    entries = catalog["antibodies"].values()
    assert {len(entry) for entry in entries} == {15}
    placeholders = [
        entry
        for entry in entries
        if entry["negative_fixture"] == f"# Triggering defect: {entry['target_pattern']}\n"
        and entry["positive_fixture"] == "# Repaired exact state\n"
    ]
    assert len(placeholders) == 49
    others = [entry for entry in entries if entry not in placeholders]
    assert len(others) == 12
    for entry in others:
        for key in ("negative_fixture", "positive_fixture"):
            assert len(entry[key].rstrip("\n").split("\n")) <= 4


def test_evidence_digests_hash_identifiers_not_receipts(catalog: dict) -> None:
    entries = catalog["antibodies"].values()
    digests = [entry["evidence_sha256"] for entry in entries]
    assert all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in digests)
    assert len(set(digests)) == 61
    reconstructed = Counter()
    for entry in entries:
        for run_id, task_id in RUN_TASKS:
            text = f"{entry['target_pattern']}:{run_id}:{task_id}"
            if hashlib.sha256(text.encode("utf-8")).hexdigest() == entry["evidence_sha256"]:
                reconstructed[entry["failure_class"]] += 1
                break
    assert reconstructed == {
        "defect:defect:0": 3,
        "defect:defect:1": 3,
        "defect:defect:2": 3,
        "defect:defect:3": 3,
        "defect:defect:4": 3,
        "defect:h_boundary": 4,
    }
