"""Tests for C034 Reference Solver and 4D Convex Geometry Engine.

AuthorityEffect: None.
"""

from __future__ import annotations

from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c034_calabi_yau_hodge_numbers.reference_solver.calabi_yau import (
    compute_affine_dimension,
    cross4,
    det3,
    det4,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c034_calabi_yau_hodge_numbers.reference_solver.ddc_tracer import (
    DDCTracer,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c034_calabi_yau_hodge_numbers.reference_solver.solver import (
    solve,
)


def test_linear_algebra_primitives():
    """Validates 3x3/4x4 determinants, 4D cross products, and affine dimension."""
    # 3x3 det
    assert det3((1, 0, 0), (0, 1, 0), (0, 0, 1)) == 1
    assert det3((2, 0, 0), (0, 3, 0), (0, 0, 5)) == 30

    # 4x4 det
    assert det4((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)) == 1
    assert det4((1, 1, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)) == 1

    # 4D cross product orthogonality
    d1 = (1, 0, 0, 0)
    d2 = (0, 1, 0, 0)
    d3 = (0, 0, 1, 0)
    n = cross4(d1, d2, d3)
    assert n == (0, 0, 0, -1)
    assert sum(n[i] * d1[i] for i in range(4)) == 0
    assert sum(n[i] * d2[i] for i in range(4)) == 0
    assert sum(n[i] * d3[i] for i in range(4)) == 0

    # Affine dimension
    assert compute_affine_dimension([(0, 0, 0, 0)]) == 0
    assert compute_affine_dimension([(0, 0, 0, 0), (1, 0, 0, 0)]) == 1
    assert compute_affine_dimension([(0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0)]) == 2
    assert compute_affine_dimension([(0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)]) == 3
    assert (
        compute_affine_dimension(
            [(0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)]
        )
        == 4
    )


def test_solver_quintic_primal_and_dual():
    """Validates quintic threefold in both dual and primal readings."""
    quintic_v = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [-1, -1, -1, -1]]

    # Dual reading (input is Delta*) -> h11=1, h21=101, euler=-200
    res_dual = solve({"case_id": "quintic_dual", "reading": "dual", "vertices": quintic_v})
    assert res_dual["status"] == "SOLVED"
    assert res_dual["h11"] == 1
    assert res_dual["h21"] == 101
    assert res_dual["euler"] == -200
    assert res_dual["face_data"]["l_delta"] == 126
    assert res_dual["face_data"]["l_delta_star"] == 6

    # Primal reading (input is Delta) -> h11=101, h21=1, euler=200
    res_primal = solve({"case_id": "quintic_primal", "reading": "primal", "vertices": quintic_v})
    assert res_primal["status"] == "SOLVED"
    assert res_primal["h11"] == 101
    assert res_primal["h21"] == 1
    assert res_primal["euler"] == 200


def test_solver_16cell_and_products():
    """Validates 4D cross-polytope (16-cell) and direct products."""
    crosspoly_v = [
        [1, 0, 0, 0],
        [-1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, -1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, -1, 0],
        [0, 0, 0, 1],
        [0, 0, 0, -1],
    ]
    res = solve({"case_id": "16cell", "reading": "dual", "vertices": crosspoly_v})
    assert res["status"] == "SOLVED"
    assert res["h11"] == 4
    assert res["h21"] == 68
    assert res["euler"] == -128


def test_solver_gl4z_invariance():
    """Validates invariance under unimodular coordinate shear."""
    # Quintic sheared by unimodular matrix
    sheared_v = [[1, 0, 0, 0], [1, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [-2, -1, -1, -1]]
    res = solve({"case_id": "sheared", "reading": "dual", "vertices": sheared_v})
    assert res["status"] == "SOLVED"
    assert res["h11"] == 1
    assert res["h21"] == 101
    assert res["euler"] == -200


def test_solver_codim2_correction_accuracy():
    """Validates that cases with non-trivial 2-faces compute correct positive correction terms."""
    codim2_v = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [-1, -2, -2, -2]]
    # Dual reading: input is Delta*, X_Delta has h11=2, h21=86, euler=-168
    res_dual = solve(
        {"id": "codim2_dual", "case_id": "codim2", "reading": "dual", "vertices": codim2_v}
    )
    assert res_dual["status"] == "SOLVED"
    assert res_dual["h11"] == 2
    assert res_dual["h21"] == 86
    assert res_dual["euler"] == -168
    prods_d = res_dual["face_data"]["codim2_products"]
    assert len(prods_d) > 0
    assert sum(p["product"] for p in prods_d) == 3

    # Primal reading: input is Delta, X_Delta* has h11=86, h21=2, euler=168
    res_primal = solve(
        {"id": "codim2_primal", "case_id": "codim2", "reading": "primal", "vertices": codim2_v}
    )
    assert res_primal["status"] == "SOLVED"
    assert res_primal["h11"] == 86
    assert res_primal["h21"] == 2
    assert res_primal["euler"] == 168


def test_solver_convex_hull_redundancy_removal():
    """Validates that redundant interior origin is eliminated without altering convex hull."""
    quintic_v = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [-1, -1, -1, -1]]
    redundant_v = quintic_v + [[0, 0, 0, 0]]
    res = solve({"case_id": "redundant", "reading": "dual", "vertices": redundant_v})
    assert res["status"] == "SOLVED"
    assert res["h11"] == 1
    assert res["h21"] == 101


