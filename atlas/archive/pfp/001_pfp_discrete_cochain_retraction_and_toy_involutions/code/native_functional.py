"""Transport graph inputs to the self-contained Rust graph_phi1 calculator.

Provides an exact rational interface to the native Rust binary solve_graph_phi1.
A native refusal, timeout, nonzero exit or malformed response is raised as a
typed error; it is never replaced by another solver's answer. Only when no
compiled binary exists, and the caller has not required the native path, does
the adapter use the paper-local Python certificate builder, with the same exact
weights and reports.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Mapping, Optional, Sequence, Tuple

PAPER_DIR = Path(__file__).resolve().parent.parent
RUST_DIR = PAPER_DIR / "code" / "rust"
NATIVE_TIMEOUT_SECONDS = 30
MAX_NATIVE_FORESTS = 100_000


class NativeFunctionalError(RuntimeError):
    """Base class for native boundary failures."""


class NativeFunctionalUnavailable(NativeFunctionalError):
    code = "FUNCTIONAL_BOUNDARY_UNAVAILABLE"


class NativeFunctionalRefusal(NativeFunctionalError):
    """The native solver refused the request (for example EnumerationLimit)."""

    code = "NATIVE_REFUSAL"


class NativeFunctionalTimeout(NativeFunctionalError):
    code = "NATIVE_TIMEOUT"


class NativeFunctionalProtocolError(NativeFunctionalError):
    """The executable exited or answered outside the declared JSON protocol."""

    code = "NATIVE_PROTOCOL_ERROR"


def _exact(value: int | Fraction) -> str:
    if type(value) not in (int, Fraction):
        raise TypeError("functional inputs require exact int or Fraction, not float or bool")
    return str(value)


def _find_binary() -> Optional[Path]:
    """Return an explicitly configured or package-local compiled executable."""
    env_bin = os.environ.get("CORE_FUNCTIONAL_GRAPH_BIN")
    if env_bin:
        configured = Path(env_bin)
        if not configured.is_file():
            raise NativeFunctionalUnavailable(f"CORE_FUNCTIONAL_GRAPH_BIN is not a file: {configured}")
        return configured

    candidates = [
        RUST_DIR / "target" / "release" / "solve_graph_phi1.exe",
        RUST_DIR / "target" / "release" / "solve_graph_phi1",
        RUST_DIR / "target" / "debug" / "solve_graph_phi1.exe",
        RUST_DIR / "target" / "debug" / "solve_graph_phi1",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _run_native(binary: Path, request: dict) -> Tuple[Fraction, dict[str, Fraction]]:
    try:
        completed = subprocess.run(
            [str(binary)],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            check=False,
            timeout=NATIVE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise NativeFunctionalTimeout(f"solve_graph_phi1 exceeded {NATIVE_TIMEOUT_SECONDS}s") from error
    except OSError as error:
        raise NativeFunctionalUnavailable(f"cannot execute {binary}: {error}") from error
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise NativeFunctionalProtocolError(
            f"non-JSON output (exit {completed.returncode}): {completed.stdout[:200]!r}"
        ) from error
    if not isinstance(payload, dict):
        raise NativeFunctionalProtocolError("native response must be a JSON object")
    if payload.get("status") == "REFUSE":
        if not isinstance(payload.get("reason"), str):
            raise NativeFunctionalProtocolError("native refusal requires a string reason")
        raise NativeFunctionalRefusal(payload["reason"])
    if completed.returncode != 0 or payload.get("status") != "PASS":
        raise NativeFunctionalProtocolError(f"unexpected native response (exit {completed.returncode}): {payload!r}")

    def exact_response(value):
        if type(value) is not str or re.fullmatch(r"[+-]?[0-9]+(?:/[+-]?[0-9]+)?", value) is None:
            raise ValueError("native rationals must be integer or fraction strings")
        return Fraction(value)

    try:
        result = payload["result"]
        if type(result) is not dict or set(result) != {"phi1", "gauge", "forests_checked"}:
            raise ValueError("native result requires phi1, gauge, and forests_checked")
        phi1 = exact_response(result["phi1"])
        raw_gauge = result["gauge"]
        if type(raw_gauge) is not dict or set(raw_gauge) != set(request["vertices"]):
            raise ValueError("native gauge must cover exactly the declared vertices")
        gauge = {name: exact_response(value) for name, value in raw_gauge.items()}
        checked = result["forests_checked"]
        if type(checked) is not int or not 1 <= checked <= MAX_NATIVE_FORESTS:
            raise ValueError("invalid native forest count")
        if phi1 < 0:
            raise ValueError("negative graph repair cost")
        cost = sum((Fraction(edge["weight"]) * abs(
            Fraction(edge["claim"]) - gauge[edge["v"]] + gauge[edge["u"]]
        ) for edge in request["edges"]), Fraction(0))
        if cost != phi1:
            raise ValueError("native potential cost does not match phi1")
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise NativeFunctionalProtocolError(f"malformed native result: {payload!r}") from error
    # Objective agreement checks primal consistency, not the global lower bound.
    # The native solver's complete exact enumeration remains trusted here.
    return phi1, gauge


def compute_graph_phi1(
    vertices: Sequence[str],
    edges: Sequence[Tuple[str, str, int | Fraction]],
    claims: Mapping[Tuple[str, str], int | Fraction],
    require_native: bool = False,
) -> Tuple[Fraction, dict[str, Fraction]]:
    """Return the exact graph quotient minimum and a minimizing potential.

    Uses the compiled native binary when one is present. Without a binary, the
    paper-local Python certificate builder answers unless require_native is set.
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
            "u": u,
            "v": v,
            "weight": encoded_weight,
            "claim": _exact(claims.get((u, v), 0)),
        })
    if set(claims) - edge_keys:
        raise ValueError("claim edge absent from declared carrier")

    binary = _find_binary()
    if binary is not None:
        return _run_native(binary, {"vertices": names, "edges": request_edges})
    if require_native:
        raise NativeFunctionalUnavailable("Compiled solve_graph_phi1 binary required")

    from symbol_game_governor import compute_exact_phi_1

    certificate = compute_exact_phi_1(names, list(edges), dict(claims))
    return certificate.phi_1, dict(certificate.primal_potentials)
