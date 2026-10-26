"""Runtime Event Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any


def _require_text(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    """An observational fact; events do not drive critical control flow."""

    event_type: str
    run_id: str
    subject_id: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text("event_type", self.event_type)
        _require_text("run_id", self.run_id)
        _require_text("subject_id", self.subject_id)
        object.__setattr__(self, "payload", _freeze_mapping(self.payload))
