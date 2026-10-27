"""Mode Enum.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class Mode(str, Enum):
    DEV = "DEV"
    STRICT = "STRICT"
