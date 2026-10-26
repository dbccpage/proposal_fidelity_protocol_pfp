"""
Zenodo Readiness Regression Suite: 5 Core Release Verification Tests.

Tests the five critical publication blockers identified in the adversarial audit:
  1. Tree Phi_1 = 0 with matching primal-dual certificates.
  2. Triangle Phi_1 = 5 with matching primal section (D=5) and dual circulation (sum c*x = 5).
  3. CUT invariance of Phi_1([c]) alongside strict section defect descent D(s_{t+1}) < D(s_t).
  4. Rejection of the 'cancel' pseudo-witness (gibberish/empty mapping receives refusal).
  5. Physics negative controls: U=0 and balanced U<0 recognized as sign-free under
     determinantal representations, while odd-cycle worldline hopping triggers obstruction.
"""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from certificate_gate import BqnfCertificateGate
from symbol_game_governor import (
    ConstraintGraph,
    Edge,
    L1SymbolGameGovernor,
    MoveType,
    StepVerdict,
    compute_exact_phi_1,
)


def test_regression_1_tree_phi_1_zero():
    """
    Regression Test 1:
    Two-edge tree: e1 = (a -> b, w=1, c=1), e2 = (b -> c, w=1, c=2).
    True Phi_1 must be 0 with exact primal section s=(0, 1, 3) and dual circulation x=(0, 0).
    """
    vertices = ("a", "b", "c")
    edges = (
        ("a", "b", 1),
        ("b", "c", 1),
    )
    claims = {("a", "b"): Fraction(1), ("b", "c"): Fraction(2)}

    cert = compute_exact_phi_1(vertices, edges, claims)

    assert cert.phi_1 == 0, f"Expected Phi_1 = 0 on tree, got {cert.phi_1}"
    assert cert.duality_gap == 0, f"Expected duality gap = 0, got {cert.duality_gap}"
    assert cert.verify(vertices, edges, claims)

    # Verify primal section gives D(s) = 0
    s = cert.primal_potentials
    diff_ab = s["b"] - s["a"]
    diff_bc = s["c"] - s["b"]
    d_s = 1 * abs(Fraction(1) - diff_ab) + 1 * abs(Fraction(2) - diff_bc)
    assert d_s == 0, f"Primal section defect must be 0, got {d_s}"

    # Verify dual circulation is identically zero
    assert cert.dual_circulations[("a", "b")] == 0
    assert cert.dual_circulations[("b", "c")] == 0


def test_regression_2_triangle_phi_1_five():
    """
    Regression Test 2:
    Weighted triangle: e1 = (a -> b, w=1, c=1), e2 = (b -> c, w=2, c=2), e3 = (c -> a, w=2, c=2).
    Cycle claim sum = 1 + 2 + 2 = 5.
    Every edge weight >= 1, so 5 is a lower bound (unit circulation lower bound = 5).
    Section s(a)=0, s(b)=-4, s(c)=-2 has defect D(s) = 1*|1 - (-4)| + 2*|2 - 2| + 2*|2 - 2| = 5.
    True minimum Phi_1 is 5 (not 7).
    """
    vertices = ("a", "b", "c")
    edges = (
        ("a", "b", 1),
        ("b", "c", 2),
        ("c", "a", 2),
    )
    claims = {
        ("a", "b"): Fraction(1),
        ("b", "c"): Fraction(2),
        ("c", "a"): Fraction(2),
    }

    cert = compute_exact_phi_1(vertices, edges, claims)

    assert cert.phi_1 == 5, f"Expected exact Phi_1 = 5 on weighted triangle, got {cert.phi_1}"
    assert cert.duality_gap == 0, f"Expected duality gap = 0, got {cert.duality_gap}"
    assert cert.verify(vertices, edges, claims)

    # Primal certificate verification
    s = cert.primal_potentials
    res_ab = abs(Fraction(1) - (s["b"] - s["a"]))
    res_bc = abs(Fraction(2) - (s["c"] - s["b"]))
    res_ca = abs(Fraction(2) - (s["a"] - s["c"]))
    d_s = 1 * res_ab + 2 * res_bc + 2 * res_ca
    assert d_s == 5, f"Primal section must achieve upper bound D(s) = 5, got {d_s}"

    # Dual circulation verification: x(e) in [-w_e, w_e] with zero divergence
    x = cert.dual_circulations
    assert abs(x[("a", "b")]) <= 1
    assert abs(x[("b", "c")]) <= 2
    assert abs(x[("c", "a")]) <= 2
    # Divergence at each node must be zero
    div_a = x[("c", "a")] - x[("a", "b")]
    div_b = x[("a", "b")] - x[("b", "c")]
    div_c = x[("b", "c")] - x[("c", "a")]
    assert div_a == 0 and div_b == 0 and div_c == 0, "Dual vector must be a circulation (zero divergence)"

    # Dual lower bound calculation
    dual_val = Fraction(1) * x[("a", "b")] + Fraction(2) * x[("b", "c")] + Fraction(2) * x[("c", "a")]
    assert dual_val == 5, f"Dual circulation lower bound must equal 5, got {dual_val}"


