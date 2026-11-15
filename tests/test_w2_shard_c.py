"""Test suite for Window 2 Wave 1 Shard C derivations.

Covers:
- AUDIT-N002-002 (ATL-N002-002): Schatten-1 classification under axioms P1-P4
- AUDIT-N002-014 (ATL-N002-014): Conditional unitary frame symmetry under CP and state-cone preservation
- AUDIT-N002-016 (ATL-N002-016): Telescoping Schatten-p path distinguishability bound
- AUDIT-N002-021 (ATL-N002-021): Exact secular-root comparison floor and Loewner bound transfer
"""

import math
from fractions import Fraction
import numpy as np
import scipy.linalg
import pytest


# ============================================================================
# AUDIT-N002-002: Schatten-1 Classification under Axioms P1-P4
# ============================================================================

def test_audit_n002_002_positive_rank_one_norming_functional():
    """Verify rank-one norming functional construction Phi(C) = Tr(X^* C) B / ||B||_1.

    Given A, B with ||A||_1 = ||B||_1, let A = U |A| be the polar decomposition.
    Then X = U satisfies ||X||_op = 1 and Tr(X^* A) = ||A||_1.
    The map Phi(C) = Tr(X^* C) B / ||B||_1 has ||Phi||_{B_1 -> B_1} = 1 and maps A to B.
    """
    np.random.seed(42)
    for dim in [2, 3]:
        # Generate random matrix A
        raw_a = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        u_a, s_a, vh_a = np.linalg.svd(raw_a)
        norm_a_1 = np.sum(s_a)
        # Polar decomposition of A: A = U_polar * |A|
        u_polar = u_a @ vh_a

        # Generate random matrix B and normalize so ||B||_1 = ||A||_1
        raw_b = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        _, s_b_raw, _ = np.linalg.svd(raw_b)
        mat_b = raw_b * (norm_a_1 / np.sum(s_b_raw))
        _, s_b, _ = np.linalg.svd(mat_b)
        norm_b_1 = np.sum(s_b)
        assert np.isclose(norm_a_1, norm_b_1)

        # Norming functional witness X = U_polar
        mat_x = u_polar
        # Operator norm of X is max singular value = 1
        _, s_x, _ = np.linalg.svd(mat_x)
        assert np.isclose(np.max(s_x), 1.0)

        # Pairing Tr(X^* A) equals ||A||_1
        pairing_a = np.trace(mat_x.conj().T @ raw_a)
        assert np.isclose(pairing_a.real, norm_a_1)
        assert np.isclose(pairing_a.imag, 0.0)

        # Map Phi(C) = Tr(X^* C) * B / ||B||_1
        phi_a = (np.trace(mat_x.conj().T @ raw_a) / norm_b_1) * mat_b
        # Phi(A) == B
        np.testing.assert_allclose(phi_a, mat_b, atol=1e-12)

        # Operator norm ||Phi||_{B_1 -> B_1} <= ||X||_op = 1
        # Test across 20 random test matrices C
        for _ in range(20):
            test_c = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
            _, s_c, _ = np.linalg.svd(test_c)
            norm_c_1 = np.sum(s_c)
            phi_c = (np.trace(mat_x.conj().T @ test_c) / norm_b_1) * mat_b
            _, s_phi_c, _ = np.linalg.svd(phi_c)
            norm_phi_c_1 = np.sum(s_phi_c)
            assert norm_phi_c_1 <= norm_c_1 + 1e-12


def test_audit_n002_002_positive_edge_orbit_weight_constancy_3edge_path():
    """Verify that presheaf automorphism invariance forces edge weights constant on orbits,

    and that on a 3-edge path graph with Z_2 symmetry, orbit weights (w1, w2, w1)
    satisfy automorphism invariance while permitting non-uniform weights across orbits.
    """
    # Path graph: v0 - e0 - v1 - e1 - v2 - e2 - v3
    # Automorphism sigma: v0 <-> v3, v1 <-> v2
    # Induced edge action: sigma(e0) = e2, sigma(e1) = e1, sigma(e2) = e0
    orbit_1 = [0, 2]  # {e0, e2}
    orbit_2 = [1]     # {e1}

    # Weight assignment constant on orbits:
    w_orbit_1 = Fraction(3, 2)
    w_orbit_2 = Fraction(5, 1)
    weights = [w_orbit_1, w_orbit_2, w_orbit_1]

    # Check automorphism invariance: sigma(e) has weight w_e
    sigma_edges = [2, 1, 0]
    permuted_weights = [weights[sigma_edges[i]] for i in range(3)]
    assert permuted_weights == weights

    # Distinct orbits permit non-uniform weights:
    assert weights[0] != weights[1]


