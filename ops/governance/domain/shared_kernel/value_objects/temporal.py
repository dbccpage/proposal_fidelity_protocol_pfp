"""Strongly-Typed Temporal Value Objects.

AuthorityEffect: None.
Guarantees timezone-aware UTC ISO-8601 parsing, expiration checks, and ordering.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Self

from .domain_invariant_error import DomainInvariantError


@dataclass(frozen=True, slots=True, eq=False)
class UtcTimestamp:
    """Immutable ISO-8601 UTC Timestamp Value Object."""

    value: str
    dt: datetime

    def __init__(self, value: str | datetime) -> None:
        if isinstance(value, datetime):
            parsed_dt = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
            parsed_dt = parsed_dt.astimezone(timezone.utc)
            iso_str = parsed_dt.isoformat()
            object.__setattr__(self, "value", iso_str)
            object.__setattr__(self, "dt", parsed_dt)
            return

        if type(value) is not str:
            raise DomainInvariantError("INVALID_TIMESTAMP_TYPE", f"UtcTimestamp requires str or datetime, got {type(value).__name__}")

        raw = value.strip()
        if not raw:
            raise DomainInvariantError("EMPTY_TIMESTAMP", "UtcTimestamp must not be empty")

        try:
            parsed_dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed_dt.tzinfo is None:
                parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
            else:
                parsed_dt = parsed_dt.astimezone(timezone.utc)
        except (ValueError, TypeError) as exc:
            raise DomainInvariantError("INVALID_ISO8601_TIMESTAMP", f"Cannot parse {raw!r}: {exc}") from exc

        object.__setattr__(self, "value", raw)
        object.__setattr__(self, "dt", parsed_dt)

    @classmethod
    def now(cls) -> UtcTimestamp:
        return cls(datetime.now(timezone.utc))

    @classmethod
    def from_iso(cls: type[Self], val: str | datetime | Self) -> Self:
        if isinstance(val, cls):
            return val
        return cls(val)

    def as_datetime(self) -> datetime:
        return self.dt

    def to_iso(self) -> str:
        return self.value

    def is_expired_at(self, reference: UtcTimestamp | datetime | None = None) -> bool:
        """True if this timestamp <= reference timestamp (default: now)."""
        ref_dt = reference.dt if isinstance(reference, UtcTimestamp) else (reference if isinstance(reference, datetime) else datetime.now(timezone.utc))
        if ref_dt.tzinfo is None:
            ref_dt = ref_dt.replace(tzinfo=timezone.utc)
        else:
            ref_dt = ref_dt.astimezone(timezone.utc)
        return self.dt <= ref_dt

    def is_after(self, other: UtcTimestamp | datetime | str) -> bool:
        other_ts = UtcTimestamp.from_iso(other)
        return self.dt > other_ts.dt

    def is_before(self, other: UtcTimestamp | datetime | str) -> bool:
        other_ts = UtcTimestamp.from_iso(other)
        return self.dt < other_ts.dt

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UtcTimestamp):
            return False
        return self.dt == other.dt

    def __hash__(self) -> int:
        return hash((type(self), self.dt))

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"UtcTimestamp({self.value!r})"


# Canonical alias for domain shared kernel
TimestampUtc = UtcTimestamp