def test_regression_3_cut_invariance_and_defect_descent():
    """
    Regression Test 3:
    A CUT modifies section potentials s, descending section defect D(s).
    Phi_1([c]) depends strictly on edge claims [c] and is INVARIANT under CUT.
    The governor must maintain D(s) >= Phi_1([c]) at all steps.
    """
    vertices = ("a", "b", "c")
    edges = (
        Edge("a", "b", weight=1),
        Edge("b", "c", weight=2),
        Edge("c", "a", weight=2),
    )
    graph = ConstraintGraph(vertices, edges)
    claims = {
        ("a", "b"): 1,
        ("b", "c"): 2,
        ("c", "a"): 2,
    }
    gov = L1SymbolGameGovernor(graph, initial_claims=claims)

    # Initial state: s = (0, 0, 0)
    init_defect = gov.compute_section_defect(gov.section)
    init_phi1, _ = gov.compute_phi_1()

    assert init_phi1 == 5
    assert init_defect == 9  # 1*1 + 2*2 + 2*2 = 9
    assert init_defect >= init_phi1, f"Invariant D(s) >= Phi_1 violated: {init_defect} < {init_phi1}"

    # Execute valid CUT to s = (0, -4, -2)
    cut_step = gov.execute_move(MoveType.CUT, {"potentials": {"a": 0, "b": -4, "c": -2}})
    assert cut_step.admitted
    assert cut_step.defect == 5
    assert cut_step.phi_1 == 5  # Phi_1 is strictly INVARIANT under CUT!
    assert cut_step.verdict == StepVerdict.HOLD  # Optimal positive cost is HOLD; EXACT is reserved for cost zero.

    # Assert invariant holds post-CUT
    assert cut_step.defect >= cut_step.phi_1

    # Attempt defect-increasing CUT: must be REFUSED
    bad_cut = gov.execute_move(MoveType.CUT, {"potentials": {"a": 0, "b": 10, "c": -10}})
    assert not bad_cut.admitted
    assert bad_cut.verdict == StepVerdict.REFUSAL
    assert "DefectIncrease" in bad_cut.feedback
    assert gov.compute_section_defect(gov.section) == 5  # State unchanged


def test_regression_4_rejection_of_cancel_pseudo_witness():
    """
    Regression Test 4:
    A witness with type 'gibberish', empty mapping, or proof text 'cancel'
    must NOT receive ExactCancellation. It must be refused with all 4 laws reported false.
    """
    gate = BqnfCertificateGate("free_fermion")

    # Pseudo-witness: gibberish type, empty mapping, proof says "cancel"
    pseudo_witness = {
        "move_type": "VERIFY_SIGN_FREE",
        "xi_witness": {
            "type": "gibberish",
            "proof": "cancel all terms",
            "mapping": "",
        },
    }

    cert = gate.verify_sign_free(pseudo_witness)

    assert not cert.valid, "Pseudo-witness must be rejected"
    assert cert.status == "Refused_UnverifiedInvolution_InvalidWitness"
    assert cert.condition_checks["involution_law"] is False
    assert cert.condition_checks["fixed_point_free"] is False
    assert cert.condition_checks["sign_reversing"] is False
    assert cert.condition_checks["weight_preserving"] is False

    # Also test incomplete laws (e.g. valid mapping but missing weight-preserving proof)
    incomplete_witness = {
        "move_type": "VERIFY_SIGN_FREE",
        "xi_witness": {
            "type": "sublattice_pairing",
            "proof": "involution xi(xi(x))=x pairs opposite sign sgn(xi(x))=-sgn(x)",
            "mapping": "x <-> y",
        },
    }
    cert_inc = gate.verify_sign_free(incomplete_witness)
    assert not cert_inc.valid
    assert cert_inc.status == "Refused_UnverifiedInvolution_InvalidWitness"
    assert cert_inc.condition_checks["weight_preserving"] is False