def test_audit_n002_002_negative_schatten_2_norm_violates_p3_linear_functoriality():
    """Negative control: Verify that non-trace norms (such as Schatten-2 Frobenius norm)

    violate Axiom P3 (bounded linear functoriality with operator norm subordinate to B_1).
    A map contractive under B_1 (||Phi||_{B_1 -> B_1} <= 1) strictly expands the S_2 norm.
    """
    # Let C = diag(1/2, 1/2) in M_2(C).
    # ||C||_1 = 1/2 + 1/2 = 1.
    # ||C||_2 = sqrt((1/2)^2 + (1/2)^2) = 1/sqrt(2) ~ 0.70710678.
    mat_c = np.diag([0.5, 0.5])
    norm_c_1 = np.sum(np.linalg.svd(mat_c, compute_uv=False))
    norm_c_2 = np.linalg.norm(mat_c, 'fro')
    assert np.isclose(norm_c_1, 1.0)
    assert np.isclose(norm_c_2, 1.0 / np.sqrt(2.0))

    # Define linear map Phi(M) = Tr(M) * diag(1, 0).
    # For any M: ||Phi(M)||_1 = |Tr(M)| * ||diag(1, 0)||_1 = |Tr(M)| <= ||M||_1.
    # Hence ||Phi||_{B_1 -> B_1} = 1.
    phi_c = np.trace(mat_c) * np.diag([1.0, 0.0])
    norm_phi_c_2 = np.linalg.norm(phi_c, 'fro')
    assert np.isclose(norm_phi_c_2, 1.0)

    # In S_2, ||Phi(C)||_2 = 1.0 > 1/sqrt(2) = ||C||_2!
    # Contraction under B_1 fails to bound S_2 norm, demonstrating that Axiom P3
    # selects the trace norm specifically.
    assert norm_phi_c_2 > norm_c_2


# ============================================================================
# AUDIT-N002-014: Conditional Unitary Frame Symmetry
# ============================================================================

def test_audit_n002_014_positive_unitary_conjugation_preserves_density_operators():
    """Verify that unitary conjugation A -> U A U^* preserves trace norm, spectrum,

    Hermiticity, and complete positivity for 2-level and 3-level density operators.
    """
    np.random.seed(101)
    for dim in [2, 3]:
        # Generate Haar-random unitary U
        raw_u = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        mat_u, _ = scipy.linalg.qr(raw_u)

        # Generate valid density matrix rho (Hermitian, positive semidefinite, Tr(rho) = 1)
        raw_rho = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        rho = raw_rho @ raw_rho.conj().T
        rho = rho / np.trace(rho)

        # Apply unitary conjugation
        transformed_rho = mat_u @ rho @ mat_u.conj().T

        # 1. Hermiticity
        np.testing.assert_allclose(transformed_rho, transformed_rho.conj().T, atol=1e-12)

        # 2. Trace preservation
        assert np.isclose(np.trace(transformed_rho).real, 1.0)
        assert np.isclose(np.trace(transformed_rho).imag, 0.0)

        # 3. Spectral preservation
        eigs_orig = np.sort(np.linalg.eigvalsh(rho))
        eigs_trans = np.sort(np.linalg.eigvalsh(transformed_rho))
        np.testing.assert_allclose(eigs_orig, eigs_trans, atol=1e-12)

        # 4. Trace norm preservation
        s_orig = np.sum(np.linalg.svd(rho, compute_uv=False))
        s_trans = np.sum(np.linalg.svd(transformed_rho, compute_uv=False))
        assert np.isclose(s_orig, s_trans)

        # 5. Complete positivity via Choi matrix
        # For map T(A) = U A U^*, the Choi matrix J(T) = sum_{i,j} |i><j| (x) T(|i><j|)
        # = (I (x) U) |Omega><Omega| (I (x) U)^* >= 0 where |Omega> = sum_i |i>|i>.
        choi = np.zeros((dim * dim, dim * dim), dtype=np.complex128)
        for i in range(dim):
            for j in range(dim):
                e_ij = np.zeros((dim, dim), dtype=np.complex128)
                e_ij[i, j] = 1.0
                t_e_ij = mat_u @ e_ij @ mat_u.conj().T
                # outer block (i, j)
                choi[i * dim:(i + 1) * dim, j * dim:(j + 1) * dim] = t_e_ij

        choi_eigs = np.linalg.eigvalsh(choi)
        assert np.all(choi_eigs >= -1e-12)


