"""The c_quantum reference answers live on the judge side.

Before the 2026-09-29 correction `c_quantum/answers.jsonl`, next to the public
examples, held the reference answers for the theme's hidden, control and
poisoned cases, and the theme runner rewrote it there on every run.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

RUNNER = importlib.import_module("omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.runner")
THEME = Path(RUNNER.__file__).resolve().parent


def _judge_ids() -> set[str]:
    ids: set[str] = set()
    for name in ("hidden_base_cases.json", "relabel_controls.json", "poisoned_cases.json"):
        ids |= {
            case["id"] for case in json.loads((THEME / "judge" / name).read_text(encoding="utf-8"))
        }
    return ids


def test_no_answers_file_in_the_participant_facing_theme_root() -> None:
    assert not (THEME / "answers.jsonl").exists()


def test_reference_answers_are_on_the_judge_side() -> None:
    lines = (THEME / "judge" / "reference_answers.jsonl").read_text(encoding="utf-8").splitlines()
    answered = {json.loads(line)["id"] for line in lines if line.strip()}
    assert _judge_ids() <= answered


def test_runner_writes_reference_answers_to_the_judge_side() -> None:
    source = Path(RUNNER.__file__).read_text(encoding="utf-8")
    assert 'JUDGE_DIR / "reference_answers.jsonl"' in source
    assert 'CHALLENGE_DIR / "answers.jsonl"' not in source
