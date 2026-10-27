"""Hash-chained genealogy persistence for the stage infrastructure layer.

The domain owns :class:`GenealogyEntryV1`; this module owns the file format,
crash-recovery policy, and the adapter that connects those effects to the
application port.  Filesystem, lock, and codec collaborators are injectable so
the adapter can be tested without patching process-global functions.
"""

from __future__ import annotations

import hashlib
import os
import threading
from collections.abc import Callable
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from governance.domain.intelligence_community import canonical_intelligence_route
from operations.domain.rop.result import Err, Ok, Refusal, Result

from ..domain.canonical import canonical_json_bytes, strict_json_loads
from ..domain.genealogy import GenealogyEntryV1
from ..domain.ports import GenealogyStorePort
from .file_lock import AdvisoryFileLock

MAX_GENEALOGY_RECORD_BYTES = 4 * 1024 * 1024
_SEALED_FIELDS = frozenset(
    {"sequence", "parent_sha256", "payload", "record_sha256"}
)


class GenealogyFileSystem(Protocol):
    """Minimal filesystem capability required by the genealogy adapter."""

    def size(self, path: Path) -> int: ...

    def read_bytes(self, path: Path) -> bytes: ...

    def truncate(self, path: Path, size: int) -> None: ...

    def append(self, path: Path, body: bytes) -> int: ...


class LocalGenealogyFileSystem:
    """Production filesystem implementation with durable truncation and append."""

    def size(self, path: Path) -> int:
        return path.stat().st_size if path.exists() else 0

    def read_bytes(self, path: Path) -> bytes:
        return path.read_bytes() if path.exists() else b""

    def truncate(self, path: Path, size: int) -> None:
        with path.open("r+b") as stream:
            stream.truncate(size)
            stream.flush()
            os.fsync(stream.fileno())

    def append(self, path: Path, body: bytes) -> int:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0),
            0o600,
        )
        try:
            if os.write(descriptor, body) != len(body):
                raise OSError("short genealogy append")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return self.size(path)


@dataclass(frozen=True, slots=True)
class DecodedGenealogyRecord:
    """One verified record and its resulting hash-chain cursor."""

    entry: GenealogyEntryV1
    head_sha256: str
    next_sequence: int


class GenealogyRecordCodec:
    """Canonical JSON and SHA-256 codec for legacy and sealed genealogy rows."""

    @staticmethod
    def is_sealed(payload: dict[str, Any]) -> bool:
        return bool(_SEALED_FIELDS.intersection(payload))

    def parse_json(self, raw_line: bytes, line_number: int) -> dict[str, Any]:
        try:
            payload = strict_json_loads(raw_line)
        except Exception as exc:
            raise ValueError(
                f"unparseable genealogy record at line {line_number}"
            ) from exc
        if not isinstance(payload, dict):
            raise ValueError(f"unparseable genealogy record at line {line_number}")
        return payload

    def decode(
        self,
        payload: dict[str, Any],
        raw_line: bytes,
        *,
        expected_sequence: int,
        expected_parent: str | None,
    ) -> DecodedGenealogyRecord:
        if not self.is_sealed(payload):
            entry = GenealogyEntryV1.from_dict(payload)
            return DecodedGenealogyRecord(
                entry=entry,
                head_sha256=hashlib.sha256(raw_line).hexdigest(),
                next_sequence=expected_sequence + 1,
            )
        if set(payload) != _SEALED_FIELDS:
            missing = _SEALED_FIELDS - set(payload)
            unknown = set(payload) - _SEALED_FIELDS
            details = []
            if missing:
                details.append(f"missing fields: {', '.join(sorted(missing))}")
            if unknown:
                details.append(f"unknown fields: {', '.join(sorted(unknown))}")
            raise ValueError(f"invalid sealed genealogy record ({'; '.join(details)})")
        return self._decode_sealed(payload, expected_sequence, expected_parent)

    def encode(
        self,
        entry: GenealogyEntryV1,
        *,
        sequence: int,
        parent_sha256: str | None,
    ) -> tuple[bytes, str]:
        payload = entry.to_dict()
        material = canonical_json_bytes(
            {
                "sequence": sequence,
                "parent_sha256": parent_sha256,
                "payload": payload,
            }
        )
        record_sha256 = hashlib.sha256(material).hexdigest()
        envelope = {
            "sequence": sequence,
            "parent_sha256": parent_sha256,
            "payload": payload,
            "record_sha256": record_sha256,
        }
        body = canonical_json_bytes(envelope) + b"\n"
        if len(body) > MAX_GENEALOGY_RECORD_BYTES:
            raise ValueError("genealogy record exceeds 4 MiB")
        return body, record_sha256

    def _decode_sealed(
        self,
        payload: dict[str, Any],
        expected_sequence: int,
        expected_parent: str | None,
    ) -> DecodedGenealogyRecord:
        try:
            sequence = payload["sequence"]
            parent_sha256 = payload.get("parent_sha256")
            record_sha256 = payload["record_sha256"]
            inner_payload = payload["payload"]
        except KeyError as exc:
            raise ValueError("sealed genealogy record is missing a required field") from exc
        if type(sequence) is not int or sequence < 0:
            raise ValueError("genealogy sequence must be a non-negative exact integer")
        if type(record_sha256) is not str or len(record_sha256) != 64:
            raise ValueError("genealogy record digest must be 64 lowercase hex characters")
        if any(character not in "0123456789abcdef" for character in record_sha256):
            raise ValueError("genealogy record digest must be 64 lowercase hex characters")
        if parent_sha256 is not None and (
            type(parent_sha256) is not str
            or len(parent_sha256) != 64
            or any(character not in "0123456789abcdef" for character in parent_sha256)
        ):
            raise ValueError("genealogy parent digest must be null or 64 lowercase hex characters")
        if sequence != expected_sequence:
            raise ValueError(
                f"genealogy sequence gap: expected {expected_sequence}, got {sequence}"
            )
        if parent_sha256 != expected_parent:
            raise ValueError(f"genealogy hash chain broken at seq {sequence}")
        material = canonical_json_bytes(
            {
                "sequence": sequence,
                "parent_sha256": parent_sha256,
                "payload": inner_payload,
            }
        )
        recomputed = hashlib.sha256(material).hexdigest()
        if recomputed != record_sha256:
            raise ValueError(f"genealogy record digest mismatch at seq {sequence}")
        return DecodedGenealogyRecord(
            entry=GenealogyEntryV1.from_dict(inner_payload),
            head_sha256=record_sha256,
            next_sequence=expected_sequence + 1,
        )


