"""Resolve the repository root that owns ``_ic/``.

Run folders are durable intelligence: they are mined later, so they must
not land in a linked git worktree that is deleted when its branch merges. From a
linked worktree the root is the main checkout; the worktree's own
``_ic/`` is gitignored scratch that dies with the worktree.

Precedence:

1. ``OMEGA_INTELLIGENCE_ROOT`` names the directory under which ``_ic/``
   lives (the repository root, not the ``_ic`` folder itself).
2. From inside a linked worktree, the main checkout (parent of the common git dir).
3. From anywhere inside the main checkout, its top-level directory, so a run
   launched from a subdirectory still lands in the central store.
4. Outside git, and with the variable unset, there is no durable store to
   name. This is a typed refusal (``INTELLIGENCE_ROOT_UNRESOLVED``). It used to
   fall back to the working directory, which scattered run folders wherever a
   command happened to be launched.

AuthorityEffect: None.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

INTELLIGENCE_ROOT_ENV = "OMEGA_INTELLIGENCE_ROOT"
INTELLIGENCE_ROOT_UNRESOLVED = "INTELLIGENCE_ROOT_UNRESOLVED"

GitDirQuery = Callable[[Path], tuple[Path, Path, Path] | None]


class IntelligenceRootUnresolvedError(RuntimeError):
    """Typed refusal raised by the Path-returning resolver; carries the ``Refusal``."""

    def __init__(self, refusal: Refusal) -> None:
        self.refusal = refusal
        self.code = refusal.code
        super().__init__(f"{refusal.code}: {refusal.message}")


def query_git_dirs(cwd: Path) -> tuple[Path, Path, Path] | None:
    """Return ``(git_dir, git_common_dir, top_level)`` for ``cwd``, or ``None`` outside git."""
    try:
        completed = subprocess.run(
            [
                "git",
                "rev-parse",
                "--path-format=absolute",
                "--git-dir",
                "--git-common-dir",
                "--show-toplevel",
            ],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != 3:
        return None
    return Path(lines[0]).resolve(), Path(lines[1]).resolve(), Path(lines[2]).resolve()


def try_resolve_intelligence_repo_root(
    cwd: Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    git_dirs: GitDirQuery | None = None,
) -> Result[Path, Refusal]:
    """Return the directory whose ``_ic/`` receives run folders, or a refusal."""
    env = os.environ if environ is None else environ
    override = env.get(INTELLIGENCE_ROOT_ENV, "").strip()
    if override:
        return Ok(Path(override).resolve())

    base = (Path.cwd() if cwd is None else Path(cwd)).resolve()
    dirs = (query_git_dirs if git_dirs is None else git_dirs)(base)
    if dirs is None:
        return Err(
            Refusal(
                code=INTELLIGENCE_ROOT_UNRESOLVED,
                message=(
                    f"{base} is not inside a git checkout and {INTELLIGENCE_ROOT_ENV} "
                    "is not set; refusing to write intelligence into the working directory"
                ),
                locus="omega_engine_operating_system.adapters.intelligence_custody.intelligence_root",
            )
        )
    git_dir, common_dir, top_level = dirs
    if git_dir == common_dir:
        return Ok(top_level)
    return Ok(common_dir.parent)


def resolve_intelligence_repo_root(
    cwd: Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    git_dirs: GitDirQuery | None = None,
) -> Path:
    """Path form for scripts; raises ``IntelligenceRootUnresolvedError`` instead of guessing."""
    resolved = try_resolve_intelligence_repo_root(cwd, environ=environ, git_dirs=git_dirs)
    if resolved.is_err:
        raise IntelligenceRootUnresolvedError(resolved.unwrap_err())
    return resolved.unwrap()


__all__ = [
    "INTELLIGENCE_ROOT_ENV",
    "INTELLIGENCE_ROOT_UNRESOLVED",
    "IntelligenceRootUnresolvedError",
    "query_git_dirs",
    "resolve_intelligence_repo_root",
    "try_resolve_intelligence_repo_root",
]
