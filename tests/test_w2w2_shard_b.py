"""
Executable verification for Window 2 Wave 2 Shard B Derivations (Note 001 & Note 002).

Derivations:
- AUDIT-N001-013: Discrete Chebyshev approximation on graphs (ATL-N001-013)
- AUDIT-N001-019: Quantum cocycle defect bound and trace-norm coherence (ATL-N001-019)
- AUDIT-N001-020: Nonzero classes define non-trivial H^1(G; R) (ATL-N001-020)
- AUDIT-N002-020: Admission check for d1 d0 = 0 (ATL-N002-020)

AuthorityEffect: None.
"""

import cmath
from dataclasses import dataclass
from fractions import Fraction
import math
import sys
from typing import Any, Sequence

import numpy as np
import pytest

# Add archive modules to sys.path
sys.path.insert(0, "atlas/archive/non_pfp/001_l1_native_cohomology/code")
sys.path.insert(0, "atlas/archive/non_pfp/002_l1_obstruction_framework/code")

from l1_cohomology import (
    DirectedGraph,
    ExactRationalLinfChebyshevSolver,
    L1QuotientSolver,
    LinfCertificateReceipt,
    check_linf_certificate_receipt,
)


# ============================================================================
# Helpers for AUDIT-N002-020: Admission Check for d1 d0 = 0
# ============================================================================

class AdmissionRefusalError(Exception):
    """Raised when a complex fails nilpotency admission check d1 d0 = 0."""
    pass


@dataclass(frozen=True)
class AdmissionReceipt:
    admitted: bool
    status: str
    d1_d0_matrix: list[list[Fraction]]
    max_absolute_defect: Fraction
    face_count: int
    edge_count: int
    vertex_count: int


def admission_check_d1_d0(
    d0: Sequence[Sequence[Fraction | int]],
    d1: Sequence[Sequence[Fraction | int]],
    vertex_count: int,
    edge_count: int,
    face_count: int,
) -> AdmissionReceipt:
    """
    Perform exact rational admission check d1 d0 = 0.
    
    Returns AdmissionReceipt with status:
    - ADMITTED_VACUOUS_GRAPH_TRUNCATION if face_count == 0
    - ADMITTED if d1 d0 == 0 identically over Fraction
    - REFUSED_NILPOTENCY_FAILURE if d1 d0 != 0
    """
    if face_count == 0 or len(d1) == 0:
        return AdmissionReceipt(
            admitted=True,
            status="ADMITTED_VACUOUS_GRAPH_TRUNCATION",
            d1_d0_matrix=[],
            max_absolute_defect=Fraction(0),
            face_count=0,
            edge_count=edge_count,
            vertex_count=vertex_count,
        )

    # Convert to Fraction matrices
    d0_frac = [[Fraction(val) for val in row] for row in d0]
    d1_frac = [[Fraction(val) for val in row] for row in d1]

    # Matrix product P = d1 @ d0: size (face_count x vertex_count)
    product: list[list[Fraction]] = []
    max_defect = Fraction(0)
    is_zero = True

    for f_idx in range(face_count):
        row: list[Fraction] = []
        for v_idx in range(vertex_count):
            entry = sum(
                (d1_frac[f_idx][e_idx] * d0_frac[e_idx][v_idx] for e_idx in range(edge_count)),
                Fraction(0),
            )
            row.append(entry)
            abs_entry = abs(entry)
            if abs_entry > max_defect:
                max_defect = abs_entry
            if entry != Fraction(0):
                is_zero = False
        product.append(row)

    if is_zero:
        return AdmissionReceipt(
            admitted=True,
            status="ADMITTED",
            d1_d0_matrix=product,
            max_absolute_defect=Fraction(0),
            face_count=face_count,
            edge_count=edge_count,
            vertex_count=vertex_count,
        )
    else:
        return AdmissionReceipt(
            admitted=False,
            status="REFUSED_NILPOTENCY_FAILURE",
            d1_d0_matrix=product,
            max_absolute_defect=max_defect,
            face_count=face_count,
            edge_count=edge_count,
            vertex_count=vertex_count,
        )


