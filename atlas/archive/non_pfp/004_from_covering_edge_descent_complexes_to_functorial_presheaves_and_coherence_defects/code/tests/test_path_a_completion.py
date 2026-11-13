"""Unit tests for Path A strict completion and diamond independence (PO-001).

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from covering_edge_poset import FinitePoset
from exact import exact_equal
from exactsym import Matrix, Rational
from restriction_system import (
    RestrictionMap,
    RestrictionSystem,
    build_path_a_completion,
    check_path_a_diamond_independence,
)


def test_path_a_commuting_diamond():
    # Commuting diamond: 0 < 1 < 3 and 0 < 2 < 3
    poset = FinitePoset(
        elements=["0", "1", "2", "3"],
        relations=[("0", "1"), ("1", "3"), ("0", "2"), ("2", "3")],
    )

    dims = {"0": 2, "1": 2, "2": 2, "3": 2}

    # Left path: r_{1, 0} * r_{3, 1}
    # Right path: r_{2, 0} * r_{3, 2}
    r_31 = RestrictionMap(source="3", target="1", matrix=Matrix([[1, 0], [0, 2]]))
    r_10 = RestrictionMap(source="1", target="0", matrix=Matrix([[3, 0], [0, 1]]))
    # composite 3->0 via 1 is diag(3, 2)

    r_32 = RestrictionMap(source="3", target="2", matrix=Matrix([[3, 0], [0, 1]]))
    r_20 = RestrictionMap(source="2", target="0", matrix=Matrix([[1, 0], [0, 2]]))
    # composite 3->0 via 2 is diag(3, 2)

    cov_maps = [r_31, r_10, r_32, r_20]
    sys = RestrictionSystem(poset, dims, cov_maps)

    is_indep, defect = check_path_a_diamond_independence(poset, sys, "0", "1", "2", "3")
    assert is_indep
    assert exact_equal(defect, Matrix.zeros(2, 2))

    # Path A completion succeeds uniquely
    completed_sys = build_path_a_completion(poset, dims, cov_maps)
    r_30 = completed_sys.get_restriction(target="0", source="3")
    assert exact_equal(r_30.matrix, Matrix([[3, 0], [0, 2]]))


def test_path_a_non_commuting_diamond_rejection():
    # Non-commuting diamond violates Path A assumption
    poset = FinitePoset(
        elements=["0", "1", "2", "3"],
        relations=[("0", "1"), ("1", "3"), ("0", "2"), ("2", "3")],
    )

    dims = {"0": 1, "1": 1, "2": 1, "3": 1}

    # Left path product: 2 * 3 = 6
    r_31 = RestrictionMap(source="3", target="1", matrix=Matrix([[3]]))
    r_10 = RestrictionMap(source="1", target="0", matrix=Matrix([[2]]))

    # Right path product: 1 * 5 = 5
    r_32 = RestrictionMap(source="3", target="2", matrix=Matrix([[5]]))
    r_20 = RestrictionMap(source="2", target="0", matrix=Matrix([[1]]))

    cov_maps = [r_31, r_10, r_32, r_20]
    sys = RestrictionSystem(poset, dims, cov_maps)

    is_indep, defect = check_path_a_diamond_independence(poset, sys, "0", "1", "2", "3")
    assert not is_indep
    assert exact_equal(defect, Matrix([[1]]))  # 6 - 5 = 1

    with pytest.raises(ValueError, match="Path A hypothesis violated"):
        build_path_a_completion(poset, dims, cov_maps)
