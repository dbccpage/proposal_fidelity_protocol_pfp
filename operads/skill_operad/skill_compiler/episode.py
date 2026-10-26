#!/usr/bin/env python3
"""Append-only episode sink for skill-compiler learnings.

Episodes are episodic memory (State -> Receipt). They are NOT procedural
SKILL.md text. Autoskill and meta stages write here first; resolve() decides
representation before any skill edit.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONFIDENCE_OK = frozenset({"HIGH", "MEDIUM", "LOW"})
INPUT_SCHEMA = "omega.skill_compiler.episode.input.v1"
EPISODE_SCHEMA = "omega.skill_compiler.episode.v1"
INPUT_FIELDS = frozenset(
    {
        "schema",
        "source",
        "signal_type",
        "signal",
        "proposed_invariant",
        "locus",
        "confidence",
        "session_id",
        "evidence",
        "extra",
    }
)

# Episodes live under repo runs/ so they are not skill-garden procedural mass.
DEFAULT_REL_EPISODES_DIR = Path("runs") / "skill_compiler" / "episodes"


def repo_root_from(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".git").exists() and (candidate / ".agents").is_dir():
            return candidate
    return Path.cwd().resolve()


def episodes_dir(repo_root: Path) -> Path:
    return repo_root / DEFAULT_REL_EPISODES_DIR


def _day_path(repo_root: Path, when: datetime | None = None) -> Path:
    ts = when or datetime.now(timezone.utc)
    return episodes_dir(repo_root) / f"{ts.strftime('%Y-%m-%d')}.jsonl"


def make_episode(
    *,
    source: str,
    signal_type: str = "unspecified",
    signal: str,
    proposed_invariant: str,
    locus: str = "",
    confidence: str = "MEDIUM",
    session_id: str = "",
    evidence: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    conf = (confidence or "MEDIUM").strip().upper()
    if conf not in CONFIDENCE_OK:
        conf = "MEDIUM"
    normalized_signal = (signal or "").strip()
    normalized_invariant = (proposed_invariant or "").strip()
    if not normalized_signal:
        raise ValueError("signal must be a non-empty string")
    if not normalized_invariant:
        raise ValueError("proposed_invariant must be a non-empty string")
    normalized_evidence = evidence or []
    if not isinstance(normalized_evidence, list) or not all(
        isinstance(item, str) and item.strip() for item in normalized_evidence
    ):
        raise ValueError("evidence must be a list of non-empty strings")

    now = datetime.now(timezone.utc)
    ep: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "ts": now.isoformat(),
        "source": (source or "unknown").strip() or "unknown",
        "signal_type": (signal_type or "unspecified").strip() or "unspecified",
        "signal": normalized_signal,
        "proposed_invariant": normalized_invariant,
        "locus": (locus or "").strip(),
        "confidence": conf,
        "session_id": (session_id or "").strip(),
        "evidence": [item.strip() for item in normalized_evidence],
        "schema": EPISODE_SCHEMA,
    }
    if extra:
        ep["extra"] = extra
    return ep


def load_episode_input(path: Path) -> dict[str, Any]:
    """Load and validate an inert JSON episode proposal.

    LLM-generated prose crosses the process boundary only through this file.
    Shell interpolation is therefore unnecessary and unknown fields fail closed.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise ValueError(f"invalid episode input file: {err}") from err
    if not isinstance(payload, dict):
        raise ValueError("episode input must be a JSON object")
    unknown = sorted(set(payload) - INPUT_FIELDS)
    if unknown:
        raise ValueError(f"unknown episode input fields: {', '.join(unknown)}")
    if payload.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"schema must equal {INPUT_SCHEMA!r}")
    for field in ("source", "signal", "proposed_invariant"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    for field in ("signal_type", "locus", "confidence", "session_id"):
        if field in payload and not isinstance(payload[field], str):
            raise ValueError(f"{field} must be a string")
    evidence = payload.get("evidence", [])
    if not isinstance(evidence, list) or not all(isinstance(item, str) and item.strip() for item in evidence):
        raise ValueError("evidence must be a list of non-empty strings")
    extra = payload.get("extra")
    if extra is not None and not isinstance(extra, dict):
        raise ValueError("extra must be an object when present")
    return payload


def append_episode(repo_root: Path, episode: dict[str, Any]) -> Path:
    """Append one episode as a single JSONL line. Creates parent dirs."""
    if not episode.get("id"):
        episode = {**episode, "id": str(uuid.uuid4())}
    if not episode.get("ts"):
        episode = {
            **episode,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
    raw_timestamp = episode.get("ts")
    if not isinstance(raw_timestamp, str):
        raise ValueError("episode ts must be an ISO-8601 string")
    try:
        timestamp = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
    except ValueError as err:
        raise ValueError("episode ts must be a valid ISO-8601 timestamp") from err
    if timestamp.tzinfo is None:
        raise ValueError("episode ts must include a UTC offset")
    path = _day_path(repo_root, timestamp.astimezone(timezone.utc))
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(episode, ensure_ascii=False, separators=(",", ":"))
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")
    return path


def load_episodes(
    repo_root: Path,
    *,
    day: str | None = None,
    limit: int = 0,
) -> list[dict[str, Any]]:
    """Load episodes for one day (YYYY-MM-DD) or all files in the sink."""
    root = episodes_dir(repo_root)
    if not root.is_dir():
        return []
    if day:
        paths = [root / f"{day}.jsonl"]
    else:
        paths = sorted(root.glob("*.jsonl"))
    out: list[dict[str, Any]] = []
    for p in paths:
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if limit > 0:
        return out[-limit:]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)

    ap = sub.add_parser("append", help="Append one episode from an inert JSON file")
    ap.add_argument("--file", required=True, type=Path)

    lp = sub.add_parser("list", help="List recent episodes")
    lp.add_argument("--day", default=None, help="YYYY-MM-DD")
    lp.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()

    if args.cmd == "append":
        try:
            payload = load_episode_input(args.file)
            ep = make_episode(
                source=payload["source"],
                signal_type=payload.get("signal_type", "unspecified"),
                signal=payload["signal"],
                proposed_invariant=payload["proposed_invariant"],
                locus=payload.get("locus", ""),
                confidence=payload.get("confidence", "MEDIUM"),
                session_id=payload.get("session_id", ""),
                evidence=payload.get("evidence", []),
                extra=payload.get("extra"),
            )
        except ValueError as err:
            print(json.dumps({"ok": False, "error": str(err)}, indent=2), file=sys.stderr)
            return 2
        path = append_episode(root, ep)
        print(json.dumps({"ok": True, "path": str(path), "id": ep["id"]}, indent=2))
        return 0

    if args.cmd == "list":
        rows = load_episodes(root, day=args.day, limit=args.limit)
        print(json.dumps(rows, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