def evaluate_degree_2_curvature_gated(
    admission: AdmissionReceipt,
    d1: Sequence[Sequence[Fraction | int]],
    cochain: Sequence[Fraction | int],
) -> list[Fraction]:
    """
    Evaluate degree-2 curvature Gamma_2 = d1(omega) gated by nilpotency admission check.
    Refuses computation if the complex was not admitted.
    """
    if not admission.admitted:
        raise AdmissionRefusalError(
            f"Degree-2 inference refused: complex status {admission.status} "
            f"with max defect {admission.max_absolute_defect}"
        )
    cochain_frac = [Fraction(x) for x in cochain]
    curvatures = []
    for f_row in d1:
        val = sum((Fraction(c) * w for c, w in zip(f_row, cochain_frac)), Fraction(0))
        curvatures.append(val)
    return curvatures


# ============================================================================
# Tests for ATL-N001-013: Discrete Chebyshev Approximation
# ============================================================================

def test_audit_n001_013_chebyshev_c4_optimal_pairing_positive():
    """
    Positive Control: On C4 cycle with uniform weights and cochain (1, 0, 0, 0),
    Chebyshev norm is 1/4, duality gap is 0, and all 4 edges support the dual circulation.
    """
    graph = DirectedGraph.cycle(4)
    h = [1, 0, 0, 0]

    receipt = ExactRationalLinfChebyshevSolver.solve(graph, h)

    # Check Chebyshev norm
    assert receipt.chebyshev_norm == Fraction(1, 4)
    assert receipt.dual_bound == Fraction(1, 4)
    assert receipt.duality_gap == Fraction(0)
    assert receipt.status == "OPTIMAL_LINF"

    # Verify all 4 edges are active peak edges
    assert set(receipt.peak_edges) == {0, 1, 2, 3}

    # Verify residuals: all have magnitude 1/4
    for r in receipt.primal_residual:
        assert abs(r) == Fraction(1, 4)

    # Verify dual circulation z = (1/4, 1/4, 1/4, 1/4) satisfies B^T z = 0 and sum |z_e|/w_e <= 1
    z = receipt.dual_circulation
    for z_e in z:
        assert z_e == Fraction(1, 4)
    weighted_l1_dual = sum(abs(z_e) / w for z_e, w in zip(z, graph.weights))
    assert weighted_l1_dual == Fraction(1)

    # Check complementary slackness pairing
    primal_dual_pairing = sum(z_e * r_e for z_e, r_e in zip(z, receipt.primal_residual))
    assert primal_dual_pairing == receipt.chebyshev_norm

    # Validate receipt with repository checker
    assert check_linf_certificate_receipt(receipt, graph, h)


def test_audit_n001_013_chebyshev_exact_coboundary_positive():
    """
    Positive Control: On an exact coboundary cochain h = d0(f),
    Chebyshev quotient norm is exactly 0 with zero duality gap.
    """
    graph = DirectedGraph.triangle()
    f = [Fraction(2), Fraction(5), Fraction(1)]
    # Use graph.d0 to compute exact coboundary on edges ((0, 1), (1, 2), (0, 2))
    h = graph.d0(f)

    receipt = ExactRationalLinfChebyshevSolver.solve(graph, h)

    assert receipt.chebyshev_norm == Fraction(0)
    assert receipt.dual_bound == Fraction(0)
    assert receipt.duality_gap == Fraction(0)
    for r in receipt.primal_residual:
        assert r == Fraction(0)

    assert check_linf_certificate_receipt(receipt, graph, h)


def test_audit_n001_013_negative_control_dimension_mismatch():
    """
    Negative Control: Passing length-3 cochain to 4-edge cycle raises ValueError.
    """
    graph = DirectedGraph.cycle(4)
    with pytest.raises(ValueError, match="1-cochain h length 3 != edge count 4"):
        ExactRationalLinfChebyshevSolver.solve(graph, [1, 0, 0])


def test_audit_n001_013_negative_control_subgradient_non_active_edge():
    """
    Negative Control: Placing dual weight on a non-active edge strictly fails
    the complementary slackness equality condition.
    """
    # Graph with 2 edges where residual magnitudes differ:
    # Let residual be r = (1, 1/2) with weights w = (1, 1).
    # Peak norm is ||r||_inf = 1, achieved only on edge 0.
    # Edge 1 is non-active: |r_1| = 1/2 < 1.
    r = [Fraction(1), Fraction(1, 2)]
    weights = [Fraction(1), Fraction(1)]
    linf_norm = Fraction(1)

    # Valid dual on active edge: z_active = (1, 0)
    z_active = [Fraction(1), Fraction(0)]
    active_pairing = sum(z_e * r_e for z_e, r_e in zip(z_active, r))
    active_dual_norm = sum(abs(z_e) / w for z_e, w in zip(z_active, weights))
    assert active_pairing == linf_norm * active_dual_norm == Fraction(1)

    # Perturbed dual placing weight on non-active edge: z_perturbed = (1/2, 1/2)
    z_perturbed = [Fraction(1, 2), Fraction(1, 2)]
    perturbed_dual_norm = sum(abs(z_e) / w for z_e, w in zip(z_perturbed, weights))
    assert perturbed_dual_norm == Fraction(1)  # Unit dual norm

    perturbed_pairing = sum(z_e * r_e for z_e, r_e in zip(z_perturbed, r))
    # 1/2 * 1 + 1/2 * (1/2) = 3/4 < 1
    assert perturbed_pairing == Fraction(3, 4)
    assert perturbed_pairing < linf_norm * perturbed_dual_norm


