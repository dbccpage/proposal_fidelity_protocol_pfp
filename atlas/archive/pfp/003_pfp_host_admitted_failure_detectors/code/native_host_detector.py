"""Bridge to the Rust port (``rust/``) of the PFP Paper 003 package code.

The ``solve_host_detector`` binary is used only when it can be found:

1. the path named by the environment variable ``PFP003_HOST_DETECTOR_BIN``, or
2. a build inside this package, ``code/rust/target/{release,debug}/``.

``native_*`` functions call the binary and raise ``NativeHostUnavailable`` when
no binary is found, or ``NativeHostError`` when the binary fails or refuses. They
never fall back silently. ``evaluate_gate`` and ``scan_canaries`` choose the
backend explicitly (Rust if a binary is found, otherwise the Python reference)
and report which backend produced the result.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Sequence

from canaries import CanaryFinding, scan_for_canaries
from danger_gate import (
    Signal1Match,
    Signal2Danger,
    TwoSignalDecision,
    evaluate_two_signal_gate,
)

BINARY_ENV = "PFP003_HOST_DETECTOR_BIN"
_TIMEOUT_SECONDS = 10


class NativeHostUnavailable(RuntimeError):
    """No Rust binary was found."""


class NativeHostError(RuntimeError):
    """The Rust binary was found but failed, timed out, or refused the request."""


def native_binary_path() -> Path | None:
    explicit = os.environ.get(BINARY_ENV)
    if explicit:
        path = Path(explicit)
        return path if path.is_file() else None
    target = Path(__file__).resolve().parent / "rust" / "target"
    for profile in ("release", "debug"):
        for name in ("solve_host_detector.exe", "solve_host_detector"):
            candidate = target / profile / name
            if candidate.is_file():
                return candidate
    return None


def is_native_available() -> bool:
    return native_binary_path() is not None


def _call_native(payload: dict[str, Any]) -> Any:
    binary = native_binary_path()
    if binary is None:
        raise NativeHostUnavailable(
            f"no solve_host_detector binary; build code/rust or set {BINARY_ENV}"
        )
    try:
        proc = subprocess.run(
            [str(binary)],
            input=json.dumps(payload),
            capture_output=True,
            encoding="utf-8",
            timeout=_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise NativeHostError(f"native call failed: {error}") from error
    if proc.returncode != 0:
        raise NativeHostError(f"native binary exited {proc.returncode}: {proc.stderr.strip()}")
    try:
        response = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        raise NativeHostError("native binary returned non-JSON output") from error
    if not isinstance(response, dict) or response.get("success") is not True:
        detail = response.get("error") if isinstance(response, dict) else response
        raise NativeHostError(f"native binary refused the request: {detail}")
    return response.get("data")


def _signal_payload(
    signal1_matches: Sequence[Signal1Match] | Sequence[dict[str, Any]],
    signal2: Signal2Danger | dict[str, Any] | None,
) -> dict[str, Any]:
    s1_dicts = [m.to_dict() if isinstance(m, Signal1Match) else m for m in signal1_matches]
    if isinstance(signal2, Signal2Danger):
        s2_dict: dict[str, Any] | None = signal2.to_dict()
    elif isinstance(signal2, dict):
        s2_dict = signal2
    else:
        s2_dict = None
    return {"command": "evaluate_gate", "signal1_matches": s1_dicts, "signal2": s2_dict}


def native_evaluate_two_signal_gate(
    signal1_matches: Sequence[Signal1Match] | Sequence[dict[str, Any]],
    signal2: Signal2Danger | dict[str, Any] | None = None,
) -> TwoSignalDecision:
    data = _call_native(_signal_payload(signal1_matches, signal2))
    try:
        return TwoSignalDecision(
            decision=data["decision"],
            is_refusal=data["is_refusal"],
            disposition=data["disposition"],
            signal1_count=data["signal1_count"],
            signal2_severity=data.get("signal2_severity"),
            is_suppressed=data["is_suppressed"],
            rationale=data["rationale"],
        )
    except (KeyError, TypeError) as error:
        raise NativeHostError(f"malformed native gate response: {error}") from error


def native_scan_for_canaries(text: str) -> list[CanaryFinding]:
    data = _call_native({"command": "scan_canaries", "text": text})
    try:
        return [
            CanaryFinding(
                canary_id=f["canary_id"],
                name=f["name"],
                description=f["description"],
                pattern_matched=f["pattern_matched"],
                severity=f["severity"],
                confidence_num=f["confidence_num"],
                confidence_den=f["confidence_den"],
            )
            for f in data
        ]
    except (KeyError, TypeError) as error:
        raise NativeHostError(f"malformed native scan response: {error}") from error


def evaluate_gate(
    signal1_matches: Sequence[Signal1Match] | Sequence[dict[str, Any]],
    signal2: Signal2Danger | dict[str, Any] | None = None,
) -> tuple[TwoSignalDecision, str]:
    """Return (decision, backend); backend is "rust" or "python"."""
    if is_native_available():
        return native_evaluate_two_signal_gate(signal1_matches, signal2), "rust"
    return evaluate_two_signal_gate(signal1_matches, signal2), "python"


def scan_canaries(text: str) -> tuple[list[CanaryFinding], str]:
    """Return (findings, backend); backend is "rust" or "python"."""
    if is_native_available():
        return native_scan_for_canaries(text), "rust"
    return scan_for_canaries(text), "python"
