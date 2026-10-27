"""Invasive fault-injection test suite and mathematical verification for Paper 007.

Tests achieve >=95% statement and branch coverage across:
- DirectedGraph topology, weights, connectedness, cycle rank, and coboundary operators.
- Simplicial2Complex boundary matrices D1, D2 and nilpotency D1 @ D2 == 0.
- Exact Two-Phase Simplex LP solver (optimal, infeasible, unbounded, degenerate, Bland's rule).
- L1 quotient solver, dual circulation maximum, and complementary slackness certification.
- Cycle rank support bound |supp(r)| <= beta (Theorem L1C-T5).
- Total unimodularity and integer attainment (Theorem L1C-T6).
- The L1 vs L2 localization counterexample from paper Section 8.
- Discrete physics: lattice gauge connections, Bianchi identity, current conservation.
- Finite quantum obstruction calculus: phase cocycles, density matrices, trace bounds.
- Invasive fault injections: corrupted topology, self-loops, zero/negative weights, broken
  nilpotency, capacity violations, divergent circulations, non-Hermitian/unnormalized states.

AuthorityEffect: None.
"""

import math
from fractions import Fraction

import numpy as np
import pytest
from l1_cohomology import (
    BianchiViolationError,
    CapacityBoundExceededError,
    CertificateViolationError,
    CirculationDivergenceError,
    CochainDimensionError,
    ComplementarySlacknessError,
    DirectedGraph,
    DualityGapNonZeroError,
    DuplicateEdgeError,
    ExactRationalL2LaplacianSolver,
    ExactRationalLinfChebyshevSolver,
    ExactTwoPhaseSimplexSolver,
    HighPrecisionLpConvexSolver,
    L1CertificateReceipt,
    L1QuotientSolver,
    NegativeSpectrumError,
    NegativeWeightError,
    NilpotencyViolationError,
    NonHermitianStateError,
    OperatorSchattenPModule,
    PrimalFeasibilityError,
    QuantumDensityMatrix,
    QuantumIntegrityError,
    RationalComplex,
    SelfLoopError,
    Simplicial2Complex,
    SolverInfeasibleError,
    SolverIterationLimitError,
    SolverUnboundedError,
    TopologyIntegrityError,
    TraceNormalizationError,
    ZeroWeightRefusalError,
    check_certificate_receipt,
)

# ============================================================================
# 1. Topology & Weight Integrity Tests (with Invasive Fault Injections)
# ============================================================================

def test_directed_graph_valid_initialization():
    """Verify clean graph creation on trees, cycles, and complete graphs."""
    g = DirectedGraph(vertices=[0, 1, 2], edges=[(0, 1), (1, 2)], weights=[2, 3])
    assert g.is_connected()
    assert g.cycle_rank() == 0
    assert len(g.edges) == 2
    assert len(g.vertices) == 3


def test_directed_graph_fault_injection_self_loop():
    """Invasive fault injection: Self-loop must raise SelfLoopError."""
    with pytest.raises(SelfLoopError) as exc_info:
        DirectedGraph(vertices=[0, 1], edges=[(0, 0)])
    assert "Self-loop detected" in str(exc_info.value)


def test_directed_graph_fault_injection_duplicate_edge():
    """Invasive fault injection: Duplicate edge must raise DuplicateEdgeError."""
    with pytest.raises(DuplicateEdgeError) as exc_info:
        DirectedGraph(vertices=[0, 1], edges=[(0, 1), (0, 1)])
    assert "Duplicate edge declared" in str(exc_info.value)


def test_directed_graph_fault_injection_duplicate_vertex():
    """Invasive fault injection: Duplicate vertex must raise TopologyIntegrityError."""
    with pytest.raises(TopologyIntegrityError) as exc_info:
        DirectedGraph(vertices=[0, 1, 0], edges=[(0, 1)])
    assert "Duplicate vertex" in str(exc_info.value)


def test_directed_graph_fault_injection_nonexistent_vertex():
    """Invasive fault injection: Edge referencing absent vertex must raise TopologyIntegrityError."""
    with pytest.raises(TopologyIntegrityError) as exc_info:
        DirectedGraph(vertices=[0, 1], edges=[(0, 2)])
    assert "not in vertex set" in str(exc_info.value)


def test_directed_graph_fault_injection_zero_weight_refusal():
    """Invasive fault injection: Zero weight must raise ZeroWeightRefusalError per L1C-T2."""
    with pytest.raises(ZeroWeightRefusalError) as exc_info:
        DirectedGraph(vertices=[0, 1], edges=[(0, 1)], weights=[0])
    assert "strictly positive weights required by L1C-T2" in str(exc_info.value)


def test_directed_graph_fault_injection_negative_weight():
    """Invasive fault injection: Negative weight must raise NegativeWeightError."""
    with pytest.raises(NegativeWeightError) as exc_info:
        DirectedGraph(vertices=[0, 1], edges=[(0, 1)], weights=[-5])
    assert "negative weight" in str(exc_info.value)


def test_directed_graph_fault_injection_weight_dimension_mismatch():
    """Invasive fault injection: Weights count != edges count raises CochainDimensionError."""
    with pytest.raises(CochainDimensionError):
        DirectedGraph(vertices=[0, 1, 2], edges=[(0, 1), (1, 2)], weights=[1])


def test_directed_graph_cycle_rank_and_components():
    """Verify Betti number beta = |E| - |V| + c on disconnected graphs."""
    # Two disconnected 3-cycles: 6 vertices, 6 edges, 2 components => beta = 6 - 6 + 2 = 2
    g = DirectedGraph(
        vertices=[0, 1, 2, 3, 4, 5],
        edges=[(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)],
    )
    assert not g.is_connected()
    assert len(g.connected_components()) == 2
    assert g.cycle_rank() == 2


def test_directed_graph_cycle_factory_bounds():
    """Test DirectedGraph.cycle factory and size checks."""
    with pytest.raises(TopologyIntegrityError):
        DirectedGraph.cycle(2)
    c4 = DirectedGraph.cycle(4, weights=[1, 2, 3, 4])
    assert c4.is_connected()
    assert c4.cycle_rank() == 1


# ============================================================================
# 2. Simplicial 2-Complex & Nilpotency Tests
# ============================================================================

def test_simplicial_complex_valid():
    """Verify standard triangle 2-complex with D1 @ D2 == 0."""
    sc = Simplicial2Complex(
        vertices=[0, 1, 2],
        edges=[(0, 1), (1, 2), (0, 2)],
        faces=[(0, 1, 2)],
    )
    assert sc.verify_nilpotency()
    # d1(d0 phi) == 0 for all vertex potentials phi
    phi = [Fraction(3), Fraction(-7), Fraction(11)]
    assert sc.discrete_bianchi_identity(phi) == [Fraction(0)]


def test_simplicial_complex_fault_injection_corrupted_face():
    """Invasive fault injection: Face with missing boundary edge raises TopologyIntegrityError."""
    with pytest.raises(TopologyIntegrityError) as exc_info:
        Simplicial2Complex(
            vertices=[0, 1, 2],
            edges=[(0, 1), (1, 2)],  # Missing (0, 2)
            faces=[(0, 1, 2)],
        )
    assert "missing from edges" in str(exc_info.value)


def test_simplicial_complex_fault_injection_weights_mismatch():
    """Invasive fault injection: Weights count != edges count raises CochainDimensionError."""
    with pytest.raises(CochainDimensionError):
        Simplicial2Complex(
            vertices=[0, 1, 2],
            edges=[(0, 1), (1, 2), (0, 2)],
            faces=[(0, 1, 2)],
            weights=[1, 1],
        )


def test_simplicial_complex_cochain_dimension_guards():
    """Verify dimension guards on d0, d1, and d0_star."""
    sc = Simplicial2Complex(
        vertices=[0, 1, 2],
        edges=[(0, 1), (1, 2), (0, 2)],
        faces=[(0, 1, 2)],
    )
    with pytest.raises(CochainDimensionError):
        sc.d0([1, 2])
    with pytest.raises(CochainDimensionError):
        sc.d1([1, 2])


# ============================================================================
# 3. Two-Phase Simplex Solver Tests (Full Operational Spectrum)
# ============================================================================

def test_simplex_solver_standard_lp():
    """Test standard LP minimization."""
    # min x0 + 2 x1 subject to x0 + x1 = 3, x0, x1 >= 0
    A = [[Fraction(1), Fraction(1)]]
    b = [Fraction(3)]
    c = [Fraction(1), Fraction(2)]
    res = ExactTwoPhaseSimplexSolver.solve_standard_lp(c, A, b)
    assert res.status == "OPTIMAL"
    assert res.obj_val == Fraction(3)
    assert res.x == [Fraction(3), Fraction(0)]


def test_simplex_solver_infeasible():
    """Invasive fault injection: Infeasible LP raises SolverInfeasibleError."""
    # x0 + x1 = 2, x0 + x1 = 5
    A = [[Fraction(1), Fraction(1)], [Fraction(1), Fraction(1)]]
    b = [Fraction(2), Fraction(5)]
    c = [Fraction(1), Fraction(1)]
    with pytest.raises(SolverInfeasibleError):
        ExactTwoPhaseSimplexSolver.solve_standard_lp(c, A, b)