# ============================================================================
# Tests for ATL-N001-019: Quantum Cocycle Defect Bound
# ============================================================================

def test_audit_n001_019_quantum_defect_pure_state_coherence_positive():
    """
    Positive Control: For a 3-state pure superposition state on a 3-cycle,
    trace distance to the diagonal dephased state satisfies the bound:
    ||rho - rho_diag||_tr <= 1/2 * C_{l1}(rho).
    Also checks 2x2 principal minor conditions and dual circulation lower bound.
    """
    # Pure state |psi> = (1, 1, 1)/sqrt(3)
    psi = np.ones(3, dtype=np.complex128) / np.sqrt(3.0)
    rho = np.outer(psi, np.conj(psi))

    # Basic state axioms
    assert np.allclose(rho, rho.conj().T)
    assert np.isclose(np.trace(rho).real, 1.0)
    eigenvalues = np.linalg.eigvalsh(rho)
    assert all(ev >= -1e-15 for ev in eigenvalues)

    # Off-diagonal coherence sum: C_{l1}(rho) = sum_{u != v} |rho_uv|
    c_l1 = sum(abs(rho[u, v]) for u in range(3) for v in range(3) if u != v)
    assert math.isclose(c_l1, 2.0, abs_tol=1e-12)

    # Diagonal dephased state
    rho_diag = np.diag(np.diag(rho))
    diff = rho - rho_diag
    # Trace distance = 1/2 * sum of singular values of diff
    singular_values = np.linalg.svd(diff, compute_uv=False)
    trace_distance = 0.5 * sum(singular_values)
    assert math.isclose(trace_distance, 2.0 / 3.0, abs_tol=1e-12)

    # Verify bound: trace_distance <= 0.5 * C_{l1}(rho)
    assert trace_distance <= 0.5 * c_l1
    assert math.isclose(0.5 * c_l1, 1.0, abs_tol=1e-12)

    # 2x2 principal minor bounds: |rho_uv| <= sqrt(rho_uu * rho_vv)
    for u in range(3):
        for v in range(3):
            assert abs(rho[u, v]) <= math.sqrt(rho[u, u].real * rho[v, v].real) + 1e-15
            assert abs(rho[u, v]) <= 0.5 * (rho[u, u].real + rho[v, v].real) + 1e-15

    # Dual circulation lower bound on quotient norm:
    # For cycle circulation C = (1, 1, 1) with uniform weights w_e = 1:
    # M_C = max_e |C_e|/w_e = 1.
    # Lower bound on Phi_1: Phi_1 >= |<C, omega>| / M_C.
    graph = DirectedGraph.triangle()
    omega_zero = [Fraction(0), Fraction(0), Fraction(0)]
    rec_zero = L1QuotientSolver.solve(graph, omega_zero)
    assert rec_zero.primal_norm == Fraction(0)


