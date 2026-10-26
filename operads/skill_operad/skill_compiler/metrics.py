#!/usr/bin/env python3
"""Validate an autoskill run record and derive its counts deterministically.

The input contains semantic rows selected by an LLM or human. This program owns
all arithmetic. It does not certify the quality of those rows or authorize edits.
AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

RUN_SCHEMA = "omega.autoskill.run.v1"
SIGNAL_FIELDS = frozenset({"signal_type", "description", "durable", "confidence", "evidence"})
CONFIDENCE = frozenset({"HIGH", "MEDIUM", "LOW"})


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def load_run(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise ValueError(f"invalid run file: {err}") from err
    if not isinstance(data, dict) or data.get("schema") != RUN_SCHEMA:
        raise ValueError(f"run must be an object with schema {RUN_SCHEMA!r}")
    _text(data.get("session_id"), "session_id")
    signals = data.get("signals")
    if not isinstance(signals, list):
        raise ValueError("signals must be a list")
    for index, row in enumerate(signals):
        if not isinstance(row, dict):
            raise ValueError(f"signals[{index}] must be an object")
        unknown = sorted(set(row) - SIGNAL_FIELDS)
        if unknown:
            raise ValueError(f"signals[{index}] has unknown fields: {', '.join(unknown)}")
        _text(row.get("signal_type"), f"signals[{index}].signal_type")
        _text(row.get("description"), f"signals[{index}].description")
        if type(row.get("durable")) is not bool:
            raise ValueError(f"signals[{index}].durable must be boolean")
        if row.get("confidence") not in CONFIDENCE:
            raise ValueError(f"signals[{index}].confidence must be HIGH, MEDIUM, or LOW")
        evidence = row.get("evidence", [])
        if not isinstance(evidence, list) or not all(
            isinstance(item, str) and item.strip() for item in evidence
        ):
            raise ValueError(f"signals[{index}].evidence must be a list of non-empty strings")
    for field in ("proposals", "skills_updated", "corrections", "manual_skill_edits"):
        value = data.get(field, [])
        if not isinstance(value, list):
            raise ValueError(f"{field} must be a list")
    return data


def _git_skill_commit_count(repo_root: Path) -> int | None:
    proc = subprocess.run(
        ["git", "log", "--format=%H", "--", "omega_engine_operads/skills", ".agents/skills"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return None
    return len([line for line in proc.stdout.splitlines() if line.strip()])


def summarize(run: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    signals = run["signals"]
    by_type = Counter(row["signal_type"] for row in signals)
    by_confidence = Counter(row["confidence"] for row in signals)
    durable = sum(1 for row in signals if row["durable"])
    evidenced = sum(1 for row in signals if row.get("evidence"))
    return {
        "schema": "omega.autoskill.metrics.v1",
        "session_id": run["session_id"],
        "signal_count": len(signals),
        "durable_signal_count": durable,
        "evidenced_signal_count": evidenced,
        "signals_by_type": dict(sorted(by_type.items())),
        "signals_by_confidence": dict(sorted(by_confidence.items())),
        "proposal_count": len(run.get("proposals", [])),
        "skills_updated_count": len(run.get("skills_updated", [])),
        "correction_count": len(run.get("corrections", [])),
        "manual_skill_edit_count": len(run.get("manual_skill_edits", [])),
        "repository_skill_commit_count": _git_skill_commit_count(repo_root),
        "capture_rate": None,
        "capture_rate_reason": "No rate is emitted without an independently defined eligible-signal denominator.",
        "authority_effect": "None",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument("--out", default=None, type=Path)
    args = parser.parse_args()
    try:
        result = summarize(load_run(args.file), args.repo_root.resolve())
    except ValueError as err:
        print(json.dumps({"ok": False, "error": str(err)}, indent=2), file=sys.stderr)
        return 2
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