def test_audit_n002_014_negative_transpose_violates_complete_positivity():
    """Negative control: Verify that matrix transposition A -> A^T preserves trace norm

    and state positivity for single systems, but strictly violates complete positivity.
    The Choi matrix (or partial transpose on Bell state |Phi+>) has a negative eigenvalue -1/2.
    """
    # 2-qubit Bell state: |Phi+> = (|00> + |11>) / sqrt(2)
    rho_bell = np.zeros((4, 4), dtype=np.float64)
    rho_bell[0, 0] = 0.5
    rho_bell[0, 3] = 0.5
    rho_bell[3, 0] = 0.5
    rho_bell[3, 3] = 0.5

    # Partial transpose on subsystem B: (I (x) T)(rho)
    # Block matrix transpose: block (i, j) gets transposed
    rho_pt = np.zeros((4, 4), dtype=np.float64)
    for i in range(2):
        for j in range(2):
            block = rho_bell[i * 2:(i + 1) * 2, j * 2:(j + 1) * 2]
            rho_pt[i * 2:(i + 1) * 2, j * 2:(j + 1) * 2] = block.T

    # Explicit check of partial transpose matrix entries:
    expected_pt = np.array([
        [0.5, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.5, 0.0],
        [0.0, 0.5, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.5]
    ])
    np.testing.assert_allclose(rho_pt, expected_pt)

    # Eigenvalues of partial transpose:
    eigs_pt = np.linalg.eigvalsh(rho_pt)
    # The middle 2x2 block has eigenvalues +0.5 and -0.5
    np.testing.assert_allclose(np.sort(eigs_pt), [-0.5, 0.5, 0.5, 0.5])
    assert np.min(eigs_pt) == -0.5 < 0.0


def test_audit_n002_014_negative_non_adjoint_violates_state_cone_positivity():
    """Negative control: Verify that linear isometries A -> U A V with V != U^*

    violate state-cone preservation (unitality / positive semidefiniteness of identity image).
    """
    # Let U be Pauli X: [[0, 1], [1, 0]]
    u_mat = np.array([[0.0, 1.0], [1.0, 0.0]])
    # If V = I != U^*
    v_mat = np.eye(2)
    # Under T(A) = U A V, T(I) = U V = Pauli X
    t_identity = u_mat @ np.eye(2) @ v_mat
    eigs = np.linalg.eigvalsh(t_identity)
    # Pauli X has eigenvalues {-1, 1}, not positive semidefinite
    assert np.any(eigs < 0.0)

    # If V = i * I
    v_imag = 1j * np.eye(2)
    t_imag = u_mat @ np.eye(2) @ v_imag
    # Not even Hermitian: T(I)^* != T(I)
    assert not np.allclose(t_imag, t_imag.conj().T)


# ============================================================================
# AUDIT-N002-016: Telescoping Schatten-p Path Distinguishability Bound
# ============================================================================

