"""Tests for C033 Dual Checkers and Manifest Cryptographic Integrity.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.judge_packet.checkers.dual_evaluator import (
    assert_dual_agreement,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c033_lie_algebra_weight_multiplicities.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
JUDGE_DIR = CHALLENGE_DIR / "judge_packet"
CASES_DIR = JUDGE_DIR / "cases"

ALL_CASE_FILES = sorted(CASES_DIR.glob("*/*.json"))


def test_judge_cases_inventory():
    """Asserts that all 46 judge cases exist in cases/ directory."""
    assert len(ALL_CASE_FILES) >= 46, (
        f"Expected at least 46 judge cases, found {len(ALL_CASE_FILES)}"
    )


def test_manifest_cryptographic_integrity_and_ordinal_sorting():
    """Asserts that judge manifest is complete, strictly ordinal sorted, and SHA-256 certified."""
    manifest_file = JUDGE_DIR / "manifest.json"
    assert manifest_file.is_file(), "manifest.json must exist in judge_packet"

    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest_data.get("challenge_id") == "c033_lie_algebra_weight_multiplicities"
    assert manifest_data.get("protocol") == "SG-CP v1"

    files_entry = manifest_data.get("files", [])
    assert len(files_entry) >= 80, f"Expected >= 80 judge files in manifest, got {len(files_entry)}"

    # Check 1: Strict ordinal UTF-8 sorting invariant
    paths = [item["path"] for item in files_entry]
    sorted_paths = sorted(paths, key=lambda s: s.encode("utf-8"))
    assert paths == sorted_paths, (
        "manifest.json files are not ordered in strict ordinal UTF-8 byte order!"
    )

    # Check 2: Byte-level SHA-256 and size verification on disk
    for item in files_entry:
        file_path = JUDGE_DIR / item["path"]
        assert file_path.is_file(), f"Declared manifest file missing from disk: {item['path']}"
        data = file_path.read_bytes()
        actual_sha = hashlib.sha256(data).hexdigest()
        assert actual_sha == item["sha256"], (
            f"SHA-256 mismatch for {item['path']}: {actual_sha} != {item['sha256']}"
        )
        assert len(data) == item["size_bytes"], f"Size mismatch for {item['path']}"


@pytest.mark.parametrize("case_file", ALL_CASE_FILES, ids=lambda p: p.stem)
def test_dual_checkers_concordance_on_judge_cases(case_file: Path):
    """Asserts that both independent checkers agree 100% on every judge case."""
    case_data = json.loads(case_file.read_text(encoding="utf-8"))
    result = solve(case_data)

    ok, msg = assert_dual_agreement(case_data, result)
    assert ok, f"Dual checker failure on {case_file.name}: {msg}"
