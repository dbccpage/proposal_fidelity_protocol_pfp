# AuthorityEffect: None.
"""Tests for exact arithmetic over Q(sqrt(2)) in C027."""

from fractions import Fraction

from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c027_kochen_specker_contextuality.reference_solver.quad_field import (
    QuadRat,
    format_fraction,
    parse_fraction,
)


def test_fraction_wire_format():
    assert format_fraction(Fraction(0, 1)) == "0"
    assert format_fraction(Fraction(1, 1)) == "1"
    assert format_fraction(Fraction(-3, 1)) == "-3"
    assert format_fraction(Fraction(5, 7)) == "5/7"

    assert parse_fraction("0") == Fraction(0, 1)
    assert parse_fraction("1") == Fraction(1, 1)
    assert parse_fraction("-3") == Fraction(-3, 1)
    assert parse_fraction("5/7") == Fraction(5, 7)


def test_quad_rat_operations():
    # z1 = 1 + sqrt(2), z2 = 1 - sqrt(2)
    z1 = QuadRat("1", "1")
    z2 = QuadRat("1", "-1")

    # Conjugate
    assert z1.conjugate() == z2

    # Addition: (1 + s) + (1 - s) = 2
    z_sum = z1 + z2
    assert z_sum == QuadRat("2", "0")

    # Subtraction: (1 + s) - (1 - s) = 2s
    z_diff = z1 - z2
    assert z_diff == QuadRat("0", "2")

    # Multiplication: (1 + s)(1 - s) = 1 - 2 = -1
    z_prod = z1 * z2
    assert z_prod == QuadRat("-1", "0")

    # Division: (1 + s) / (1 + s) = 1
    z_div = z1 / z1
    assert z_div == QuadRat.one()

    # Norm: N(1 + s) = 1 - 2 = -1
    assert z1.norm() == Fraction(-1, 1)


def test_quad_rat_wire_roundtrip():
    z = QuadRat("3/4", "-5/2")
    wire = z.to_wire()
    assert wire == ["3/4", "-5/2"]

    z_parsed = QuadRat.from_wire(wire)
    assert z_parsed == z