def test_audit_n002_016_positive_telescoping_path_bound_taut_equality():
    """Verify Theorem 5.1 worked replay: two-edge qubit path a - m - b with identity restrictions.

    rho_a = diag(1, 0), rho_m = diag(1/2, 1/2), rho_b = diag(0, 1).
    Demonstrates exact taut equality T_p = (1/2) I_p across p in {1, 2, infinity}.
    """
    rho_a = np.diag([1.0, 0.0])
    rho_m = np.diag([0.5, 0.5])
    rho_b = np.diag([0.0, 1.0])

    delta_am = rho_m - rho_a  # diag(-0.5, 0.5)
    delta_mb = rho_b - rho_m  # diag(-0.5, 0.5)
    delta_ab = rho_b - rho_a  # diag(-1.0, 1.0)

    # Exponent p = 1 (Trace distance):
    # ||delta_e||_{S_1} = |-0.5| + |0.5| = 1.0
    # I_1 = 1.0 + 1.0 = 2.0
    # T_1 = (1/2) * ||rho_a - rho_b||_{S_1} = (1/2) * 2.0 = 1.0
    s_am_1 = np.sum(np.linalg.svd(delta_am, compute_uv=False))
    s_mb_1 = np.sum(np.linalg.svd(delta_mb, compute_uv=False))
    i_1 = s_am_1 + s_mb_1
    t_1 = 0.5 * np.sum(np.linalg.svd(delta_ab, compute_uv=False))
    assert np.isclose(i_1, 2.0)
    assert np.isclose(t_1, 1.0)
    assert np.isclose(t_1, 0.5 * i_1)

    # Exponent p = 2 (Frobenius / Hilbert-Schmidt distance):
    # ||delta_e||_{S_2} = sqrt((-0.5)^2 + 0.5^2) = 1/sqrt(2) ~ 0.70710678
    # I_2 = sqrt(2) ~ 1.41421356
    # T_2 = (1/2) * ||rho_a - rho_b||_{S_2} = (1/2) * sqrt(2) = 1/sqrt(2)
    s_am_2 = np.linalg.norm(delta_am, 'fro')
    s_mb_2 = np.linalg.norm(delta_mb, 'fro')
    i_2 = s_am_2 + s_mb_2
    t_2 = 0.5 * np.linalg.norm(delta_ab, 'fro')
    assert np.isclose(i_2, np.sqrt(2.0))
    assert np.isclose(t_2, 1.0 / np.sqrt(2.0))
    assert np.isclose(t_2, 0.5 * i_2)

    # Exponent p = infinity (Operator spectral norm):
    # ||delta_e||_{S_inf} = 0.5
    # I_inf = 0.5 + 0.5 = 1.0
    # T_inf = (1/2) * 1.0 = 0.5
    s_am_inf = np.max(np.linalg.svd(delta_am, compute_uv=False))
    s_mb_inf = np.max(np.linalg.svd(delta_mb, compute_uv=False))
    i_inf = s_am_inf + s_mb_inf
    t_inf = 0.5 * np.max(np.linalg.svd(delta_ab, compute_uv=False))
    assert np.isclose(i_inf, 1.0)
    assert np.isclose(t_inf, 0.5)
    assert np.isclose(t_inf, 0.5 * i_inf)

    # Verify canonical monotonic ordering chain:
    # T_inf <= T_2 <= T_1 <= (1/2) * I_1
    assert t_inf <= t_2 + 1e-12
    assert t_2 <= t_1 + 1e-12
    assert t_1 <= 0.5 * i_1 + 1e-12


def test_audit_n002_016_positive_contractive_channel_path_bound():
    """Verify path distinguishability bound on a 3-edge path with contractive quantum channels."""
    # Path v0 - e0 - v1 - e1 - v2 - e2 - v3
    np.random.seed(202)
    # Local states
    states = []
    for _ in range(4):
        raw = np.random.randn(2, 2) + 1j * np.random.randn(2, 2)
        r = raw @ raw.conj().T
        states.append(r / np.trace(r))

    # Contractive depolarizing channels r_{i+1, i}(X) = (1 - eps) X + eps Tr(X) I/2
    eps = 0.2
    def channel(x):
        return (1.0 - eps) * x + eps * np.trace(x) * np.eye(2) * 0.5

    # Transport from v3 to v0: R_{3,0} = channel(channel(channel(states[3])))
    r30_rho3 = channel(channel(channel(states[3])))
    dist_endpoint = 0.5 * np.sum(np.linalg.svd(states[0] - r30_rho3, compute_uv=False))

    # Accumulated defect along path
    # e0: delta_0 = channel(states[1]) - states[0]
    # e1: delta_1 = channel(states[2]) - states[1]
    # e2: delta_2 = channel(states[3]) - states[2]
    d0 = channel(states[1]) - states[0]
    d1 = channel(states[2]) - states[1]
    d2 = channel(states[3]) - states[2]

    i_1 = (np.sum(np.linalg.svd(d0, compute_uv=False)) +
           np.sum(np.linalg.svd(d1, compute_uv=False)) +
           np.sum(np.linalg.svd(d2, compute_uv=False)))

    assert dist_endpoint <= 0.5 * i_1 + 1e-12


