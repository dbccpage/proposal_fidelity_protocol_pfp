"""Hash-chained crash recovery and projection verification for Prompt Civilization.

Remediates SYS-PCIV-008: replaces unconditional is_consistent=True projection
replay with canonical sequence, prev_sha256 link, and event_sha256 digest verification
across both in-memory event logs and durable .jsonl files.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from pciv.infrastructure.persistence import PromptProjectionV1, RecoveredProjections

GENESIS_PREV_SHA256 = "0" * 64

CORRUPTION_CODES = frozenset(
    {
        "HASH_CHAIN_MISMATCH",
        "EVENT_DIGEST_TAMPERED",
        "SEQUENCE_GAP",
        "TRUNCATED_JSON_RECORD",
    }
)

_REQUIRED_EVENT_FIELDS = frozenset(
    {
        "seq",
        "prompt_id",
        "kind",
        "payload",
        "prev_sha256",
        "event_sha256",
    }
)


def compute_event_sha256(
    *,
    seq: int,
    prompt_id: str,
    kind: str,
    payload: Mapping[str, Any],
    prev_sha256: str,
) -> str:
    """Compute canonical SHA-256 hex digest over (seq, prompt_id, kind, payload, prev_sha256)."""
    canonical_tuple = [seq, prompt_id, kind, dict(payload), prev_sha256]
    encoded = json.dumps(
        canonical_tuple,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


class VerifiedRecoveredProjections(RecoveredProjections):
    """Projections recovered from verified hash-chained event replay."""

    def __init__(
        self,
        *args: Any,
        is_consistent: bool = True,
        corruption_code: str | None = None,
        verified_event_count: int = 0,
        corruption_detail: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, is_consistent=is_consistent, **kwargs)
        if corruption_code is not None and corruption_code not in CORRUPTION_CODES:
            raise ValueError(f"Unknown corruption_code: {corruption_code!r}")
        self.corruption_code = corruption_code
        self.verified_event_count = verified_event_count
        self.corruption_detail = corruption_detail


def _unique_json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, val in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON key: {key!r}")
        obj[key] = val
    return obj


def _reject_json_constant(token: str) -> Any:
    raise ValueError(f"non-finite JSON constant forbidden: {token!r}")


def _strict_json_loads(line: str) -> Any:
    return json.loads(
        line,
        object_pairs_hook=_unique_json_pairs,
        parse_constant=_reject_json_constant,
    )


def _validate_record_shape(record: Any, expected_seq: int) -> tuple[str | None, str | None]:
    if not isinstance(record, dict) or not _REQUIRED_EVENT_FIELDS.issubset(record.keys()):
        return ("TRUNCATED_JSON_RECORD", f"record at index {expected_seq} is missing required fields")
    if set(record.keys()) != _REQUIRED_EVENT_FIELDS:
        extra = sorted(set(record.keys()) - _REQUIRED_EVENT_FIELDS)
        return ("EVENT_DIGEST_TAMPERED", f"record at index {expected_seq} contains unhashed extra fields: {extra}")
    seq = record.get("seq")
    if isinstance(seq, bool) or not isinstance(seq, int) or seq != expected_seq:
        return ("SEQUENCE_GAP", f"expected seq={expected_seq}, observed seq={seq!r}")
    prompt_id = record.get("prompt_id")
    kind = record.get("kind")
    if not isinstance(prompt_id, str) or not prompt_id or not isinstance(kind, str) or not kind:
        return ("TRUNCATED_JSON_RECORD", f"invalid prompt_id or kind at seq={expected_seq}")
    if not isinstance(record.get("payload"), dict):
        return ("TRUNCATED_JSON_RECORD", f"payload at seq={expected_seq} must be a JSON object")
    return (None, None)


def _validate_single_record(
    record: Any,
    *,
    expected_seq: int,
    expected_prev_sha256: str,
) -> tuple[str | None, str | None, str | None]:
    """Validate one parsed event record against sequence, chain link, and digest contracts."""
    shape_code, shape_detail = _validate_record_shape(record, expected_seq)
    if shape_code is not None:
        return (shape_code, shape_detail, None)

    prev_sha256 = record.get("prev_sha256")
    if not isinstance(prev_sha256, str) or prev_sha256 != expected_prev_sha256:
        return (
            "HASH_CHAIN_MISMATCH",
            f"at seq={expected_seq}, expected prev_sha256={expected_prev_sha256}, got {prev_sha256!r}",
            None,
        )

    try:
        recomputed = compute_event_sha256(
            seq=record["seq"],
            prompt_id=record["prompt_id"],
            kind=record["kind"],
            payload=record["payload"],
            prev_sha256=prev_sha256,
        )
    except (TypeError, ValueError) as exc:
        return ("EVENT_DIGEST_TAMPERED", f"non-canonical payload at seq={expected_seq}: {exc}", None)

    event_sha256 = record.get("event_sha256")
    if not isinstance(event_sha256, str) or recomputed != event_sha256:
        return (
            "EVENT_DIGEST_TAMPERED",
            f"at seq={expected_seq}, recomputed digest {recomputed} != stored {event_sha256!r}",
            None,
        )

    return (None, None, recomputed)


class VerifiedProjectionEngineV1:
    """Projection engine verifying hash-chained event logs in memory or durable .jsonl storage."""

    def __init__(self, log_path: Path | str | None = None) -> None:
        self._log_path = Path(log_path) if log_path is not None else None
        self._events: list[dict[str, Any]] = []
        if self._log_path is not None and self._log_path.exists():
            self._load_existing_log_into_memory()

    @property
    def events(self) -> list[dict[str, Any]]:
        """Mutable reference to in-memory event records (for replay and tamper testing)."""
        return self._events

    def _load_existing_log_into_memory(self) -> None:
        if self._log_path is None or not self._log_path.exists():
            return
        try:
            raw_text = self._log_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return
        if not raw_text:
            return
        loaded: list[dict[str, Any]] = []
        for line in raw_text.splitlines():
            try:
                parsed = _strict_json_loads(line)
            except (json.JSONDecodeError, ValueError):
                return
            if not isinstance(parsed, dict):
                return
            loaded.append(parsed)
        self._events = loaded

    def append_event(
        self,
        *,
        prompt_id: str,
        kind: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append a canonically sequenced and hash-chained event."""
        if not isinstance(prompt_id, str) or not prompt_id.strip():
            raise ValueError("prompt_id must be a non-empty string")
        if not isinstance(kind, str) or not kind.strip():
            raise ValueError("kind must be a non-empty string")
        payload_dict = {} if payload is None else deepcopy(dict(payload))

        check = self.recover_from_crash()
        if not check.is_consistent:
            raise ValueError(
                f"APPEND_REFUSED_CORRUPTED_LOG: cannot append onto corrupted log ({check.corruption_code})"
            )
        if self._log_path is not None and self._log_path.exists():
            items, _err = self._iter_replay_items()
            self._events = [deepcopy(rec) for ok, rec, _ in items if ok and isinstance(rec, dict)]

        seq = len(self._events)
        prev_sha256 = GENESIS_PREV_SHA256 if seq == 0 else str(self._events[-1]["event_sha256"])
        event_sha256 = compute_event_sha256(
            seq=seq,
            prompt_id=prompt_id,
            kind=kind,
            payload=payload_dict,
            prev_sha256=prev_sha256,
        )
        record: dict[str, Any] = {
            "seq": seq,
            "prompt_id": prompt_id,
            "kind": kind,
            "payload": payload_dict,
            "prev_sha256": prev_sha256,
            "event_sha256": event_sha256,
        }

        if self._log_path is not None:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            serialized_line = (
                json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n"
            )
            with self._log_path.open("ab") as handle:
                handle.write(serialized_line.encode("ascii"))
                handle.flush()
                os.fsync(handle.fileno())

        self._events.append(record)
        return deepcopy(record)

    def record_event(self, event: Mapping[str, Any]) -> dict[str, Any]:
        """Compatibility wrapper extracting prompt_id, kind, and payload."""
        prompt_id = str(event.get("prompt_id", ""))
        kind = str(event.get("kind", ""))
        raw_payload = event.get("payload")
        if isinstance(raw_payload, Mapping):
            payload = dict(raw_payload)
        else:
            payload = {k: v for k, v in event.items() if k not in {"prompt_id", "kind"}}
        return self.append_event(prompt_id=prompt_id, kind=kind, payload=payload)

    def _iter_replay_items(self) -> tuple[list[tuple[bool, Any, str | None]], str | None]:
        if self._log_path is None:
            return ([(True, item, None) for item in self._events], None)

        if not self._log_path.exists():
            return ([], None)

        try:
            raw_text = self._log_path.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            return ([], f"invalid UTF-8 in journal: {exc}")

        if not raw_text:
            return ([], None)

        items: list[tuple[bool, Any, str | None]] = []
        for idx, line in enumerate(raw_text.splitlines()):
            if not line.strip():
                items.append((False, None, f"blank or truncated record at line {idx}"))
                continue
            try:
                parsed = _strict_json_loads(line)
            except (json.JSONDecodeError, ValueError) as exc:
                items.append((False, None, f"truncated or malformed JSON at line {idx}: {exc}"))
                continue
            items.append((True, parsed, None))
        return (items, None)

    def recover_from_crash(self) -> VerifiedRecoveredProjections:
        """Replay and verify every event record before exposing recovered projections."""
        items, fatal_decode_err = self._iter_replay_items()
        if fatal_decode_err is not None:
            return VerifiedRecoveredProjections(
                {},
                is_consistent=False,
                corruption_code="TRUNCATED_JSON_RECORD",
                verified_event_count=0,
                corruption_detail=fatal_decode_err,
            )

        projections: dict[str, PromptProjectionV1] = {}
        expected_prev = GENESIS_PREV_SHA256

        for expected_seq, (ok_json, record, json_err) in enumerate(items):
            if not ok_json:
                return VerifiedRecoveredProjections(
                    {},
                    is_consistent=False,
                    corruption_code="TRUNCATED_JSON_RECORD",
                    verified_event_count=expected_seq,
                    corruption_detail=json_err,
                )
            code, detail, verified_sha = _validate_single_record(
                record,
                expected_seq=expected_seq,
                expected_prev_sha256=expected_prev,
            )
            if code is not None or verified_sha is None:
                return VerifiedRecoveredProjections(
                    {},
                    is_consistent=False,
                    corruption_code=code,
                    verified_event_count=expected_seq,
                    corruption_detail=detail,
                )

            expected_prev = verified_sha
            pid = str(record["prompt_id"])
            if pid not in projections:
                projections[pid] = PromptProjectionV1(prompt_id=pid)
            if record["kind"] == "ExecutionPass":
                projections[pid].pass_count += 1

        return VerifiedRecoveredProjections(
            projections,
            is_consistent=True,
            corruption_code=None,
            verified_event_count=len(items),
            corruption_detail=None,
        )


__all__ = [
    "CORRUPTION_CODES",
    "GENESIS_PREV_SHA256",
    "VerifiedProjectionEngineV1",
    "VerifiedRecoveredProjections",
    "compute_event_sha256",
]
