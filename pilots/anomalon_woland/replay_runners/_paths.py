"""Locate pilot and repository roots by sentinel rather than directory depth."""
from __future__ import annotations

from pathlib import Path


def _candidates(start: Path) -> tuple[Path, ...]:
    resolved = start.resolve()
    return (resolved, *resolved.parents)


def pilots_root(start: Path) -> Path:
    """Return the pilot estate containing its matrix and base template."""
    for candidate in _candidates(start):
        for estate in (candidate, candidate / "pilots", candidate / "omega_engine_woland/tests/pilots"):
            if (estate / "matrix").is_dir() and (
                (estate / "pilot_0000000").is_dir() or (estate / "pilot_0000006").is_dir()
            ):
                return estate
    raise FileNotFoundError(f"PILOTS_ROOT_NOT_FOUND: {start}")


def repository_root(start: Path) -> Path:
    """Return the linked-worktree root, accepting a .git file or directory."""
    candidates = _candidates(start)
    for candidate in candidates:
        if (candidate / ".git").exists():
            return candidate
    for candidate in candidates:
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise FileNotFoundError(f"REPOSITORY_ROOT_NOT_FOUND: {start}")
