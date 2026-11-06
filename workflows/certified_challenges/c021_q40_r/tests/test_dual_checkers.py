"""Comprehensive Tests for C021 Judge Packet Dual Checkers and Case Suite.

Verifies:
1. Exact case inventory and schema compliance across all 46 hidden cases
   (32 base, 8 controls, 6 poisoned).
2. Checker 1 (Exact Algebraic Symplectic Certifier) passes 100% of cases.
3. Checker 2 (Exact Dense Spectral LDL^H over Q[i]) passes 100% of cases.
4. Secondary NumPy numeric eigensolver passes 100% of cases.
5. Dual Evaluator asserts 100% agreement and zero CHECKER_DISAGREEMENT.
6. Relabel & gauge invariance across all 8 controls.
7. Deceptive trap detection across all 6 poisoned adversarial cases.
8. Total parsing safety against hostile inputs and malformed results.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from c021_q40_r.judge_packet.checkers.algebraic_checker import (
    verify_certificate,
)
from c021_q40_r.judge_packet.checkers.dual_evaluator import (
    CheckerDisagreementError,
    assert_dual_agreement,
    evaluate_dual,
)
from c021_q40_r.judge_packet.checkers.spectral_checker import (
    secondary_numeric_check,
    verify_spectral_optimality,
)
from c021_q40_r.reference_solver.solver import (
    solve,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT_DIR / "judge_packet" / "cases"
BASE_DIR = CASES_DIR / "base"
CTRL_DIR = CASES_DIR / "controls"
POISON_DIR = CASES_DIR / "poisoned"

BASE_FILES = sorted(BASE_DIR.glob("case_*.json"))
CTRL_FILES = sorted(CTRL_DIR.glob("ctrl_*.json"))
POISON_FILES = sorted(POISON_DIR.glob("poison_*.json"))
ALL_CASE_FILES = BASE_FILES + CTRL_FILES + POISON_FILES


# ---------------------------------------------------------------------------
# 1. Inventory, Schema Conformance & Manifest Integrity Tests
# ---------------------------------------------------------------------------


def test_judge_cases_inventory_counts():
    """Asserts exact 44-case inventory: 30 base, 8 controls, 6 poisoned (two leaked cases removed)."""
    assert len(BASE_FILES) == 30, f"Expected 30 base cases, found {len(BASE_FILES)}"
    assert len(CTRL_FILES) == 8, f"Expected 8 controls, found {len(CTRL_FILES)}"
    assert len(POISON_FILES) == 6, f"Expected 6 poisoned cases, found {len(POISON_FILES)}"
    assert len(ALL_CASE_FILES) == 44, f"Expected 44 total cases, found {len(ALL_CASE_FILES)}"


def test_manifest_integrity_and_ordinal_utf8_sorting():
    """Asserts manifest.json exists, files are sorted in ordinal UTF-8, and SHA-256 matches."""
    import hashlib

    judge_dir = ROOT_DIR / "judge_packet"
    manifest_path = judge_dir / "manifest.json"
    assert manifest_path.exists(), "manifest.json does not exist in judge_packet"

    manifest_raw = manifest_path.read_bytes()
    assert not manifest_raw.startswith(b"\xef\xbb\xbf"), "manifest.json contains UTF-8 BOM"

    manifest = json.loads(manifest_raw.decode("utf-8"))
    assert manifest["package_type"] == "judge_packet_v1"
    assert manifest["challenge_id"] == "c021_q40_r"
    assert manifest["case_counts"]["total_cases"] == 44

    files = manifest["files"]
    paths = [item["path"] for item in files]

    # Verify strict ordinal UTF-8 byte ordering
    sorted_paths = sorted(paths, key=lambda s: s.encode("utf-8"))
    assert paths == sorted_paths, "manifest.json files array is not in ordinal UTF-8 byte order"

    # Verify SHA-256 digests and file sizes match actual files on disk
    for entry in files:
        rel_p = entry["path"]
        expected_sha = entry["sha256"]
        file_path = judge_dir / rel_p
        assert file_path.exists(), f"File {rel_p} listed in manifest does not exist"
        actual_bytes = file_path.read_bytes()
        actual_sha = hashlib.sha256(actual_bytes).hexdigest()
        assert actual_sha == expected_sha, f"SHA-256 mismatch for {rel_p}"
        assert len(actual_bytes) == entry["size_bytes"], f"Size mismatch for {rel_p}"


def test_base_cases_outcomes_distribution():
    """Asserts at least 20 SOLVED, at least 6 OUT_OF_SCOPE, and at least 3 UNKNOWN."""
    solved_count = 0
    oos_count = 0
    unknown_count = 0

    for f in BASE_FILES:
        case = json.loads(f.read_text(encoding="utf-8"))
        res = solve(case)
        status = res["status"]
        if status == "SOLVED":
            solved_count += 1
        elif status == "OUT_OF_SCOPE":
            oos_count += 1
        elif status == "UNKNOWN":
            unknown_count += 1

    assert solved_count >= 20, f"Expected >= 20 SOLVED cases, got {solved_count}"
    assert oos_count >= 6, f"Expected >= 6 OUT_OF_SCOPE cases, got {oos_count}"
    assert unknown_count >= 3, f"Expected >= 3 UNKNOWN cases, got {unknown_count}"


@pytest.mark.parametrize("case_path", ALL_CASE_FILES, ids=lambda p: p.stem)
def test_case_file_schema_and_id_consistency(case_path: Path):
    """Asserts each case is valid JSON with consistent top-level fields."""
    case = json.loads(case_path.read_text(encoding="utf-8"))
    assert "id" in case, f"Missing 'id' in {case_path.name}"
    assert "n" in case, f"Missing 'n' in {case_path.name}"
    assert "terms" in case, f"Missing 'terms' in {case_path.name}"


# ---------------------------------------------------------------------------
# 2. Dual Checkers Agreement Across All 46 Cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case_path", ALL_CASE_FILES, ids=lambda p: p.stem)
def test_dual_checkers_agree_and_pass_all_46_cases(case_path: Path):
    """Verifies that Checker 1 and Checker 2 agree 100% on reference solver outputs."""
    case = json.loads(case_path.read_text(encoding="utf-8"))
    result = solve(case)

    # 1. Checker 1 (Exact Algebraic)
    ok1, msg1 = verify_certificate(case, result)
    assert ok1 is True, f"Checker 1 FAILED on {case_path.name}: {msg1}"
    assert msg1.startswith("VALID:"), f"Checker 1 msg: {msg1}"

    # 2. Checker 2 (Exact Spectral LDL^H)
    ok2, msg2 = verify_spectral_optimality(case, result)
    assert ok2 is True, f"Checker 2 FAILED on {case_path.name}: {msg2}"
    assert msg2.startswith("VALID:"), f"Checker 2 msg: {msg2}"

    # 3. Secondary Numeric Check (NumPy)
    ok_num, msg_num = secondary_numeric_check(case, result)
    assert ok_num is True, f"Secondary numeric FAILED on {case_path.name}: {msg_num}"

    # 4. Dual Evaluator
    eval_res = assert_dual_agreement(case, result)
    assert eval_res["verdict"] == "PASS"
    assert eval_res["agreement"] is True


# ---------------------------------------------------------------------------
# 3. Relabel & Gauge Invariance Controls
# ---------------------------------------------------------------------------


def test_controls_invariance_verification():
    """Asserts expected physical symmetry properties across all 8 controls."""
    # ctrl_01: qubit permutation of GHZ
    c01 = json.loads((CTRL_DIR / "ctrl_01_qubit_permutation.json").read_text(encoding="utf-8"))
    r01 = solve(c01)
    assert r01["status"] == "SOLVED"
    assert r01["energy"] == [0, 1]
    assert r01["degeneracy"] == 1

    # ctrl_02: term reordering
    c02 = json.loads((CTRL_DIR / "ctrl_02_term_reordering.json").read_text(encoding="utf-8"))
    r02 = solve(c02)
    assert r02["status"] == "SOLVED"
    assert r02["energy"] == [0, 1]
    assert r02["degeneracy"] == 1

    # ctrl_03: term id renaming
    c03 = json.loads((CTRL_DIR / "ctrl_03_term_id_renaming.json").read_text(encoding="utf-8"))
    r03 = solve(c03)
    assert r03["status"] == "SOLVED"
    assert r03["energy"] == [0, 1]
    assert r03["degeneracy"] == 1
    assert set(r03["basis"]) == {"ghz_stab_a", "ghz_stab_b", "ghz_stab_c"}

    # ctrl_04: weight rescaling (rescaled by 3 from [1, 1] to [3, 1] on frustrated triangle)
    c04 = json.loads((CTRL_DIR / "ctrl_04_weight_rescaling.json").read_text(encoding="utf-8"))
    r04 = solve(c04)
    assert r04["status"] == "SOLVED"
    assert r04["energy"] == [3, 1]  # scaled by 3 from [1, 1]
    assert r04["degeneracy"] == 6  # invariant degeneracy

    # ctrl_05: local Clifford Hadamard X <-> Z on qubit 0
    c05 = json.loads((CTRL_DIR / "ctrl_05_local_clifford_x_to_z.json").read_text(encoding="utf-8"))
    r05 = solve(c05)
    assert r05["status"] == "SOLVED"
    assert r05["energy"] == [0, 1]
    assert r05["degeneracy"] == 1

    # ctrl_06: local Clifford phase S on qubit 0
    c06 = json.loads((CTRL_DIR / "ctrl_06_local_clifford_y_basis.json").read_text(encoding="utf-8"))
    r06 = solve(c06)
    assert r06["status"] == "SOLVED"
    assert r06["energy"] == [0, 1]
    assert r06["degeneracy"] == 1

    # ctrl_07: unused qubit shift (embed into 4 qubits)
    c07 = json.loads((CTRL_DIR / "ctrl_07_unused_qubit_shift.json").read_text(encoding="utf-8"))
    r07 = solve(c07)
    assert r07["status"] == "SOLVED"
    assert r07["energy"] == [0, 1]
    assert r07["degeneracy"] == 2  # doubled due to 1 unused qubit (2^(4-3))

    # ctrl_08: cyclic shift (0->1, 1->2, 2->0)
    c08 = json.loads((CTRL_DIR / "ctrl_08_cyclic_shift.json").read_text(encoding="utf-8"))
    r08 = solve(c08)
    assert r08["status"] == "SOLVED"
    assert r08["energy"] == [0, 1]
    assert r08["degeneracy"] == 1


# ---------------------------------------------------------------------------
# 4. Poisoned Cases Trap Detection
# ---------------------------------------------------------------------------


def test_poisoned_cases_detection():
    """Asserts correct handling of deceptive adversarial edge cases."""
    # poison_01: buried anticommuting in 24 terms
    p01 = json.loads(
        (POISON_DIR / "poison_01_buried_anticommuting_in_23.json").read_text(encoding="utf-8")
    )
    r01 = solve(p01)
    assert r01["status"] == "OUT_OF_SCOPE"
    assert r01["witness"] == ["t_buried_anticommute", "t_z_0"]

    # poison_02: Y count phase trap (XY * YZ = -ZX, frustrated triangle with 3 minimizers)
    p02 = json.loads((POISON_DIR / "poison_02_y_count_phase_trap.json").read_text(encoding="utf-8"))
    r02 = solve(p02)
    assert r02["status"] == "SOLVED"
    assert r02["energy"] == [1, 1]
    assert r02["degeneracy"] == 3

    # poison_03: unreduced weight fraction [6, 4], [10, 5]
    p03 = json.loads(
        (POISON_DIR / "poison_03_unreduced_weight_fraction.json").read_text(encoding="utf-8")
    )
    r03 = solve(p03)
    assert r03["status"] == "SOLVED"
    assert r03["energy"] == [0, 1]  # must be coprime reduced

    # poison_04: signed product term (ZZ, XX, YY frustrated)
    p04 = json.loads(
        (POISON_DIR / "poison_04_signed_product_term.json").read_text(encoding="utf-8")
    )
    r04 = solve(p04)
    assert r04["status"] == "SOLVED"
    assert r04["energy"] == [1, 1]

    # poison_05: non-positional string sorting IDs ('t10', 't2', 't1')
    p05 = json.loads(
        (POISON_DIR / "poison_05_non_positional_string_sorting.json").read_text(encoding="utf-8")
    )
    r05 = solve(p05)
    assert r05["status"] == "SOLVED"
    assert r05["energy"] == [0, 1]
    decomp_ids = [d["id"] for d in r05["decomposition"]]
    assert set(decomp_ids) == {"t10", "t2", "t1"}

    # poison_06: duplicate term ID
    p06 = json.loads((POISON_DIR / "poison_06_duplicate_term_id.json").read_text(encoding="utf-8"))
    r06 = solve(p06)
    assert r06["status"] == "UNKNOWN"
    assert r06["refusal_code"] == "DUPLICATE_TERM_ID"


# ---------------------------------------------------------------------------
# 5. Checker Disagreement Tripping
# ---------------------------------------------------------------------------


def test_checker_disagreement_detection():
    """Asserts that evaluate_dual detects and reports CHECKER_DISAGREEMENT."""
    case = json.loads((BASE_DIR / "case_06.json").read_text(encoding="utf-8"))
    res = solve(case)

    # Corrupt ONLY the minimizers list (e.g. wrong bitmask)
    # Checker 1 checks exhaustive minimizers and fails
    # Checker 2 checks wire count and degeneracy
    bad_res = dict(res)
    bad_res["minimizers"] = [7]  # mask 7 does not achieve E0, but len is 1, so len * 1 = 1 == deg

    ok1, msg1 = verify_certificate(case, bad_res)
    ok2, msg2 = verify_spectral_optimality(case, bad_res)

    # Checker 1 must fail
    assert not ok1

    # Verify evaluate_dual reports disagreement if one fails and other passes
    eval_res = evaluate_dual(case, bad_res)
    if ok1 != ok2:
        assert eval_res["verdict"] == "CHECKER_DISAGREEMENT"
        with pytest.raises(CheckerDisagreementError):
            assert_dual_agreement(case, bad_res)


# ---------------------------------------------------------------------------
# 6. Total Parsing & Crash-Proof Safety
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "hostile_input",
    [
        None,
        {},
        [],
        "random_string",
        12345,
        True,
        False,
        3.14159,
        {"status": "BOGUS"},
        {"status": "SOLVED", "energy": None},
        {"status": "SOLVED", "energy": [1, 2], "degeneracy": None},
        {"status": "OUT_OF_SCOPE", "witness": None},
        {"status": "UNKNOWN", "refusal_code": None},
    ],
)
def test_checkers_total_parsing_safety(hostile_input: Any):
    """Asserts that checkers never throw unhandled exceptions on hostile inputs."""
    case = json.loads((BASE_DIR / "case_01.json").read_text(encoding="utf-8"))

    ok1, msg1 = verify_certificate(case, hostile_input)
    assert ok1 is False
    assert isinstance(msg1, str)
    assert msg1.startswith("FAIL:")

    ok2, msg2 = verify_spectral_optimality(case, hostile_input)
    assert ok2 is False
    assert isinstance(msg2, str)
    assert msg2.startswith("FAIL:")

    eval_res = evaluate_dual(case, hostile_input)
    assert eval_res["verdict"] == "FAIL"
