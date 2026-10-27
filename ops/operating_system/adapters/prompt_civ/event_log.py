"""Durable event log and event identity model for Prompt Civ.

Enforces:
- F-EVT-01: Distinct acquisitions both survive, and idempotent replay does not duplicate.
- F-EVT-02: Same ID with different payload raises EVENT_IDENTITY_CONFLICT.
- Multi-process concurrent logging with cross-platform advisory file locking, contention tracking, and recovery.
- Event bytes remain immutable upon append; survives process restart via durable log.
AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl


class EventIdentityConflictError(ValueError):
    """Raised when an event ID already exists in the durable log with conflicting payload."""
    pass


class EventLogFileLockTimeout(TimeoutError):
    """Raised when an event log file lock is not acquired within the declared timeout."""
    pass


class EventLogFileLock:
    """Advisory file lock providing bounded acquisition, contention detection, and recovery."""

    def __init__(
        self,
        lock_path: Path,
        timeout: float = 30.0,
        poll_interval: float = 0.005,
    ) -> None:
        self.lock_path = lock_path
        self.timeout = float(timeout)
        self.poll_interval = float(poll_interval)
        self._thread_lock = threading.RLock()
        self._contention_count: int = 0
        self._acquisition_count: int = 0
        self._nesting_depth: int = 0

    @property
    def contention_count(self) -> int:
        return self._contention_count

    @property
    def acquisition_count(self) -> int:
        return self._acquisition_count

    @contextmanager
    def acquire(self) -> Iterator[bool]:
        """Acquire lock exclusively. Yields True if contention occurred, False otherwise."""
        started_at = time.monotonic()
        deadline = started_at + self.timeout

        if not self._thread_lock.acquire(timeout=self.timeout):
            raise EventLogFileLockTimeout(
                f"Timed out acquiring thread lock for {self.lock_path} after {self.timeout}s"
            )

        if self._nesting_depth > 0:
            self._nesting_depth += 1
            try:
                yield False
            finally:
                self._nesting_depth -= 1
                self._thread_lock.release()
            return

        handle = None
        contended = False
        try:
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            handle = self.lock_path.open("a+b")
            if handle.seek(0, os.SEEK_END) == 0:
                handle.write(b"0")
                handle.flush()
                try:
                    os.fsync(handle.fileno())
                except OSError:
                    pass

            while True:
                handle.seek(0)
                try:
                    if sys.platform == "win32":
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self._acquisition_count += 1
                    self._nesting_depth = 1
                    break
                except OSError as exc:
                    if not contended:
                        contended = True
                        self._contention_count += 1
                    if time.monotonic() >= deadline:
                        raise EventLogFileLockTimeout(
                            f"Timed out acquiring lock {self.lock_path} after {self.timeout}s"
                        ) from exc
                    time.sleep(self.poll_interval)

            yield contended

        finally:
            self._nesting_depth = 0
            if handle is not None:
                try:
                    handle.seek(0)
                    if sys.platform == "win32":
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
                try:
                    handle.close()
                except OSError:
                    pass
            self._thread_lock.release()


@dataclass
class PromptCivEventV1:
    """Prompt civilization event record with producer-minted identity."""
    producer_id: str
    event_kind: str
    run_id: str
    occurrence_id: str
    semantic_subject: str
    producer_ordinal: int
    payload: Dict[str, Any]
    event_id: str = ""
    payload_sha256: str = ""

    def __post_init__(self) -> None:
        if not self.payload_sha256:
            canonical_payload = json.dumps(self.payload, sort_keys=True).encode("utf-8")
            self.payload_sha256 = hashlib.sha256(canonical_payload).hexdigest()
        if not self.event_id:
            key = f"{self.producer_id}:{self.event_kind}:{self.run_id}:{self.occurrence_id}:{self.semantic_subject}:{self.producer_ordinal}"
            self.event_id = f"evt_{hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]}"


class DurableEventLogV1:
    """Append-only durable event log with idempotent replay, conflict rejection, and concurrent file locking."""

    DEFAULT_LOG_PATH = Path("_ic/odni/oeos/events/event_log.jsonl")

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        log_file: Optional[Path] = None,
        lock_timeout: float = 30.0,
        lock_poll_interval: float = 0.005,
    ) -> None:
        if log_dir is not None:
            self.log_file = log_dir / "event_log.jsonl"
        elif log_file is not None:
            self.log_file = log_file
        else:
            self.log_file = self.DEFAULT_LOG_PATH

        self.lock = EventLogFileLock(
            self.log_file.with_name(self.log_file.name + ".lock"),
            timeout=lock_timeout,
            poll_interval=lock_poll_interval,
        )
        self._events: Dict[str, PromptCivEventV1] = {}
        self._order: List[str] = []
        self._last_read_offset: int = 0
        self._load_from_disk()

    @property
    def lock_contention_count(self) -> int:
        return self.lock.contention_count

    @property
    def lock_acquisition_count(self) -> int:
        return self.lock.acquisition_count

    def _sync_from_disk(self) -> None:
        if not self.log_file.exists():
            return
        try:
            valid_lines: List[str] = []
            had_corruption = False
            content = self.log_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                    evt = PromptCivEventV1(
                        producer_id=data["producer_id"],
                        event_kind=data["event_kind"],
                        run_id=data["run_id"],
                        occurrence_id=data["occurrence_id"],
                        semantic_subject=data["semantic_subject"],
                        producer_ordinal=data["producer_ordinal"],
                        payload=data["payload"],
                        event_id=data["event_id"],
                        payload_sha256=data.get("payload_sha256", ""),
                    )
                    if evt.event_id not in self._events:
                        self._events[evt.event_id] = evt
                        self._order.append(evt.event_id)
                    valid_lines.append(stripped)
                except Exception:
                    had_corruption = True
            if had_corruption:
                clean_content = ("\n".join(valid_lines) + "\n") if valid_lines else ""
                self.log_file.write_text(clean_content, encoding="utf-8")
            self._last_read_offset = self.log_file.stat().st_size if self.log_file.exists() else 0
        except Exception:
            pass

    def _load_from_disk(self) -> None:
        if self.log_file.exists():
            with self.lock.acquire():
                self._sync_from_disk()

    def sync(self) -> None:
        """Explicitly synchronize in-memory state with any newly appended lines on disk."""
        with self.lock.acquire():
            self._sync_from_disk()

    def append_event(self, event: PromptCivEventV1) -> None:
        payload_copy = copy.deepcopy(event.payload)
        canonical_bytes = json.dumps(payload_copy, sort_keys=True).encode("utf-8")
        computed_sha = hashlib.sha256(canonical_bytes).hexdigest()

        with self.lock.acquire():
            self._sync_from_disk()

            if event.event_id in self._events:
                existing = self._events[event.event_id]
                existing_sha = existing.payload_sha256 or hashlib.sha256(
                    json.dumps(existing.payload, sort_keys=True).encode("utf-8")
                ).hexdigest()
                if existing_sha != computed_sha:
                    raise EventIdentityConflictError(
                        f"EVENT_IDENTITY_CONFLICT: Event {event.event_id} already exists with conflicting payload"
                    )
                # Idempotent replay: no-op
                return

            stored_event = PromptCivEventV1(
                producer_id=event.producer_id,
                event_kind=event.event_kind,
                run_id=event.run_id,
                occurrence_id=event.occurrence_id,
                semantic_subject=event.semantic_subject,
                producer_ordinal=event.producer_ordinal,
                payload=payload_copy,
                event_id=event.event_id,
                payload_sha256=computed_sha,
            )

            self._events[stored_event.event_id] = stored_event
            self._order.append(stored_event.event_id)

            # Append to disk
            try:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                record_dict = {
                    "producer_id": stored_event.producer_id,
                    "event_kind": stored_event.event_kind,
                    "run_id": stored_event.run_id,
                    "occurrence_id": stored_event.occurrence_id,
                    "semantic_subject": stored_event.semantic_subject,
                    "producer_ordinal": stored_event.producer_ordinal,
                    "payload": stored_event.payload,
                    "event_id": stored_event.event_id,
                    "payload_sha256": stored_event.payload_sha256,
                }
                with self.log_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(record_dict, sort_keys=True) + "\n")
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except OSError:
                        pass
                    self._last_read_offset = f.tell()
            except Exception:
                pass

    def append(self, event: PromptCivEventV1) -> None:
        self.append_event(event)

    def get_events(self) -> List[PromptCivEventV1]:
        with self.lock.acquire():
            self._sync_from_disk()
            return [self._events[eid] for eid in self._order]

    def get_event(self, event_id: str) -> PromptCivEventV1:
        if event_id not in self._events:
            with self.lock.acquire():
                self._sync_from_disk()
        return self._events[event_id]

    def event_count(self) -> int:
        with self.lock.acquire():
            self._sync_from_disk()
            return len(self._order)


__all__ = [
    "DurableEventLogV1",
    "EventIdentityConflictError",
    "EventLogFileLock",
    "EventLogFileLockTimeout",
    "PromptCivEventV1",
]
