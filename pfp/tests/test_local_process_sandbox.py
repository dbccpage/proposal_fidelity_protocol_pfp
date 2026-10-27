"""Unit tests for LocalProcessSandbox (U09).

AuthorityEffect: None.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from operations.domain.rop.result import Err, Ok, Refusal
from operating_system.adapters.rust_host.ffi import RustSandboxHost
from pfp.domain.ports.process_sandbox import SandboxOutcomeKind
from pfp.infrastructure.sandbox.local_process_sandbox import (
    LocalProcessSandbox,
)


@pytest.fixture
def sandbox() -> LocalProcessSandbox:
    return LocalProcessSandbox()


@pytest.mark.skipif(os.name != "nt", reason="POSIX isolation is unavailable")
def test_sandbox_benign_command(sandbox: LocalProcessSandbox) -> None:
    res = sandbox.execute(
        [sys.executable, "-c", "print('SANDBOX_OK')"],
        timeout_ms=5000,
    )
    assert res.outcome == SandboxOutcomeKind.COMPLETED
    assert res.exit_code == 0
    assert "SANDBOX_OK" in res.stdout
    assert res.is_success is True


@pytest.mark.skipif(os.name != "nt", reason="POSIX isolation is unavailable")
def test_sandbox_timeout(sandbox: LocalProcessSandbox) -> None:
    res = sandbox.execute(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        timeout_ms=1000,
    )
    assert res.outcome == SandboxOutcomeKind.TIMED_OUT
    assert res.is_success is False


@pytest.mark.skipif(os.name != "nt", reason="POSIX isolation is unavailable")
def test_sandbox_output_limit_exceeded(sandbox: LocalProcessSandbox) -> None:
    res = sandbox.execute(
        [sys.executable, "-c", "print('X' * 200_000)"],
        max_output_bytes=10_000,
        timeout_ms=5000,
    )
    assert res.outcome == SandboxOutcomeKind.OUTPUT_LIMIT_EXCEEDED
    assert res.is_success is False


@pytest.mark.skipif(os.name != "nt", reason="POSIX isolation is unavailable")
def test_sandbox_memory_limit_exceeded(sandbox: LocalProcessSandbox) -> None:
    res = sandbox.execute(
        [sys.executable, "-c", "x = [0] * (10**11)"],
        memory_limit_bytes=67_108_864,
        timeout_ms=5000,
    )
    assert res.outcome == SandboxOutcomeKind.MEMORY_LIMIT_EXCEEDED
    assert res.is_success is False


@pytest.mark.skipif(os.name != "nt", reason="POSIX isolation is unavailable")
def test_sandbox_nonzero_exit_code(sandbox: LocalProcessSandbox) -> None:
    res = sandbox.execute(
        [sys.executable, "-c", "import sys; sys.exit(42)"],
        timeout_ms=5000,
    )
    assert res.outcome == SandboxOutcomeKind.COMPLETED
    assert res.exit_code == 42
    assert res.is_success is False


def test_sandbox_empty_command_refused(sandbox: LocalProcessSandbox) -> None:
    res = sandbox.execute([])
    assert res.outcome == SandboxOutcomeKind.LAUNCH_REFUSED
    assert res.is_success is False


def test_missing_native_host_never_executes_command(tmp_path: Path) -> None:
    marker = tmp_path / "must_not_exist"
    result = LocalProcessSandbox(tmp_path / "missing_native").execute(
        [sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"]
    )
    assert result.outcome == SandboxOutcomeKind.ISOLATION_UNAVAILABLE
    assert not marker.exists()


@pytest.mark.parametrize("native_failure", ["nonzero", "malformed", "timeout", "spawn"])
def test_native_transport_failure_never_retries_submitted_command(
    monkeypatch, tmp_path, native_failure
):
    binary = tmp_path / "core-sandbox-run"
    binary.touch()
    calls = []

    def failed_run(command, **kwargs):
        calls.append(command)
        assert kwargs["check"] is False
        if native_failure == "timeout":
            raise subprocess.TimeoutExpired(command, 1)
        if native_failure == "spawn":
            raise OSError("unavailable")
        if native_failure == "nonzero":
            return subprocess.CompletedProcess(command, 7, b"", b"failure")
        return subprocess.CompletedProcess(command, 0, b"malformed", b"")

    monkeypatch.setattr(subprocess, "run", failed_run)
    result = LocalProcessSandbox(binary).execute(["submitted_untrusted_command"])
    assert result.outcome == SandboxOutcomeKind.ISOLATION_UNAVAILABLE
    assert calls == [[str(binary)]]


@pytest.mark.parametrize("outcome", list(SandboxOutcomeKind))
def test_native_outcome_and_resource_contract_are_preserved(monkeypatch, outcome):
    captured = []
    detail = {
        "exit_code": 42,
        "stdout": "out",
        "stderr": "err",
        "duration_ms": 3,
        "peak_memory_bytes": 100,
    }
    data = {"outcome": outcome.value}
    if outcome == SandboxOutcomeKind.COMPLETED:
        data["detail"] = detail
    elif outcome in {SandboxOutcomeKind.ISOLATION_UNAVAILABLE, SandboxOutcomeKind.LAUNCH_REFUSED}:
        data["detail"] = "native refusal"

    def execute(_host, config):
        captured.append(config)
        return Ok(data)

    monkeypatch.setattr(RustSandboxHost, "execute", execute)
    result = LocalProcessSandbox().execute(
        ["tool", "arg"], timeout_ms=77, memory_limit_bytes=99, max_output_bytes=88
    )
    assert result.outcome == outcome
    assert captured[0]["timeout_ms"] == 77
    assert captured[0]["memory_limit_bytes"] == 99
    assert captured[0]["max_output_bytes"] == 88
    assert result.authority_effect == "None"
    if outcome == SandboxOutcomeKind.COMPLETED:
        assert result.exit_code == 42
        assert result.stdout == "out"
        assert result.is_success is False


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"outcome": "invented"},
        {"outcome": "Completed", "detail": {}},
        {"outcome": "TimedOut", "detail": "unexpected"},
        {
            "outcome": "Completed",
            "detail": {
                "exit_code": True,
                "stdout": "",
                "stderr": "",
                "duration_ms": 1,
                "peak_memory_bytes": 1,
            },
        },
    ],
)
def test_invalid_native_receipt_refuses(monkeypatch, data):
    monkeypatch.setattr(RustSandboxHost, "execute", lambda _host, config: Ok(data))
    result = LocalProcessSandbox().execute(["tool"])
    assert result.outcome == SandboxOutcomeKind.ISOLATION_UNAVAILABLE
    assert result.detail == "SANDBOX_OUTCOME_INVALID"


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_invalid_resource_limit_never_dispatches(monkeypatch, limit):
    def forbidden(*args, **kwargs):
        pytest.fail("invalid limit dispatched")

    monkeypatch.setattr(RustSandboxHost, "execute", forbidden)
    assert (
        LocalProcessSandbox().execute(["tool"], memory_limit_bytes=limit).outcome
        == SandboxOutcomeKind.LAUNCH_REFUSED
    )


def test_typed_native_refusal_code_preserved(monkeypatch):
    monkeypatch.setattr(
        RustSandboxHost,
        "execute",
        lambda _host, config: Err(Refusal(code="HOST_TIMEOUT", message="timeout")),
    )
    result = LocalProcessSandbox().execute(["tool"])
    assert result.outcome == SandboxOutcomeKind.ISOLATION_UNAVAILABLE
    assert result.detail == "HOST_TIMEOUT"
