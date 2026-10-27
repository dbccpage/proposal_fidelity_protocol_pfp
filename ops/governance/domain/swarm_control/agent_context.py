"""Agent Context Domain Aggregate.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any

from .message import Message


def _require_text(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class AgentContext:
    """Run-local state; service dependencies never live in this object."""

    run_id: str
    task_id: str
    messages: tuple[Message, ...] = ()
    artifacts: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    remaining_steps: int = 0

    def __post_init__(self) -> None:
        _require_text("run_id", self.run_id)
        _require_text("task_id", self.task_id)
        if self.remaining_steps < 0:
            raise ValueError("remaining_steps cannot be negative")
        object.__setattr__(self, "messages", tuple(self.messages))
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def with_message(self, message: Message) -> AgentContext:
        return replace(self, messages=(*self.messages, message))

    def append(self, message: Message) -> AgentContext:
        return self.with_message(message)

    def with_remaining_steps(self, remaining_steps: int) -> AgentContext:
        return replace(self, remaining_steps=remaining_steps)
