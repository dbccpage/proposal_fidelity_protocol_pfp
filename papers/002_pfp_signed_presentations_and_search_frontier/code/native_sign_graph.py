"""Transport sign graph inputs to the self-contained Rust solve_sign_graph binary.

Provides an exact interface to the native Rust binary solve_sign_graph.
Uses the exact Python classifier only when no native binary exists; a found
binary decides, and its refusals propagate as NativeSignGraphRefused.
"""

from __future__ import annotations

import json
import os
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Optional, Sequence, Union

if __package__:
    from .genesis_alpha.sign_graph import (
        GaugeWitness,
        OddCycleWitness,
        SignedRewrite,
        SignResult,
    )
    from .genesis_alpha.sign_graph import (
        classify_sign_graph as py_classify_sign_graph,
    )
    from .genesis_alpha.sign_graph import (
        matrix_sign_graph as py_matrix_sign_graph,
    )
    from .genesis_alpha.sign_graph import (
        verify_gauge as py_verify_gauge,
    )
    from .genesis_alpha.sign_graph import (
        verify_odd_cycle as py_verify_odd_cycle,
    )
else:
    from genesis_alpha.sign_graph import (
        GaugeWitness,
        OddCycleWitness,
        SignedRewrite,
        SignResult,
    )
    from genesis_alpha.sign_graph import (
        classify_sign_graph as py_classify_sign_graph,
    )
    from genesis_alpha.sign_graph import (
        matrix_sign_graph as py_matrix_sign_graph,
    )
    from genesis_alpha.sign_graph import (
        verify_gauge as py_verify_gauge,
    )
    from genesis_alpha.sign_graph import (
        verify_odd_cycle as py_verify_odd_cycle,
    )

PAPER_DIR = Path(__file__).resolve().parent.parent
RUST_DIR = PAPER_DIR / "code" / "rust"


class NativeSignGraphUnavailable(RuntimeError):
    """The native binary is required but absent, could not run, or answered malformed output."""

    code = "NATIVE_SIGN_GRAPH_UNAVAILABLE"


class NativeSignGraphRefused(RuntimeError):
    """The native binary ran and refused the request; its refusal is never replaced."""

    code = "NATIVE_SIGN_GRAPH_REFUSED"