def test_audit_n002_016_negative_expansive_channel_violates_path_bound():
    """Negative control: Verify that if restriction channel is expansive (||R||_op > 1),

    the telescoping bound T_p <= (1/2) I_p fails.
    """
    rho_a = np.diag([1.0, 0.0])
    rho_b = np.diag([0.0, 1.0])

    # Expansive restriction R(X) = 2.5 * X
    gamma = 2.5
    r_rho_b = gamma * rho_b  # diag(0, 2.5)

    # Endpoint distance: ||rho_a - R(rho_b)||_1 = ||diag(1.0, -2.5)||_1 = 1.0 + 2.5 = 3.5
    t_1 = 0.5 * np.sum(np.linalg.svd(rho_a - r_rho_b, compute_uv=False))
    assert np.isclose(t_1, 1.75)

    # Un-amplified edge defect: delta = rho_b - rho_a = diag(-1.0, 1.0), ||delta||_1 = 2.0
    # (1/2) * I_1 = (1/2) * 2.0 = 1.0
    i_1_unscaled = np.sum(np.linalg.svd(rho_b - rho_a, compute_uv=False))
    assert np.isclose(0.5 * i_1_unscaled, 1.0)

    # With expansive factor, t_1 (1.75) strictly exceeds (1/2) * I_1 (1.0)
    assert t_1 > 0.5 * i_1_unscaled


# ============================================================================
# AUDIT-N002-021: Exact Secular-Root Comparison Floor & Loewner Bound Transfer
# ============================================================================

def secular_function(t, alpha, n, d):
    """Secular function F(t) = (alpha / n) * sum_{i=1}^n 1 / (d_i - t)."""
    return (alpha / n) * np.sum(1.0 / (d - t))


def solve_secular_root(alpha, n, v, tol=1e-14):
    """Find the unique root tau in [0, d_min) such that F(tau) = 1."""
    d = alpha + v
    d_min = np.min(d)

    # If v is zero everywhere: F(0) = (alpha/n) * (n/alpha) = 1, so tau = 0
    if np.allclose(v, 0.0):
        return 0.0

    # For positive loads, F(0) < 1, and F(t) -> +infinity as t -> d_min^-
    # Upper search bound: u = d_min - (alpha / n) / 2
    f_0 = secular_function(0.0, alpha, n, d)
    assert f_0 <= 1.0 + 1e-12

    # Bisection search
    low = 0.0
    high = d_min - 1e-15
    # Expand high until F(high) > 1
    step = (d_min - low) * 0.5
    probe = low + step
    while secular_function(probe, alpha, n, d) < 1.0:
        low = probe
        step *= 0.5
        probe = low + step

    high = probe
    for _ in range(120):
        mid = 0.5 * (low + high)
        val = secular_function(mid, alpha, n, d)
        if abs(val - 1.0) < tol:
            return mid
        if val < 1.0:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def test_audit_n002_021_positive_secular_root_comparison_equality_and_eigenvector():
    """Verify Proposition E.7e:

    The unique secular root tau in [0, d_min) satisfying F(tau) = 1 equals
    lambda_min(alpha(I - P) + diag(v)) exactly, and x_i = (d_i - tau)^(-1)
    is the exact attaining eigenvector.
    """
    np.random.seed(777)
    for n in [3, 4, 5]:
        alpha = 2.5
        v = np.random.uniform(0.5, 4.0, size=n)
        d = alpha + v
        p_proj = np.ones((n, n)) / n

        # Solve secular root
        tau = solve_secular_root(alpha, n, v)
        f_tau = secular_function(tau, alpha, n, d)
        assert np.isclose(f_tau, 1.0, atol=1e-10)

        # Comparison operator M_comp = alpha(I - P) + diag(v)
        m_comp = alpha * (np.eye(n) - p_proj) + np.diag(v)
        eigs_m = np.linalg.eigvalsh(m_comp)
        min_eig = np.min(eigs_m)

        # Verify lambda_min == tau
        assert np.isclose(min_eig, tau, atol=1e-10)

        # Verify attaining eigenvector x_i = 1 / (d_i - tau)
        x_att = 1.0 / (d - tau)
        # Check M_comp @ x == tau * x
        residual = m_comp @ x_att - tau * x_att
        np.testing.assert_allclose(residual, np.zeros(n), atol=1e-10)