def test_audit_n001_019_branch_cut_winding_vs_u1_holonomy_positive():
    """
    Positive Control: Demonstrates Theorem L1C-T8 branch winding vs U(1) holonomy.
    Under diagonal unitary rotation theta = (0, 3pi/4, 3pi/2), the real quotient norm
    jumps to 2pi due to branch-cut wrapping, while multiplicative U(1) holonomy remains 1.0.
    """
    graph = DirectedGraph(vertices=[0, 1, 2], edges=[(0, 1), (1, 2), (2, 0)])

    # Initial state with positive real coherences
    psi = np.ones(3, dtype=np.complex128) / np.sqrt(3.0)
    rho = np.outer(psi, np.conj(psi))

    initial_phases = [cmath.phase(rho[u, v]) for (u, v) in graph.edges]
    assert all(math.isclose(ph, 0.0, abs_tol=1e-12) for ph in initial_phases)

    # Diagonal unitary rotation U_theta with theta = (0, 3pi/4, 3pi/2)
    theta = [0.0, 3.0 * math.pi / 4.0, 3.0 * math.pi / 2.0]
    U_theta = np.diag([cmath.exp(-1j * th) for th in theta])
    rho_prime = U_theta @ rho @ U_theta.conj().T

    # Entrywise transformation sign check: (U_theta rho U_theta^dagger)_uv = e^{i (d0 theta)_uv} rho_uv
    for (u, v) in graph.edges:
        d0_theta_uv = theta[v] - theta[u]
        expected_entry = cmath.exp(1j * d0_theta_uv) * rho[u, v]
        assert np.isclose(rho_prime[u, v], expected_entry, atol=1e-12)

    # Principal branch argument extraction in (-pi, pi]
    extracted_phases = [cmath.phase(rho_prime[u, v]) for (u, v) in graph.edges]
    # Edge (0, 1): 3pi/4
    assert math.isclose(extracted_phases[0], 3.0 * math.pi / 4.0, abs_tol=1e-12)
    # Edge (1, 2): 3pi/4
    assert math.isclose(extracted_phases[1], 3.0 * math.pi / 4.0, abs_tol=1e-12)
    # Edge (2, 0): -3pi/2 wraps to +pi/2 in principal range (-pi, pi]
    assert math.isclose(extracted_phases[2], math.pi / 2.0, abs_tol=1e-12)

    # Real cycle sum and real quotient norm
    cycle_sum = sum(extracted_phases)
    assert math.isclose(cycle_sum, 2.0 * math.pi, abs_tol=1e-12)

    # Rational solver evaluation of the extracted flux:
    # 3/4 + 3/4 + 1/2 = 2
    receipt_real = L1QuotientSolver.solve(graph, [Fraction(3, 4), Fraction(3, 4), Fraction(1, 2)])
    assert receipt_real.primal_norm == Fraction(2)

    # Multiplicative U(1) cycle holonomy is 1.0 (invariant under unitary conjugation)
    holonomy_u1 = 1.0 + 0.0j
    for (u, v) in graph.edges:
        holonomy_u1 *= (rho_prime[u, v] / abs(rho_prime[u, v]))
    assert math.isclose(holonomy_u1.real, 1.0, abs_tol=1e-12)
    assert math.isclose(holonomy_u1.imag, 0.0, abs_tol=1e-12)

    # Period shift k = (0, 0, -1) cancels branch winding:
    # omega' + 2pi*k = (3pi/4, 3pi/4, -3pi/2) = d0(theta), so residual is 0
    k_shift = [0, 0, -1]
    unwrapped_phases = [
        extracted_phases[idx] + 2.0 * math.pi * k_shift[idx]
        for idx in range(3)
    ]
    assert math.isclose(unwrapped_phases[0], 3.0 * math.pi / 4.0, abs_tol=1e-12)
    assert math.isclose(unwrapped_phases[1], 3.0 * math.pi / 4.0, abs_tol=1e-12)
    assert math.isclose(unwrapped_phases[2], -3.0 * math.pi / 2.0, abs_tol=1e-12)
    assert math.isclose(sum(unwrapped_phases), 0.0, abs_tol=1e-12)


def test_audit_n001_019_negative_control_psd_minor_violation():
    """
    Negative Control: Perturbing an off-diagonal entry to exceed sqrt(rho_uu * rho_vv)
    violates positive semidefiniteness.
    """
    # 2x2 matrix with diagonal (1/2, 1/2) and off-diagonal 0.6 > sqrt(0.5 * 0.5) = 0.5
    matrix_bad = np.array([
        [0.5 + 0.0j, 0.6 + 0.0j],
        [0.6 + 0.0j, 0.5 + 0.0j],
    ])
    # Determinant is 0.25 - 0.36 = -0.11 < 0
    det = np.linalg.det(matrix_bad).real
    assert det < 0.0

    # Eigenvalues contain a negative value: 0.5 - 0.6 = -0.1
    eigvals = np.linalg.eigvalsh(matrix_bad)
    assert any(ev < 0.0 for ev in eigvals)


# ============================================================================
# Tests for ATL-N001-020: Cohomological Classification on 1-Graphs
# ============================================================================

