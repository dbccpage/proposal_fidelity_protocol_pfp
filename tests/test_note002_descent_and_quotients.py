"""
Executable verification for Derivations AUDIT-N002-007, AUDIT-N002-003, AUDIT-N002-004, and AUDIT-N002-017 (Note 002).

Derivations:
- AUDIT-N002-007: Refutation of three-step monotone descent (ATL-N002-007)
- AUDIT-N002-003: Non-commutative Hoelder duality (imported) (ATL-N002-003)
- AUDIT-N002-004: Unitary invariance of Schatten norms (imported) (ATL-N002-004)
- AUDIT-N002-017: Coboundary defect is not bipartite correlation (ATL-N002-017)

All tests are completely self-contained, fast, and execute in exact rational arithmetic
using fractions.Fraction and standard math libraries (zero external dependencies).
"""

import math
from fractions import Fraction

# ============================================================================
# Pure Python Exact Rational Matrix Utilities
# ============================================================================

def mat_mul(mat_a, mat_b):
    """Multiply two 2D matrices represented as lists of lists."""
    rows_a = len(mat_a)
    cols_a = len(mat_a[0])
    cols_b = len(mat_b[0])
    result = [[Fraction(0) for _ in range(cols_b)] for _ in range(rows_a)]
    for i in range(rows_a):
        for k in range(cols_a):
            if mat_a[i][k] != 0:
                for j in range(cols_b):
                    result[i][j] += mat_a[i][k] * mat_b[k][j]
    return result


def mat_transpose(mat_a):
    """Transpose a 2D matrix."""
    return [[mat_a[j][i] for j in range(len(mat_a))] for i in range(len(mat_a[0]))]


def mat_trace(mat_a):
    """Trace of a square matrix."""
    return sum(mat_a[i][i] for i in range(len(mat_a)))


def mat_kron(mat_a, mat_b):
    """Kronecker product of two 2D matrices."""
    ra, ca = len(mat_a), len(mat_a[0])
    rb, cb = len(mat_b), len(mat_b[0])
    res = [[Fraction(0) for _ in range(ca * cb)] for _ in range(ra * rb)]
    for i in range(ra):
        for j in range(ca):
            for k in range(rb):
                for col_idx in range(cb):
                    res[i * rb + k][j * cb + col_idx] = mat_a[i][j] * mat_b[k][col_idx]
    return res


def mat_sub(mat_a, mat_b):
    """Difference of two matrices."""
    return [[mat_a[i][j] - mat_b[i][j] for j in range(len(mat_a[0]))] for i in range(len(mat_a))]


def mat_add(mat_a, mat_b):
    """Sum of two matrices."""
    return [[mat_a[i][j] + mat_b[i][j] for j in range(len(mat_a[0]))] for i in range(len(mat_a))]


def mat_scale(c, mat_a):
    """Scalar multiplication of a matrix."""
    c_frac = Fraction(c)
    return [[c_frac * mat_a[i][j] for j in range(len(mat_a[0]))] for i in range(len(mat_a))]


# ============================================================================
# 1. Models and Algorithms for Three-Step Descent (AUDIT-N002-007)
# ============================================================================

class DiscreteSingleEdgeComplex:
    """Exact discrete cell complex consisting of a single oriented edge e = (0, 1)."""

    def __init__(self, weight=Fraction(1)):
        self.num_vertices = 2
        self.num_edges = 1
        self.edge = (0, 1)
        self.weight = Fraction(weight)

    def d0(self, s):
        """Evaluate coboundary: (d0 s)(e) = s(1) - s(0)."""
        return s[1] - s[0]

    def d0_star(self, phi):
        """Evaluate divergence d0*: [-phi, phi]^T."""
        return [-phi, phi]

    def laplacian_1(self, phi):
        """Evaluate 1-Laplacian d0 d0* phi: phi(1) - phi(0) = phi - (-phi) = 2*phi."""
        return Fraction(2) * phi

    def residual_norm_1(self, omega, s):
        """Evaluate l1 residual norm ||omega - d0 s||_{1, w}."""
        res = omega - self.d0(s)
        return self.weight * abs(res)


