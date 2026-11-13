"""Checks for the weighted-cycle note in docs/completion_supplement.md.

The note proves min_f sum_i a_i |r_i| = min(a) * |sum(w)| on a directed cycle.
These tests check its three table rows, the unique projection of the first row,
and the calculation path that the package governor takes when no native graph
calculator is configured.
"""

from fractions import Fraction

import pytest

from l1_symbol_game_governor import Cochain1, ConstraintGraph, Edge, compute_phi1

TABLE_ROWS = [
    ((1, 1, 1), (1, 2, 2), 3),
    ((1, 1, 0), (1, 1, 1), 2),
    ((1, -1, 0), (1, 1, 1), 0),
]


def _triangle(penalties):
    a, b, c = penalties
    return ConstraintGraph(
        vertices=("x", "y", "z"),
        edges=(Edge("x", "y", a), Edge("y", "z", b), Edge("z", "x", c)),
    )


def _claims(values):
    keys = (("x", "y"), ("y", "z"), ("z", "x"))
    return Cochain1({key: Fraction(value) for key, value in zip(keys, values)})


@pytest.mark.parametrize("claims, penalties, minimum", TABLE_ROWS)
def test_cycle_minimum_matches_closed_form(claims, penalties, minimum):
    """Each table row: the computed minimum equals min(a) * |sum(w)|."""
    assert min(penalties) * abs(sum(claims)) == minimum
    value, _ = compute_phi1(_triangle(penalties), _claims(claims))
    assert value == Fraction(minimum)


def test_first_row_projection_is_unique():
    """Claims (1,1,1) with penalties (1,2,2) project to (-2,1,1) for any optimal gauge."""
    value, gauge = compute_phi1(_triangle((1, 2, 2)), _claims((1, 1, 1)))
    projected = (
        gauge["y"] - gauge["x"],
        gauge["z"] - gauge["y"],
        gauge["x"] - gauge["z"],
    )
    assert value == Fraction(3)
    assert projected == (Fraction(-2), Fraction(1), Fraction(1))


def test_missing_native_pins_fall_back_to_python_enumeration(monkeypatch):
    """Without pins the package governor returns an enumerated value, not a refusal.

    This pins the documented current behaviour of the package copy; it is not a
    native result.
    """
    monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
    monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)
    value, gauge = compute_phi1(_triangle((1, 2, 3)), _claims((1, 1, 1)))
    assert value == Fraction(3)
    assert set(gauge) == {"x", "y", "z"}
