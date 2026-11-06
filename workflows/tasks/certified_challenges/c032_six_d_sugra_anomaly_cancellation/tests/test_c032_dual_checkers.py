"""Tests for C032 Dual Checkers and Manifest Cryptographic Integrity.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from c032_six_d_sugra_anomaly_cancellation.judge_packet.checkers.dual_evaluator import (
    assert_dual_agreement,
    evaluate_dual,
)
from c032_six_d_sugra_anomaly_cancellation.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
JUDGE_DIR = CHALLENGE_DIR / "judge_packet"
CASES_DIR = JUDGE_DIR / "cases"

ALL_CASE_FILES = sorted(CASES_DIR.glob("*/*.json"))


def test_judge_cases_inventory():
    """Asserts that all 42 judge cases exist in cases/ directory."""
    assert len(ALL_CASE_FILES) >= 42, (
        f"Expected at least 42 judge cases, found {len(ALL_CASE_FILES)}"
    )


def test_manifest_cryptographic_integrity_and_ordinal_sorting():
    """Asserts that judge manifest is complete, strictly ordinal sorted, and SHA-256 certified."""
    manifest_file = JUDGE_DIR / "manifest.json"
    assert manifest_file.is_file(), "manifest.json must exist in judge_packet"

    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest_data.get("challenge_id") == "c032_six_d_sugra_anomaly_cancellation"
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
def test_dual_checkers_agree_on_judge_cases(case_file: Path):
    """Asserts that Checker 1 and Checker 2 agree on 100% of judge cases."""
    case_data = json.loads(case_file.read_text(encoding="utf-8"))
    res = solve(case_data)

    consensus = assert_dual_agreement(case_data, res)
    assert consensus["agreement"] is True, f"Checkers disagreed on {case_file.name}: {consensus}"
    assert consensus["verdict"] == "PASS", f"Evaluation failed on {case_file.name}: {consensus}"


@pytest.mark.parametrize(
    "case_id",
    ["ctrl_05_three_factors", "ctrl_06_three_factors_permuted"],
)
def test_unwarranted_representation_refusal_rejected_on_singlets(case_id: str):
    """Asserts that fake refusal REPRESENTATION_NOT_SUPPORTED on multi-factor cases with singlets
    (ctrl_05, ctrl_06) is rejected by both Checker 1 and Checker 2, returning FAIL."""
    case_file = CASES_DIR / "controls" / f"{case_id}.json"
    assert case_file.is_file(), f"Control case file missing: {case_file}"
    case_data = json.loads(case_file.read_text(encoding="utf-8"))

    for refusal_key in ("refusal", "refusal_code"):
        fake_submission = {
            "id": case_data["id"],
            "status": "UNKNOWN",
            refusal_key: "REPRESENTATION_NOT_SUPPORTED",
        }
        res = evaluate_dual(case_data, fake_submission)
        assert res["verdict"] == "FAIL", (
            f"Dual evaluator accepted fake refusal on {case_id} ({refusal_key}): {res}"
        )
        assert res["checker1"]["passed"] is False, (
            f"Checker 1 accepted fake refusal on {case_id}: {res['checker1']}"
        )
        assert res["checker2"]["passed"] is False, (
            f"Checker 2 accepted fake refusal on {case_id}: {res['checker2']}"
        )
        expected_msg = (
            "FAIL: refused REPRESENTATION_NOT_SUPPORTED but all representations are supported"
        )
        assert expected_msg in res["checker1"]["message"]
        assert expected_msg in res["checker2"]["message"]
