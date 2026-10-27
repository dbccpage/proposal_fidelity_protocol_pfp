"""Idempotent receipt delivery with a separately retained authenticated tip.

The operator supplies a stable ledger identity, an external tip path and a
secret key. A signed pending intent permits exact process-crash recovery, never
repinning from the database alone. The tip directory/key need independent OS
custody; rolling back both stores or stealing the key is outside this boundary.
AuthorityEffect: None. Authentic custody does not certify an event's truth.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import stat
import tempfile
from pathlib import Path

from operations.domain.rop.result import Err, Ok
from adversary.stage.infrastructure.file_lock import AdvisoryFileLock

from ...domain.errors.domain_errors import DomainInvariantError
from .receipt_ledger import (
    GENESIS_DIGEST,
    LedgerError,
    ReceiptLedger,
    canonical_payload,
    entry_digest,
)
from .sqlite_inbox_subscriber import SqliteInboxSubscriber, _envelope

PROFILE = "core.oewas.authenticated-ledger-tip.v1"


def _plain_path(path: Path) -> None:
    if any(part in {".."} or part.endswith((".", " ")) for part in path.parts[1:]):
        raise LedgerError("TIP_PATH_UNSAFE", str(path))
    for member in (path, *path.parents):
        if member.exists() or member.is_symlink():
            info = member.lstat()
            if (stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400
                    or (stat.S_ISREG(info.st_mode) and info.st_nlink != 1)):
                raise LedgerError("TIP_PATH_UNSAFE", str(member))


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise LedgerError("TIP_INVALID", "duplicate field")
        result[key] = value
    return result


def read_tip_key(path: Path) -> bytes:
    """Read the explicitly configured operator key without following aliases."""
    path = Path(os.path.abspath(path))
    _plain_path(path)
    key = path.read_bytes()
    _plain_path(path)
    if len(key) < 32:
        raise LedgerError("TIP_TRUST_REQUIRED", "operator key must contain at least 32 bytes")
    return key


def validate_database_paths(db_path: str) -> None:
    """Check SQLite's writable sidecars before its first connection is opened."""
    if db_path != ":memory:":
        database = Path(os.path.abspath(db_path))
        for suffix in ("", "-wal", "-shm", "-journal"):
            _plain_path(Path(str(database) + suffix))


def validate_delivery_paths(db_path: str, tip_path: Path) -> tuple[Path, Path, Path, Path]:
    """Validate all derived custody targets without opening or creating files."""
    if not db_path or db_path == ":memory:":
        raise LedgerError("TIP_FILE_DB_REQUIRED", "delivery requires a file database")
    tip = Path(os.path.abspath(tip_path))
    pending, lock = tip.with_name(tip.name + ".pending"), tip.with_name(tip.name + ".lock")
    database = Path(os.path.abspath(db_path))
    database_files = tuple(Path(str(database) + suffix) for suffix in ("", "-wal", "-shm", "-journal"))
    if {tip, pending, lock} & set(database_files):
        raise LedgerError("TIP_PATH_UNSAFE", "tip, pending intent and lock must be separate from SQLite files")
    validate_database_paths(db_path)
    for path in (tip, pending, lock, *database_files):
        _plain_path(path)
        if path.exists() and not path.is_file():
            raise LedgerError("TIP_PATH_UNSAFE", "expected a regular file: " + str(path))
    return tip, pending, lock, database


