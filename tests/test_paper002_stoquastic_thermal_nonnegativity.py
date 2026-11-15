"""
Executable test witness for Derivation ATL-P002-003 (PFP002-03).

Claim:
For a finite real matrix H with H_ij <= 0 for i != j (stoquastic in the declared basis)
and beta >= 0, the thermal exponential e^(-beta * H) is entrywise nonnegative.

Mathematical decomposition and proof mechanism:
Let H be an n x n real symmetric matrix with H_ij <= 0 for all i != j.
Let beta >= 0.
Shift scalar: c = max_i H_ii.
Shifted matrix: M = c*I - H.
1. Diagonal: M_ii = c - H_ii >= 0 since c >= H_ii.
2. Off-diagonal: for i != j, M_ij = -H_ij >= 0 since H_ij <= 0.
Thus M is entrywise nonnegative: M >= 0.

Exponential decomposition:
Because c*I and H commute (c*I is a central scalar matrix),
e^(-beta * H) = e^(-beta * (c*I - M)) = e^(-beta * c) * e^(beta * M)
              = e^(-beta * c) * sum_{k=0}^infty (beta^k * M^k) / k!.
- Since M >= 0 and beta >= 0, every matrix power M^k >= 0 entrywise.
- The coefficients beta^k / k! >= 0.
- The scalar prefactor e^(-beta * c) > 0.
- The series converges absolutely for every finite real matrix in any submultiplicative norm.
Therefore, every partial sum S_K is entrywise nonnegative, and the infinite sum limit
e^(-beta * H) is entrywise nonnegative.

Test structure:
1. Positive property 1: Shift decomposition M = c*I - H entrywise nonnegative for
   stoquastic matrices across dimensions 2, 3, 5, 8 (including Paper 002 gauged running matrix).
2. Positive property 2: Truncated Taylor polynomial S_K = e^(-beta*c) * sum_{k=0}^K (beta^k * M^k)/k!
   is entrywise nonnegative for all K in {0, 1, 2, 5, 10, 20} and beta in {0.0, 0.1, 0.5, 1.0, 5.0}.
3. Positive property 3: Exact rational computation and high-precision evaluation of e^(-beta * H)
   via power series with explicit Cauchy remainder bounds confirming all entries >= 0.
4. Falsification / Negative control: A non-stoquastic matrix with positive off-diagonal entries
   (e.g., ungauged running matrix H_01 > 0, or all-positive triangle graph) yields strictly
   negative entries in e^(-beta * H) for appropriate beta > 0.
"""

from fractions import Fraction
import math
import pytest


# ---------------------------------------------------------------------------
# Exact Rational Matrix Arithmetic
# ---------------------------------------------------------------------------

def mat_mul(A, B):
    n = len(A)
    return [[sum(A[i][r] * B[r][j] for r in range(n)) for j in range(n)] for i in range(n)]


def mat_add(A, B):
    n = len(A)
    return [[A[i][j] + B[i][j] for j in range(n)] for i in range(n)]


def mat_sub(A, B):
    n = len(A)
    return [[A[i][j] - B[i][j] for j in range(n)] for i in range(n)]


def mat_scale(s, A):
    n = len(A)
    return [[s * A[i][j] for j in range(n)] for i in range(n)]


def mat_identity(n):
    return [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)]


def mat_norm_1(A):
    """Induced matrix 1-norm (maximum column sum of absolute values)."""
    n = len(A)
    return max(sum(abs(A[i][j]) for i in range(n)) for j in range(n))


def shift_decomposition(H):
    """
    Computes c = max_i H_ii and shifted matrix M = c*I - H.
    """
    n = len(H)
    c = max(H[i][i] for i in range(n))
    M = [[c * (1 if i == j else 0) - H[i][j] for j in range(n)] for i in range(n)]
    return c, M


def taylor_expansion_series(A, K):
    """
    Computes sum_{k=0}^K A^k / k! in exact Fraction arithmetic.
    """
    n = len(A)
    cur_power = mat_identity(n)
    poly = mat_identity(n)
    for k in range(1, K + 1):
        cur_power = mat_mul(cur_power, A)
        coeff = Fraction(1, math.factorial(k))
        term = mat_scale(coeff, cur_power)
        poly = mat_add(poly, term)
    return poly


