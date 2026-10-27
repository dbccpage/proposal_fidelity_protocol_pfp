"""Tests for C035 Dual Independent Checkers and Anti-Bypass Defenses.

Validates Checker 1, Checker 2, consensus evaluator, and all eight anti-bypass defense layers.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c035_k3_elliptic_genus_mathieu_moonshine.judge_packet.checkers.dual_evaluator import (
    CheckerDisagreementError,
    assert_dual_agreement,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c035_k3_elliptic_genus_mathieu_moonshine.judge_packet.checkers.jacobi_character_checker import (
    verify_jacobi_character_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c035_k3_elliptic_genus_mathieu_moonshine.judge_packet.checkers.matrix_inversion_checker import (
    verify_matrix_inversion_certificate,
)
from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c035_k3_elliptic_genus_mathieu_moonshine.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
BASE_CASES_DIR = CHALLENGE_DIR / "judge_packet" / "cases" / "base"
CTRL_CASES_DIR = CHALLENGE_DIR / "judge_packet" / "cases" / "controls"
POIS_CASES_DIR = CHALLENGE_DIR / "judge_packet" / "cases" / "poisoned"


def test_checker1_and_checker2_agree_on_base_cases():
    """Both Checker 1 and Checker 2 must accept all 24 base cases."""
    base_cases = sorted(BASE_CASES_DIR.glob("*.json"))
    assert len(base_cases) == 24

    for bf in base_cases:
        case = json.loads(bf.read_text(encoding="utf-8"))
        ans = solve(case)
        ok1, msg1 = verify_jacobi_character_certificate(case, ans)
        ok2, msg2 = verify_matrix_inversion_certificate(case, ans)
        assert ok1, f"Checker 1 failed on {bf.name}: {msg1}"
        assert ok2, f"Checker 2 failed on {bf.name}: {msg2}"


def test_checker1_and_checker2_agree_on_control_cases():
    """Both Checker 1 and Checker 2 must accept all 8 control cases."""
    ctrl_cases = sorted(CTRL_CASES_DIR.glob("*.json"))
    assert len(ctrl_cases) == 8

    for cf in ctrl_cases:
        case = json.loads(cf.read_text(encoding="utf-8"))
        ans = solve(case)
        ok1, msg1 = verify_jacobi_character_certificate(case, ans)
        ok2, msg2 = verify_matrix_inversion_certificate(case, ans)
        assert ok1, f"Checker 1 failed on {cf.name}: {msg1}"
        assert ok2, f"Checker 2 failed on {cf.name}: {msg2}"


def test_checker1_and_checker2_agree_on_poisoned_cases():
    """Both Checker 1 and Checker 2 must accept OUT_OF_SCOPE verdicts for all 6 poisoned cases."""
    pois_cases = sorted(POIS_CASES_DIR.glob("*.json"))
    assert len(pois_cases) == 6

    for pf in pois_cases:
        case = json.loads(pf.read_text(encoding="utf-8"))
        ans = solve(case)
        assert ans.get("status") == "OUT_OF_SCOPE"
        ok1, msg1 = verify_jacobi_character_certificate(case, ans)
        ok2, msg2 = verify_matrix_inversion_certificate(case, ans)
        assert ok1, f"Checker 1 failed on {pf.name}: {msg1}"
        assert ok2, f"Checker 2 failed on {pf.name}: {msg2}"


def test_checker_disagreement_raises_error(monkeypatch):
    """Injected divergence between Checker 1 and Checker 2 must raise CheckerDisagreementError."""
    case = {"case_id": "test_div", "query": "coefficients", "max_n": 3}
    ans = solve(case)

    # Monkeypatch Checker 1 to reject while Checker 2 accepts
    from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c035_k3_elliptic_genus_mathieu_moonshine.judge_packet.checkers import (
        dual_evaluator,
    )

    monkeypatch.setattr(
        dual_evaluator, "verify_jacobi_character_certificate", lambda c, a: (False, "MOCK_FAIL")
    )
    with pytest.raises(CheckerDisagreementError):
        assert_dual_agreement(case, ans)


def test_anti_bypass_rejects_dimension_only_matching():
    """Checkers must reject solvers attempting dimension-only heuristic guessing on poisoned cases."""
    case = {
        "case_id": "pois_dim_cheat",
        "query": "decompose",
        "n": 1,
        "class_order": [
            "1A",
            "2A",
            "3A",
            "5A",
            "4B",
            "7A",
            "7B",
            "8A",
            "6A",
            "11A",
            "15A",
            "15B",
            "14A",
            "14B",
            "23A",
            "23B",
            "12B",
            "6B",
            "4C",
            "3B",
            "2B",
            "10A",
            "21A",
            "21B",
            "4A",
            "12A",
        ],
        # Dim is 90, but 2A altered from -6 to 10
        "values": [
            90,
            10,
            0,
            0,
            2,
            -1,
            -1,
            -2,
            0,
            2,
            0,
            0,
            1,
            1,
            -2,
            -2,
            2,
            -2,
            2,
            6,
            10,
            0,
            -1,
            -1,
            -6,
            0,
        ],
    }
    # Guessing 45 + 45bar based solely on dim 90
    cheat_answer = {
        "id": "pois_dim_cheat",
        "status": "SOLVED",
        "multiplicities": {"45": 1, "45bar": 1},
        "zero_elsewhere": True,
    }
    ok1, msg1 = verify_jacobi_character_certificate(case, cheat_answer)
    ok2, msg2 = verify_matrix_inversion_certificate(case, cheat_answer)
    assert not ok1, "Checker 1 failed to reject dimension-only matching cheat"
    assert not ok2, "Checker 2 failed to reject dimension-only matching cheat"


def test_anti_bypass_rejects_boolean_injection():
    """Checkers must strictly reject boolean values masquerading as integers."""
    case = {"case_id": "t_bool_coeff", "query": "coefficients", "max_n": 3}
    bad_answer = {"id": "t_bool_coeff", "status": "SOLVED", "A": {"1": True, "2": 462, "3": 1540}}
    ok1, _ = verify_jacobi_character_certificate(case, bad_answer)
    ok2, _ = verify_matrix_inversion_certificate(case, bad_answer)
    assert not ok1
    assert not ok2


def test_anti_bypass_rejects_float_values():
    """Checkers must reject float representations in coefficients or multiplicities."""
    case = {"case_id": "t_float_coeff", "query": "coefficients", "max_n": 3}
    bad_answer = {"id": "t_float_coeff", "status": "SOLVED", "A": {"1": 90.0, "2": 462, "3": 1540}}
    ok1, _ = verify_jacobi_character_certificate(case, bad_answer)
    ok2, _ = verify_matrix_inversion_certificate(case, bad_answer)
    assert not ok1
    assert not ok2


def test_anti_bypass_rejects_phantom_keys():
    """Checkers must reject answers containing undeclared phantom keys."""
    case = {"case_id": "t_phantom", "query": "coefficients", "max_n": 3}
    bad_answer = {
        "id": "t_phantom",
        "status": "SOLVED",
        "A": {"1": 90, "2": 462, "3": 1540},
        "injected_telemetry": 42,
    }
    ok1, _ = verify_jacobi_character_certificate(case, bad_answer)
    ok2, _ = verify_matrix_inversion_certificate(case, bad_answer)
    assert not ok1
    assert not ok2


def test_anti_bypass_rejects_unwarranted_refusals():
    """Checkers must reject fake refusals on valid cases."""
    case = {"case_id": "t_fake_ref", "query": "coefficients", "max_n": 5}
    fake_refusal = {
        "id": "t_fake_ref",
        "status": "UNKNOWN",
        "refusal_code": "MAX_N_OUT_OF_BOUNDS",
    }
    ok1, msg1 = verify_jacobi_character_certificate(case, fake_refusal)
    ok2, msg2 = verify_matrix_inversion_certificate(case, fake_refusal)
    assert not ok1, f"C1 accepted unwarranted refusal: {msg1}"
    assert not ok2, f"C2 accepted unwarranted refusal: {msg2}"


def test_checkers_independent_dynamic_derivation():
    """Assert neither checker uses static dictionary lookup and both evaluate A_n dynamically.

    1. Verifies absence of _C1_KNOWN_COEFFS and _C2_DISCRIMINANT_A.
    2. Inspects ASTs of both checkers to prohibit embedded coefficient tables.
    3. Confirms both checkers dynamically verify valid answers.
    4. Confirms both checkers independently reject falsified coefficients.
    """
    import ast

    from projects.mssn_sn_symgam.challenges.d_physics_mtheory.c035_k3_elliptic_genus_mathieu_moonshine.judge_packet.checkers import (
        jacobi_character_checker,
        matrix_inversion_checker,
    )

    # 1. Verify absence of static tables in checker modules
    assert not hasattr(jacobi_character_checker, "_C1_KNOWN_COEFFS"), (
        "Integrity Violation: _C1_KNOWN_COEFFS static table present in Checker 1"
    )
    assert not hasattr(matrix_inversion_checker, "_C2_DISCRIMINANT_A"), (
        "Integrity Violation: _C2_DISCRIMINANT_A static table present in Checker 2"
    )

    # 2. AST inspection across both checker files
    mathieu_signatures = {90, 462, 1540, 4554, 11592, 27830}
    a30_val = 8816896000

    for checker_mod, name in [
        (jacobi_character_checker, "Checker 1 (jacobi_character_checker)"),
        (matrix_inversion_checker, "Checker 2 (matrix_inversion_checker)"),
    ]:
        src_path = Path(checker_mod.__file__).resolve()
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Dict, ast.List, ast.Tuple)):
                elements = node.values if isinstance(node, ast.Dict) else node.elts
                int_vals = [
                    e.value
                    for e in elements
                    if isinstance(e, ast.Constant) and isinstance(e.value, int)
                ]
                matched = set(int_vals).intersection(mathieu_signatures)
                assert len(matched) < 3, (
                    f"Integrity Violation: Hardcoded coefficient table detected in {name} with values: {matched}"
                )
                assert a30_val not in int_vals, (
                    f"Integrity Violation: A_30 ({a30_val}) hardcoded in {name}"
                )

    # 3. Dynamic verification across multiple orders
    for max_n in (1, 3, 5, 10):
        case = {"case_id": f"test_dyn_n{max_n}", "query": "coefficients", "max_n": max_n}
        ans = solve(case)
        ok1, msg1 = verify_jacobi_character_certificate(case, ans)
        ok2, msg2 = verify_matrix_inversion_certificate(case, ans)
        assert ok1, f"Checker 1 dynamic evaluation failed on N={max_n}: {msg1}"
        assert ok2, f"Checker 2 dynamic evaluation failed on N={max_n}: {msg2}"

    # 4. Independent falsification detection on perturbed coefficients
    bad_case = {"case_id": "test_falsified", "query": "coefficients", "max_n": 3}
    bad_ans = {
        "id": "test_falsified",
        "status": "SOLVED",
        "A": {"1": 90, "2": 462, "3": 1541},  # Corrupted A_3 (1540 -> 1541)
    }
    ok1, msg1 = verify_jacobi_character_certificate(bad_case, bad_ans)
    ok2, msg2 = verify_matrix_inversion_certificate(bad_case, bad_ans)
    assert not ok1, "Checker 1 failed to detect corrupted A_3 coefficient"
    assert not ok2, "Checker 2 failed to detect corrupted A_3 coefficient"
    assert "1541" in msg1 or "mismatch" in msg1.lower()
    assert "1541" in msg2 or "mismatch" in msg2.lower()
