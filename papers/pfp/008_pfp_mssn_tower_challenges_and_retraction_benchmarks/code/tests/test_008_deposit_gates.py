"""Negative controls for the named Lean census gate; no compiler is mocked as a proof."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def verifier():
    spec = importlib.util.spec_from_file_location("pfp008_deposit_under_test", ROOT / "verify_deposit.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def report_rows() -> list[str]:
    return [line for line in (ROOT / "lean4" / "axiom_report.txt").read_text().splitlines() if line.startswith("'")]


def fake_lake(monkeypatch, output: str) -> None:
    def run(command, **kwargs):
        stdout = "build completed" if command == ["lake", "build"] else output
        return subprocess.CompletedProcess(command, 0, stdout, "")

    monkeypatch.setattr(subprocess, "run", run)


@pytest.mark.parametrize("change", ["empty", "missing", "duplicate", "extra", "axiom"])
def test_success_exit_cannot_replace_a_complete_matching_census(verifier, monkeypatch, change: str) -> None:
    rows = report_rows()
    outputs = {
        "empty": "",
        "missing": "\n".join(rows[:-1]),
        "duplicate": "\n".join(rows + rows[:1]),
        "extra": "\n".join(rows + ["'unrelated.example' does not depend on any axioms"]),
        "axiom": "\n".join(rows).replace("propext", "sorryAx", 1),
    }
    fake_lake(monkeypatch, outputs[change])
    assert verifier.check_lean()


def test_matching_named_output_passes_only_the_mocked_control_logic(verifier, monkeypatch) -> None:
    fake_lake(monkeypatch, "\n".join(report_rows()))
    assert verifier.check_lean() == []


def test_stale_census_is_refused_before_build(verifier, monkeypatch, tmp_path: Path) -> None:
    shutil.copytree(ROOT / "lean4", tmp_path / "lean4", ignore=shutil.ignore_patterns(".lake"))
    with (tmp_path / "lean4" / "Census.lean").open("a") as handle:
        handle.write("\n-- stale generated census\n")
    monkeypatch.setattr(verifier, "ROOT", tmp_path)

    def refuse(*args, **kwargs):
        raise AssertionError("a build should not start for a stale census")

    monkeypatch.setattr(subprocess, "run", refuse)
    assert "stale generated census" in verifier.check_lean()[0]