def test_regression_5_physics_negative_controls():
    """
    Regression Test 5:
    Physical and basis scoping:
      - U=0 (free fermions) on an odd cycle has determinantal positivity det(I + e^{-beta h}) > 0.
      - Balanced U < 0 (attractive Hubbard) on an odd cycle has determinantal squaring [det M(sigma)]^2 >= 0.
      - In worldline hopping basis, odd cycles (C3, C5, Kagome) lack alternating site gauge:
        VERIFY_SIGN_FREE is refused (AM-FSP-2) and OPEN_SIGN_OBSTRUCTION is admitted.
    """
    hopping = [[0, -1, -1], [-1, 0, -1], [-1, -1, 0]]
    # 1. Free fermions U=0 with explicit Hermitian matrices
    gate_c3_u0 = BqnfCertificateGate("c3_triangular", parameters={"U": 0, "h_up": hopping, "h_down": hopping})
    u0_det_move = {
        "move_type": "VERIFY_SIGN_FREE",
        "representation": "determinant",
        "route": "determinantal_positivity",
    }
    cert_u0 = gate_c3_u0.verify_sign_free(u0_det_move)
    assert cert_u0.valid, "U=0 free fermions on C3 must be admitted under determinant representation"
    assert cert_u0.status == "DeterminantalPositivity"

    # 2. Spin-balanced attractive Hubbard (U = -2.0) on C5 pentagon under continuous HS decoupling
    gate_c5_attr = BqnfCertificateGate("c5_pentagon", parameters={"U": -2, "h_up": hopping, "h_down": hopping, "mu_up": 0, "mu_down": 0})
    attr_det_move = {
        "move_type": "VERIFY_SIGN_FREE",
        "representation": "continuous_hs",
        "route": "determinant_squaring",
    }
    cert_attr = gate_c5_attr.verify_sign_free(attr_det_move)
    assert cert_attr.valid, "Balanced attractive Hubbard (U < 0) on C5 must be admitted via determinant squaring"
    assert cert_attr.status == "DeterminantalPositivity"

    # 3. Worldline hopping basis on odd cycle (C3): alternating site gauge is obstructed
    gate_c3_hop = BqnfCertificateGate("c3_triangular", parameters={"U": 2, "t": 1, "bonds": [(0,1), (1,2), (2,0)]})
    hop_move = {
        "move_type": "VERIFY_SIGN_FREE",
        "representation": "worldline_hopping",
        "xi_witness": {
            "type": "sublattice_gauge",
            "proof": "Attempt alternating site gauge on C3",
            "mapping": "c_i -> (-1)^i c_i",
        },
    }
    cert_hop = gate_c3_hop.verify_sign_free(hop_move)
    assert not cert_hop.valid, "Worldline hopping on odd cycle must reject uncertified verify"
    assert cert_hop.status == "Refused_UnverifiedInvolution_InvalidWitness"

    # Proper move in worldline hopping basis is OPEN_SIGN_OBSTRUCTION
    obs_move = {
        "move_type": "OPEN_SIGN_OBSTRUCTION",
        "obstruction_witness": {"type": "alternating_site_gauge", "cycle": [0,1,2]},
    }
    status, admitted, feedback = gate_c3_hop.verify_proposal_item(obs_move)
    assert admitted
    assert status == "OpenGaugeObstruction"