@dataclass(frozen=True, slots=True)
class GenealogyRecovery:
    """Explicit evidence that an unacknowledged tail was discarded."""

    reason: str
    original_size: int
    recovered_size: int


@dataclass(frozen=True, slots=True)
class GenealogyReplay:
    """Verified ledger state produced by replaying acknowledged records."""

    entries: tuple[GenealogyEntryV1, ...]
    head_sha256: str | None
    next_sequence: int
    acknowledged_size: int
    recovery: GenealogyRecovery | None = None


@dataclass(slots=True)
class _ReplayState:
    entries: list[GenealogyEntryV1] = field(default_factory=list)
    by_child: dict[str, GenealogyEntryV1] = field(default_factory=dict)
    head_sha256: str | None = None
    next_sequence: int = 0
    acknowledged_size: int = 0


LockFactory = Callable[[Path, float], AbstractContextManager[Any]]


def _advisory_lock(lock_path: Path, timeout: float) -> AbstractContextManager[Any]:
    return AdvisoryFileLock(lock_path, timeout=timeout)


def _is_unterminated_tail(raw_line: bytes, is_last: bool) -> bool:
    return is_last and not raw_line.endswith(b"\n")


def _accept_entry(state: _ReplayState, decoded: DecodedGenealogyRecord) -> None:
    prior = state.by_child.get(decoded.entry.child_run_key)
    if prior is not None and prior != decoded.entry:
        raise ValueError(
            f"conflicting genealogy for child {decoded.entry.child_run_key}"
        )
    state.by_child[decoded.entry.child_run_key] = decoded.entry
    state.entries.append(decoded.entry)
    state.head_sha256 = decoded.head_sha256
    state.next_sequence = decoded.next_sequence


def _parse_replay_line(
    raw_line: bytes,
    *,
    line_number: int,
    is_last: bool,
    codec: GenealogyRecordCodec,
) -> tuple[dict[str, Any] | None, str | None]:
    if _is_unterminated_tail(raw_line, is_last):
        return None, "unterminated final record"
    stripped = raw_line.strip()
    if not stripped:
        raise ValueError(f"blank genealogy record at line {line_number}")
    return codec.parse_json(stripped, line_number), None


def replay_genealogy(
    raw_bytes: bytes,
    codec: GenealogyRecordCodec,
) -> GenealogyReplay:
    """Replay a ledger and identify the only recoverable condition: a torn tail."""
    state = _ReplayState()
    lines = raw_bytes.splitlines(keepends=True)
    recovery_reason: str | None = None
    for index, raw_line in enumerate(lines):
        is_last = index == len(lines) - 1
        payload, recovery_reason = _parse_replay_line(
            raw_line,
            line_number=index + 1,
            is_last=is_last,
            codec=codec,
        )
        if payload is None:
            break
        decoded = codec.decode(
            payload,
            raw_line.strip(),
            expected_sequence=state.next_sequence,
            expected_parent=state.head_sha256,
        )
        _accept_entry(state, decoded)
        state.acknowledged_size += len(raw_line)
    recovery = None
    if recovery_reason is not None:
        recovery = GenealogyRecovery(
            reason=recovery_reason,
            original_size=len(raw_bytes),
            recovered_size=state.acknowledged_size,
        )
    return GenealogyReplay(
        entries=tuple(state.entries),
        head_sha256=state.head_sha256,
        next_sequence=state.next_sequence,
        acknowledged_size=state.acknowledged_size,
        recovery=recovery,
    )


