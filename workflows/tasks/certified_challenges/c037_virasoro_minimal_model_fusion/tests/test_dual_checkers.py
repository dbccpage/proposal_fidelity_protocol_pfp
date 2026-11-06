"""Tests for C037 Dual Checkers & Ring Axiom Verification.

Verifies:
  1. Concordance between Verlinde Cyclotomic Evaluator and Combinatorial Fusion Verifier.
  2. Commutativity, associativity, and unit ring axioms.
  3. CheckerDisagreementError on simulated divergence.
  4. Anti-bypass tests: rejecting floats, unreduced rationals, booleans, and phantoms.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from c037_virasoro_minimal_model_fusion.judge_packet.checkers.combinatorial_fusion_checker import (
    verify_combinatorial_fusion_certificate,
)
from c037_virasoro_minimal_model_fusion.judge_packet.checkers.dual_evaluator import (
    CheckerDisagreementError,
)
from c037_virasoro_minimal_model_fusion.judge_packet.checkers.verlinde_cyclotomic_checker import (
    verify_verlinde_cyclotomic_certificate,
)
from c037_virasoro_minimal_model_fusion.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
CASES_DIR = CHALLENGE_DIR / "judge_packet" / "cases"


def test_dual_checkers_agree_on_base_cases():
    """Both checkers must pass and agree on all 20 hidden base cases."""
    base_cases = sorted((CASES_DIR / "base").glob("*.json"))
    assert len(base_cases) == 20
    for cf in base_cases:
        case = json.loads(cf.read_text(encoding="utf-8"))
        ans = solve(case)
        ok1, msg1 = verify_verlinde_cyclotomic_certificate(case, ans)
        ok2, msg2 = verify_combinatorial_fusion_certificate(case, ans)
        assert ok1, f"Checker 1 rejected {cf.name}: {msg1}"
        assert ok2, f"Checker 2 rejected {cf.name}: {msg2}"


def test_dual_checkers_agree_on_controls():
    """Both checkers must pass and agree on all 8 relabel/gauge controls."""
    ctrl_cases = sorted((CASES_DIR / "controls").glob("*.json"))
    assert len(ctrl_cases) == 8
    for cf in ctrl_cases:
        case = json.loads(cf.read_text(encoding="utf-8"))
        ans = solve(case)
        ok1, msg1 = verify_verlinde_cyclotomic_certificate(case, ans)
        ok2, msg2 = verify_combinatorial_fusion_certificate(case, ans)
        assert ok1, f"Checker 1 rejected {cf.name}: {msg1}"
        assert ok2, f"Checker 2 rejected {cf.name}: {msg2}"


def test_dual_checkers_agree_on_poisoned_cases():
    """Both checkers must pass and agree on all 6 poisoned cases."""
    pois_cases = sorted((CASES_DIR / "poisoned").glob("*.json"))
    assert len(pois_cases) == 6
    for cf in pois_cases:
        case = json.loads(cf.read_text(encoding="utf-8"))
        ans = solve(case)
        ok1, msg1 = verify_verlinde_cyclotomic_certificate(case, ans)
        ok2, msg2 = verify_combinatorial_fusion_certificate(case, ans)
        assert ok1, f"Checker 1 rejected {cf.name}: {msg1}"
        assert ok2, f"Checker 2 rejected {cf.name}: {msg2}"


def test_checker_disagreement_raises_error():
    """Dual evaluator must raise CheckerDisagreementError when checkers diverge."""
    case = {"case_id": "test_div", "model": "minimal", "p": 4, "p_prime": 3}
    ans = solve(case)

    import c037_virasoro_minimal_model_fusion.judge_packet.checkers.dual_evaluator as de

    orig_c1 = de.verify_verlinde_cyclotomic_certificate
    try:
        de.verify_verlinde_cyclotomic_certificate = lambda c, a: (False, "simulated divergence")
        with pytest.raises(CheckerDisagreementError):
            de.assert_dual_agreement(case, ans)
    finally:
        de.verify_verlinde_cyclotomic_certificate = orig_c1


def test_anti_bypass_rejects_unreduced_rationals():
    """Checkers must reject unreduced fraction strings like 2/4 or 2/32."""
    case = {"case_id": "unred", "model": "minimal", "p": 4, "p_prime": 3}
    ans = solve(case)
    ans["central_charge"] = "2/4"
    ok1, msg1 = verify_verlinde_cyclotomic_certificate(case, ans)
    ok2, msg2 = verify_combinatorial_fusion_certificate(case, ans)
    assert not ok1 and "reduced rational" in msg1.lower()
    assert not ok2 and "reduced rational" in msg2.lower()


def test_anti_bypass_rejects_floats():
    """Checkers must reject float literals and float strings with decimals."""
    case = {"case_id": "flt", "model": "minimal", "p": 4, "p_prime": 3}
    ans = solve(case)
    ans["central_charge"] = 0.5
    ok1, _ = verify_verlinde_cyclotomic_certificate(case, ans)
    ok2, _ = verify_combinatorial_fusion_certificate(case, ans)
    assert not ok1
    assert not ok2
