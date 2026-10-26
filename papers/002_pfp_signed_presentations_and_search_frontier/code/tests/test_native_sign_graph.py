"""Classifier results through the native adapter, with the Python checker as fallback."""

import sys
from pathlib import Path

import pytest

_code_dir = Path(__file__).resolve().parent.parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

from genesis_alpha.sign_graph import GaugeWitness, OddCycleWitness, SignedRewrite  # noqa: E402
from native_sign_graph import (  # noqa: E402
    classify_matrix_sign_gauge,
    classify_sign_graph,
    find_binary,
    verify_gauge,
    verify_odd_cycle,
)


def test_native_or_py_classify_tree():
    vertices = ("0", "1", "2")
    edges = (
        SignedRewrite("0", "1", 1),
        SignedRewrite("1", "2", 0),
    )
    res = classify_sign_graph(vertices, edges)
    assert isinstance(res, GaugeWitness)
    assert res.bits == (0, 1, 1)
    assert verify_gauge(vertices, edges, res)


def test_native_or_py_classify_odd_triangle():
    vertices = ("0", "1", "2")
    edges = (
        SignedRewrite("0", "1", 1),
        SignedRewrite("1", "2", 0),
        SignedRewrite("2", "0", 0),
    )
    res = classify_sign_graph(vertices, edges)
    assert isinstance(res, OddCycleWitness)
    assert verify_odd_cycle(vertices, edges, res)


def test_native_matrix_classification():
    matrix = [
        [0, -1, 1],
        [-1, 0, -1],
        [1, -1, 0],
    ]
    res = classify_matrix_sign_gauge(matrix)
    assert isinstance(res, OddCycleWitness)


def test_native_binary_discovered():
    bin_path = find_binary()
    if bin_path is None:
        pytest.skip(
            "solve_sign_graph is not built; run "
            "cargo build -j 1 --manifest-path code/rust/Cargo.toml --bin solve_sign_graph"
        )
    assert bin_path.is_file()
