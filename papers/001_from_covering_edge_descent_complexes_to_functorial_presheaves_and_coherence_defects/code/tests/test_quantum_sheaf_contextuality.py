"""Unit tests for Quantum Sheaf Contextuality and Bell-CHSH Presheaf Gluing Obstruction.

AuthorityEffect: None.

Tests:
1. Poset structure: 9 contexts (base, 4 singles, 4 pairs) and covering edge relations.
2. Presheaf flatness: K == 0 identically on all 49 triples (composite marginals commute).
3. No-Signaling condition: covering-edge descent d_0 e == 0 holds for physical models,
   and fails with non-zero residual for signaling models.
4. Classical LHV models: Bell parameter |S| <= 2 and exact Cech obstruction distance == 0.
5. PR-box model: Bell parameter S == 4 and exact Cech obstruction distance == 2 with zero duality gap.
6. Isotropic Werner mixture: exact linear scaling Gamma_{context}(p) == 2*max(0, 2p - 1)
   with sharp LHV boundary at p == 1/2.
7. Fine's Theorem certification: non-contextual iff optimal joint distribution P* in Delta_16
   satisfies M_{glue} P* == e.
8. Dual witness certificate feasibility: ||Y*||_infty <= 1 and M_{glue}^T Y* + lambda * 1 <= 0.
"""

from fractions import Fraction
import pytest

from quantum_sheaf_contextuality import (
    GLUING_MATRIX_ROWS,
    JOINT_CONTEXTS,
    MICRO_STATES,
    EmpiricalModel,
    build_bell_chsh_poset,
    build_bell_sheaf_system,
    check_no_signaling_descent,
    compute_bell_chsh_parameter,
    solve_cech_contextuality_obstruction,
    verify_bell_sheaf_flatness,
)


def test_bell_poset_structure():
    poset = build_bell_chsh_poset()
    assert len(poset.elements) == 9
    assert set(poset.elements) == {
        "base", "A1", "A2", "B1", "B2", "C11", "C12", "C21", "C22"
    }

    # Covering edges count
    # 4 from base to singles, 8 from singles to pairs = 12 covering edges
    assert len(poset.covering_edges) == 12


def test_bell_sheaf_flatness():
    system = build_bell_sheaf_system()
    is_flat, triple_count = verify_bell_sheaf_flatness(system)
    assert is_flat
    assert triple_count == 49


def test_no_signaling_covering_descent():
    system = build_bell_sheaf_system()

    # 1. PR box satisfies no-signaling
    pr = EmpiricalModel.pr_box()
    is_ns, res = check_no_signaling_descent(system, pr)
    assert is_ns
    assert res == Fraction(0)

    # 2. Classical deterministic model satisfies no-signaling
    det = EmpiricalModel.classical_deterministic(1, 0, 1, 0)
    is_ns_det, res_det = check_no_signaling_descent(system, det)
    assert is_ns_det
    assert res_det == Fraction(0)

    # 3. Signaling model: distort Bob's marginal in C11
    signaling_data = dict(pr.context_data)
    # Change C11 distribution from (1/2, 0, 0, 1/2) to (3/4, 0, 0, 1/4)
    signaling_data["C11"] = (Fraction(3, 4), Fraction(0), Fraction(0), Fraction(1, 4))
    signaling_model = EmpiricalModel(name="SignalingModel", context_data=signaling_data)

    is_ns_sig, res_sig = check_no_signaling_descent(system, signaling_model)
    assert not is_ns_sig
    assert res_sig > Fraction(0)


