"""Transport harness to the Rust immune host CLI binary ``pfp_immune``.

Provides typed command execution for Epistemic Immune System (EIS)
and Prompt Civilization (PCIV) subcommands:
- screen: Thymus negative selection over sealed self panel
- decide: Two-signal disposition check using exact rational comparisons
- taint: Lineage DAG causal taint propagation with cycle refusal
- select: 60/30/10 ecological reserve partition via largest-remainder allocation
- exclusion: Multi-family consensus agreement and falsifier ordering

AuthorityEffect: None.
Validation checks execute in Rust; Python acts as an execution harness.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

ENVIRONMENT = "PFP_IMMUNE_BIN"
NAME = "pfp_immune"
TIMEOUT_SECONDS = 60
BUILD_HINT = (
    "IMMUNE_HOST_NOT_FOUND: set PFP_IMMUNE_BIN to the pfp_immune binary, "
    "put it on PATH, or build it with `cargo build --manifest-path code/rust/Cargo.toml -p pfp_immune`"
)


class ImmuneHostError(RuntimeError):
    """The immune host reported an execution or syntax error or could not be found."""


def _checkout_builds():
    executable = NAME + (".exe" if os.name == "nt" else "")
    for parent in Path(__file__).resolve().parents:
        for profile in ("release", "debug"):
            yield parent / "code" / "rust" / "target" / profile / executable


def binary() -> Path:
    """Resolve the host binary path."""
    named = os.environ.get(ENVIRONMENT) or shutil.which(NAME)
    if named and Path(named).is_file():
        return Path(named)
    for candidate in _checkout_builds():
        if candidate.is_file():
            return candidate
    raise ImmuneHostError(BUILD_HINT)


def is_available() -> bool:
    """Check whether the host binary exists and is callable."""
    try:
        return binary().is_file()
    except ImmuneHostError:
        return False


def call(
    subcommand: str, payload: dict[str, Any], *, use_tempfile: bool = False
) -> tuple[int, dict[str, Any]]:
    """Execute one host subcommand with input payload.

    Exit code 0: PASS -> returns (0, stdout_json)
    Exit code 1: FAIL / REFUSED / non-pass disposition -> returns (1, stdout_json)
    Exit code 2: Usage / syntax error -> raises ImmuneHostError
    """
    bin_path = binary()
    payload_bytes = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")

    if use_tempfile:
        with tempfile.TemporaryDirectory(prefix="pfp-immune-") as scratch:
            req_path = Path(scratch) / "input.json"
            req_path.write_bytes(payload_bytes)
            args = [str(bin_path), subcommand, "--input", str(req_path)]
            try:
                proc = subprocess.run(  # noqa: S603
                    args, capture_output=True, timeout=TIMEOUT_SECONDS, check=False
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise ImmuneHostError(f"IMMUNE_HOST_DID_NOT_RUN: {exc}") from exc
    else:
        args = [str(bin_path), subcommand]
        try:
            proc = subprocess.run(  # noqa: S603
                args,
                input=payload_bytes,
                capture_output=True,
                timeout=TIMEOUT_SECONDS,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ImmuneHostError(f"IMMUNE_HOST_DID_NOT_RUN: {exc}") from exc

    if proc.returncode == 2:
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        raise ImmuneHostError(f"IMMUNE_HOST_ERROR (code 2): {err}")
    if proc.returncode not in (0, 1):
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        raise ImmuneHostError(f"IMMUNE_HOST_FAILED (exit code {proc.returncode}): {err}")

    try:
        outcome = json.loads(proc.stdout.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        raise ImmuneHostError(
            f"IMMUNE_HOST_NO_OUTCOME: stdout={proc.stdout!r}, stderr={err!r}"
        ) from exc

    return proc.returncode, outcome


def _as_rational(val: Fraction | tuple[int, int] | Mapping[str, int]) -> dict[str, int]:
    """Convert rational representations to serde WireRational, prohibiting floats."""
    if isinstance(val, float):
        raise TypeError(f"floating point values prohibited in check paths: {val!r}")
    if isinstance(val, Fraction):
        return {"num": val.numerator, "den": val.denominator}
    if isinstance(val, (tuple, list)) and len(val) == 2:
        if isinstance(val[0], float) or isinstance(val[1], float):
            raise TypeError(f"floating point values prohibited in check paths: {val!r}")
        return {"num": int(val[0]), "den": int(val[1])}
    if isinstance(val, Mapping) and "num" in val and "den" in val:
        if isinstance(val["num"], float) or isinstance(val["den"], float):
            raise TypeError(f"floating point values prohibited in check paths: {val!r}")
        return {"num": int(val["num"]), "den": int(val["den"])}
    raise ValueError(f"cannot convert {val!r} to wire rational")


def screen(self_panel: Sequence[str], candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Execute thymus negative selection over clean self panel."""
    payload = {
        "self_panel": [str(s) for s in self_panel],
        "candidates": [
            {
                "rule_id": str(c["rule_id"]),
                "pattern": str(c["pattern"]),
                "capability_kind": str(c.get("capability_kind", "Detector")),
            }
            for c in candidates
        ],
    }
    _code, res = call("screen", payload)
    return res


def decide(
    signal1_matches: Sequence[str],
    danger_score: Fraction | tuple[int, int] | Mapping[str, int],
    threshold: Fraction | tuple[int, int] | Mapping[str, int],
) -> dict[str, Any]:
    """Execute two-signal disposition check using exact rationals."""
    payload = {
        "signal1_matches": [str(m) for m in signal1_matches],
        "danger_score": _as_rational(danger_score),
        "threshold": _as_rational(threshold),
    }
    _code, res = call("decide", payload)
    return res


def taint(edges: Sequence[Mapping[str, str]], revoked_parents: Sequence[str]) -> dict[str, Any]:
    """Execute lineage DAG causal taint propagation with cycle refusal."""
    payload = {
        "edges": [
            {
                "parent": str(e["parent"]),
                "child": str(e["child"]),
                "witness": str(e.get("witness", "sha256:00")),
            }
            for e in edges
        ],
        "revoked_parents": [str(r) for r in revoked_parents],
    }
    _code, res = call("taint", payload)
    return res


def select(population: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Execute 60/30/10 ecological reserve partition via largest-remainder allocation."""
    payload = {
        "population": [
            {
                "id": str(m["id"]),
                "fitness": _as_rational(m["fitness"]),
                "lineage_depth": int(m.get("lineage_depth", 0)),
            }
            for m in population
        ]
    }
    _code, res = call("select", payload)
    return res


def exclusion(family_votes: Mapping[str, str], hypotheses: Sequence[str]) -> dict[str, Any]:
    """Execute multi-family consensus agreement and falsifier ordering."""
    payload = {
        "family_votes": {str(k): str(v) for k, v in family_votes.items()},
        "hypotheses": [str(h) for h in hypotheses],
    }
    _code, res = call("exclusion", payload)
    return res