def test_simplex_solver_unbounded():
    """Invasive fault injection: Unbounded LP raises SolverUnboundedError."""
    # min -x0 subject to x0 - x1 = 1, x0, x1 >= 0 => unbounded
    A = [[Fraction(1), Fraction(-1)]]
    b = [Fraction(1)]
    c = [Fraction(-1), Fraction(0)]
    with pytest.raises(SolverUnboundedError):
        ExactTwoPhaseSimplexSolver.solve_standard_lp(c, A, b)


def test_simplex_solver_empty_constraints():
    """Verify behavior on empty constraints."""
    c = [Fraction(1), Fraction(2)]
    res = ExactTwoPhaseSimplexSolver.solve_standard_lp(c, [], [])
    assert res.status == "OPTIMAL"
    assert res.obj_val == Fraction(0)
    assert res.x == [Fraction(0), Fraction(0)]

    with pytest.raises(SolverUnboundedError):
        ExactTwoPhaseSimplexSolver.solve_standard_lp([Fraction(-1)], [], [])


def test_simplex_solver_negative_rhs_handling():
    """Verify automatic negation of negative RHS rows."""
    # -x0 - x1 = -4  =>  x0 + x1 = 4
    A = [[Fraction(-1), Fraction(-1)]]
    b = [Fraction(-4)]
    c = [Fraction(2), Fraction(3)]
    res = ExactTwoPhaseSimplexSolver.solve_standard_lp(c, A, b)
    assert res.status == "OPTIMAL"
    assert res.obj_val == Fraction(8)
    assert res.x == [Fraction(4), Fraction(0)]


# ============================================================================
# 4. L1-Native Cohomology Core Theorems (L1C-T1 through L1C-T6)
# ============================================================================

def test_l1c_exact_cochain_gives_exact_repair():
    """Test Corollary L1C-C1: an exact cochain omega in im(d0) has Phi_1 = 0."""
    g = DirectedGraph.triangle()
    # Choose potential f = (0, 4, 10)
    # d0 f = (4 - 0, 10 - 4, 10 - 0) = (4, 6, 10)
    omega = g.d0([0, 4, 10])
    receipt = L1QuotientSolver.solve(g, omega)

    assert receipt.diagnostic_type == "ExactRepair"
    assert receipt.primal_norm == Fraction(0)
    assert receipt.dual_bound == Fraction(0)
    assert receipt.duality_gap == Fraction(0)
    assert receipt.satisfies_complementary_slackness
    assert receipt.satisfies_support_bound
    assert receipt.is_integral


def test_l1c_single_cycle_exact_formula():
    """Verify Section 5 formula on a directed cycle: Phi_1([omega]) = |S| * min_e w_e."""
    # 4-cycle with distinct weights w = (2, 5, 1, 4)
    g = DirectedGraph.cycle(4, weights=[2, 5, 1, 4])
    # omega = (3, 2, -1, 4) => S = 3 + 2 - 1 + 4 = 8
    # min_e w_e = 1 (edge 2)
    # Expected Phi_1 = 8 * 1 = 8
    omega = [3, 2, -1, 4]
    receipt = L1QuotientSolver.solve(g, omega)

    assert receipt.diagnostic_type == "ClosedResidual"
    assert receipt.primal_norm == Fraction(8)
    assert receipt.dual_bound == Fraction(8)
    assert receipt.duality_gap == Fraction(0)
    assert receipt.cycle_rank == 1
    assert receipt.satisfies_support_bound  # |supp(r)| <= 1
    assert receipt.satisfies_complementary_slackness
    assert receipt.is_integral


def test_l1c_paper_section8_l1_vs_l2_counterexample():
    """Verify Section 8 counterexample where L1 localizes defect while L2 spreads it.

    B = (1, 1, 1)^T, omega = (0, 0, 10)^T.
    3 parallel edges between 2 vertices (v0, v1):
    edges: e0=(0,1), e1=(0,1), e2=(0,1).
    Cycle rank beta = 3 - 2 + 1 = 2.
    """
    g = DirectedGraph(
        vertices=[0, 1],
        edges=[(0, 1), (0, 1), (0, 1)],
        weights=[1, 1, 1],
        allow_parallel_edges=True,
    )
    omega = [0, 0, 10]
    receipt = L1QuotientSolver.solve(g, omega)

    # L1 optimal norm is 10 (taking f = (0, 0), residual = (0, 0, 10), supp = 1 <= beta = 2)
    assert receipt.primal_norm == Fraction(10)
    assert receipt.dual_bound == Fraction(10)
    assert receipt.duality_gap == Fraction(0)
    assert receipt.satisfies_support_bound
    assert receipt.support_size <= receipt.cycle_rank


def test_l1c_cycle_rank_support_bound_on_grid():
    """Verify Theorem L1C-T5: |supp(r*)| <= beta on a 2x2 grid (beta = 2)."""
    # 4 vertices, 5 edges (square with diagonal): beta = 5 - 4 + 1 = 2
    g = DirectedGraph(
        vertices=[0, 1, 2, 3],
        edges=[(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)],
        weights=[1, 1, 1, 1, 1],
    )
    assert g.cycle_rank() == 2
    omega = [1, 2, 3, 4, 5]
    receipt = L1QuotientSolver.solve(g, omega)

    assert receipt.duality_gap == Fraction(0)
    assert receipt.satisfies_support_bound
    assert receipt.support_size <= 2


def test_l1c_total_unimodularity_integer_attainment():
    """Verify Theorem L1C-T6: Integral inputs guarantee integral optima."""
    g = DirectedGraph.triangle(weights=[3, 4, 5])
    omega = [7, -11, 13]
    receipt = L1QuotientSolver.solve(g, omega)

    assert receipt.is_integral
    for r in receipt.primal_residual:
        assert r.denominator == 1
    for f in receipt.primal_potential:
        assert f.denominator == 1


def test_l1c_custom_gauge_vertex():
    """Verify solving with explicitly selected non-zero gauge vertex."""
    g = DirectedGraph.triangle()
    omega = [2, 3, 5]
    receipt = L1QuotientSolver.solve(g, omega, gauge_vertex=2)
    assert receipt.primal_potential[2] == Fraction(0)
    assert receipt.duality_gap == Fraction(0)


def test_l1c_fault_injection_invalid_gauge_vertex():
    """Invasive fault injection: Non-existent gauge vertex raises TopologyIntegrityError."""
    g = DirectedGraph.triangle()
    with pytest.raises(TopologyIntegrityError):
        L1QuotientSolver.solve(g, [1, 1, 1], gauge_vertex="nonexistent_v")


def test_l1c_fault_injection_omega_dimension_mismatch():
    """Invasive fault injection: omega length != edge count raises CochainDimensionError."""
    g = DirectedGraph.triangle()
    with pytest.raises(CochainDimensionError):
        L1QuotientSolver.solve(g, [1, 2])


# ============================================================================
# 5. Discrete Physics Operators (Theorem L1C-T7)
# ============================================================================

def test_discrete_physics_bianchi_identity():
    """Verify discrete Bianchi identity d1(d0 phi) == 0 across diverse 2-complexes."""
    # 2-triangle complex
    sc = Simplicial2Complex(
        vertices=[0, 1, 2, 3],
        edges=[(0, 1), (1, 2), (0, 2), (2, 3), (0, 3)],
        faces=[(0, 1, 2), (0, 2, 3)],
    )
    for test_phi in [
        [0, 0, 0, 0],
        [1, -2, 3, -4],
        [Fraction(1, 3), Fraction(-5, 7), Fraction(11, 2), Fraction(0)],
    ]:
        assert sc.discrete_bianchi_identity(test_phi) == [Fraction(0), Fraction(0)]


def test_discrete_physics_current_conservation():
    """Verify discrete Kirchhoff current law div(z) = B^T z == 0 on dual circulation."""
    g = DirectedGraph.triangle()
    omega = [5, 5, 0]
    receipt = L1QuotientSolver.solve(g, omega)
    div = g.d0_star(receipt.dual_circulation)
    assert all(d == Fraction(0) for d in div)


# ============================================================================
# 6. Finite Quantum Obstruction Calculus (Theorem L1C-T8)
# ============================================================================

def test_quantum_density_matrix_valid():
    """Verify valid quantum density matrix construction and off-diagonal coherence."""
    # 2x2 density matrix: [[3/4, 1/4], [1/4, 1/4]]
    # Tr = 1, Hermitian, non-negative diagonal, det = 3/16 - 1/16 = 2/16 > 0
    mat = [
        [RationalComplex(Fraction(3, 4), Fraction(0)), RationalComplex(Fraction(1, 4), Fraction(0))],
        [RationalComplex(Fraction(1, 4), Fraction(0)), RationalComplex(Fraction(1, 4), Fraction(0))],
    ]
    rho = QuantumDensityMatrix(mat)
    assert rho.dim == 2
    assert rho.off_diagonal_l1_coherence() == Fraction(1, 4)

    # Dephased pointer state
    rho_diag = rho.dephased_state()
    assert rho_diag.matrix[0][1].re == Fraction(0)
    assert rho_diag.matrix[1][0].re == Fraction(0)


