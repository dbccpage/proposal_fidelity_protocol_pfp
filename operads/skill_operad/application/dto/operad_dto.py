"""Data Transfer Objects (DTOs) for the Operad Application Layer.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ValidationReportDTO:
    """Structured report returned by the ValidateOperadUseCase."""
    colour_count: int
    operation_count: int
    unit_count: int
    admitted_entry_skills: List[str]
    slices_verified: int
    provisional_meta_skills: Dict[str, int]
    unverified_laws: List[str]
    is_valid: bool
    authority_effect: str = "None"
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DispatchResultDTO:
    """Result of dispatching or resolving an operadic operation."""
    op_id: str
    is_resolved: bool
    source_colours: Tuple[str, ...]
    target_colour: str
    detail: str
    authority_effect: str = "None"
