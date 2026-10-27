"""Project typed Markdown without overwriting files in the four host estates.

This is a byte-preserving, absent-or-identical projection, not admission. Static
symlinks and Windows reparse points are refused. Preflight conflicts make no
changes; exclusive file creation refuses final-file races. A filesystem error
or a concurrent change after creation begins can leave a partial projection.
There is no cross-file transaction or protection against hostile concurrent
parent-directory replacement; callers must serialize directory ownership.
"""

from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass, replace
from pathlib import Path

from operations.use_cases.packaging.sync_cross_host_skills import (
    CANONICAL_SKILL_ROOT,
    HOST_SKILL_ROOTS,
)

_SKILL_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z", re.ASCII)
_RESERVED = {"con", "prn", "aux", "nul"} | {
    f"{prefix}{number}" for prefix in ("com", "lpt") for number in range(1, 10)
}


class HostProjectionRefusal(ValueError):
    """A projection could not safely satisfy its filesystem contract."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class _Destination:
    path: Path
    content: bytes
    identity: tuple[int, int, int, int] | None


def _validate_request(repo_root: Path, packages: tuple, check: bool) -> None:
    if not isinstance(repo_root, Path) or not repo_root.is_absolute():
        raise HostProjectionRefusal("HOST_PROJECTION_INVALID_REQUEST", "absolute Path required")
    if ".." in repo_root.parts or "\x00" in str(repo_root) or type(check) is not bool:
        raise HostProjectionRefusal("HOST_PROJECTION_INVALID_REQUEST", "invalid root or check mode")
    if type(packages) is not tuple or not packages:
        raise HostProjectionRefusal(
            "HOST_PROJECTION_INVALID_REQUEST", "nonempty package tuple required"
        )
    seen: set[str] = set()
    for row in packages:
        _validate_package(row, seen)


def _validate_package(row: tuple, seen: set[str]) -> None:
    if type(row) is not tuple or len(row) != 2:
        raise HostProjectionRefusal("HOST_PROJECTION_INVALID_REQUEST", "expected (skill_id, bytes)")
    skill_id, content = row
    if type(skill_id) is not str or not _SKILL_ID.fullmatch(skill_id):
        raise HostProjectionRefusal("HOST_PROJECTION_INVALID_REQUEST", "invalid skill_id")
    if skill_id in _RESERVED or skill_id in seen:
        raise HostProjectionRefusal(
            "HOST_PROJECTION_INVALID_REQUEST", "reserved or duplicate skill_id"
        )
    if type(content) is not bytes or not content:
        raise HostProjectionRefusal(
            "HOST_PROJECTION_INVALID_REQUEST", "nonempty exact bytes required"
        )
    seen.add(skill_id)


def _safe_stat(path: Path) -> os.stat_result | None:
    try:
        result = path.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(result.st_mode) or getattr(result, "st_file_attributes", 0) & getattr(
        stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400
    ):
        raise HostProjectionRefusal("HOST_PROJECTION_UNSAFE_PATH", str(path))
    return result


def _require_directory(path: Path, *, required: bool = True) -> bool:
    result = _safe_stat(path)
    if result is None:
        if required:
            raise HostProjectionRefusal("HOST_PROJECTION_HOST_ROOT_MISSING", str(path))
        return False
    if not stat.S_ISDIR(result.st_mode):
        raise HostProjectionRefusal("HOST_PROJECTION_UNSAFE_PATH", str(path))
    return True


def _check_ancestors(path: Path) -> None:
    for ancestor in reversed(path.parents):
        _require_directory(ancestor)


def _identity(result: os.stat_result) -> tuple[int, int, int, int]:
    return result.st_dev, result.st_ino, result.st_size, result.st_mtime_ns


def _inspect_file(path: Path, content: bytes) -> tuple[int, int, int, int] | None:
    before = _safe_stat(path)
    if before is None:
        return None
    if not stat.S_ISREG(before.st_mode):
        raise HostProjectionRefusal("HOST_PROJECTION_UNSAFE_PATH", str(path))
    actual = path.read_bytes()
    after = _safe_stat(path)
    if after is None or _identity(before) != _identity(after):
        raise HostProjectionRefusal("HOST_PROJECTION_CHANGED", str(path))
    if actual != content:
        raise HostProjectionRefusal("HOST_PROJECTION_CONFLICT", str(path))
    return _identity(after)


def _preflight(repo_root: Path, packages: tuple[tuple[str, bytes], ...]) -> list[_Destination]:
    _check_ancestors(repo_root)
    _require_directory(repo_root)
    for host in HOST_SKILL_ROOTS:
        _require_directory(repo_root / Path(host).parts[0])
        _require_directory(repo_root / host)
    destinations = []
    for skill_id, content in packages:
        destinations.extend(_package_destinations(repo_root, skill_id, content))
    return destinations


def _package_destinations(repo_root: Path, skill_id: str, content: bytes) -> list[_Destination]:
    destinations = []
    roots = HOST_SKILL_ROOTS
    if (repo_root / CANONICAL_SKILL_ROOT).is_dir():
        roots = (CANONICAL_SKILL_ROOT, *roots)
    for host in roots:
        directory = repo_root / host / skill_id
        _require_directory(directory, required=False)
        path = directory / "SKILL.md"
        destinations.append(_Destination(path, content, _inspect_file(path, content)))
    return destinations


def _verify_unchanged(destinations: list[_Destination]) -> None:
    for destination in destinations:
        _check_ancestors(destination.path.parent)
        _require_directory(destination.path.parent, required=False)
        identity = _inspect_file(destination.path, destination.content)
        if identity != destination.identity:
            raise HostProjectionRefusal("HOST_PROJECTION_CHANGED", str(destination.path))


def _create_file(destination: _Destination) -> _Destination:
    _check_ancestors(destination.path.parent)
    if not _require_directory(destination.path.parent, required=False):
        try:
            destination.path.parent.mkdir()
        except FileExistsError as exc:
            raise HostProjectionRefusal(
                "HOST_PROJECTION_CHANGED", str(destination.path.parent)
            ) from exc
    _require_directory(destination.path.parent)
    try:
        with destination.path.open("xb") as stream:
            stream.write(destination.content)
    except FileExistsError as exc:
        raise HostProjectionRefusal("HOST_PROJECTION_CHANGED", str(destination.path)) from exc
    identity = _inspect_file(destination.path, destination.content)
    if identity is None:
        raise HostProjectionRefusal("HOST_PROJECTION_CHANGED", str(destination.path))
    return replace(destination, identity=identity)


def _project(destinations: list[_Destination], *, check: bool) -> None:
    if check:
        if any(destination.identity is None for destination in destinations):
            raise HostProjectionRefusal("HOST_PROJECTION_MISSING", "projection is incomplete")
        _verify_unchanged(destinations)
        return
    for index, destination in enumerate(destinations):
        _verify_unchanged(destinations)
        if destination.identity is None:
            destinations[index] = _create_file(destination)
    _verify_unchanged(destinations)


def project_typed_packages(
    repo_root: Path,
    packages: tuple[tuple[str, bytes], ...],
    *,
    check: bool = False,
) -> tuple[str, ...]:
    """Return every planned relative path after successful projection/verification.

    All configured host roots must already exist. Differing bytes always refuse,
    even with a generated marker. No resources are pruned and no file is replaced.
    ``check=True`` requires a complete identical projection and performs no writes.
    """
    _validate_request(repo_root, packages, check)
    try:
        destinations = _preflight(repo_root, packages)
        _project(destinations, check=check)
    except OSError as exc:
        raise HostProjectionRefusal("HOST_PROJECTION_IO_ERROR", str(exc)) from exc
    return tuple(destination.path.relative_to(repo_root).as_posix() for destination in destinations)
