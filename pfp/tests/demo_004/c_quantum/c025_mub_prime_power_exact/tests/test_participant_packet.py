# AuthorityEffect: None.
"""Tests for participant packet, examples, and sandboxed runner."""

import json
from pathlib import Path

from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c025_mub_prime_power_exact.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c025_mub_prime_power_exact.participant_packet.runner import (
    load_solver_func,
    run_benchmark,
)

_pkg_dir = Path(__file__).resolve().parent.parent


def test_participant_examples_exist():
    ex_dir = _pkg_dir / "participant_packet" / "examples"
    assert ex_dir.is_dir()
    examples = list(ex_dir.glob("*.json"))
    assert len(examples) == 8


def test_participant_runner_execution(tmp_path):
    ex_dir = _pkg_dir / "participant_packet" / "examples"
    out_file = tmp_path / "test_answers.jsonl"
    solver = load_solver_func()

    count = run_benchmark(ex_dir, out_file, solver)
    assert count == 8
    assert out_file.is_file()

    # Verify answers line by line
    with open(out_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) == 8

    # Load corresponding cases and evaluate
    case_files = sorted(ex_dir.glob("*.json"))
    for cf, line in zip(case_files, lines):
        with open(cf, "r", encoding="utf-8") as f:
            case_data = json.load(f)
        ans = json.loads(line)
        passed, msg, _ = evaluate_dual(case_data, ans)
        assert passed, f"Participant answer failed dual evaluation: {msg}"
