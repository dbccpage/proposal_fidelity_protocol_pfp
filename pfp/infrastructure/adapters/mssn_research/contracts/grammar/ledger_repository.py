"""Confined filesystem adapter for epistemic quarantine ledgers."""

from __future__ import annotations

import os
import re
from hashlib import sha256
from pathlib import Path

from omega_engine_pfp.domain.mssn_research.grammar.entities import EpistemicQuarantineLedger
from omega_engine_pfp.domain.mssn_research.grammar.errors import (
    GrammarDomainError,
    LedgerSerializationError,
)
from omega_engine_pfp.domain.mssn_research.packets.value_objects import RefusalCode
from omega_engine_pfp.domain.mssn_research.shared_kernel.result import Err, Ok, Refusal, Result

from .ledger_codec import deserialize_ledger_from_jsonl, serialize_ledger_to_jsonl

_SAFE_LEDGER_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_MAX_LEDGER_BYTES = 16 * 1024 * 1024


class EpistemicQuarantineRepository:
    """Filesystem repository with confined names and atomic replacement."""

    def __init__(self, base_directory: str | Path) -> None:
        self.base_directory = Path(base_directory).resolve()
        self.base_directory.mkdir(parents=True, exist_ok=True)

    def _file_path(self, ledger_id: str) -> Result[Path, GrammarDomainError]:
        if (not isinstance(ledger_id, str) or not ledger_id or len(ledger_id) > 256
                or any(ord(character) < 32 for character in ledger_id)):
            return Refusal(_serialization_error(
                "Ledger id must be non-empty, at most 256 characters, and contain no control characters"
            ))
        filename = ledger_id if _SAFE_LEDGER_ID.fullmatch(ledger_id) else sha256(
            ledger_id.encode("utf-8")
        ).hexdigest()
        candidate = (self.base_directory / f"{filename}.jsonl").resolve()
        if candidate.parent != self.base_directory:
            return Refusal(_serialization_error("Ledger path escapes configured repository directory"))
        return Ok(candidate)

    def save(self, ledger: EpistemicQuarantineLedger) -> Result[Path, GrammarDomainError]:
        """Atomically save a ledger after validating its identifier."""
        path_result = self._file_path(ledger.ledger_id)
        if path_result.is_err():
            return path_result
        target_path = path_result.unwrap()
        payload = serialize_ledger_to_jsonl(ledger).encode("utf-8")
        if len(payload) > _MAX_LEDGER_BYTES:
            return Refusal(_serialization_error("Serialized ledger exceeds 16 MiB persistence limit"))
        tmp_path = target_path.with_suffix(".tmp")
        try:
            tmp_path.write_bytes(payload)
            os.replace(tmp_path, target_path)
        except OSError as exc:
            return Err(_serialization_error(f"Failed to write ledger file to disk: {exc}"))
        return Ok(target_path)

    def load(self, ledger_id: str) -> Result[EpistemicQuarantineLedger, GrammarDomainError]:
        """Load a ledger by its confined identifier."""
        path_result = self._file_path(ledger_id)
        if path_result.is_err():
            return path_result
        return self.load_from_path(path_result.unwrap())

    def load_from_path(self, path: str | Path) -> Result[EpistemicQuarantineLedger, GrammarDomainError]:
        """Load a ledger only when the resolved path stays inside this repository."""
        candidate = Path(path).resolve()
        if candidate.parent != self.base_directory:
            return Refusal(_serialization_error("Ledger path escapes configured repository directory"))
        if not candidate.is_file():
            return Refusal(LedgerSerializationError(
                code=RefusalCode.UNDECLARED_REFERENCE,
                message=f"Ledger file does not exist: {candidate}",
            ))
        try:
            if candidate.stat().st_size > _MAX_LEDGER_BYTES:
                return Refusal(_serialization_error("Ledger file exceeds 16 MiB read limit"))
            raw_bytes = candidate.read_bytes()
            if raw_bytes.startswith(b"\xef\xbb\xbf"):
                return Refusal(_serialization_error("UTF-8 BOM detected in ledger file; pure UTF-8 required"))
            content = raw_bytes.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return Err(_serialization_error(f"Failed to read ledger file: {exc}"))
        return deserialize_ledger_from_jsonl(content)


def _serialization_error(message: str) -> LedgerSerializationError:
    return LedgerSerializationError(code=RefusalCode.MALFORMED_PACKET, message=message)