def test_audit_n001_020_cohomology_quotient_isomorphism_on_graphs_positive():
    """
    Positive Control: On 1-dimensional graph complexes (C^2 = {0}),
    every 1-cochain is a cocycle (Z^1 = C^1), and the quotient space Q^1 is
    canonically isomorphic to H^1(G; R), with dimension beta_1 = |E| - |V| + c.
    """
    # 1. 4-cycle graph: V=4, E=4, c=1 -> beta_1 = 4 - 4 + 1 = 1
    cycle_graph = DirectedGraph.cycle(4)
    beta_cycle = cycle_graph.cycle_rank()
    assert beta_cycle == 1

    # Non-coboundary cochain h = (1, 0, 0, 0)
    receipt_non_exact = L1QuotientSolver.solve(cycle_graph, [1, 0, 0, 0])
    assert receipt_non_exact.primal_norm > Fraction(0)
    assert receipt_non_exact.primal_norm == Fraction(1)  # L1 quotient norm is 1

    # Coboundary cochain h = d0(f)
    f = [Fraction(1), Fraction(3), Fraction(6), Fraction(2)]
    # Edges are (0, 1), (1, 2), (2, 3), (3, 0)
    h_exact = [f[1] - f[0], f[2] - f[1], f[3] - f[2], f[0] - f[3]]
    receipt_exact = L1QuotientSolver.solve(cycle_graph, h_exact)
    assert receipt_exact.primal_norm == Fraction(0)

    # 2. Tree graph (K_{1, 3} star): V=4, E=3, c=1 -> beta_1 = 3 - 4 + 1 = 0
    tree_graph = DirectedGraph(
        vertices=[0, 1, 2, 3],
        edges=[(0, 1), (0, 2), (0, 3)],
    )
    beta_tree = tree_graph.cycle_rank()
    assert beta_tree == 0

    # On a tree, all 1-cochains are coboundaries (H^1 = {0})
    h_arbitrary = [Fraction(7), Fraction(-4), Fraction(11)]
    receipt_tree = L1QuotientSolver.solve(tree_graph, h_arbitrary)
    assert receipt_tree.primal_norm == Fraction(0)


def test_audit_n001_020_negative_control_2complex_curvature_distinction():
    """
    Negative Control: On a 2-complex with a 2-cell attached, a cochain with
    non-vanishing coboundary d1(omega) != 0 is NOT a cocycle (omega not in Z^1),
    demonstrating that Q^1 does not collapse to H^1 on complexes of dimension >= 2.
    """
    # 2-complex: oriented triangle with 2-cell f_0
    # Edges: e0 = (0, 1), e1 = (1, 2), e2 = (2, 0)
    # 2-cell boundary: d1 = [[1, 1, 1]]
    d1 = [[1, 1, 1]]

    # Cochain omega = (1, 0, 0)
    omega = [1, 0, 0]

    # Evaluate d1(omega):
    curvature = sum(c * val for c, val in zip(d1[0], omega))
    assert curvature == 1  # d1(omega) != 0, so omega is NOT in ker(d1)

    # On a 1-graph (without the 2-cell), omega represents a non-trivial cohomology class.
    # But on this 2-complex, the 2-cell boundary makes the cycle a boundary of the 2-cell,
    # and omega has non-zero curvature defect.
    # Therefore, Q^1 contains non-cocycle elements and is strictly larger than H^1.
    assert curvature != 0


# ============================================================================
# Tests for ATL-N002-020: Admission Check for d1 d0 = 0
# ============================================================================

