"""Opt-in single sandbox execution and unsigned, task-bound resource readback."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

from ..domain.native_gate_check import ResourceCheckConfig, decode_native_json

RESOURCE_PROFILE = "adversary.host-job-resources.v1"
HARDWARE_CONSTRAINT = "PFP-22-HARDWARE-CONSTRAINT"


def _binary(config):
    from .teamwork_native_gates import _safe_native_path

    path = _safe_native_path(config.sandbox_binary_path)
    if (not path.is_file() or path.stat().st_nlink != 1
            or hashlib.sha256(path.read_bytes()).hexdigest() != config.sandbox_binary_sha256):
        raise ValueError("RESOURCE_SANDBOX_BINARY_CHANGED")
    return path


def bind_resource_check_config(path):
    from .teamwork_native_gates import _safe_native_path

    config = ResourceCheckConfig.model_validate(decode_native_json(Path(path).read_bytes()))
    config = config.model_copy(update={"sandbox_binary_path": str(_safe_native_path(config.sandbox_binary_path))})
    _binary(config)
    return config


def _context(action):
    return {"run_id": action.run_id, "task_id": action.initial_task_id,
        "source_digest": action.check_source_id, "checker_id": action.checker_id,
        "candidate_sha256": hashlib.sha256(action.candidate.encode()).hexdigest(),
        "requested_argv": list(action.check_command), "artifacts": dict(action.artifacts),
        "configuration": action.native_gate_check.resource_check.model_dump(mode="json")}


def execute_resource_check(action, command, *, timeout):
    """Execute once. Partial/refused observations never reuse an earlier success."""
    from pfp.infrastructure.sandbox.local_process_sandbox import LocalProcessSandbox

    config = action.native_gate_check.resource_check
    capture = {"context": _context(action), "action_id": action.action_id, "native_process": None,
               "native_result": None, "failure_code": None}
    observed = []
    def record(process):
        observed.append({"args": list(process["args"]), "exit_code": process["exit_code"],
            **{name.removesuffix("_bytes") + "_hex": process[name].hex()
               for name in ("stdin_bytes", "stdout_bytes", "stderr_bytes")}})
    try:
        if config.timeout_ms > timeout * 1000:
            raise ValueError("RESOURCE_TIMEOUT_EXCEEDS_HOST_ALLOWANCE")
        binary = _binary(config)
        executable = shutil.which(command[0])
        if executable is None:
            raise ValueError("RESOURCE_CHECKER_EXECUTABLE_UNAVAILABLE")
        executable = Path(executable).resolve()
        command = [str(executable), *command[1:]]
        capture["executed_argv"] = command
        capture["executable_sha256"] = hashlib.sha256(executable.read_bytes()).hexdigest()
        result = LocalProcessSandbox(binary, process_observer=record).execute_observed(command,
            timeout_ms=config.timeout_ms, memory_limit_bytes=config.memory_limit_bytes,
            max_output_bytes=config.max_output_bytes)
        if observed:
            capture["native_process"] = observed[-1]
            capture["native_result"] = decode_native_json(bytes.fromhex(observed[-1]["stdout_hex"]))
        _binary(config)
        if hashlib.sha256(executable.read_bytes()).hexdigest() != capture["executable_sha256"]:
            raise ValueError("RESOURCE_CHECKER_EXECUTABLE_CHANGED")
        if result.outcome.value != "Completed" or result.resource_observation is None:
            capture["failure_code"] = "RESOURCE_CHECK_" + result.outcome.value.upper()
            return None, capture
        observation = result.resource_observation
        if observation["stdout_hex"] is None or observation["stderr_hex"] is None:
            raise ValueError("RESOURCE_OUTPUT_UNAVAILABLE")
        _validate_capture(capture)
        return subprocess.CompletedProcess(command, result.exit_code,
            bytes.fromhex(observation["stdout_hex"]), bytes.fromhex(observation["stderr_hex"])), capture
    except (ValueError, OSError, TypeError, KeyError, UnicodeError) as exc:
        if observed:
            capture["native_process"] = observed[-1]
        capture["failure_code"] = str(exc).split(":", 1)[0] or type(exc).__name__
        return None, capture


def _validate_capture(capture):
    """Compare saved exact transport bytes without executing or signing anything."""
    process = capture["native_process"]
    config = capture["context"]["configuration"]
    if not process or process["exit_code"] != 0:
        raise ValueError("RESOURCE_NATIVE_CAPTURE_UNAVAILABLE")
    if process["args"] != [config["sandbox_binary_path"], "--observe-resources"]:
        raise ValueError("RESOURCE_NATIVE_ARGV_CHANGED")
    request = decode_native_json(bytes.fromhex(process["stdin_hex"]))
    if (request["command"] != capture["executed_argv"]
            or request["command"][1:] != capture["context"]["requested_argv"][1:]
            or request["timeout_ms"] != config["timeout_ms"]
            or request["memory_limit_bytes"] != config["memory_limit_bytes"]
            or request["max_output_bytes"] != config["max_output_bytes"]
            or request["cwd"] is not None or request["env"] != {}):
        raise ValueError("RESOURCE_NATIVE_REQUEST_CHANGED")
    if decode_native_json(bytes.fromhex(process["stdout_hex"])) != capture["native_result"]:
        raise ValueError("RESOURCE_NATIVE_RESULT_CHANGED")


def resource_gate_payload(action, *, replay=False):
    config = action.native_gate_check.resource_check
    expected = _context(action)
    if not replay:
        _binary(config)
    latest = next((item for item in reversed(action.native_host_observations)
                   if "resource_capture" in item), None)
    capture = latest.get("resource_capture") if latest else None
    payload = {"resource_profile": RESOURCE_PROFILE, "resource_expected": expected,
               "resource_observation": None}
    if capture is None:
        return payload
    if capture["context"] != expected or capture["action_id"] != latest["action_id"]:
        return payload
    if capture.get("failure_code") is None or capture.get("native_result") is not None:
        _validate_capture(capture)
    result = capture.get("native_result") or {}
    measurements = result.get("observation")
    payload["resource_observation"] = {
        "context": capture["context"], "action_id": capture["action_id"],
        "failure_code": capture.get("failure_code"),
        "native_outcome": result.get("outcome", {}).get("outcome"),
        "measurements": ({key: value for key, value in measurements.items()
            if key not in {"stdout_hex", "stderr_hex"}} if measurements else None),
        "native_result_sha256": (hashlib.sha256(bytes.fromhex(capture["native_process"]["stdout_hex"])).hexdigest()
            if capture.get("native_process") else None)}
    return payload
