"""Fail-closed paths shared by deposit verification, manifests and ZIP assembly."""

from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path, PurePosixPath


def _link(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def safe_path(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    if (
        not relative
        or not pure.parts
        or pure.is_absolute()
        or pure.as_posix() != relative
        or ".." in pure.parts
        or "\\" in relative
        or ":" in relative
        or any(ord(c) < 32 for c in relative)
        or any(p.rstrip(" .") != p or p.split(".")[0].upper() in reserved for p in pure.parts)
    ):
        raise ValueError(f"unsafe deposit path: {relative!r}")
    root = root.absolute()
    for ancestor in (root, *root.parents):
        if _link(ancestor):
            raise ValueError(f"symlink or junction in deposit root: {ancestor}")
    path = root
    for part in pure.parts:
        path = path / part
        if _link(path):
            raise ValueError(f"symlink or junction in deposit path: {relative}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"deposit path escapes root: {relative}")
    return path


def _register_case_path(seen: dict[str, tuple[str, bool]], relative: str) -> None:
    parts = PurePosixPath(relative).parts
    for index in range(1, len(parts) + 1):
        prefix = "/".join(parts[:index])
        is_file = index == len(parts)
        prior = seen.get(prefix.casefold())
        if prior is not None and (prior[0] != prefix or prior[1] != is_file):
            raise ValueError(f"case-colliding file or directory: {relative}")
        if prior is not None and is_file:
            raise ValueError(f"duplicate deposit path: {relative}")
        seen[prefix.casefold()] = (prefix, is_file)


def walk_files(
    root: Path, excluded_dirs: set[str], excluded_names: set[str], excluded_suffixes: set[str]
) -> list[Path]:
    safe_path(root, "__root_check__")
    files: list[Path] = []
    seen: dict[str, tuple[str, bool]] = {}

    def traversal_error(error: OSError) -> None:
        raise error

    for directory, dirs, names in os.walk(root, followlinks=False, onerror=traversal_error):
        parent = Path(directory)
        relative_parent = parent.relative_to(root)
        archived = relative_parent.parts[:2] == ("docs", "source_archive")
        for name in (*dirs, *names):
            if _link(parent / name):
                raise ValueError(f"symlink or junction in deposit: {parent / name}")
        # Captured sources are an exhaustive raw inventory. Their historical
        # directory names cannot silently exempt them from the release.
        if not archived:
            dirs[:] = [
                name
                for name in dirs
                if name not in {"__pycache__", ".pytest_cache", ".ruff_cache"}
                and not (
                    parent == root
                    and (
                        name in excluded_dirs or name.startswith(".") or name.endswith(".egg-info")
                    )
                )
            ]
        for name in names:
            path = parent / name
            if not archived and (
                (parent == root and name in excluded_names) or path.suffix in excluded_suffixes
            ):
                continue
            relative = path.relative_to(root).as_posix()
            safe_path(root, relative)
            if not stat.S_ISREG(path.stat().st_mode):
                raise ValueError(f"nonregular deposit file: {relative}")
            _register_case_path(seen, relative)
            files.append(path)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix().encode("utf-8"))


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(root: Path, manifest: Path) -> list[tuple[str, str]]:
    safe_path(root, manifest.absolute().relative_to(root.absolute()).as_posix())
    entries: list[tuple[str, str]] = []
    seen: dict[str, tuple[str, bool]] = {}
    for number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([a-fA-F0-9]{64})  (.+)", line)
        if match is None:
            raise ValueError(f"malformed manifest line {number}")
        digest, relative = match.groups()
        safe_path(root, relative)
        _register_case_path(seen, relative)
        if relative == manifest.name or (
            relative.lower().endswith(".zip")
            and PurePosixPath(relative).parts[:2] != ("docs", "source_archive")
        ):
            raise ValueError(f"circular manifest entry: {relative}")
        entries.append((relative, digest.lower()))
    if [name for name, _ in entries] != sorted(
        (name for name, _ in entries), key=lambda name: name.encode("utf-8")
    ):
        raise ValueError("manifest paths are not in ordinal UTF-8 order")
    return entries
