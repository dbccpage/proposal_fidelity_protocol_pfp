"""Tests for C034 Dual Independent Checkers and Anti-Bypass Defenses.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c034_calabi_yau_hodge_numbers.judge_packet.checkers.affine_hnf_checker import (
    verify_affine_hnf_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c034_calabi_yau_hodge_numbers.judge_packet.checkers.dual_evaluator import (
    CheckerDisagreementError,
    assert_dual_agreement,
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c034_calabi_yau_hodge_numbers.judge_packet.checkers.facet_point_checker import (
    verify_facet_point_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c034_calabi_yau_hodge_numbers.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
JUDGE_DIR = CHALLENGE_DIR / "judge_packet"
CASES_DIR = JUDGE_DIR / "cases"


def test_judge_cases_inventory():
    """Asserts that exactly 46 judge cases exist on disk."""
    base_cases = list((CASES_DIR / "base").glob("*.json"))
    ctrl_cases = list((CASES_DIR / "controls").glob("*.json"))
    pois_cases = list((CASES_DIR / "poisoned").glob("*.json"))

    assert len(base_cases) == 30, f"Expected 30 base cases, found {len(base_cases)}"
    assert len(ctrl_cases) == 10, f"Expected 10 control cases, found {len(ctrl_cases)}"
    assert len(pois_cases) == 6, f"Expected 6 poisoned cases, found {len(pois_cases)}"
    assert len(base_cases) + len(ctrl_cases) + len(pois_cases) == 46


def test_manifest_cryptographic_integrity_and_ordinal_sorting():
    """Asserts manifest.json paths are strictly ordinal UTF-8 sorted and match files on disk."""
    manifest_file = JUDGE_DIR / "manifest.json"
    assert manifest_file.is_file(), "manifest.json missing"

    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    files = data.get("files", [])
    assert len(files) == 99, f"Expected 99 indexed files, got {len(files)}"

    paths = [item["path"] for item in files]
    sorted_paths = sorted(paths, key=lambda s: s.encode("utf-8"))
    assert paths == sorted_paths, "Manifest paths are not in strict ordinal UTF-8 byte order"

    for item in files:
        fpath = JUDGE_DIR / item["path"]
        assert fpath.is_file(), f"Indexed file missing on disk: {item['path']}"
        raw = fpath.read_bytes()
        actual_hash = hashlib.sha256(raw).hexdigest()
        assert actual_hash == item["sha256"], f"SHA-256 mismatch for {item['path']}"
        assert len(raw) == item["size_bytes"], f"Byte count mismatch for {item['path']}"


def test_dual_checkers_agree_on_all_judge_cases():
    """Asserts that Checker 1 and Checker 2 agree and pass on all 46 judge cases."""
    all_case_files = sorted(CASES_DIR.rglob("*.json"))
    assert len(all_case_files) == 46

    for cf in all_case_files:
        case = json.loads(cf.read_text(encoding="utf-8"))
        ans = solve(case)
        eval_res = evaluate_dual(case, ans)

        assert eval_res["agreed"], f"Checker disagreement on {cf.name}: {eval_res}"
        assert eval_res["verdict"] == "PASS", f"Checkers failed on {cf.name}: {eval_res}"


def test_unwarranted_refusals_rejected_by_dual_checkers():
    """Asserts that fake UNKNOWN or OUT_OF_SCOPE refusals on valid cases return FAIL."""
    valid_case = {
        "id": "base_01_quintic_4simplex",
        "case_id": "base_01_quintic_4simplex",
        "reading": "dual",
        "vertices": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [-1, -1, -1, -1]],
    }

    # Fake UNKNOWN
    fake_unknown = {
        "id": "base_01_quintic_4simplex",
        "status": "UNKNOWN",
        "refusal_code": "COORDINATES_OUT_OF_BOUNDS",
    }
    ok1, _ = verify_facet_point_certificate(valid_case, fake_unknown)
    ok2, _ = verify_affine_hnf_certificate(valid_case, fake_unknown)
    assert not ok1
    assert not ok2

    # Fake OUT_OF_SCOPE
    fake_oos = {
        "id": "base_01_quintic_4simplex",
        "status": "OUT_OF_SCOPE",
        "witness": {"kind": "facet_distance", "distance": 2},
    }
    ok1, _ = verify_facet_point_certificate(valid_case, fake_oos)
    ok2, _ = verify_affine_hnf_certificate(valid_case, fake_oos)
    assert not ok1
    assert not ok2


def test_corrupted_face_data_rejected_by_dual_checkers():
    """Asserts that altered face_data yields verdict FAIL even with correct Hodge numbers."""
    valid_case = {
        "id": "base_01_quintic_4simplex",
        "case_id": "base_01_quintic_4simplex",
        "reading": "dual",
        "vertices": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [-1, -1, -1, -1]],
    }
    ans = solve(valid_case)

    # Corrupt l_delta
    corrupted = json.loads(json.dumps(ans))
    corrupted["face_data"]["l_delta"] += 1
    ok1, _ = verify_facet_point_certificate(valid_case, corrupted)
    ok2, _ = verify_affine_hnf_certificate(valid_case, corrupted)
    assert not ok1
    assert not ok2


def test_boolean_injections_rejected():
    """Asserts boolean injections in integer fields return FAIL."""
    valid_case = {
        "id": "base_01_quintic_4simplex",
        "case_id": "base_01_quintic_4simplex",
        "reading": "dual",
        "vertices": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [-1, -1, -1, -1]],
    }
    ans = solve(valid_case)

    # Boolean True in h11
    b_ans = json.loads(json.dumps(ans))
    b_ans["h11"] = True
    ok1, _ = verify_facet_point_certificate(valid_case, b_ans)
    ok2, _ = verify_affine_hnf_certificate(valid_case, b_ans)
    assert not ok1
    assert not ok2


def test_assert_dual_agreement_raises_on_divergence(monkeypatch):
    """Asserts assert_dual_agreement raises CheckerDisagreementError on divergence."""
    valid_case = {
        "id": "c034_base_01",
        "reading": "primal",
        "vertices": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [-1, -1, -1, -1]],
    }
    ans = solve(valid_case)

    # Checker 1 accepts ans (True), force Checker 2 to reject (False)
    import projects.mssn_sn_symgam.challenges.d_physics_mtheory.c034_calabi_yau_hodge_numbers.judge_packet.checkers.dual_evaluator as de_mod

    monkeypatch.setattr(
        de_mod, "verify_affine_hnf_certificate", lambda c, a: (False, "forced divergence")
    )

    with pytest.raises(CheckerDisagreementError):
        assert_dual_agreement(valid_case, ans)


def test_dual_checkers_mirror_swap_all_solvable_base_cases():
    """Asserts both checkers agree and pass on both primal and dual readings for all 24 solvable base cases."""
    base_cases = sorted((CASES_DIR / "base").glob("*.json"))
    solvable_cases = [
        cf
        for cf in base_cases
        if not cf.stem.startswith(
            ("base_25", "base_26", "base_27", "base_28", "base_29", "base_30")
        )
    ]
    assert len(solvable_cases) == 24

    for cf in solvable_cases:
        case = json.loads(cf.read_text(encoding="utf-8"))
        case_dual = {**case, "reading": "dual"}
        case_primal = {**case, "reading": "primal"}

        ans_dual = solve(case_dual)
        ans_primal = solve(case_primal)

        eval_d = evaluate_dual(case_dual, ans_dual)
        eval_p = evaluate_dual(case_primal, ans_primal)

        assert eval_d["agreed"], f"Disagreement on dual {cf.name}: {eval_d}"
        assert eval_d["verdict"] == "PASS", f"Checker failed on dual {cf.name}: {eval_d}"

        assert eval_p["agreed"], f"Disagreement on primal {cf.name}: {eval_p}"
        assert eval_p["verdict"] == "PASS", f"Checker failed on primal {cf.name}: {eval_p}"


def test_dual_checkers_base_09_vs_ctrl_10_mirror_symmetry():
    """Asserts dual checkers certify (2, 86) for base_09 and (86, 2) for ctrl_10."""
    f_b09 = CASES_DIR / "base" / "base_09_codim2_k3_fibration.json"
    f_c10 = CASES_DIR / "controls" / "ctrl_10_dual_reading_swap_codim2.json"

    case_b09 = json.loads(f_b09.read_text(encoding="utf-8"))
    case_c10 = json.loads(f_c10.read_text(encoding="utf-8"))

    ans_b09 = solve(case_b09)
    ans_c10 = solve(case_c10)

    assert (ans_b09["h11"], ans_b09["h21"], ans_b09["euler"]) == (2, 86, -168)
    assert (ans_c10["h11"], ans_c10["h21"], ans_c10["euler"]) == (86, 2, 168)

    ev_b09 = evaluate_dual(case_b09, ans_b09)
    ev_c10 = evaluate_dual(case_c10, ans_c10)

    assert ev_b09["agreed"] and ev_b09["verdict"] == "PASS"
    assert ev_c10["agreed"] and ev_c10["verdict"] == "PASS"

    # Submitting swapped answer to opposite case must be rejected by both checkers
    ok1_cross, _ = verify_facet_point_certificate(case_b09, ans_c10)
    ok2_cross, _ = verify_affine_hnf_certificate(case_b09, ans_c10)
    assert not ok1_cross, "Checker 1 accepted mirror-swapped answer on base_09"
    assert not ok2_cross, "Checker 2 accepted mirror-swapped answer on base_09"
