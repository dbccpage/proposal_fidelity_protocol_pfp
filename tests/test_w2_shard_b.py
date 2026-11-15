"""
Executable verification for Window 2 Wave 1 Shard B Derivations (Note 001).

Derivations:
- AUDIT-N001-014: Secondary selection in the p -> 1+ limit via weighted entropy minimization (ATL-N001-014)
- AUDIT-N001-016: Integral cut-lattice optimum and total unimodularity integrality (ATL-N001-016)
- AUDIT-N001-017: Discrete Bianchi identity and coboundary nilpotency d1 d0 = 0 (ATL-N001-017)
- AUDIT-N001-018: Schatten-p quantum quotient defect and non-commutative Hölder bounds (ATL-N001-018)

AuthorityEffect: None.
"""

from fractions import Fraction
import itertools
import math
import numpy as np
import pytest
from scipy.optimize import minimize


# ============================================================================
# Helpers for ATL-N001-014: p -> 1+ Entropy Selection
# ============================================================================

def evaluate_p_dirichlet(potential, edges, weights, omega, p):
    """Evaluate J_p(f) = (1/p) * sum_e w_e |omega_e + (d0 f)_e|^p with f[0] = 0."""
    full_potential = [0.0] + list(potential)
    val = 0.0
    for idx, (u, v) in enumerate(edges):
        r_e = omega[idx] + (full_potential[v] - full_potential[u])
        val += weights[idx] * (abs(r_e) ** p)
    return val / p


def evaluate_residuals(potential, edges, omega):
    """Compute residuals r_e = omega_e + (d0 f)_e with f[0] = 0."""
    full_potential = [0.0] + list(potential)
    return [omega[idx] + (full_potential[v] - full_potential[u]) for idx, (u, v) in enumerate(edges)]


def evaluate_l1_norm(potential, edges, weights, omega):
    """Compute ||omega + d0 f||_{1, w}."""
    res = evaluate_residuals(potential, edges, omega)
    return sum(w * abs(r) for w, r in zip(weights, res))


def evaluate_weighted_entropy(potential, edges, weights, omega):
    """Compute weighted entropy E(f) = sum_e w_e |r_e| log |r_e| with 0 log 0 = 0."""
    res = evaluate_residuals(potential, edges, omega)
    val = 0.0
    for w, r in zip(weights, res):
        ar = abs(r)
        if ar > 1e-15:
            val += w * ar * math.log(ar)
    return val


# ============================================================================
# Tests for ATL-N001-014 (AUDIT-N001-014)
# ============================================================================

def test_n001_014_p_to_1_selection_convergence_positive():
    """
    Positive Control: As p -> 1+, the unique p-Laplacian minimizer converges
    to the unique weighted entropy minimizer on the L1 optimal set M_1.
    """
    # 3-cycle with vertices 0, 1, 2 and edges (0,1), (1,2), (2,0)
    edges = [(0, 1), (1, 2), (2, 0)]
    weights = [1.0, 1.0, 1.0]
    omega = [2.0, 2.0, 2.0]  # total flux = 6.0

    # On unweighted triangle, all non-negative residuals with r0+r1+r2=6 achieve min L1 norm = 6.
    # The unique entropy minimizer on this simplex is r = (2, 2, 2), which corresponds to f = (0, 0, 0).
    p_values = [2.0, 1.5, 1.2, 1.1, 1.05, 1.01]
    f_stars = []

    for p in p_values:
        res = minimize(
            lambda f: evaluate_p_dirichlet(f, edges, weights, omega, p),
            x0=[0.5, -0.5],
            method="BFGS",
            tol=1e-6,
        )
        assert res.success or res.status == 2  # Found stationary point within float precision
        f_stars.append(res.x)

    # Check convergence of potential to f_ent = [0.0, 0.0]
    final_f = f_stars[-1]
    assert np.allclose(final_f, [0.0, 0.0], atol=1e-5)

    # Check convergence of residuals to (2.0, 2.0, 2.0)
    final_res = evaluate_residuals(final_f, edges, omega)
    assert np.allclose(final_res, [2.0, 2.0, 2.0], atol=1e-5)

    # Check L1 norm attainment
    l1_val = evaluate_l1_norm(final_f, edges, weights, omega)
    assert abs(l1_val - 6.0) < 1e-5

    # Check entropy value E(f) = 3 * (2 * log(2)) = 6 * log(2)
    expected_entropy = 6.0 * math.log(2.0)
    actual_entropy = evaluate_weighted_entropy(final_f, edges, weights, omega)
    assert abs(actual_entropy - expected_entropy) < 1e-5


