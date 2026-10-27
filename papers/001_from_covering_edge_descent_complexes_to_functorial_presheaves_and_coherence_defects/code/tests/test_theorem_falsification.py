"""Falsification tests and mutation attacks against PO-001 theorems.

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from covering_edge_poset import FinitePoset
from exact import exact_equal
from exactsym import Matrix
from restriction_system import RestrictionMap, RestrictionSystem
from cochain_complex import Section0Cochain, coboundary_d0, coboundary_d1
from curvature_cochain import (
    compute_curvature_operator,
    evaluate_d2_boundary,
    is_flat_system,
    verify_theorem_3_2_pointwise,
)
from payload_quotient import (
    CurvaturePacket,
    PayloadPrimitiveDifference,
    certify_local_green_global_red,
)


def test_falsify_non_flat_chain_composition():
    # Poset 0 < 1 < 2
    poset = FinitePoset(elements=["0", "1", "2"], relations=[("0", "1"), ("1", "2")])
    dims = {"0": 1, "1": 1, "2": 1}

    # Deliberate nonzero curvature: r_{1,0} * r_{2,1} = 2 * 3 = 6 != 5 = r_{2,0}
    r_21 = RestrictionMap(source="2", target="1", matrix=Matrix([[3]]))
    r_10 = RestrictionMap(source="1", target="0", matrix=Matrix([[2]]))
    r_20 = RestrictionMap(source="2", target="0", matrix=Matrix([[5]]))

    sys = RestrictionSystem(poset, dims, [r_21, r_10, r_20])
    assert not is_flat_system(sys)

    k_op = compute_curvature_operator(sys, "0", "1", "2")
    assert not k_op.is_zero()
    assert exact_equal(k_op.matrix, Matrix([[1]]))  # 6 - 5 = 1


def test_falsify_mutated_coboundary_sign():
    # If d1 formula had a wrong sign: r_{ba}(g(bc)) + g(ac) + g(ab)
    # it would fail to equal K(s(c))!
    poset = FinitePoset(elements=["0", "1", "2"], relations=[("0", "1"), ("1", "2")])
    dims = {"0": 1, "1": 1, "2": 1}

    r_21 = RestrictionMap(source="2", target="1", matrix=Matrix([[3]]))
    r_10 = RestrictionMap(source="1", target="0", matrix=Matrix([[2]]))
    r_20 = RestrictionMap(source="2", target="0", matrix=Matrix([[4]]))
    sys = RestrictionSystem(poset, dims, [r_21, r_10, r_20])

    s = Section0Cochain(poset=poset, values={"0": Matrix([[7]]), "1": Matrix([[11]]), "2": Matrix([[13]])})

    # Standard formula
    matches, d1_d0_val, k_val = verify_theorem_3_2_pointwise(sys, s, "0", "1", "2")
    assert matches
    # Mutated formula with + g(ac) instead of - g(ac)
    g = coboundary_d0(sys, s)
    mutated_d1 = sys.get_restriction("0", "1")(g("1", "2")) + g("0", "2") + g("0", "1")
    assert not exact_equal(mutated_d1, k_val)


def test_falsify_payload_quotient_collapses_curvature():
    # Packets with identical payloads but different curvatures
    payload = Matrix([[10]])
    curv_zero = Matrix([[0]])
    curv_defect = Matrix([[99]])

    p_clean = CurvaturePacket(payload=payload, curvature=curv_zero)
    p_defect = CurvaturePacket(payload=payload, curvature=curv_defect)

    # A verifier looking only at payload sees equality:
    assert PayloadPrimitiveDifference.zero_rel(p_clean, p_defect)

    # Attempting to assign a well-defined curvature value to the equivalence class fails:
    assert not PayloadPrimitiveDifference.curvature_is_invariant_congruent([p_clean, p_defect])
