"""Unit tests for curvature cochain K, Theorem 3.2 (d1 d0 = K), and Theorem 3.4 (d2 K) (PO-001).

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from covering_edge_poset import FinitePoset
from exact import exact_equal
from exactsym import Matrix, Rational
from restriction_system import RestrictionMap, RestrictionSystem
from cochain_complex import Section0Cochain, coboundary_d0, coboundary_d1
from curvature_cochain import (
    compute_curvature_operator,
    evaluate_d2_boundary,
    is_flat_system,
    verify_theorem_3_2_all_triples,
    verify_theorem_3_2_pointwise,
)


def test_theorem_3_2_linear_chain():
    # 3-element chain: 0 < 1 < 2
    poset = FinitePoset(
        elements=["0", "1", "2"],
        relations=[("0", "1"), ("1", "2")],
    )

    dims = {"0": 2, "1": 2, "2": 2}

    # Declare restrictions:
    # r_{2, 1}: F(2) -> F(1)
    # r_{1, 0}: F(1) -> F(0)
    # r_{2, 0}: F(2) -> F(0)
    r_21 = RestrictionMap(source="2", target="1", matrix=Matrix([[1, 2], [3, 4]]))
    r_10 = RestrictionMap(source="1", target="0", matrix=Matrix([[2, 0], [1, -1]]))
    # Composite r_{1, 0} * r_{2, 1} = [[2, 4], [-2, -2]]
    # Let r_{2, 0} intentionally differ by a defect matrix
    defect_mat = Matrix([[1, -1], [2, 0]])
    r_20 = RestrictionMap(source="2", target="0", matrix=r_10.matrix * r_21.matrix - defect_mat)

    system = RestrictionSystem(poset, dims, [r_21, r_10, r_20])

    # Arbitrary section s
    s = Section0Cochain(
        poset=poset,
        values={
            "0": Matrix([[5], [7]]),
            "1": Matrix([[-3], [4]]),
            "2": Matrix([[2], [-1]]),
        },
    )

    # Pointwise check of Theorem 3.2
    matches, d1_d0_val, k_val = verify_theorem_3_2_pointwise(system, s, "0", "1", "2")
    assert matches
    # Defect value should match defect_mat * s("2")
    expected_k_val = defect_mat * s("2")
    assert exact_equal(k_val, expected_k_val)

    # Check across all triples
    assert verify_theorem_3_2_all_triples(system, s)


def test_flat_locus_equivalence():
    # A system where K = 0 everywhere
    poset = FinitePoset(
        elements=["0", "1", "2"],
        relations=[("0", "1"), ("1", "2")],
    )
    dims = {"0": 2, "1": 2, "2": 2}

    r_21 = RestrictionMap(source="2", target="1", matrix=Matrix([[1, 1], [0, 1]]))
    r_10 = RestrictionMap(source="1", target="0", matrix=Matrix([[2, 3], [1, 2]]))
    # Exact composition: r_{2, 0} = r_{1, 0} * r_{2, 1}
    r_20 = RestrictionMap(source="2", target="0", matrix=r_10.matrix * r_21.matrix)

    flat_sys = RestrictionSystem(poset, dims, [r_21, r_10, r_20])
    assert is_flat_system(flat_sys)

    s = Section0Cochain(
        poset=poset,
        values={
            "0": Matrix([[1], [1]]),
            "1": Matrix([[2], [2]]),
            "2": Matrix([[3], [3]]),
        },
    )
    g = coboundary_d0(flat_sys, s)
    h = coboundary_d1(flat_sys, g)
    assert exact_equal(h("0", "1", "2"), Matrix.zeros(2, 1))


def test_theorem_3_4_degree_3_boundary():
    # 4-element chain: 0 < 1 < 2 < 3
    poset = FinitePoset(
        elements=["0", "1", "2", "3"],
        relations=[("0", "1"), ("1", "2"), ("2", "3")],
    )
    dims = {"0": 2, "1": 2, "2": 2, "3": 2}

    # Covering maps
    r_32 = RestrictionMap(source="3", target="2", matrix=Matrix([[2, 1], [0, 1]]))
    r_21 = RestrictionMap(source="2", target="1", matrix=Matrix([[1, 0], [1, 1]]))
    r_10 = RestrictionMap(source="1", target="0", matrix=Matrix([[3, 1], [2, 1]]))

    # Composites with deliberate arbitrary defects
    r_31 = RestrictionMap(source="3", target="1", matrix=Matrix([[5, 2], [1, 3]]))
    r_30 = RestrictionMap(source="3", target="0", matrix=Matrix([[10, 4], [3, 2]]))
    r_20 = RestrictionMap(source="2", target="0", matrix=Matrix([[4, 1], [3, 1]]))

    system = RestrictionSystem(poset, dims, [r_32, r_21, r_10, r_31, r_30, r_20])

    s_3 = Matrix([[3], [-2]])
    s_2 = Matrix([[1], [4]])

    d2_val, lower_diff = evaluate_d2_boundary(system, "0", "1", "2", "3", s_3, s_2)
    # Theorem 3.4 states d2_val == lower_diff identically!
    assert exact_equal(d2_val, lower_diff)

    # Edge-compatible section: s_2 = r_{3, 2}(s_3)
    s_2_compat = r_32(s_3)
    d2_compat, lower_diff_compat = evaluate_d2_boundary(system, "0", "1", "2", "3", s_3, s_2_compat)
    assert exact_equal(d2_compat, Matrix.zeros(2, 1))
    assert exact_equal(lower_diff_compat, Matrix.zeros(2, 1))
