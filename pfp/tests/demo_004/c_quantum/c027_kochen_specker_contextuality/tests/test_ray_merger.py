# AuthorityEffect: None.
"""Tests for ray parsing and canonical merging in C027."""

from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c027_kochen_specker_contextuality.reference_solver.quad_field import (
    QuadRat,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c027_kochen_specker_contextuality.reference_solver.ray_merger import (
    normalize_ray,
    parse_and_merge_rays,
)


def test_normalize_ray():
    # v = [2, 4, 6] -> [1, 2, 3]
    v = [QuadRat("2", "0"), QuadRat("4", "0"), QuadRat("6", "0")]
    norm_v = normalize_ray(v)
    assert norm_v[0] == QuadRat.one()
    assert norm_v[1] == QuadRat("2", "0")
    assert norm_v[2] == QuadRat("3", "0")


def test_merge_parallel_vectors():
    # Vector v, 2*v, and -v should merge to the same ray
    vecs = [
        [["1", "0"], ["1", "0"], ["0", "0"]],
        [["2", "0"], ["2", "0"], ["0", "0"]],
        [["-5", "0"], ["-5", "0"], ["0", "0"]],
        [["0", "0"], ["1", "0"], ["0", "0"]],
    ]
    is_valid, witness, canon_rays, ray_map = parse_and_merge_rays(3, vecs)
    assert is_valid is True
    assert len(canon_rays) == 2
    assert ray_map == [0, 0, 0, 1]


def test_zero_vector_rejection():
    vecs = [
        [["1", "0"], ["0", "0"], ["0", "0"]],
        [["0", "0"], ["0", "0"], ["0", "0"]],  # zero vector
    ]
    is_valid, witness, _, _ = parse_and_merge_rays(3, vecs)
    assert is_valid is False
    assert witness["kind"] == "zero_vector"
    assert witness["index"] == 1


def test_dimension_mismatch_rejection():
    vecs = [
        [["1", "0"], ["0", "0"], ["0", "0"]],
        [["1", "0"], ["0", "0"]],  # 2 coords instead of 3
    ]
    is_valid, witness, _, _ = parse_and_merge_rays(3, vecs)
    assert is_valid is False
    assert witness["kind"] == "dimension_mismatch"
