import contextlib
import importlib.util
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import types

import pytest

PILOT = Path(__file__).resolve().parents[2]
SOURCE = PILOT / "check.py"
SPEC = importlib.util.spec_from_file_location("pilot24_check_under_test", SOURCE)
c = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = c
SPEC.loader.exec_module(c)
RUN_SPEC = importlib.util.spec_from_file_location("pilot24_check_run", PILOT / "run.py")
r = importlib.util.module_from_spec(RUN_SPEC)
sys.modules[RUN_SPEC.name] = r
RUN_SPEC.loader.exec_module(r)
BREAK = {"answer": 41}


def default_stdout():
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        assert r.main([]) == 0
    return buffer.getvalue().encode("utf-8")


class FakeRun:
    """Stands in for subprocess.run and writes the files each check command would produce."""

    def __init__(self, codes=(0, 0, 0), failure=False, mutants=None, files=("run.py",), excluded=0, percent=100.0,
                 stdout=None):
        self.codes, self.failure, self.files, self.excluded, self.percent = codes, failure, files, excluded, percent
        self.mutants = c.MUTANTS if mutants is None else mutants
        self.stdout, self.calls = stdout, []

    def __call__(self, command, **kwargs):
        index = len(self.calls)
        self.calls.append((command, kwargs))
        assert kwargs["check"] is False and kwargs["cwd"] == c.HERE
        if "--junitxml" in command:
            cases = [f'<testcase name="test_compiled_semantic_mutants[{n}]"/>' for n in range(self.mutants)]
            cases.append('<testcase name="test_other"><failure/></testcase>' if self.failure else '<testcase name="test_other"/>')
            Path(command[command.index("--junitxml") + 1]).write_text("<testsuites><testsuite>" + "".join(cases)
                                                                      + "</testsuite></testsuites>", encoding="utf-8")
        elif "json" in command:
            report = {"files": {name: {} for name in self.files},
                      "totals": {"percent_covered": self.percent, "excluded_lines": self.excluded}}
            Path(command[command.index("-o") + 1]).write_text(json.dumps(report), encoding="utf-8")
        stdout = (default_stdout() if self.stdout is None else self.stdout) if index == 2 else b""
        return types.SimpleNamespace(returncode=self.codes[index], stdout=stdout, stderr=b"err" if self.codes[index] else b"")


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
    assert code == 0 and report["status"] == "PASSED" and report["mutations"] == c.MUTANTS and report["output"] is None
    assert [path.exists() for path in temporaries] == [False]
    assert str(c.TEST) in fake.calls[0][0] and fake.calls[2][0][-1] == str(c.HERE / "run.py")


def test_out_keeps_the_logs(monkeypatch, capsys, temporaries, tmp_path):
    code, report = launch(monkeypatch, capsys, FakeRun(), ["--out", str(tmp_path / "kept")])
    assert code == 0 and report["output"] == str(tmp_path / "kept")
    assert json.loads((tmp_path / "kept" / "result.json").read_bytes())["status"] == "PASSED"
    assert json.loads((tmp_path / "kept" / "return_codes.json").read_bytes()) == [0, 0, 0]


@pytest.mark.parametrize("fake,reason", [
    (FakeRun(codes=(0, 3, 0)), "command 1 exited 3: err"),
    (FakeRun(failure=True), "a test failed"),
    (FakeRun(mutants=1), "killed mutants"),
    (FakeRun(files=("run.py", "check.py")), "expected run.py only"),
    (FakeRun(excluded=2), "2 lines excluded"),
    (FakeRun(percent=97.99), "below 98.0%"),
    (FakeRun(stdout=b"not json"), "not the expected JSON"),
    (FakeRun(stdout=b"{}"), "not the expected JSON"),
    (FakeRun(stdout=b"[]"), "not the expected JSON"),
], ids=["exit-code", "test-failure", "mutant-count", "measured-files", "excluded", "coverage", "syntax", "keys", "type"])
def test_each_gate_fails_with_a_reason(monkeypatch, capsys, temporaries, fake, reason):
    code, report = launch(monkeypatch, capsys, fake)
    assert code == 1 and report["status"] == "FAILED" and reason in report["reason"]
    assert [path.exists() for path in temporaries] == [False]


def test_unexpected_output_shape_fails(monkeypatch, capsys, temporaries):
    record = dict(json.loads(default_stdout()), **BREAK)
    code, report = launch(monkeypatch, capsys, FakeRun(stdout=json.dumps(record).encode()))
    assert code == 1 and "differs from the expected shape" in report["reason"]


def test_script_entry_exit_code(monkeypatch, capsys, temporaries):
    monkeypatch.setattr(subprocess, "run", FakeRun(codes=(1, 0, 0)))
    monkeypatch.setattr(sys, "argv", [str(SOURCE)])
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(str(SOURCE), run_name="__main__")
    assert caught.value.code == 1 and json.loads(capsys.readouterr().out)["status"] == "FAILED"