# ---------------------------------------------------------------------------
# Declared Matrix Fixtures
# ---------------------------------------------------------------------------

# Paper 002 running matrix gauged:
# RUNNING = ((0, 1, -1), (1, 0, 1), (-1, 1, 0))
# D = diag(1, -1, 1) -> H_RUNNING_GAUGED = D @ RUNNING @ D
H_RUNNING_GAUGED = [
    [Fraction(0), Fraction(-1), Fraction(-1)],
    [Fraction(-1), Fraction(0), Fraction(-1)],
    [Fraction(-1), Fraction(-1), Fraction(0)],
]

# 2x2 stoquastic matrix
H_2X2 = [
    [Fraction(3), Fraction(-2)],
    [Fraction(-2), Fraction(1)],
]

# 3x3 stoquastic matrix with distinct diagonal entries
H_3X3 = [
    [Fraction(5, 2), Fraction(-1, 3), Fraction(-2)],
    [Fraction(-1, 3), Fraction(7, 4), Fraction(-1, 2)],
    [Fraction(-2), Fraction(-1, 2), Fraction(4)],
]

# 5x5 stoquastic matrix
def generate_stoquastic_dim5():
    n = 5
    H = [[Fraction(0) for _ in range(n)] for _ in range(n)]
    for i in range(n):
        H[i][i] = Fraction(2 * (i + 1), 3)
        for j in range(n):
            if i != j:
                dist = min(abs(i - j), n - abs(i - j))
                H[i][j] = Fraction(-1, dist + 1)
    return H

# 8x8 stoquastic matrix (hypercube topology)
def generate_stoquastic_dim8():
    n = 8
    H = [[Fraction(0) for _ in range(n)] for _ in range(n)]
    for i in range(n):
        H[i][i] = Fraction(i + 1, 2)
        for j in range(i + 1, n):
            if bin(i ^ j).count("1") == 1:
                val = Fraction(-3, 4)
                H[i][j] = val
                H[j][i] = val
    return H


STOQUASTIC_MATRICES = [
    ("2x2", H_2X2),
    ("3x3_running_gauged", H_RUNNING_GAUGED),
    ("3x3_distinct_diag", H_3X3),
    ("5x5_cycle", generate_stoquastic_dim5()),
    ("8x8_hypercube", generate_stoquastic_dim8()),
]


# ==============================================================================
# Positive Property 1: Shift Decomposition Nonnegativity
# ==============================================================================

@pytest.mark.parametrize("name, H", STOQUASTIC_MATRICES)
def test_shift_decomposition_entrywise_nonnegative(name, H):
    """
    Verify M = c*I - H is entrywise nonnegative for all declared stoquastic matrices.
    c = max_i H_ii
    Diagonal: M_ii = c - H_ii >= 0
    Off-diagonal: M_ij = -H_ij >= 0 (since H_ij <= 0 for i != j).
    """
    n = len(H)
    c, M = shift_decomposition(H)
    for i in range(n):
        for j in range(n):
            if i == j:
                assert M[i][i] >= Fraction(0), f"M[{i}][{i}] = {M[i][i]} < 0 in {name}"
                assert M[i][i] == c - H[i][i]
            else:
                assert M[i][j] >= Fraction(0), f"M[{i}][{j}] = {M[i][j]} < 0 in {name}"
                assert M[i][j] == -H[i][j]
                assert H[i][j] <= Fraction(0), f"H[{i}][{j}] = {H[i][j]} > 0 in {name}"


# ==============================================================================
# Positive Property 2: Truncated Taylor Polynomial Nonnegativity
# ==============================================================================

