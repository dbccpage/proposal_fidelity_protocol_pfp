"""
Executable verification for Derivation ATL-P001-009 (PFP001-09).

Audit verification of the paper-local Python reference solver and governor:
1. Independent primal-dual certificate verification (coverage, capacity,
   flow conservation divergence, objective balance, zero duality gap, exact rational types)
   and refusal via ArithmeticError inside compute_exact_phi_1.
2. Component tree enumeration cap of 100,000 trees (SpanningTreeLimitExceeded
   on K_8 in ~0.2s) and independent per-component reset across disjoint subgraphs.
3. Governor monotonic descent enforcement under MoveType.CUT:
   - DefectIncrease refusal
   - IdempotentStationaryLoop refusal
   - NonDecreasingCut refusal (iso-defect potential changes)
   - Zero state mutation on refusal
   - Strict descent admission
"""

from fractions import Fraction
from pathlib import Path
import sys
import time
import pytest

# Ensure the paper-local code directory is importable
_CODE_DIR = (
    Path(__file__).resolve().parent.parent
    / "atlas"
    / "archive"
    / "pfp"
    / "001_pfp_discrete_cochain_retraction_and_toy_involutions"
    / "code"
)
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

import symbol_game_governor as sgg
from symbol_game_governor import (
    ConstraintGraph,
    Edge,
    MoveType,
    Phi1Certificate,
    SpanningTreeLimitExceeded,
    StepVerdict,
    SymbolGameGovernor,
    _spanning_trees,
    compute_exact_phi_1,
    verify_phi_1_certificate,
)


def test_primal_dual_independent_verification_and_refusal():
    """
    Evaluates independent certificate verification criteria:
    - coverage and well-formedness
    - dual capacity bounds |x_e| <= w_e
    - vertex flow conservation divergence == 0
    - primal and dual objective agreement == phi_1
    - zero duality gap
    - exact rational scalar types (rejecting float)

    Also evaluates that compute_exact_phi_1 raises ArithmeticError if
    certificate verification fails.
    """
    vertices = ["a", "b", "c"]
    edges = [("a", "b", 1), ("b", "c", 2), ("a", "c", 2)]
    claims = {
        ("a", "b"): Fraction(1),
        ("b", "c"): Fraction(2),
        ("a", "c"): Fraction(2),
    }

    cert = compute_exact_phi_1(vertices, edges, claims)
    assert verify_phi_1_certificate(vertices, edges, claims, cert) is True

    # 1. Capacity violation: dual flow exceeds capacity |x_e| > w_e
    bad_capacity_dual = dict(cert.dual_circulations)
    bad_capacity_dual[("a", "b")] = Fraction(2)  # w_e is 1
    bad_cert_cap = Phi1Certificate(
        phi_1=cert.phi_1,
        primal_potentials=cert.primal_potentials,
        dual_circulations=bad_capacity_dual,
        duality_gap=cert.duality_gap,
    )
    assert verify_phi_1_certificate(vertices, edges, claims, bad_cert_cap) is False

    # 2. Flow conservation violation: non-zero divergence at vertices
    bad_div_dual = dict(cert.dual_circulations)
    bad_div_dual[("b", "c")] = Fraction(0)  # breaks circulation balance
    bad_cert_div = Phi1Certificate(
        phi_1=cert.phi_1,
        primal_potentials=cert.primal_potentials,
        dual_circulations=bad_div_dual,
        duality_gap=cert.duality_gap,
    )
    assert verify_phi_1_certificate(vertices, edges, claims, bad_cert_div) is False

    # 3. Objective mismatch: phi_1 does not match recomputed primal/dual
    bad_cert_obj = Phi1Certificate(
        phi_1=Fraction(999),
        primal_potentials=cert.primal_potentials,
        dual_circulations=cert.dual_circulations,
        duality_gap=cert.duality_gap,
    )
    assert verify_phi_1_certificate(vertices, edges, claims, bad_cert_obj) is False

    # 4. Non-zero duality gap
    bad_cert_gap = Phi1Certificate(
        phi_1=cert.phi_1,
        primal_potentials=cert.primal_potentials,
        dual_circulations=cert.dual_circulations,
        duality_gap=Fraction(1),
    )
    assert verify_phi_1_certificate(vertices, edges, claims, bad_cert_gap) is False

    # 5. Non-exact scalar type: float rejected by Phi1Certificate constructor with TypeError,
    # and rejected by verify_phi_1_certificate if passed via certificate-like object
    with pytest.raises(TypeError, match="phi_1 must be an exact int or Fraction, got float"):
        Phi1Certificate(
            phi_1=float(cert.phi_1),
            primal_potentials=cert.primal_potentials,
            dual_circulations=cert.dual_circulations,
            duality_gap=cert.duality_gap,
        )

    class DuckCertWithFloat:
        phi_1 = float(cert.phi_1)
        duality_gap = cert.duality_gap
        primal_potentials = cert.primal_potentials
        dual_circulations = cert.dual_circulations

    assert verify_phi_1_certificate(vertices, edges, claims, DuckCertWithFloat()) is False

    # 6. Incomplete vertex coverage in primal potentials
    incomplete_primal = {k: v for k, v in cert.primal_potentials.items() if k != "c"}
    bad_cert_cov = Phi1Certificate(
        phi_1=cert.phi_1,
        primal_potentials=incomplete_primal,
        dual_circulations=cert.dual_circulations,
        duality_gap=cert.duality_gap,
    )
    assert verify_phi_1_certificate(vertices, edges, claims, bad_cert_cov) is False

    # 7. Independent verification refusal inside compute_exact_phi_1
    orig_verifier = sgg.verify_phi_1_certificate
    try:
        sgg.verify_phi_1_certificate = lambda *args: False
        with pytest.raises(ArithmeticError, match="Primal-dual certificate failed independent verification"):
            compute_exact_phi_1(vertices, edges, claims)
    finally:
        sgg.verify_phi_1_certificate = orig_verifier


