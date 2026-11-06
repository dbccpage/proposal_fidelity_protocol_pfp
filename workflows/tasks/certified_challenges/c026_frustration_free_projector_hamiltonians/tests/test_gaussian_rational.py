# AuthorityEffect: None.
"""Tests for exact Gaussian rational arithmetic over Q(i) in C026."""

from fractions import Fraction

from c026_frustration_free_projector_hamiltonians.reference_solver.gaussian_rational import (
    GaussianRat,
    format_fraction,
    parse_fraction,
)


def test_fraction_wire_format():
    assert format_fraction(Fraction(0, 1)) == "0"
    assert format_fraction(Fraction(1, 1)) == "1"
    assert format_fraction(Fraction(-5, 1)) == "-5"
    assert format_fraction(Fraction(3, 4)) == "3/4"
    assert format_fraction(Fraction(-7, 2)) == "-7/2"

    assert parse_fraction("0") == Fraction(0, 1)
    assert parse_fraction("1") == Fraction(1, 1)
    assert parse_fraction("-5") == Fraction(-5, 1)
    assert parse_fraction("3/4") == Fraction(3, 4)
    assert parse_fraction("-7/2") == Fraction(-7, 2)


def test_gaussian_rational_operations():
    z1 = GaussianRat("3/5", "-4/5")
    z2 = GaussianRat("3/5", "4/5")

    # Conjugate
    assert z1.conjugate() == z2

    # Addition
    z_sum = z1 + z2
    assert z_sum.r == Fraction(6, 5)
    assert z_sum.i == Fraction(0, 1)

    # Subtraction
    z_diff = z1 - z2
    assert z_diff.r == Fraction(0, 1)
    assert z_diff.i == Fraction(-8, 5)

    # Multiplication: (3/5 - 4/5 i)(3/5 + 4/5 i) = 9/25 + 16/25 = 1
    prod = z1 * z2
    assert prod == GaussianRat.one()

    # Division
    div = z1 / z1
    assert div == GaussianRat.one()

    # Norm squared
    assert z1.abs_sq() == Fraction(1, 1)


def test_gaussian_rational_wire_roundtrip():
    z = GaussianRat("-1/2", "3/4")
    wire = z.to_wire()
    assert wire == ["-1/2", "3/4"]

    z_parsed = GaussianRat.from_wire(wire)
    assert z_parsed == z
