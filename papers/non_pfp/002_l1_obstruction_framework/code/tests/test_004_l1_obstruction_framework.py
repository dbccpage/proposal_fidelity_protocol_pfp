"""Comprehensive test suite for L1 Obstruction Framework (Paper 037).

Covers:
1. Exact Rational Moore-Penrose Graph Laplacian (p = 2):
   - C_4, C_6, weighted triangle.
   - B^T W h_harm == 0 divergence-free check.
   - Exact rational squared norm and orthogonality <d0 f, W h_harm> == 0.
   - Hodge inflation factor on C_n approaching (3n-2)/n -> 3.
2. Exact Rational Chebyshev LP (p = inf):
   - C_4 single defect: Chebyshev norm 1/4.
   - Dual circulation z with B^T z = 0 and sum |z_e|/w_e <= 1.
   - Zero duality gap Delta == 0 over fractions.Fraction.
   - Peak edge detection and exact zero-defect repair.
3. High-Precision Continuous p in (1, inf):
   - IRLS and Proximal Bregman with Armijo line search.
   - Certified duality gap Delta <= 10^-12 for p in {1.25, 1.5, 2.0, 2.5, 3.0, 4.0}.
   - Divergence norm of dual circulation <= 10^-13.
4. Operator-Valued Schatten-p Module:
   - Matrix coboundaries d0 F.
   - Schatten-1 (trace), Schatten-2 (Frobenius), Schatten-inf (spectral).
   - Non-commutative Holder inequality and exact polar dual attainment.
   - Kadison unitary gauge invariance under U(d) rotations.
   - Zero matrix polar dual edge case.
5. Finite certificate comparison:
   - LocalPrimalDualIterator.certificate_dominates on a supplied KKT witness.
   - pushforward_cochain on one finite edge map. That call is not Theorem 2.1.
6. Adversarial & Refusal Contracts:
   - Zero-weight refusal (ZeroWeightRefusalError).
   - Negative-weight refusal (NegativeWeightError).
   - Cochain / potential dimension mismatches (CochainDimensionError, ValueError).
   - Topological defects (SelfLoopError, DuplicateEdgeError, TopologyIntegrityError).
   - Simplex solver edge cases (unbounded, empty constraints).
   - Continuous Lp invalid exponent refusals (p <= 1.0, math.isinf(p)).
7. Legacy Evaluator Verification:
   - PaperEvaluator backward-compatibility check.
"""

from __future__ import annotations

import math
from fractions import Fraction

import numpy as np
import pytest
from mod_004_l1_obstruction_framework_core import (
    CochainDimensionError,
    DirectedGraph,
    DuplicateEdgeError,
    ExactRationalL2LaplacianSolver,
    ExactRationalLinfChebyshevSolver,
    ExactTwoPhaseSimplexSolver,
    FunctorialAggregation,
    HighPrecisionLpConvexSolver,
    LocalPrimalDualIterator,
    NegativeWeightError,
    OperatorSchattenPModule,
    PaperEvaluator,
    SelfLoopError,
    SolverInfeasibleError,
    SolverUnboundedError,
    TopologyIntegrityError,
    ZeroWeightRefusalError,
)

# ============================================================================
# 0. Legacy Backward Compatibility Tests
# ============================================================================

def test_paper_evaluator_passes():
    """Verify PaperEvaluator returns expected pass receipt."""
    evaluator = PaperEvaluator()
    res = evaluator.evaluate()
    assert res["paper_id"] == "004_l1_obstruction_framework"
    assert res["status"] == "EVALUATED_PASS"
    assert res["authority"] == "None"


# ============================================================================
# 1. Exact Rational L2 Graph Laplacian Tests
# ============================================================================

