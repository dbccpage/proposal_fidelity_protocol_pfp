"""Regressions for false certification in the C021 Python wrappers."""

import pytest
from projects.mssn_sn_symgam.challenges.c_quantum import runner
from projects.mssn_sn_symgam.challenges.c_quantum.swarm import (
    q40_solver,
    adversary_overseer,
)


@pytest.fixture
def case():
    return {
        "id": "q",
        "n": 2,
        "terms": [
            {"id": "z0", "P": "ZI", "w": [1, 1], "target": 1},
            {"id": "z1", "P": "IZ", "w": [1, 1], "target": 1},
        ],
    }


def test_real_existing_quantum_solver_and_both_checkers(case):
    cert = q40_solver.Q40StabilizerSolver().solve(case)
    assert cert.status == "SOLVED"
    assert cert.energy == [0, 1]
    assert cert.algebraic_verified and cert.dense_verified


def test_unknown_is_not_claimed_verified(case):
    case["n"] = 9
    cert = q40_solver.Q40StabilizerSolver().solve(case)
    assert cert.status == "UNKNOWN"
    assert not cert.algebraic_verified
    assert not cert.dense_verified


def test_unchecked_large_dense_spectrum_is_not_claimed_verified():
    case = {
        "id": "large",
        "n": 7,
        "terms": [
            {"id": "z", "P": "ZIIIIII", "w": [1, 1], "target": 1},
        ],
    }
    cert = q40_solver.Q40StabilizerSolver().solve(case)
    assert cert.status == "SOLVED"
    assert cert.algebraic_verified
    assert not cert.dense_verified


def test_invalid_witness_cannot_escape_solver_wrapper(case, monkeypatch):
    monkeypatch.setattr(
        q40_solver,
        "domain_solve",
        lambda _: {
            "status": "OUT_OF_SCOPE",
            "witness": ["z0", "z1"],
        },
    )
    cert = q40_solver.Q40StabilizerSolver().solve(case)
    assert cert.status == "UNKNOWN"
    assert cert.refusal_code == "CERTIFICATE_CHECK_FAILED"


@pytest.mark.parametrize("field,value", [("degeneracy", 1.9), ("energy", [0.9, 1])])
def test_wire_corruption_cannot_be_hidden_by_integer_coercion(case, monkeypatch, field, value):
    result = q40_solver.domain_solve(case)
    result[field] = value
    monkeypatch.setattr(q40_solver, "domain_solve", lambda _: result)
    cert = q40_solver.Q40StabilizerSolver().solve(case)
    assert cert.status == "UNKNOWN"
    assert cert.refusal_code == "CERTIFICATE_CHECK_FAILED"


def test_skipped_requested_dense_check_is_refusal(case, monkeypatch):
    monkeypatch.setattr(q40_solver, "verify_dense_spectrum", lambda *_: {"dense_check": "SKIPPED"})
    cert = q40_solver.Q40StabilizerSolver().solve(case)
    assert cert.status == "UNKNOWN"
    assert cert.refusal_code == "DENSE_CHECK_UNVERIFIED"
    assert not cert.dense_verified


def test_runner_distinguishes_refusals_and_empty_input(case):
    case["n"] = 9
    report = runner.run_cases([case])
    assert report["passed_cases"] == 0
    assert report["refused_cases"] == 1
    assert not report["all_passed"]
    assert not runner.run_cases([])["all_passed"]
    assert report["billing_verified"] is False


@pytest.mark.parametrize("adversarial_zero_claim", [False, True])
def test_unbound_adversary_execution_refuses_without_artifacts(case, tmp_path, adversarial_zero_claim):
    class ForbiddenHost:
        def invoke(self, *_):
            pytest.fail("An unbound challenge must not bypass the city")

    overseer = adversary_overseer.AdversaryQuantumOverseer(tmp_path, host=ForbiddenHost())
    result = overseer.execute_challenge(
        "C021",
        case,
        task_key="unbound",
        adversarial_zero_claim=adversarial_zero_claim,
    )
    assert result.verdict == "REFUSE"
    assert result.refusal_code == "ADVERSARY_EXECUTION_UNAVAILABLE"
    assert result.certificate.status == "UNKNOWN"
    assert not result.certificate.algebraic_verified
    assert not result.certificate.dense_verified
    assert result.receipt_sha256 == ""
    assert result.billed_cost_usd == 0
    assert list(tmp_path.iterdir()) == []