def test_n001_014_asymptotic_gamma_expansion():
    """
    Positive Control: Verify the Taylor / Gamma-expansion:
    (J_p(f) - ||r||_{1,w}) / (p - 1) -> E(f) - ||r||_{1,w} as p -> 1+.
    """
    edges = [(0, 1), (1, 2), (2, 0)]
    weights = [1.5, 2.0, 2.5]
    omega = [1.0, 3.0, 2.0]
    test_f = [0.4, -0.2]

    l1_val = evaluate_l1_norm(test_f, edges, weights, omega)
    entropy_val = evaluate_weighted_entropy(test_f, edges, weights, omega)
    target_derivative = entropy_val - l1_val

    # Finite difference quotients as p -> 1+
    quotients = []
    for delta in [0.05, 0.01, 0.001, 0.0001]:
        p = 1.0 + delta
        jp = evaluate_p_dirichlet(test_f, edges, weights, omega, p)
        quotients.append((jp - l1_val) / delta)

    # Check convergence to target derivative
    assert abs(quotients[-1] - target_derivative) < 1e-3
    assert abs(quotients[-1] - quotients[-2]) < abs(quotients[-2] - quotients[-3])


def test_n001_014_strict_convexity_on_optimal_face():
    """
    Positive Control: Verify strict midpoint convexity of E(f) on the optimal face M_1.
    """
    edges = [(0, 1), (1, 2), (2, 0)]
    weights = [1.0, 1.0, 1.0]
    omega = [2.0, 2.0, 2.0]

    # Two distinct potentials in M_1:
    # f_a gives r = [3, 2, 1], f_b gives r = [1, 2, 3]
    f_a = [1.0, 1.0]    # r = [2+1, 2+1-1, 2-1] = [3, 2, 1]
    f_b = [-1.0, -1.0]  # r = [2-1, 2-1+1, 2+1] = [1, 2, 3]

    assert abs(evaluate_l1_norm(f_a, edges, weights, omega) - 6.0) < 1e-12
    assert abs(evaluate_l1_norm(f_b, edges, weights, omega) - 6.0) < 1e-12

    ent_a = evaluate_weighted_entropy(f_a, edges, weights, omega)
    ent_b = evaluate_weighted_entropy(f_b, edges, weights, omega)

    f_mid = [0.5 * (f_a[0] + f_b[0]), 0.5 * (f_a[1] + f_b[1])]
    ent_mid = evaluate_weighted_entropy(f_mid, edges, weights, omega)

    # Strict convexity: E((f_a + f_b)/2) < (E(f_a) + E(f_b)) / 2
    avg_ent = 0.5 * (ent_a + ent_b)
    assert ent_mid < avg_ent
    assert avg_ent - ent_mid > 0.1  # Significant gap


def test_n001_014_negative_control_non_positive_weight():
    """
    Negative Control: Non-positive weights permit un-coercive unbounded descent.
    """
    edges = [(0, 1), (1, 2)]
    weights = [1.0, -2.0]  # Negative weight on edge 1
    omega = [1.0, 1.0]

    # With negative weight, scaling f[1] sends J_p to -infinity
    vals = [evaluate_p_dirichlet([0.0, s], edges, weights, omega, p=1.5) for s in [10.0, 100.0, 1000.0, 10000.0]]
    assert vals[3] < vals[2] < vals[1] < vals[0]
    assert vals[3] < -1e5  # Unbounded below


