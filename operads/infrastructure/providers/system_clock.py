"""System clock implementation of ClockPort."""

from __future__ import annotations

from datetime import datetime, timezone
from ...application.ports.clock_port import ClockPort


class SystemClock(ClockPort):
    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)
