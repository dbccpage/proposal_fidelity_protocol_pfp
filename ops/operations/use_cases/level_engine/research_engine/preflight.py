# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Pre-flight against a target checker.  Never the replay of record.

* ``pin``: a checker file is used only at its pinned SHA-256 (``RR-PIN``).
* ``bar``: a checker that accepts an empty or a flag-only payload is refused
  before use (``CHECKER_BELOW_BAR``).
* ``run``: the checker runs in a subprocess, JSON on stdin and stdout.  An
  exception, a timeout or unreadable output is ``ERROR``, never a refusal.
* ``agreement``: each fixture's native verdict must equal the checker's.
  A difference is a named row (``DISAGREEMENT:<fixture>``).

With no pinned checker, the row waits: ``NEEDS_TARGET_CHECKER``, never a pass.

AuthorityEffect: None
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .canon import sha256_tag
from .errors import IntakeRefusal

TIMEOUT_S = 30


@dataclass(frozen=True)
class CheckerPin:
    path: Path
    sha256: str


def load_checker(pin: CheckerPin) -> Path:
    data = pin.path.read_bytes()
    if sha256_tag(data) != pin.sha256:
        raise IntakeRefusal("RR-PIN", f"{pin.path.name} does not match its pin")
    return pin.path


def run_checker(path: Path, obj: object) -> tuple[str, str | None]:
    try:
        proc = subprocess.run(
            [sys.executable, str(path)], input=json.dumps(obj).encode("utf-8"),
            capture_output=True, timeout=TIMEOUT_S, check=False,
        )
        out = json.loads(proc.stdout.decode("utf-8"))
    except (subprocess.TimeoutExpired, ValueError, OSError):
        return ("ERROR", None)
    raw = out.get("verdict") if isinstance(out, dict) else None
    verdict = {"PASS": "ACCEPT", "REFUSED": "REFUSE"}.get(str(raw), str(raw))
    if proc.returncode != 0 or not isinstance(out, dict) or verdict not in ("ACCEPT", "REFUSE"):
        return ("ERROR", None)
    code = out.get("code")
    return (verdict, None if code is None else str(code))


def bar(path: Path) -> None:
    for name, obj in (("empty", {}), ("flag-only", {"is_valid": True, "passes": True})):
        verdict, _ = run_checker(path, obj)
        if verdict != "REFUSE":
            raise IntakeRefusal("CHECKER_BELOW_BAR", f"the checker does not refuse the {name} payload")


def agreement(checker_input: Mapping[str, object], path: Path) -> tuple[str, ...]:
    fixtures = checker_input["fixtures"]
    assert isinstance(fixtures, list)
    rows = []
    for f in fixtures:
        verdict, _ = run_checker(path, f["input"])
        if verdict == "ERROR":
            rows.append(f"ERROR:{f['id']}")
        elif verdict != f["native_verdict"]:
            rows.append(f"DISAGREEMENT:{f['id']}")
    return tuple(rows)


def preflight(checker_input: Mapping[str, object], pin: CheckerPin | None) -> dict[str, object]:
    if pin is None:
        return {"rows": [], "target": "NEEDS_TARGET_CHECKER"}
    path = load_checker(pin)
    bar(path)
    rows = agreement(checker_input, path)
    return {"rows": list(rows), "target": "AGREES" if not rows else "DISAGREES"}


def refused_codes(results: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(set(results)))