def test_n001_014_negative_control_ungauged_non_uniqueness():
    """
    Negative Control: Without gauge fixing (fixing root f0 = 0), potentials are not unique.
    """
    edges = [(0, 1), (1, 2)]
    omega = [1.0, -1.0]
    # For any constant shift c, d0(f + c 1) = d0(f), so J_p is flat along the constant vector
    f1 = [1.0, 2.0, 3.0]
    f2 = [11.0, 12.0, 13.0]
    d0_f1 = [f1[v] - f1[u] for u, v in edges]
    d0_f2 = [f2[v] - f2[u] for u, v in edges]
    assert d0_f1 == d0_f2


# ============================================================================
# Helpers for ATL-N001-016: Total Unimodularity and Integer Attainment
# ============================================================================

def build_reduced_incidence_matrix(num_vertices, edges, root_vertex=0):
    """
    Construct reduced incidence matrix B_red of size |E| x (|V| - 1),
    deleting the root vertex column.
    Convention: edge (u, v) has -1 at u, +1 at v.
    """
    non_root_vertices = [v for v in range(num_vertices) if v != root_vertex]
    v_to_col = {v: idx for idx, v in enumerate(non_root_vertices)}
    matrix = np.zeros((len(edges), len(non_root_vertices)), dtype=int)
    for e_idx, (u, v) in enumerate(edges):
        if u in v_to_col:
            matrix[e_idx, v_to_col[u]] = -1
        if v in v_to_col:
            matrix[e_idx, v_to_col[v]] = 1
    return matrix


def is_totally_unimodular(matrix):
    """
    Test total unimodularity by evaluating all square submatrix determinants.
    Returns True if every square submatrix determinant is in {-1, 0, 1}.
    """
    rows, cols = matrix.shape
    for k in range(1, min(rows, cols) + 1):
        for row_comb in itertools.combinations(range(rows), k):
            for col_comb in itertools.combinations(range(cols), k):
                submat = matrix[np.ix_(row_comb, col_comb)]
                det = int(round(np.linalg.det(submat)))
                if det not in (-1, 0, 1):
                    return False
    return True


# ============================================================================
# Tests for ATL-N001-016 (AUDIT-N001-016)
# ============================================================================

def test_n001_016_reduced_incidence_total_unimodularity_positive():
    """
    Positive Control: Verify that reduced incidence matrices for triangle, 4-cycle,
    and line graphs are strictly totally unimodular (all square subdeterminants in {-1, 0, 1}).
    """
    # 1. Triangle graph
    edges_triangle = [(0, 1), (1, 2), (0, 2)]
    b_tri = build_reduced_incidence_matrix(3, edges_triangle, root_vertex=0)
    assert is_totally_unimodular(b_tri)

    # 2. 4-cycle graph
    edges_cycle4 = [(0, 1), (1, 2), (2, 3), (3, 0)]
    b_c4 = build_reduced_incidence_matrix(4, edges_cycle4, root_vertex=0)
    assert is_totally_unimodular(b_c4)

    # 3. 4-vertex line graph
    edges_line = [(0, 1), (1, 2), (2, 3)]
    b_line = build_reduced_incidence_matrix(4, edges_line, root_vertex=0)
    assert is_totally_unimodular(b_line)