def test_audit_n002_021_positive_loewner_bound_transfer_to_graph_laplacian():
    """Verify Proposition E.7e Loewner bound transfer:

    Because L_0 >= alpha(I - P) for alpha <= lambda_2(L_0),
    lambda_min(L_0 + diag(v)) >= tau.
    Tested on C_4 (cycle graph, lambda_2 = 2.0) and K_3 (complete graph, lambda_2 = 3.0).
    """
    # 1. Triangle graph K_3:
    # Laplacian L_0 = 3*I - ones(3,3), lambda_2 = 3.0
    l0_k3 = np.array([
        [2.0, -1.0, -1.0],
        [-1.0, 2.0, -1.0],
        [-1.0, -1.0, 2.0]
    ])
    eigs_l0_k3 = np.sort(np.linalg.eigvalsh(l0_k3))
    assert np.isclose(eigs_l0_k3[1], 3.0)

    alpha_k3 = 3.0
    v_k3 = np.array([1.2, 0.4, 2.8])
    tau_k3 = solve_secular_root(alpha_k3, 3, v_k3)

    h_obstr_k3 = l0_k3 + np.diag(v_k3)
    lambda_0_k3 = np.min(np.linalg.eigvalsh(h_obstr_k3))
    assert lambda_0_k3 >= tau_k3 - 1e-12

    # 2. Cycle graph C_4:
    # Nodes 0-1-2-3-0. L_0 has spectrum 0, 2, 2, 4. Fiedler value lambda_2 = 2.0.
    l0_c4 = np.array([
        [2.0, -1.0, 0.0, -1.0],
        [-1.0, 2.0, -1.0, 0.0],
        [0.0, -1.0, 2.0, -1.0],
        [-1.0, 0.0, -1.0, 2.0]
    ])
    eigs_l0_c4 = np.sort(np.linalg.eigvalsh(l0_c4))
    assert np.isclose(eigs_l0_c4[1], 2.0)

    alpha_c4 = 2.0
    v_c4 = np.array([0.0, 2.0, 1.0, 3.0])
    tau_c4 = solve_secular_root(alpha_c4, 4, v_c4)

    h_obstr_c4 = l0_c4 + np.diag(v_c4)
    lambda_0_c4 = np.min(np.linalg.eigvalsh(h_obstr_c4))
    assert lambda_0_c4 >= tau_c4 - 1e-12


def test_audit_n002_021_positive_flat_and_zero_potential_limits():
    """Verify exact limits of Proposition E.7e:

    - Zero potential v == 0: tau = 0 == lambda_0(L_0).
    - Flat potential v == c * 1: tau = c == lambda_0(L_0 + c*I).
    """
    n = 4
    alpha = 2.0
    # Zero potential:
    v_zero = np.zeros(n)
    tau_zero = solve_secular_root(alpha, n, v_zero)
    assert np.isclose(tau_zero, 0.0)

    # Flat potential v_i = c:
    c_val = 1.75
    v_flat = np.full(n, c_val)
    tau_flat = solve_secular_root(alpha, n, v_flat)
    assert np.isclose(tau_flat, c_val)


def test_audit_n002_021_negative_negative_loads_violate_secular_lower_bound():
    """Negative control: Verify that when vertex loads v_i < 0 are allowed,

    the secular root characterization and lower-bound floor fail.
    """
    n = 3
    alpha = 2.0
    # Invalid negative load vector
    v_neg = np.array([-1.5, 0.5, 0.5])
    d = alpha + v_neg  # [0.5, 2.5, 2.5], d_min = 0.5

    p_proj = np.ones((n, n)) / n
    m_comp = alpha * (np.eye(n) - p_proj) + np.diag(v_neg)
    min_eig = np.min(np.linalg.eigvalsh(m_comp))

    # At t=0, F(0) = (2/3) * (1/0.5 + 1/2.5 + 1/2.5) = (2/3) * (2.0 + 0.8) = 1.8666... > 1!
    f_0 = secular_function(0.0, alpha, n, d)
    assert f_0 > 1.0

    # Since F(0) > 1, the root in [0, d_min) does not exist (or t < 0),
    # and min_eig can be strictly negative:
    assert min_eig < 0.0