def test_solver_out_of_scope_detection():
    """Validates rejection of non-reflexive near-misses with exact witnesses."""
    # Distance 2
    res_dist2 = solve(
        {
            "case_id": "dist2",
            "reading": "dual",
            "vertices": [[2, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [-1, -1, -1, -1]],
        }
    )
    assert res_dist2["status"] == "OUT_OF_SCOPE"
    assert res_dist2["witness"]["kind"] == "facet_distance"
    assert res_dist2["witness"]["distance"] == 2

    # Origin on facet
    res_orig = solve(
        {
            "case_id": "orig",
            "reading": "dual",
            "vertices": [[0, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [-1, -1, -1, -1]],
        }
    )
    assert res_orig["status"] == "OUT_OF_SCOPE"
    assert res_orig["witness"]["kind"] == "origin_not_interior"

    # Lower dimension
    res_dim3 = solve(
        {
            "case_id": "dim3",
            "reading": "dual",
            "vertices": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [-1, -1, -1, 0], [0, 0, 0, 0]],
        }
    )
    assert res_dim3["status"] == "OUT_OF_SCOPE"
    assert res_dim3["witness"]["kind"] == "dimension_deficient"


def test_solver_unknown_refusals():
    """Validates fail-closed UNKNOWN refusals on out-of-bounds inputs."""
    # Out of bounds coordinate
    res_oob = solve(
        {
            "case_id": "oob",
            "reading": "dual",
            "vertices": [[35, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [-1, -1, -1, -1]],
        }
    )
    assert res_oob["status"] == "UNKNOWN"
    assert res_oob["refusal_code"] == "COORDINATES_OUT_OF_BOUNDS"

    # Too many vertices
    res_many = solve({"case_id": "many", "reading": "dual", "vertices": [[0, 0, 0, 0]] * 45})
    assert res_many["status"] == "UNKNOWN"
    assert res_many["refusal_code"] == "TOO_MANY_VERTICES"

    # Malformed structure
    assert solve("not_a_dict")["status"] == "UNKNOWN"
    assert solve({"no_id": True})["status"] == "UNKNOWN"


def test_solver_ddc_tracer_receipt_chain():
    """Validates DDC 8-letter operational tracer step chaining."""
    tracer = DDCTracer()
    tracer.record_step("C", {"action": "context_intake"})
    tracer.record_step("I", {"action": "facets_and_polar_dual"})
    tracer.record_step("Lambda", {"action": "face_lattice"})
    tracer.record_step("R", {"action": "residual_check"})
    tracer.record_step("D", {"action": "batyrev_descent"})
    tracer.record_step("E", {"action": "exact_closure"})
    tracer.record_step("T", {"action": "terminal_complete"})

    exp = tracer.export_trace()
    assert exp["step_count"] == 7
    assert exp["letters"] == ["C", "I", "Lambda", "R", "D", "E", "T"]
    assert exp["final_digest"] is not None
    assert len(exp["final_digest"]) == 64


def test_solver_mirror_swap_base_09_vs_ctrl_10():
    """Explicitly validates mirror swap duality between base_09 and ctrl_10."""
    import json
    from pathlib import Path

    judge_dir = Path(__file__).resolve().parent.parent / "judge_packet"
    f_b09 = judge_dir / "cases" / "base" / "base_09_codim2_k3_fibration.json"
    f_c10 = judge_dir / "cases" / "controls" / "ctrl_10_dual_reading_swap_codim2.json"

    case_b09 = json.loads(f_b09.read_text(encoding="utf-8"))
    case_c10 = json.loads(f_c10.read_text(encoding="utf-8"))

    res_b09 = solve(case_b09)
    res_c10 = solve(case_c10)

    assert res_b09["status"] == "SOLVED"
    assert res_c10["status"] == "SOLVED"

    # Exact Hodge numbers and Euler characteristics
    assert (res_b09["h11"], res_b09["h21"]) == (2, 86)
    assert res_b09["euler"] == -168

    assert (res_c10["h11"], res_c10["h21"]) == (86, 2)
    assert res_c10["euler"] == 168

    # Mirror swap bijection
    assert res_b09["h11"] == res_c10["h21"]
    assert res_b09["h21"] == res_c10["h11"]
    assert res_b09["euler"] == -res_c10["euler"]

    # Lattice point counts swap
    assert res_b09["face_data"]["l_delta"] == res_c10["face_data"]["l_delta_star"]
    assert res_b09["face_data"]["l_delta_star"] == res_c10["face_data"]["l_delta"]


def test_solver_mirror_swap_all_solvable_base_cases():
    """Validates mirror swap duality for all 24 solvable base cases."""
    import json
    from pathlib import Path

    judge_dir = Path(__file__).resolve().parent.parent / "judge_packet"
    base_cases = sorted((judge_dir / "cases" / "base").glob("*.json"))

    solvable_cases = [
        cf
        for cf in base_cases
        if not cf.stem.startswith(
            ("base_25", "base_26", "base_27", "base_28", "base_29", "base_30")
        )
    ]
    assert len(solvable_cases) == 24, f"Expected 24 solvable base cases, got {len(solvable_cases)}"

    for cf in solvable_cases:
        case = json.loads(cf.read_text(encoding="utf-8"))
        case_dual = {**case, "reading": "dual"}
        case_primal = {**case, "reading": "primal"}

        rd = solve(case_dual)
        rp = solve(case_primal)

        assert rd["status"] == "SOLVED", f"Failed solving dual on {cf.name}"
        assert rp["status"] == "SOLVED", f"Failed solving primal on {cf.name}"

        assert rd["h11"] == rp["h21"], (
            f"Mirror swap failed for {cf.name}: rd.h11={rd['h11']} != rp.h21={rp['h21']}"
        )
        assert rd["h21"] == rp["h11"], (
            f"Mirror swap failed for {cf.name}: rd.h21={rd['h21']} != rp.h11={rp['h11']}"
        )
        assert rd["euler"] == -rp["euler"], (
            f"Mirror Euler sign flip failed for {cf.name}: rd.euler={rd['euler']} != -rp.euler={-rp['euler']}"
        )
        assert rd["face_data"]["l_delta"] == rp["face_data"]["l_delta_star"], (
            f"Lattice point swap failed for {cf.name}: l_delta mismatch"
        )
        assert rd["face_data"]["l_delta_star"] == rp["face_data"]["l_delta"], (
            f"Lattice point swap failed for {cf.name}: l_delta_star mismatch"
        )
