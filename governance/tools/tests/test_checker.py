"""The acceptance floor: population, binding, arithmetic, evidence and mutation checks.

AuthorityEffect: None.
Contract: urn:pfp-governance:tests:checker:v1
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest

from governance.tools import checker
from governance.tools.checker import (
    MutationAccounting,
    Repository,
    ScoreRecord,
    check_source,
    glob_regex,
    matches,
    mutation_problems,
    score_problems,
)
from governance.tools.tests.helpers import digest, git, records_for, write_records


def record(repo: Path, path: str = "pfp_lab/mod.py", **changes: Any) -> int:
    contract, score = records_for(repo, path, **changes)
    contract_file, score_file = write_records(repo, contract, score)
    return checker.main(
        ["--root", str(repo), "record", path, "--contract", str(contract_file), "--score", str(score_file)],
        io.StringIO(),
    )


def run(repo: Path, *argv: str) -> tuple[int, str]:
    out = io.StringIO()
    code = checker.main(["--root", str(repo), *argv], out)
    return code, out.getvalue()


@pytest.mark.parametrize(
    ("pattern", "path", "expected"),
    [
        ("pfp_lab/**/*.py", "pfp_lab/a.py", True),
        ("pfp_lab/**/*.py", "pfp_lab/x/y/a.py", True),
        ("pfp_lab/**/*.py", "pfp_lab/a.pyc", False),
        ("pfp_lab/**/*.py", "other/pfp_lab/a.py", False),
        ("pfp_lab/*.py", "pfp_lab/x/a.py", False),
        ("a?.cs", "ab.cs", True),
        ("a?.cs", "a/.cs", False),
        ("a.b", "axb", False),
    ],
)
def test_glob(pattern: str, path: str, expected: bool) -> None:
    assert bool(glob_regex(pattern).match(path)) is expected
    assert matches(path, [pattern]) is expected


def test_population_and_categories(repo: Path) -> None:
    code, out = run(repo, "population")
    assert (code, out.splitlines()) == (0, ["pfp_lab/mod.py", "pfp_lab/tests/test_mod.py"])
    repository = Repository(repo)
    assert repository.floor_for("pfp_lab/mod.py") == ("runtime", "L4", "D")
    assert repository.floor_for("pfp_lab/tests/test_mod.py") == ("test", "L2", "D")
    assert repository.language("csharp/App/X.cs") == "C#"
    assert repository.language("pfp_lab/__pycache__/x.py") is None
    assert repository.language("notes.txt") is None


def test_missing_companion_fails(repo: Path) -> None:
    code, out = run(repo, "check")
    assert code == 1
    assert "FAIL pfp_lab/mod.py: missing companion pfp_lab/mod.contract.score.json" in out
    assert out.rstrip().endswith("0/2 governed sources meet the floor")


def test_record_then_check_and_explain(repo: Path) -> None:
    assert record(repo) == 0
    assert record(repo, "pfp_lab/tests/test_mod.py", level="L2", score_token="L2C") == 0
    assert run(repo, "check")[0] == 0
    code, out = run(repo, "explain", "pfp_lab/mod.py")
    assert code == 0
    assert "category runtime; floor L4D" in out
    assert "recorded score L4C" in out
    assert out.rstrip().endswith("ACCEPTED")
    assert run(repo, "explain", "notes.txt") == (1, "notes.txt is not a governed source\n")


def test_record_keeps_history(repo: Path) -> None:
    record(repo)
    record(repo, gates={"G1": "B", "G2": "B", "G3": "B", "G4": "B", "G5": "B"}, composite_grade="B", score_token="L4B")
    companion = json.loads((repo / "pfp_lab" / "mod.contract.score.json").read_text(encoding="utf-8"))
    assert companion["score"]["score_token"] == "L4B"
    assert [entry["score"]["score_token"] for entry in companion["history"]] == ["L4C"]


def test_changed_bytes_break_the_binding(repo: Path) -> None:
    record(repo)
    (repo / "pfp_lab" / "mod.py").write_text("VALUE = 2\n", encoding="utf-8")
    problems = check_source(Repository(repo), "pfp_lab/mod.py")
    assert problems == [
        "contract does not bind the current bytes of pfp_lab/mod.py",
        "score does not bind the current bytes of pfp_lab/mod.py",
    ]


def test_baseline_grandfathers_unchanged_bytes_only(repo: Path) -> None:
    baseline = repo / "governance" / "baseline.json"
    body = json.loads(baseline.read_text(encoding="utf-8"))
    body["entries"] = {
        "pfp_lab/mod.py": {"sha256": digest(repo / "pfp_lab" / "mod.py"), "reason": "existing"},
        "pfp_lab/tests/test_mod.py": {"sha256": "0" * 64, "reason": "stale"},
    }
    baseline.write_text(json.dumps(body), encoding="utf-8")
    code, out = run(repo, "check", "--json")
    assert code == 1
    assert list(json.loads(out)["failing"]) == ["pfp_lab/tests/test_mod.py"]


def test_changed_since_selects_changed_sources(repo: Path) -> None:
    record(repo, "pfp_lab/tests/test_mod.py", level="L2", score_token="L2C")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "scored test")
    code, out = run(repo, "check", "--changed-since", "HEAD")
    assert (code, out) == (0, "0/0 governed sources meet the floor\n")
    (repo / "pfp_lab" / "new.py").write_text("X = 1\n", encoding="utf-8")
    code, out = run(repo, "check", "--changed-since", "HEAD")
    assert code == 1
    assert "pfp_lab/new.py: missing companion" in out
    assert "mod.py" not in out


def test_language_and_path_mismatch(repo: Path) -> None:
    contract, score = records_for(repo, "pfp_lab/mod.py")
    score["artifact"] = {**score["artifact"], "language": "C#"}
    companion = {
        "schema_version": "pfp.contract-score.v1",
        "AuthorityEffect": "None",
        "artifact": "pfp_lab/other.py",
        "contract": contract,
        "score": score,
        "history": [],
    }
    (repo / "pfp_lab" / "mod.contract.score.json").write_text(json.dumps(companion), encoding="utf-8")
    problems = check_source(Repository(repo), "pfp_lab/mod.py")
    assert problems == ["companion names pfp_lab/other.py, not pfp_lab/mod.py", "score language C# is not Python"]


def test_malformed_companion(repo: Path) -> None:
    (repo / "pfp_lab" / "mod.contract.score.json").write_text("{}", encoding="utf-8")
    assert check_source(Repository(repo), "pfp_lab/mod.py")[0].startswith("companion is malformed")
    code, out = run(repo, "explain", "pfp_lab/mod.py")
    assert "companion is malformed" in out


def score(repo: Path, **changes: Any) -> ScoreRecord:
    return ScoreRecord.model_validate_json(json.dumps(records_for(repo, "pfp_lab/mod.py", **changes)[1]))


def test_score_arithmetic_and_floor(repo: Path) -> None:
    assert score_problems(score(repo), "L4", "D") == []
    incomplete = score(repo, gates={"G1": None, "G2": "B", "G3": "C", "G4": "C", "G5": "A"})
    assert score_problems(incomplete, "L4", "D") == [
        "score is incomplete: every gate must be graded and is_complete true"
    ]
    assert score_problems(score(repo, is_complete=False), "L4", "D")[0].startswith("score is incomplete")
    wrong = score(repo, composite_grade="B", score_token="L4C", grade_ceiling="C", basis={"G1": "only one"})
    assert score_problems(wrong, "L4", "D") == [
        "composite_grade B is not the weakest gate C",
        "score_token L4C is not level + composite",
        "basis must give the reasoning for all five gates",
        "grade_ceiling is below the composite grade",
    ]
    low = score(
        repo,
        level="L3",
        score_token="L3E",
        composite_grade="E",
        gates={"G1": "E", "G2": "B", "G3": "C", "G4": "C", "G5": "A"},
    )
    assert score_problems(low, "L4", "D") == ["level L3 is below the floor L4", "grade E is below the floor D"]
    assert score_problems(score(repo), "L4", "C") == []
    assert score_problems(score(repo), "L5", "B") == ["level L4 is below the floor L5", "grade C is below the floor B"]


def accounting(**counts: Any) -> MutationAccounting:
    base: dict[str, Any] = {
        "killed": 8,
        "survived": 1,
        "demonstrably_equivalent": 2,
        "invalid": 3,
        "inconclusive": 1,
        "unrun": 0,
        "conservative_ratio": 0.8,
        "report": {"path": "r", "sha256": "0" * 64},
    }
    return MutationAccounting.model_validate_json(json.dumps({**base, **counts}))


def test_mutation_accounting_matches_the_rubric_example() -> None:
    assert mutation_problems(accounting()) == []
    assert mutation_problems(accounting(conservative_ratio=0.75)) == ["conservative_ratio 0.75 is not 8/10"]
    assert mutation_problems(accounting(unrun=10, conservative_ratio=0.4)) == []
    zero = {"killed": 0, "survived": 0, "inconclusive": 0, "unrun": 0}
    assert mutation_problems(accounting(**zero, conservative_ratio=None)) == []
    assert mutation_problems(accounting(**zero)) == ["an empty eligible campaign must report a null ratio"]
    assert mutation_problems(accounting(conservative_ratio=None)) == [
        "conservative_ratio is null for a non-empty campaign"
    ]


def test_evidence_must_resolve_and_be_fresh(repo: Path) -> None:
    evidence = repo / "governance" / "evidence"
    run_record = evidence / "unit.run.json"
    report = evidence / "unit.log"
    evidence.mkdir(parents=True, exist_ok=True)
    report.write_text("ok\n", encoding="utf-8")
    body = {
        "schema_version": "pfp.evidence-run.v1",
        "AuthorityEffect": "None",
        "name": "unit",
        "command": ["pytest"],
        "working_directory": ".",
        "tool_versions": {},
        "started": "2026-10-26T00:00:00Z",
        "finished": "2026-10-26T00:00:01Z",
        "exit_status": 0,
        "inputs": [{"path": "pfp_lab/mod.py", "sha256": "1" * 64}],
        "report": {"path": "governance/evidence/unit.log", "sha256": digest(report)},
    }
    run_record.write_text(json.dumps(body), encoding="utf-8")
    refs = [
        {"path": "governance/evidence/unit.run.json", "sha256": digest(run_record)},
        {"path": "governance/evidence/missing.log", "sha256": "2" * 64},
        {"path": "governance/evidence/unit.log", "sha256": "3" * 64},
    ]
    record(repo, evidence=refs)
    assert check_source(Repository(repo), "pfp_lab/mod.py") == [
        "evidence unit.run.json ran against different bytes of pfp_lab/mod.py (stale)",
        "evidence governance/evidence/missing.log does not exist",
        "evidence governance/evidence/unit.log does not match its cited hash",
    ]
    run_record.write_text("{}", encoding="utf-8")
    refs = [{"path": "governance/evidence/unit.run.json", "sha256": digest(run_record)}]
    record(repo, evidence=refs)
    assert check_source(Repository(repo), "pfp_lab/mod.py") == ["evidence unit.run.json is not a valid run record"]


def test_fresh_run_record_and_mutation_report_are_accepted(repo: Path) -> None:
    evidence = repo / "governance" / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    report = evidence / "m.mutation.json"
    report.write_text("{}", encoding="utf-8")
    mutation = {
        "killed": 3,
        "survived": 1,
        "demonstrably_equivalent": 0,
        "invalid": 0,
        "inconclusive": 0,
        "unrun": 0,
        "conservative_ratio": 0.75,
        "report": {"path": "governance/evidence/m.mutation.json", "sha256": digest(report)},
    }
    assert record(repo, mutation_accounting=mutation) == 0
    mutation["conservative_ratio"] = 0.5
    assert record(repo, mutation_accounting=mutation) == 1


def test_empty_package_markers_are_pinned(repo: Path) -> None:
    marker = repo / "pfp_lab" / "__init__.py"
    marker.write_bytes(b"")
    repository = Repository(repo)
    assert repository.pinned("pfp_lab/__init__.py", digest(marker))
    assert check_source(repository, "pfp_lab/__init__.py") == []
    marker.write_bytes(b"x = 1\n")
    assert not repository.pinned("pfp_lab/__init__.py", digest(marker))
    assert check_source(repository, "pfp_lab/__init__.py")[0].startswith("missing companion")
    assert not repository.pinned("pfp_lab/other.py", digest(repo / "pfp_lab" / "mod.py"))
