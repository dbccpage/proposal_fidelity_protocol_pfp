"""Documentation-integrity bounded-context module. AuthorityEffect: None."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Iterable

from .domain import IntegrityError, source_root_paths


def git(
    repo_root: Path, arguments: list[str], *, input_bytes: bytes | None = None
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_text(repo_root: Path, arguments: list[str]) -> str:
    result = git(repo_root, arguments)
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise IntegrityError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout.decode("utf-8", errors="surrogateescape").strip()


def git_nul_paths(repo_root: Path, arguments: list[str]) -> set[str]:
    result = git(repo_root, arguments)
    if result.returncode not in (0, 1):
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise IntegrityError(f"git {' '.join(arguments)} failed: {detail}")
    return {
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    }


def git_tracked_paths(repo_root: Path, contract: dict[str, Any]) -> set[str]:
    return git_nul_paths(repo_root, ["ls-files", "-z", "--", *source_root_paths(contract)])


def git_index_blobs(repo_root: Path, contract: dict[str, Any]) -> dict[str, str]:
    result = git(repo_root, ["ls-files", "-s", "-z", "--", *source_root_paths(contract)])
    if result.returncode:
        raise IntegrityError(result.stderr.decode("utf-8", errors="replace").strip())
    blobs: dict[str, str] = {}
    for record in result.stdout.split(b"\0"):
        if not record or b"\t" not in record:
            continue
        prefix, raw_path = record.split(b"\t", 1)
        parts = prefix.decode("ascii", errors="replace").split()
        if len(parts) >= 2:
            blobs[raw_path.decode("utf-8", errors="surrogateescape")] = parts[1]
    return blobs


def git_modified_paths(repo_root: Path, contract: dict[str, Any]) -> set[str]:
    roots = source_root_paths(contract)
    unstaged = git_nul_paths(repo_root, ["diff", "--name-only", "-z", "--", *roots])
    staged = git_nul_paths(repo_root, ["diff", "--cached", "--name-only", "-z", "--", *roots])
    return unstaged | staged


def git_ignored_paths(repo_root: Path, candidates: Iterable[str]) -> set[str]:
    values = sorted(set(candidates))
    if not values:
        return set()
    payload = "\0".join(values).encode("utf-8", errors="surrogateescape") + b"\0"
    result = git(repo_root, ["check-ignore", "-z", "--stdin"], input_bytes=payload)
    if result.returncode not in (0, 1):
        raise IntegrityError(result.stderr.decode("utf-8", errors="replace").strip())
    return {
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    }


def git_revision(repo_root: Path) -> str:
    return git_text(repo_root, ["rev-parse", "HEAD"])


def git_changed_paths(repo_root: Path, base: str) -> set[str]:
    return git_nul_paths(
        repo_root, ["diff", "--name-only", "--diff-filter=ACMRD", "-z", f"{base}...HEAD"]
    )


def git_show(repo_root: Path, revision: str, relative_path: str) -> str | None:
    result = git(repo_root, ["show", f"{revision}:{relative_path}"])
    if result.returncode:
        return None
    return result.stdout.decode("utf-8", errors="replace")
