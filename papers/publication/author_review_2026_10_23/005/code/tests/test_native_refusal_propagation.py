"""compute_phi1 never replaces a configured native calculator's refusal with a Python answer.

Without OMEGA_FUNCTIONAL_GRAPH_BIN the minimum comes from exact enumeration of
spanning-forest potentials. With it, the native adapter decides and any error it
raises propagates to the caller. Edge weights must be exact integers or fractions on
both paths; a float or Boolean weight is refused rather than converted.
"""

from fractions import Fraction

import pytest

from l1_symbol_game_governor import Cochain1, ConstraintGraph, Edge, compute_phi1

CLAIMS = Cochain1(values={("a", "b"): Fraction(1), ("b", "c"): Fraction(1), ("c", "a"): Fraction(1)})


def _graph(weight_ca=2):
    return ConstraintGraph(
        vertices=("a", "b", "c"),
        edges=(Edge("a", "b", 1), Edge("b", "c", 2), Edge("c", "a", weight_ca)),
    )


def test_enumeration_path_without_native_configuration(monkeypatch):
    monkeypatch.delenv("OMEGA_FUNCTIONAL_GRAPH_BIN", raising=False)
    phi, potential = compute_phi1(_graph(), CLAIMS)
    assert phi == Fraction(3)
    residual_sum = sum(
        weight * abs(CLAIMS.values[(u, v)] - (potential[v] - potential[u]))
        for (u, v), weight in ((("a", "b"), 1), (("b", "c"), 2), (("c", "a"), 2))
    )
    assert residual_sum == phi


def test_configured_native_failure_is_not_replaced(monkeypatch, tmp_path):
    monkeypatch.setenv("OMEGA_FUNCTIONAL_GRAPH_BIN", str(tmp_path / "absent-solver.exe"))
    monkeypatch.setenv("OMEGA_FUNCTIONAL_GRAPH_SHA256", "0" * 64)
    with pytest.raises(Exception):
        compute_phi1(_graph(), CLAIMS)


@pytest.mark.parametrize("weight", [4.5, True], ids=["float", "bool"])
def test_float_or_bool_weight_is_refused(monkeypatch, weight):
    monkeypatch.delenv("OMEGA_FUNCTIONAL_GRAPH_BIN", raising=False)
    with pytest.raises(TypeError):
        compute_phi1(_graph(weight_ca=weight), CLAIMS)


def test_zero_weight_edge_is_refused_at_construction():
    with pytest.raises(ValueError):
        Edge("c", "a", 0)


def test_exact_fraction_weight_is_accepted(monkeypatch):
    monkeypatch.delenv("OMEGA_FUNCTIONAL_GRAPH_BIN", raising=False)
    phi, _ = compute_phi1(_graph(weight_ca=Fraction(5, 2)), CLAIMS)
    assert phi == Fraction(3)
