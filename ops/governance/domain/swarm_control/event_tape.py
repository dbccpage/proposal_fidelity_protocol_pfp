"""Event Tape Aggregate.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from .event_tape_entry_v1 import (
    _GENESIS_HASH,
    EventTapeEntryV1,
    compute_entry_hash,
    compute_payload_sha256,
)
from .event_tape_error import EventTapeError
from .value_objects import UtcTimestamp


class EventTape:
    """In-memory hash-chained tape with verified replay semantics."""

    def __init__(self) -> None:
        self._entries: list[EventTapeEntryV1] = []

    @property
    def entries(self) -> tuple[EventTapeEntryV1, ...]:
        return tuple(self._entries)

    @property
    def current_hash(self) -> str:
        return str(self._entries[-1].entry_hash) if self._entries else _GENESIS_HASH

    @property
    def next_seq(self) -> int:
        return len(self._entries)

    def append(
        self,
        *,
        event_id: str,
        transition_type: str,
        packet_id: str,
        payload: Mapping[str, Any],
        timestamp_utc: str | datetime | None = None,
    ) -> EventTapeEntryV1:
        seq = self.next_seq
        prev_hash = self.current_hash
        ts = (
            UtcTimestamp.from_iso(timestamp_utc)
            if timestamp_utc is not None
            else UtcTimestamp.now()
        )
        payload_hash = compute_payload_sha256(payload)
        entry_hash = compute_entry_hash(
            seq=seq,
            event_id=event_id,
            prev_entry_hash=prev_hash,
            transition_type=transition_type,
            packet_id=packet_id,
            payload_sha256=payload_hash,
            timestamp_utc=str(ts),
        )
        entry = EventTapeEntryV1(
            seq=seq,
            event_id=event_id,
            prev_entry_hash=prev_hash,
            transition_type=transition_type,
            packet_id=packet_id,
            payload_sha256=payload_hash,
            payload=payload,
            timestamp_utc=ts,
            entry_hash=entry_hash,
        )
        self._entries.append(entry)
        return entry

    @classmethod
    def replay(cls, entries: Sequence[EventTapeEntryV1]) -> EventTape:
        """Replay entries strictly from scratch, verifying hash continuity and gap absence."""
        tape = cls()
        expected_prev = _GENESIS_HASH
        for idx, entry in enumerate(entries):
            entry.validate_integrity()
            if entry.seq != idx:
                raise EventTapeError("SEQUENCE_GAP", f"expected {idx} got {entry.seq}")
            if entry.prev_entry_hash != expected_prev:
                raise EventTapeError(
                    "HASH_CHAIN_BROKEN",
                    f"at seq {entry.seq}: expected prev {expected_prev} got {entry.prev_entry_hash}",
                )
            tape._entries.append(entry)
            expected_prev = str(entry.entry_hash)
        return tape
