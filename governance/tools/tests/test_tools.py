"""Evidence capture, Gate 5 metrics and the mutation campaign runner.

AuthorityEffect: None.
Contract: urn:pfp-governance:tests:tools:v1
"""

from __future__ import annotations

import ast
import io
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from governance.tools import evidence, metrics, mutation
from governance.tools.checker import Repository, RunRecord
from governance.tools.mutation import Outcome
from governance.tools.tests.helpers import digest

# --- evidence ---------------------------------------------------------------


def test_capture_records_what_ran(repo: Path) -> None:
    command = [sys.executable, "-c", "print('hello'); print('world'); raise SystemExit(3)"]
    record = evidence.capture(Repository(repo), "unit", command, ["pytest", "no-such-dist"])
    assert record.exit_status == 3
    assert record.command == tuple(command)
    assert record.tool_versions["no-such-dist"] == "not installed"
    assert record.tool_versions["python"] == sys.version.split()[0]
    assert [item.path for item in record.inputs] == ["pfp_lab/mod.py", "pfp_lab/tests/test_mod.py"]
    log = repo / "governance" / "evidence" / "unit.log"
    assert log.read_bytes().startswith(b"hello\nworld\n")
    assert record.report.sha256 == digest(log)
    saved = RunRecord.model_validate_json((repo / "governance" / "evidence" / "unit.run.json").read_bytes())
    assert saved == record
    assert record.started <= record.finished


def test_capture_timeout(repo: Path) -> None:
    command = [sys.executable, "-c", "import time; time.sleep(5)"]
    record = evidence.capture(Repository(repo), "slow", command, [], timeout=1)
    assert record.exit_status == -1
    assert (repo / "governance" / "evidence" / "slow.log").read_bytes().endswith(b"TIMEOUT\n")


def test_evidence_main(monkeypatch: pytest.MonkeyPatch, repo: Path) -> None:
    monkeypatch.setattr(evidence, "ROOT", repo)
    out = io.StringIO()
    assert evidence.main(["ok", "--", sys.executable, "-c", "pass"], out) == 0
    assert out.getvalue() == "ok: exit 0; 2 inputs hashed\n"
    assert evidence.main(["bad", "--", sys.executable, "-c", "raise SystemExit(4)"], io.StringIO()) == 4
    assert (
        evidence.main(
            ["slow", "--timeout", "1", "--", sys.executable, "-c", "import time; time.sleep(5)"], io.StringIO()
        )
        == 1
    )
    for argv in (["none"], ["../x", "--", "cmd"], [".hidden", "--", "cmd"], ["a/b", "--", "cmd"]):
        assert evidence.main(argv, io.StringIO()) == 2


# --- metrics ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("metric", "value", "grade"),
    [
        ("ccn", 10, "A+"),
        ("ccn", 11, "B"),
        ("ccn", 15, "B"),
        ("ccn", 16, "C"),
        ("ccn", 20, "C"),
        ("ccn", 21, "D"),
        ("ccn", 50, "D"),
        ("ccn", 51, "E"),
        ("cognitive", 15, "A+"),
        ("cognitive", 16, "B"),
        ("cognitive", 41, "E"),
        ("nesting", 3, "A+"),
        ("nesting", 4, "B"),
        ("nesting", 5, "C"),
        ("nesting", 8, "D"),
        ("nesting", 9, "E"),
        ("nesting", None, "A+"),
    ],
)
def test_bands_follow_the_ceiling_table(metric: str, value: int | None, grade: str) -> None:
    assert metrics.band(metric, value) == grade


NESTED = """
def f(x):
    if x:
        for y in x:
            while y:
                with open(y):
                    pass
    elif x > 1:
        pass
    else:
        def inner():
            if x:
                if x:
                    pass
"""


def test_nesting_depth_counts_blocks_not_elif_or_inner_scopes(tmp_path: Path) -> None:
    function = ast.parse(NESTED).body[0]
    assert metrics.nesting_depth(function) == 4
    source = tmp_path / "n.py"
    source.write_text(NESTED, encoding="utf-8")
    assert metrics.python_nesting(source) == 4
    flat = tmp_path / "flat.py"
    flat.write_text("if True:\n    X = 1\n", encoding="utf-8")
    assert metrics.python_nesting(flat) == 1


