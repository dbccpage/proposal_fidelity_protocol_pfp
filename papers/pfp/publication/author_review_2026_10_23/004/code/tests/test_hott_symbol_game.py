"""
Tests for Homotopy Type Theory (HoTT) Identity Types and Primitive Difference Kernel.
Reference: Paper 032 (PO-032).
"""

import pytest

from hott_symbol_game import (
    ContinuousCancellationDetector,
    IdentityPath,
    PrimitiveDifference,
    ap,
    refl,
    sym,
    trans,
)


def test_hott_refl_and_sym():
    """Verifies reflexivity path refl_a : a =_A a and symmetry inversion."""
    p = refl("Prop", "P")
    assert p.is_refl is True
    assert p.source_a == "P"
    assert p.target_b == "P"

    inv_p = sym(p)
    assert inv_p.source_a == "P"
    assert inv_p.target_b == "P"


def test_hott_trans_composition():
    """Verifies transitivity p * q : a =_A c and endpoint matching."""
    p = IdentityPath("Point", "A", "B", is_refl=False, witness="p1")
    q = IdentityPath("Point", "B", "C", is_refl=False, witness="q1")

    composite = trans(p, q)
    assert composite.source_a == "A"
    assert composite.target_b == "C"

    # Mismatched endpoints must raise ValueError
    r = IdentityPath("Point", "D", "E", is_refl=False, witness="r1")
    with pytest.raises(ValueError, match="endpoint mismatch"):
        trans(p, r)


def test_hott_action_on_paths_ap():
    """Verifies action on paths ap_f(p) : f(a) =_B f(b)."""
    p = IdentityPath("Int", 3, 3, is_refl=True, witness="refl_3")

    def f(x):
        return x * 2

    ap_p = ap(f, p, "Int")
    assert ap_p.source_a == 6
    assert ap_p.target_b == 6
    assert ap_p.is_refl is True


def test_primitive_difference_quotient_identity():
    """Verifies nullary Primitive Difference and equivalence quotient certificate."""
    # Difference on integers modulo 5
    diff_kernel = PrimitiveDifference(
        carrier_type="Z",
        delta_func=lambda x, y: (y - x) % 5,
        zero_pred=lambda d: d == 0,
    )

    assert diff_kernel.zero_rel(2, 7) is True
    assert diff_kernel.zero_rel(2, 8) is False

    cert_eq = diff_kernel.certificate_of_identity(2, 7)
    assert cert_eq is not None
    assert cert_eq.source_a == 2
    assert cert_eq.target_b == 7

    cert_neq = diff_kernel.certificate_of_identity(2, 8)
    assert cert_neq is None


def test_continuous_cancellation_laundering_refusal():
    """
    Opposing feature vectors that cancel under convex combination in R^d
    are detected and refused a constructive HoTT identity path.
    """
    v1 = [1.0, 0.0, -0.5]
    v2 = [-1.0, 0.0, 0.5]  # Exactly opposite vector

    analysis = ContinuousCancellationDetector.is_cancellation_laundering(v1, v2, 0.5, 0.5)
    assert analysis["is_laundering"] is True
    assert analysis["hott_path_exists"] is False
    assert analysis["refusal_reason"] is not None
    assert "Continuous cancellation laundering detected" in analysis["refusal_reason"]
