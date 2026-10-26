# AuthorityEffect: None.
"""Tests for participant packet artifacts in C026."""

import json
from pathlib import Path

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c026_frustration_free_projector_hamiltonians.participant_packet.runner import (
    load_solver_func,
    run_benchmark,
)


@pytest.fixture
def participant_dir():
    return Path(__file__).resolve().parent.parent / "participant_packet"


def test_accounting_json_structure(participant_dir):
    acc_path = participant_dir / "accounting.json"
    assert acc_path.is_file()
    with open(acc_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["challenge_id"] == "c026_frustration_free_projector_hamiltonians"
    assert data["tier"] == "T3"
    assert data["cost_ceiling_usd"] == 1.00
    assert data["target_cost_usd"] == 0.05


def test_task_md_exists(participant_dir):
    task_path = participant_dir / "TASK.md"
    assert task_path.is_file()
    text = task_path.read_text(encoding="utf-8")
    assert "C026: Frustration-Free Projector Hamiltonians" in text
    assert "DIMENSION_OUT_OF_BOUNDS" in text
    assert "left_inverse" in text


def test_examples_and_runner(participant_dir, tmp_path):
    ex_dir = participant_dir / "examples"
    assert ex_dir.is_dir()
    ex_files = list(ex_dir.glob("*.json"))
    assert len(ex_files) == 9

    out_file = tmp_path / "test_answers.jsonl"
    solver_fn = load_solver_func()
    count = run_benchmark(ex_dir, out_file, solver_fn)
    assert count == 9
    assert out_file.is_file()

    with open(out_file, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]
    assert len(lines) == 9
    for line in lines:
        assert line["status"] in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN")
