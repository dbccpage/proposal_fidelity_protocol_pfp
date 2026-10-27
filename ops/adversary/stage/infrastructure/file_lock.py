"""Small cross-platform advisory file lock with bounded acquisition.

The implementation is dependency-free so evidence gates and production
adapters use the same lock semantics in a fresh Python environment.
"""

from __future__ import annotations

import errno
import os
import threading
import time
from pathlib import Path
from typing import BinaryIO

try:
    import msvcrt
except ImportError:  # pragma: no cover - platform branch
    msvcrt = None

try:
    import fcntl
except ImportError:  # pragma: no cover - platform branch
    fcntl = None


class FileLockTimeout(TimeoutError):
    """Raised when an advisory lock is not acquired before its deadline."""


class AdvisoryFileLock:
    """Lock the first byte of a named file using the host OS primitive."""

    def __init__(
        self,
        lock_file: str | os.PathLike[str],
        timeout: float = -1.0,
        poll_interval: float = 0.02,
    ) -> None:
        if type(timeout) not in (int, float) or timeout < -1:
            raise ValueError("timeout must be -1 or a non-negative number")
        if type(poll_interval) not in (int, float) or poll_interval <= 0:
            raise ValueError("poll_interval must be a positive number")
        self.path = Path(lock_file)
        self.timeout = float(timeout)
        self.poll_interval = float(poll_interval)
        self._handle: BinaryIO | None = None
        self._thread_lock = threading.RLock()
        self._depth = 0

    def acquire(self) -> AdvisoryFileLock:
        """Acquire the lock, waiting only up to the configured timeout."""
        started_at = time.monotonic()
        if self.timeout < 0:
            self._thread_lock.acquire()
        elif not self._thread_lock.acquire(timeout=self.timeout):
            raise FileLockTimeout(f"timed out acquiring lock {self.path}")
        if self._handle is not None:
            self._depth += 1
            return self
        handle: BinaryIO | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            handle = self.path.open("a+b")
            if handle.seek(0, os.SEEK_END) == 0:
                handle.write(b"0")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError:
            if handle is not None:
                handle.close()
            self._thread_lock.release()
            raise
        if msvcrt is None and fcntl is None:  # pragma: no cover - unsupported host
            handle.close()
            self._thread_lock.release()
            raise RuntimeError("no supported advisory file-lock primitive")

        deadline = None if self.timeout < 0 else started_at + self.timeout
        while True:
            try:
                handle.seek(0)
                if msvcrt is not None:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                elif fcntl is not None:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._handle = handle
                self._depth = 1
                return self
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN):
                    handle.close()
                    self._thread_lock.release()
                    raise
                if deadline is not None and time.monotonic() >= deadline:
                    handle.close()
                    self._thread_lock.release()
                    raise FileLockTimeout(f"timed out acquiring lock {self.path}") from exc
                time.sleep(self.poll_interval)

    def release(self) -> None:
        """Release a held lock; repeated releases are harmless."""
        handle = self._handle
        if handle is None:
            return
        if self._depth > 1:
            self._depth -= 1
            self._thread_lock.release()
            return
        try:
            handle.seek(0)
            if msvcrt is not None:
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            elif fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._handle = None
            self._depth = 0
            handle.close()
            self._thread_lock.release()

    def __enter__(self) -> AdvisoryFileLock:
        return self.acquire()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.release()


__all__ = ["AdvisoryFileLock", "FileLockTimeout"]
