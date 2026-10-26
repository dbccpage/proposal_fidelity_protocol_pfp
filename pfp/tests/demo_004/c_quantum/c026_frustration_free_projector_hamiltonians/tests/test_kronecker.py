# AuthorityEffect: None.
"""Tests for Kronecker extension in C026."""

from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c026_frustration_free_projector_hamiltonians.reference_solver.gaussian_rational import (
    GaussianRat,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c026_frustration_free_projector_hamiltonians.reference_solver.kronecker import (
    compute_strides,
    coords_to_index,
    extend_local_matrix,
    index_to_coords,
)


def test_coord_index_conversions():
    dims = [2, 3, 2]
    strides = compute_strides(dims)
    seen = set()
    for idx in range(12):
        coords = index_to_coords(idx, dims, strides)
        back_idx = coords_to_index(coords, strides)
        assert back_idx == idx
        assert tuple(coords) not in seen
        seen.add(tuple(coords))


def test_single_qubit_extension():
    # 2 qubits, term on site 0: P = [[1, 0], [0, 0]]
    # Extended P (x) I_2 = diag(1, 1, 0, 0)
    p = [[GaussianRat.one(), GaussianRat.zero()], [GaussianRat.zero(), GaussianRat.zero()]]
    ext = extend_local_matrix([2, 2], [0], p)
    assert len(ext) == 4
    assert ext[0][0] == GaussianRat.one()
    assert ext[1][1] == GaussianRat.one()
    assert ext[2][2] == GaussianRat.zero()
    assert ext[3][3] == GaussianRat.zero()


def test_two_qubit_extension_on_three_qubits():
    # 3 qubits, term on (0, 2): P = |11><11|
    # Extended operator should project onto states with x_0 = 1 and x_2 = 1 (states |101> = 5, |111> = 7)
    p = [[GaussianRat.zero() for _ in range(4)] for _ in range(4)]
    p[3][3] = GaussianRat.one()

    ext = extend_local_matrix([2, 2, 2], [0, 2], p)
    assert len(ext) == 8
    for r in range(8):
        for c in range(8):
            if r == c and r in (5, 7):
                assert ext[r][c] == GaussianRat.one()
            else:
                assert ext[r][c] == GaussianRat.zero()
