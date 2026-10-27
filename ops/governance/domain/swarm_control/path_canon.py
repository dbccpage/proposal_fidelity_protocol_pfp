"""Path canonicalization for main/worktree guards (STORY-033).

Collapses ., .., alternate separators, and case (Windows normcase).
Does not require the path to exist (resolve strict=False).
AuthorityEffect: None.
"""

from __future__ import annotations

import os
from pathlib import Path


def canonicalize_path(path: str) -> str:
    """Return a comparable path string (forward slashes, normcase, no trailing slash)."""
    raw = str(path).strip()
    if not raw:
        return ""
    try:
        resolved = Path(raw).resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        # Fallback: manual . / .. collapse with os.path
        resolved_s = os.path.normpath(raw)
        try:
            resolved = Path(resolved_s)
        except (OSError, RuntimeError, ValueError):
            resolved_s = raw.replace("\\", "/")
            return os.path.normcase(resolved_s).rstrip("/") or "/"
    # normcase on Windows lowercases AND forces backslashes — flip to / after.
    out = os.path.normcase(str(resolved)).replace("\\", "/").rstrip("/")
    return out or "/"


def canonical_repo_path(path: str) -> str:
    """Canonicalize a repository-relative path (POSIX separators, normpath, no leading slash)."""
    p = str(path).replace("\\", "/").strip()
    if p.startswith("/"):
        p = p.lstrip("/")
    parts = []
    for seg in p.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        parts.append(seg)
    return "/".join(parts)


def paths_equal(a: str, b: str) -> bool:
    return canonicalize_path(a) == canonicalize_path(b)


def path_is_under(child: str, root: str) -> bool:
    c = canonicalize_path(child)
    r = canonicalize_path(root)
    if not r:
        return False
    if c == r:
        return True
    return c.startswith(r + "/")


def paths_conflict(a: str, b: str) -> bool:
    c1 = canonicalize_path(a)
    c2 = canonicalize_path(b)
    if c1 == c2:
        return True
    if c1.startswith(c2 + "/"):
        return True
    if c2.startswith(c1 + "/"):
        return True
    return False


paths_overlap = paths_conflict
