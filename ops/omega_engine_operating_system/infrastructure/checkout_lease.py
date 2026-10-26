"""Fail-closed single-writer lease for an exact existing Git checkout.

The adapter measures identity, HEAD, ignored state-root policy, and cleanliness.
It contains no repair operation. AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Iterator
from urllib.parse import urlparse

from ..application import (
    CheckoutLeaseEvidenceV1,
    CheckoutLeaseModeV1,
    CheckoutLeaseRefusal,
)
from ..domain import TaskEnvelopeV1, canonical_json

_ALLOWED_GIT_OPERATIONS = frozenset({"check-ignore", "remote", "rev-parse", "status"})
_REPARSE_ATTRIBUTE = 0x400


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode()).hexdigest()


def _is_reparse(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    return path.is_symlink() or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE_ATTRIBUTE
    )


def _assert_plain_ancestors(path: Path, *, code: str = "CHECKOUT_LEASE_REPARSE_REFUSED") -> None:
    for candidate in reversed((path, *path.parents)):
        if _is_reparse(candidate):
            raise CheckoutLeaseRefusal(code, "lease path has a reparse ancestor")


def _normalize_remote(value: str) -> str | None:
    text = value.strip()
    if text.startswith("git@github.com:"):
        text = text.removeprefix("git@github.com:")
    else:
        parsed = urlparse(text)
        if parsed.scheme not in {"git", "https", "ssh"} or parsed.hostname != "github.com":
            return None
        text = parsed.path.lstrip("/")
    return text.removesuffix(".git") or None


class _CheckoutGuard:
    def __init__(
        self,
        manager: CheckoutLeaseManager,
        stream: IO[bytes] | None,
        repository: str,
        head_sha: str,
    ) -> None:
        self._manager = manager
        self._stream = stream
        self._released = False
        self._file_identity = os.fstat(stream.fileno()) if stream is not None else None
        mode = (
            CheckoutLeaseModeV1.MUTATION_EXCLUSIVE
            if stream is not None
            else CheckoutLeaseModeV1.READ_ONLY_NONCLAIM
        )
        self._evidence = CheckoutLeaseEvidenceV1(
            mode=mode,
            claimed=stream is not None,
            repository=repository,
            repository_head_sha=head_sha,
            lease_digest=_digest(
                {
                    "head": head_sha,
                    "lock_path": manager._lock_relative,
                    "mode": mode.value,
                    "repository": repository,
                }
            ),
        )

    @property
    def evidence(self) -> CheckoutLeaseEvidenceV1:
        return self._evidence

    def assert_held(self) -> None:
        if self._released:
            raise CheckoutLeaseRefusal("CHECKOUT_LEASE_LOST", "lease was released")
        if self._stream is not None and self._stream.closed:
            raise CheckoutLeaseRefusal("CHECKOUT_LEASE_LOST", "lease handle was closed")
        if self._stream is not None:
            current = os.fstat(self._stream.fileno())
            self._manager._assert_lease_paths(code="CHECKOUT_LEASE_LOST")
            lock_path = self._manager._lock_path
            if not lock_path.is_file() or _is_reparse(lock_path):
                raise CheckoutLeaseRefusal("CHECKOUT_LEASE_LOST", "lease path is unavailable")
            named = lock_path.stat()
            if (
                self._file_identity is None
                or (current.st_dev, current.st_ino)
                != (self._file_identity.st_dev, self._file_identity.st_ino)
                or (named.st_dev, named.st_ino)
                != (self._file_identity.st_dev, self._file_identity.st_ino)
            ):
                raise CheckoutLeaseRefusal("CHECKOUT_LEASE_LOST", "lease file identity changed")

    def release(self) -> None:
        if self._released:
            return
        self._released = True
        if self._stream is not None and not self._stream.closed:
            self._manager._unlock(self._stream)
            self._stream.close()


class CheckoutLeaseManager:
    """Measure, exclusively lock, remeasure, and never mutate a Git checkout."""

    fixture_only = False

    def __init__(
        self,
        repository_root: Path,
        *,
        state_root: Path,
        timeout_seconds: float = 0.0,
        git_executable: str = "git",
    ) -> None:
        if not isinstance(repository_root, Path) or not isinstance(state_root, Path):
            raise CheckoutLeaseRefusal("INVALID_CHECKOUT_PATH", "paths must be pathlib.Path")
        if type(timeout_seconds) not in {int, float} or not 0 <= timeout_seconds <= 30:
            raise CheckoutLeaseRefusal("INVALID_LEASE_TIMEOUT", "timeout is out of range")
        if type(git_executable) is not str or not git_executable:
            raise CheckoutLeaseRefusal("INVALID_GIT_EXECUTABLE", "git executable differs")
        self._repository_root = repository_root.absolute()
        self._state_root = state_root.absolute()
        canonical_root = self._repository_root / "_ic" / "odni" / "oeos_control"
        if self._state_root != canonical_root:
            raise CheckoutLeaseRefusal(
                "INVALID_OEOS_STATE_ROOT",
                "state root must be the canonical OEOS control root",
            )
        self._timeout_seconds = float(timeout_seconds)
        self._git_executable = git_executable
        self._lock_relative = "_ic/odni/migration/checkout-writer.lock"
        self._lock_path = self._repository_root / self._lock_relative

    @property
    def repository_root(self) -> Path:
        return self._repository_root

    @property
    def state_root(self) -> Path:
        return self._state_root

    def _assert_lease_paths(self, *, code: str = "CHECKOUT_LEASE_REPARSE_REFUSED") -> None:
        _assert_plain_ancestors(self._state_root, code=code)
        _assert_plain_ancestors(self._lock_path, code=code)

    def _verify_ignored_custody(self) -> None:
        state_relative = self._state_root.relative_to(self._repository_root).as_posix() + "/"
        for relative in (self._lock_relative, state_relative):
            self._git("check-ignore", "--quiet", "--", relative)

    def _git(self, operation: str, *arguments: str, allow_nonzero: bool = False) -> str:
        if operation not in _ALLOWED_GIT_OPERATIONS:
            raise CheckoutLeaseRefusal(
                "GIT_OPERATION_FORBIDDEN",
                "operation is outside the measurement allowlist",
            )
        environment = {
            key: os.environ[key]
            for key in (
                "HOME",
                "HOMEDRIVE",
                "HOMEPATH",
                "PATH",
                "PATHEXT",
                "SYSTEMROOT",
                "TEMP",
                "TMP",
                "USERPROFILE",
                "WINDIR",
            )
            if key in os.environ
        }
        environment.update(
            {
                "GIT_TERMINAL_PROMPT": "0",
                "LC_ALL": "C",
            }
        )
        command = [
            self._git_executable,
            "-c",
            "core.excludesFile=",
            "-C",
            str(self._repository_root),
            operation,
            *arguments,
        ]
        try:
            completed = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                shell=False,
                timeout=10,
                env=environment,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
            raise CheckoutLeaseRefusal("GIT_MEASUREMENT_UNAVAILABLE", type(exc).__name__) from exc
        if completed.returncode != 0 and not allow_nonzero:
            raise CheckoutLeaseRefusal(
                "GIT_MEASUREMENT_FAILED", f"{operation} exited {completed.returncode}"
            )
        try:
            return completed.stdout.decode("utf-8", errors="strict").strip()
        except UnicodeDecodeError as exc:
            raise CheckoutLeaseRefusal(
                "GIT_MEASUREMENT_INVALID", "Git output is not UTF-8"
            ) from exc

    def _verify_snapshot(self, repository: str, head_sha: str, *, require_clean: bool) -> None:
        if not self._repository_root.is_dir() or _is_reparse(self._repository_root):
            raise CheckoutLeaseRefusal(
                "CHECKOUT_ROOT_INVALID",
                "repository root is unavailable or reparse-backed",
            )
        self._assert_lease_paths()
        observed_root = Path(self._git("rev-parse", "--show-toplevel")).absolute()
        if observed_root != self._repository_root:
            raise CheckoutLeaseRefusal(
                "CHECKOUT_IDENTITY_MISMATCH",
                "Git top-level differs from configured root",
            )
        remote = _normalize_remote(self._git("remote", "get-url", "origin"))
        if remote != repository:
            raise CheckoutLeaseRefusal(
                "CHECKOUT_IDENTITY_MISMATCH", "origin does not name the task repository"
            )
        observed_head = self._git("rev-parse", "--verify", "HEAD")
        if observed_head != head_sha:
            raise CheckoutLeaseRefusal(
                "CHECKOUT_HEAD_MISMATCH", "checkout HEAD differs from the task snapshot"
            )
        self._verify_ignored_custody()
        if require_clean:
            porcelain = self._git("status", "--porcelain=v1", "--untracked-files=all")
            if porcelain:
                raise CheckoutLeaseRefusal(
                    "CHECKOUT_DIRTY", "mutating task requires a clean checkout"
                )

    def verify_configuration(self) -> None:
        if not self._repository_root.is_dir() or _is_reparse(self._repository_root):
            raise CheckoutLeaseRefusal(
                "CHECKOUT_ROOT_INVALID",
                "repository root is unavailable or reparse-backed",
            )
        self._assert_lease_paths()
        observed_root = Path(self._git("rev-parse", "--show-toplevel")).absolute()
        if observed_root != self._repository_root:
            raise CheckoutLeaseRefusal(
                "CHECKOUT_IDENTITY_MISMATCH",
                "Git top-level differs from configured root",
            )
        self._verify_ignored_custody()

    @staticmethod
    def _try_lock(stream: IO[bytes]) -> bool:
        stream.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return False
        return True

    @staticmethod
    def _unlock(stream: IO[bytes]) -> None:
        try:
            stream.seek(0)
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass

    def _acquire_stream(self) -> IO[bytes]:
        self._assert_lease_paths()
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._assert_lease_paths()
        stream = self._lock_path.open("a+b")
        try:
            self._assert_lease_paths()
            opened = os.fstat(stream.fileno())
            named = self._lock_path.stat()
            if (opened.st_dev, opened.st_ino) != (named.st_dev, named.st_ino):
                raise CheckoutLeaseRefusal(
                    "CHECKOUT_LEASE_REPARSE_REFUSED",
                    "lease file identity changed during acquisition",
                )
        except BaseException:
            stream.close()
            raise
        if stream.seek(0, os.SEEK_END) == 0:
            stream.write(b"\x00")
            stream.flush()
            os.fsync(stream.fileno())
        deadline = time.monotonic() + self._timeout_seconds
        while not self._try_lock(stream):
            if time.monotonic() >= deadline:
                stream.close()
                raise CheckoutLeaseRefusal(
                    "CHECKOUT_LEASE_BUSY", "another mutating worker owns the checkout"
                )
            time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))
        return stream

    @contextmanager
    def claim(self, envelope: TaskEnvelopeV1) -> Iterator[_CheckoutGuard]:
        if type(envelope) is not TaskEnvelopeV1:
            raise CheckoutLeaseRefusal("INVALID_TASK_ENVELOPE", "exact TaskEnvelopeV1 required")
        require_clean = envelope.action_limits.mutating
        self._verify_snapshot(
            envelope.repository,
            envelope.repository_head_sha,
            require_clean=require_clean,
        )
        if not require_clean:
            guard = _CheckoutGuard(self, None, envelope.repository, envelope.repository_head_sha)
            try:
                yield guard
            finally:
                guard.release()
            return
        with self._claim_exclusive(
            envelope.repository, envelope.repository_head_sha, require_clean=True
        ) as guard:
            yield guard

    @contextmanager
    def _claim_exclusive(
        self, repository: str, head_sha: str, *, require_clean: bool
    ) -> Iterator[_CheckoutGuard]:
        stream = self._acquire_stream()
        guard = _CheckoutGuard(self, stream, repository, head_sha)
        try:
            self._verify_snapshot(repository, head_sha, require_clean=require_clean)
            guard.assert_held()
            yield guard
        finally:
            guard.release()

    @contextmanager
    def claim_migration(self, repository: str, head_sha: str) -> Iterator[_CheckoutGuard]:
        """Exclude existing writers while copying ignored custody; never clean/repair.

        Updated task and migration workers share the canonical control lock.
        DEV cutover requires old workers to be quiescent. Dirty working bytes are
        permitted here; task mutation claims still require cleanliness.
        """
        if type(repository) is not str or not repository or repository.strip() != repository:
            raise CheckoutLeaseRefusal(
                "INVALID_MIGRATION_SNAPSHOT", "repository must be an exact nonempty name"
            )
        if (
            type(head_sha) is not str
            or len(head_sha) != 40
            or any(character not in "0123456789abcdef" for character in head_sha)
        ):
            raise CheckoutLeaseRefusal(
                "INVALID_MIGRATION_SNAPSHOT", "HEAD must be a full lowercase Git SHA"
            )
        self._verify_snapshot(repository, head_sha, require_clean=False)
        with self._claim_exclusive(repository, head_sha, require_clean=False) as guard:
            yield guard

    def diagnostic(self) -> dict[str, object]:
        return {
            "fixture_only": False,
            "mode": "single-writer",
            "status": "HEALTHY",
        }


__all__ = ["CheckoutLeaseManager"]
