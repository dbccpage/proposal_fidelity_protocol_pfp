"""Bound candidate readback and retained revisions. AuthorityEffect: None.

Revisions are never overwritten by this cooperative single-writer path. Host
storage remains trusted; these checks do not prevent concurrent hostile writes.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from pathlib import Path
from typing import Any

from adversary.use_cases.intelligence_digestion.archive_custody import (
    ArchiveCustodyError,
    checked_path,
)


class TransferCustodyError(RuntimeError):
    """No receiving acknowledgment is available for these candidate bytes."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}:{detail}" if detail else code)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant {value!r}")


def _finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("nonfinite JSON number")
    return result


def _candidate_object(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique_object,
            parse_constant=_reject_constant, parse_float=_finite_float,
        )
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise TransferCustodyError("TRANSFER_CUSTODY_JSON_INVALID") from exc
    if type(value) is not dict:
        raise TransferCustodyError("TRANSFER_CUSTODY_JSON_OBJECT_REQUIRED")
    return value


def _read_regular_file(root: Path, path: Path) -> bytes:
    path = checked_path(root, path)
    if not stat.S_ISREG(path.lstat().st_mode):
        raise TransferCustodyError("TRANSFER_CUSTODY_REGULAR_FILE_REQUIRED")
    return path.read_bytes()


def _persist_revision(root: Path, revisions_root: Path, raw: bytes, digest: str) -> Path:
    directory = checked_path(root, revisions_root)
    directory.mkdir(parents=True, exist_ok=True)
    revision = checked_path(root, directory / f"{digest}.json")
    try:
        with revision.open("xb") as handle:
            handle.write(raw)
            handle.flush()
    except FileExistsError:
        pass
    if _read_regular_file(root, revision) != raw:
        raise TransferCustodyError("TRANSFER_CUSTODY_REVISION_MISMATCH")
    with revision.open("r+b") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise TransferCustodyError("TRANSFER_CUSTODY_REGULAR_FILE_REQUIRED")
        if handle.read() != raw:
            raise TransferCustodyError("TRANSFER_CUSTODY_REVISION_MISMATCH")
        os.fsync(handle.fileno())
    if os.name != "nt":
        directory_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    return revision


def validate_candidate_revision(
    repo_root: Path,
    candidate_path: Path,
    revisions_root: Path,
    *,
    antibody_id: str,
    finding: str,
    run_id: str,
    source_id: str,
) -> tuple[str, str]:
    """Retain the same bytes that were parsed and return their hash and locator."""
    expected = {
        "antibody_id": antibody_id,
        "target_pattern": finding,
        "pharmacy_status": "candidate",
        "authority_effect": "None",
        "source_run_id": run_id,
        "source_task_id": f"digestion:{source_id}",
    }
    try:
        raw = _read_regular_file(repo_root, candidate_path)
        candidate = _candidate_object(raw)
        for key, value in expected.items():
            if type(value) is not str or not value or type(candidate.get(key)) is not str:
                raise TransferCustodyError("TRANSFER_CUSTODY_BINDING_INVALID", key)
            if candidate[key] != value:
                raise TransferCustodyError("TRANSFER_CUSTODY_BINDING_MISMATCH", key)
        digest = hashlib.sha256(raw).hexdigest()
        revision = _persist_revision(repo_root, revisions_root, raw, digest)
    except ArchiveCustodyError as exc:
        raise TransferCustodyError("TRANSFER_CUSTODY_PATH_REFUSED", exc.code) from exc
    except OSError as exc:
        raise TransferCustodyError("TRANSFER_CUSTODY_IO_FAILED", type(exc).__name__) from exc
    return f"sha256:{digest}", revision.relative_to(repo_root.absolute()).as_posix()