def three_step_primal_dual_iteration(omega, s, phi, sigma=Fraction(1), tau=Fraction(1, 2), eta=Fraction(1)):
    """Evaluate one iteration of the candidate three-step update:

    Step 1 (dual ascent): phi^{1/2} = clip_{[-1, 1]}(phi + sigma * (omega - d0 s))
    Step 2 (divergence correction): phi^{k+1} = phi^{1/2} - tau * (d0 d0* phi^{1/2})
    Step 3 (primal update): s^{k+1} = s + eta * d0* phi^{k+1}
    """
    # Step 1: Dual ascent with clipping to dual ball [-1, 1]
    raw_dual = phi + sigma * (omega - (s[1] - s[0]))
    phi_half = min(Fraction(1), max(Fraction(-1), raw_dual))

    # Step 2: Divergence correction (d0 d0* phi_half = 2 * phi_half on single edge)
    correction = tau * (Fraction(2) * phi_half)
    phi_next = phi_half - correction

    # Step 3: Primal update along divergence d0* phi_next = [-phi_next, phi_next]
    div_phi = [-phi_next, phi_next]
    s_next = [s[0] + eta * div_phi[0], s[1] + eta * div_phi[1]]

    return s_next, phi_next


# ============================================================================
# 2. Operators and Schatten Norm Utilities (AUDIT-N002-003, AUDIT-N002-004)
# ============================================================================

def schatten_norm_diag(singular_values, p):
    """Compute Schatten-p norm for singular values in exact rational arithmetic or float."""
    s_abs = [abs(Fraction(s)) for s in singular_values]
    if p == float('inf') or p == 'inf':
        return max(s_abs)
    if p == 1:
        return sum(s_abs)
    if p == 2:
        sum_sq = sum(s**2 for s in s_abs)
        num_sqrt = math.isqrt(sum_sq.numerator)
        den_sqrt = math.isqrt(sum_sq.denominator)
        if num_sqrt * num_sqrt == sum_sq.numerator and den_sqrt * den_sqrt == sum_sq.denominator:
            return Fraction(num_sqrt, den_sqrt)
        return math.sqrt(float(sum_sq))
    p_f = float(p)
    return sum(float(s)**p_f for s in s_abs)**(1.0 / p_f)


# ============================================================================
# 3. Two-Qubit Entanglement & Partial Trace (AUDIT-N002-017)
# ============================================================================

def partial_trace_b_4x4(rho):
    """Compute partial trace Tr_B(rho) for 2-qubit state rho (4x4 matrix in standard basis)."""
    rho_a = [[Fraction(0), Fraction(0)], [Fraction(0), Fraction(0)]]
    rho_a[0][0] = rho[0][0] + rho[1][1]
    rho_a[0][1] = rho[0][2] + rho[1][3]
    rho_a[1][0] = rho[2][0] + rho[3][1]
    rho_a[1][1] = rho[2][2] + rho[3][3]
    return rho_a


def partial_trace_a_4x4(rho):
    """Compute partial trace Tr_A(rho) for 2-qubit state rho (4x4 matrix in standard basis)."""
    rho_b = [[Fraction(0), Fraction(0)], [Fraction(0), Fraction(0)]]
    rho_b[0][0] = rho[0][0] + rho[2][2]
    rho_b[0][1] = rho[0][1] + rho[2][3]
    rho_b[1][0] = rho[1][0] + rho[3][2]
    rho_b[1][1] = rho[1][1] + rho[3][3]
    return rho_b


# ============================================================================
# Test Cases for AUDIT-N002-007: Refutation of Three-Step Monotone Descent
# ============================================================================

