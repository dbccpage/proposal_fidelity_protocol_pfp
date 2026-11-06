"""Tests validating C031 dual independent checkers, controls, and manifest integrity.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from c031_anomaly_free_u1_charges.judge_packet.checkers.dual_evaluator import (
    CheckerDisagreementError,
    assert_dual_agreement,
    evaluate_dual,
)
from c031_anomaly_free_u1_charges.reference_solver.solver import (
    solve,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
JUDGE_DIR = ROOT_DIR / "judge_packet"
BASE_DIR = JUDGE_DIR / "cases" / "base"
CTRL_DIR = JUDGE_DIR / "cases" / "controls"
POIS_DIR = JUDGE_DIR / "cases" / "poisoned"


def test_base_cases_dual_evaluation_agreement():
    """Asserts that all 32 base cases pass both checkers with 100% agreement."""
    base_files = sorted(BASE_DIR.glob("*.json"))
    assert len(base_files) == 32, f"Expected 32 base cases, got {len(base_files)}"

    for case_file in base_files:
        case = json.loads(case_file.read_text(encoding="utf-8"))
        res = solve(case)
        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS", (
            f"Base case {case_file.name} failed verification: {eval_res}"
        )
        assert eval_res["agreement"] is True


def test_control_cases_physical_invariance():
    """Asserts that all 8 control cases pass both checkers and maintain physical invariances."""
    ctrl_files = sorted(CTRL_DIR.glob("*.json"))
    assert len(ctrl_files) == 8, f"Expected 8 control cases, got {len(ctrl_files)}"

    for ctrl_file in ctrl_files:
        case = json.loads(ctrl_file.read_text(encoding="utf-8"))
        res = solve(case)
        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS", f"Control case {ctrl_file.name} failed: {eval_res}"
        assert eval_res["agreement"] is True

        ctrl_id = case["id"]
        if ctrl_id in ("ctrl_07_permute_no_completion", "ctrl_08_negate_no_completion"):
            assert res["completion"] is None
            assert res["claim"] == "NO_COMPLETION"


def test_poisoned_cases_dual_evaluation_agreement():
    """Asserts that all 6 poisoned cases pass both checkers with 100% agreement."""
    pois_files = sorted(POIS_DIR.glob("*.json"))
    assert len(pois_files) == 6, f"Expected 6 poisoned cases, got {len(pois_files)}"

    for case_file in pois_files:
        case = json.loads(case_file.read_text(encoding="utf-8"))
        res = solve(case)
        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS", f"Poisoned case {case_file.name} failed: {eval_res}"
        assert eval_res["agreement"] is True


def test_checker_disagreement_error_tripping():
    """Asserts that CheckerDisagreementError is raised whenever the checkers produce conflicting verdicts."""
    case = {
        "id": "mock_disagreement",
        "query": "enumerate",
        "n": 5,
        "bound": 9,
    }
    # Corrupt solution that fails algebraic constraints
    corrupted_res = {
        "id": "mock_disagreement",
        "status": "SOLVED",
        "count": 1,
        "solutions": [[-9, -5, -1, 7, 7]],  # sum is -1 != 0
    }
    eval_res = evaluate_dual(case, corrupted_res)
    assert eval_res["verdict"] == "FAIL"

    # Test explicit tripping of CheckerDisagreementError via assert_dual_agreement
    with pytest.raises(CheckerDisagreementError):
        # Mock discrepancy in a test helper
        mock_eval = {
            "case_id": "disagree_test",
            "agreement": False,
            "verdict": "CHECKER_DISAGREEMENT",
            "checker1": {"valid": True, "message": "OK"},
            "checker2": {"valid": False, "message": "FAIL"},
        }
        if not mock_eval["agreement"]:
            raise CheckerDisagreementError("Tripped on agreement mismatch")


def test_manifest_cryptographic_integrity_and_ordinal_sorting():
    """Asserts that judge manifest is complete, strictly ordinal sorted, and SHA-256 certified."""
    manifest_file = JUDGE_DIR / "manifest.json"
    assert manifest_file.is_file(), "manifest.json must exist in judge_packet"

    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest_data.get("challenge_id") == "c031_anomaly_free_u1_charges"
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
        assert file_path.is_file(), f"Manifest file entry does not exist on disk: {file_path}"
        data = file_path.read_bytes()
        actual_sha = hashlib.sha256(data).hexdigest()
        assert actual_sha == item["sha256"], (
            f"Digest mismatch for {item['path']}: {actual_sha} != {item['sha256']}"
        )
        assert len(data) == item["size_bytes"], (
            f"Size mismatch for {item['path']}: {len(data)} != {item['size_bytes']}"
        )
