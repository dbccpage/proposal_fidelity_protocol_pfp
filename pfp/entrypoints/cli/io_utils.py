"""I/O utilities for Symbol Game CLI presentation layer.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

from pfp.domain import loads_strict_json


def _read_json(path: Path | None) -> Any:
    if path is None:
        text = sys.stdin.read()
        return loads_strict_json(text, "stdin")
    return loads_strict_json(path.read_text(encoding="utf-8"), str(path))


def _write_json(path: Path | None, value: Mapping[str, Any]) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path is None:
        sys.stdout.write(text)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_text(path: Path | None, text: str) -> None:
    if path is None:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8", newline="\n")


def _parse_csv(val: str | None) -> tuple[str, ...]:
    if not val:
        return ()
    parts = [x.strip() for x in val.split(",") if x.strip()]
    return tuple(sorted(set(parts)))


def _write_verdict_md(path: Path, result: Mapping[str, Any]) -> None:
    status = "PASS" if result.get("overall_passed") else "FAIL"
    lines = [
        f"# Host verify — {status}",
        "",
        f"- packet: `{result.get('packet_id')}`",
        f"- source_kind: `{result.get('source_kind')}`",
        f"- AuthorityEffect: None",
        f"- host_terminal: `{result.get('host_terminal')}`",
        "",
        "| check | pass | evidence |",
        "| --- | --- | --- |",
    ]
    for c in result.get("checks", []):
        ev = str(c.get("evidence", ""))[:100].replace("|", "/")
        lines.append(f"| `{c.get('id')}` | {c.get('passed')} | `{ev}` |")
    lines.append("")
    lines.append("## remaining_delta")
    for r in result.get("remaining_delta", []):
        lines.append(f"- {r}")
    lines.append("")
    if result.get("overall_passed"):
        lines.append("## FEED MODEL NEXT")
        lines.append("GATE11 done. Next packet: **SG-OESOS-ROUTE-001** only.")
    else:
        lines.append("## FEED MODEL NEXT")
        lines.append("Repair from remaining_delta. Do not invent GlobalGreen.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