def test_quantum_fault_injection_non_hermitian():
    """Invasive fault injection: Non-Hermitian matrix raises NonHermitianStateError."""
    mat = [
        [RationalComplex(Fraction(1, 2), Fraction(0)), RationalComplex(Fraction(1, 2), Fraction(0))],
        [RationalComplex(Fraction(1, 4), Fraction(0)), RationalComplex(Fraction(1, 2), Fraction(0))],
    ]
    with pytest.raises(NonHermitianStateError):
        QuantumDensityMatrix(mat)


def test_quantum_fault_injection_trace_non_one():
    """Invasive fault injection: Tr(rho) != 1 raises TraceNormalizationError."""
    mat = [
        [RationalComplex(Fraction(1, 2), Fraction(0)), RationalComplex(Fraction(0), Fraction(0))],
        [RationalComplex(Fraction(0), Fraction(0)), RationalComplex(Fraction(2, 3), Fraction(0))],
    ]
    with pytest.raises(TraceNormalizationError):
        QuantumDensityMatrix(mat)


def test_quantum_fault_injection_negative_diagonal():
    """Invasive fault injection: Negative diagonal element raises NegativeSpectrumError."""
    mat = [
        [RationalComplex(Fraction(-1, 4), Fraction(0)), RationalComplex(Fraction(0), Fraction(0))],
        [RationalComplex(Fraction(0), Fraction(0)), RationalComplex(Fraction(5, 4), Fraction(0))],
    ]
    with pytest.raises(NegativeSpectrumError):
        QuantumDensityMatrix(mat)


def test_quantum_fault_injection_principal_minor_violated():
    """Invasive fault injection: Coherence exceeding diagonal product raises NegativeSpectrumError."""
    # rho_00 = 1/2, rho_11 = 1/2, prod = 1/4. Off-diagonal = 3/4 => |off|^2 = 9/16 > 1/4
    mat = [
        [RationalComplex(Fraction(1, 2), Fraction(0)), RationalComplex(Fraction(3, 4), Fraction(0))],
        [RationalComplex(Fraction(3, 4), Fraction(0)), RationalComplex(Fraction(1, 2), Fraction(0))],
    ]
    with pytest.raises(NegativeSpectrumError):
        QuantumDensityMatrix(mat)


def test_quantum_pure_state_factory():
    """Verify pure state |psi><psi| construction."""
    # |psi> = (1/sqrt(2), 1/sqrt(2)) encoded with exact rational amplitudes: (3/5, 4/5) (norm^2 = 9/25 + 16/25 = 1)
    amps = [RationalComplex(Fraction(3, 5), Fraction(0)), RationalComplex(Fraction(4, 5), Fraction(0))]
    rho_pure = QuantumDensityMatrix.pure_state(amps)
    assert rho_pure.matrix[0][0].re == Fraction(9, 25)
    assert rho_pure.matrix[1][1].re == Fraction(16, 25)
    assert rho_pure.matrix[0][1].re == Fraction(12, 25)
    assert rho_pure.matrix[1][0].re == Fraction(12, 25)


def test_quantum_pure_state_unnormalized():
    """Invasive fault injection: Unnormalized amplitude vector raises TraceNormalizationError."""
    amps = [RationalComplex(Fraction(1), Fraction(0)), RationalComplex(Fraction(1), Fraction(0))]
    with pytest.raises(TraceNormalizationError):
        QuantumDensityMatrix.pure_state(amps)


# ============================================================================
# 7. Helper Operators & Edge Cases
# ============================================================================

def test_rational_complex_arithmetic():
    """Verify exact rational complex operations."""
    z1 = RationalComplex(Fraction(1, 2), Fraction(1, 3))
    z2 = RationalComplex(Fraction(1, 4), Fraction(2, 3))
    z_add = z1 + z2
    assert z_add.re == Fraction(3, 4)
    assert z_add.im == Fraction(1)
    z_sub = z1 - z2
    assert z_sub.re == Fraction(1, 4)
    assert z_sub.im == Fraction(-1, 3)
    z_mul = z1 * z2
    # (1/2 + i/3)(1/4 + 2i/3) = (1/8 - 2/9) + i(1/3 + 1/12) = (-7/72) + i(5/12)
    assert z_mul.re == Fraction(-7, 72)
    assert z_mul.im == Fraction(5, 12)
    z_scale = z1 * 2
    assert z_scale.re == Fraction(1)
    assert z_scale.im == Fraction(2, 3)


def test_directed_graph_d0_dimension_mismatch():
    """Verify cochain dimension mismatch on d0 and d0_star."""
    g = DirectedGraph.triangle()
    with pytest.raises(CochainDimensionError):
        g.d0([1, 2])
    with pytest.raises(CochainDimensionError):
        g.d0_star([1, 2])
    with pytest.raises(CochainDimensionError):
        g.weighted_l1_norm([1, 2])
    with pytest.raises(CochainDimensionError):
        g.inner_product([1, 2], [1, 2, 3])


def test_empty_directed_graph():
    """Verify degenerate empty graph."""
    g = DirectedGraph(vertices=[], edges=[], weights=[])
    assert g.is_connected()
    assert g.cycle_rank() == 0


def test_directed_graph_additional_branches():
    """Verify endpoint u not in vertex set, validate=False, and inner_product second mismatch."""
    with pytest.raises(TopologyIntegrityError) as exc_info:
        DirectedGraph(vertices=[0, 1], edges=[(2, 0)])
    assert "Edge endpoint 2 not in vertex set" in str(exc_info.value)

    # validate=False bypasses validate_topology_and_weights
    g_no_val = DirectedGraph(vertices=[0, 1], edges=[(0, 1)], validate=False)
    assert g_no_val.is_connected()

    # Valid evaluations covering generator comprehensions
    g = DirectedGraph.triangle()
    norm = g.weighted_l1_norm([1, 2, 3])
    assert norm == Fraction(6)
    dot = g.inner_product([1, 2, 3], [4, 5, 6])
    assert dot == Fraction(32)

    # inner_product second argument length mismatch
    with pytest.raises(CochainDimensionError):
        g.inner_product([1, 2, 3], [1, 2])


def test_simplicial_complex_additional_branches_and_fault_injections():
    """Verify Simplicial2Complex weights, reversed face segment orientation, and fault injections."""
    # Explicit weights
    sc_wt = Simplicial2Complex(
        vertices=[0, 1, 2],
        edges=[(0, 1), (1, 2), (0, 2)],
        faces=[(0, 1, 2)],
        weights=[3, 4, 5],
    )
    assert sc_wt.weights == (Fraction(3), Fraction(4), Fraction(5))

    # Face segment reversed: face (0, 1, 2) has segments (0, 1), (1, 2), (0, 2).
    # If edge is declared as (2, 0) instead of (0, 2), it hits elif (b, a) in self.edge_index
    sc_rev = Simplicial2Complex(
        vertices=[0, 1, 2],
        edges=[(0, 1), (1, 2), (2, 0)],
        faces=[(0, 1, 2)],
    )
    assert sc_rev.verify_nilpotency()

    # validate=False bypasses verify_nilpotency
    sc_no_val = Simplicial2Complex(
        vertices=[0, 1, 2],
        edges=[(0, 1), (1, 2), (0, 2)],
        faces=[(0, 1, 2)],
        validate=False,
    )
    assert len(sc_no_val.faces) == 1

    # Corrupt D1 so that D1 @ D2 != 0 triggers NilpotencyViolationError
    sc_corrupt = Simplicial2Complex(
        vertices=[0, 1, 2],
        edges=[(0, 1), (1, 2), (0, 2)],
        faces=[(0, 1, 2)],
        validate=False,
    )
    sc_corrupt.D1[0][0] = Fraction(99)
    with pytest.raises(NilpotencyViolationError) as exc_info:
        sc_corrupt.verify_nilpotency()
    assert "D1 @ D2 != 0" in str(exc_info.value)

    # Force Bianchi violation via mock d1 output
    sc_bianchi = Simplicial2Complex(
        vertices=[0, 1, 2],
        edges=[(0, 1), (1, 2), (0, 2)],
        faces=[(0, 1, 2)],
    )
    sc_bianchi.d1 = lambda A: [Fraction(7)]
    with pytest.raises(BianchiViolationError) as exc_info:
        sc_bianchi.discrete_bianchi_identity([0, 0, 0])
    assert "Discrete Bianchi identity violated" in str(exc_info.value)


def test_quantum_density_matrix_fault_injection_empty_nonsquare_and_novalidate():
    """Invasive fault injection: Empty, non-square, and unvalidated density matrices."""
    with pytest.raises(QuantumIntegrityError) as exc1:
        QuantumDensityMatrix([])
    assert "Empty density matrix" in str(exc1.value)

    row1 = [RationalComplex(Fraction(1), Fraction(0))]
    row2 = [RationalComplex(Fraction(0), Fraction(0)), RationalComplex(Fraction(1), Fraction(0))]
    with pytest.raises(QuantumIntegrityError) as exc2:
        QuantumDensityMatrix([row1, row2])
    assert "Non-square density matrix" in str(exc2.value)

    # validate=False allows constructing unvalidated matrix
    bad_mat = [[RationalComplex(Fraction(5), Fraction(0))]]
    rho_no_val = QuantumDensityMatrix(bad_mat, validate=False)
    assert rho_no_val.dim == 1