def find_binary() -> Optional[Path]:
    """Return an explicitly configured or package-local compiled executable.

    CORE_SIGN_GRAPH_BIN may name the executable; otherwise only this crate's
    own target/release and target/debug directories are searched.
    """
    env_bin = os.environ.get("CORE_SIGN_GRAPH_BIN")
    if env_bin and Path(env_bin).is_file():
        return Path(env_bin)

    candidates = [
        RUST_DIR / "target" / "release" / "solve_sign_graph.exe",
        RUST_DIR / "target" / "release" / "solve_sign_graph",
        RUST_DIR / "target" / "debug" / "solve_sign_graph.exe",
        RUST_DIR / "target" / "debug" / "solve_sign_graph",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def _run_native(binary: Path, request: dict, timeout: int) -> dict:
    """Run one native request and return its PASS payload; raise a typed error otherwise."""
    try:
        completed = subprocess.run(
            [str(binary)],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise NativeSignGraphUnavailable(f"native solve_sign_graph could not run: {error}") from error
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        if completed.returncode != 0:
            raise NativeSignGraphRefused(
                f"native solve_sign_graph exited {completed.returncode}: {completed.stderr.strip()[:200]}"
            ) from error
        raise NativeSignGraphUnavailable("native solve_sign_graph returned malformed output") from error
    if completed.returncode != 0 or not isinstance(payload, dict) or payload.get("status") != "PASS":
        detail = payload.get("error") if isinstance(payload, dict) else None
        raise NativeSignGraphRefused(
            f"native solve_sign_graph refused (exit {completed.returncode}): {detail or completed.stderr.strip()[:200]}"
        )
    return payload


def _edges(edges: Sequence[SignedRewrite]) -> list:
    return [{"source": e.source, "target": e.target, "odd": e.odd} for e in edges]


def classify_sign_graph(
    vertices: Sequence[str],
    edges: Sequence[SignedRewrite],
    require_native: bool = False,
) -> SignResult:
    """Return an exact gauge or odd cycle witness.

    A found native binary decides, and its refusals propagate. The exact Python
    classifier is used only when no binary exists and native is not required.
    """
    binary = find_binary()
    if binary is None:
        if require_native:
            raise NativeSignGraphUnavailable("solve_sign_graph binary not found")
        return py_classify_sign_graph(vertices, edges)
    payload = _run_native(binary, {"mode": "classify", "vertices": list(vertices), "edges": _edges(edges)}, 30)
    witness_data = payload.get("witness")
    if not isinstance(witness_data, dict):
        raise NativeSignGraphUnavailable("native solve_sign_graph returned a malformed witness")
    if payload.get("result_type") == "gauge":
        names, bits = witness_data.get("vertices"), witness_data.get("bits")
        if (not isinstance(names, list) or not isinstance(bits, list)
                or len(names) != len(bits)
                or any(not isinstance(name, str) for name in names)
                or len(set(names)) != len(names)
                or any(type(bit) is not int or bit not in (0, 1) for bit in bits)):
            raise NativeSignGraphUnavailable("native solve_sign_graph returned a malformed gauge")
        return GaugeWitness(
            vertices=tuple(names),
            bits=tuple(bits),
        )
    if payload.get("result_type") == "odd_cycle":
        raw_steps = witness_data.get("steps")
        if (not isinstance(raw_steps, list) or not raw_steps
                or any(not isinstance(step, list) or len(step) != 3
                       or type(step[0]) is not int or step[0] < 0
                       or not isinstance(step[1], str) or not isinstance(step[2], str)
                       for step in raw_steps)):
            raise NativeSignGraphUnavailable("native solve_sign_graph returned malformed walk steps")
        return OddCycleWitness(steps=tuple((s[0], s[1], s[2]) for s in raw_steps))
    raise NativeSignGraphUnavailable("native solve_sign_graph returned an unknown result type")


def _native_validity(payload: dict) -> bool:
    valid = payload.get("valid")
    if type(valid) is not bool:
        raise NativeSignGraphUnavailable("native solve_sign_graph returned no Boolean verdict")
    return valid


def verify_gauge(
    vertices: Sequence[str],
    edges: Sequence[SignedRewrite],
    witness: GaugeWitness,
    require_native: bool = False,
) -> bool:
    """Verify gauge equation alpha(u) XOR alpha(v) = odd for all edges."""
    binary = find_binary()
    if binary is None:
        if require_native:
            raise NativeSignGraphUnavailable("solve_sign_graph binary not found")
        return py_verify_gauge(vertices, edges, witness)
    request = {
        "mode": "verify_gauge",
        "vertices": list(vertices),
        "edges": _edges(edges),
        "witness_gauge": {"vertices": list(witness.vertices), "bits": list(witness.bits)},
    }
    return _native_validity(_run_native(binary, request, 10))


def verify_odd_cycle(
    vertices: Sequence[str],
    edges: Sequence[SignedRewrite],
    witness: OddCycleWitness,
    require_native: bool = False,
) -> bool:
    """Verify odd cycle witness independently."""
    binary = find_binary()
    if binary is None:
        if require_native:
            raise NativeSignGraphUnavailable("solve_sign_graph binary not found")
        return py_verify_odd_cycle(vertices, edges, witness)
    request = {
        "mode": "verify_odd_cycle",
        "vertices": list(vertices),
        "edges": _edges(edges),
        "witness_odd_cycle": {"steps": [list(s) for s in witness.steps]},
    }
    return _native_validity(_run_native(binary, request, 10))


def classify_matrix_sign_gauge(
    matrix: Sequence[Sequence[Union[int, Fraction]]],
    require_native: bool = False,
) -> SignResult:
    """Adapt matrix to signed graph and classify."""
    vertices, edges = py_matrix_sign_graph(matrix)
    return classify_sign_graph(vertices, edges, require_native=require_native)
