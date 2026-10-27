"""Snapshot and filesystem utilities for gate 52 packaging checks.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Set, Tuple

CACHES: Set[str] = {
    ".git",
    ".lake",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".ipynb_checkpoints",
    "htmlcov",
}
MAX_FILE_BYTES: int = 64 * 1024 * 1024
MAX_PAYLOAD_BYTES: int = 256 * 1024 * 1024
SOURCE_REF: str = "operads/skills/core-paper-review-swarm/references/canonical_zenodo_republication_gate_prompt.md"


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_name(name: str) -> str:
    if (
        not name
        or "\\" in name
        or ":" in name
        or PurePosixPath(name).is_absolute()
        or any(part in ("", ".", "..") for part in name.split("/"))
        or any(ord(char) < 32 for char in name)
    ):
        raise ValueError(f"unsafe path: {name!r}")
    return name


def _regular(path: Path, directory: bool = False) -> None:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError(f"symlink or reparse point: {path}")
    if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise ValueError(f"nonregular path: {path}")


def _snapshot(root: Path) -> Dict[str, bytes]:
    _regular(root, directory=True)
    files: Dict[str, bytes] = {}
    total = 0

    def walk_error(error: OSError) -> None:
        raise error

    for current, directories, names in os.walk(root, followlinks=False, onerror=walk_error):
        folder = Path(current)
        for name in directories:
            _regular(folder / name, directory=True)
        directories[:] = [
            name
            for name in directories
            if name not in CACHES
            and not name.endswith(".egg-info")
            and (folder / name).relative_to(root).as_posix() != "lean4/b"
        ]
        for name in names:
            path = folder / name
            _regular(path)
            if name == ".coverage" or name.startswith(".coverage."):
                continue
            relative = _safe_name(path.relative_to(root).as_posix())
            size = path.stat().st_size
            total += size
            if size > MAX_FILE_BYTES or total > MAX_PAYLOAD_BYTES:
                raise ValueError("snapshot byte limit exceeded; no partial PASS is permitted")
            with path.open("rb") as stream:
                data = stream.read(MAX_FILE_BYTES + 1)
            if len(data) != size:
                raise ValueError(f"file changed while reading: {relative}")
            files[relative] = data
    return dict(sorted(files.items(), key=lambda pair: pair[0].encode("utf-8")))


def _identity(files: Dict[str, bytes]) -> Tuple[str, List[Dict[str, Any]]]:
    rows = [
        {"path": name, "bytes": len(data), "sha256": _digest(data)} for name, data in files.items()
    ]
    encoded = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return _digest(encoded), rows


def _checksums(data: bytes) -> Dict[str, str]:
    rows: Dict[str, str] = {}
    for line in data.decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise ValueError("malformed checksum entry")
        checksum, name = match.groups()
        _safe_name(name)
        if name in rows:
            raise ValueError(f"duplicate checksum entry: {name}")
        rows[name] = checksum
    if not rows or list(rows) != sorted(rows, key=lambda name: name.encode("utf-8")):
        raise ValueError("empty or unsorted checksum manifest")
    return rows


def _normalize(text: str) -> str:
    return "".join(char.casefold() for char in text if char.isalnum())


def _multiline(value: object) -> bool:
    return (
        isinstance(value, str)
        or isinstance(value, list)
        and all(isinstance(line, str) for line in value)
    )


def _stored_output(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    kind = value.get("output_type")
    if kind == "stream":
        return value.get("name") in ("stdout", "stderr") and _multiline(value.get("text"))
    if kind not in ("display_data", "execute_result"):
        return False
    if not isinstance(value.get("data"), dict) or not isinstance(value.get("metadata"), dict):
        return False
    return (
        kind != "execute_result"
        or type(value.get("execution_count")) is int
        and value["execution_count"] > 0
    )


def resolve_paper_paths(paper_path_input: Path | str) -> Tuple[Path, Path]:
    """Resolve package root directory and main monograph file path."""
    p = Path(paper_path_input).resolve()
    if p.is_file():
        paper_dir = p.parent
        monograph = p
    elif p.is_dir():
        paper_dir = p
        md_files = sorted(
            f
            for f in paper_dir.glob("*.md")
            if not f.name.lower().endswith(
                (
                    "_change_log.md",
                    "_claim_ledger.md",
                    "_math_spine.md",
                    "readme.md",
                    "review_scope.md",
                    "_supplement.md",
                    "supplement.md",
                )
            )
        )
        if len(md_files) > 1:
            raise ValueError(
                "Ambiguous monograph; pass its exact Markdown path: "
                + ", ".join(f.name for f in md_files)
            )
        if md_files:
            monograph = md_files[0]
        else:
            monograph = paper_dir / f"{paper_dir.name}.md"
    else:
        raise FileNotFoundError(f"Paper path does not exist: {p}")
    return paper_dir, monograph
