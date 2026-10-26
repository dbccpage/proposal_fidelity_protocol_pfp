"""Thin native sandbox adapter. Unavailable isolation is a typed refusal.

AuthorityEffect: None. Resource enforcement belongs to omega_sandbox; Python
never launches the submitted command or substitutes an unrestricted process.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from omega_engine_operations.domain.rop.result import Err
from omega_engine_operating_system.adapters.rust_host.ffi import RustSandboxHost
from omega_engine_pfp.domain.ports.process_sandbox import (
    ProcessSandboxPort,
    SandboxExecutionResult,
    SandboxOutcomeKind,
)


class LocalProcessSandbox(ProcessSandboxPort):
    """Pass configuration to the canonical native process seam."""

    def __init__(self, binary_path: Path | None = None, *, process_observer=None) -> None:
        self._binary_path = binary_path
        self._process_observer = process_observer

    def execute(
        self,
        command: Sequence[str],
        *,
        cwd: str | None = None,
        timeout_ms: int = 5000,
        memory_limit_bytes: int = 268_435_456,
        max_output_bytes: int = 1_048_576,
        env: Mapping[str, str] | None = None,
    ) -> SandboxExecutionResult:
        return self._execute(command, cwd=cwd, timeout_ms=timeout_ms,
            memory_limit_bytes=memory_limit_bytes, max_output_bytes=max_output_bytes, env=env)

    def execute_observed(
        self,
        command: Sequence[str],
        *,
        cwd: str | None = None,
        timeout_ms: int = 5000,
        memory_limit_bytes: int = 268_435_456,
        max_output_bytes: int = 1_048_576,
        env: Mapping[str, str] | None = None,
    ) -> SandboxExecutionResult:
        return self._execute(command, cwd=cwd, timeout_ms=timeout_ms,
            memory_limit_bytes=memory_limit_bytes, max_output_bytes=max_output_bytes, env=env,
            observe_resources=True)

    def _execute(
        self,
        command: Sequence[str],
        *,
        cwd: str | None = None,
        timeout_ms: int = 5000,
        memory_limit_bytes: int = 268_435_456,
        max_output_bytes: int = 1_048_576,
        env: Mapping[str, str] | None = None,
        observe_resources: bool = False,
    ) -> SandboxExecutionResult:
        if not command or any(type(part) is not str or not part for part in command):
            return SandboxExecutionResult(
                outcome=SandboxOutcomeKind.LAUNCH_REFUSED,
                detail="Command must contain nonempty string arguments",
            )
        limits = (timeout_ms, memory_limit_bytes, max_output_bytes)
        if any(type(limit) is not int or limit <= 0 for limit in limits):
            return SandboxExecutionResult(
                outcome=SandboxOutcomeKind.LAUNCH_REFUSED,
                detail="Resource limits must be positive integers",
            )
        host = RustSandboxHost(
            binary=self._binary_path,
            timeout_seconds=max(10.0, timeout_ms / 1000.0 + 5.0),
            **({"process_observer": self._process_observer} if self._process_observer else {}),
        )
        config = {
                "command": list(command),
                "cwd": cwd,
                "timeout_ms": timeout_ms,
                "memory_limit_bytes": memory_limit_bytes,
                "max_output_bytes": max_output_bytes,
                "env": dict(env or {}),
            }
        result = host.execute(config, observe_resources=True) if observe_resources else host.execute(config)
        if isinstance(result, Err):
            return SandboxExecutionResult(
                outcome=SandboxOutcomeKind.ISOLATION_UNAVAILABLE,
                detail=result.error.code,
            )
        try:
            data = result.value
            observation = None
            if observe_resources:
                if (set(data) != {"schema_version", "outcome", "observation"}
                        or data["schema_version"] != "omega.sandbox.resource-observation.v1"):
                    raise ValueError("Resource profile unavailable")
                observation = _resource_observation(data["observation"], max_output_bytes)
                data = data["outcome"]
            outcome = SandboxOutcomeKind(data["outcome"])
            expected = (
                {"outcome", "detail"}
                if outcome
                in {
                    SandboxOutcomeKind.COMPLETED,
                    SandboxOutcomeKind.LAUNCH_REFUSED,
                    SandboxOutcomeKind.ISOLATION_UNAVAILABLE,
                }
                else {"outcome"}
            )
            if set(data) != expected:
                raise ValueError("Unexpected sandbox outcome fields")
            if outcome != SandboxOutcomeKind.COMPLETED:
                detail = data.get("detail")
                if detail is not None and type(detail) is not str:
                    raise ValueError("Refusal detail must be a string")
                return SandboxExecutionResult(outcome=outcome, detail=detail, resource_observation=observation)
            detail = data["detail"]
            fields = {"exit_code", "stdout", "stderr", "duration_ms", "peak_memory_bytes"}
            if type(detail) is not dict or set(detail) != fields:
                raise ValueError("Invalid completed sandbox outcome")
            for field in ("exit_code", "duration_ms", "peak_memory_bytes"):
                if type(detail[field]) is not int:
                    raise ValueError("Sandbox numeric fields must be integers")
            if detail["duration_ms"] < 0 or detail["peak_memory_bytes"] < 0:
                raise ValueError("Sandbox measurements cannot be negative")
            for field in ("stdout", "stderr"):
                if type(detail[field]) is not str:
                    raise ValueError("Sandbox output must be text")
                if observation is not None:
                    raw = observation[field + "_hex"]
                    if raw is None or bytes.fromhex(raw).decode("utf-8", errors="replace") != detail[field]:
                        raise ValueError("Resource raw output differs from completed text")
                if observation is None and len(detail[field].encode("utf-8")) > max_output_bytes:
                    return SandboxExecutionResult(outcome=SandboxOutcomeKind.OUTPUT_LIMIT_EXCEEDED)
            if observation is not None and observation["memory_bytes"] is not None:
                if observation["memory_bytes"] != detail["peak_memory_bytes"]:
                    raise ValueError("Resource memory readbacks differ")
            return SandboxExecutionResult(outcome=outcome, **detail, resource_observation=observation)
        except (KeyError, TypeError, ValueError, UnicodeError):
            return SandboxExecutionResult(
                outcome=SandboxOutcomeKind.ISOLATION_UNAVAILABLE,
                detail="SANDBOX_OUTCOME_INVALID",
            )


def _resource_observation(data, max_output_bytes):
    fields = {"task_pid", "elapsed_ms", "memory_metric", "memory_bytes", "measurement_error",
              "isolation_applied", "stdout_hex", "stderr_hex"}
    if type(data) is not dict or set(data) != fields:
        raise ValueError("Invalid resource observation")
    if (type(data["elapsed_ms"]) is not int or data["elapsed_ms"] < 0
            or type(data["isolation_applied"]) is not bool
            or data["memory_metric"] != "windows_job_peak_committed_bytes"):
        raise ValueError("Invalid resource measurement")
    for name, minimum in (("task_pid", 1), ("memory_bytes", 0)):
        if data[name] is not None and (type(data[name]) is not int or data[name] < minimum):
            raise ValueError("Invalid resource integer")
    if data["measurement_error"] is not None and type(data["measurement_error"]) is not str:
        raise ValueError("Invalid measurement error")
    if (data["memory_bytes"] is None) != (data["measurement_error"] is not None):
        raise ValueError("Unavailable memory must remain explicit")
    for name in ("stdout_hex", "stderr_hex"):
        value = data[name]
        if value is not None:
            if type(value) is not str or bytes.fromhex(value).hex() != value or len(value) > 2 * max_output_bytes:
                raise ValueError("Invalid raw output")
    return dict(data)


__all__ = ["LocalProcessSandbox"]