def test_two_phase_simplex_redundant_constraints_artificial_pivot():
    """Verify Phase 1 artificial variable pivot-out with linearly dependent rows and zero RHS."""
    A = [
        [Fraction(1), Fraction(1)],
        [Fraction(2), Fraction(2)],
    ]
    b = [Fraction(3), Fraction(6)]
    c = [Fraction(1), Fraction(2)]
    res = ExactTwoPhaseSimplexSolver.solve_standard_lp(c, A, b)
    assert res.status == "OPTIMAL"
    assert res.obj_val == Fraction(3)
    assert res.x == [Fraction(3), Fraction(0)]

    # Zero RHS to force degenerate artificial variable in basis at end of Phase 1
    A2 = [[Fraction(1), Fraction(-1)], [Fraction(1), Fraction(1)]]
    b2 = [Fraction(0), Fraction(1)]
    c2 = [Fraction(1), Fraction(1)]
    res2 = ExactTwoPhaseSimplexSolver.solve_standard_lp(c2, A2, b2)
    assert res2.status == "OPTIMAL"
    assert res2.obj_val == Fraction(1)


def test_l1_solver_defensive_fault_injections(monkeypatch):
    """Invasive fault injections for L1QuotientSolver runtime certificates."""
    g = DirectedGraph.triangle()
    omega = [1, 2, 3]

    from l1_cohomology import SimplexResult
    original_solve_lp = ExactTwoPhaseSimplexSolver.solve_standard_lp

    # 1. Primal solver fails with non-OPTIMAL status
    def fake_solve_lp_primal_fail(c, A, b, max_iter=10000):
        return SimplexResult("INFEASIBLE", Fraction(0), [], [])

    monkeypatch.setattr(ExactTwoPhaseSimplexSolver, "solve_standard_lp", fake_solve_lp_primal_fail)
    with pytest.raises(SolverInfeasibleError) as exc_primal:
        L1QuotientSolver.solve(g, omega)
    assert "Primal L1 quotient solver failed" in str(exc_primal.value)

    # 2. Dual solver fails with non-OPTIMAL status
    call_count = 0
    def fake_solve_lp_dual_fail(c, A, b, max_iter=10000):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            return SimplexResult("INFEASIBLE", Fraction(0), [], [])
        return original_solve_lp(c, A, b, max_iter)

    monkeypatch.setattr(ExactTwoPhaseSimplexSolver, "solve_standard_lp", fake_solve_lp_dual_fail)
    with pytest.raises(SolverInfeasibleError) as exc_dual:
        L1QuotientSolver.solve(g, omega)
    assert "Dual circulation solver failed" in str(exc_dual.value)

    # 3. Nonzero duality gap fault injection (Delta != 0)
    def fake_solve_lp_bad_gap(c, A, b, max_iter=10000):
        res = original_solve_lp(c, A, b, max_iter)
        if len(c) == 2 * len(g.edges):
            perturbed_x = list(res.x)
            perturbed_x[0] += Fraction(1)
            return SimplexResult(res.status, res.obj_val, perturbed_x, res.dual)
        return res

    monkeypatch.setattr(ExactTwoPhaseSimplexSolver, "solve_standard_lp", fake_solve_lp_bad_gap)
    with pytest.raises(DualityGapNonZeroError) as exc_gap:
        L1QuotientSolver.solve(g, omega)
    assert "Duality gap is nonzero" in str(exc_gap.value)

    # 4. Capacity bound exceeded fault injection (|z_e| > w_e)
    # Use zero omega so duality gap is 0 even when z is huge
    def fake_solve_lp_huge_z(c, A, b, max_iter=10000):
        res = original_solve_lp(c, A, b, max_iter)
        if len(c) == 2 * len(g.edges):
            perturbed_x = list(res.x)
            # Make u_0 huge so z_0 = u_0 - w_0 > w_0
            perturbed_x[0] += Fraction(100)
            return SimplexResult(res.status, res.obj_val, perturbed_x, res.dual)
        return res

    monkeypatch.setattr(ExactTwoPhaseSimplexSolver, "solve_standard_lp", fake_solve_lp_huge_z)
    with pytest.raises(CertificateViolationError):
        L1QuotientSolver.solve(g, [0, 0, 0])

    # 5. Circulation divergence nonzero (B^T z != 0)
    def fake_solve_lp_div_nonzero(c, A, b, max_iter=10000):
        res = original_solve_lp(c, A, b, max_iter)
        if len(c) == 2 * len(g.edges):
            # u = w so z = 0, but set z_0 = 1, z_1 = 0, z_2 = 0
            perturbed_x = [w for w in g.weights] + [Fraction(0)] * len(g.edges)
            perturbed_x[0] += Fraction(1)  # z_0 = 1, div on vertex 0 is -1 != 0
            return SimplexResult(res.status, res.obj_val, perturbed_x, res.dual)
        return res

    monkeypatch.setattr(ExactTwoPhaseSimplexSolver, "solve_standard_lp", fake_solve_lp_div_nonzero)
    with pytest.raises(CirculationDivergenceError) as exc_div:
        L1QuotientSolver.solve(g, [0, 0, 0])
    assert "Dual witness divergence is nonzero" in str(exc_div.value)

    monkeypatch.setattr(ExactTwoPhaseSimplexSolver, "solve_standard_lp", original_solve_lp)



def test_sparsify_representative_and_nullspace_branches():
    """Verify nullspace and sparsification edge cases."""
    # nullspace with n == 0
    assert L1QuotientSolver._nullspace_rational([], 0) == []

    # nullspace with full rank (no free variables)
    full_rank_mat = [
        [Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(1)],
    ]
    assert L1QuotientSolver._nullspace_rational(full_rank_mat, 2) == []

    # _sparsify_representative with max_steps=0
    g = DirectedGraph([0, 1, 2, 3], [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)], [1, 1, 1, 1, 1])
    r_init = [Fraction(1)] * 5
    f_init = [Fraction(0)] * 4
    act_verts = [1, 2, 3]
    act_map = {1: 0, 2: 1, 3: 2}
    r_out, _f_out = L1QuotientSolver._sparsify_representative(
        g, r_init, f_init, 0, act_verts, act_map, max_steps=0
    )
    assert r_out == r_init

    # _sparsify_representative where delta_act is all zero (branch 842-843)
    import l1_cohomology
    orig_nullspace = l1_cohomology.L1QuotientSolver._nullspace_rational
    l1_cohomology.L1QuotientSolver._nullspace_rational = staticmethod(lambda A, n: [Fraction(0)] * n)
    try:
        r_out2, _f_out2 = L1QuotientSolver._sparsify_representative(
            g, r_init, f_init, 0, act_verts, act_map
        )
        assert r_out2 == r_init
    finally:
        l1_cohomology.L1QuotientSolver._nullspace_rational = orig_nullspace

    # _sparsify_representative with negative ratios (branch 855->850 and 859-860)
    g_mock = DirectedGraph([0, 1, 2, 3], [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)], [1, 1, 1, 1, 1])
    g_mock.d0 = lambda f: [Fraction(1), Fraction(1), Fraction(1), Fraction(1), Fraction(1)]
    r_neg, _f_neg = L1QuotientSolver._sparsify_representative(
        g_mock, [Fraction(1)] * 5, [Fraction(0)] * 4, 0, act_verts, act_map, max_steps=1
    )
    assert len(r_neg) == 5

    # _sparsify_representative with empty ratio candidates (branch 861-862)
    g_mock.d0 = lambda f: [Fraction(0), Fraction(0), Fraction(0), Fraction(0), Fraction(0)]
    r_empty, _f_empty = L1QuotientSolver._sparsify_representative(
        g_mock, [Fraction(1)] * 5, [Fraction(0)] * 4, 0, act_verts, act_map, max_steps=1
    )
    assert len(r_empty) == 5



def test_l1c_complementary_slackness_branches():
    """Verify complementary slackness branches when r_opt is negative or slackness is violated."""
    g = DirectedGraph.cycle(3, weights=[1, 1, 1])
    omega = [-5, 0, 0]
    receipt = L1QuotientSolver.solve(g, omega)
    assert receipt.satisfies_complementary_slackness
    assert any(re < Fraction(0) for re in receipt.primal_residual)


# ============================================================================
# 8. Peer Review Remediation Regressions (Items 1, 3, 4, 6, 7, 8)
# ============================================================================

