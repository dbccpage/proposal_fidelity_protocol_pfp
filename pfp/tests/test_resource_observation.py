"""Opt-in resource wire preserves measurements without relabelling commit as RSS."""
from operations.domain.rop.result import Ok
from operating_system.adapters.rust_host.ffi import RustSandboxHost
from pfp.infrastructure.sandbox.local_process_sandbox import LocalProcessSandbox


def wire():
    return {"schema_version": "core.sandbox.resource-observation.v1",
        "outcome": {"outcome": "Completed", "detail": {"exit_code": 0, "stdout": "ok",
            "stderr": "", "duration_ms": 7, "peak_memory_bytes": 4096}},
        "observation": {"task_pid": 123, "elapsed_ms": 7,
            "memory_metric": "windows_job_peak_committed_bytes", "memory_bytes": 4096,
            "measurement_error": None, "isolation_applied": True,
            "stdout_hex": "6f6b", "stderr_hex": ""}}


def test_opt_in_resource_wire_retains_actual_pid_metric_and_raw_bytes(monkeypatch):
    calls = []
    def execute(host, config, *, observe_resources=False):
        calls.append((config, observe_resources))
        return Ok(wire())
    monkeypatch.setattr(RustSandboxHost, "execute", execute)
    result = LocalProcessSandbox().execute_observed(["checker"], timeout_ms=50)
    assert len(calls) == 1 and calls[0][1] is True
    assert result.outcome.value == "Completed"
    assert result.resource_observation["task_pid"] == 123
    assert result.resource_observation["memory_metric"] == "windows_job_peak_committed_bytes"
    assert result.resource_observation["stdout_hex"] == "6f6b"
    assert "resident_memory_bytes" not in result.resource_observation


def test_missing_measurement_stays_unavailable_and_legacy_profile_cannot_fallback(monkeypatch):
    from pfp.domain.ports.process_sandbox import SandboxOutcomeKind
    raw = wire()
    raw["observation"]["memory_bytes"] = None
    raw["observation"]["measurement_error"] = "JOB_MEMORY_QUERY_FAILED"
    monkeypatch.setattr(RustSandboxHost, "execute", lambda *a, **k: Ok(raw))
    result = LocalProcessSandbox().execute_observed(["checker"])
    assert result.resource_observation["memory_bytes"] is None
    monkeypatch.setattr(RustSandboxHost, "execute", lambda *a, **k: Ok(wire()["outcome"]))
    result = LocalProcessSandbox().execute_observed(["checker"])
    assert result.outcome == SandboxOutcomeKind.ISOLATION_UNAVAILABLE


def test_exact_output_bytes_are_not_counted_as_lossy_utf8(monkeypatch):
    raw = wire()
    raw["observation"]["stdout_hex"] = "ff"
    raw["outcome"]["detail"]["stdout"] = "\ufffd"
    monkeypatch.setattr(RustSandboxHost, "execute", lambda *a, **k: Ok(raw))
    result = LocalProcessSandbox().execute_observed(["checker"], max_output_bytes=1)
    assert result.is_success
    assert result.resource_observation["stdout_hex"] == "ff"