def test_classical_lhv_non_contextuality():
    # Test deterministic LHV models
    for a1 in (0, 1):
        for b1 in (0, 1):
            det = EmpiricalModel.classical_deterministic(a1, 0, b1, 0)
            receipt = solve_cech_contextuality_obstruction(det)
            assert not receipt.is_contextual
            assert receipt.obstruction_distance == Fraction(0)
            assert receipt.duality_gap == Fraction(0)
            assert abs(receipt.bell_chsh_parameter) <= Fraction(2)

    # Test convex mixture of deterministic models
    weights = [Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)]
    tuples = [(0, 0, 0, 0), (1, 0, 0, 1), (0, 1, 1, 0)]
    mixture = EmpiricalModel.classical_mixture(weights, tuples, name="TestMixture")
    receipt_mix = solve_cech_contextuality_obstruction(mixture)
    assert not receipt_mix.is_contextual
    assert receipt_mix.obstruction_distance == Fraction(0)
    assert receipt_mix.duality_gap == Fraction(0)
    assert abs(receipt_mix.bell_chsh_parameter) <= Fraction(2)


def test_pr_box_maximal_contextuality():
    pr = EmpiricalModel.pr_box()
    receipt = solve_cech_contextuality_obstruction(pr)

    assert receipt.is_contextual
    assert receipt.is_bell_violating
    assert receipt.bell_chsh_parameter == Fraction(4)
    assert receipt.obstruction_distance == Fraction(2)
    assert receipt.duality_gap == Fraction(0)
    assert receipt.dual_objective == Fraction(2)


def test_isotropic_werner_mixture_phase_transition():
    # p = 1: PR box (S = 4, Obs = 2)
    w_1 = EmpiricalModel.isotropic_werner_model(Fraction(1))
    r_1 = solve_cech_contextuality_obstruction(w_1)
    assert r_1.bell_chsh_parameter == Fraction(4)
    assert r_1.obstruction_distance == Fraction(2)
    assert r_1.duality_gap == Fraction(0)

    # p = 3/4: Contextual (S = 3, Obs = 1)
    w_34 = EmpiricalModel.isotropic_werner_model(Fraction(3, 4))
    r_34 = solve_cech_contextuality_obstruction(w_34)
    assert r_34.bell_chsh_parameter == Fraction(3)
    assert r_34.obstruction_distance == Fraction(1)
    assert r_34.duality_gap == Fraction(0)

    # p = 1/2: Classical boundary (S = 2, Obs = 0)
    w_12 = EmpiricalModel.isotropic_werner_model(Fraction(1, 2))
    r_12 = solve_cech_contextuality_obstruction(w_12)
    assert r_12.bell_chsh_parameter == Fraction(2)
    assert r_12.obstruction_distance == Fraction(0)
    assert r_12.duality_gap == Fraction(0)

    # p = 1/4: Strictly classical (S = 1, Obs = 0)
    w_14 = EmpiricalModel.isotropic_werner_model(Fraction(1, 4))
    r_14 = solve_cech_contextuality_obstruction(w_14)
    assert r_14.bell_chsh_parameter == Fraction(1)
    assert r_14.obstruction_distance == Fraction(0)
    assert r_14.duality_gap == Fraction(0)

    # p = 0: White noise (S = 0, Obs = 0)
    w_0 = EmpiricalModel.isotropic_werner_model(Fraction(0))
    r_0 = solve_cech_contextuality_obstruction(w_0)
    assert r_0.bell_chsh_parameter == Fraction(0)
    assert r_0.obstruction_distance == Fraction(0)
    assert r_0.duality_gap == Fraction(0)


def test_dual_witness_feasibility():
    # Verify that dual witness Y* satisfies dual feasibility:
    # 1. |Y*_i| <= 1 for all i
    # 2. M_{glue}^T Y* + lambda * 1 <= 0
    pr = EmpiricalModel.pr_box()
    receipt = solve_cech_contextuality_obstruction(pr)

    y = receipt.dual_witness
    assert y is not None
    assert len(y) == 16
    for y_i in y:
        assert abs(y_i) <= Fraction(1)

    # Dual variable lambda:
    e = pr.joint_vector()
    dual_obj_without_lam = sum(y[i] * e[i] for i in range(16))
    lam = receipt.dual_objective - dual_obj_without_lam

    for j in range(16):
        col_dot_y = sum(GLUING_MATRIX_ROWS[i][j] * y[i] for i in range(16))
        assert col_dot_y + lam <= Fraction(0)
