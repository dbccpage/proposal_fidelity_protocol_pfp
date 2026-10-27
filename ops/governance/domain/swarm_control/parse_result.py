"""Parse Result Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from .parse_disposition import ParseDisposition


@dataclass(frozen=True, slots=True)
class ParseResult:
    disposition: ParseDisposition
    residual: str | None = None
    value: str | None = None
