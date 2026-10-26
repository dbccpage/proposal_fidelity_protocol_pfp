"""Checker edges that the mutation campaign showed were unpinned.

AuthorityEffect: None.
Contract: urn:pfp-governance:tests:checker-pins:v1
"""

from __future__ import annotations

import io
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from governance.tools import checker
from governance.tools.checker import Companion, MutationAccounting, Repository, ScoreRecord, check_source
from governance.tools.tests.conftest import REAL_ROOT
from governance.tools.tests.helpers import digest, git, records_for, write_records


def run(repo: Path, *argv: str) -> tuple[int, str]:
    out = io.StringIO()
    return checker.main(["--root", str(repo), *argv], out), out.getvalue()


def record(repo: Path, **changes: Any) -> tuple[int, str]:
    contract, score = records_for(repo, "pfp_lab/mod.py", **changes)
    contract_file, score_file = write_records(repo, contract, score)
    return run(repo, "record", "pfp_lab/mod.py", "--contract", str(contract_file), "--score", str(score_file))


def test_root_and_tolerance() -> None:
    assert checker.ROOT == REAL_ROOT
    assert Fraction(1, 1_000_000_000) == checker.RATIO_TOLERANCE


def test_ratio_tolerance_edges() -> None:
    def accounting(ratio: float) -> MutationAccounting:
        body = {
            "killed": 4,
            "survived": 1,
            "demonstrably_equivalent": 0,
            "invalid": 0,
            "inconclusive": 0,
            "unrun": 0,
            "conservative_ratio": ratio,
            "report": {"path": "r", "sha256": "0" * 64},
        }
        return MutationAccounting.model_validate_json(json.dumps(body))

    assert checker.mutation_problems(accounting(0.8000000005)) == []
    assert checker.mutation_problems(accounting(0.800001)) != []


def test_explain_and_record_report_failures(repo: Path) -> None:
    code, out = record(repo, level="L3", score_token="L3C")
    assert code == 1
    assert "NOT accepted" in out
    code, out = run(repo, "explain", "pfp_lab/mod.py")
    assert code == 1
    assert out.rstrip().endswith("NOT ACCEPTED")


def test_outputs_are_indented_json(repo: Path) -> None:
    record(repo)
    text = (repo / "pfp_lab" / "mod.contract.score.json").read_text(encoding="utf-8")
    assert text.startswith('{\n  "schema_version": "pfp.contract-score.v1",\n  "AuthorityEffect": "None"')
    code, out = run(repo, "check", "--json")
    assert out.startswith('{\n  "checked": 2,\n  "failing": {')


def test_command_line_requirements(repo: Path) -> None:
    for argv in (
        [],
        ["record", "pfp_lab/mod.py", "--score", "s.json"],
        ["record", "pfp_lab/mod.py", "--contract", "c"],
    ):
        with pytest.raises(SystemExit) as caught:
            checker.main(["--root", str(repo), *argv], io.StringIO())
        assert caught.value.code == 2
    assert (
        checker.build_parser().description
        == "Enforce the SCORING.md section 1.5 acceptance floor on every governed source."
    )


def test_git_failures_are_reported(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    code, out = run(repo, "check", "--changed-since", "no-such-ref")
    assert code == checker.USAGE_ERROR
    assert out.startswith("governance-check: git merge-base no-such-ref HEAD failed")
    monkeypatch.setattr("shutil.which", lambda name: None)
    with pytest.raises(FileNotFoundError, match="git is required"):
        Repository(repo).population()


def test_fresh_run_record_without_this_source(repo: Path) -> None:
    evidence = repo / "governance" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    log = evidence / "u.log"
    log.write_text("ok\n", encoding="utf-8")
    source_digest = digest(repo / "pfp_lab" / "mod.py")
    for name, inputs in (
        ("other.run.json", [{"path": "x.py", "sha256": "1" * 64}]),
        ("fresh.run.json", [{"path": "pfp_lab/mod.py", "sha256": source_digest}]),
    ):
        (evidence / name).write_text(
            json.dumps(
                {
                    "schema_version": "pfp.evidence-run.v1",
                    "AuthorityEffect": "None",
                    "name": "u",
                    "command": ["x"],
                    "working_directory": ".",
                    "tool_versions": {},
                    "started": "2026-10-26T00:00:00Z",
                    "finished": "2026-10-26T00:00:01Z",
                    "exit_status": 0,
                    "inputs": inputs,
                    "report": {"path": "governance/evidence/u.log", "sha256": digest(log)},
                }
            ),
            encoding="utf-8",
        )
    refs = [
        {"path": f"governance/evidence/{name}", "sha256": digest(evidence / name)}
        for name in ("other.run.json", "fresh.run.json")
    ]
    assert record(repo, evidence=refs)[0] == 0
    assert check_source(Repository(repo), "pfp_lab/mod.py") == []


def test_changed_companion_selects_its_source(repo: Path) -> None:
    record(repo)
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "scored")
    companion = repo / "pfp_lab" / "mod.contract.score.json"
    companion.write_text(companion.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    code, out = run(repo, "check", "--changed-since", "HEAD")
    assert out.rstrip().endswith("1/1 governed sources meet the floor")


def test_records_are_strict_frozen_and_need_a_level_basis(repo: Path) -> None:
    contract, score = records_for(repo, "pfp_lab/mod.py")
    parsed = ScoreRecord.model_validate_json(json.dumps(score))
    with pytest.raises(ValidationError):
        parsed.level = "L5"  # type: ignore[misc]
    for change in ({"level_basis": ""}, {"is_complete": "true"}):
        with pytest.raises(ValidationError):
            ScoreRecord.model_validate_json(json.dumps({**score, **change}))


def test_malformed_companion_names_the_first_problem(repo: Path) -> None:
    contract, score = records_for(repo, "pfp_lab/mod.py")
    body = {
        "schema_version": "pfp.contract-score.v1",
        "AuthorityEffect": "None",
        "artifact": "pfp_lab/mod.py",
        "contract": contract,
        "score": score,
    }
    (repo / "pfp_lab" / "mod.contract.score.json").write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(ValidationError) as caught:
        Companion.model_validate_json(json.dumps(body))
    expected = f"companion is malformed: 1 problem(s): {caught.value.errors()[0]['msg']}"
    assert check_source(Repository(repo), "pfp_lab/mod.py") == [expected]
