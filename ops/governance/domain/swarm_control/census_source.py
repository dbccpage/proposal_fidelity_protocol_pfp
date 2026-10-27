"""Census Source Enum.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class CensusSource(str, Enum):
    DIRECT = "direct"
    SEARCH = "search"
