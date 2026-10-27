"""Event Tape Entry V1 Domain Event.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any

from .event_tape_error import EventTapeError
from .value_objects import (
    DigestKind,
    DomainInvariantError,
    EventId,
    IdKind,
    PacketId,
    Sha256Digest,
    UtcTimestamp,
)

TAPE_SCHEMA_V1 = "core.event_tape.v1"
_GENESIS_HASH = "0" * 64


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key, child in value.items():
            if type(key) is not str:
                raise EventTapeError(
                    "INVALID_PAYLOAD", "mapping keys must be exact strings"
                )
            frozen[key] = _freeze_json(child)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(child) for child in value)
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    raise EventTapeError(
        "INVALID_PAYLOAD", f"unsupported JSON value {type(value).__name__}"
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _json_ready(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(child) for child in value]
    return value


def compute_payload_sha256(payload: Mapping[str, Any]) -> str:
    canonical_json = json.dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical_json).hexdigest()


def compute_entry_hash(
    *,
    seq: int,
    event_id: EventId | str,
    prev_entry_hash: str,
    transition_type: str,
    packet_id: PacketId | str,
    payload_sha256: Sha256Digest | str,
    timestamp_utc: UtcTimestamp | str,
) -> str:
    hasher = hashlib.sha256()
    for item in (
        TAPE_SCHEMA_V1,
        str(seq),
        str(event_id),
        str(prev_entry_hash),
        str(transition_type),
        str(packet_id),
        str(payload_sha256),
        str(timestamp_utc),
    ):
        hasher.update(item.encode("utf-8"))
        hasher.update(b"\0")
    return hasher.hexdigest()


@dataclass(frozen=True, slots=True, eq=False)
class EventTapeEntryV1:
    """A single append-only Domain Event entry in the cryptographic event tape."""

    seq: int
    event_id: EventId
    prev_entry_hash: str
    transition_type: str
    packet_id: PacketId
    payload_sha256: Sha256Digest
    payload: Mapping[str, Any]
    timestamp_utc: UtcTimestamp
    entry_hash: Sha256Digest
    schema_version: str = TAPE_SCHEMA_V1

    def __init__(
        self,
        *,
        seq: int,
        event_id: EventId | str,
        prev_entry_hash: str,
        transition_type: str,
        packet_id: PacketId | str,
        payload_sha256: Sha256Digest | str,
        payload: Mapping[str, Any],
        timestamp_utc: UtcTimestamp | str | datetime,
        entry_hash: Sha256Digest | str,
        schema_version: str = TAPE_SCHEMA_V1,
    ) -> None:
        if seq < 0:
            raise EventTapeError("INVALID_SEQ")
        if schema_version != TAPE_SCHEMA_V1:
            raise EventTapeError(
                "SCHEMA_VERSION_MISMATCH",
                f"expected {TAPE_SCHEMA_V1} got {schema_version}",
            )
        try:
            ev_id = EventId.from_str(event_id, kind=IdKind.EVENT)
            pkt_id = PacketId.from_str(packet_id, kind=IdKind.PACKET)
            p_sha = Sha256Digest.from_str(payload_sha256, kind=DigestKind.SHA256)
            ts = UtcTimestamp.from_iso(timestamp_utc)
            e_sha = Sha256Digest.from_str(entry_hash, kind=DigestKind.SHA256)
        except DomainInvariantError as exc:
            raise EventTapeError("INVALID_FIELD", str(exc)) from exc

        if not prev_entry_hash or (
            prev_entry_hash != _GENESIS_HASH and len(prev_entry_hash) != 64
        ):
            raise EventTapeError("INVALID_PREV_ENTRY_HASH")
        if not transition_type:
            raise EventTapeError("EMPTY_TRANSITION_TYPE")

        frozen_payload = _freeze_json(payload)
        computed_payload_hash = compute_payload_sha256(frozen_payload)
        if str(p_sha) != computed_payload_hash:
            raise EventTapeError(
                "PAYLOAD_SHA256_MISMATCH",
                f"expected {computed_payload_hash} got {p_sha}",
            )

        computed_entry_hash = compute_entry_hash(
            seq=seq,
            event_id=ev_id,
            prev_entry_hash=prev_entry_hash,
            transition_type=transition_type,
            packet_id=pkt_id,
            payload_sha256=p_sha,
            timestamp_utc=ts,
        )
        if str(e_sha) != computed_entry_hash:
            raise EventTapeError(
                "ENTRY_HASH_MISMATCH",
                f"expected {computed_entry_hash} got {e_sha}",
            )

        object.__setattr__(self, "seq", seq)
        object.__setattr__(self, "event_id", ev_id)
        object.__setattr__(self, "prev_entry_hash", prev_entry_hash)
        object.__setattr__(self, "transition_type", transition_type)
        object.__setattr__(self, "packet_id", pkt_id)
        object.__setattr__(self, "payload_sha256", p_sha)
        object.__setattr__(self, "payload", frozen_payload)
        object.__setattr__(self, "timestamp_utc", ts)
        object.__setattr__(self, "entry_hash", e_sha)
        object.__setattr__(self, "schema_version", schema_version)

    def validate_integrity(self) -> None:
        """Recompute payload and entry hashes before accepting replay input."""
        if self.schema_version != TAPE_SCHEMA_V1:
            raise EventTapeError(
                "SCHEMA_VERSION_MISMATCH",
                f"expected {TAPE_SCHEMA_V1} got {self.schema_version}",
            )
        computed_payload_hash = compute_payload_sha256(self.payload)
        if str(self.payload_sha256) != computed_payload_hash:
            raise EventTapeError(
                "PAYLOAD_SHA256_MISMATCH",
                f"expected {computed_payload_hash} got {self.payload_sha256}",
            )
        computed_entry = compute_entry_hash(
            seq=self.seq,
            event_id=self.event_id,
            prev_entry_hash=self.prev_entry_hash,
            transition_type=self.transition_type,
            packet_id=self.packet_id,
            payload_sha256=self.payload_sha256,
            timestamp_utc=self.timestamp_utc,
        )
        if str(self.entry_hash) != computed_entry:
            raise EventTapeError(
                "ENTRY_HASH_MISMATCH",
                f"expected {computed_entry} got {self.entry_hash}",
            )

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.entry_hash == other.entry_hash

    def __hash__(self) -> int:
        return hash((type(self), self.entry_hash))