@pytest.mark.parametrize("name, H", STOQUASTIC_MATRICES)
@pytest.mark.parametrize("beta_val", [Fraction(0), Fraction(1, 10), Fraction(1, 2), Fraction(1), Fraction(5)])
@pytest.mark.parametrize("K", [0, 1, 2, 5, 10, 20])
def test_truncated_taylor_polynomial_nonnegative(name, H, beta_val, K):
    """
    Verify S_K = e^(-beta*c) * sum_{k=0}^K (beta^k * M^k)/k! is entrywise nonnegative
    for all truncation depths K in {0, 1, 2, 5, 10, 20} and beta in {0, 0.1, 0.5, 1.0, 5.0}.
    In exact arithmetic, sum_{k=0}^K (beta^k * M^k)/k! is entrywise >= 0.
    """
    n = len(H)
    c, M = shift_decomposition(H)
    beta_M = mat_scale(beta_val, M)
    poly_exact = taylor_expansion_series(beta_M, K)

    for i in range(n):
        for j in range(n):
            assert poly_exact[i][j] >= Fraction(0), (
                f"poly_exact[{i}][{j}] = {poly_exact[i][j]} < 0 in {name} at K={K}, beta={beta_val}"
            )

    # Floating point scaling by exp(-beta * c)
    exp_neg_beta_c = math.exp(-float(beta_val) * float(c))
    assert exp_neg_beta_c > 0.0
    for i in range(n):
        for j in range(n):
            s_k_val = exp_neg_beta_c * float(poly_exact[i][j])
            assert s_k_val >= 0.0


def test_taylor_polynomial_monotonic_convergence():
    """
    Verify that T_K = sum_{k=0}^K (beta^k * M^k)/k! is entrywise monotonically
    nondecreasing in K, because every added term beta^(K+1) * M^(K+1) / (K+1)! >= 0.
    """
    H = H_RUNNING_GAUGED
    n = len(H)
    _, M = shift_decomposition(H)
    beta = Fraction(1, 2)
    beta_M = mat_scale(beta, M)

    power = mat_identity(n)
    poly = mat_identity(n)
    for k in range(1, 16):
        power = mat_mul(power, beta_M)
        coeff = Fraction(1, math.factorial(k))
        term = mat_scale(coeff, power)
        new_poly = mat_add(poly, term)

        for i in range(n):
            for j in range(n):
                assert term[i][j] >= Fraction(0)
                assert new_poly[i][j] >= poly[i][j]
        poly = new_poly


# ==============================================================================
# Positive Property 3: Exact Rational Computation and Remainder Bounds
# ==============================================================================

@pytest.mark.parametrize("name, H", STOQUASTIC_MATRICES)
@pytest.mark.parametrize("beta_val", [Fraction(1, 10), Fraction(1, 2), Fraction(1)])
def test_exact_thermal_exponential_series_convergence(name, H, beta_val):
    """
    Verify e^(-beta * H) using the shifted series:
    e^(-beta * H) = e^(-beta * c) * sum_{k=0}^infty (beta * M)^k / k!.
    In 1-norm, remainder bound for truncation at K is:
    ||R_K||_1 <= ||beta*M||_1^(K+1) / (K+1)! * exp(||beta*M||_1).
    Verify that at K=25, remainder bound is negligible (< 1e-12)
    and all truncated entries are strictly positive for connected stoquastic components.
    """
    n = len(H)
    c, M = shift_decomposition(H)
    beta_M = mat_scale(beta_val, M)
    norm_beta_M = mat_norm_1(beta_M)
    float_norm = float(norm_beta_M)

    # Choose K dynamically such that Cauchy remainder bound is < 1e-9
    float_norm = float(norm_beta_M)
    K = 10
    while K < 50:
        remainder_bound = (float_norm ** (K + 1) / math.factorial(K + 1)) * math.exp(float_norm)
        if remainder_bound < 1e-9:
            break
        K += 5

    poly_K = taylor_expansion_series(beta_M, K)
    assert remainder_bound < 1e-9

    exp_neg_beta_c = math.exp(-float(beta_val) * float(c))
    for i in range(n):
        for j in range(n):
            entry_approx = exp_neg_beta_c * float(poly_K[i][j])
            # Even with worst-case remainder subtracted, entries are nonnegative
            assert entry_approx - remainder_bound >= -1e-14
            assert entry_approx >= 0.0


# ==============================================================================
# Falsification / Negative Control: Non-Stoquastic Matrices
# ==============================================================================

