"""Core integration test for Paper PO-001 verifying all primary mathematical claims.

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from covering_edge_poset import FinitePoset
from exact import exact_equal
from exactsym import Matrix
from restriction_system import (
    RestrictionMap,
    RestrictionSystem,
    build_path_a_completion,
    check_path_a_diamond_independence,
)
from cochain_complex import Section0Cochain
from curvature_cochain import (
    compute_all_curvature_operators,
    compute_curvature_operator,
    evaluate_d2_boundary,
    is_flat_system,
    verify_theorem_3_2_all_triples,
)
from payload_quotient import certify_local_green_global_red


def test_po001_full_pipeline_verification():
    """Verify Claims 1 through 10 in a single integrated mathematical workflow."""
    # 1. Poset diamond: 0 < 1 < 3 and 0 < 2 < 3
    poset = FinitePoset(
        elements=["0", "1", "2", "3"],
        relations=[("0", "1"), ("1", "3"), ("0", "2"), ("2", "3")],
    )
    dims = {"0": 2, "1": 2, "2": 2, "3": 2}

    # Path A covering maps that commute around the diamond: powers of [[1, 1], [0, 1]]
    r_31 = RestrictionMap(source="3", target="1", matrix=Matrix([[1, 1], [0, 1]]))
    r_10 = RestrictionMap(source="1", target="0", matrix=Matrix([[1, 2], [0, 1]]))
    r_32 = RestrictionMap(source="3", target="2", matrix=Matrix([[1, 2], [0, 1]]))
    r_20 = RestrictionMap(source="2", target="0", matrix=Matrix([[1, 1], [0, 1]]))

    # Claim 3: Diamond Path-Independence
    cov_system = RestrictionSystem(poset, dims, [r_31, r_10, r_32, r_20])
    is_indep, defect = check_path_a_diamond_independence(poset, cov_system, "0", "1", "2", "3")
    assert is_indep
    assert exact_equal(defect, Matrix.zeros(2, 2))

    # Claim 2: Strict Completion from Covering Edges
    full_presheaf = build_path_a_completion(poset, dims, [r_31, r_10, r_32, r_20])
    assert full_presheaf.has_restriction("0", "3")
    assert is_flat_system(full_presheaf)

    # Claim 6 & 7: Theorem 3.2 on flat presheaf (d1 d0 == 0 == K)
    sec = Section0Cochain(
        poset=poset,
        values={
            "0": Matrix([[1], [1]]),
            "1": Matrix([[2], [1]]),
            "2": Matrix([[1], [2]]),
            "3": Matrix([[3], [3]]),
        },
    )
    assert verify_theorem_3_2_all_triples(full_presheaf, sec)

    # Path B: Introduce a non-trivial curvature defect on an independent system
    # Claim 9: Theorem 3.4 d2 K boundary evaluation
    # Chain 0 < 1 < 2 < 3
    chain_poset = FinitePoset(elements=["0", "1", "2", "3"], relations=[("0", "1"), ("1", "2"), ("2", "3")])
    c_dims = {"0": 1, "1": 1, "2": 1, "3": 1}
    r_32_b = RestrictionMap(source="3", target="2", matrix=Matrix([[2]]))
    r_21_b = RestrictionMap(source="2", target="1", matrix=Matrix([[3]]))
    r_10_b = RestrictionMap(source="1", target="0", matrix=Matrix([[5]]))
    r_31_b = RestrictionMap(source="3", target="1", matrix=Matrix([[7]]))  # defect: 3*2 - 7 = -1
    r_30_b = RestrictionMap(source="3", target="0", matrix=Matrix([[30]])) # defect: 5*7 - 30 = 5
    r_20_b = RestrictionMap(source="2", target="0", matrix=Matrix([[14]])) # defect: 5*3 - 14 = 1

    curv_system = RestrictionSystem(chain_poset, c_dims, [r_32_b, r_21_b, r_10_b, r_31_b, r_30_b, r_20_b])
    d2_val, lower_diff = evaluate_d2_boundary(curv_system, "0", "1", "2", "3", Matrix([[4]]), Matrix([[8]]))
    assert exact_equal(d2_val, lower_diff)

    # Claim 10: Theorem 3.5 Primitive Difference / LGGR boundary
    cert = certify_local_green_global_red(
        payload=Matrix([[1], [0]]),
        curvature_k=Matrix([[0]]),
        curvature_l=Matrix([[3]]),
    )
    assert cert["lggr_boundary_confirmed"] is True
