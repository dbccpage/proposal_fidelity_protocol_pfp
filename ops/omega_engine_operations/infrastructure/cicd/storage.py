"""Infrastructure file storage and atomic receipt persistence for local_ci Bounded Context."""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path
from typing import Any

from omega_engine_operations.domain.cicd import LocalCiExecutionReceiptV3
from omega_engine_operations.domain.cicd.constants import _CONCRETE_PATH_TYPE, MAX_RECEIPT_BYTES
from omega_engine_operations.domain.cicd.errors import (
    LocalCiReceiptError,
    LocalCiReceiptErrorCode,
)
from omega_engine_operations.infrastructure.cicd.serialization import (
    canonical_local_ci_json_bytes,
    parse_local_ci_receipt,
)


def _read_receipt_buffer_once(path: Path) -> bytes:
    """Open once and perform one bounded max-plus-one receipt read."""
    try:
        with path.open("rb") as stream:
            data = stream.read(MAX_RECEIPT_BYTES + 1)
    except (OSError, TypeError, ValueError) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.IO_ERROR,
            f"cannot read receipt file: {error}",
        ) from error
    if len(data) > MAX_RECEIPT_BYTES:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INPUT_TOO_LARGE,
            "receipt exceeds the byte ceiling",
        )
    return data


def load_local_ci_receipt(path: str | os.PathLike[str]) -> LocalCiExecutionReceiptV3:
    """Read and strictly parse one receipt file."""
    try:
        exact_path = Path(path)
    except (TypeError, ValueError) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.IO_ERROR,
            f"cannot read receipt file: {error}",
        ) from error
    return parse_local_ci_receipt(_read_receipt_buffer_once(exact_path))


def _path_is_reparse_point(path: Path) -> bool:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    except (OSError, ValueError) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.IO_ERROR,
            f"cannot inspect atomic-write path component: {error}",
        ) from error
    windows_reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    file_attributes = getattr(metadata, "st_file_attributes", 0)
    return stat.S_ISLNK(metadata.st_mode) or bool(
        file_attributes & windows_reparse_flag
    )


def _validate_atomic_target(path: Any) -> Path:
    if type(path) is not _CONCRETE_PATH_TYPE:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_PATH,
            "atomic receipt target must be an exact concrete pathlib.Path",
        )
    if not _is_normalized_scalar_path(path):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_PATH,
            "atomic receipt target is not a normalized scalar file path",
        )
    try:
        target = path.absolute()
    except (OSError, RuntimeError, ValueError) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_PATH,
            "atomic receipt target cannot be normalized",
        ) from error
    parent = target.parent
    _validate_atomic_parent(parent)
    _validate_existing_atomic_target(target)
    return target


def _is_normalized_scalar_path(path: Path) -> bool:
    path_text = str(path)
    return bool(path_text) and not (
        "\0" in path_text
        or any(character in path_text for character in ("\n", "\r", "\t"))
        or any(part in {".", ".."} for part in path.parts)
        or path.name in {"", ".", ".."}
    )


def _validate_atomic_parent(parent: Path) -> None:
    cursor = parent
    while True:
        if _path_is_reparse_point(cursor):
            raise LocalCiReceiptError(
                LocalCiReceiptErrorCode.REPARSE_POINT_REFUSED,
                f"atomic receipt parent is a symlink, junction, or reparse point: {cursor}",
            )
        if cursor == cursor.parent:
            break
        cursor = cursor.parent
    try:
        parent_metadata = os.lstat(parent)
    except (OSError, ValueError) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_PATH,
            "atomic receipt parent must be an existing directory",
        ) from error
    if not stat.S_ISDIR(parent_metadata.st_mode):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_PATH,
            "atomic receipt parent must be an existing directory",
        )


def _validate_existing_atomic_target(target: Path) -> None:
    if not os.path.lexists(target):
        return
    if _path_is_reparse_point(target):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.REPARSE_POINT_REFUSED,
            "atomic receipt target must not be a symlink or reparse point",
        )
    try:
        target_metadata = os.lstat(target)
    except (OSError, ValueError) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.IO_ERROR,
            "cannot inspect existing atomic receipt target",
        ) from error
    if not stat.S_ISREG(target_metadata.st_mode):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_PATH,
            "existing atomic receipt target must be a regular file",
        )


def _fsync_parent_directory(parent: Path) -> None:
    """Fsync a directory where the host exposes POSIX directory descriptors."""
    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(parent, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_local_ci_receipt_atomic(
    path: Path, receipt: LocalCiExecutionReceiptV3
) -> None:
    """Persist via a same-directory, file-fsynced atomic replacement."""
    target = _validate_atomic_target(path)
    data = canonical_local_ci_json_bytes(receipt)
    temporary: Path | None = None
    descriptor: int | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
        )
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = None
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        _fsync_parent_directory(target.parent)
        _validate_atomic_target(target)
        os.replace(temporary, target)
        temporary = None
        _fsync_parent_directory(target.parent)
    except (OSError, RuntimeError, ValueError) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.IO_ERROR,
            f"atomic receipt write failed: {error}",
        ) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
