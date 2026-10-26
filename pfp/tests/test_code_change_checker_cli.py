"""Actual canonical CLI consumer of the independently configured native checker."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from omega_engine_pfp.ffi import find_omega_symbol_game_binary
from omega_engine_pfp.use_cases.code_change import CreateCodeChangeProposalUseCase

_REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def command(tmp_path):
    root = tmp_path / "source"
    (root / "src").mkdir(parents=True)
    (root / "src/x.py").write_bytes(b"x = 0\n")
    packet = tmp_path / "packet.json"
    session = CreateCodeChangeProposalUseCase().execute(
        task_id="cli-finite",
        objective="Check one finite patch",
        base_revision="a" * 40,
        owned_paths=("src/x.py",),
        protected_paths=("README.md",),
    )
    packet.write_text(json.dumps(session.envelope.to_dict()), encoding="utf-8")
    patch = tmp_path / "candidate.diff"
    patch.write_bytes(b"--- a/src/x.py\n+++ b/src/x.py\n@@ -1,1 +1,1 @@\n-x = 0\n+x = 1\n")
    binary = find_omega_symbol_game_binary()
    return [
        sys.executable,
        "-m",
        "omega_engine_pfp",
        "code-change-check-source-bound",
        "--packet",
        str(packet),
        "--patch-bytes",
        str(patch),
        "--source-root",
        str(root),
        "--source-path",
        "src/x.py",
        "--checker-binary",
        str(binary),
        "--checker-sha256",
        hashlib.sha256(binary.read_bytes()).hexdigest(),
        "--run-id",
        "cli-run",
        "--attempt-id",
        "attempt-0",
        "--max-native-calls",
        "3",
        "--output",
        str(tmp_path / "result.json"),
        "--replay-check",
    ]


def _run(command):
    environ = dict(os.environ)
    environ.pop("OPENROUTER_API_KEY", None)
    return subprocess.run(
        command, cwd=_REPO, env=environ, capture_output=True, text=True, timeout=60, check=False
    )


def _path(command, option):
    return Path(command[command.index(option) + 1])


def test_actual_pfp_cli_checks_native_patch_and_replays_without_dispatch(command):
    completed = _run(command)
    assert completed.returncode == 0, completed.stderr
    result = json.loads(_path(command, "--output").read_text(encoding="utf-8"))
    assert result["check"]["diagnostic_status"] == "PASS"
    assert result["check"]["authorization_status"] == "HOST_CONFIGURED_CHECKER"
    assert result["check"]["authority_effect"] == "None"
    assert result["native_calls"] == 3
    assert result["provider_calls"] == 0
    assert result["replay_check"] == {"native_calls": 0, "provider_calls": 0, "equal": True}
    assert result["source_files"][0]["path"] == "src/x.py"


def test_actual_pfp_cli_retains_real_native_negative_diagnostic(command):
    patch = _path(command, "--patch-bytes")
    patch.write_bytes(patch.read_bytes().replace(b"src/x.py", b"README.md"))
    completed = _run(command)
    assert completed.returncode == 2, completed.stderr
    result = json.loads(_path(command, "--output").read_text(encoding="utf-8"))
    assert result["check"]["diagnostic_status"] == "FAIL"
    assert "gate_protected_FAILED" in result["check"]["refusal_codes"]
    assert result["native_calls"] == 3
    assert result["replay_check"]["native_calls"] == 0


@pytest.mark.parametrize(
    ("option", "value", "code"),
    [
        ("--source-path", "../outside.py", "CHECKER_INPUT_MALFORMED"),
        ("--checker-sha256", "0" * 64, "CHECKER_PIN_MISMATCH"),
    ],
)
def test_host_input_refusals_precede_native_dispatch(command, option, value, code):
    command[command.index(option) + 1] = value
    completed = _run(command)
    assert completed.returncode == 2, completed.stderr
    result = json.loads(_path(command, "--output").read_text(encoding="utf-8"))
    assert result["refusal"]["code"] == code
    assert result["native_calls"] == result["provider_calls"] == 0


def test_cli_never_overwrites_historical_output(command):
    output = _path(command, "--output")
    original = b"historical evidence\r\n"
    output.write_bytes(original)
    completed = _run(command)
    assert completed.returncode == 2
    assert "CHECKER_OUTPUT_EXISTS" in completed.stderr
    assert output.read_bytes() == original


def test_compatibility_cli_registers_identical_source_bound_command(command):
    from omega_engine_pfp.entrypoints.cli.parser import build_parser

    args = build_parser().parse_args(command[3:])
    assert args.func is not None
    assert args.checker_binary == _path(command, "--checker-binary")
    assert args.source_path == ["src/x.py"]
