"""Tests for C022 Participant Packet."""

from __future__ import annotations

import json
from pathlib import Path

from c022_stabilizer_code_distance.participant_packet.runner import (
    run_benchmark,
)

PKG_DIR = Path(__file__).resolve().parent.parent / "participant_packet"


def test_participant_packet_files_exist():
    assert (PKG_DIR / "TASK.md").exists()
    assert (PKG_DIR / "accounting.json").exists()
    assert (PKG_DIR / "runner.py").exists()
    assert (PKG_DIR / "examples").is_dir()


def test_public_examples_count_and_schema():
    examples_dir = PKG_DIR / "examples"
    example_files = list(examples_dir.glob("*.json"))
    assert len(example_files) >= 10, f"Expected at least 10 examples, found {len(example_files)}"

    for ef in example_files:
        data = json.loads(ef.read_text(encoding="utf-8"))
        assert "id" in data
        assert "num_qubits" in data
        assert "generators" in data
        assert isinstance(data["generators"], list)
        assert data["num_qubits"] >= 1


def test_accounting_json_conformance():
    acc_file = PKG_DIR / "accounting.json"
    data = json.loads(acc_file.read_text(encoding="utf-8"))
    assert data["challenge_id"] == "c022_stabilizer_code_distance"
    assert data["protocol"] == "SG-CP v1"
    assert data["tier"] == "T3"
    assert data["target_cost_usd"] == 0.05
    assert data["cost_ceiling_usd"] == 1.00


def test_runner_execution(tmp_path):
    output_file = tmp_path / "test_answers.jsonl"
    examples_dir = PKG_DIR / "examples"
    ret = run_benchmark(cases_dir=examples_dir, output_path=output_file)
    assert ret == 0
    assert output_file.exists()

    lines = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 10
    for line in lines:
        ans = json.loads(line)
        assert "id" in ans
        assert ans["status"] in ("SOLVED", "OUT_OF_SCOPE")