def test_n001_016_integer_attainment_exact_simplex_positive():
    """
    Positive Control: Solve the exact rational L1 quotient problem with integer data
    and verify that optimal potential and residuals are strictly integral.
    """
    import sys
    sys.path.insert(0, "atlas/archive/non_pfp/001_l1_native_cohomology/code")
    from l1_cohomology import DirectedGraph, L1QuotientSolver

    # Triangle graph with integer weights and integer cochain
    g_tri = DirectedGraph.triangle(weights=[3, 4, 5])
    omega_tri = [7, -11, 13]
    receipt_tri = L1QuotientSolver.solve(g_tri, omega_tri)

    assert receipt_tri.is_integral
    for r in receipt_tri.primal_residual:
        assert isinstance(r, Fraction) and r.denominator == 1
    for f in receipt_tri.primal_potential:
        assert isinstance(f, Fraction) and f.denominator == 1

    # 4-cycle graph with integer data
    g_c4 = DirectedGraph.cycle(4, weights=[2, 3, 2, 4])
    omega_c4 = [5, -3, 7, 1]
    receipt_c4 = L1QuotientSolver.solve(g_c4, omega_c4)

    assert receipt_c4.is_integral
    for r in receipt_c4.primal_residual:
        assert r.denominator == 1
    for f in receipt_c4.primal_potential:
        assert f.denominator == 1


def test_n001_016_negative_control_fractional_data():
    """
    Negative Control: Non-integral cochain data (e.g. half-integers) produces fractional
    optimal solutions, proving that integrality requires integer data.
    """
    import sys
    sys.path.insert(0, "atlas/archive/non_pfp/001_l1_native_cohomology/code")
    from l1_cohomology import DirectedGraph, L1QuotientSolver

    g = DirectedGraph.triangle(weights=[1, 1, 1])
    # Non-integral cochain with denominator 2
    omega_frac = [Fraction(1, 2), Fraction(1, 2), Fraction(1, 2)]
    receipt = L1QuotientSolver.solve(g, omega_frac)

    # Some potential or residual must have non-trivial denominator
    denominators = [r.denominator for r in receipt.primal_residual] + [f.denominator for f in receipt.primal_potential]
    assert any(d > 1 for d in denominators)


def test_n001_016_negative_control_non_unimodular_matrix():
    """
    Negative Control: Non-totally-unimodular constraint matrices (e.g. odd cycle hypergraph)
    produce non-integer vertex determinants.
    """
    # 3-odd cycle incidence matrix with all positive entries
    non_tu_matrix = np.array([
        [1, 1, 0],
        [0, 1, 1],
        [1, 0, 1]
    ], dtype=int)
    det = int(round(np.linalg.det(non_tu_matrix)))
    assert det == 2
    assert not is_totally_unimodular(non_tu_matrix)


# ============================================================================
# Tests for ATL-N001-017 (AUDIT-N001-017)
# ============================================================================

def test_n001_017_discrete_bianchi_nilpotency_triangle_positive():
    """
    Positive Control: For a 2-simplicial triangle complex, D1 D2 = 0 and d1 d0 = 0.
    Curvature d1(d0 phi) vanishes for all vertex potentials phi.
    """
    # Vertices: 0, 1, 2. Edges: (0,1), (1,2), (0,2). Face: (0,1,2).
    # Boundary D1: |V| x |E|, D2: |E| x |F|
    D1 = np.array([
        [-1,  0, -1],  # v0
        [ 1, -1,  0],  # v1
        [ 0,  1,  1]   # v2
    ], dtype=int)

    D2 = np.array([
        [ 1],   # e01
        [ 1],   # e12
        [-1]    # e02 (oriented 0->2)
    ], dtype=int)

    # Boundary squared vanishes identically
    boundary_composite = D1 @ D2
    assert np.all(boundary_composite == 0)

    # Coboundaries d0 = D1.T, d1 = D2.T
    d0 = D1.T
    d1 = D2.T
    coboundary_composite = d1 @ d0
    assert np.all(coboundary_composite == 0)

    # For random potentials
    for phi in [[0, 0, 0], [1, -5, 7], [-100, 42, 99]]:
        phi_vec = np.array(phi, dtype=int)
        edge_cochain = d0 @ phi_vec
        face_curvature = d1 @ edge_cochain
        assert np.all(face_curvature == 0)


