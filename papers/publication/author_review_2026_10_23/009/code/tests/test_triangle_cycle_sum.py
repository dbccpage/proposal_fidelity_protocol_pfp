"""Checks of the Section 3 triangle arithmetic in Paper 009."""

from fractions import Fraction

import pytest

from triangle_cycle_sum import cycle_sum, edge_differences, exact_triple, subtract

THIRD = Fraction(1, 3)
CLAIMS = (THIRD, THIRD, THIRD)
POTENTIAL = (Fraction(0), THIRD, Fraction(2, 3))


def test_worked_example_values():
    differences = edge_differences(POTENTIAL)
    assert differences == (THIRD, THIRD, Fraction(-2, 3))
    assert subtract(CLAIMS, differences) == (0, 0, 1)
    assert cycle_sum(CLAIMS) == 1


def test_potential_subtraction_keeps_cycle_sum():
    residual = subtract(CLAIMS, edge_differences(POTENTIAL))
    assert cycle_sum(residual) == cycle_sum(CLAIMS) == 1


def test_edge_differences_sum_to_zero():
    shifted = tuple(value + Fraction(7, 5) for value in POTENTIAL)
    for potential in (POTENTIAL, (0, 0, 0), shifted):
        assert cycle_sum(edge_differences(potential)) == 0


def test_replacing_claims_by_differences_gives_zero_cycle_sum():
    replacement = edge_differences(POTENTIAL)
    assert cycle_sum(replacement) == 0
    assert cycle_sum(CLAIMS) != cycle_sum(replacement)


def test_inexact_or_malformed_inputs_are_refused():
    with pytest.raises(TypeError):
        edge_differences((0.0, THIRD, Fraction(2, 3)))
    with pytest.raises(TypeError):
        cycle_sum((True, 0, 0))
    with pytest.raises(ValueError):
        subtract((THIRD, THIRD), (0, 0, 0))
    with pytest.raises(ValueError):
        exact_triple("abc", "claims")