def test_file_metrics_and_report(tmp_path: Path) -> None:
    source = tmp_path / "n.py"
    source.write_text(NESTED, encoding="utf-8")
    measured = metrics.file_metrics(source)
    assert measured["nesting_max"] == 4
    assert measured["gate5_ceiling"] == "B"
    assert measured["functions"] == 2
    csharp = tmp_path / "A.cs"
    csharp.write_text("class A { int F(int x) { if (x > 0) { return 1; } return 0; } }\n", encoding="utf-8")
    measured_cs = metrics.file_metrics(csharp)
    assert (measured_cs["ccn_max"], measured_cs["cognitive_max"]) == (2, None)
    out = io.StringIO()
    target = tmp_path / "report.json"
    monkey_cwd = Path.cwd()
    try:
        import os

        os.chdir(tmp_path)
        assert metrics.main([str(target), "n.py", "A.cs"], out) == 0
    finally:
        os.chdir(monkey_cwd)
    assert set(json.loads(target.read_text(encoding="utf-8"))) == {"n.py", "A.cs"}
    assert out.getvalue() == "2 files; lowest Gate 5 ceiling B\n"
    assert metrics.main(["only-one"], io.StringIO()) == 2


# --- mutation -----------------------------------------------------------------

SAMPLE = """
def check(x, flag=True):
    if x == 1 and not flag:
        raise ValueError("bad")
    return x + 2 * 3
"""


def test_sites_cover_each_operator() -> None:
    found = [site.description for site in mutation.sites(SAMPLE)]
    assert found == [
        "return value -> return None",
        "True -> False",
        "And -> Or",
        "raise -> pass",
        "Add -> Sub",
        "Eq -> NotEq",
        "remove not",
        "Mult -> Add",
        "1 -> 2",
        "2 -> 3",
        "3 -> 4",
    ]


def test_mutants_change_one_thing() -> None:
    text = mutation.mutant(SAMPLE, 5)
    assert "x != 1" in text
    assert "x + 2 * 3" in text
    assert mutation.mutant(SAMPLE, 0).endswith("    return\n")
    assert "flag=False" in mutation.mutant(SAMPLE, 1)
    assert "raise" not in mutation.mutant(SAMPLE, 3)
    assert "if x == 1 and flag" in mutation.mutant(SAMPLE, 6)


def test_annotations_and_main_guard_are_not_mutated() -> None:
    source = "def f(x: int = 1) -> bool:\n    return x\nif __name__ == '__main__':\n    f()\n"
    assert [site.description for site in mutation.sites(source)] == ["return value -> return None", "1 -> 2"]
    assert mutation.sites("def f():\n    return None\n") == []


def test_compiles_and_classify() -> None:
    assert mutation.compiles("x = 1\n")
    assert not mutation.compiles("x = (\n")
    assert [mutation.classify(code) for code in (0, 1, 2, 5, None)] == [
        Outcome.SURVIVED,
        Outcome.KILLED,
        Outcome.INCONCLUSIVE,
        Outcome.INCONCLUSIVE,
        Outcome.INCONCLUSIVE,
    ]


def test_conservative_ratio_matches_rubric_example() -> None:
    counts = {
        Outcome.KILLED: 8,
        Outcome.SURVIVED: 1,
        Outcome.EQUIVALENT: 2,
        Outcome.INVALID: 3,
        Outcome.INCONCLUSIVE: 1,
        Outcome.UNRUN: 0,
    }
    assert mutation.conservative_ratio(counts) == Fraction(4, 5)
    assert mutation.conservative_ratio(dict.fromkeys(Outcome, 0)) is None


def test_split_command() -> None:
    assert mutation.split_command(["a", "--", "b", "--", "c"]) == (["a"], ["b", "--", "c"])
    assert mutation.split_command(["a"]) == (["a"], [])


@pytest.fixture
def project(repo: Path) -> Path:
    (repo / "pfp_lab" / "calc.py").write_text(
        "def double(x):\n    return x * 2\n\n\ndef unused():\n    return 1\n", encoding="utf-8"
    )
    (repo / "pfp_lab" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "pfp_lab" / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "pfp_lab" / "tests" / "test_calc.py").write_text(
        "from pfp_lab.calc import double\n\n\ndef test_double():\n    assert double(3) == 6\n", encoding="utf-8"
    )
    return repo


