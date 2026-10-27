"""Infrastructure tree content-addressing and path validation.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

_SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "target",
        ".mypy_cache",
        ".pytest_cache",
        "exports",
    }
)
_SKIP_FILE_SUFFIXES = frozenset({".pyc", ".pyo", ".env"})
_SKIP_FILE_NAMES = frozenset({".env", ".env.local"})
_WINDOWS_INVALID_FILENAME_CHARS = frozenset('<>:"/\\|?*')
_WINDOWS_RESERVED_STEMS = frozenset(
    {
        "AUX",
        "CLOCK$",
        "CON",
        "CONIN$",
        "CONOUT$",
        "NUL",
        "PRN",
        *(f"COM{index}" for index in range(1, 10)),
        *(f"LPT{index}" for index in range(1, 10)),
    }
)


class SnapshotError(ValueError):
    """Snapshot or undo failure."""


def _is_windows_reserved_component(component: str) -> bool:
    return component.split(".", 1)[0].upper() in _WINDOWS_RESERVED_STEMS


def _has_windows_invalid_filename_char(component: str) -> bool:
    return any(
        character in _WINDOWS_INVALID_FILENAME_CHARS or ord(character) < 32
        for character in component
    )


def canonical_mutation_target(root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise SnapshotError("path alias refused: require a canonical relative path")
    relative = Path(relative_path)
    raw_parts = relative_path.replace("\\", "/").split("/")
    if (
        relative.is_absolute()
        or relative.anchor
        or relative.drive
        or "\\" in relative_path
        or any(
            not part
            or part in (".", "..")
            or _has_windows_invalid_filename_char(part)
            or part.endswith((" ", "."))
            or _is_windows_reserved_component(part)
            for part in raw_parts
        )
    ):
        raise SnapshotError("path alias refused: require a canonical relative path")

    cursor = root
    for part in raw_parts:
        if cursor.is_dir():
            try:
                child_names = tuple(child.name for child in cursor.iterdir())
            except OSError as exc:
                raise SnapshotError("path validation failed") from exc
            if part not in child_names and any(
                child.casefold() == part.casefold() for child in child_names
            ):
                raise SnapshotError(
                    "path alias refused: component case is not canonical"
                )
        cursor /= part

    target = cursor.resolve()
    try:
        relative_target = target.relative_to(root)
    except ValueError as exc:
        raise SnapshotError("path escape refused") from exc
    if not relative_target.parts:
        raise SnapshotError("path escape refused: target must be below paper_root")
    if relative_target.as_posix() != "/".join(raw_parts):
        raise SnapshotError("path alias refused: resolved target is not canonical")
    return target


def iter_files(root: Path) -> Iterable[Path]:
    root = root.resolve()
    if not root.is_dir():
        raise SnapshotError(f"not a directory: {root}")
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel_parts = p.relative_to(root).parts
        if any(part in _SKIP_DIR_NAMES for part in rel_parts[:-1]):
            continue
        if p.name in _SKIP_FILE_NAMES:
            continue
        if p.suffix in _SKIP_FILE_SUFFIXES:
            continue
        yield p


def tree_sha256(root: Path | str) -> str:
    root_p = Path(root).resolve()
    h = hashlib.sha256()
    count = 0
    for f in iter_files(root_p):
        rel = f.relative_to(root_p).as_posix().encode("utf-8")
        body = f.read_bytes()
        fh = hashlib.sha256(body).hexdigest().encode("ascii")
        h.update(rel)
        h.update(b"\0")
        h.update(fh)
        h.update(b"\n")
        count += 1
    if count == 0:
        h.update(b"EMPTY_TREE\n")
    return h.hexdigest()


__all__ = [
    "SnapshotError",
    "canonical_mutation_target",
    "iter_files",
    "tree_sha256",
]