def test_n001_017_discrete_bianchi_nilpotency_plaquette_positive():
    """
    Positive Control: For a 4-vertex square lattice plaquette cell,
    the boundary composite D1 D2 and coboundary d1 d0 vanish identically.
    """
    # Vertices: 0, 1, 2, 3. Edges: (0,1), (1,2), (2,3), (0,3). Plaquette: 0123.
    D1 = np.array([
        [-1,  0,  0, -1],  # v0
        [ 1, -1,  0,  0],  # v1
        [ 0,  1, -1,  0],  # v2
        [ 0,  0,  1,  1]   # v3
    ], dtype=int)

    D2 = np.array([
        [ 1],  # e01
        [ 1],  # e12
        [ 1],  # e23
        [-1]   # e03
    ], dtype=int)

    assert np.all(D1 @ D2 == 0)
    assert np.all(D2.T @ D1.T == 0)

    # Random lattice gauge potentials
    phi = np.array([13, -7, 21, 5], dtype=int)
    assert (D2.T @ (D1.T @ phi))[0] == 0


def test_n001_017_discrete_bianchi_nilpotency_5cycle_positive():
    """
    Positive Control: For a 5-cycle loop, the telescoping boundary sum is identically zero.
    """
    # Vertices: 0, 1, 2, 3, 4. Edges: (0,1), (1,2), (2,3), (3,4), (0,4).
    D1 = np.array([
        [-1,  0,  0,  0, -1],
        [ 1, -1,  0,  0,  0],
        [ 0,  1, -1,  0,  0],
        [ 0,  0,  1, -1,  0],
        [ 0,  0,  0,  1,  1]
    ], dtype=int)

    D2 = np.array([[1], [1], [1], [1], [-1]], dtype=int)

    assert np.all(D1 @ D2 == 0)
    assert np.all(D2.T @ D1.T == 0)


def test_n001_017_circulation_orthogonality():
    """
    Positive Control: For every 1-cycle z with D1 z = 0, <z, d0 phi> = 0 for all phi.
    """
    # 4-cycle loop circulation z = [1, 1, 1, -1]
    z = np.array([1, 1, 1, -1], dtype=int)
    D1 = np.array([
        [-1,  0,  0, -1],
        [ 1, -1,  0,  0],
        [ 0,  1, -1,  0],
        [ 0,  0,  1,  1]
    ], dtype=int)
    assert np.all(D1 @ z == 0)

    for phi in [[1, 2, 3, 4], [0, -10, 5, 2], [100, 100, 100, 100]]:
        phi_vec = np.array(phi, dtype=int)
        d0_phi = D1.T @ phi_vec
        assert np.dot(z, d0_phi) == 0


def test_n001_017_negative_control_orientation_inversion():
    """
    Negative Control: Inverting an edge orientation in face boundary destroys nilpotency (D1 D2 != 0).
    """
    D1 = np.array([
        [-1,  0, -1],
        [ 1, -1,  0],
        [ 0,  1,  1]
    ], dtype=int)

    # Inverted sign on e02: [1, 1, +1]^T instead of [1, 1, -1]^T
    D2_corrupt = np.array([[1], [1], [1]], dtype=int)

    composite = D1 @ D2_corrupt
    assert not np.all(composite == 0)
    assert np.array_equal(composite, np.array([[-2], [0], [2]]))


# ============================================================================
# Helpers for ATL-N001-018: Schatten-p Operator Calculus
# ============================================================================

def schatten_p_norm(matrix, p):
    """Compute Schatten-p norm ||A||_{S_p} for a complex matrix."""
    singular_values = np.linalg.svd(matrix, compute_uv=False)
    if p == 1.0:
        return float(np.sum(singular_values))
    elif math.isinf(p):
        return float(np.max(singular_values)) if len(singular_values) > 0 else 0.0
    else:
        return float(np.sum(singular_values ** p) ** (1.0 / p))