def test_campaign_end_to_end(project: Path) -> None:
    target = project / "pfp_lab" / "calc.py"
    original = target.read_bytes()
    equivalents = project / "eq.json"
    equivalents.write_text(
        json.dumps(
            {
                "equivalents": [
                    {
                        "path": "pfp_lab/calc.py",
                        "index": 3,
                        "description": "1 -> 2",
                        "sha256": digest(target),
                        "justification": "for the test",
                    },
                    {
                        "path": "pfp_lab/calc.py",
                        "index": 1,
                        "description": "return value -> return None",
                        "sha256": "0" * 64,
                        "justification": "stale hash is ignored",
                    },
                    {
                        "path": "pfp_lab/calc.py",
                        "index": 4,
                        "description": "2 -> 3",
                        "sha256": digest(target),
                        "justification": "",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    out = io.StringIO()
    argv = [
        "unit",
        "--target",
        "pfp_lab/calc.py",
        "--equivalent",
        str(equivalents),
        "--max",
        "3",
        "--",
        "pfp_lab/tests/test_calc.py",
    ]
    assert mutation.main(argv, out, root=project) == 0
    assert target.read_bytes() == original
    report = json.loads((project / "governance" / "evidence" / "unit.mutation.json").read_text(encoding="utf-8"))
    outcomes = [(item["description"], item["outcome"]) for item in report["mutants"]]
    assert outcomes == [
        ("return value -> return None", "killed"),
        ("return value -> return None", "survived"),
        ("Mult -> Add", "killed"),
        ("1 -> 2", "demonstrably_equivalent"),
        ("2 -> 3", "unrun"),
    ]
    assert report["totals"]["conservative_ratio"] == "1/2"
    assert report["per_file"]["pfp_lab/calc.py"]["killed"] == 2
    assert report["targets"]["pfp_lab/calc.py"] == digest(target)
    assert not (project / "governance" / "evidence" / "unit.journal").exists()


def test_budget_marks_the_rest_unrun(project: Path) -> None:
    argv = ["cap", "--target", "pfp_lab/calc.py", "--max", "1", "--", "pfp_lab/tests/test_calc.py"]
    assert mutation.main(argv, io.StringIO(), root=project) == 0
    report = json.loads((project / "governance" / "evidence" / "cap.mutation.json").read_text(encoding="utf-8"))
    assert [item["outcome"] for item in report["mutants"]] == ["killed", "unrun", "unrun", "unrun", "unrun"]


def test_failing_baseline_and_journal_recovery(project: Path) -> None:
    (project / "pfp_lab" / "tests" / "test_fail.py").write_text("def test_no():\n    assert False\n", encoding="utf-8")
    out = io.StringIO()
    assert mutation.main(["x", "--target", "pfp_lab/calc.py", "--", "pfp_lab/tests"], out, root=project) == 2
    assert "does not pass" in out.getvalue()
    target = project / "pfp_lab" / "calc.py"
    original = target.read_bytes()
    journal = project / "governance" / "evidence" / "x.journal"
    journal.parent.mkdir(parents=True, exist_ok=True)
    import base64

    journal.write_text(
        json.dumps({"path": "pfp_lab/calc.py", "bytes": base64.b64encode(original).decode()}), encoding="utf-8"
    )
    target.write_text("broken\n", encoding="utf-8")
    blocked = io.StringIO()
    assert mutation.main(["x", "--target", "pfp_lab/calc.py"], blocked, root=project) == 2
    assert "--recover" in blocked.getvalue()
    recovered = io.StringIO()
    assert mutation.main(["x", "--recover"], recovered, root=project) == 0
    assert (recovered.getvalue(), target.read_bytes()) == ("restored\n", original)
    nothing = io.StringIO()
    assert mutation.main(["x", "--recover"], nothing, root=project) == 0
    assert nothing.getvalue() == "no journal\n"


def test_invalid_and_inconclusive_outcomes(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    campaign = mutation.Campaign(project, "y", ["pfp_lab/tests/test_calc.py"], timeout=60)
    target = project / "pfp_lab" / "calc.py"
    monkeypatch.setattr(mutation, "compiles", lambda text, suffix: False)
    results = campaign.mutate_file(target, set(), budget=10)
    assert {item.outcome for item in results} == {Outcome.INVALID}
    monkeypatch.setattr(mutation, "compiles", lambda text, suffix: True)
    monkeypatch.setattr(campaign, "run_tests", lambda: None)
    assert {item.outcome for item in campaign.mutate_file(target, set(), budget=10)} == {Outcome.INCONCLUSIVE}


def test_run_tests_timeout(project: Path) -> None:
    (project / "pfp_lab" / "tests" / "test_slow.py").write_text(
        "import time\n\n\ndef test_slow():\n    time.sleep(10)\n", encoding="utf-8"
    )
    campaign = mutation.Campaign(project, "z", ["pfp_lab/tests/test_slow.py"], timeout=2)
    assert campaign.run_tests() is None


# --- C# lexical mutants and the command runner ----------------------------------

CSHARP = (
    'if (a == b && c != "x == y") { return true; } // a == b\n'
    "var list = new List<int>(); if (n < 3 || m >= 4 || k <= 2 || j > 1) { throw new E(); }\n"
)


def test_lexical_sites_skip_strings_comments_and_generics() -> None:
    from governance.tools.mutation import mask

    assert mask('x = "a == b"; // c == d') == 'x = "      ";' + " " * 10
    found = [(site.line, site.description) for site in mutation.lexical_sites(CSHARP)]
    assert found == [
        (1, "== -> !="),
        (1, "!= -> =="),
        (1, "&& -> ||"),
        (1, "true -> false"),
        (2, "|| -> &&"),
        (2, "|| -> &&"),
        (2, "|| -> &&"),
        (2, "<= -> >"),
        (2, ">= -> <"),
        (2, "< -> >="),
        (2, "> -> <="),
        (2, "throw new -> _ = new"),
    ]
    assert mutation.sites(CSHARP, ".cs")[0].description == "== -> !="
    assert mutation.lexical_mutant(CSHARP, 0).startswith('if (a != b && c != "x == y")')
    assert "_ = new E();" in mutation.mutant(CSHARP, 11, ".cs")
    assert mutation.lexical_mutant("a\r\nb == c\r\n", 0) == "a\r\nb != c\r\n"
    assert mutation.compiles("not python (", ".cs")


def test_classify_with_custom_exit_codes() -> None:
    killed, invalid = frozenset({3}), frozenset({1})
    assert [mutation.classify(code, killed, invalid) for code in (0, 3, 1, 2, None)] == [
        Outcome.SURVIVED,
        Outcome.KILLED,
        Outcome.INVALID,
        Outcome.INCONCLUSIVE,
        Outcome.INCONCLUSIVE,
    ]


def test_command_runner_runs_the_words_given(project: Path) -> None:
    script = project / "check.py"
    script.write_text(
        "import sys\nfrom pathlib import Path\n"
        "text = Path('pfp_lab/calc.py').read_text()\n"
        "sys.exit(0 if 'x * 2' in text else (1 if 'broken' in text else 3))\n",
        encoding="utf-8",
    )
    argv = [
        "cmd",
        "--target",
        "pfp_lab/calc.py",
        "--runner",
        "command",
        "--killed-exit",
        "3",
        "--invalid-exit",
        "1",
        "--",
        sys.executable,
        str(script),
    ]
    assert mutation.main(argv, io.StringIO(), root=project) == 0
    report = json.loads((project / "governance" / "evidence" / "cmd.mutation.json").read_text(encoding="utf-8"))
    assert [item["outcome"] for item in report["mutants"]] == ["killed", "survived", "killed", "survived", "killed"]


def test_evidence_records_a_command_that_cannot_start(repo: Path) -> None:
    record = evidence.capture(Repository(repo), "missing", [str(repo / "no-such-program.exe")], [])
    assert record.exit_status == evidence.NOT_STARTED
    assert (repo / "governance" / "evidence" / "missing.log").read_bytes().startswith(b"COULD NOT START:")


def test_csharp_nesting_counts_braces_below_members(tmp_path: Path) -> None:
    source = tmp_path / "B.cs"
    source.write_text(
        'namespace N;\nclass B\n{\n    void F()\n    {\n        if (x) { while (y) { Z("{{{"); } } // {\n    }\n}\n',
        encoding="utf-8",
    )
    assert metrics.csharp_nesting(source) == 2
    assert metrics.file_metrics(source)["nesting_max"] == 2
    flat = tmp_path / "C.cs"
    flat.write_text("namespace N;\nclass C { }\n", encoding="utf-8")
    assert metrics.csharp_nesting(flat) == 0


def test_collection_errors_count_as_killed_only_for_pytest(project: Path) -> None:
    (project / "pfp_lab" / "tests" / "test_import.py").write_text(
        "from pfp_lab.calc import double\n\nVALUE = 1 // (double(1) - 1)\n\n\ndef test_v():\n    assert VALUE\n",
        encoding="utf-8",
    )
    target = project / "pfp_lab" / "calc.py"
    target.write_text("def double(x):\n    return x * 1\n", encoding="utf-8")
    campaign = mutation.Campaign(project, "c", ["pfp_lab/tests/test_import.py"], timeout=60)
    assert campaign.run_tests() == mutation.PYTEST_FAILED
    assert mutation._collection_failed(b"1 error\nERROR collecting pfp_lab/tests/x.py")
    assert not mutation._collection_failed(b"Interrupted: KeyboardInterrupt")
    command = mutation.Campaign(
        project, "d", [sys.executable, "-c", "raise SystemExit(2)"], timeout=60, runner="command"
    )
    assert command.run_tests() == 2