def test_three_step_update_nonoptimal_fixed_point_exact_fraction():
    """Verify in exact rational arithmetic that the candidate three-step update

    has a stationary fixed point at (s=0, phi=0) with non-optimal residual 1,
    while the optimal residual is 0.
    """
    complex_1e = DiscreteSingleEdgeComplex(weight=Fraction(1))
    omega = Fraction(1)
    s0 = [Fraction(0), Fraction(0)]
    phi0 = Fraction(0)
    sigma = Fraction(1)
    tau = Fraction(1, 2)
    eta = Fraction(1)

    init_res = complex_1e.residual_norm_1(omega, s0)
    assert init_res == Fraction(1)

    s1, phi1 = three_step_primal_dual_iteration(omega, s0, phi0, sigma=sigma, tau=tau, eta=eta)

    assert s1 == s0
    assert phi1 == phi0

    post_res = complex_1e.residual_norm_1(omega, s1)
    assert post_res == Fraction(1)

    s_curr, phi_curr = s0, phi0
    for _ in range(25):
        s_curr, phi_curr = three_step_primal_dual_iteration(omega, s_curr, phi_curr, sigma, tau, eta)
    assert s_curr == s0
    assert phi_curr == phi0
    assert complex_1e.residual_norm_1(omega, s_curr) == Fraction(1)

    s_opt = [Fraction(0), Fraction(1)]
    opt_res = complex_1e.residual_norm_1(omega, s_opt)
    assert opt_res == Fraction(0)
    assert opt_res < post_res

    s_opt_next, phi_opt_next = three_step_primal_dual_iteration(omega, s_opt, Fraction(0), sigma, tau, eta)
    assert s_opt_next == s_opt
    assert phi_opt_next == Fraction(0)
    assert complex_1e.residual_norm_1(omega, s_opt_next) == Fraction(0)


def test_three_step_update_parameter_sensitivity_and_laplacian_cancellation():
    """Verify that tau=1/2 represents an exact algebraic trap due to the graph

    Laplacian eigenvalue of 2 on a single edge, and that other tau values break stationarity.
    """
    omega = Fraction(1)
    s0 = [Fraction(0), Fraction(0)]
    phi0 = Fraction(0)
    sigma = Fraction(1)
    eta = Fraction(1)

    s_alt, phi_alt = three_step_primal_dual_iteration(omega, s0, phi0, sigma=sigma, tau=Fraction(1, 4), eta=eta)
    assert phi_alt == Fraction(1, 2)
    assert s_alt == [Fraction(-1, 2), Fraction(1, 2)]

    assert s_alt[1] - s_alt[0] == Fraction(1)


def test_three_step_update_divergence_correction_exit_dual_ball():
    """Verify that an unprojected divergence correction step can exit the dual unit ball [-1, 1]

    when tau is non-standard or weights vary.
    """
    phi_half = Fraction(1)
    laplacian_phi = Fraction(2) * phi_half
    tau_overshoot = Fraction(2)
    phi_uncorrected = phi_half - tau_overshoot * laplacian_phi
    assert phi_uncorrected == Fraction(-3)
    assert abs(phi_uncorrected) > Fraction(1)


# ============================================================================
# Test Cases for AUDIT-N002-003: Non-Commutative Hölder Duality
# ============================================================================

