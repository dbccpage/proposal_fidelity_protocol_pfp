"""Tests for C036 Dual Checkers and Anti-Bypass Defenses.

Validates 100% concordance between Checker 1 (Hypergeometric Closed-Form) and
Checker 2 (Picard-Fuchs Recurrence), exercises all 8 anti-bypass defense layers,
and performs AST inspection to enforce zero hardcoded invariant lookup tables.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from c036_quintic_gromov_witten_mirror.judge_packet.checkers import (
    hypergeometric_mirror_checker,
    picard_fuchs_recurrence_checker,
)
from c036_quintic_gromov_witten_mirror.judge_packet.checkers.dual_evaluator import (
    CheckerDisagreementError,
)
from c036_quintic_gromov_witten_mirror.judge_packet.checkers.hypergeometric_mirror_checker import (
    verify_hypergeometric_mirror_certificate,
)
from c036_quintic_gromov_witten_mirror.judge_packet.checkers.picard_fuchs_recurrence_checker import (
    verify_picard_fuchs_recurrence_certificate,
)
from c036_quintic_gromov_witten_mirror.reference_solver import (
    mirror_symmetry,
    solver,
)
from c036_quintic_gromov_witten_mirror.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
CASES_DIR = CHALLENGE_DIR / "judge_packet" / "cases"


def test_checker1_and_checker2_agree_on_base_cases():
    """Both checkers must agree and pass on all 16 hidden base cases."""
    base_cases = sorted((CASES_DIR / "base").glob("*.json"))
    assert len(base_cases) == 16
    for cf in base_cases:
        case = json.loads(cf.read_text(encoding="utf-8"))
        ans = solve(case)
        ok1, msg1 = verify_hypergeometric_mirror_certificate(case, ans)
        ok2, msg2 = verify_picard_fuchs_recurrence_certificate(case, ans)
        assert ok1, f"Checker 1 rejected {cf.name}: {msg1}"
        assert ok2, f"Checker 2 rejected {cf.name}: {msg2}"


def test_checker1_and_checker2_agree_on_control_cases():
    """Both checkers must agree and pass on all 6 control cases."""
    ctrl_cases = sorted((CASES_DIR / "controls").glob("*.json"))
    assert len(ctrl_cases) == 6
    for cf in ctrl_cases:
        case = json.loads(cf.read_text(encoding="utf-8"))
        ans = solve(case)
        ok1, msg1 = verify_hypergeometric_mirror_certificate(case, ans)
        ok2, msg2 = verify_picard_fuchs_recurrence_certificate(case, ans)
        assert ok1, f"Checker 1 rejected {cf.name}: {msg1}"
        assert ok2, f"Checker 2 rejected {cf.name}: {msg2}"


def test_checker1_and_checker2_agree_on_poisoned_cases():
    """Both checkers must agree and pass on all 6 poisoned cases."""
    pois_cases = sorted((CASES_DIR / "poisoned").glob("*.json"))
    assert len(pois_cases) == 6
    for cf in pois_cases:
        case = json.loads(cf.read_text(encoding="utf-8"))
        ans = solve(case)
        ok1, msg1 = verify_hypergeometric_mirror_certificate(case, ans)
        ok2, msg2 = verify_picard_fuchs_recurrence_certificate(case, ans)
        assert ok1, f"Checker 1 rejected {cf.name}: {msg1}"
        assert ok2, f"Checker 2 rejected {cf.name}: {msg2}"


def test_checker_disagreement_raises_error():
    """Dual evaluator must raise CheckerDisagreementError when checkers diverge."""
    case = {"case_id": "test_div", "weights": [1, 1, 1, 1, 1], "degree": 5, "max_curve_degree": 2}
    ans = solve(case)

    # Artificially monkeypatch one checker to test divergence
    import c036_quintic_gromov_witten_mirror.judge_packet.checkers.dual_evaluator as de

    orig_c1 = de.verify_hypergeometric_mirror_certificate
    try:
        de.verify_hypergeometric_mirror_certificate = lambda c, a: (False, "mock failure")
        with pytest.raises(CheckerDisagreementError):
            de.assert_dual_agreement(case, ans)
    finally:
        de.verify_hypergeometric_mirror_certificate = orig_c1


def test_anti_bypass_rejects_memorized_quintic_numbers():
    """Checker must reject quintic 2875 invariant returned for non-quintic families."""
    sextic_case = {
        "case_id": "sx_mem",
        "weights": [1, 1, 1, 1, 2],
        "degree": 6,
        "max_curve_degree": 1,
    }
    fake_ans = {
        "id": "sx_mem",
        "status": "SOLVED",
        "kappa": "3",
        "gv": {"1": "2875"},  # memorization trap!
        "gw": {"1": "2875"},
        "mirror_map_coeffs": ["1"],
    }
    ok1, msg1 = verify_hypergeometric_mirror_certificate(sextic_case, fake_ans)
    ok2, msg2 = verify_picard_fuchs_recurrence_certificate(sextic_case, fake_ans)
    assert not ok1 and "memorization" in msg1.lower()
    assert not ok2 and "memorization" in msg2.lower()


def test_anti_bypass_rejects_unreduced_rationals():
    """Checkers must reject unreduced fraction strings like 9753750/16."""
    case = {"case_id": "unred", "weights": [1, 1, 1, 1, 1], "degree": 5, "max_curve_degree": 2}
    ans = solve(case)
    ans["gw"]["2"] = "9753750/16"
    ok1, msg1 = verify_hypergeometric_mirror_certificate(case, ans)
    ok2, msg2 = verify_picard_fuchs_recurrence_certificate(case, ans)
    assert not ok1 and "reduced rational" in msg1.lower()
    assert not ok2 and "reduced rational" in msg2.lower()


def test_anti_bypass_rejects_boolean_injection():
    """Checkers must reject boolean values in degree, status, or invariants."""
    bad_case = {
        "case_id": "bool_deg",
        "weights": [1, 1, 1, 1, 1],
        "degree": True,
        "max_curve_degree": 2,
    }
    ans = {
        "id": "bool_deg",
        "status": "SOLVED",
        "kappa": "5",
        "gv": {"1": "2875"},
        "gw": {"1": "2875"},
        "mirror_map_coeffs": ["1"],
    }
    ok1, _ = verify_hypergeometric_mirror_certificate(bad_case, ans)
    ok2, _ = verify_picard_fuchs_recurrence_certificate(bad_case, ans)
    assert not ok1
    assert not ok2


def test_anti_bypass_rejects_float_values():
    """Checkers must reject float literals and float strings with decimals."""
    case = {"case_id": "flt", "weights": [1, 1, 1, 1, 1], "degree": 5, "max_curve_degree": 2}
    ans = solve(case)
    ans["gv"]["2"] = 609250.0  # float literal
    ok1, _ = verify_hypergeometric_mirror_certificate(case, ans)
    ok2, _ = verify_picard_fuchs_recurrence_certificate(case, ans)
    assert not ok1
    assert not ok2


def test_anti_bypass_rejects_phantom_keys():
    """Checkers must reject undeclared telemetry or debugging keys."""
    case = {"case_id": "phantom", "weights": [1, 1, 1, 1, 1], "degree": 5, "max_curve_degree": 1}
    ans = solve(case)
    ans["injected_debug_key"] = True
    ok1, msg1 = verify_hypergeometric_mirror_certificate(case, ans)
    ok2, msg2 = verify_picard_fuchs_recurrence_certificate(case, ans)
    assert not ok1 and "phantom keys" in msg1
    assert not ok2 and "phantom keys" in msg2


def test_anti_bypass_rejects_unwarranted_refusals():
    """Checkers must reject unwarranted UNKNOWN or OUT_OF_SCOPE on valid cases."""
    case = {"case_id": "valid_q", "weights": [1, 1, 1, 1, 1], "degree": 5, "max_curve_degree": 2}
    bad_ans = {"id": "valid_q", "status": "UNKNOWN", "refusal_code": "FAMILY_NOT_IN_PINNED_LIST"}
    ok1, msg1 = verify_hypergeometric_mirror_certificate(case, bad_ans)
    ok2, msg2 = verify_picard_fuchs_recurrence_certificate(case, bad_ans)
    assert not ok1 and "unwarranted refusal" in msg1
    assert not ok2 and "unwarranted refusal" in msg2


def test_no_hardcoded_invariants_tables():
    """AST Anti-Hardcoding Regression Test.

    Inspects ASTs of solver and checkers to assert no static lookup tables
    contain known invariant signatures.
    """
    modules_to_inspect = [
        (hypergeometric_mirror_checker, "Checker 1 (hypergeometric_mirror_checker)"),
        (picard_fuchs_recurrence_checker, "Checker 2 (picard_fuchs_recurrence_checker)"),
        (solver, "Reference Solver (solver)"),
        (mirror_symmetry, "Mirror Symmetry Engine (mirror_symmetry)"),
    ]

    target_signatures = {
        2875,
        609250,
        317206375,
        7884,
        6028452,
        29504,
        168280,
        704288164978454686113488249750,
    }

    for mod, name in modules_to_inspect:
        src_path = Path(mod.__file__).resolve()
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Dict, ast.List, ast.Tuple)):
                elements = node.values if isinstance(node, ast.Dict) else node.elts
                int_vals = [
                    e.value
                    for e in elements
                    if isinstance(e, ast.Constant) and isinstance(e.value, int)
                ]
                str_vals = [
                    e.value
                    for e in elements
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)
                ]
                matched_ints = set(int_vals).intersection(target_signatures)
                assert not matched_ints, (
                    f"Integrity Violation: Hardcoded invariant integers detected in {name}: {matched_ints}"
                )
                matched_strs = {s for s in str_vals if s.isdigit() and int(s) in target_signatures}
                assert not matched_strs, (
                    f"Integrity Violation: Hardcoded invariant strings detected in {name}: {matched_strs}"
                )
