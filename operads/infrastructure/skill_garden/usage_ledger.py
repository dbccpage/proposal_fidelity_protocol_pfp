"""Append-only ledger of skill invocations.

## What this measures, and what it does not

It records that a skill was **explicitly invoked** -- a `Skill` tool call or a
slash command. Three limits follow, and they are stated here rather than
discovered later, because an under-counting sensor driving an archive decision
archives skills that are in use:

1. **Invocation is not use.** A skill whose content reaches a model by
   description-match, or through a `_shared` document another skill cites,
   leaves no record here.
2. **One host only.** The capture paths available today see Claude Code. Use on
   `.codex` or `.grok` is invisible, so a skill must never be nominated for
   archival on the strength of a host this ledger cannot see.
3. **The ledger under-counts by construction.** Absence of a record is not
   evidence of absence of use.

## Why a separate ledger

`.agents/operad/record_trace.py` is a complete, durable recorder and its pattern
is reused here -- content-addressed entry id, an `observed_at` distinct from the
event time, `authority_effect: "None"`. Its *file* is not reused, for four
reasons: its payload requires finite non-negative `phi_before`/`phi_after` and a
usage event has no phi; it raises when one `(skill_id, run_id)` pair recurs with
different evidence, which two invocations in one session do immediately; it
rewrites a whole JSON array per append, which is O(n) and a merge conflict on
every branch; and its schema is bound to phi-descent, so overloading it would
leave a later reader unable to tell "the skill ran" from "the skill contracted
phi".

JSONL under `runs/` follows the convention `runs/skill_compiler/episodes/`
already sets: day-sharded, append-only, O(1), and merge-friendly across
worktrees.

`AuthorityEffect: None`.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

USAGE_SCHEMA = "omega.skill_garden.usage_event.v1"
CLASSIFICATION = "RecordedResidualObservation"

DEFAULT_REL_USAGE_DIR = Path("runs") / "skill_usage"
SKILLS_REL = Path("omega_engine_operads") / "skills"

#: Fields bound into `entry_id`. Deliberately excludes `observed_at`, so
#: re-harvesting the same transcript twice is idempotent rather than duplicating.
_IDENTITY_FIELDS = (
    "schema",
    "skill_id",
    "invoked_at",
    "host",
    "channel",
    "caller",
    "session_id",
)

_THREAD_LOCK = threading.Lock()


class UsageLedgerError(RuntimeError):
    """Typed boundary failure for malformed or unavailable usage storage."""


def repo_root_from(start: Path | None = None) -> Path:
    """Walk upward for the repository root.

    Keyed on `.git` plus `.agents`, both of which exist. The sibling helper in
    `check_skill_usage.py` keys on `omega_engine_py/`, which does not, so its
    loop never matches and it silently scans whatever the cwd happens to be.
    """
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".git").exists() and (candidate / ".agents").is_dir():
            return candidate
    raise UsageLedgerError(f"no repository root above {here}")


def usage_dir(repo_root: Path) -> Path:
    return repo_root / DEFAULT_REL_USAGE_DIR


def _day_path(repo_root: Path, when: datetime) -> Path:
    return usage_dir(repo_root) / f"{when.strftime('%Y-%m-%d')}.jsonl"


def garden_roster(repo_root: Path) -> frozenset[str]:
    """Package names currently in the canonical garden.

    Leading `_` and `.` are excluded: `_shared` and `_templates` are libraries,
    not skills, and a dot-prefixed directory is hidden from host discovery.
    """
    root = repo_root / SKILLS_REL
    if not root.is_dir():
        raise UsageLedgerError(f"skill garden not found at {root}")
    return frozenset(
        path.parent.name
        for path in root.glob("*/SKILL.md")
        if not path.parent.name.startswith(("_", "."))
    )


def normalize_skill_id(raw: str, roster: frozenset[str]) -> str | None:
    """Reduce a recorded invocation name to a garden package, or refuse it.

    Invocations arrive scope-prefixed in at least two shapes:
    `.claude/worktrees/bg-session-worktree:auto-oe-autop` (a directory-scoped
    skill) and `mattpocock-skills:grilling` (a plugin skill). Only the first is
    ours. Returning `None` for anything not in the roster is what stops a plugin
    or built-in from being minted as a garden name -- and what stops a renamed
    package's old name from resurrecting as a phantom.
    """
    if not isinstance(raw, str):
        return None
    candidate = raw.strip()
    if not candidate:
        return None
    if ":" in candidate:
        candidate = candidate.rsplit(":", 1)[-1].strip()
    return candidate if candidate in roster else None


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def make_usage_event(
    *,
    skill_id: str,
    invoked_at: datetime | str,
    host: str = "claude",
    channel: str = "transcript",
    caller: str = "direct",
    session_id: str = "",
    cwd_kind: str = "root",
) -> dict[str, Any]:
    """Build one event. Pure; performs no I/O."""
    if not isinstance(skill_id, str) or not skill_id.strip():
        raise UsageLedgerError("skill_id must be a non-empty string")
    if isinstance(invoked_at, datetime):
        stamp = invoked_at.astimezone(timezone.utc).isoformat()
    else:
        stamp = str(invoked_at).strip()
    if not stamp:
        raise UsageLedgerError("invoked_at must be a timestamp")

    payload = {
        "schema": USAGE_SCHEMA,
        "skill_id": skill_id.strip(),
        "invoked_at": stamp,
        "host": (host or "unknown").strip() or "unknown",
        "channel": (channel or "unknown").strip() or "unknown",
        "caller": (caller or "direct").strip() or "direct",
        "session_id": (session_id or "").strip(),
    }
    entry_id = (
        "sha256:"
        + hashlib.sha256(
            _canonical_bytes({key: payload[key] for key in _IDENTITY_FIELDS})
        ).hexdigest()
    )
    return {
        **payload,
        "entry_id": entry_id,
        "cwd_kind": (cwd_kind or "root").strip() or "root",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "authority_effect": "None",
        "classification": CLASSIFICATION,
    }


@contextmanager
def _exclusive_lock(lock_path: Path, timeout_seconds: float) -> Iterator[None]:
    """Cross-process lock by atomically creating one file.

    Lifted from `record_trace.py`, including its Windows caveat: the unlink can
    raise PermissionError while another process still holds the handle, and that
    must not fail the caller.
    """
    deadline = time.monotonic() + timeout_seconds
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(descriptor, str(os.getpid()).encode("ascii"))
            os.fsync(descriptor)
        except (FileExistsError, PermissionError):
            if time.monotonic() >= deadline:
                raise UsageLedgerError(f"timed out acquiring usage lock {lock_path}")
            time.sleep(0.01)
    try:
        yield
    finally:
        os.close(descriptor)
        try:
            lock_path.unlink(missing_ok=True)
        except PermissionError:
            pass


def _existing_entry_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    found = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            found.add(json.loads(line)["entry_id"])
        except (json.JSONDecodeError, KeyError) as err:
            raise UsageLedgerError(f"malformed usage row in {path}: {err}") from err
    return found


def append_usage_events(
    repo_root: Path,
    events: Sequence[dict[str, Any]],
    *,
    timeout_seconds: float = 30.0,
) -> dict[str, int]:
    """Append events, skipping any whose `entry_id` is already on file.

    Content addressing makes re-harvesting the same transcripts idempotent
    without holding a lock across the whole corpus.
    """
    by_day: dict[Path, list[dict[str, Any]]] = {}
    for event in events:
        stamp = event["invoked_at"]
        day = usage_dir(repo_root) / f"{str(stamp)[:10]}.jsonl"
        by_day.setdefault(day, []).append(event)

    written = 0
    skipped = 0
    with _THREAD_LOCK:
        for day, rows in sorted(by_day.items()):
            day.parent.mkdir(parents=True, exist_ok=True)
            lock_path = day.with_name(day.name + ".lock")
            with _exclusive_lock(lock_path, timeout_seconds):
                seen = _existing_entry_ids(day)
                fresh = []
                for row in rows:
                    if row["entry_id"] in seen:
                        skipped += 1
                        continue
                    seen.add(row["entry_id"])
                    fresh.append(row)
                if not fresh:
                    continue
                with day.open("a", encoding="utf-8", newline="\n") as handle:
                    for row in fresh:
                        handle.write(json.dumps(row, ensure_ascii=True) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                written += len(fresh)
    return {"written": written, "skipped": skipped, "days": len(by_day)}


def load_usage_events(
    repo_root: Path,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[dict[str, Any]]:
    directory = usage_dir(repo_root)
    if not directory.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for day in sorted(directory.glob("*.jsonl")):
        for line in day.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as err:
                raise UsageLedgerError(f"malformed usage row in {day}: {err}") from err
            stamp = _parse_stamp(row.get("invoked_at", ""))
            if stamp is None:
                continue
            if since is not None and stamp < since:
                continue
            if until is not None and stamp > until:
                continue
            rows.append(row)
    return rows


def _parse_stamp(value: str) -> datetime | None:
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def last_used_index(repo_root: Path, *, since: datetime | None = None) -> dict[str, datetime]:
    """Most recent recorded invocation per skill id."""
    latest: dict[str, datetime] = {}
    for row in load_usage_events(repo_root, since=since):
        stamp = _parse_stamp(row["invoked_at"])
        if stamp is None:
            continue
        skill_id = row["skill_id"]
        if skill_id not in latest or stamp > latest[skill_id]:
            latest[skill_id] = stamp
    return latest


def ledger_span(repo_root: Path) -> tuple[datetime | None, datetime | None]:
    """Earliest and latest recorded invocation.

    The cull policy refuses to nominate anything when this span is shorter than
    its window: a 30-day window over 20 days of data measures the sensor, not
    the garden.
    """
    stamps = [
        stamp
        for stamp in (
            _parse_stamp(row.get("invoked_at", "")) for row in load_usage_events(repo_root)
        )
        if stamp is not None
    ]
    if not stamps:
        return (None, None)
    return (min(stamps), max(stamps))


def summarize(repo_root: Path) -> dict[str, Any]:
    """Counts a human can read without opening the JSONL."""
    roster = garden_roster(repo_root)
    index = last_used_index(repo_root)
    first, last = ledger_span(repo_root)
    seen = sorted(skill for skill in index if skill in roster)
    return {
        "roster": len(roster),
        "seen": len(seen),
        "never_seen": len(roster) - len(seen),
        "span_start": first.isoformat() if first else None,
        "span_end": last.isoformat() if last else None,
        "span_days": (last - first).total_seconds() / 86400.0 if first and last else 0.0,
        "seen_skills": seen,
    }


def _events_for(rows: Iterable[dict[str, Any]]) -> int:
    return sum(1 for _ in rows)
