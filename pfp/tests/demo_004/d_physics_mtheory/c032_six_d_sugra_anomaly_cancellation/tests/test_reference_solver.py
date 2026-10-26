"""Tests for C032 Reference Solver and Group Theory Engine.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction

from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.reference_solver.solver import (
    solve_with_trace,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.reference_solver.sugra_6d import (
    compute_exact_inertia,
    get_group_dim,
    get_rep_dim,
    get_trace_coefficients,
    is_rep_pseudoreal,
)


def test_group_dimensions():
    """Verifies adjoint dimensions of classical and exceptional groups."""
    assert get_group_dim("SU(2)") == 3
    assert get_group_dim("SU(3)") == 8
    assert get_group_dim("SU(4)") == 15
    assert get_group_dim("SO(7)") == 21
    assert get_group_dim("Sp(1)") == 3
    assert get_group_dim("Sp(2)") == 10
    assert get_group_dim("G2") == 14
    assert get_group_dim("F4") == 52
    assert get_group_dim("E6") == 78
    assert get_group_dim("E7") == 133
    assert get_group_dim("E8") == 248


def test_representation_dimensions_and_pseudoreality():
    """Verifies representation dimensions and pseudoreal classification."""
    assert get_rep_dim("SU(2)", "fund") == 2
    assert is_rep_pseudoreal("SU(2)", "fund") is True

    assert get_rep_dim("SU(3)", "fund") == 3
    assert is_rep_pseudoreal("SU(3)", "fund") is False

    assert get_rep_dim("Sp(2)", "fund") == 4
    assert is_rep_pseudoreal("Sp(2)", "fund") is True

    assert get_rep_dim("E7", "fund") == 56
    assert is_rep_pseudoreal("E7", "fund") is True

    assert get_rep_dim("SU(4)", "antisym") == 6
    assert is_rep_pseudoreal("SU(4)", "antisym") is False


def test_trace_coefficients():
    """Verifies exact rational trace coefficients (A, B, C)."""
    # SU(4) fund: A=1, B=1, C=0
    a, b, c = get_trace_coefficients("SU(4)", "fund")
    assert (a, b, c) == (Fraction(1), Fraction(1), Fraction(0))

    # SU(4) adj: A=8, B=8, C=6
    a, b, c = get_trace_coefficients("SU(4)", "adj")
    assert (a, b, c) == (Fraction(8), Fraction(8), Fraction(6))

    # SU(4) antisym: A=2, B=-4, C=3
    a, b, c = get_trace_coefficients("SU(4)", "antisym")
    assert (a, b, c) == (Fraction(2), Fraction(-4), Fraction(3))

    # SU(2) has no quartic Casimir: B=0 and tr_fund F^4 = 1/2 (tr F^2)^2 is carried by C
    a, b, c = get_trace_coefficients("SU(2)", "fund")
    assert (a, b, c) == (Fraction(1), Fraction(0), Fraction(1, 2))


def test_exact_inertia():
    """Verifies exact LDL^T rational inertia calculations."""
    # Positive definite 2x2
    M1 = [[Fraction(2), Fraction(0)], [Fraction(0), Fraction(3)]]
    assert compute_exact_inertia(M1) == {"positive": 2, "negative": 0, "zero": 0}

    # Indefinite (hyperbolic plane)
    M2 = [[Fraction(0), Fraction(1)], [Fraction(1), Fraction(0)]]
    assert compute_exact_inertia(M2) == {"positive": 1, "negative": 1, "zero": 0}

    # Zero matrix
    M3 = [[Fraction(0), Fraction(0)], [Fraction(0), Fraction(0)]]
    assert compute_exact_inertia(M3) == {"positive": 0, "negative": 0, "zero": 2}


def test_ddc_tracer_integrity():
    """Verifies DDC 8-letter trace logging and cryptographic hash chaining."""
    case = {"id": "test_trace", "T": 9, "gauge_group": [], "hypers": [], "neutral_hypers": 12}
    res, tracer = solve_with_trace(case)
    assert res.get("verdict") == "PASSES_NECESSARY_CONDITIONS"

    valid, msg = tracer.verify_integrity()
    assert valid, f"DDC trace integrity failed: {msg}"
    trace = tracer.export_trace()
    assert len(trace) >= 4
    letters = [s["letter"] for s in trace]
    assert letters[0] == "C"
    assert letters[-1] == "T"


def test_solver_fail_closed_on_adversarial_defects():
    """Asserts that solver emits fail-closed UNKNOWN with exact refusal codes on all 6 defect classes."""
    defect_cases = [
        (
            {
                "id": "defect_hypers_none",
                "T": 1,
                "gauge_group": ["SU(2)"],
                "hypers": None,
                "neutral_hypers": 0,
            },
            "MALFORMED_CASE_STRUCTURE",
        ),
        (
            {
                "id": "defect_unknown_rep",
                "T": 1,
                "gauge_group": ["SU(2)"],
                "hypers": [{"multiplicity": 1, "reps": ["nonexistent_rep"]}],
                "neutral_hypers": 0,
            },
            "REPRESENTATION_NOT_SUPPORTED",
        ),
        (
            {
                "id": "defect_bool_t",
                "T": True,
                "gauge_group": ["SU(2)"],
                "hypers": [],
                "neutral_hypers": 0,
            },
            "T_OUT_OF_BOUNDS",
        ),
        (
            {
                "id": "defect_bool_neutral_hypers",
                "T": 0,
                "gauge_group": ["SU(2)"],
                "hypers": [],
                "neutral_hypers": False,
            },
            "NEUTRAL_HYPERS_OUT_OF_BOUNDS",
        ),
        (
            {
                "id": "defect_bool_multiplicity",
                "T": 1,
                "gauge_group": ["SU(2)"],
                "hypers": [{"multiplicity": True, "reps": ["fund"]}],
                "neutral_hypers": 0,
            },
            "MULTIPLICITY_OUT_OF_BOUNDS",
        ),
        (
            {
                "id": "defect_invalid_float_multiplicity",
                "T": 1,
                "gauge_group": ["SU(2)"],
                "hypers": [{"multiplicity": 0.333, "reps": ["fund"]}],
                "neutral_hypers": 0,
            },
            "MULTIPLICITY_OUT_OF_BOUNDS",
        ),
    ]

    for case, expected_refusal in defect_cases:
        # Step 1: Execute solver with trace to verify crash-freedom and typed refusal
        res, tracer = solve_with_trace(case)
        assert res.get("status") == "UNKNOWN", (
            f"Expected status UNKNOWN on {case['id']}, got {res.get('status')}"
        )
        assert res.get("refusal_code") == expected_refusal, (
            f"Expected refusal {expected_refusal} on {case['id']}, got {res.get('refusal_code')}"
        )
        assert res.get("id") == case["id"]

        # Step 2: Verify DDC 8-letter trace integrity and typed refusal letter 'M'
        valid, msg = tracer.verify_integrity()
        assert valid, f"DDC trace integrity failed on {case['id']}: {msg}"
        trace = tracer.export_trace()
        assert len(trace) >= 4, f"Trace too short on {case['id']}: {len(trace)}"
        assert trace[0]["letter"] == "C", "Trace must begin with Context (C)"
        letters = [s["letter"] for s in trace]
        assert "M" in letters, f"Expected typed refusal 'M' in trace: {letters}"
        assert trace[-1]["letter"] == "T", "Trace must terminate with Terminalization (T)"
