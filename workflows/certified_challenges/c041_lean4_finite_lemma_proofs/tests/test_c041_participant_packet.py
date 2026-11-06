# AuthorityEffect: None.
"""Tests for participant packet deliverables in C041."""

import json
from pathlib import Path

_pkg_root = Path(__file__).resolve().parent.parent


def test_participant_task_md_exists():
    task_file = _pkg_root / "participant_packet" / "TASK.md"
    assert task_file.exists()
    content = task_file.read_text(encoding="utf-8")
    assert "C041" in content
    assert "leanprover/lean4:v4.34.1" in content
    assert "propext" in content
    assert "Quot.sound" in content


def test_accounting_json_valid():
    acct_file = _pkg_root / "participant_packet" / "accounting.json"
    assert acct_file.exists()
    with open(acct_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["challenge_id"] == "c041_lean4_finite_lemma_proofs"
    assert data["tier"] == "T3"
    assert data["budget_ceiling_usd"] == 1.0


def test_twelve_public_examples_present():
    examples_dir = _pkg_root / "participant_packet" / "examples"
    examples = list(examples_dir.glob("*.json"))
    assert len(examples) == 12


def test_answers_jsonl_valid():
    answers_file = _pkg_root / "participant_packet" / "answers.jsonl"
    assert answers_file.exists()
    lines = [
        line.strip()
        for line in answers_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) == 12
    for line in lines:
        record = json.loads(line)
        assert "case_id" in record
        assert "status" in record
        assert record["status"] in {"SOLVED", "OUT_OF_SCOPE", "UNKNOWN"}
