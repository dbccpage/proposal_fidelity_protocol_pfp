"""Harvest skill invocations out of Claude Code session transcripts.

The sensor already existed; nothing had read it. Claude Code writes one JSONL
per session under `~/.claude/projects/<mangled-cwd>/<session-uuid>.jsonl`, and
every skill invocation appears there in one of two shapes:

  * a `tool_use` block with `name == "Skill"`, carrying `input.skill` and
    `caller.type`;
  * a `<command-name>/x</command-name>` span in user-message text, which is how
    a slash invocation is recorded.

Both are harvested. Missing the second would under-count `auto-oe-autop` by a
factor of three.

## Why this is urgent rather than merely useful

Claude Code's default `cleanupPeriodDays` is 30 -- the same order as the cull
window this ledger exists to feed. The evidence is on a rolling expiry and a gap
is unrecoverable, so a backfill deferred is a backfill partly lost.

## Worktrees

Each worktree mangles to its own project directory, so a repository worked on
from several worktrees has its invocations scattered across several of them.
Harvesting only the current one silently under-counts.

`AuthorityEffect: None`. Reading a transcript certifies nothing.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from omega_engine_operads.infrastructure.skill_garden.usage_ledger import (
    append_usage_events,
    garden_roster,
    make_usage_event,
    normalize_skill_id,
)

#: A slash invocation, as Claude Code records it in user-message text.
_COMMAND_NAME = re.compile(r"<command-name>/?([A-Za-z0-9][A-Za-z0-9._-]*)</command-name>")

_WORKTREE_SEGMENT = re.compile(r"[\\/]\.claude[\\/]worktrees[\\/][^\\/]+$")


def home_projects_dir(home: Path | None = None) -> Path:
    return (home or Path.home()) / ".claude" / "projects"


def mangle(path: Path) -> str:
    """Claude Code's project-directory name for a working directory.

    Observed: `C:\\Users\\a343o\\source\\repos\\anomalonpy` becomes
    `C--Users-a343o-source-repos-anomalonpy`, and the worktree beneath it
    becomes `...-anomalonpy--claude-worktrees-bg-session-worktree`. Each of
    `:`, `\\`, `/` and `.` maps to `-`.
    """
    text = str(path)
    for character in (":", "\\", "/", "."):
        text = text.replace(character, "-")
    return text


def main_checkout(repo_root: Path) -> Path:
    """The main checkout for a repo root that may itself be a worktree."""
    text = str(repo_root)
    stripped = _WORKTREE_SEGMENT.sub("", text)
    return Path(stripped)


def project_dirs_for_repo(repo_root: Path, home: Path | None = None) -> list[Path]:
    """Every project directory belonging to this checkout or a worktree of it."""
    projects = home_projects_dir(home)
    if not projects.is_dir():
        return []
    prefix = mangle(main_checkout(repo_root))
    return sorted(
        entry for entry in projects.iterdir() if entry.is_dir() and entry.name.startswith(prefix)
    )


def _stamp(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _text_of(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "\n".join(parts)
    return ""


def iter_skill_invocations(jsonl_path: Path) -> Iterator[dict[str, Any]]:
    """Yield raw invocation records from one transcript.

    A malformed line is skipped rather than fatal: transcripts are a foreign
    format this repository does not own, and one truncated row must not cost the
    whole harvest.
    """
    try:
        lines = jsonl_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return
    for line in lines:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        stamp = _stamp(record.get("timestamp"))
        session = str(record.get("sessionId") or "").strip()
        message = record.get("message")
        content = message.get("content") if isinstance(message, dict) else None

        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") != "tool_use" or block.get("name") != "Skill":
                    continue
                payload = block.get("input")
                raw = payload.get("skill") if isinstance(payload, dict) else None
                caller = block.get("caller")
                caller_kind = (caller.get("type") if isinstance(caller, dict) else None) or "direct"
                if raw:
                    yield {
                        "raw": raw,
                        "invoked_at": stamp,
                        "session_id": session,
                        "caller": str(caller_kind),
                        "channel": "tool_use",
                    }

        for match in _COMMAND_NAME.finditer(_text_of(content)):
            yield {
                "raw": match.group(1),
                "invoked_at": stamp,
                "session_id": session,
                "caller": "slash",
                "channel": "slash",
            }


def harvest(
    repo_root: Path,
    *,
    home: Path | None = None,
    since: str | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    roster = garden_roster(repo_root)
    directories = project_dirs_for_repo(repo_root, home)

    events: list[dict[str, Any]] = []
    seen_raw: set[str] = set()
    unmatched: dict[str, int] = {}
    transcripts = 0

    for directory in directories:
        worktree = directory.name != mangle(main_checkout(repo_root))
        for transcript in sorted(directory.glob("*.jsonl")):
            transcripts += 1
            for record in iter_skill_invocations(transcript):
                raw = record["raw"]
                seen_raw.add(raw)
                stamp = record["invoked_at"]
                if not stamp:
                    continue
                if since and stamp[:10] < since:
                    continue
                skill_id = normalize_skill_id(raw, roster)
                if skill_id is None:
                    unmatched[raw] = unmatched.get(raw, 0) + 1
                    continue
                events.append(
                    make_usage_event(
                        skill_id=skill_id,
                        invoked_at=stamp,
                        host="claude",
                        channel=record["channel"],
                        caller=record["caller"],
                        session_id=record["session_id"],
                        cwd_kind="worktree" if worktree else "root",
                    )
                )

    result: dict[str, Any] = {
        "project_dirs": len(directories),
        "transcripts": transcripts,
        "invocations_found": len(events),
        "distinct_names_seen": len(seen_raw),
        "unmatched": dict(sorted(unmatched.items(), key=lambda item: -item[1])),
    }
    if apply:
        result.update(append_usage_events(repo_root, events))
    return result
