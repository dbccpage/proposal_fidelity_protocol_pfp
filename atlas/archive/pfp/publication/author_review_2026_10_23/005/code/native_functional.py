# Vendored copy, kept in this package so that it runs without the repository.
# vendored-from-path: providers/adapters/native_functional.py
# vendored-from-commit: 52cb5457f6c485ba548cfd292f6012a941ed22cf
# vendored-from-sha256: 0f3590824eeedf1b91919eeac997193ef9ae16013f84857a79341dd7d402c045
# The source file is byte-identical at commit 691a01ec3e0ee4f06b4d13b1b8f751edb67c5cee.
# Local changes: this comment block, and the import statements put in the order
# required by the package lint settings. No executable statement is changed.
# code/tests/test_vendored_sources.py checks this inside a repository checkout.
"""Transport graph inputs to the pinned canonical Rust functional calculator.

The SHA-256 pin is supplied by the caller's trusted build process. It binds the
executed bytes, not a source-to-binary provenance proof. No Python fallback is
permitted for missing, refused, or malformed native results.
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

FUNCTIONAL_OWNER = "engine/crates_rs/core_functional/src"


class NativeFunctionalUnavailable(RuntimeError):
    code = "FUNCTIONAL_BOUNDARY_UNAVAILABLE"

    def __init__(self, reason: str) -> None:
        super().__init__(f"{self.code}: {reason}; calculator: {FUNCTIONAL_OWNER}")


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

    Unasserted edges receive the declared zero claim. Unknown claim edges and
    duplicate edges are refused instead of being silently discarded.
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
        raise ValueError("claim edge absent from declared carrier")
    binary = os.environ.get("CORE_FUNCTIONAL_GRAPH_BIN")
    expected = os.environ.get("CORE_FUNCTIONAL_GRAPH_SHA256", "").lower()
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
    if completed.returncode != 0:
        raise NativeFunctionalUnavailable("native graph evaluator refused")
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
