"""Tests for C022 Dual Checkers."""

from __future__ import annotations

import pytest
from projects.mssn_sn_symgam.challenges.c_quantum.c022_stabilizer_code_distance.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.c_quantum.c022_stabilizer_code_distance.judge_packet.checkers.exact_checker import (
    check_certificate as exact_check,
)
from projects.mssn_sn_symgam.challenges.c_quantum.c022_stabilizer_code_distance.reference_solver.solver import (
    solve,
)


@pytest.fixture
def steane_case():
    return {
        "id": "steane",
        "num_qubits": 7,
        "generators": [
            "+IIIXXXX",
            "+IXXIIXX",
            "+XIXIXIX",
            "+IIIZZZZ",
            "+IZZIIZZ",
            "+ZIZIZIZ",
        ],
    }


def test_dual_checkers_valid_certificate(steane_case):
    cert = solve(steane_case)
    ok, reason, details = evaluate_dual(steane_case, cert)
    assert ok, f"Dual evaluator failed on valid cert: {reason}"
    assert details["exact"]["verdict"] == "PASS"
    assert details["independent"]["verdict"] == "PASS"


def test_dual_checkers_reject_wrong_distance(steane_case):
    cert = solve(steane_case)
    corrupted = dict(cert)
    corrupted["distance"] = 2
    ok, reason, details = evaluate_dual(steane_case, corrupted)
    assert not ok
    assert "Logical weight 3 != reported distance 2" in reason


def test_dual_checkers_reject_stabilizer_as_logical(steane_case):
    cert = solve(steane_case)
    corrupted = dict(cert)
    corrupted["logical"] = "IIIXXXX"
    corrupted["distance"] = 4
    ok, reason, details = evaluate_dual(steane_case, corrupted)
    assert not ok
    assert "lies in" in reason.lower() or "defect" in reason.lower()


def test_dual_checkers_reject_anticommuting_logical(steane_case):
    cert = solve(steane_case)
    corrupted = dict(cert)
    # ZIIIIII anticommutes with XIXIXIX (qubit 0)
    corrupted["logical"] = "ZIIIIII"
    corrupted["distance"] = 1
    ok, reason, details = evaluate_dual(steane_case, corrupted)
    assert not ok
    assert "does not commute" in reason.lower() or "lighter" in reason.lower()


def test_exact_checker_rejects_any_lower_bound_object(steane_case):
    """The synthetic LRAT object is gone; a non-null lower_bound is rejected."""
    cert = solve(steane_case)
    assert cert["lower_bound"] is None
    corrupted = dict(cert)
    corrupted["lower_bound"] = {"format": "lrat", "encoding_sha256": "0" * 64, "proof_b64gz": ""}
    res = exact_check(steane_case, corrupted)
    assert res["verdict"] == "FAIL"
    assert "lower_bound must be null" in res["reason"]


def test_exact_checker_does_not_consult_the_reference(steane_case):
    """A correct certificate with a different minimum-weight logical must pass."""
    cert = solve(steane_case)
    alternative = dict(cert)
    assert cert["logical"] != "ZIIIIZZ"
    alternative["logical"] = "ZIIIIZZ"
    ok, reason, _ = evaluate_dual(steane_case, alternative)
    assert ok, reason
