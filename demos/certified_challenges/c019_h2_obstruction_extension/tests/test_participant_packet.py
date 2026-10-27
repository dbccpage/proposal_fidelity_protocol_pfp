"""Test participant packet files, schemas, and public examples."""

from __future__ import annotations

import json
import pathlib

from c019_h2_obstruction_extension.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c019_h2_obstruction_extension.reference_solver.solver import (
    solve,
)

C019_DIR = pathlib.Path(__file__).parent.parent
PARTICIPANT_DIR = C019_DIR / "participant_packet"
EXAMPLES_DIR = PARTICIPANT_DIR / "examples"


def test_participant_packet_files_exist():
    assert (PARTICIPANT_DIR / "TASK.md").is_file()
    assert (PARTICIPANT_DIR / "accounting.json").is_file()
    assert (PARTICIPANT_DIR / "runner.py").is_file()
    assert EXAMPLES_DIR.is_dir()


def test_accounting_json_validity():
    acc = json.loads((PARTICIPANT_DIR / "accounting.json").read_text(encoding="utf-8"))
    assert acc["challenge_id"] == "c019_h2_obstruction_extension"
    assert acc["tier"] == "T3"
    assert acc["budget_ceiling_usd"] == 1.00
    assert acc["allow_fallbacks"] is False


def test_public_examples_solve_and_pass_dual_eval():
    ex_files = sorted(EXAMPLES_DIR.glob("ex*.json"))
    assert len(ex_files) == 18
    for ef in ex_files:
        case = json.loads(ef.read_text(encoding="utf-8"))
        res, tracer = solve(case)
        assert res["status"] in ("SOLVED", "OUT_OF_SCOPE")
        ok, reason, details = evaluate_dual(case, res)
        assert ok, f"Example {ef.name} failed dual eval: {reason}"