def polar_dual_maximizer(matrix, p):
    """
    Construct polar dual witness B_opt in S_q satisfying ||B_opt||_{S_q} = 1
    and |Tr(A^dagger B_opt)| = ||A||_{S_p}.
    """
    u, s, vh = np.linalg.svd(matrix)
    norm_p = schatten_p_norm(matrix, p)
    if norm_p < 1e-15:
        return np.zeros_like(matrix)
    s_dual = (s ** (p - 1.0)) / (norm_p ** (p - 1.0))
    return u @ np.diag(s_dual) @ vh


# ============================================================================
# Tests for ATL-N001-018 (AUDIT-N001-018)
# ============================================================================

def test_n001_018_schatten_holder_inequality_and_polar_attainment_positive():
    """
    Positive Control: Verify non-commutative Hölder inequality |Tr(A^dagger B)| <= ||A||_{S_p} ||B||_{S_q}
    and exact attainment by polar dual witness B_opt.
    """
    np.random.seed(42)
    d = 3
    for p in [1.2, 1.5, 2.0, 3.5, 4.0]:
        q = p / (p - 1.0)
        A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        B = np.random.randn(d, d) + 1j * np.random.randn(d, d)

        norm_A_p = schatten_p_norm(A, p)
        norm_B_q = schatten_p_norm(B, q)

        # Hölder inequality
        tr_AB = abs(np.trace(A.conj().T @ B))
        assert tr_AB <= norm_A_p * norm_B_q + 1e-12

        # Polar witness attainment
        B_opt = polar_dual_maximizer(A, p)
        norm_B_opt_q = schatten_p_norm(B_opt, q)
        assert abs(norm_B_opt_q - 1.0) < 1e-11

        tr_opt = abs(np.trace(A.conj().T @ B_opt))
        assert abs(tr_opt - norm_A_p) < 1e-11


def test_n001_018_operator_cochain_weak_duality_positive():
    """
    Positive Control: For operator-valued cochains and divergence-free dual circulation Y (d0* Y = 0),
    the pairing Re Tr <Y, H> is gauge-invariant and lower-bounds ||H - d0 F||_{p, w}.
    """
    np.random.seed(123)
    d = 2
    # 3-cycle graph
    edges = [(0, 1), (1, 2), (2, 0)]
    weights = [1.0, 1.0, 1.0]
    p = 2.0
    q = 2.0

    # Operator cochain H_e
    H = [np.random.randn(d, d) + 1j * np.random.randn(d, d) for _ in edges]

    # Circulation Y: uniform matrix M along the cycle so that at every vertex:
    # v0: Y_{20} - Y_{01} = M - M = 0
    # v1: Y_{01} - Y_{12} = M - M = 0
    # v2: Y_{12} - Y_{20} = M - M = 0
    M = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    Y = [M, M, M]

    # Normalize Y so that ||Y||_{q, w*} = (sum_e w_e^{-q/p} ||Y_e||_q^q)^{1/q} <= 1
    total_norm_q = (sum(schatten_p_norm(Y_e, q) ** q for Y_e in Y)) ** (1.0 / q)
    Y = [Y_e / total_norm_q for Y_e in Y]
    assert abs((sum(schatten_p_norm(Y_e, q) ** q for Y_e in Y)) ** (1.0 / q) - 1.0) < 1e-11

    # Invariance under gauge shifts F
    F = [np.random.randn(d, d) + 1j * np.random.randn(d, d) for _ in range(3)]
    # d0 F: e=(u, v) -> F_v - F_u
    d0_F = [F[v] - F[u] for u, v in edges]
    H_shifted = [H[i] - d0_F[i] for i in range(len(edges))]

    pairing_original = sum(np.trace(Y[i].conj().T @ H[i]).real for i in range(len(edges)))
    pairing_shifted = sum(np.trace(Y[i].conj().T @ H_shifted[i]).real for i in range(len(edges)))

    assert abs(pairing_original - pairing_shifted) < 1e-11

    # Weak duality bound: |Re Tr <Y, H>| <= ||H - d0 F||_{p, w}
    norm_H_shifted_p = (sum(schatten_p_norm(H_shifted[i], p) ** p for i in range(len(edges)))) ** (1.0 / p)
    assert abs(pairing_shifted) <= norm_H_shifted_p + 1e-11


