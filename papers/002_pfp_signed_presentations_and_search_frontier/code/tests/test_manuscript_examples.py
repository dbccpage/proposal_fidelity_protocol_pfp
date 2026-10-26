"""Worked examples of Sections 1, 2 and 4 of the manuscript, checked exactly."""

import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "genesis_alpha"))

from frontier_search import (
    CHECKER_VERSION,
    DIAGONAL_Z2_GRAMMAR,
    PresentationKey,
    exact_matrix_digest,
    search_exact_matrix,
    verify_search_receipt,
)
from sign_graph import (
    GaugeWitness,
    OddCycleWitness,
    SignedRewrite,
    classify_matrix_sign_gauge,
    classify_sign_graph,
    matrix_sign_graph,
    verify_gauge,
    verify_odd_cycle,
)

RUNNING = ((0, 1, -1), (1, 0, 1), (-1, 1, 0))
ALL_POSITIVE = ((0, 1, 1), (1, 0, 1), (1, 1, 0))


def _key(matrix):
    return PresentationKey(
        hamiltonian_digest=exact_matrix_digest(matrix),
        basis="declared-three-state-basis",
        ensemble="toy-none",
        filling="toy-not-defined",
        boundary="finite-three-state",
        representation="fixed-real-matrix",
        estimator="off-diagonal-sign-only",
        observables=("toy-matrix-sign",),
        beta="not-used",
        parameters=(),
        transformation_grammar=DIAGONAL_Z2_GRAMMAR,
        adapter_digest="0" * 64,
        checker_version=CHECKER_VERSION,
    )


def test_running_matrix_gauge_and_sign_change():
    signs = (1, -1, 1)
    for i, j in ((0, 1), (0, 2), (1, 2)):
        assert signs[i] * RUNNING[i][j] * signs[j] < 0
    vertices, edges = matrix_sign_graph(RUNNING)
    assert {(e.source, e.target): e.odd for e in edges} == {("0", "1"): 1, ("0", "2"): 0, ("1", "2"): 1}
    assert verify_gauge(vertices, edges, GaugeWitness(vertices, (0, 1, 0)))
    result = classify_matrix_sign_gauge(RUNNING)
    assert isinstance(result, GaugeWitness) and verify_gauge(vertices, edges, result)


def test_all_positive_triangle_and_odd_self_loop_are_obstructions():
    vertices, edges = matrix_sign_graph(ALL_POSITIVE)
    assert all(e.odd == 1 for e in edges)
    assert not any(verify_gauge(vertices, edges, GaugeWitness(vertices, bits))
                   for bits in product((0, 1), repeat=3))
    result = classify_matrix_sign_gauge(ALL_POSITIVE)
    assert isinstance(result, OddCycleWitness) and verify_odd_cycle(vertices, edges, result)
    loop = (SignedRewrite("v", "v", 1),)
    witness = classify_sign_graph(("v",), loop)
    assert isinstance(witness, OddCycleWitness) and verify_odd_cycle(("v",), loop, witness)


def test_frontier_worked_trace_of_section_4():
    key = _key(RUNNING)
    vertices, edges = matrix_sign_graph(RUNNING)
    first = search_exact_matrix(RUNNING, key, node_budget=2)
    assert first.status == "UNKNOWN" and first.witness is None
    assert [(c.index, c.bits, c.valid) for c in first.checks] == [
        (0, (0, 0, 0), False), (1, (0, 0, 1), False)]
    assert (first.frontier.next_index, first.frontier.stop_index) == (2, 8)
    second = search_exact_matrix(RUNNING, key, node_budget=1,
                                 frontier=first.frontier, prior_receipts=(first,))
    assert second.status == "GAUGE_VERIFIED"
    assert [(c.index, c.bits, c.valid) for c in second.checks] == [(2, (0, 1, 0), True)]
    assert second.frontier.next_index == 3
    assert verify_search_receipt(vertices, edges, key, second, prior_receipts=(first,))
    assert not verify_search_receipt(vertices, edges, key, second)