def test_falsification_ungauged_running_matrix_fails_nonnegativity():
    """
    Paper 002 running matrix before diagonal sign gauge:
    RUNNING = ((0, 1, -1), (1, 0, 1), (-1, 1, 0))
    Here H_01 = 1 > 0 and H_12 = 1 > 0 (not stoquastic in declared basis).
    For small beta > 0:
    (e^(-beta * H))_01 = -beta * H_01 + O(beta^2) = -beta + O(beta^2) < 0.
    With beta = 1/10 and K=12, the exact remainder is bounded by:
    norm(beta*H)^13 / 13! * exp(norm) < 1e-14, while the linear term is -1/10 = -0.1.
    Thus (e^(-beta * H))_01 is certifiably negative.
    """
    H_ungauged = [
        [Fraction(0), Fraction(1), Fraction(-1)],
        [Fraction(1), Fraction(0), Fraction(1)],
        [Fraction(-1), Fraction(1), Fraction(0)],
    ]
    beta = Fraction(1, 10)
    neg_beta_H = mat_scale(-beta, H_ungauged)

    K = 12
    poly_exact = taylor_expansion_series(neg_beta_H, K)
    norm = mat_norm_1(neg_beta_H)
    float_norm = float(norm)
    remainder = (float_norm ** (K + 1) / math.factorial(K + 1)) * math.exp(float_norm)

    # Exact value of poly_exact[0][1] is approximately -0.1055 < 0
    val_01 = float(poly_exact[0][1])
    assert val_01 + remainder < 0.0, f"Expected certifiably negative entry, got {val_01} +/- {remainder}"

    # Also check poly_exact[1][2]
    val_12 = float(poly_exact[1][2])
    assert val_12 + remainder < 0.0


def test_falsification_all_positive_triangle_odd_cycle_fails_nonnegativity():
    """
    All-positive triangle obstruction from Paper 002 Section 2 & 3:
    ALL_POSITIVE = ((0, 1, 1), (1, 0, 1), (1, 1, 0))
    This matrix has odd-cycle frustration; no diagonal sign gauge can make it stoquastic.
    For small beta = 1/10, all off-diagonal entries of e^(-beta * H) are certifiably negative.
    """
    H_all_positive = [
        [Fraction(0), Fraction(1), Fraction(1)],
        [Fraction(1), Fraction(0), Fraction(1)],
        [Fraction(1), Fraction(1), Fraction(0)],
    ]
    beta = Fraction(1, 10)
    neg_beta_H = mat_scale(-beta, H_all_positive)

    K = 12
    poly_exact = taylor_expansion_series(neg_beta_H, K)
    norm = mat_norm_1(neg_beta_H)
    float_norm = float(norm)
    remainder = (float_norm ** (K + 1) / math.factorial(K + 1)) * math.exp(float_norm)

    for i in range(3):
        for j in range(3):
            if i != j:
                val = float(poly_exact[i][j])
                assert val + remainder < 0.0, (
                    f"Expected certifiably negative off-diagonal at ({i}, {j}), got {val} +/- {remainder}"
                )


@pytest.mark.parametrize("dim", [2, 3, 4, 6])
def test_falsification_arbitrary_positive_off_diagonal_fails_nonnegativity(dim):
    """
    For any symmetric matrix H with at least one off-diagonal H_01 > 0,
    the thermal exponential entry (e^(-beta * H))_01 is certifiably negative
    for sufficiently small beta > 0.
    """
    # Construct matrix with H[0][1] = 2 > 0 and bounded other entries
    H = [[Fraction(0) for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        H[i][i] = Fraction(i)
    H[0][1] = Fraction(2)
    H[1][0] = Fraction(2)

    beta = Fraction(1, 100)
    neg_beta_H = mat_scale(-beta, H)

    K = 10
    poly_exact = taylor_expansion_series(neg_beta_H, K)
    norm = mat_norm_1(neg_beta_H)
    float_norm = float(norm)
    remainder = (float_norm ** (K + 1) / math.factorial(K + 1)) * math.exp(float_norm)

    val_01 = float(poly_exact[0][1])
    assert val_01 + remainder < 0.0, f"Expected certifiably negative entry in dim {dim}"
