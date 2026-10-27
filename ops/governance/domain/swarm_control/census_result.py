"""Census Result Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any
from .census_source import CensusSource


@dataclass(frozen=True)
class CensusResult:
    repository: str
    open_count: int
    open_numbers: tuple[int, ...]
    source: CensusSource
    residual: str | None = None
    observation_binding: Mapping[str, Any] = field(default_factory=dict)

    @property
    def zero_open(self) -> bool:
        """Terminal zero-open only from direct source with no failure residual."""
        if self.source is not CensusSource.DIRECT or self.open_count != 0:
            return False
        return self.residual in (None, "ZERO_OPEN")
