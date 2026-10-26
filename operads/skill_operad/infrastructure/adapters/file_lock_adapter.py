"""File lock adapter providing cross-platform exclusive atomic locking.

AuthorityEffect: None.
"""

from __future__ import annotations

import contextlib
import os
import time
from pathlib import Path
from typing import Iterator


@contextlib.contextmanager
def exclusive_file_lock(lock_path: Path, timeout_seconds: float = 30.0) -> Iterator[None]:
    """Acquires an exclusive atomic file lock with fail-closed timeout."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + max(0.1, timeout_seconds)
    descriptor: int | None = None

    while True:
        try:
            descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            break
        except FileExistsError:
            if time.time() >= deadline:
                raise TimeoutError(f"Timed out after {timeout_seconds}s waiting for exclusive lock at {lock_path}")
            time.sleep(0.05)
        except PermissionError:
            if time.time() >= deadline:
                raise TimeoutError(f"Access denied after {timeout_seconds}s waiting for lock at {lock_path}")
            time.sleep(0.05)

    try:
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            lock_path.unlink(missing_ok=True)
        except (PermissionError, FileNotFoundError):
            pass
