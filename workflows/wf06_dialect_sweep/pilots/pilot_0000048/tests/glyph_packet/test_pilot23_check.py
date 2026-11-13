import importlib.util
import json
from pathlib import Path
import runpy
import subprocess
import sys
import types

import pytest
import yaml

SOURCE = Path(__file__).resolve().parents[2] / "check.py"
SPEC = importlib.util.spec_from_file_location("pilot23_check_under_test", SOURCE)
c = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = c
SPEC.loader.exec_module(c)
PRESERVED = json.dumps({"status": "PRESERVED", "output": "kept", "reason": ""}).encode()


class FakeRun:
    """Stands in for subprocess.run and writes the files each check command would produce."""

    def __init__(self, codes=(0, 0, 0), tests=None, failures=0, files=("run.py",), excluded=0, percent=100.0,
                 mutations=None, killed=True, stdout=PRESERVED):
        self.codes, self.failures, self.files, self.excluded, self.percent = codes, failures, files, excluded, percent
        self.tests = c.TESTS if tests is None else tests
        self.mutations = c.MUTATIONS if mutations is None else mutations
        self.killed, self.stdout, self.calls = killed, stdout, []

    def __call__(self, command, **kwargs):
        index = len(self.calls)
        self.calls.append(command)
        assert kwargs["check"] is False and kwargs["cwd"] == c.HERE
        if "--junitxml" in command:
            Path(command[command.index("--junitxml") + 1]).write_text(
                f'<testsuites><testsuite tests="{self.tests}" failures="{self.failures}"/></testsuites>', encoding="utf-8")
            report = Path(command[command.index("--basetemp") + 1]) / "test_compiled_mutations0" / "mutations.json"
            report.parent.mkdir(parents=True)
            report.write_text(json.dumps([{"killed": self.killed}] * self.mutations), encoding="utf-8")
        elif "json" in command:
            totals = {"percent_covered": self.percent, "excluded_lines": self.excluded}
            Path(command[command.index("-o") + 1]).write_text(json.dumps({"files": {n: {} for n in self.files},
                                                                           "totals": totals}), encoding="utf-8")
        return types.SimpleNamespace(returncode=self.codes[index], stdout=self.stdout if index == 2 else b"",
                                     stderr=b"err" if self.codes[index] else b"")


@pytest.fixture
def temporaries(monkeypatch, tmp_path):
    made = []

    def mkdtemp(prefix):
        path = tmp_path / ("t" + str(len(made)))
        path.mkdir()
        made.append(path)
        return str(path)

    monkeypatch.setattr(c.tempfile, "mkdtemp", mkdtemp)
    return made


def launch(monkeypatch, capsys, fake, argv=()):
    monkeypatch.setattr(subprocess, "run", fake)
    code = c.main(list(argv))
    return code, json.loads(capsys.readouterr().out)


def test_pass_cleans_the_temporary_directory(monkeypatch, capsys, temporaries):
    fake = FakeRun()
    code, report = launch(monkeypatch, capsys, fake)
    assert code == 0 and report["status"] == "PASSED" and report["tests_passed"] == c.TESTS and report["output"] is None
    assert [path.exists() for path in temporaries] == [False]
    assert str(c.TEST) in fake.calls[0] and "--output-root" in fake.calls[2]


def test_out_keeps_result_twins(monkeypatch, capsys, temporaries, tmp_path):
    code, report = launch(monkeypatch, capsys, FakeRun(), ["--out", str(tmp_path / "kept")])
    assert code == 0 and report["output"] == str(tmp_path / "kept")
    data = json.loads((tmp_path / "kept" / "result.json").read_bytes())
    assert data == yaml.safe_load((tmp_path / "kept" / "result.yaml").read_bytes()) and data["mutations_killed"] == 15


@pytest.mark.parametrize("fake,reason", [
    (FakeRun(codes=(0, 0, 4)), "command 2 exited 4: err"),
    (FakeRun(tests=76), "expected 77 tests, found 76"),
    (FakeRun(failures=1), "a test failed"),
    (FakeRun(files=("run.py", "check.py")), "coverage scope"),
    (FakeRun(excluded=1), "1 excluded lines"),
    (FakeRun(percent=97.5), "below 98.0%"),
    (FakeRun(mutations=14), "expected 15 killed mutations"),
    (FakeRun(killed=False), "found 0 of 15"),
    (FakeRun(stdout=b"not json"), "not the expected JSON"),
    (FakeRun(stdout=b'{"status": "REJECTED"}'), "expected PRESERVED"),
], ids=["exit-code", "test-count", "failure", "scope", "excluded", "coverage", "mutation-count", "survivor", "syntax",
        "status"])
def test_each_gate_fails_with_a_reason(monkeypatch, capsys, temporaries, fake, reason):
    code, report = launch(monkeypatch, capsys, fake)
    assert code == 1 and report["status"] == "FAILED" and reason in report["reason"]
    assert [path.exists() for path in temporaries] == [False]


def test_script_entry_exit_code(monkeypatch, capsys, temporaries):
    monkeypatch.setattr(subprocess, "run", FakeRun(codes=(1, 0, 0)))
    monkeypatch.setattr(sys, "argv", [str(SOURCE)])
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(str(SOURCE), run_name="__main__")
    assert caught.value.code == 1 and json.loads(capsys.readouterr().out)["status"] == "FAILED"
