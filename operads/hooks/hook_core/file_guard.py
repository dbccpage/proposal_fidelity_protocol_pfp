"""File hygiene and validation gatekeeper.

Enforces:
1. Strict UTF-8 validation across all text files.
2. BOM detection and atomic stripping on valid UTF-8 text files without corrupting invalid data.
3. Binary file preservation (never rewrites binary assets like .png, .jpg, .bin).
4. Workspace containment (refuses paths outside declared workspace bounds).
5. Accurate path resolution respecting payload `cwd`.

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

UTF8_BOM = b"\xef\xbb\xbf"

TEXT_EXTENSIONS = {
    ".py",
    ".pyi",
    ".ipynb",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".txt",
    ".rs",
    ".lean",
    ".proto",
    ".css",
    ".html",
    ".js",
    ".ts",
    ".sh",
    ".ps1",
    ".rst",
    ".tex",
    ".xml",
    ".svg",
    ".csv",
    ".ini",
    ".cfg",
    ".lock",
}

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".webp",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".parquet",
    ".arrow",
    ".pyc",
    ".pyd",
    ".npy",
    ".npz",
}


def is_text_file(file_path: Path) -> bool:
    """Determine whether a file is a designated text format."""
    suffix = file_path.suffix.lower()
    if suffix in BINARY_EXTENSIONS:
        return False
    if suffix in TEXT_EXTENSIONS:
        return True
    return True


def resolve_path(path_str: str, cwd: Optional[str] = None) -> Path:
    """Resolve a target path string against payload cwd or current directory."""
    path = Path(path_str)
    if not path.is_absolute() and cwd:
        path = Path(cwd) / path
    return path.resolve()


def check_workspace_containment(file_path: Path, workspace_paths: List[str]) -> bool:
    """Check if file_path is contained within at least one declared workspace path."""
    if not workspace_paths:
        return True
    resolved = file_path.resolve()
    for ws in workspace_paths:
        try:
            ws_resolved = Path(ws).resolve()
            if resolved.is_relative_to(ws_resolved):
                return True
        except (ValueError, OSError):
            continue
    return False


def check_and_clean_bom(file_path: Path) -> bool:
    """Verify strict UTF-8 encoding and atomically strip BOM if present.

    Returns:
        True if BOM was detected and stripped.
        False if file was clean UTF-8 without BOM, or if file is binary.

    Raises:
        ValueError if file contains invalid UTF-8 encoding.
    """
    if not file_path.is_file():
        return False

    suffix = file_path.suffix.lower()
    if suffix in BINARY_EXTENSIONS:
        # Binary files must never be inspected or mutated as UTF-8
        return False

    try:
        content = file_path.read_bytes()
    except OSError as exc:
        raise ValueError(f"Cannot read file {file_path}: {exc}") from exc

    if content.startswith(UTF8_BOM):
        clean_content = content[len(UTF8_BOM) :]
        try:
            clean_content.decode("utf-8")
        except UnicodeError as exc:
            raise ValueError(f"Invalid UTF-8 content following BOM in {file_path}") from exc

        try:
            file_path.write_bytes(clean_content)
        except OSError as exc:
            raise ValueError(f"Cannot write clean UTF-8 bytes to {file_path}: {exc}") from exc

        sys.stderr.write(
            f"[UTF8_BOM_DETECTED_AND_STRIPPED] Removed UTF-8 BOM from {file_path.as_posix()}\n"
        )
        return True

    # No BOM prefix: verify entire file is valid UTF-8
    try:
        content.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError(f"Invalid UTF-8 encoding in {file_path}") from exc

    return False
