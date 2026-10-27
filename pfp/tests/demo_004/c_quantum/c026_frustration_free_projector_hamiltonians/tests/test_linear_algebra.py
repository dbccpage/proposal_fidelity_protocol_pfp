# AuthorityEffect: None.
"""Tests for exact Gaussian rational linear algebra in C026."""

from projects.mssn_sn_symgam.challenges.c_quantum.c026_frustration_free_projector_hamiltonians.reference_solver.gaussian_rational import (
    GaussianRat,
)
from projects.mssn_sn_symgam.challenges.c_quantum.c026_frustration_free_projector_hamiltonians.reference_solver.linear_algebra import (
    compute_left_inverse,
    compute_rref_and_kernel,
    invert_matrix,
    mat_mul,
)


def test_identity_kernel_and_rank():
    # 3x3 identity matrix has rank 3 and kernel dimension 0
    I3 = [
        [GaussianRat.one(), GaussianRat.zero(), GaussianRat.zero()],
        [GaussianRat.zero(), GaussianRat.one(), GaussianRat.zero()],
        [GaussianRat.zero(), GaussianRat.zero(), GaussianRat.one()],
    ]
    rref, rank, kernel = compute_rref_and_kernel(I3)
    assert rank == 3
    assert len(kernel) == 0


def test_zero_matrix_kernel_and_rank():
    # 2x2 zero matrix has rank 0 and kernel dimension 2
    Z2 = [[GaussianRat.zero(), GaussianRat.zero()], [GaussianRat.zero(), GaussianRat.zero()]]
    rref, rank, kernel = compute_rref_and_kernel(Z2)
    assert rank == 0
    assert len(kernel) == 2


def test_hermitian_matrix_inversion():
    # Invert 2x2 Hermitian matrix: [[2, 1+i], [1-i, 3]]
    # det = 2*3 - (1+i)(1-i) = 6 - 2 = 4
    # inv = 1/4 * [[3, -1-i], [-1+i, 2]]
    A = [
        [GaussianRat("2", "0"), GaussianRat("1", "1")],
        [GaussianRat("1", "-1"), GaussianRat("3", "0")],
    ]
    A_inv = invert_matrix(A)
    assert A_inv is not None

    prod = mat_mul(A, A_inv)
    assert prod[0][0] == GaussianRat.one()
    assert prod[0][1] == GaussianRat.zero()
    assert prod[1][0] == GaussianRat.zero()
    assert prod[1][1] == GaussianRat.one()


def test_left_inverse_computation():
    # 4x2 matrix with full column rank 2
    M = [
        [GaussianRat.one(), GaussianRat.zero()],
        [GaussianRat.zero(), GaussianRat.one()],
        [GaussianRat.one(), GaussianRat.one()],
        [GaussianRat.zero(), GaussianRat.zero()],
    ]
    L = compute_left_inverse(M)
    assert L is not None
    assert len(L) == 2
    assert len(L[0]) == 4

    LM = mat_mul(L, M)
    assert LM[0][0] == GaussianRat.one()
    assert LM[0][1] == GaussianRat.zero()
    assert LM[1][0] == GaussianRat.zero()
    assert LM[1][1] == GaussianRat.one()