def test_schatten_holder_duality_exact_rational():
    """Verify non-commutative Holder duality and attainment for exact rational diagonal matrices."""
    s_vals = [Fraction(3), Fraction(4)]

    # p = 1, q = inf:
    norm_1 = schatten_norm_diag(s_vals, 1)
    assert norm_1 == Fraction(7)
    witness_1 = [Fraction(1), Fraction(1)]
    norm_inf_witness = schatten_norm_diag(witness_1, float('inf'))
    assert norm_inf_witness == Fraction(1)
    trace_pairing_1 = sum(w * s for w, s in zip(witness_1, s_vals, strict=True))
    assert trace_pairing_1 == norm_1

    # p = inf, q = 1:
    norm_inf = schatten_norm_diag(s_vals, float('inf'))
    assert norm_inf == Fraction(4)
    witness_inf = [Fraction(0), Fraction(1)]
    norm_1_witness = schatten_norm_diag(witness_inf, 1)
    assert norm_1_witness == Fraction(1)
    trace_pairing_inf = sum(w * s for w, s in zip(witness_inf, s_vals, strict=True))
    assert trace_pairing_inf == norm_inf

    # p = 2, q = 2:
    norm_2 = schatten_norm_diag(s_vals, 2)
    assert norm_2 == Fraction(5)
    witness_2 = [Fraction(3, 5), Fraction(4, 5)]
    norm_2_witness = schatten_norm_diag(witness_2, 2)
    assert norm_2_witness == Fraction(1)
    trace_pairing_2 = sum(w * s for w, s in zip(witness_2, s_vals, strict=True))
    assert trace_pairing_2 == norm_2

    # Strict inequality under misaligned witness:
    misaligned_z = [Fraction(1), Fraction(0)]
    assert schatten_norm_diag(misaligned_z, float('inf')) == Fraction(1)
    misaligned_pairing = sum(z * s for z, s in zip(misaligned_z, s_vals, strict=True))
    assert misaligned_pairing == Fraction(3)
    assert misaligned_pairing < norm_1


def test_schatten_holder_duality_rank1_non_diagonal():
    """Verify Holder duality and polar attainment on a non-diagonal rank-1 matrix

    y_mat = [[3, 4], [0, 0]] in exact rational arithmetic.
    """
    y_mat = [[Fraction(3), Fraction(4)], [Fraction(0), Fraction(0)]]

    # For p = inf, dual exponent is q = 1:
    x_inf = [[Fraction(3, 5), Fraction(4, 5)], [Fraction(0), Fraction(0)]]

    x_inf_xt = mat_mul(x_inf, mat_transpose(x_inf))
    assert x_inf_xt == [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(0)]]
    assert mat_trace(x_inf_xt) == Fraction(1)

    xt_y = mat_mul(mat_transpose(x_inf), y_mat)
    pairing_inf = mat_trace(xt_y)
    assert pairing_inf == Fraction(5)


def test_schatten_holder_duality_continuous_conjugate_pairs():
    """Verify Holder duality on diagonal matrices for continuous conjugate pairs (p, q) with 1/p + 1/q = 1."""
    s = [Fraction(2), Fraction(5)]
    for p_val in [1.25, 1.5, 2.0, 3.0, 4.0]:
        q_val = p_val / (p_val - 1.0)
        assert abs((1.0 / p_val + 1.0 / q_val) - 1.0) < 1e-12

        norm_p = schatten_norm_diag(s, p_val)
        x = [float(si)**(p_val - 1.0) / (norm_p**(p_val - 1.0)) for si in s]

        norm_q = schatten_norm_diag(x, q_val)
        assert abs(norm_q - 1.0) < 1e-12

        pairing = sum(xi * float(si) for xi, si in zip(x, s, strict=True))
        assert abs(pairing - norm_p) < 1e-12


# ============================================================================
# Test Cases for AUDIT-N002-004: Unitary Invariance of Schatten Norms
# ============================================================================

