"""Unit tests for payload quotient boundary and Primitive Difference / LGGR (PO-001).

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from exact import exact_equal
from exactsym import Matrix
from payload_quotient import (
    CurvaturePacket,
    PayloadPrimitiveDifference,
    certify_local_green_global_red,
)


def test_payload_quotient_factors_payload():
    payload = Matrix([[1], [2]])
    curv1 = Matrix([[0]])
    curv2 = Matrix([[5]])

    p1 = CurvaturePacket(payload=payload, curvature=curv1)
    p2 = CurvaturePacket(payload=payload, curvature=curv2)

    # Identical payloads are in the same equivalence class under delta
    assert PayloadPrimitiveDifference.zero_rel(p1, p2)

    # Payload classifier factors through the quotient
    assert PayloadPrimitiveDifference.payload_is_invariant_congruent([p1, p2])

    # Curvature classifier FAILS to factor through the quotient
    assert not PayloadPrimitiveDifference.curvature_is_invariant_congruent([p1, p2])


def test_certify_local_green_global_red():
    payload = Matrix([[42], [7]])
    curv_k = Matrix([[1, 0], [0, 1]])
    curv_l = Matrix([[2, 0], [0, 3]])

    cert = certify_local_green_global_red(payload, curv_k, curv_l)
    assert cert["payload_equivalent"] is True
    assert cert["local_payload_factors"] is True
    assert cert["global_curvature_factors"] is False
    assert cert["lggr_boundary_confirmed"] is True


def test_value_object_exact_type_equality():
    p = CurvaturePacket(payload=Matrix([[1]]), curvature=Matrix([[0]]))
    other = "NotACurvaturePacket"
    assert p != other
    assert type(p) is not type(other)
