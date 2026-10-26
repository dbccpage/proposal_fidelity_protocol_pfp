"""Receipt destinations. ``--out`` never selects a corpus write."""

from __future__ import annotations

import os
from pathlib import Path

FORBIDDEN_RECEIPT_PARTS = frozenset({".agents", ".claude", ".codex", ".grok", "_intelligence", "_ic"})


def _normalized_parts(path: str) -> tuple[str, ...]:
    parts: list[str] = []
    for part in Path(path).parts:
        if part in {".", ""}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return tuple(parts)


def _governed_parts(path: str, root: Path | None) -> tuple[str, ...]:
    # An absolute path inside the repository root is judged by its parts below that
    # root, so a checkout under .claude/worktrees/ can still write runs/ receipts.
    candidate = Path(path)
    if candidate.is_absolute():
        base = Path(os.path.normpath(root if root is not None else Path.cwd()))
        try:
            return _normalized_parts(str(Path(os.path.normpath(candidate)).relative_to(base)))
        except ValueError:
            pass
    return _normalized_parts(path)


def receipt_destination_allowed(path: str, root: Path | None = None) -> bool:
    """False when any path component below the repository root (default: cwd) is a governed corpus root."""
    return not any(part in FORBIDDEN_RECEIPT_PARTS for part in _governed_parts(path, root))


def write_receipt(path: str, payload: str, root: Path | None = None) -> None:
    """Write a receipt. Refuses governed corpus roots and does not create them."""
    if not receipt_destination_allowed(path, root):
        raise PermissionError(f"receipt destination is not allowed: {path}")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(payload, encoding="utf-8", newline="\n")