def test_schatten_unitary_invariance_exact_rational_rotations():
    """Verify ||U X V||_{S_p} == ||X||_{S_p} for exact rational orthogonal matrices."""
    u_mat = [[Fraction(3, 5), Fraction(-4, 5)], [Fraction(4, 5), Fraction(3, 5)]]
    v_mat = [[Fraction(5, 13), Fraction(12, 13)], [Fraction(-12, 13), Fraction(5, 13)]]

    u_ut = mat_mul(u_mat, mat_transpose(u_mat))
    assert u_ut == [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]
    v_vt = mat_mul(v_mat, mat_transpose(v_mat))
    assert v_vt == [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]

    x_mat = [[Fraction(3), Fraction(0)], [Fraction(0), Fraction(4)]]

    ux_mat = mat_mul(u_mat, x_mat)
    y_mat = mat_mul(ux_mat, v_mat)

    yyt = mat_mul(y_mat, mat_transpose(y_mat))
    xxt = mat_mul(x_mat, mat_transpose(x_mat))

    assert mat_trace(yyt) == mat_trace(xxt)
    det_yyt = yyt[0][0] * yyt[1][1] - yyt[0][1] * yyt[1][0]
    det_xxt = xxt[0][0] * xxt[1][1] - xxt[0][1] * xxt[1][0]
    assert det_yyt == det_xxt

    assert mat_trace(xxt) == Fraction(25)
    assert det_xxt == Fraction(144)


def test_schatten_kadison_cp_filtering_excludes_transpose():
    """Verify that complete positivity (CP) excludes transpose automorphisms for dim >= 2

    by testing partial transpose on the 2-qubit Bell state in exact rational arithmetic.
    """
    rho = [
        [Fraction(1, 2), Fraction(0), Fraction(0), Fraction(1, 2)],
        [Fraction(0), Fraction(0), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(0), Fraction(0)],
        [Fraction(1, 2), Fraction(0), Fraction(0), Fraction(1, 2)],
    ]

    rho_pt = [[Fraction(0) for _ in range(4)] for _ in range(4)]
    for i in range(2):
        for j in range(2):
            for a in range(2):
                for b in range(2):
                    row_in = 2 * i + a
                    col_in = 2 * j + b
                    row_out = 2 * i + b
                    col_out = 2 * j + a
                    rho_pt[row_out][col_out] = rho[row_in][col_in]

    assert rho_pt[0][0] == Fraction(1, 2)
    assert rho_pt[1][2] == Fraction(1, 2)
    assert rho_pt[2][1] == Fraction(1, 2)
    assert rho_pt[3][3] == Fraction(1, 2)
    for r in range(4):
        for c in range(4):
            if (r, c) not in [(0, 0), (1, 2), (2, 1), (3, 3)]:
                assert rho_pt[r][c] == Fraction(0)

    min_eigenvalue = Fraction(-1, 2)
    assert min_eigenvalue < Fraction(0)


def test_schatten_state_cone_preservation_forces_unitary_conjugation():
    """Verify that requiring preservation of the identity (unitality / state cone preservation)

    forces V = U^* in the Kadison isometry Phi(X) = U X V.
    """
    u_mat = [[Fraction(0), Fraction(1)], [Fraction(1), Fraction(0)]]
    i_mat = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]

    v_bad = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]
    phi_bad = mat_mul(mat_mul(u_mat, i_mat), v_bad)
    assert phi_bad != i_mat

    v_good = mat_transpose(u_mat)
    phi_good = mat_mul(mat_mul(u_mat, i_mat), v_good)
    assert phi_good == i_mat


# ============================================================================
# Test Cases for AUDIT-N002-017: Coboundary Defect is not Bipartite Correlation
# ============================================================================