class FileGenealogyAdapter(GenealogyStorePort):
    """Parent-child lineage store with verified replay and explicit recovery state."""

    def __init__(
        self,
        genealogy_file: str | Path | None = None,
        *,
        filesystem: GenealogyFileSystem | None = None,
        lock_factory: LockFactory | None = None,
        codec: GenealogyRecordCodec | None = None,
    ) -> None:
        self.genealogy_file = Path(
            genealogy_file
            or canonical_intelligence_route("_intelligence/_stage/prompt_genealogy.jsonl")
        )
        self._filesystem = filesystem or LocalGenealogyFileSystem()
        self._lock_factory = lock_factory or _advisory_lock
        self._codec = codec or GenealogyRecordCodec()
        self.entries: list[GenealogyEntryV1] = []
        self._head_sha256: str | None = None
        self._next_sequence = 0
        self._loaded = False
        self._lock = threading.RLock()
        self._last_file_size = -1
        self.last_recovery: GenealogyRecovery | None = None

    @contextmanager
    def _file_lock(self, timeout: float = 15.0):
        lock_path = self.genealogy_file.with_name(f"{self.genealogy_file.name}.lock")
        with self._lock_factory(lock_path, timeout):
            yield

    def _load_entries(self, force_reload: bool = False) -> None:
        current_size = self._filesystem.size(self.genealogy_file)
        if self._loaded and not force_reload and current_size == self._last_file_size:
            return
        raw_bytes = self._filesystem.read_bytes(self.genealogy_file)
        if type(raw_bytes) is not bytes:
            raise TypeError("genealogy filesystem must return exact bytes")
        if len(raw_bytes) != current_size:
            raise OSError("genealogy file changed while being read")
        replay = replay_genealogy(raw_bytes, self._codec)
        if replay.recovery is not None:
            self._filesystem.truncate(
                self.genealogy_file, replay.recovery.recovered_size
            )
        self.entries = list(replay.entries)
        self._head_sha256 = replay.head_sha256
        self._next_sequence = replay.next_sequence
        self._loaded = True
        self._last_file_size = replay.acknowledged_size
        self.last_recovery = replay.recovery

    def record_lineage(self, entry: GenealogyEntryV1) -> Result[None, Refusal]:
        try:
            if type(entry) is not GenealogyEntryV1:
                raise TypeError("entry must be an exact GenealogyEntryV1")
            with self._lock, self._file_lock():
                self._load_entries(force_reload=True)
                prior = next(
                    (
                        item
                        for item in self.entries
                        if item.child_run_key == entry.child_run_key
                    ),
                    None,
                )
                if prior is not None:
                    if prior != entry:
                        raise ValueError(
                            f"conflicting genealogy for child {entry.child_run_key}"
                        )
                    return Ok(None)
                body, record_sha256 = self._codec.encode(
                    entry,
                    sequence=self._next_sequence,
                    parent_sha256=self._head_sha256,
                )
                expected_size = self._last_file_size + len(body)
                appended_size = self._filesystem.append(self.genealogy_file, body)
                if type(appended_size) is not int or appended_size != expected_size:
                    raise OSError(
                        "genealogy append did not report the expected durable size"
                    )
                self._last_file_size = appended_size
                self.entries.append(entry)
                self._head_sha256 = record_sha256
                self._next_sequence += 1
            return Ok(None)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="GENEALOGY_RECORD_FAILED",
                    message=f"Failed to record lineage: {exc}",
                    locus=(
                        "adversary.stage.infrastructure.genealogy_store."
                        "FileGenealogyAdapter"
                    ),
                )
            )

    def get_lineage(
        self, child_run_key: str
    ) -> Result[GenealogyEntryV1 | None, Refusal]:
        try:
            if type(child_run_key) is not str:
                raise TypeError("child_run_key must be an exact string")
            with self._lock, self._file_lock():
                self._load_entries(force_reload=True)
                entry = next(
                    (
                        item
                        for item in reversed(self.entries)
                        if item.child_run_key == child_run_key
                    ),
                    None,
                )
                return Ok(entry)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="GENEALOGY_LOAD_FAILED",
                    message=f"Failed to load lineage: {exc}",
                    locus=(
                        "adversary.stage.infrastructure.genealogy_store."
                        "FileGenealogyAdapter"
                    ),
                )
            )


__all__ = [
    "FileGenealogyAdapter",
    "GenealogyFileSystem",
    "GenealogyRecordCodec",
    "GenealogyRecovery",
    "GenealogyReplay",
    "LocalGenealogyFileSystem",
    "MAX_GENEALOGY_RECORD_BYTES",
    "replay_genealogy",
]
