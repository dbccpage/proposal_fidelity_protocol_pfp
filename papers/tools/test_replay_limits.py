"""Negative controls for the bounded, source-bound paper replay runner."""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPLAY = Path(__file__).resolve().parents[1] / "replay_completion.py"
spec = importlib.util.spec_from_file_location("current_paper_replay", REPLAY)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_expired_deadline_starts_no_test_process(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("an expired deadline must not start a test process")

    monkeypatch.setattr(runner, "run_test_command", forbidden)
    output = tmp_path / "expired.json"
    assert runner.replay(output, deadline=datetime.now(timezone.utc) - timedelta(seconds=1)) == 1
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert not receipt["selected_commands_succeeded"]
    assert not receipt["all_selected_tests_passed"]
    assert receipt["checks"][0]["exit_code"] == 124
    assert "not started" in receipt["checks"][0]["stderr"]
    assert receipt["test_counts"]["passed"] == 0


def test_timeout_terminates_the_spawned_descendant():
    child_code = "import time; time.sleep(120)"
    parent_code = "import subprocess,sys,time; child=subprocess.Popen([sys.executable,'-c'," + repr(child_code) + "]); print(child.pid,flush=True); time.sleep(120)"
    code, stdout, stderr = runner.run_test_command([sys.executable, "-c", parent_code], REPLAY.parent, dict(os.environ), 1)
    assert code == 124
    assert "process tree exceeded" in stderr
    child_pid = int(stdout.strip().splitlines()[0])
    if os.name == "nt":
        result = subprocess.run(["tasklist", "/FI", f"PID eq {child_pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True, check=True)
        rows = list(csv.reader(io.StringIO(result.stdout)))
        assert all(len(row) < 2 or row[1] != str(child_pid) for row in rows)
    else:
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)


def test_expired_notebook_deadline_starts_no_kernel(monkeypatch):
    def forbidden():
        raise AssertionError("an expired notebook deadline must not inspect or start a kernel")

    monkeypatch.setattr(runner, "packages", forbidden)
    with pytest.raises(ValueError, match="not started"):
        runner.notebook_replay(deadline=datetime.now(timezone.utc) - timedelta(seconds=1))


def test_notebook_environment_retains_assertions_and_excludes_provider_keys(monkeypatch):
    for name in ("PYTHONOPTIMIZE", "PYTHONPATH", "OPENAI_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.setenv(name, "negative-control")
    environment = runner.notebook_environment()
    for name in ("PYTHONOPTIMIZE", "PYTHONPATH", "OPENAI_API_KEY", "OPENROUTER_API_KEY"):
        assert name not in environment
    result = subprocess.run([sys.executable, "-c", "import sys; print(sys.flags.optimize, __debug__)"], env=environment, capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "0 True"