def test_n001_018_offdiagonal_coherence_bounds():
    """
    Positive Control: Test off-diagonal coherence bounds:
    - For 1 <= p <= 2: ||A||_{S_p} <= (sum_{u != v} |A_{uv}|^p)^{1/p}
    - For 2 <= p <= inf: ||A||_{S_p} <= d^{1 - 2/p} (sum_{u != v} |A_{uv}|^p)^{1/p}
    """
    np.random.seed(777)
    d = 4
    # Create density matrix rho
    raw = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    rho = raw @ raw.conj().T
    rho /= np.trace(rho)

    A = rho.copy()
    np.fill_diagonal(A, 0.0)

    # 1. Test p in [1, 2]
    for p in [1.0, 1.3, 1.7, 2.0]:
        norm_sp = schatten_p_norm(A, p)
        entrywise_lp = (np.sum(np.abs(A) ** p)) ** (1.0 / p)
        assert norm_sp <= entrywise_lp + 1e-12

    # At p=1, ||A||_1 <= C_l1(rho)
    c_l1 = np.sum(np.abs(A))
    assert schatten_p_norm(A, 1.0) <= c_l1 + 1e-12

    # 2. Test p >= 2 with dimension factor d^{1 - 2/p}
    for p in [2.5, 4.0, 10.0]:
        norm_sp = schatten_p_norm(A, p)
        dim_factor = d ** (1.0 - 2.0 / p)
        entrywise_lp = (np.sum(np.abs(A) ** p)) ** (1.0 / p)
        bound = dim_factor * entrywise_lp
        assert norm_sp <= bound + 1e-12


def test_n001_018_negative_control_non_circulation_gauge_variance():
    """
    Negative Control: A non-divergence-free operator field (d0* Y != 0) is gauge-variant,
    failing to lower-bound the quotient defect.
    """
    d = 2
    edges = [(0, 1), (1, 2), (2, 0)]
    H = [np.eye(d) for _ in edges]

    # Non-circulation Y: divergence at v0 is Y_{20} - Y_{01} != 0
    Y = [np.eye(d), np.zeros((d, d)), np.zeros((d, d))]

    F_zero = [np.zeros((d, d)) for _ in range(3)]
    F_shift = [np.eye(d), np.zeros((d, d)), np.zeros((d, d))]

    d0_F_shift = [F_shift[v] - F_shift[u] for u, v in edges]
    H_shifted = [H[i] - d0_F_shift[i] for i in range(len(edges))]

    pairing_0 = sum(np.trace(Y[i].conj().T @ H[i]).real for i in range(len(edges)))
    pairing_shift = sum(np.trace(Y[i].conj().T @ H_shifted[i]).real for i in range(len(edges)))

    # Non-circulation gives different pairings under gauge shift!
    assert abs(pairing_0 - pairing_shift) > 0.5


def test_n001_018_negative_control_p_above_2_dimension_factor_required():
    """
    Negative Control: For p > 2, the entrywise bound WITHOUT dimension factor
    d^{1 - 2/p} fails on dense unitary matrices.
    """
    # Hadamard-type off-diagonal matrix
    d = 4
    # Real symmetric Hadamard matrix scaled
    H = np.array([
        [ 0,  1,  1,  1],
        [ 1,  0,  1, -1],
        [ 1,  1,  0, -1],
        [ 1, -1, -1,  0]
    ], dtype=float)

    p = 4.0
    norm_sp = schatten_p_norm(H, p)
    raw_entrywise = (np.sum(np.abs(H) ** p)) ** (1.0 / p)

    # Without dimension factor, raw_entrywise < norm_sp
    # With dimension factor d^{1 - 2/p} = 4^{0.5} = 2, bound holds
    assert norm_sp > raw_entrywise
    assert norm_sp <= 2.0 * raw_entrywise
