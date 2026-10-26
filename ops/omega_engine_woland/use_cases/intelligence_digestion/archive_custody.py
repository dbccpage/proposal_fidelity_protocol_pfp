"""Filesystem custody checks for a cooperative single writer. AuthorityEffect: None.

These checks reject existing redirects. They are not an OS sandbox against a
writer replacing directories between a check, read, and move.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Any

SOURCE_MANIFEST_SCHEMA = "omega.intelligence.source-manifest.v1"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_RESERVED = re.compile(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", re.IGNORECASE)


class ArchiveCustodyError(RuntimeError):
    """Retain source and archive bytes when custody cannot be established."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}:{detail}" if detail else code)


def require_digest(value: object) -> str:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        raise ArchiveCustodyError("ARCHIVE_CUSTODY_DIGEST_INVALID")
    return value


def relative_parts(value: object) -> tuple[str, ...]:
    if type(value) is not str or not value or "\\" in value:
        raise ArchiveCustodyError("ARCHIVE_CUSTODY_PATH_INVALID")
    parts = tuple(value.split("/"))
    if any(not part or part in {".", ".."} or ":" in part or part[-1] in " ."
           or _RESERVED.fullmatch(part)
           or any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in part)
           for part in parts):
        raise ArchiveCustodyError("ARCHIVE_CUSTODY_PATH_INVALID", value)
    return parts


def checked_path(root: Path, path: Path) -> Path:
    """Check lexical containment and every existing ancestor, including the root."""
    root, path = root.absolute(), path.absolute()
    if ".." in path.parts or ".." in root.parts:
        raise ArchiveCustodyError("ARCHIVE_CUSTODY_PATH_INVALID", str(path))
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ArchiveCustodyError("ARCHIVE_CUSTODY_PATH_OUTSIDE_ROOT", str(path)) from exc
    if relative.parts:
        relative_parts(relative.as_posix())
    for candidate in (*reversed(path.parents), path):
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & 0x400:
            raise ArchiveCustodyError("ARCHIVE_CUSTODY_LINK_REFUSED", str(candidate))
    return path


def archivable_source_path(root: Path, path: Path) -> Path:
    path = checked_path(root, path)
    for relative in ("_ic/nara/historical", "_ic/odni/migrations", "_ic/odni/migration"):
        protected = root.absolute() / relative
        if path.is_relative_to(protected) or protected.is_relative_to(path):
            raise ArchiveCustodyError("ARCHIVE_CUSTODY_PROTECTED_SOURCE", str(path))
    return path


def _directory_members(root: Path, bundle: Path) -> list[tuple[str, Path]]:
    members = []

    def walk_error(error: OSError) -> None:
        raise error

    for directory, dirs, files in os.walk(bundle, followlinks=False, onerror=walk_error):
        for name in (*dirs, *files):
            member = checked_path(root, Path(directory) / name)
            mode = member.lstat().st_mode
            if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise ArchiveCustodyError("ARCHIVE_CUSTODY_MEMBER_INVALID", str(member))
        for name in files:
            member = Path(directory) / name
            members.append((member.relative_to(bundle).as_posix(), member))
    return members


def bundle_entries(root: Path, bundle: Path) -> list[dict[str, Any]]:
    bundle = checked_path(root, bundle)
    if not bundle.exists():
        raise ArchiveCustodyError("ARCHIVE_CUSTODY_BUNDLE_MISSING", str(bundle))
    if bundle.is_file():
        members = [(bundle.name, bundle)]
    elif bundle.is_dir():
        members = _directory_members(root, bundle)
    else:
        raise ArchiveCustodyError("ARCHIVE_CUSTODY_BUNDLE_INVALID", str(bundle))
    entries = []
    for name, member in sorted(members):
        relative_parts(name)
        raw = member.read_bytes()
        entries.append({"path": name, "size_bytes": len(raw),
                        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest()})
    if not entries:
        raise ArchiveCustodyError("ARCHIVE_CUSTODY_BUNDLE_EMPTY", str(bundle))
    return entries


def validate_sealed_manifest(sealed: object) -> dict[str, Any]:
    expected = {"schema_version", "source_id", "producer_id", "source_class", "source_locator",
                "manifest_sha256", "entries", "authority_effect"}
    if (type(sealed) is not dict or set(sealed) != expected
            or sealed["schema_version"] != SOURCE_MANIFEST_SCHEMA
            or sealed["authority_effect"] != "None"):
        raise ArchiveCustodyError("ARCHIVE_CUSTODY_MANIFEST_INVALID")
    require_digest(sealed["source_id"])
    require_digest(sealed["manifest_sha256"])
    relative_parts(sealed["source_locator"])
    if any(type(sealed[key]) is not str or not sealed[key].strip()
           for key in ("producer_id", "source_class")):
        raise ArchiveCustodyError("ARCHIVE_CUSTODY_MANIFEST_INVALID")
    entries = sealed["entries"]
    if type(entries) is not list or not entries:
        raise ArchiveCustodyError("ARCHIVE_CUSTODY_MANIFEST_INVALID")
    names = []
    for entry in entries:
        if (type(entry) is not dict or set(entry) != {"path", "size_bytes", "sha256"}
                or type(entry["size_bytes"]) is not int or entry["size_bytes"] < 0):
            raise ArchiveCustodyError("ARCHIVE_CUSTODY_MANIFEST_INVALID")
        relative_parts(entry["path"])
        require_digest(entry["sha256"])
        names.append(entry["path"])
    if names != sorted(set(names)):
        raise ArchiveCustodyError("ARCHIVE_CUSTODY_MANIFEST_INVALID")
    return sealed
