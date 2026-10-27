"""Tests for C023 Participant Packet and Runner."""

from __future__ import annotations

import json
from pathlib import Path

from projects.mssn_sn_symgam.challenges.c_quantum.c023_clifford_tableau_synthesis.participant_packet.runner import (
    load_cases,
    run_benchmark,
)


def test_participant_packet_files_exist():
    pkg_dir = Path(__file__).resolve().parent.parent / "participant_packet"
    assert (pkg_dir / "TASK.md").is_file()
    assert (pkg_dir / "accounting.json").is_file()
    assert (pkg_dir / "runner.py").is_file()
    assert (pkg_dir / "examples").is_dir()

    with open(pkg_dir / "accounting.json", "r", encoding="utf-8") as f:
        acct = json.load(f)
    assert acct["challenge_id"] == "c023_clifford_tableau_synthesis"
    assert acct["tier"] == "T2"
    assert acct["cost_ceiling_usd"] == 0.50
    assert acct["target_cost_usd"] == 0.05


def test_load_examples():
    pkg_dir = Path(__file__).resolve().parent.parent / "participant_packet"
    examples_dir = pkg_dir / "examples"
    cases = load_cases(examples_dir)
    assert len(cases) == 10
    for case in cases:
        assert "num_qubits" in case
        assert "images" in case


def test_runner_execution(tmp_path: Path):
    pkg_dir = Path(__file__).resolve().parent.parent / "participant_packet"
    examples_dir = pkg_dir / "examples"
    out_answers = tmp_path / "answers.jsonl"

    ret = run_benchmark(cases_dir=examples_dir, output_path=out_answers)
    assert ret == 0
    assert out_answers.is_file()

    with open(out_answers, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) == 10