def test_theorem_8_weighted_loop_bound_correction():
    """Verify corrected weighted circulation bound M_C = max_e |C_e|/w_e (Item 1).

    Exact counterexample from review:
    A directed 3-cycle with weights w_e = 1/2, cochain omega = (1, 0, 0), and circulation C = (1, 1, 1).
    - Uncorrected printed bound claimed: Phi_1 >= |<C, omega>| / ||w||_infty = 1 / (1/2) = 2.
    - Actual primal L1 quotient norm is Phi_1 = 1/2.
    - Corrected bound: M_C = max_e (|C_e|/w_e) = 1 / (1/2) = 2.
      Phi_1 >= |<C, omega>| / M_C = 1 / 2.
    """
    g = DirectedGraph.cycle(3, weights=[Fraction(1, 2), Fraction(1, 2), Fraction(1, 2)])
    omega = [Fraction(1), Fraction(0), Fraction(0)]
    receipt = L1QuotientSolver.solve(g, omega)

    assert receipt.primal_norm == Fraction(1, 2)
    assert receipt.dual_bound == Fraction(1, 2)

    C = [Fraction(1), Fraction(1), Fraction(1)]
    pairing = sum(C[e] * omega[e] for e in range(3))  # 1
    M_C = max(abs(C[e]) / g.weights[e] for e in range(3))  # 2
    corrected_bound = abs(pairing) / M_C  # 1/2

    # Verify the corrected bound holds with exact equality
    assert receipt.primal_norm >= corrected_bound
    assert corrected_bound == Fraction(1, 2)

    # Verify the old uncorrected bound would falsely assert Phi_1 >= 2
    w_infty = max(g.weights)
    false_bound = abs(pairing) / w_infty
    assert false_bound == Fraction(2)
    assert receipt.primal_norm < false_bound, "Old printed bound was violated by this exact instance!"


def test_quantum_exact_psd_rejection_of_3x3_counterexample():
    """Verify exact rational PSD validator rejects 3x3 matrix with negative eigenvalue (Item 3).

    Matrix: rho = (1/12) * [[4, -3, -3], [-3, 4, -3], [-3, -3, 4]]
    - Trace = 12/12 = 1.
    - Hermitian: real symmetric.
    - Diagonals = 4/12 > 0.
    - All 2x2 principal minors = 16/144 - 9/144 = 7/144 > 0.
    - Eigenvalues: -1/6, 7/12, 7/12.
    The old 2x2-only validator accepted this non-PSD state. The exact LDL^dagger validator must reject it.
    """
    mat = [
        [RationalComplex(Fraction(4, 12), Fraction(0)), RationalComplex(Fraction(-3, 12), Fraction(0)), RationalComplex(Fraction(-3, 12), Fraction(0))],
        [RationalComplex(Fraction(-3, 12), Fraction(0)), RationalComplex(Fraction(4, 12), Fraction(0)), RationalComplex(Fraction(-3, 12), Fraction(0))],
        [RationalComplex(Fraction(-3, 12), Fraction(0)), RationalComplex(Fraction(-3, 12), Fraction(0)), RationalComplex(Fraction(4, 12), Fraction(0))],
    ]
    # Check that 2x2 principal minors are indeed positive
    for j in range(3):
        for k in range(j + 1, 3):
            assert mat[j][j].re * mat[k][k].re > mat[j][k].norm_sq()

    # Must raise NegativeSpectrumError
    with pytest.raises(NegativeSpectrumError) as exc_info:
        QuantumDensityMatrix(mat)
    assert "positive semidefiniteness" in str(exc_info.value)


def test_quantum_exact_psd_acceptance_of_rank_deficient_singular_state():
    """Verify exact rational PSD validator accepts valid singular / rank-deficient state (Item 3)."""
    # 3x3 pure state with amplitudes (1/3, 2/3, 2/3): norm^2 = 1/9 + 4/9 + 4/9 = 1.
    # This state has rank 1, trace 1, and two zero eigenvalues.
    amps = [
        RationalComplex(Fraction(1, 3), Fraction(0)),
        RationalComplex(Fraction(2, 3), Fraction(0)),
        RationalComplex(Fraction(2, 3), Fraction(0)),
    ]
    rho = QuantumDensityMatrix.pure_state(amps)
    assert rho.dim == 3
    assert rho.validate_state() is None


def test_quantum_complex_off_diagonal_coherence():
    """Verify off-diagonal coherence computes complex moduli |z| and does not ignore imaginary parts (Item 4).

    Valid state: rho = 1/2 * [[1, i], [-i, 1]]
    - Trace = 1, Hermitian, rank 1, positive semidefinite.
    - Off-diagonal entries: rho_01 = i/2, |rho_01| = 1/2.
    - Old method summed |Re(rho_01)| = 0.
    - Correct method yields off-diagonal coherence = 1/2, total coherence = 1.
    """
    mat = [
        [RationalComplex(Fraction(1, 2), Fraction(0)), RationalComplex(Fraction(0), Fraction(1, 2))],
        [RationalComplex(Fraction(0), Fraction(-1, 2)), RationalComplex(Fraction(1, 2), Fraction(0))],
    ]
    rho = QuantumDensityMatrix(mat)
    assert rho.dim == 2
    # Off-diagonal coherence must be exactly 1/2 (NOT 0)
    coherence = rho.off_diagonal_l1_coherence()
    assert coherence == Fraction(1, 2)
    assert rho.total_l1_coherence() == Fraction(1)


def test_simplex_solver_iteration_limit_exhaustion():
    """Verify iteration exhaustion raises SolverIterationLimitError instead of false verdicts (Item 7)."""
    # Phase 1 budget exhaustion: A = I_2, b = (1, 1), c = (0, 0) with max_iter=1
    A1 = [
        [Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(1)],
    ]
    b1 = [Fraction(1), Fraction(1)]
    c1 = [Fraction(0), Fraction(0)]
    with pytest.raises(SolverIterationLimitError) as exc1:
        ExactTwoPhaseSimplexSolver.solve_standard_lp(c1, A1, b1, max_iter=1)
    assert "Phase 1 simplex reached iteration limit" in str(exc1.value)

    # Phase 2 budget exhaustion: A = [[1, 1, 1]], b = [1], c = [0, -1, -2] with max_iter=1
    A2 = [[Fraction(1), Fraction(1), Fraction(1)]]
    b2 = [Fraction(1)]
    c2 = [Fraction(0), Fraction(-1), Fraction(-2)]
    with pytest.raises(SolverIterationLimitError) as exc2:
        ExactTwoPhaseSimplexSolver.solve_standard_lp(c2, A2, b2, max_iter=1)
    assert "Phase 2 simplex reached iteration limit" in str(exc2.value)


def test_l1_solver_primal_feasibility_check_and_receipt_validator():
    """Verify primal feasibility equation r = omega + B f enforcement and receipt checker (Item 6)."""
    g = DirectedGraph.cycle(5, weights=[2, 3, 1, 4, 5])
    omega = [Fraction(10), Fraction(-4), Fraction(7), Fraction(1), Fraction(-2)]
    receipt = L1QuotientSolver.solve(g, omega)

    # 1. Standalone checker confirms valid receipt
    assert check_certificate_receipt(receipt, g, omega) is True

    # 2. Injected defect: tampered potential violates primal equation
    corrupted_potential = list(receipt.primal_potential)
    corrupted_potential[1] += Fraction(1)
    corrupted_receipt = L1CertificateReceipt(
        primal_norm=receipt.primal_norm,
        dual_bound=receipt.dual_bound,
        duality_gap=receipt.duality_gap,
        primal_potential=tuple(corrupted_potential),
        primal_residual=receipt.primal_residual,
        dual_circulation=receipt.dual_circulation,
        support_size=receipt.support_size,
        cycle_rank=receipt.cycle_rank,
        satisfies_support_bound=receipt.satisfies_support_bound,
        satisfies_complementary_slackness=receipt.satisfies_complementary_slackness,
        solution_is_integral=receipt.solution_is_integral,
        integrality_theorem_satisfied=receipt.integrality_theorem_satisfied,
        diagnostic_type=receipt.diagnostic_type,
        is_integral=receipt.is_integral,
    )
    with pytest.raises(PrimalFeasibilityError) as exc_tamper:
        check_certificate_receipt(corrupted_receipt, g, omega)
    assert "Primal feasibility failed" in str(exc_tamper.value)

    # 3. Non-integral inputs: separate solution_is_integral from integrality_theorem_satisfied
    g3 = DirectedGraph.cycle(3, weights=[1, 1, 1])
    omega_non_integral = [Fraction(1, 2), Fraction(0), Fraction(0)]
    receipt_non_int = L1QuotientSolver.solve(g3, omega_non_integral)

    # Solution is (1/2, 0, 0), which is NOT integral!
    assert receipt_non_int.solution_is_integral is False
    assert receipt_non_int.is_integral is False
    # But theorem implication (inputs_integral => solution_integral) is satisfied vacuously!
    assert receipt_non_int.integrality_theorem_satisfied is True


def test_simplicial_complex_curvature_residual_vs_closed_residual():
    """Verify diagnostic distinguishes closed residual from non-closed curvature residual (Item 8)."""
    # 2-complex with 1 face (0, 1, 2) and edges (0, 1), (1, 2), (0, 2)
    sc = Simplicial2Complex(
        vertices=[0, 1, 2],
        edges=[(0, 1), (1, 2), (0, 2)],
        faces=[(0, 1, 2)],
    )
    g = DirectedGraph(
        vertices=[0, 1, 2],
        edges=[(0, 1), (1, 2), (0, 2)],
    )

    # omega = (1, 0, 0): d1 omega = 1 != 0 (non-closed curvature on 2-complex)
    omega = [Fraction(1), Fraction(0), Fraction(0)]
    receipt = L1QuotientSolver.solve(g, omega)

    # On graph alone, diagnostic is ClosedResidual (since graph has no 2-faces)
    assert receipt.diagnostic_type == "ClosedResidual"

    # On 2-complex, d1(r) = d1(omega + d0 f) = d1(omega) != 0, so curvature is present
    curv = sc.d1(receipt.primal_residual)
    assert curv != [Fraction(0)]
    # Calling check_certificate_receipt with complex2 confirms CurvatureResidual detection
    with pytest.raises(CertificateViolationError) as exc_diag:
        check_certificate_receipt(receipt, g, omega, complex2=sc)
    assert "CurvatureResidual" in str(exc_diag.value)


