"""Typed Error DTO for Railway Responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True, slots=True)
class ApiErrorDTO:
    code: str
    message: str
    status_code: int = 400
    locus: str = ""
    details: Dict[str, str] = None

    def __post_init__(self) -> None:
        if self.details is None:
            object.__setattr__(self, "details", {})