def test_l2_laplacian_cycle_c4():
    """Verify exact rational L2 Laplacian projection on C_4."""
    graph = DirectedGraph.cycle(4)
    h = [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
    receipt = ExactRationalL2LaplacianSolver.solve(graph, h)

    assert receipt.is_exact_norm is True
    assert receipt.squared_norm == Fraction(1, 4)
    assert receipt.norm_value == Fraction(1, 2)
    assert receipt.harmonic_residual == (Fraction(1, 4), Fraction(1, 4), Fraction(1, 4), Fraction(1, 4))
    assert all(d == Fraction(0) for d in receipt.divergence)
    assert receipt.orthogonality_verified is True
    assert receipt.status == "OPTIMAL_L2"


def test_l2_laplacian_weighted_triangle():
    """Verify exact rational L2 Laplacian projection on weighted triangle."""
    graph = DirectedGraph.triangle(weights=[Fraction(2), Fraction(3), Fraction(6)])
    h = [Fraction(1), Fraction(2), Fraction(0)]
    receipt = ExactRationalL2LaplacianSolver.solve(graph, h)

    assert all(d == Fraction(0) for d in receipt.divergence)
    assert receipt.orthogonality_verified is True
    assert receipt.squared_norm >= Fraction(0)


def test_package_exports():
    """Verify code package __all__ matches exports."""
    import mod_004_l1_obstruction_framework_core as core

    assert hasattr(core, "PaperEvaluator")
    assert hasattr(core, "ExactRationalL2LaplacianSolver")
    assert hasattr(core, "ExactRationalLinfChebyshevSolver")
    assert hasattr(core, "HighPrecisionLpConvexSolver")
    assert hasattr(core, "OperatorSchattenPModule")
    assert len(core.__all__) > 0


def test_l2_laplacian_irrational_norm():
    """Verify non-perfect square norm branches to float norm_value."""
    # On C_3 with weights (1,1,1) and h=(1,0,0), h_harm = (1/3, 1/3, 1/3)
    # squared_norm = 3 * (1/9) = 1/3, which is not a rational square.
    graph = DirectedGraph.cycle(3)
    receipt = ExactRationalL2LaplacianSolver.solve(graph, [Fraction(1), Fraction(0), Fraction(0)])
    assert receipt.squared_norm == Fraction(1, 3)
    assert receipt.is_exact_norm is False
    assert abs(receipt.norm_value - 1.0 / math.sqrt(3.0)) < 1e-12


def test_l2_laplacian_dimension_mismatch():
    """Verify L2 solver rejects 1-cochain of wrong dimension."""
    graph = DirectedGraph.cycle(4)
    with pytest.raises(ValueError, match="1-cochain h length"):
        ExactRationalL2LaplacianSolver.solve(graph, [Fraction(1), Fraction(0)])


def test_l2_vs_l1_hodge_inflation_limit():
    """Verify that L1 cost of L2 Hodge components on cycle graph approaches (3n-2)/n -> 3."""
    for n in [3, 4, 10, 50, 100]:
        graph = DirectedGraph.cycle(n)
        h = [Fraction(1)] + [Fraction(0)] * (n - 1)
        receipt = ExactRationalL2LaplacianSolver.solve(graph, h)

        # L1 norm of harmonic component: n * (1/n) = 1
        l1_harm = sum(abs(x) for x in receipt.harmonic_residual)
        assert l1_harm == Fraction(1)

        # Coboundary component d0 f = h - h_harm
        d0_f = [h[i] - receipt.harmonic_residual[i] for i in range(n)]
        l1_coboundary = sum(abs(x) for x in d0_f)
        total_l1 = l1_harm + l1_coboundary

        expected_ratio = Fraction(3 * n - 2, n)
        assert total_l1 == expected_ratio


# ============================================================================
# 2. Exact Rational Linf Chebyshev Tests
# ============================================================================

def test_linf_chebyshev_cycle_c4():
    """Verify exact rational Linf Chebyshev quotient norm on C_4."""
    graph = DirectedGraph.cycle(4)
    h = [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
    receipt = ExactRationalLinfChebyshevSolver.solve(graph, h)

    assert receipt.chebyshev_norm == Fraction(1, 4)
    assert receipt.duality_gap == Fraction(0)
    assert receipt.dual_bound == Fraction(1, 4)
    assert len(receipt.peak_edges) == 4
    assert receipt.primal_residual == (Fraction(1, 4), Fraction(1, 4), Fraction(1, 4), Fraction(1, 4))
    assert receipt.status == "OPTIMAL_LINF"


def test_linf_chebyshev_with_gauge_vertex():
    """Verify Chebyshev solver with explicit gauge vertex selection."""
    graph = DirectedGraph.cycle(4)
    h = [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
    receipt = ExactRationalLinfChebyshevSolver.solve(graph, h, gauge_vertex=2)
    assert receipt.chebyshev_norm == Fraction(1, 4)
    assert receipt.duality_gap == Fraction(0)


def test_linf_chebyshev_zero_defect():
    """Verify exact repair (norm = 0) for exact coboundaries in Linf."""
    graph = DirectedGraph.triangle()
    f = [Fraction(2), Fraction(5), Fraction(1)]
    d0_f = graph.d0(f)
    receipt = ExactRationalLinfChebyshevSolver.solve(graph, d0_f)

    assert receipt.chebyshev_norm == Fraction(0)
    assert receipt.duality_gap == Fraction(0)
    assert all(r == Fraction(0) for r in receipt.primal_residual)


def test_linf_chebyshev_dimension_mismatch():
    """Verify Linf solver rejects 1-cochain of wrong dimension."""
    graph = DirectedGraph.cycle(4)
    with pytest.raises(ValueError, match="1-cochain h length"):
        ExactRationalLinfChebyshevSolver.solve(graph, [Fraction(1)])


# ============================================================================
# 3. High-Precision Continuous Lp Solvers Tests
# ============================================================================

@pytest.mark.parametrize("p_val", [1.25, 1.5, 2.0, 2.5, 3.0, 4.0])
def test_continuous_lp_irls_duality_gap(p_val: float):
    """Verify IRLS satisfies certified duality gap Delta <= 10^-12."""
    graph = DirectedGraph.cycle(4)
    h = [1.0, 0.0, 0.0, 0.0]
    receipt = HighPrecisionLpConvexSolver.solve_irls(graph, h, p=p_val)

    assert receipt.numerical_checks_passed is True
    assert receipt.duality_gap <= 1e-12
    assert receipt.divergence_norm <= 1e-13
    assert receipt.solver_method == "IRLS_Adaptive_Armijo"
    assert receipt.p == p_val


@pytest.mark.parametrize("p_val", [1.5, 2.0, 3.0])
def test_continuous_lp_bregman_duality_gap(p_val: float):
    """Verify Proximal Bregman satisfies certified duality gap Delta <= 10^-12."""
    graph = DirectedGraph.cycle(4)
    h = [1.0, 0.0, 0.0, 0.0]
    receipt = HighPrecisionLpConvexSolver.solve_bregman(graph, h, p=p_val, max_iter=800, lr=0.1)

    assert receipt.numerical_checks_passed is True
    assert receipt.duality_gap <= 1e-12
    assert receipt.divergence_norm <= 1e-13
    assert receipt.solver_method == "Proximal_Bregman_Nesterov"


def test_continuous_lp_refusals():
    """Verify continuous Lp solver rejects p <= 1.0, p = inf, and cochain mismatch."""
    graph = DirectedGraph.cycle(4)
    h = [1.0, 0.0, 0.0, 0.0]

    with pytest.raises(ValueError, match="Continuous Lp solver requires 1 < p < inf"):
        HighPrecisionLpConvexSolver.solve_irls(graph, h, p=1.0)

    with pytest.raises(ValueError, match="Continuous Lp solver requires 1 < p < inf"):
        HighPrecisionLpConvexSolver.solve_irls(graph, h, p=float('inf'))

    with pytest.raises(ValueError, match="Continuous Lp solver requires 1 < p < inf"):
        HighPrecisionLpConvexSolver.solve_bregman(graph, h, p=0.5)

    with pytest.raises(ValueError, match="1-cochain h length"):
        HighPrecisionLpConvexSolver.solve_irls(graph, [1.0, 0.0], p=2.0)

    with pytest.raises(ValueError, match="1-cochain h length"):
        HighPrecisionLpConvexSolver.solve_bregman(graph, [1.0, 0.0], p=2.0)


# ============================================================================
# 4. Operator-Valued Schatten-p Module Tests
# ============================================================================

def test_schatten_norms_known_matrices():
    """Verify Schatten-1, 2, and inf match Trace, Frobenius, and Spectral norms."""
    np.random.seed(101)
    A = np.random.randn(4, 4) + 1j * np.random.randn(4, 4)

    s1 = OperatorSchattenPModule.schatten_norm(A, 1.0)
    s2 = OperatorSchattenPModule.schatten_norm(A, 2.0)
    sinf = OperatorSchattenPModule.schatten_norm(A, float('inf'))

    assert abs(s2 - np.linalg.norm(A, 'fro')) < 1e-12
    assert abs(sinf - np.linalg.norm(A, 2)) < 1e-12
    assert s1 >= s2 >= sinf


def test_schatten_holder_duality_and_polar_attainment():
    """Verify non-commutative Holder inequality and exact polar witness attainment."""
    np.random.seed(202)
    d = 3
    A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    B = np.random.randn(d, d) + 1j * np.random.randn(d, d)

    p = 3.5
    q = p / (p - 1.0)

    # 1. Inequality check
    tr_AB = abs(np.trace(A.conj().T @ B))
    holder_bound = OperatorSchattenPModule.schatten_norm(A, p) * OperatorSchattenPModule.schatten_norm(B, q)
    assert tr_AB <= holder_bound + 1e-12

    # 2. Polar witness attainment
    B_opt = OperatorSchattenPModule.polar_dual_maximizer(A, p)
    assert abs(OperatorSchattenPModule.schatten_norm(B_opt, q) - 1.0) < 1e-12
    tr_opt = abs(np.trace(A.conj().T @ B_opt))
    norm_A_p = OperatorSchattenPModule.schatten_norm(A, p)
    assert abs(tr_opt - norm_A_p) < 1e-12


def test_schatten_polar_dual_zero_matrix():
    """Verify polar dual maximizer of zero matrix returns zero matrix."""
    Z = np.zeros((3, 3), dtype=np.complex128)
    B = OperatorSchattenPModule.polar_dual_maximizer(Z, 2.0)
    assert np.all(B == 0.0)


def test_schatten_kadison_unitary_invariance():
    """Verify Kadison unitary gauge invariance under U(d) gauge transformations."""
    np.random.seed(303)
    d = 3
    A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    Q1, _ = np.linalg.qr(np.random.randn(d, d) + 1j * np.random.randn(d, d))
    Q2, _ = np.linalg.qr(np.random.randn(d, d) + 1j * np.random.randn(d, d))

    assert OperatorSchattenPModule.verify_kadison_unitary_invariance(A, Q1, Q2) is True


def test_operator_coboundary_evaluation():
    """Verify operator coboundary d0 F on DirectedGraph."""
    graph = DirectedGraph.triangle()
    F = [
        np.array([[1.0, 0.0], [0.0, 1.0]]),
        np.array([[0.0, 1.0], [1.0, 0.0]]),
        np.array([[2.0, 0.0], [0.0, -1.0]]),
    ]
    d0_F = OperatorSchattenPModule.operator_coboundary_d0(graph, F)
    assert len(d0_F) == 3
    np.testing.assert_allclose(d0_F[0], F[1] - F[0])
    np.testing.assert_allclose(d0_F[1], F[2] - F[1])
    np.testing.assert_allclose(d0_F[2], F[2] - F[0])


def test_operator_total_schatten_p_norm():
    """Verify total weighted Schatten-p norm over graph cochains."""
    graph = DirectedGraph.triangle(weights=[Fraction(1), Fraction(2), Fraction(3)])
    H = [
        np.eye(2, dtype=np.complex128),
        np.eye(2, dtype=np.complex128) * 2.0,
        np.eye(2, dtype=np.complex128) * 3.0,
    ]
    # For p = 1: ||H[0]||_{S_1} = 2, ||H[1]||_{S_1} = 4, ||H[2]||_{S_1} = 6
    # Total = 1*2 + 2*4 + 3*6 = 2 + 8 + 18 = 28
    tot_1 = OperatorSchattenPModule.total_schatten_p_norm(graph, H, 1.0)
    assert abs(tot_1 - 28.0) < 1e-12

    # For p = inf: max(1 * 1, 2 * 2, 3 * 3) = 9
    tot_inf = OperatorSchattenPModule.total_schatten_p_norm(graph, H, float('inf'))
    assert abs(tot_inf - 9.0) < 1e-12


def test_operator_dimension_mismatches():
    """Verify operator module rejects cochains of wrong dimensions."""
    graph = DirectedGraph.triangle()
    with pytest.raises(ValueError, match="0-cochain length"):
        OperatorSchattenPModule.operator_coboundary_d0(graph, [np.eye(2)])

    with pytest.raises(ValueError, match="1-cochain length"):
        OperatorSchattenPModule.total_schatten_p_norm(graph, [np.eye(2)], 2.0)


# ============================================================================
# 5. Paper 037 KKT Fixed-Point & Functorial Aggregation Tests
# ============================================================================

def test_kkt_fixed_point_verification():
    """A supplied circulation, capacity, and slackness witness is accepted."""
    graph = DirectedGraph.cycle(4)
    h = [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
    f = [Fraction(0), Fraction(0), Fraction(0), Fraction(0)]
    z = [Fraction(1), Fraction(1), Fraction(1), Fraction(1)]

    # (f, z) is a KKT fixed point
    assert LocalPrimalDualIterator.is_kkt_fixed_point(graph, h, f, z) is True

    # Corrupted dual (non-circulation) fails
    z_bad = [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
    assert LocalPrimalDualIterator.is_kkt_fixed_point(graph, h, f, z_bad) is False

    # Capacity violation fails
    z_over = [Fraction(2), Fraction(2), Fraction(2), Fraction(2)]
    assert LocalPrimalDualIterator.is_kkt_fixed_point(graph, h, f, z_over) is False

    # Complementary slackness violation fails
    z_cs_bad = [Fraction(1, 2), Fraction(1, 2), Fraction(1, 2), Fraction(1, 2)]
    assert LocalPrimalDualIterator.is_kkt_fixed_point(graph, h, f, z_cs_bad) is False

    # Negative residual complementary slackness check
    h_neg = [Fraction(-1), Fraction(0), Fraction(0), Fraction(0)]
    z_neg = [Fraction(-1), Fraction(-1), Fraction(-1), Fraction(-1)]
    assert LocalPrimalDualIterator.is_kkt_fixed_point(graph, h_neg, f, z_neg) is True

    z_neg_bad = [Fraction(1), Fraction(-1), Fraction(-1), Fraction(-1)]
    assert LocalPrimalDualIterator.is_kkt_fixed_point(graph, h_neg, f, z_neg_bad) is False


def test_certificate_dominates_on_cycle():
    """The shipped checker compares a KKT residual with another potential."""
    graph = DirectedGraph.cycle(4)
    h = [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
    f = [Fraction(0), Fraction(0), Fraction(0), Fraction(0)]
    z = [Fraction(1), Fraction(1), Fraction(1), Fraction(1)]
    f_alt = [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
    assert LocalPrimalDualIterator.certificate_dominates(graph, h, f, z, f_alt) is True
    assert LocalPrimalDualIterator.certificate_dominates(graph, h, f, z, f) is True

    z_bad = [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
    assert LocalPrimalDualIterator.certificate_dominates(graph, h, f, z_bad, f_alt) is False
    assert LocalPrimalDualIterator.certificate_dominates(graph, h, f, z, [Fraction(0), Fraction(0)]) is False


def test_functorial_aggregation_monotonicity():
    """pushforward_cochain on one finite map. Not a proof of Theorem 2.1."""
    src_edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    tgt_edges = [('V0', 'V1'), ('V1', 'V0')]
    vertex_map = {0: 'V0', 2: 'V0', 1: 'V1', 3: 'V1'}
    edge_map = {
        (0, 1): ('V0', 'V1'),
        (1, 2): ('V1', 'V0'),
        (2, 3): ('V0', 'V1'),
        (3, 0): ('V1', 'V0'),
    }

    # Case 1: Cancellation
    omega_cancelling = [Fraction(1), Fraction(0), Fraction(-1), Fraction(0)]
    push_cancelling = FunctorialAggregation.pushforward_cochain(
        vertex_map, edge_map, tgt_edges, omega_cancelling, src_edges
    )
    norm_src = sum(abs(x) for x in omega_cancelling)
    norm_tgt = sum(abs(x) for x in push_cancelling)
    assert norm_tgt <= norm_src
    assert norm_tgt == Fraction(0)
    assert norm_src == Fraction(2)

    # Case 2: Invariant norm
    omega_same = [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
    push_same = FunctorialAggregation.pushforward_cochain(
        vertex_map, edge_map, tgt_edges, omega_same, src_edges
    )
    assert sum(abs(x) for x in push_same) <= sum(abs(x) for x in omega_same)


# ============================================================================
# 6. Adversarial Tests: Weights, Topology & Dimensions
# ============================================================================

def test_zero_weight_refusal():
    """Verify ZeroWeightRefusalError when edge weight is zero."""
    with pytest.raises(ZeroWeightRefusalError):
        DirectedGraph.cycle(4, weights=[Fraction(1), Fraction(0), Fraction(1), Fraction(1)])


def test_negative_weight_refusal():
    """Verify NegativeWeightError when edge weight is negative."""
    with pytest.raises(NegativeWeightError):
        DirectedGraph.triangle(weights=[Fraction(1), Fraction(-2), Fraction(1)])


def test_weights_dimension_mismatch():
    """Verify CochainDimensionError when weights length != edge count."""
    with pytest.raises(CochainDimensionError):
        DirectedGraph.cycle(4, weights=[Fraction(1), Fraction(1)])


def test_topology_duplicate_vertex():
    """Verify TopologyIntegrityError on duplicate vertex declaration."""
    with pytest.raises(TopologyIntegrityError):
        DirectedGraph([0, 1, 0], [(0, 1)])


def test_topology_duplicate_edge():
    """Verify DuplicateEdgeError on duplicate edge declaration unless allowed."""
    with pytest.raises(DuplicateEdgeError):
        DirectedGraph([0, 1], [(0, 1), (0, 1)])

    # Allowed when allow_parallel_edges=True
    g_par = DirectedGraph([0, 1], [(0, 1), (0, 1)], allow_parallel_edges=True)
    assert len(g_par.edges) == 2



def test_topology_self_loop():
    """Verify SelfLoopError on self-loop edge."""
    with pytest.raises(SelfLoopError):
        DirectedGraph([0, 1], [(0, 0)])


def test_topology_missing_endpoint():
    """Verify TopologyIntegrityError on undeclared edge endpoint."""
    with pytest.raises(TopologyIntegrityError):
        DirectedGraph([0, 1], [(0, 2)])
    with pytest.raises(TopologyIntegrityError):
        DirectedGraph([0, 1], [(2, 0)])


def test_graph_factory_validation():
    """Verify graph factory minimum vertex constraints."""
    with pytest.raises(TopologyIntegrityError):
        DirectedGraph.cycle(2)
    with pytest.raises(TopologyIntegrityError):
        DirectedGraph.path(0)
    with pytest.raises(TopologyIntegrityError):
        DirectedGraph.complete(1)


def test_graph_connectivity_and_cycle_rank():
    """Verify connected components, connectivity, and Betti number computation."""
    g_empty = DirectedGraph([], [])
    assert g_empty.is_connected() is True

    g_path = DirectedGraph.path(4)
    assert g_path.is_connected() is True
    assert g_path.cycle_rank() == 0

    g_cycle = DirectedGraph.cycle(4)
    assert g_cycle.cycle_rank() == 1

    g_disc = DirectedGraph([0, 1, 2, 3], [(0, 1), (2, 3)])
    assert g_disc.is_connected() is False
    assert len(g_disc.connected_components()) == 2


def test_cochain_dimension_errors():
    """Verify dimension mismatch errors on d0 and d0_star."""
    graph = DirectedGraph.triangle()
    with pytest.raises(CochainDimensionError):
        graph.d0([Fraction(1), Fraction(0)])
    with pytest.raises(CochainDimensionError):
        graph.d0_star([Fraction(1)])


def test_simplex_solver_edge_cases():
    """Verify Two-Phase Simplex handling of edge cases."""
    # Empty constraints, non-negative objective
    res = ExactTwoPhaseSimplexSolver.solve_standard_lp([Fraction(1), Fraction(2)], [], [])
    assert res.status == "OPTIMAL"
    assert res.objective_value == Fraction(0)

    # Empty constraints, negative objective -> unbounded
    with pytest.raises(SolverUnboundedError):
        ExactTwoPhaseSimplexSolver.solve_standard_lp([Fraction(-1)], [], [])

    # Unbounded LP
    # min -x1 s.t. x1 - x2 = 0, x >= 0 -> unbounded
    with pytest.raises(SolverUnboundedError):
        ExactTwoPhaseSimplexSolver.solve_standard_lp(
            [Fraction(-1), Fraction(0)],
            [[Fraction(1), Fraction(-1)]],
            [Fraction(0)]
        )

    # Infeasible LP: x1 + x2 = -1 (after negation: -x1 - x2 = 1, infeasible for x >= 0)
    with pytest.raises(SolverInfeasibleError):
        ExactTwoPhaseSimplexSolver.solve_standard_lp(
            [Fraction(1), Fraction(1)],
            [[Fraction(1), Fraction(1)]],
            [Fraction(-1)]
        )



def test_review_disconnected_l2_has_componentwise_zero_mean():
    graph = DirectedGraph([0,1,2,3], [(0,1),(2,3)])
    receipt = ExactRationalL2LaplacianSolver.solve(graph, [1,1])
    assert receipt.squared_norm == 0
    assert sum(receipt.primal_potential[:2]) == 0
    assert sum(receipt.primal_potential[2:]) == 0


def test_review_rectangular_polar_witness():
    import numpy as np
    for shape in [(2,3),(3,2)]:
        matrix = np.arange(1,7,dtype=float).reshape(shape)
        dual = OperatorSchattenPModule.polar_dual_maximizer(matrix,2.0)
        assert dual.shape == shape
        assert np.isclose(OperatorSchattenPModule.schatten_norm(dual,2.0),1.0)
        assert np.isclose(np.vdot(matrix,dual),OperatorSchattenPModule.schatten_norm(matrix,2.0))


def test_review_numeric_lp_is_never_an_exact_certificate():
    receipt = HighPrecisionLpConvexSolver.solve_irls(DirectedGraph.triangle(), [1,1,1], 2.0)
    assert receipt.numerical_checks_passed
    assert not receipt.is_certified
    import pytest
    for p in [float("nan"),1.0,float("inf")]:
        with pytest.raises(ValueError):
            HighPrecisionLpConvexSolver.solve_irls(DirectedGraph.triangle(), [1,1,1],p)


def test_review_three_step_update_has_nonoptimal_fixed_point_on_one_edge():
    """The withdrawn proposed update cannot support a strict descent theorem."""
    # On one oriented edge, d0*d0_star acts as multiplication by 2.
    # With omega=1, s=0, phi=0, sigma=1 and tau=1/2, clipping gives
    # phi_half=1 and correction gives phi_next=0. Hence s is unchanged,
    # while the feasible choice d0(s)=omega has zero residual.
    residual = Fraction(1)
    phi_half = min(Fraction(1), max(Fraction(-1), residual))
    phi_next = phi_half - Fraction(1, 2) * 2 * phi_half
    assert phi_next == 0
    assert residual > 0


def test_schatten_polar_dual_p1_and_pinf():
    """Verify polar dual witness for extreme Schatten exponents p=1 (dual q=inf) and p=inf (dual q=1)."""
    np.random.seed(42)
    A = np.random.randn(3, 3) + 1j * np.random.randn(3, 3)

    # 1. p = inf (dual q = 1, witness is rank-one singular vector projection)
    dual_inf = OperatorSchattenPModule.polar_dual_maximizer(A, float("inf"))
    norm_A_inf = OperatorSchattenPModule.schatten_norm(A, float("inf"))
    norm_dual_1 = OperatorSchattenPModule.schatten_norm(dual_inf, 1.0)
    pairing_inf = abs(np.trace(dual_inf.conj().T @ A))
    assert np.isclose(norm_dual_1, 1.0, atol=1e-12)
    assert np.isclose(pairing_inf, norm_A_inf, atol=1e-12)

    # 2. p = 1 (dual q = inf, witness is partial isometry)
    dual_1 = OperatorSchattenPModule.polar_dual_maximizer(A, 1.0)
    norm_A_1 = OperatorSchattenPModule.schatten_norm(A, 1.0)
    norm_dual_inf = OperatorSchattenPModule.schatten_norm(dual_1, float("inf"))
    pairing_1 = abs(np.trace(dual_1.conj().T @ A))
    assert np.isclose(norm_dual_inf, 1.0, atol=1e-12)
    assert np.isclose(pairing_1, norm_A_1, atol=1e-12)


def test_bell_state_marginal_compatibility_vs_correlation():
    """Counterexample: Bell state marginal incompatibility across identity edge is zero,

    while bipartite product defect ||rho - rho_A (x) rho_B||_1 is 3/2.
    """
    # Bell state |Phi+> = (|00> + |11>) / sqrt(2)
    phi_plus = np.array([1, 0, 0, 1], dtype=np.complex128) / np.sqrt(2)
    rho = np.outer(phi_plus, phi_plus.conj())

    # Partial traces to get 1-qubit marginals rho_A and rho_B:
    # rho has basis |00>, |01>, |10>, |11>
    rho_A = np.array([
        [rho[0, 0] + rho[1, 1], rho[0, 2] + rho[1, 3]],
        [rho[2, 0] + rho[3, 1], rho[2, 2] + rho[3, 3]],
    ])
    rho_B = np.array([
        [rho[0, 0] + rho[2, 2], rho[0, 1] + rho[2, 3]],
        [rho[1, 0] + rho[3, 2], rho[1, 1] + rho[3, 3]],
    ])

    # Both marginals are maximally mixed: I/2
    I2_half = 0.5 * np.eye(2, dtype=np.complex128)
    assert np.allclose(rho_A, I2_half)
    assert np.allclose(rho_B, I2_half)

    # Local edge difference between identical single-qubit stalks vanishes:
    delta_edge = rho_B - rho_A
    assert np.allclose(delta_edge, 0.0)
    assert OperatorSchattenPModule.schatten_norm(delta_edge, 1.0) == 0.0

    # Yet true two-site product defect ||rho - rho_A (x) rho_B||_1 is 3/2:
    rho_prod = np.kron(rho_A, rho_B)
    product_defect = OperatorSchattenPModule.schatten_norm(rho - rho_prod, 1.0)
    assert np.isclose(product_defect, 1.5, atol=1e-12)


def test_isomorphism_invariance_orbit_weights_3edge_path():
    """On a 3-edge path, weights (1, 2, 1) are automorphism-invariant but non-uniform."""
    # Path graph 0 - 1 - 2 - 3 with edges e0=(0,1), e1=(1,2), e2=(2,3)
    # Automorphism group is Z_2: sigma(0)=3, sigma(1)=2, sigma(2)=1, sigma(3)=0.
    # Edge action: sigma(e0) = (3,2) ~ e2, sigma(e1) = (2,1) ~ e1, sigma(e2) = (1,0) ~ e0.
    # Orbit 1: {e0, e2}; Orbit 2: {e1}.
    weights = [Fraction(1), Fraction(2), Fraction(1)]

    # Weights are invariant under the reflection automorphism sigma:
    sigma_edges = [2, 1, 0]  # maps edge index 0 -> 2, 1 -> 1, 2 -> 0
    assert [weights[sigma_edges[i]] for i in range(3)] == weights

    # Yet weights are NOT uniform:
    assert len(set(weights)) > 1


# ============================================================================
# 8. Republication Review Regression Tests (v5.5.2)
# ============================================================================

def test_kkt_checker_dimension_validation():
    """Verify that is_kkt_fixed_point and certificate_dominates enforce full input dimensions."""
    graph = DirectedGraph.path(2)
    assert len(graph.edges) == 1
    assert len(graph.vertices) == 2

    valid_h = [Fraction(1)]
    valid_f = [Fraction(0), Fraction(0)]
    valid_z = [Fraction(0)]

    # Overlong observation cochain (Review finding 7.1)
    overlong_h = [Fraction(1), Fraction(999)]
    with pytest.raises(CochainDimensionError):
        LocalPrimalDualIterator.is_kkt_fixed_point(graph, overlong_h, valid_f, valid_z)
    with pytest.raises(CochainDimensionError):
        LocalPrimalDualIterator.certificate_dominates(graph, overlong_h, valid_f, valid_z, valid_f)

    # Short observation cochain
    short_h: list[Fraction] = []
    with pytest.raises(CochainDimensionError):
        LocalPrimalDualIterator.is_kkt_fixed_point(graph, short_h, valid_f, valid_z)
    with pytest.raises(CochainDimensionError):
        LocalPrimalDualIterator.certificate_dominates(graph, short_h, valid_f, valid_z, valid_f)

    # Overlong / short potential
    with pytest.raises(CochainDimensionError):
        LocalPrimalDualIterator.is_kkt_fixed_point(graph, valid_h, [Fraction(0)], valid_z)
    with pytest.raises(CochainDimensionError):
        LocalPrimalDualIterator.is_kkt_fixed_point(graph, valid_h, [Fraction(0), Fraction(0), Fraction(0)], valid_z)

    # Overlong / short dual
    with pytest.raises(CochainDimensionError):
        LocalPrimalDualIterator.is_kkt_fixed_point(graph, valid_h, valid_f, [Fraction(0), Fraction(0)])
    with pytest.raises(CochainDimensionError):
        LocalPrimalDualIterator.is_kkt_fixed_point(graph, valid_h, valid_f, [])


def test_directed_graph_incidence_immutability():
    """Verify DirectedGraph.B is immutable and d0/d0_star cannot desynchronize."""
    graph = DirectedGraph.path(2)
    assert isinstance(graph.B, tuple)
    assert isinstance(graph.B[0], tuple)

    with pytest.raises(TypeError):
        graph.B[0][0] = Fraction(0)  # type: ignore

    with pytest.raises(AttributeError):
        graph.B = tuple()  # type: ignore

    z = [Fraction(3)]
    div = graph.d0_star(z)
    assert div == [Fraction(-3), Fraction(3)]


def test_primal_residual_divergence_non_equivalence_counterexample():
    """Review Finding 1: An L1-optimal residual can have non-zero primal divergence."""
    # Cyclically oriented triangle 0 -> 1 -> 2 -> 0
    graph = DirectedGraph.cycle(3)
    r = [Fraction(2), Fraction(1), Fraction(1)]
    phi = [Fraction(1), Fraction(1), Fraction(1)]
    f_zero = [Fraction(0), Fraction(0), Fraction(0)]

    div_phi = graph.d0_star(phi)
    assert all(d == Fraction(0) for d in div_phi)
    assert all(abs(phi[e]) <= graph.weights[e] for e in range(3))

    dot_val = sum(phi[e] * r[e] for e in range(3))
    l1_val = sum(graph.weights[e] * abs(r[e]) for e in range(3))
    assert dot_val == l1_val == Fraction(4)

    assert LocalPrimalDualIterator.is_kkt_fixed_point(graph, r, f_zero, phi) is True

    div_r = graph.d0_star(r)
    assert div_r == [Fraction(-1), Fraction(1), Fraction(0)]
    assert any(d != Fraction(0) for d in div_r)

    # Support difference: r=(3, 0, 0) certified by same phi=(1, 1, 1)
    r_sparse = [Fraction(3), Fraction(0), Fraction(0)]
    assert LocalPrimalDualIterator.is_kkt_fixed_point(graph, r_sparse, f_zero, phi) is True
    assert phi[1] != Fraction(0) and r_sparse[1] == Fraction(0)
    assert phi[2] != Fraction(0) and r_sparse[2] == Fraction(0)


def test_overlapping_cycle_holonomy_counterexample():
    """Review Finding 2: Holonomy sum overcounts shared edges; capacity normalization is required."""
    vertices = [0, 1, 2, 3]
    edges = [(0, 1), (1, 2), (0, 2), (2, 3), (0, 3)]
    graph = DirectedGraph(vertices, edges)

    omega = [Fraction(0), Fraction(0), Fraction(1), Fraction(0), Fraction(0)]

    c1 = [Fraction(1), Fraction(1), Fraction(-1), Fraction(0), Fraction(0)]
    c2 = [Fraction(0), Fraction(0), Fraction(1), Fraction(1), Fraction(-1)]

    assert all(d == Fraction(0) for d in graph.d0_star(c1))
    assert all(d == Fraction(0) for d in graph.d0_star(c2))

    hol1 = sum(c1[e] * omega[e] for e in range(5))
    hol2 = sum(c2[e] * omega[e] for e in range(5))
    assert hol1 == Fraction(-1)
    assert hol2 == Fraction(1)

    sum_abs_hol = abs(hol1) + abs(hol2)
    assert sum_abs_hol == Fraction(2)

    f_zero = [Fraction(0)] * 4
    assert LocalPrimalDualIterator.is_kkt_fixed_point(graph, omega, f_zero, c2) is True
    true_l1_opt = sum(graph.weights[e] * abs(omega[e]) for e in range(5))
    assert true_l1_opt == Fraction(1)

    assert sum_abs_hol > true_l1_opt

    M_c2 = max(abs(c2[e]) / graph.weights[e] for e in range(5))
    normalized_bound = abs(sum(c2[e] * omega[e] for e in range(5))) / M_c2
    assert normalized_bound == Fraction(1) <= true_l1_opt