def test_check_certificate_receipt_fault_injections():
    """Verify all failure branches in check_certificate_receipt."""
    g = DirectedGraph.triangle()
    omega = [1, 2, 3]
    receipt = L1QuotientSolver.solve(g, omega)

    # 1. Dimension mismatch
    with pytest.raises(CochainDimensionError):
        check_certificate_receipt(receipt, g, [1, 2])

    # 2. Primal norm mismatch
    bad_norm_receipt = L1CertificateReceipt(
        primal_norm=receipt.primal_norm + Fraction(1),
        dual_bound=receipt.dual_bound,
        duality_gap=receipt.duality_gap,
        primal_potential=receipt.primal_potential,
        primal_residual=receipt.primal_residual,
        dual_circulation=receipt.dual_circulation,
        support_size=receipt.support_size,
        cycle_rank=receipt.cycle_rank,
        satisfies_support_bound=receipt.satisfies_support_bound,
        satisfies_complementary_slackness=receipt.satisfies_complementary_slackness,
        solution_is_integral=receipt.solution_is_integral,
        integrality_theorem_satisfied=receipt.integrality_theorem_satisfied,
        diagnostic_type=receipt.diagnostic_type,
    )
    with pytest.raises(CertificateViolationError) as exc_norm:
        check_certificate_receipt(bad_norm_receipt, g, omega)
    assert "Primal norm mismatch" in str(exc_norm.value)

    # 3. Dual divergence nonzero
    bad_div_receipt = L1CertificateReceipt(
        primal_norm=receipt.primal_norm,
        dual_bound=receipt.dual_bound,
        duality_gap=receipt.duality_gap,
        primal_potential=receipt.primal_potential,
        primal_residual=receipt.primal_residual,
        dual_circulation=(Fraction(99), Fraction(0), Fraction(0)),
        support_size=receipt.support_size,
        cycle_rank=receipt.cycle_rank,
        satisfies_support_bound=receipt.satisfies_support_bound,
        satisfies_complementary_slackness=receipt.satisfies_complementary_slackness,
        solution_is_integral=receipt.solution_is_integral,
        integrality_theorem_satisfied=receipt.integrality_theorem_satisfied,
        diagnostic_type=receipt.diagnostic_type,
    )
    with pytest.raises(CirculationDivergenceError):
        check_certificate_receipt(bad_div_receipt, g, omega)

    # 4. Capacity bound exceeded
    # Make circulation valid but exceeding weights
    bad_cap_receipt = L1CertificateReceipt(
        primal_norm=receipt.primal_norm,
        dual_bound=receipt.dual_bound,
        duality_gap=receipt.duality_gap,
        primal_potential=receipt.primal_potential,
        primal_residual=receipt.primal_residual,
        dual_circulation=(Fraction(10), Fraction(10), Fraction(-10)),
        support_size=receipt.support_size,
        cycle_rank=receipt.cycle_rank,
        satisfies_support_bound=receipt.satisfies_support_bound,
        satisfies_complementary_slackness=receipt.satisfies_complementary_slackness,
        solution_is_integral=receipt.solution_is_integral,
        integrality_theorem_satisfied=receipt.integrality_theorem_satisfied,
        diagnostic_type=receipt.diagnostic_type,
    )
    with pytest.raises(CapacityBoundExceededError):
        check_certificate_receipt(bad_cap_receipt, g, omega)

    # 5. Dual bound mismatch
    bad_dual_receipt = L1CertificateReceipt(
        primal_norm=receipt.primal_norm,
        dual_bound=receipt.dual_bound + Fraction(1),
        duality_gap=receipt.duality_gap,
        primal_potential=receipt.primal_potential,
        primal_residual=receipt.primal_residual,
        dual_circulation=receipt.dual_circulation,
        support_size=receipt.support_size,
        cycle_rank=receipt.cycle_rank,
        satisfies_support_bound=receipt.satisfies_support_bound,
        satisfies_complementary_slackness=receipt.satisfies_complementary_slackness,
        solution_is_integral=receipt.solution_is_integral,
        integrality_theorem_satisfied=receipt.integrality_theorem_satisfied,
        diagnostic_type=receipt.diagnostic_type,
    )
    with pytest.raises(CertificateViolationError) as exc_db:
        check_certificate_receipt(bad_dual_receipt, g, omega)
    assert "Dual bound mismatch" in str(exc_db.value)

    # 6. Duality gap mismatch
    bad_gap_receipt = L1CertificateReceipt(
        primal_norm=receipt.primal_norm,
        dual_bound=receipt.dual_bound,
        duality_gap=Fraction(5),
        primal_potential=receipt.primal_potential,
        primal_residual=receipt.primal_residual,
        dual_circulation=receipt.dual_circulation,
        support_size=receipt.support_size,
        cycle_rank=receipt.cycle_rank,
        satisfies_support_bound=receipt.satisfies_support_bound,
        satisfies_complementary_slackness=receipt.satisfies_complementary_slackness,
        solution_is_integral=receipt.solution_is_integral,
        integrality_theorem_satisfied=receipt.integrality_theorem_satisfied,
        diagnostic_type=receipt.diagnostic_type,
    )
    with pytest.raises(DualityGapNonZeroError):
        check_certificate_receipt(bad_gap_receipt, g, omega)

    # 7. Support size mismatch
    bad_supp_receipt = L1CertificateReceipt(
        primal_norm=receipt.primal_norm,
        dual_bound=receipt.dual_bound,
        duality_gap=receipt.duality_gap,
        primal_potential=receipt.primal_potential,
        primal_residual=receipt.primal_residual,
        dual_circulation=receipt.dual_circulation,
        support_size=99,
        cycle_rank=receipt.cycle_rank,
        satisfies_support_bound=receipt.satisfies_support_bound,
        satisfies_complementary_slackness=receipt.satisfies_complementary_slackness,
        solution_is_integral=receipt.solution_is_integral,
        integrality_theorem_satisfied=receipt.integrality_theorem_satisfied,
        diagnostic_type=receipt.diagnostic_type,
    )
    with pytest.raises(CertificateViolationError) as exc_supp:
        check_certificate_receipt(bad_supp_receipt, g, omega)
    assert "Support size mismatch" in str(exc_supp.value)

    # 8. Complementary slackness violations
    # Edge with positive residual r_e > 0 but z_e != w_e
    g_cs = DirectedGraph.cycle(3, weights=[1, 1, 1])
    # r = (1, 0, 0), z = (0, 0, 0), w = (1, 1, 1) -> z_0 = 0 != w_0 = 1
    bad_cs1 = L1CertificateReceipt(
        primal_norm=Fraction(1),
        dual_bound=Fraction(0),
        duality_gap=Fraction(0),  # dummy
        primal_potential=(Fraction(0), Fraction(0), Fraction(0)),
        primal_residual=(Fraction(1), Fraction(0), Fraction(0)),
        dual_circulation=(Fraction(0), Fraction(0), Fraction(0)),
        support_size=1,
        cycle_rank=1,
        satisfies_support_bound=True,
        satisfies_complementary_slackness=True,
        solution_is_integral=True,
        integrality_theorem_satisfied=True,
        diagnostic_type="ClosedResidual",
    )
    with pytest.raises(ComplementarySlacknessError):
        check_certificate_receipt(bad_cs1, g_cs, [1, 0, 0])

    # Edge with negative residual r_e < 0 but z_e != -w_e
    bad_cs2 = L1CertificateReceipt(
        primal_norm=Fraction(1),
        dual_bound=Fraction(0),
        duality_gap=Fraction(0),
        primal_potential=(Fraction(0), Fraction(0), Fraction(0)),
        primal_residual=(Fraction(-1), Fraction(0), Fraction(0)),
        dual_circulation=(Fraction(0), Fraction(0), Fraction(0)),
        support_size=1,
        cycle_rank=1,
        satisfies_support_bound=True,
        satisfies_complementary_slackness=True,
        solution_is_integral=True,
        integrality_theorem_satisfied=True,
        diagnostic_type="ClosedResidual",
    )
    with pytest.raises(ComplementarySlacknessError):
        check_certificate_receipt(bad_cs2, g_cs, [-1, 0, 0])

    # 9. 2-complex exact repair diagnostic check
    sc = Simplicial2Complex(
        vertices=[0, 1, 2],
        edges=[(0, 1), (1, 2), (0, 2)],
        faces=[(0, 1, 2)],
    )
    exact_receipt = L1QuotientSolver.solve(g, [1, 1, 2])
    assert check_certificate_receipt(exact_receipt, g, [1, 1, 2], complex2=sc) is True


