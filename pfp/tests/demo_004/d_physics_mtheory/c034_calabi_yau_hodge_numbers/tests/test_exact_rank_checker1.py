"""C034 Checker 1 must compute ranks exactly over Q.

Counterexample named by this test: rows (2^53, 1) and (2^53 + 1, 1) have determinant -1,
so the rank is 2; float elimination rounds 2^53 + 1 to 2^53 and, with a 1e-9 tolerance,
reported rank 1. Booleans were silently accepted as 1.0.
"""

from __future__ import annotations

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c034_calabi_yau_hodge_numbers.judge_packet.checkers.facet_point_checker import (
    _compute_affine_dim_c1,
    _compute_rank_c1,
)


def test_rank_is_exact_beyond_float_precision() -> None:
    assert _compute_rank_c1([[2**53, 1], [2**53 + 1, 1]]) == 2


def test_rank_detects_small_nonzero_pivot() -> None:
    big = 10**12
    assert _compute_rank_c1([[big, 1], [big + 1, 1]]) == 2


def test_affine_dimension_is_exact() -> None:
    pts = [(0, 0, 0, 0), (2**53, 1, 0, 0), (2**53 + 1, 1, 0, 0)]
    assert _compute_affine_dim_c1(pts) == 2


def test_rank_of_dependent_rows() -> None:
    assert _compute_rank_c1([[1, 2, 3, 4], [2, 4, 6, 8], [0, 0, 0, 0]]) == 1


@pytest.mark.parametrize("bad", [True, 1.0, "1"])
def test_rank_rejects_non_int_entries(bad: object) -> None:
    with pytest.raises(TypeError):
        _compute_rank_c1([[bad, 0], [0, 1]])
