"""Tests for C036 Reference Solver.

Validates solver across all 4 pinned Calabi-Yau families, permutation invariance,
fail-closed refusal semantics, DDC operational tracing, and performance bounds.

AuthorityEffect: None.
"""

from __future__ import annotations

import time

from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c036_quintic_gromov_witten_mirror.reference_solver.solver import (
    get_last_tracer,
    solve,
)


def test_solver_quintic_small_d():
    """Verifies quintic instanton numbers for D=1, 2, 3."""
    case = {"case_id": "test_q3", "weights": [1, 1, 1, 1, 1], "degree": 5, "max_curve_degree": 3}
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["kappa"] == "5"
    assert res["gv"]["1"] == "2875"
    assert res["gv"]["2"] == "609250"
    assert res["gv"]["3"] == "317206375"
    assert res["gw"]["1"] == "2875"
    assert res["gw"]["2"] == "4876875/8"
    assert res["gw"]["3"] == "8564575000/27"
    assert res["mirror_map_coeffs"] == ["1", "-770", "171525"]


def test_solver_quintic_large_d():
    """Verifies quintic instanton numbers up to D=10 without 64-bit overflow."""
    case = {"case_id": "test_q10", "weights": [1, 1, 1, 1, 1], "degree": 5, "max_curve_degree": 10}
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["gv"]["4"] == "242467530000"
    assert res["gv"]["5"] == "229305888887625"
    assert res["gv"]["10"] == "704288164978454686113488249750"


def test_solver_sextic_invariants():
    """Verifies sextic invariants with kappa=3."""
    case = {"case_id": "test_sx3", "weights": [1, 1, 1, 1, 2], "degree": 6, "max_curve_degree": 3}
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["kappa"] == "3"
    assert res["gv"]["1"] == "7884"
    assert res["gv"]["2"] == "6028452"
    assert res["gv"]["3"] == "11900417220"


def test_solver_octic_invariants():
    """Verifies octic invariants with kappa=2."""
    case = {"case_id": "test_oc3", "weights": [1, 1, 1, 1, 4], "degree": 8, "max_curve_degree": 3}
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["kappa"] == "2"
    assert res["gv"]["1"] == "29504"
    assert res["gv"]["2"] == "128834912"


def test_solver_decic_invariants():
    """Verifies decic invariants with kappa=1."""
    case = {"case_id": "test_dec2", "weights": [1, 1, 1, 2, 5], "degree": 10, "max_curve_degree": 2}
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["kappa"] == "1"
    assert res["gv"]["1"] == "231200"


def test_solver_permuted_weights_invariance():
    """Permutations of the weight vector must yield identical invariants."""
    c1 = {"case_id": "c1", "weights": [1, 1, 1, 1, 2], "degree": 6, "max_curve_degree": 2}
    c2 = {"case_id": "c2", "weights": [2, 1, 1, 1, 1], "degree": 6, "max_curve_degree": 2}
    r1 = solve(c1)
    r2 = solve(c2)
    assert r1["gv"] == r2["gv"]
    assert r1["gw"] == r2["gw"]
    assert r1["mirror_map_coeffs"] == r2["mirror_map_coeffs"]


def test_solver_refusal_non_calabi_yau():
    """Non-Calabi-Yau inputs must fail-closed with OUT_OF_SCOPE and structured witness."""
    case = {"case_id": "bad_cy", "weights": [1, 1, 1, 1, 1], "degree": 6, "max_curve_degree": 2}
    res = solve(case)
    assert res["status"] == "OUT_OF_SCOPE"
    assert res["witness"] == {"kind": "not_calabi_yau", "degree": 6, "weight_sum": 5}


def test_solver_refusal_unlisted_family():
    """Calabi-Yau families not in the pinned 4-list must refuse with UNKNOWN."""
    case = {"case_id": "unlisted", "weights": [1, 1, 2, 2, 2], "degree": 8, "max_curve_degree": 2}
    res = solve(case)
    assert res["status"] == "UNKNOWN"
    assert res["refusal_code"] == "FAMILY_NOT_IN_PINNED_LIST"


def test_solver_refusal_out_of_bounds_degree():
    """Curve degree D < 1 or D > 10 must refuse with MAX_CURVE_DEGREE_OUT_OF_BOUNDS."""
    c_low = {"case_id": "low", "weights": [1, 1, 1, 1, 1], "degree": 5, "max_curve_degree": 0}
    c_high = {"case_id": "high", "weights": [1, 1, 1, 1, 1], "degree": 5, "max_curve_degree": 11}
    assert solve(c_low)["refusal_code"] == "MAX_CURVE_DEGREE_OUT_OF_BOUNDS"
    assert solve(c_high)["refusal_code"] == "MAX_CURVE_DEGREE_OUT_OF_BOUNDS"


def test_solver_ddc_tracer_emits_valid_alphabet():
    """DDC tracer must record transitions over {E, R, C, I, Lambda, D, M, T} with SHA-256 chaining."""
    case = {"case_id": "test_ddc", "weights": [1, 1, 1, 1, 1], "degree": 5, "max_curve_degree": 2}
    solve(case)
    tracer = get_last_tracer()
    assert tracer is not None
    trace = tracer.export_trace()
    assert trace["step_count"] >= 6
    valid_letters = {"E", "R", "C", "I", "Lambda", "D", "M", "T"}
    for step in trace["steps"]:
        assert step["letter"] in valid_letters
        assert len(step["digest"]) == 64


def test_solver_performance_d10():
    """Solving D=10 quintic must execute in under 2.0 seconds."""
    case = {"case_id": "perf_d10", "weights": [1, 1, 1, 1, 1], "degree": 5, "max_curve_degree": 10}
    t0 = time.perf_counter()
    res = solve(case)
    elapsed = time.perf_counter() - t0
    assert res["status"] == "SOLVED"
    assert elapsed < 2.0, f"Solver took {elapsed:.3f}s for D=10"