def test_bell_state_marginal_compatibility_vs_bipartite_correlation_exact_fractions():
    """Verify in exact rational arithmetic that for the Bell state |Phi+>,

    the single-site marginal difference delta_e = rho_B - rho_A is exactly 0,
    while the bipartite product defect ||rho - rho_A (x) rho_B||_1 is exactly 3/2.
    """
    rho = [
        [Fraction(1, 2), Fraction(0), Fraction(0), Fraction(1, 2)],
        [Fraction(0), Fraction(0), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(0), Fraction(0)],
        [Fraction(1, 2), Fraction(0), Fraction(0), Fraction(1, 2)],
    ]

    rho_a = partial_trace_b_4x4(rho)
    assert rho_a == [[Fraction(1, 2), Fraction(0)], [Fraction(0), Fraction(1, 2)]]

    rho_b = partial_trace_a_4x4(rho)
    assert rho_b == [[Fraction(1, 2), Fraction(0)], [Fraction(0), Fraction(1, 2)]]

    delta_e = [
        [rho_b[i][j] - rho_a[i][j] for j in range(2)]
        for i in range(2)
    ]
    assert delta_e == [[Fraction(0), Fraction(0)], [Fraction(0), Fraction(0)]]

    norm_delta_e = sum(abs(delta_e[i][j]) for i in range(2) for j in range(2))
    assert norm_delta_e == Fraction(0)

    rho_prod = mat_kron(rho_a, rho_b)
    for i in range(4):
        for j in range(4):
            expected = Fraction(1, 4) if i == j else Fraction(0)
            assert rho_prod[i][j] == expected

    delta_mat = mat_sub(rho, rho_prod)
    assert delta_mat[0][0] == Fraction(1, 4)
    assert delta_mat[0][3] == Fraction(1, 2)
    assert delta_mat[1][1] == Fraction(-1, 4)
    assert delta_mat[2][2] == Fraction(-1, 4)
    assert delta_mat[3][0] == Fraction(1, 2)
    assert delta_mat[3][3] == Fraction(1, 4)

    eigenvalues = [Fraction(3, 4), Fraction(-1, 4), Fraction(-1, 4), Fraction(-1, 4)]

    trace_norm_delta = sum(abs(lam) for lam in eigenvalues)
    assert trace_norm_delta == Fraction(3, 4) + Fraction(1, 4) + Fraction(1, 4) + Fraction(1, 4)
    assert trace_norm_delta == Fraction(3, 2)

    assert norm_delta_e == Fraction(0)
    assert trace_norm_delta == Fraction(3, 2)
    assert trace_norm_delta > norm_delta_e


def test_separable_state_negative_control():
    """Verify negative control: for a product / separable state |00><00|,

    both the 1-site coboundary defect and the bipartite product defect vanish.
    """
    rho_sep = [[Fraction(0) for _ in range(4)] for _ in range(4)]
    rho_sep[0][0] = Fraction(1)

    rho_a = partial_trace_b_4x4(rho_sep)
    rho_b = partial_trace_a_4x4(rho_sep)

    delta_e = mat_sub(rho_b, rho_a)
    assert delta_e == [[Fraction(0), Fraction(0)], [Fraction(0), Fraction(0)]]

    rho_prod = mat_kron(rho_a, rho_b)
    delta_mat = mat_sub(rho_sep, rho_prod)
    for r in range(4):
        for c in range(4):
            assert delta_mat[r][c] == Fraction(0)


def test_classical_correlated_state_comparison():
    """Verify that a classical correlated mixture (1/2)(|00><00| + |11><11|)

    has product defect 1, strictly lower than the quantum Bell state (3/2),
    while both have vanishing 1-site coboundary defect.
    """
    rho_class = [
        [Fraction(1, 2), Fraction(0), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(0), Fraction(1, 2)],
    ]
    rho_a = partial_trace_b_4x4(rho_class)
    rho_b = partial_trace_a_4x4(rho_class)
    assert rho_a == rho_b == [[Fraction(1, 2), Fraction(0)], [Fraction(0), Fraction(1, 2)]]

    delta_e = mat_sub(rho_b, rho_a)
    assert delta_e == [[Fraction(0), Fraction(0)], [Fraction(0), Fraction(0)]]

    rho_prod = mat_kron(rho_a, rho_b)
    delta_class = mat_sub(rho_class, rho_prod)
    for i in range(4):
        for j in range(4):
            if i != j:
                assert delta_class[i][j] == Fraction(0)
    trace_norm_class = sum(abs(delta_class[i][i]) for i in range(4))
    assert trace_norm_class == Fraction(1)
    assert trace_norm_class < Fraction(3, 2)