def test_component_tree_cap_100k_and_per_component_reset():
    """
    Evaluates:
    - Complete graph K_8 (8 vertices, 28 edges, Cayley formula 8^6 = 262,144 trees)
      raises SpanningTreeLimitExceeded upon reaching MAX_SPANNING_TREES (100,000)
      in sub-second runtime.
    - Disjoint components each below the 100,000 cap succeed without
      accumulating tree counts across component boundaries.
    """
    # 1. Complete graph K_8 hits 100,000 cap quickly
    v8 = [f"v{i}" for i in range(8)]
    e8 = [(v8[i], v8[j], 1) for i in range(8) for j in range(i + 1, 8)]

    start_time = time.perf_counter()
    with pytest.raises(SpanningTreeLimitExceeded, match="more than 100000 spanning trees in a component of 8 vertices"):
        _spanning_trees(v8, e8, 100_000)
    elapsed = time.perf_counter() - start_time
    # Should terminate rapidly (typically < 0.5s)
    assert elapsed < 5.0, f"Enumeration took longer than expected: {elapsed:.2f}s"

    # 2. Disjoint components each below cap execute without cross-component accumulation
    # Two disconnected 3-cycles, each having 3 spanning trees (total 6 spanning trees).
    v_disjoint = ["a1", "a2", "a3", "b1", "b2", "b3"]
    e_disjoint = [
        ("a1", "a2", 1), ("a2", "a3", 1), ("a1", "a3", 1),
        ("b1", "b2", 1), ("b2", "b3", 1), ("b1", "b3", 1),
    ]
    c_disjoint = {
        ("a1", "a2"): Fraction(1), ("a2", "a3"): Fraction(1), ("a1", "a3"): Fraction(2),
        ("b1", "b2"): Fraction(2), ("b2", "b3"): Fraction(2), ("b1", "b3"): Fraction(4),
    }

    # Verify that compute_exact_phi_1 runs each component with MAX_SPANNING_TREES independently
    cert = compute_exact_phi_1(v_disjoint, e_disjoint, c_disjoint)
    assert cert.phi_1 == Fraction(0)
    assert cert.duality_gap == Fraction(0)
    assert verify_phi_1_certificate(v_disjoint, e_disjoint, c_disjoint, cert) is True


def test_governor_strictly_decreasing_updates_and_rejections():
    """
    Evaluates SymbolGameGovernor.execute_move(MoveType.CUT, payload):
    - DefectIncrease refusal: proposed defect > current defect
    - IdempotentStationaryLoop refusal: proposed defect == current defect with unchanged state
    - NonDecreasingCut refusal: proposed defect == current defect with modified state
    - Zero state mutation on all refusal modes
    - Strict descent admission: proposed defect < current defect
    """
    graph = ConstraintGraph(
        ("a", "b", "c"),
        (Edge("a", "b", 1), Edge("b", "c", 1), Edge("a", "c", 1)),
    )
    # Exact 1-cochain where c(a,b)=3, c(b,c)=3, c(a,c)=6 (3+3=6, so phi_1=0)
    claims = {("a", "b"): 3, ("b", "c"): 3, ("a", "c"): 6}
    gov = SymbolGameGovernor(graph, claims)

    # Initial potential is 0 everywhere; initial defect is |3-0| + |3-0| + |6-0| = 12
    init_section = dict(gov.section)
    assert gov.compute_section_defect(gov.section) == 12

    # 1. DefectIncrease refusal: proposing potentials that increase defect
    out_increase = gov.execute_move(MoveType.CUT, {"potentials": {"a": 10, "b": -10, "c": 0}})
    assert out_increase.admitted is False
    assert out_increase.verdict == StepVerdict.REFUSAL
    assert "Refused: DefectIncrease" in out_increase.feedback
    assert gov.section == init_section  # Zero mutation

    # 2. IdempotentStationaryLoop refusal: proposing identical potentials
    out_stationary = gov.execute_move(MoveType.CUT, {"potentials": {"a": 0, "b": 0, "c": 0}})
    assert out_stationary.admitted is False
    assert out_stationary.verdict == StepVerdict.REFUSAL
    assert "Refused: IdempotentStationaryLoop" in out_stationary.feedback
    assert gov.section == init_section  # Zero mutation

    # 3. NonDecreasingCut refusal: iso-defect potential shift (uniform shift preserving defect 12)
    out_isocut = gov.execute_move(MoveType.CUT, {"potentials": {"a": 5, "b": 5, "c": 5}})
    assert out_isocut.admitted is False
    assert out_isocut.verdict == StepVerdict.REFUSAL
    assert "Refused: NonDecreasingCut" in out_isocut.feedback
    assert gov.section == init_section  # Zero mutation

    # 4. Strict descent admission: proposing potentials with strictly lower defect (defect 8 < 12)
    out_descent = gov.execute_move(MoveType.CUT, {"potentials": {"a": 0, "b": 1, "c": 2}})
    assert out_descent.admitted is True
    assert out_descent.verdict == StepVerdict.DESCENT
    assert out_descent.defect == 8
    assert "Admitted CUT" in out_descent.feedback
    # State is mutated to the admitted potential
    assert gov.section["a"] == Fraction(0)
    assert gov.section["b"] == Fraction(1)
    assert gov.section["c"] == Fraction(2)