class AnchoredLedgerSubscriber:
    """Existing SQLite inbox owns deduplication and the ledger effect transaction."""

    def __init__(self, db_path: str, tip_path: Path, key: bytes, ledger_id: str):
        if type(key) is not bytes or len(key) < 32 or type(ledger_id) is not str or not ledger_id.strip():
            raise LedgerError("TIP_TRUST_REQUIRED", "explicit identity and >=32-byte operator key required")
        self.path, self.pending, self.lock_path, self._db_path = validate_delivery_paths(db_path, tip_path)
        self.key, self.ledger_id = key, ledger_id
        self._check_paths()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger = ReceiptLedger(db_path)
        try:
            self.inbox = SqliteInboxSubscriber(db_path, "receipt-ledger:" + ledger_id, self._effect)
            with AdvisoryFileLock(self.lock_path, timeout=10):
                self._recover()
        except BaseException:
            if hasattr(self, "inbox"):
                self.inbox.close()
            self.ledger.close()
            raise

    def close(self):
        self.inbox.close()
        self.ledger.close()

    def _check_paths(self):
        validate_database_paths(str(self._db_path))
        for path in (self.path, self.pending, self.lock_path):
            _plain_path(path)

    def _signature(self, body):
        return hmac.new(self.key, PROFILE.encode() + b"\0" + canonical_payload(body).encode(), hashlib.sha256).hexdigest()

    def _read(self, path):
        self._check_paths()
        data = json.loads(path.read_bytes(), object_pairs_hook=_unique)
        if (type(data) is not dict or set(data) != {"body", "signature"}
                or type(data["body"]) is not dict or type(data["signature"]) is not str
                or not hmac.compare_digest(data["signature"], self._signature(data["body"]))):
            raise LedgerError("TIP_AUTHENTICATION_FAILED", str(path))
        body = data["body"]
        if body.get("profile") != PROFILE or body.get("ledger_id") != self.ledger_id:
            raise LedgerError("TIP_BINDING_MISMATCH", str(path))
        return body

    def _write(self, path, body):
        self._check_paths()
        raw = canonical_payload({"body": body, "signature": self._signature(body)}).encode("utf-8")
        fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            self._check_paths()
            os.replace(temporary, path)
            if os.name != "nt":
                directory = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _tip_body(self, sequence, tip):
        return dict(profile=PROFILE, ledger_id=self.ledger_id, sequence=sequence, tip=tip)

    def _require_tip(self, body):
        if (type(body.get("sequence")) is not int or body["sequence"] != len(self.ledger)
                or body.get("tip") != self.ledger.tip()
                or (len(self.ledger) and not self.ledger.verify().is_intact)):
            raise LedgerError("TIP_INCOMPLETE", "database differs from separately authenticated tip")

    def _effect(self, connection, event):
        row = connection.execute("SELECT sequence,entry_digest FROM receipt_ledger_v1 ORDER BY sequence DESC LIMIT 1").fetchone()
        sequence, previous = (1, GENESIS_DIGEST) if row is None else (row[0] + 1, row[1])
        text = canonical_payload(event)
        connection.execute("INSERT INTO receipt_ledger_v1 VALUES (?,?,?,?)",
                           (sequence, text, previous, entry_digest(sequence, previous, text)))

    def _recover(self):
        self._check_paths()
        if not self.path.exists():
            if len(self.ledger):
                raise LedgerError("TIP_MISSING", "refuse to repin a populated database")
            self._write(self.path, self._tip_body(0, GENESIS_DIGEST))
        anchor = self._read(self.path)
        if not self.pending.exists():
            self._require_tip(anchor)
            return
        intent = self._read(self.pending)
        event = intent["event"]
        _event_id, event, _digest = _envelope(event)
        previous, next_tip = intent["previous"], intent["next"]
        if (type(previous.get("sequence")) is not int
                or next_tip != self._tip_body(previous["sequence"] + 1,
                    entry_digest(previous["sequence"] + 1, previous["tip"], canonical_payload(event)))
                or anchor not in (previous, next_tip)):
            raise LedgerError("TIP_INTENT_MISMATCH", "foreign or invalid recovery intent")
        if self.ledger.tip() == previous["tip"]:
            self._require_tip(previous)
            outcome = self.inbox(event)
            if outcome.is_err:
                raise LedgerError("TIP_RECOVERY_FAILED", str(outcome.unwrap_err()))
        self._require_tip(next_tip)
        self._write(self.path, next_tip)
        self.pending.unlink()

    def __call__(self, message):
        try:
            event_id, event, _digest = _envelope(message)
            with AdvisoryFileLock(self.lock_path, timeout=10):
                self._recover()
                # Retrying after an acknowledgement crash must not append twice.
                for entry in self.ledger.entries():
                    prior = json.loads(entry.payload)
                    if prior.get("event_id") == event_id:
                        if prior != event:
                            raise LedgerError("INBOX_EVENT_CONFLICT", event_id)
                        return Ok(None)
                previous = self._read(self.path)
                following = self._tip_body(len(self.ledger) + 1,
                    entry_digest(len(self.ledger) + 1, self.ledger.tip(), canonical_payload(event)))
                self._write(self.pending, dict(profile=PROFILE, ledger_id=self.ledger_id,
                    previous=previous, next=following, event=event))
                result = self.inbox(event)
                if result.is_err:
                    return result
                self._require_tip(following)
                self._write(self.path, following)
                self.pending.unlink()
                return Ok(None)
        except (LedgerError, OSError, ValueError, TypeError, KeyError) as error:
            return Err(DomainInvariantError(code=getattr(error, "code", "TIP_DELIVERY_FAILED"), message=str(error)))
