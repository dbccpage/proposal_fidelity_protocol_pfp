"""Rational separation, enumeration, and input rejection regressions."""
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from certificate_gate import BqnfCertificateGate
from exact_fock_gap import exp_minus_bounds, hopping_amplitude, verify_exact_gap


def test_exact_gap_covers_every_length_class():
    result = verify_exact_gap()
    assert result["total_3hop_paths"] == 192
    assert result["positive_3hop_paths"] == result["negative_3hop_paths"] == 96
    lo, hi = Fraction(result["target_lower"]), Fraction(result["target_upper"])
    assert Fraction(result["four_or_more_hop_upper"]) < lo <= hi
    assert all(hi < Fraction(result[key]) for key in (
        "zero_hop_lower", "two_hop_lower", "positive_three_hop_lower"))
    assert result["physical_sign_problem_classification"] is False


def test_alternating_bounds_nest_without_numeric_exponentials():
    assert exp_minus_bounds(Fraction(0)) == (Fraction(1), Fraction(1))
    lo1, hi1 = exp_minus_bounds(Fraction(1), 2)
    lo2, hi2 = exp_minus_bounds(Fraction(1), 3)
    assert lo1 < lo2 < hi2 < hi1


@pytest.mark.parametrize("invalid", [True, "1/2", Fraction(-1), Fraction(3, 2)])
def test_outside_exact_exponential_domain_rejected(invalid):
    with pytest.raises(ValueError):
        exp_minus_bounds(invalid)


def test_hopping_rejects_cross_spin_and_diagonal_moves():
    a = (1, 0, 0, 0, 0, 0)
    assert hopping_amplitude(a, a) == 0
    assert hopping_amplitude(a, (0, 0, 0, 1, 0, 0)) == 0
    assert hopping_amplitude(a, (0, 1, 0, 0, 0, 0)) == 1


def test_optimized_python_retains_certificate_rejection():
    code = "import exact_fock_gap as g; g.hopping_amplitude = lambda a,b: 0; g.verify_exact_gap()"
    result = subprocess.run(
        [sys.executable, "-O", "-B", "-c", code],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "Unexpected signed path counts" in result.stderr


def test_active_gate_uses_exact_gap_without_numeric_display(monkeypatch):
    import fock_path_enumerator

    def forbidden_display():
        raise AssertionError("Numerical display cannot be the certification route")

    monkeypatch.setattr(fock_path_enumerator, "verify_fock_path_proposition", forbidden_display)
    gate = BqnfCertificateGate("c3_triangular", {"t": 1, "U": 2, "beta": Fraction(1, 4), "mu": 0})
    status, admitted, _ = gate.verify_proposal_item({
        "move_type": "OPEN_SIGN_OBSTRUCTION",
        "obstruction_witness": {"type": "c3_integrated_path_gap"},
    })
    assert admitted and status == "OpenSignObstruction"
