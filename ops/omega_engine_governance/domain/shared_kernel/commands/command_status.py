from __future__ import annotations

from enum import Enum


class CommandStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"
    REFUSED = "REFUSED"
