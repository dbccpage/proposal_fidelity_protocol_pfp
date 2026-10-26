"""Domain models and results for the 52-Point Republication Gate.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class GateItemResult:
    """Individual domain gate check result."""

    item_id: int
    name: str
    category: str  # "STATIC" or "DYNAMIC"
    passed: bool
    details: str


@dataclass(frozen=True)
class Gate52Report:
    """Full 52-point verification report for domain models."""

    passed: bool
    static_passed_count: int
    dynamic_passed_count: int
    total_passed_count: int
    items: Tuple[GateItemResult, ...]
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")
