# AuthorityEffect: None.
"""Unit tests for exact cyclotomic field arithmetic over Q(zeta_m)."""

from fractions import Fraction

from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c025_mub_prime_power_exact.reference_solver.cyclotomic import (
    CyclotomicElement,
    format_fraction,
    get_cyclotomic_polynomial,
    parse_fraction,
)


def test_format_and_parse_fraction():
    assert format_fraction(Fraction(1, 1)) == "1"
    assert format_fraction(Fraction(-5, 1)) == "-5"
    assert format_fraction(Fraction(0, 1)) == "0"
    assert format_fraction(Fraction(1, 2)) == "1/2"
    assert format_fraction(Fraction(-3, 4)) == "-3/4"

    assert parse_fraction("1") == Fraction(1, 1)
    assert parse_fraction("-5") == Fraction(-5, 1)
    assert parse_fraction("3/4") == Fraction(3, 4)
    assert parse_fraction(Fraction(2, 3)) == Fraction(2, 3)
    assert parse_fraction(7) == Fraction(7, 1)


def test_cyclotomic_polynomials():
    # Phi_3(x) = x^2 + x + 1
    assert get_cyclotomic_polynomial(3) == [Fraction(1), Fraction(1), Fraction(1)]
    # Phi_4(x) = x^2 + 1
    assert get_cyclotomic_polynomial(4) == [Fraction(1), Fraction(0), Fraction(1)]
    # Phi_5(x) = x^4 + x^3 + x^2 + x + 1
    assert get_cyclotomic_polynomial(5) == [
        Fraction(1),
        Fraction(1),
        Fraction(1),
        Fraction(1),
        Fraction(1),
    ]
    # Phi_8(x) = x^4 + 1
    assert get_cyclotomic_polynomial(8) == [
        Fraction(1),
        Fraction(0),
        Fraction(0),
        Fraction(0),
        Fraction(1),
    ]
    # Phi_12(x) = x^4 - x^2 + 1
    assert get_cyclotomic_polynomial(12) == [
        Fraction(1),
        Fraction(0),
        Fraction(-1),
        Fraction(0),
        Fraction(1),
    ]


def test_cyclotomic_arithmetic_q4():
    # In Q(zeta_4) = Q(i): i^2 == -1
    i = CyclotomicElement.zeta_pow(4, 1)
    i2 = i * i
    minus_1 = CyclotomicElement.from_rational(4, -1)
    assert i2 == minus_1

    # (1 + i)(1 - i) == 2
    one = CyclotomicElement.one(4)
    z1 = one + i
    z2 = one - i
    assert z1 * z2 == CyclotomicElement.from_rational(4, 2)
    assert z1.abs_sq() == CyclotomicElement.from_rational(4, 2)

    is_rat, rat_val = z1.abs_sq().is_rational()
    assert is_rat and rat_val == Fraction(2, 1)


def test_cyclotomic_arithmetic_q3():
    # In Q(zeta_3): 1 + w + w^2 == 0
    w = CyclotomicElement.zeta_pow(3, 1)
    w2 = CyclotomicElement.zeta_pow(3, 2)
    one = CyclotomicElement.one(3)
    sum_roots = one + w + w2
    assert sum_roots.is_zero()

    # w^3 == 1
    w3 = w * w2
    assert w3 == one


def test_cyclotomic_lifting():
    # w in Q(zeta_3) lifted to Q(zeta_12)
    w = CyclotomicElement.zeta_pow(3, 1)
    w_lift = w.lift_to(12)
    assert w_lift.m == 12
    assert w == w_lift

    # Cross-order addition and multiplication
    i = CyclotomicElement.zeta_pow(4, 1)  # i in Q(zeta_4)
    prod = i * w
    assert prod.m == 12
    # |i * w|^2 == |i|^2 * |w|^2 == 1 * 1 == 1
    is_rat, rat_val = prod.abs_sq().is_rational()
    assert is_rat and rat_val == Fraction(1, 1)