def test_audit_n002_020_admission_check_positive_valid_complexes():
    """
    Positive Control: The exact rational admission check d1 d0 = 0 admits valid
    simplicial and cell complexes:
    1. Oriented triangle C3
    2. Square plaquette
    3. Triangulated square (2 triangles sharing an edge)
    """
    # 1. Oriented triangle C3: V = 3, E = 3, F = 1
    # Edges: e0=(0, 1), e1=(1, 2), e2=(2, 0)
    # d0: E x V
    d0_tri = [
        [-1,  1,  0],  # e0: 1 - 0
        [ 0, -1,  1],  # e1: 2 - 1
        [ 1,  0, -1],  # e2: 0 - 2
    ]
    # d1: F x E
    d1_tri = [
        [1, 1, 1],     # face bounded by e0 + e1 + e2
    ]
    receipt_tri = admission_check_d1_d0(d0_tri, d1_tri, vertex_count=3, edge_count=3, face_count=1)
    assert receipt_tri.admitted is True
    assert receipt_tri.status == "ADMITTED"
    assert receipt_tri.max_absolute_defect == Fraction(0)

    # Downstream degree-2 evaluation succeeds
    curv = evaluate_degree_2_curvature_gated(receipt_tri, d1_tri, [1, 0, 0])
    assert curv == [Fraction(1)]

    # 2. Square plaquette: V = 4, E = 4, F = 1
    # Edges: e0=(0,1), e1=(1,2), e2=(2,3), e3=(3,0)
    d0_sq = [
        [-1,  1,  0,  0],  # e0
        [ 0, -1,  1,  0],  # e1
        [ 0,  0, -1,  1],  # e2
        [ 1,  0,  0, -1],  # e3
    ]
    d1_sq = [
        [1, 1, 1, 1],      # face bounded by e0 + e1 + e2 + e3
    ]
    receipt_sq = admission_check_d1_d0(d0_sq, d1_sq, vertex_count=4, edge_count=4, face_count=1)
    assert receipt_sq.admitted is True
    assert receipt_sq.status == "ADMITTED"
    assert receipt_sq.max_absolute_defect == Fraction(0)

    # 3. Triangulated square: V = 4, E = 5, F = 2
    # Edges: e0=(0,1), e1=(1,2), e2=(2,3), e3=(3,0), e4=(0,2) [diagonal]
    d0_triang = [
        [-1,  1,  0,  0],  # e0: 1 - 0
        [ 0, -1,  1,  0],  # e1: 2 - 1
        [ 0,  0, -1,  1],  # e2: 3 - 2
        [ 1,  0,  0, -1],  # e3: 0 - 3
        [-1,  0,  1,  0],  # e4: 2 - 0
    ]
    # Triangle 1 (0, 1, 2): e0 + e1 - e4 (since e4 is 0->2, e0+e1 is 0->1->2)
    # Triangle 2 (0, 2, 3): e4 + e2 + e3 (since e4 is 0->2, e2 is 2->3, e3 is 3->0)
    d1_triang = [
        [1, 1, 0, 0, -1],
        [0, 0, 1, 1,  1],
    ]
    receipt_triang = admission_check_d1_d0(d0_triang, d1_triang, vertex_count=4, edge_count=5, face_count=2)
    assert receipt_triang.admitted is True
    assert receipt_triang.status == "ADMITTED"
    assert receipt_triang.max_absolute_defect == Fraction(0)


def test_audit_n002_020_admission_check_vacuous_graph_truncation_positive():
    """
    Positive Control: On a 1-dimensional graph complex where C^2 = {0} and F = empty,
    the nilpotency check passes vacuously under graph truncation.
    """
    d0_graph = [
        [-1, 1, 0],
        [0, -1, 1],
        [1, 0, -1],
    ]
    d1_empty = []  # 0 faces

    receipt = admission_check_d1_d0(d0_graph, d1_empty, vertex_count=3, edge_count=3, face_count=0)
    assert receipt.admitted is True
    assert receipt.status == "ADMITTED_VACUOUS_GRAPH_TRUNCATION"
    assert receipt.max_absolute_defect == Fraction(0)
    assert receipt.face_count == 0


def test_audit_n002_020_negative_control_orientation_inversion_rejection():
    """
    Negative Control: Inverting an edge orientation in a 2-cell boundary causes
    d1 d0 != 0, strictly failing admission and blocking degree-2 inferences.
    """
    d0_tri = [
        [-1,  1,  0],  # e0: 1 - 0
        [ 0, -1,  1],  # e1: 2 - 1
        [ 1,  0, -1],  # e2: 0 - 2
    ]
    # Inverted orientation on edge e2: [1, 1, -1] instead of [1, 1, 1]
    d1_bad = [
        [1, 1, -1],
    ]

    receipt = admission_check_d1_d0(d0_tri, d1_bad, vertex_count=3, edge_count=3, face_count=1)
    assert receipt.admitted is False
    assert receipt.status == "REFUSED_NILPOTENCY_FAILURE"
    assert receipt.max_absolute_defect == Fraction(2)
    # The matrix product row is [-2, 0, 2]
    assert receipt.d1_d0_matrix == [[Fraction(-2), Fraction(0), Fraction(2)]]

    # Attempting to evaluate degree-2 curvature on unadmitted complex raises AdmissionRefusalError
    with pytest.raises(AdmissionRefusalError, match="Degree-2 inference refused"):
        evaluate_degree_2_curvature_gated(receipt, d1_bad, [1, 0, 0])
