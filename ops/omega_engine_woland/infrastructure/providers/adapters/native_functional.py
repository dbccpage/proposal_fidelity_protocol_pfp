"""Transport graph inputs to the pinned canonical Rust functional calculator.

The SHA-256 pin is supplied by the caller's trusted build process. It binds the
executed bytes, not a source-to-binary provenance proof. No Python fallback is
permitted for missing, refused, or malformed native results.

Three typed outcomes other than a result:

* ``NativeFunctionalInputRefused`` -- the request is refused before the native
  call (for example a claim on an edge the carrier does not declare);
* ``NativeFunctionalRefusal`` -- the native evaluator ran and refused; its
  reason, exit status and output are kept;
* ``NativeFunctionalUnavailable`` -- no pinned executable could be run, or its
  reply was malformed.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Mapping, Sequence

FUNCTIONAL_OWNER = "omega_engine/crates_rs/omega_functional/src"


class NativeFunctionalUnavailable(RuntimeError):
    code = "FUNCTIONAL_BOUNDARY_UNAVAILABLE"

    def __init__(self, reason: str) -> None:
        super().__init__(f"{self.code}: {reason}; calculator: {FUNCTIONAL_OWNER}")


class NativeFunctionalInputRefused(ValueError):
    """The request is refused before any native call."""

    code = "FUNCTIONAL_INPUT_REFUSED"

    def __init__(self, reason: str) -> None:
        super().__init__(f"{self.code}: {reason}")
        self.reason = reason


class NativeFunctionalRefusal(RuntimeError):
    """The native evaluator ran and refused; its own reason is kept."""

    code = "NATIVE_FUNCTIONAL_REFUSAL"
    _MAX_DETAIL = 4096

    def __init__(self, reason: str, *, returncode: int, stdout: str, stderr: str) -> None:
        super().__init__(f"{self.code}: {reason}; calculator: {FUNCTIONAL_OWNER}")
        self.reason = reason
        self.returncode = returncode
        self.stdout = stdout[: self._MAX_DETAIL]
        self.stderr = stderr[: self._MAX_DETAIL]


def _exact(value: int | Fraction) -> str:
    if type(value) not in (int, Fraction):
        raise TypeError("functional inputs require exact int or Fraction, not float or bool")
    return str(value)


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate result key")
        result[key] = value
    return result


def _rational(value: object) -> Fraction:
    if not isinstance(value, str) or re.fullmatch(r"-?\d+(?:/[1-9]\d*)?", value) is None:
        raise ValueError("native rational result must be an integer or fraction string")
    return Fraction(value)


def compute_graph_phi1(
    vertices: Sequence[str],
    edges: Sequence[tuple[str, str, int | Fraction]],
    claims: Mapping[tuple[str, str], int | Fraction],
) -> tuple[Fraction, dict[str, Fraction]]:
    """Return the native exact graph quotient minimum and minimizing gauge.

    Unasserted edges receive the declared zero claim: this is the L1 game's
    stated convention (an edge a proposer does not assert carries claim zero),
    which the paper governors rely on. Unknown claim edges and duplicate edges
    are refused instead of being silently discarded.
    """
    names = list(vertices)
    if any(type(name) is not str for name in names) or len(set(names)) != len(names):
        raise ValueError("graph vertices must be distinct strings")
    known = set(names)
    edge_keys = set()
    request_edges = []
    for u, v, weight in edges:
        if u == v or u not in known or v not in known:
            raise ValueError("graph edges must join distinct declared vertices")
        if (u, v) in edge_keys:
            raise ValueError("duplicate directed edge")
        edge_keys.add((u, v))
        encoded_weight = _exact(weight)
        if weight <= 0:
            raise ValueError("edge weight must be positive")
        request_edges.append({
            "u": u, "v": v, "weight": encoded_weight,
            "claim": _exact(claims.get((u, v), 0)),
        })
    if set(claims) - edge_keys:
        raise NativeFunctionalInputRefused("claim edge absent from declared carrier")
    binary = os.environ.get("OMEGA_FUNCTIONAL_GRAPH_BIN")
    expected = os.environ.get("OMEGA_FUNCTIONAL_GRAPH_SHA256", "").lower()
    if not binary or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        raise NativeFunctionalUnavailable("pinned native graph executable required")
    try:
        executable = Path(binary).resolve(strict=True)
        digest = hashlib.sha256(executable.read_bytes()).hexdigest()
        if digest != expected:
            raise NativeFunctionalUnavailable("native graph executable digest mismatch")
        completed = subprocess.run(
            [str(executable)],
            input=json.dumps({"vertices": names, "edges": request_edges}),
            text=True, capture_output=True, check=False, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise NativeFunctionalUnavailable("native graph executable could not run") from error
    refusal = _native_refusal(completed)
    if refusal is not None:
        raise refusal
    try:
        response = json.loads(completed.stdout, object_pairs_hook=_unique_object)
        if type(response) is not dict or set(response) != {"status", "result"} or response["status"] != "PASS":
            raise ValueError("native PASS envelope required")
        result = response["result"]
        if type(result) is not dict or set(result) != {"phi1", "gauge", "forests_checked"}:
            raise ValueError("invalid native graph result fields")
        if type(result["gauge"]) is not dict or set(result["gauge"]) != known:
            raise ValueError("native gauge carrier mismatch")
        count = result["forests_checked"]
        if type(count) is not int or count < 1:
            raise ValueError("native exhaustive search count required")
        value = _rational(result["phi1"])
        gauge = {name: _rational(number) for name, number in result["gauge"].items()}
        if value < 0:
            raise ValueError("negative native quotient minimum")
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise NativeFunctionalUnavailable("malformed native graph result") from error
    return value, gauge


def _native_refusal(completed: subprocess.CompletedProcess) -> NativeFunctionalRefusal | None:
    """A refusal when the evaluator exited non-zero or answered ``REFUSE``.

    The evaluator prints ``{"status": "REFUSE", "reason": ...}`` and exits 2.
    Its reason is kept; output that is not that envelope is kept verbatim.
    """
    stdout = getattr(completed, "stdout", None)
    stderr = getattr(completed, "stderr", None)
    stdout = stdout if isinstance(stdout, str) else ""
    stderr = stderr if isinstance(stderr, str) else ""
    try:
        envelope = json.loads(stdout, object_pairs_hook=_unique_object)
    except (TypeError, ValueError):
        envelope = None
    declared_refusal = (
        type(envelope) is dict
        and envelope.get("status") == "REFUSE"
        and type(envelope.get("reason")) is str
    )
    if completed.returncode == 0 and not declared_refusal:
        return None
    if declared_refusal:
        reason = envelope["reason"]
    else:
        reason = f"exit status {completed.returncode} without a REFUSE envelope"
    return NativeFunctionalRefusal(
        reason, returncode=completed.returncode, stdout=stdout, stderr=stderr
    )