def test_quantum_density_matrix_zero_diagonal_with_nonzero_offdiagonal():
    """Verify state with zero diagonal and non-zero off-diagonal raises NegativeSpectrumError."""
    # [[0, 1/2], [1/2, 1]] has Tr = 1, Hermitian, but diag 0 with off-diag 1/2
    mat = [
        [RationalComplex(Fraction(0), Fraction(0)), RationalComplex(Fraction(1, 2), Fraction(0))],
        [RationalComplex(Fraction(1, 2), Fraction(0)), RationalComplex(Fraction(1), Fraction(0))],
    ]
    with pytest.raises(NegativeSpectrumError) as exc:
        QuantumDensityMatrix(mat)
    assert "Zero diagonal entry" in str(exc.value)


def test_quantum_density_matrix_irrational_modulus_coherence():
    """Verify off-diagonal coherence with irrational modulus returns high-precision float."""
    # State with off-diagonal element 1/3 + i/3: |z|^2 = 1/9 + 1/9 = 2/9, which is not a rational square
    # Construct a valid 2x2 state: [[1/2, 1/3 + i/3], [1/3 - i/3, 1/2]]
    # Principal minor: (1/2)*(1/2) - 2/9 = 1/4 - 2/9 = 9/36 - 8/36 = 1/36 > 0 (strictly positive!)
    mat = [
        [RationalComplex(Fraction(1, 2), Fraction(0)), RationalComplex(Fraction(1, 3), Fraction(1, 3))],
        [RationalComplex(Fraction(1, 3), Fraction(-1, 3)), RationalComplex(Fraction(1, 2), Fraction(0))],
    ]
    rho = QuantumDensityMatrix(mat)
    assert rho.dim == 2
    c = rho.off_diagonal_l1_coherence()
    assert isinstance(c, float)
    import math
    expected = math.sqrt(2.0 / 9.0)
    assert abs(c - expected) < 1e-12

    # Also test RationalComplex.modulus() helper
    z = RationalComplex(Fraction(1, 3), Fraction(1, 3))
    assert abs(z.modulus() - expected) < 1e-12
    z_zero = RationalComplex(Fraction(0), Fraction(0))
    assert z_zero.modulus() == Fraction(0)


def test_l1_solver_internal_primal_feasibility_error(monkeypatch):
    """Invasive fault injection: internal solver raises PrimalFeasibilityError if residual corrupted."""
    g = DirectedGraph.triangle()
    omega = [1, 2, 3]

    # Corrupt _sparsify_representative so that it returns an invalid residual
    def fake_sparsify(graph, r_opt, f_opt, root_idx, active_vertices, act_map, max_steps=100):
        corrupted_r = list(r_opt)
        corrupted_r[0] += Fraction(10)  # corrupt!
        return corrupted_r, f_opt

    monkeypatch.setattr(L1QuotientSolver, "_sparsify_representative", fake_sparsify)
    with pytest.raises(PrimalFeasibilityError) as exc:
        L1QuotientSolver.solve(g, omega)
    assert "Primal certificate feasibility equation violated" in str(exc.value)


def test_quantum_psd_complete_pivoting_and_deflation():
    """Verify LDL^dagger complete pivoting swaps rows/cols and handles deflated zero blocks."""
    # 1. Pivoting swap: diagonal element at index 1 (3/4) is strictly larger than at 0 (1/4)
    mat_swap = [
        [RationalComplex(Fraction(1, 4), Fraction(0)), RationalComplex(Fraction(1, 4), Fraction(0))],
        [RationalComplex(Fraction(1, 4), Fraction(0)), RationalComplex(Fraction(3, 4), Fraction(0))],
    ]
    rho_swap = QuantumDensityMatrix(mat_swap)
    assert rho_swap.dim == 2

    # 2. Deflated zero block: 3x3 with one non-zero entry on diagonal (1) and all others zero
    mat_deflated = [
        [RationalComplex(Fraction(1), Fraction(0)), RationalComplex(Fraction(0), Fraction(0)), RationalComplex(Fraction(0), Fraction(0))],
        [RationalComplex(Fraction(0), Fraction(0)), RationalComplex(Fraction(0), Fraction(0)), RationalComplex(Fraction(0), Fraction(0))],
        [RationalComplex(Fraction(0), Fraction(0)), RationalComplex(Fraction(0), Fraction(0)), RationalComplex(Fraction(0), Fraction(0))],
    ]
    rho_deflated = QuantumDensityMatrix(mat_deflated)
    assert rho_deflated.dim == 3


def test_check_certificate_receipt_diagnostic_mismatch():
    """Verify check_certificate_receipt catches diagnostic_type mismatch."""
    g = DirectedGraph.triangle()
    omega = [1, 2, 3]
    receipt = L1QuotientSolver.solve(g, omega)
    sc = Simplicial2Complex(
        vertices=[0, 1, 2],
        edges=[(0, 1), (1, 2), (0, 2)],
        faces=[(0, 1, 2)],
    )

    bad_diag_receipt = L1CertificateReceipt(
        primal_norm=receipt.primal_norm,
        dual_bound=receipt.dual_bound,
        duality_gap=receipt.duality_gap,
        primal_potential=receipt.primal_potential,
        primal_residual=receipt.primal_residual,
        dual_circulation=receipt.dual_circulation,
        support_size=receipt.support_size,
        cycle_rank=receipt.cycle_rank,
        satisfies_support_bound=receipt.satisfies_support_bound,
        satisfies_complementary_slackness=receipt.satisfies_complementary_slackness,
        solution_is_integral=receipt.solution_is_integral,
        integrality_theorem_satisfied=receipt.integrality_theorem_satisfied,
        diagnostic_type="BogusDiagnostic",
    )
    with pytest.raises(CertificateViolationError) as exc:
        check_certificate_receipt(bad_diag_receipt, g, omega, complex2=sc)
    assert "Diagnostic type mismatch" in str(exc.value)


# ============================================================================
# 8. Requirement R3: L^p Family and Schatten-p Solver Verification
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


def test_l2_laplacian_irrational_norm():
    """Verify non-perfect square norm branches to float norm_value."""
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

        l1_harm = sum(abs(x) for x in receipt.harmonic_residual)
        assert l1_harm == Fraction(1)

        d0_f = [h[i] - receipt.harmonic_residual[i] for i in range(n)]
        l1_coboundary = sum(abs(x) for x in d0_f)
        total_l1 = l1_harm + l1_coboundary

        expected_ratio = Fraction(3 * n - 2, n)
        assert total_l1 == expected_ratio


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


def test_review_schatten_entrywise_bound_requires_dimension_factor_for_p_above_two():
    """The 3x3 uniform density matrix refutes the former dimension-free claim."""
    rho = np.ones((3, 3), dtype=np.complex128) / 3
    off_diagonal = rho - np.diag(np.diag(rho))

    schatten_three_cubed = OperatorSchattenPModule.schatten_norm(off_diagonal, 3.0) ** 3
    entrywise_three_cubed = np.sum(np.abs(off_diagonal) ** 3)

    assert np.isclose(schatten_three_cubed, 10 / 27)
    assert np.isclose(entrywise_three_cubed, 6 / 27)
    assert schatten_three_cubed > entrywise_three_cubed
    assert schatten_three_cubed <= 3 * entrywise_three_cubed


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
    tot_1 = OperatorSchattenPModule.total_schatten_p_norm(graph, H, 1.0)
    assert abs(tot_1 - 28.0) < 1e-12

    tot_inf = OperatorSchattenPModule.total_schatten_p_norm(graph, H, float('inf'))
    assert abs(tot_inf - 9.0) < 1e-12


def test_operator_dimension_mismatches():
    """Verify operator module rejects cochains of wrong dimensions."""
    graph = DirectedGraph.triangle()
    with pytest.raises(ValueError, match="0-cochain length"):
        OperatorSchattenPModule.operator_coboundary_d0(graph, [np.eye(2)])

    with pytest.raises(ValueError, match="1-cochain length"):
        OperatorSchattenPModule.total_schatten_p_norm(graph, [np.eye(2)], 2.0)





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


def test_receipt_validator_recomputes_and_rejects_false_labels():
    """Verify check_certificate_receipt catches false satisfies_support_bound and false diagnostic_type."""
    graph = DirectedGraph.triangle()  # V=3, E=3, beta=1 with edges (0,1), (1,2), (0,2)
    omega = [Fraction(1), Fraction(1), Fraction(-1)]

    # Legitimate solve gives residual on 1 edge (support 1 <= beta 1)
    valid_receipt = L1QuotientSolver.solve(graph, omega)
    assert check_certificate_receipt(valid_receipt, graph, omega) is True

    # 1. Tamper satisfies_support_bound to True when support exceeds beta
    from dataclasses import replace
    # Residual (1,1,-1), f=(0,0,0), z=(1,1,-1) is primal-dual optimal with zero gap, but support 3 > beta 1
    bad_supp_receipt = replace(
        valid_receipt,
        primal_potential=(Fraction(0), Fraction(0), Fraction(0)),
        primal_residual=(Fraction(1), Fraction(1), Fraction(-1)),
        dual_circulation=(Fraction(1), Fraction(1), Fraction(-1)),
        primal_norm=Fraction(3),
        dual_bound=Fraction(3),
        duality_gap=Fraction(0),
        support_size=3,
        cycle_rank=1,
        satisfies_support_bound=True,  # False label! (3 <= 1 is False)
        diagnostic_type="ClosedResidual",
    )
    with pytest.raises(CertificateViolationError, match="Support bound predicate mismatch"):
        check_certificate_receipt(bad_supp_receipt, graph, omega)

    # 2. Tamper diagnostic_type to "ExactRepair" when residual is nonzero
    bad_diag_receipt = replace(
        valid_receipt,
        diagnostic_type="ExactRepair",  # False label! (primal_norm > 0 is ClosedResidual)
    )
    with pytest.raises(CertificateViolationError, match="Diagnostic type mismatch"):
        check_certificate_receipt(bad_diag_receipt, graph, omega)


