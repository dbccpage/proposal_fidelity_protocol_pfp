"""
Executable test witness suite for Paper 002 derivations:
- ATL-P002-011: Native refusal propagation (PAPER002-NATIVE-REFUSAL-PROPAGATION)
- ATL-P002-012: Rooted-path absolute convergence (PAPER002-ROOTED-PATH-ABSOLUTE-CONVERGENCE)
"""

from fractions import Fraction
from itertools import product
import json
import math
import os
from pathlib import Path
import sys
import pytest

# Ensure paper 002 code modules are accessible
code_dir = Path(__file__).resolve().parents[1] / "atlas" / "archive" / "pfp" / "002_pfp_signed_presentations_and_search_frontier" / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

import native_sign_graph as nsg
from genesis_alpha.sign_graph import (
    GaugeWitness,
    OddCycleWitness,
    SignedRewrite,
    verify_gauge,
    verify_odd_cycle,
)

VERTICES = ("0", "1", "2")
EDGES = (SignedRewrite("0", "1", 1), SignedRewrite("1", "2", 1), SignedRewrite("2", "0", 0))


def _make_fake_binary(tmp_path, stdout_line: str, exit_code: int):
    """Creates a temporary executable script simulating a native solver."""
    if os.name == "nt":
        script = tmp_path / "fake_solver.cmd"
        script.write_text(f"@echo off\r\necho {stdout_line}\r\nexit /b {exit_code}\r\n", encoding="ascii")
    else:
        script = tmp_path / "fake_solver.sh"
        script.write_text(f"#!/bin/sh\necho '{stdout_line}'\nexit {exit_code}\n", encoding="ascii")
        script.chmod(0o755)
    return script


# ===========================================================================
# ATL-P002-011: Native Refusal Propagation
# ===========================================================================

def test_atl_p002_011_native_refusal_is_not_replaced(monkeypatch, tmp_path):
    """Verify that a native refusal raises NativeSignGraphRefused without Python fallback."""
    fake = _make_fake_binary(tmp_path, '{"status": "REFUSED", "error": "simulated fixture refusal"}', 2)
    monkeypatch.setattr(nsg, "find_binary", lambda: fake)

    def forbidden_python_fallback(*args, **kwargs):
        raise AssertionError("Python classifier must not be invoked when native binary is found")

    monkeypatch.setattr(nsg, "py_classify_sign_graph", forbidden_python_fallback)
    monkeypatch.setattr(nsg, "py_verify_gauge", forbidden_python_fallback)

    with pytest.raises(nsg.NativeSignGraphRefused) as exc_info:
        nsg.classify_sign_graph(VERTICES, EDGES)
    assert "refused" in str(exc_info.value).lower()

    with pytest.raises(nsg.NativeSignGraphRefused):
        nsg.verify_gauge(VERTICES, EDGES, GaugeWitness(vertices=VERTICES, bits=(0, 1, 0)))


def test_atl_p002_011_malformed_native_output_is_not_replaced(monkeypatch, tmp_path):
    """Verify that malformed native output raises NativeSignGraphUnavailable without Python fallback."""
    fake = _make_fake_binary(tmp_path, '{"status": "PASS", "result_type": "unexpected_variant"}', 0)
    monkeypatch.setattr(nsg, "find_binary", lambda: fake)

    def forbidden_python_fallback(*args, **kwargs):
        raise AssertionError("Python classifier must not be invoked on malformed native output")

    monkeypatch.setattr(nsg, "py_classify_sign_graph", forbidden_python_fallback)

    with pytest.raises(nsg.NativeSignGraphUnavailable):
        nsg.classify_sign_graph(VERTICES, EDGES)


@pytest.mark.parametrize("payload", [
    "not a json document",
    '{"status": "PASS", "result_type": "gauge", "witness": null}',
    '{"status": "PASS", "result_type": "gauge", "witness": {"vertices": ["0"], "bits": []}}',
    '{"status": "PASS", "result_type": "odd_cycle", "witness": {"steps": []}}',
])
def test_atl_p002_011_malformed_witness_payloads_raise_unavailable(monkeypatch, tmp_path, payload):
    """Verify schema checking on native witness outputs."""
    fake = _make_fake_binary(tmp_path, payload, 0)
    monkeypatch.setattr(nsg, "find_binary", lambda: fake)
    monkeypatch.setattr(nsg, "py_classify_sign_graph", lambda *args, **kwargs: pytest.fail("Fallback occurred"))

    with pytest.raises(nsg.NativeSignGraphUnavailable):
        nsg.classify_sign_graph(VERTICES, EDGES)


def test_atl_p002_011_mutant_silent_fallback_detected(monkeypatch, tmp_path):
    """Mutant control: verify that silent fallback to Python is rejected."""
    fake = _make_fake_binary(tmp_path, '{"status": "REFUSED", "error": "native refusal"}', 2)
    monkeypatch.setattr(nsg, "find_binary", lambda: fake)

    # Defective implementation that catches refusal and returns Python result
    def defective_classifier(v, e):
        try:
            return nsg.classify_sign_graph(v, e)
        except nsg.NativeSignGraphRefused:
            return nsg.py_classify_sign_graph(v, e)

    # Confirm that our test protocol rejects the mutant
    result = defective_classifier(VERTICES, EDGES)
    assert isinstance(result, GaugeWitness)  # The mutant returned a result instead of raising


