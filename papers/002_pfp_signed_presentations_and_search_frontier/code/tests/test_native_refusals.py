"""A found native sign-graph binary decides; its refusals are never replaced.

The exact Python classifier runs only when no binary exists. When a binary is
found, a refusal (nonzero exit or a non-PASS status) raises NativeSignGraphRefused
and malformed output raises NativeSignGraphUnavailable, instead of silently
returning a Python answer.
"""

import json
import os
import sys
from pathlib import Path

import pytest

_code_dir = Path(__file__).resolve().parents[1]
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

import native_sign_graph as nsg  # noqa: E402
from genesis_alpha.sign_graph import GaugeWitness, SignedRewrite  # noqa: E402

VERTICES = ("0", "1", "2")
EDGES = (SignedRewrite("0", "1", 1), SignedRewrite("1", "2", 1), SignedRewrite("2", "0", 0))


def _fake_binary(tmp_path, stdout_line: str, exit_code: int):
    if os.name == "nt":
        path = tmp_path / "fake_solver.cmd"
        path.write_text(f"@echo off\r\necho {stdout_line}\r\nexit /b {exit_code}\r\n", encoding="ascii")
    else:
        path = tmp_path / "fake_solver.sh"
        path.write_text(f"#!/bin/sh\necho '{stdout_line}'\nexit {exit_code}\n", encoding="ascii")
        path.chmod(0o755)
    return path


def test_python_classifier_runs_only_without_a_binary(monkeypatch):
    monkeypatch.setattr(nsg, "find_binary", lambda: None)
    result = nsg.classify_sign_graph(VERTICES, EDGES)
    assert isinstance(result, GaugeWitness)


def test_native_refusal_is_not_replaced(monkeypatch, tmp_path):
    fake = _fake_binary(tmp_path, '{"status": "REFUSED", "error": "fixture refusal"}', 2)
    monkeypatch.setattr(nsg, "find_binary", lambda: fake)
    with pytest.raises(nsg.NativeSignGraphRefused):
        nsg.classify_sign_graph(VERTICES, EDGES)
    with pytest.raises(nsg.NativeSignGraphRefused):
        nsg.verify_gauge(VERTICES, EDGES, GaugeWitness(vertices=VERTICES, bits=(0, 1, 0)))


def test_malformed_native_output_is_not_replaced(monkeypatch, tmp_path):
    fake = _fake_binary(tmp_path, '{"status": "PASS", "result_type": "unexpected"}', 0)
    monkeypatch.setattr(nsg, "find_binary", lambda: fake)
    with pytest.raises(nsg.NativeSignGraphUnavailable):
        nsg.classify_sign_graph(VERTICES, EDGES)
    with pytest.raises(nsg.NativeSignGraphUnavailable):
        nsg.verify_gauge(VERTICES, EDGES, GaugeWitness(vertices=VERTICES, bits=(0, 1, 0)))


@pytest.mark.parametrize("result_type,witness", [
    ("gauge", None),
    ("gauge", {}),
    ("gauge", {"vertices": ["0"], "bits": [True]}),
    ("gauge", {"vertices": ["0"], "bits": []}),
    ("gauge", {"vertices": [["0"]], "bits": [0]}),
    ("odd_cycle", None),
    ("odd_cycle", {"steps": []}),
    ("odd_cycle", {"steps": [[0, "0"]]}),
    ("odd_cycle", {"steps": [[True, "0", "0"]]}),
    ("odd_cycle", {"steps": [[0, "0", None]]}),
])
def test_malformed_native_witness_is_typed_and_not_replaced(
    monkeypatch, tmp_path, result_type, witness,
):
    payload = json.dumps({"status": "PASS", "result_type": result_type, "witness": witness})
    fake = _fake_binary(tmp_path, payload, 0)
    monkeypatch.setattr(nsg, "find_binary", lambda: fake)

    def forbidden_fallback(*args, **kwargs):
        raise AssertionError("Malformed native output must not invoke the Python classifier")

    monkeypatch.setattr(nsg, "py_classify_sign_graph", forbidden_fallback)
    with pytest.raises(nsg.NativeSignGraphUnavailable):
        nsg.classify_sign_graph(VERTICES, EDGES)