def test_solve_l2_laplacian_large_input_overflow_safe():
    """Verify L2 Laplacian solver does not raise OverflowError on astronomical inputs like 10^160."""
    graph = DirectedGraph(['v0', 'v1', 'v2'], [('v0', 'v1'), ('v1', 'v2'), ('v2', 'v0')])
    receipt = ExactRationalL2LaplacianSolver.solve(graph, [0, 0, 10**160])

    assert receipt.squared_norm == Fraction(10**320, 3)
    assert receipt.is_exact_norm is False
    assert math.isclose(receipt.norm_value, float(10**160) * math.sqrt(1 / 3), rel_tol=1e-12)
    assert receipt.orthogonality_verified is True


def test_quantum_phase_additive_flux_vs_u1_holonomy():
    """Demonstrate that positive real quotient norm Phi_1 does not imply non-trivial U(1) holonomy.

    On an unweighted cycle, omega = (2*pi, 0, 0) gives additive flux Phi_1 = 2*pi,
    while every U(1) phase factor is exp(i * omega_e) = 1, giving trivial holonomy.
    """
    import cmath
    omega_real = [Fraction(2 * 314159, 100000), Fraction(0), Fraction(0)]  # approx 2*pi
    graph = DirectedGraph.triangle()
    receipt = L1QuotientSolver.solve(graph, omega_real)
    assert receipt.primal_norm == Fraction(2 * 314159, 100000)

    # Exact 2*pi phase in U(1)
    phase_factors = [cmath.exp(1j * 2 * math.pi), cmath.exp(1j * 0), cmath.exp(1j * 0)]
    u1_cycle_holonomy = phase_factors[0] * phase_factors[1] * phase_factors[2]
    assert math.isclose(u1_cycle_holonomy.real, 1.0, abs_tol=1e-12)
    assert math.isclose(u1_cycle_holonomy.imag, 0.0, abs_tol=1e-12)


def test_quantum_phase_gauge_invariance_and_branch_winding():
    """Verify Theorem L1C-T8: unitary transformation sign, branch winding, and U(1) holonomy.

    On a directed 3-cycle with vertices [0, 1, 2] and edges [(0, 1), (1, 2), (2, 0)],
    start with pure state |psi> = (|0> + |1> + |2>) / sqrt(3), giving a valid density
    matrix rho = |psi><psi| with positive real off-diagonal coherences rho_uv = 1/3 > 0.
    1. Initial edge phases on E_rho are omega = (0, 0, 0), with real quotient norm Phi_1 = 0.
    2. Diagonal unitary U_theta = diag(e^{-i theta_v}) with theta = (0, 3pi/4, 3pi/2) acts as:
       (U_theta rho U_theta^dagger)_{uv} = e^{i (d_0 theta)_{uv}} rho_{uv}.
       Under incidence (d_0 theta)(u,v) = theta_v - theta_u:
         edge (0,1): theta_1 - theta_0 = 3pi/4
         edge (1,2): theta_2 - theta_1 = 3pi/4
         edge (2,0): theta_0 - theta_2 = -3pi/2
    3. Principal argument extraction Arg(.) in (-pi, pi] wraps -3pi/2 to pi/2, yielding
       principal edge phases omega' = (3pi/4, 3pi/4, pi/2).
    4. Cycle sum around C is 3pi/4 + 3pi/4 + pi/2 = 2pi, producing real quotient norm Phi_1 = 2pi > 0
       solely due to branch cut wrapping on an otherwise gauge-equivalent state.
    5. The gauge-invariant multiplicative U(1) cycle holonomy remains exp(i * 2pi) = 1.0.
    6. Minimizing over integer period shifts k in Z^E (Phi_1^{U(1)}) eliminates the branch winding:
       for k = (0, 0, -1) and f = -theta, ||omega' + d_0 f + 2pi k||_1 = 0.
    """
    import cmath
    import numpy as np

    # 3-cycle graph: V = [0, 1, 2], E = [(0, 1), (1, 2), (2, 0)]
    graph = DirectedGraph(vertices=[0, 1, 2], edges=[(0, 1), (1, 2), (2, 0)])

    # Valid pure state density matrix rho = |psi><psi|
    psi = np.ones(3, dtype=np.complex128) / np.sqrt(3.0)
    rho = np.outer(psi, np.conj(psi))
    assert np.allclose(rho, rho.conj().T)
    assert np.isclose(np.trace(rho).real, 1.0)

    # 1. Initial edge coherences are positive real
    initial_phases = [cmath.phase(rho[u, v]) for (u, v) in graph.edges]
    assert all(math.isclose(ph, 0.0, abs_tol=1e-12) for ph in initial_phases)
    initial_receipt = L1QuotientSolver.solve(graph, [Fraction(0), Fraction(0), Fraction(0)])
    assert initial_receipt.primal_norm == Fraction(0)

    # 2. Diagonal unitary transformation U_theta with theta = (0, 3pi/4, 3pi/2)
    theta = [0.0, 3.0 * math.pi / 4.0, 3.0 * math.pi / 2.0]
    U_theta = np.diag([cmath.exp(-1j * th) for th in theta])
    rho_prime = U_theta @ rho @ U_theta.conj().T

    # Verify unitary sign: (U_theta rho U_theta^dagger)_{uv} = e^{i (d_0 theta)_{uv}} rho_{uv}
    for (u, v) in graph.edges:
        d0_theta_uv = theta[v] - theta[u]
        expected_entry = cmath.exp(1j * d0_theta_uv) * rho[u, v]
        assert np.isclose(rho_prime[u, v], expected_entry, atol=1e-12)

    # 3. Principal branch extraction Arg(.) in (-pi, pi]
    extracted_phases = [cmath.phase(rho_prime[u, v]) for (u, v) in graph.edges]
    # Edge (0, 1): 3pi/4
    assert math.isclose(extracted_phases[0], 3.0 * math.pi / 4.0, abs_tol=1e-12)
    # Edge (1, 2): 3pi/4
    assert math.isclose(extracted_phases[1], 3.0 * math.pi / 4.0, abs_tol=1e-12)
    # Edge (2, 0): -3pi/2 wraps to +pi/2 in principal range (-pi, pi]
    assert math.isclose(extracted_phases[2], math.pi / 2.0, abs_tol=1e-12)

    # 4. Cycle sum and real quotient norm
    cycle_sum = sum(extracted_phases)
    assert math.isclose(cycle_sum, 2.0 * math.pi, abs_tol=1e-12)

    # In real L1 quotient, cycle flux 2*pi enforces Phi_1 >= 2*pi / max |C_e| = 2*pi
    # Using rational representation: (3/4 + 3/4 + 1/2) = 2
    p0 = Fraction(3, 4)
    p1 = Fraction(3, 4)
    p2 = Fraction(1, 2)
    receipt_real = L1QuotientSolver.solve(graph, [p0, p1, p2])
    assert receipt_real.primal_norm == Fraction(2)

    # 5. Multiplicative U(1) cycle holonomy is 1.0 (unaffected by branch choice)
    holonomy_u1 = 1.0 + 0.0j
    for (u, v) in graph.edges:
        holonomy_u1 *= (rho_prime[u, v] / abs(rho_prime[u, v]))
    assert math.isclose(holonomy_u1.real, 1.0, abs_tol=1e-12)
    assert math.isclose(holonomy_u1.imag, 0.0, abs_tol=1e-12)

    # 6. Branch-independent U(1) defect: period shift k = (0, 0, -1) cancels winding
    # omega' + 2pi*k = (3pi/4, 3pi/4, -3pi/2) = d0(theta), so with f = -theta, residual is 0
    k_shift = [0, 0, -1]  # edge (2,0) shifted by -2*pi
    unwrapped_phases = [
        extracted_phases[i] + 2.0 * math.pi * k_shift[i] for i in range(3)
    ]
    # Check that unwrapped_phases == d0(theta)
    d0_theta = [theta[v] - theta[u] for (u, v) in graph.edges]
    for i in range(3):
        assert math.isclose(unwrapped_phases[i], d0_theta[i], abs_tol=1e-12)
    # Residual with f = -theta: unwrapped_phases + d0(f) = d0_theta - d0_theta = 0
    u1_defect = sum(abs(unwrapped_phases[i] - d0_theta[i]) for i in range(3))
    assert math.isclose(u1_defect, 0.0, abs_tol=1e-12)