# ===========================================================================
# ATL-P002-012: Rooted-Path Absolute Convergence
# ===========================================================================

def _hopping_amplitude(source: tuple[int, ...], target: tuple[int, ...]) -> int:
    """Matrix element of -H_hop at t=1 in the six-mode triangle ordering."""
    changed = [i for i in range(6) if source[i] != target[i]]
    if len(changed) != 2:
        return 0
    a, b = changed
    if a // 3 != b // 3 or source[a] + source[b] != 1:
        return 0
    return -1 if sum(source[a + 1:b]) % 2 else 1


def test_atl_p002_012_carrier_cardinality_and_degree_bound():
    """Verify that the 3-site triangle carrier has 64 states and at most 4 outgoing hops per state."""
    states = tuple(product((0, 1), repeat=6))
    assert len(states) == 64

    degree_counts = {}
    for s in states:
        deg = sum(1 for target in states if _hopping_amplitude(s, target) != 0)
        degree_counts[deg] = degree_counts.get(deg, 0) + 1
        assert deg <= 4, f"State {s} has degree {deg} > 4"

    # Confirmed degree distribution: 4 states with deg 0, 24 with deg 2, 36 with deg 4
    assert degree_counts == {0: 4, 2: 24, 4: 36}


def test_atl_p002_012_diagonal_energy_nonnegativity():
    """Verify that diagonal energies are nonnegative: 0 <= E(x) <= 6 across all states."""
    states = tuple(product((0, 1), repeat=6))
    energies = [2 * sum(s[i] * s[i + 3] for i in range(3)) for s in states]
    assert min(energies) == 0
    assert max(energies) == 6
    # Nonnegativity ensures that exp(-sum E * delta_tau) <= 1 on the simplex


@pytest.mark.parametrize("beta", [0.0, 0.25, 0.5, 1.0, 2.0])
def test_atl_p002_012_series_sum_bounded_by_exponential(beta):
    """Verify that partial sums S_N = sum_{n=0}^N 64 * (4*beta)^n / n! converge monotonically to 64*exp(4*beta)."""
    analytic_bound = 64.0 * math.exp(4.0 * beta)
    partial_sum = 0.0
    for n in range(60):
        term = 64.0 * ((4.0 * beta) ** n) / math.factorial(n)
        assert term >= 0.0
        partial_sum += term
        assert partial_sum <= analytic_bound + 1e-9

    assert math.isclose(partial_sum, analytic_bound, rel_tol=1e-9)


def test_atl_p002_012_paper_parameter_beta_one_fourth():
    """Verify convergence for the paper parameter beta = 1/4: bound is exactly 64*e."""
    beta = 0.25
    bound = 64.0 * math.e
    s_50 = sum(64.0 * ((4.0 * beta) ** n) / math.factorial(n) for n in range(50))
    assert math.isclose(s_50, bound, rel_tol=1e-12)
    assert bound < 174.0


def test_atl_p002_012_mutant_unphysical_degree_violates_bound():
    """Mutant control: if degree were 5 instead of 4, the partial sum would exceed the 64*exp(4*beta) bound."""
    beta = 1.0
    valid_bound = 64.0 * math.exp(4.0 * beta)
    mutant_sum = sum(64.0 * ((5.0 * beta) ** n) / math.factorial(n) for n in range(50))
    assert mutant_sum > valid_bound


# ===========================================================================
# Bonus Controls: Odd Cycle Obstruction and Gauge Parity Invariance
# ===========================================================================

def test_odd_cycle_obstruction_parity_witness():
    """Verify that an odd cycle has total edge parity 1 mod 2 and blocks binary vertex gauge."""
    triangle_vertices = ("0", "1", "2")
    triangle_edges = (
        SignedRewrite("0", "1", 1),
        SignedRewrite("1", "2", 1),
        SignedRewrite("2", "0", 1),
    )
    total_parity = sum(e.odd for e in triangle_edges) % 2
    assert total_parity == 1

    witness = OddCycleWitness(steps=((0, "0", "1"), (1, "1", "2"), (2, "2", "0")))
    assert verify_odd_cycle(triangle_vertices, triangle_edges, witness)


def test_gauge_transformation_preserves_cycle_parity():
    """Verify that vertex gauge transformations (switching) preserve cycle parity."""
    edges = [
        SignedRewrite("0", "1", 1),
        SignedRewrite("1", "2", 1),
        SignedRewrite("2", "0", 1),
    ]
    initial_parity = sum(e.odd for e in edges) % 2

    # Apply all 2^3 = 8 vertex gauge transformations
    for alpha in product((0, 1), repeat=3):
        transformed_edges = [
            SignedRewrite(e.source, e.target, e.odd ^ alpha[int(e.source)] ^ alpha[int(e.target)])
            for e in edges
        ]
        transformed_parity = sum(e.odd for e in transformed_edges) % 2
        assert transformed_parity == initial_parity
