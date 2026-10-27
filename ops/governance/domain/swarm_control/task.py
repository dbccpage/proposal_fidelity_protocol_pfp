"""Task Domain Entity.

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
class Task:
    """A unit of work admitted to an agent or swarm."""

    task_id: str
    goal: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    required_capability: str | None = None

    def __post_init__(self) -> None:
        _require_text("task_id", self.task_id)
        _require_text("goal", self.goal)
        if self.required_capability is not None:
            _require_text("required_capability", self.required_capability)
        object.__setattr__(self, "payload", _freeze_mapping(self.payload))
