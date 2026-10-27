"""Parse Disposition Enum.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class ParseDisposition(str, Enum):
    ACTIVE = "ACTIVE"
    STOP = "STOP"
    REFUSED = "REFUSED"
