"""Agent Spec Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


def _require_text(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class AgentSpec:
    """Immutable construction data for one agent instance."""

    agent_id: str
    kind: str
    model_ref: str
    memory_ref: str
    policy_ref: str
    tool_refs: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    max_steps: int = 12

    def __post_init__(self) -> None:
        for field_name in (
            "agent_id",
            "kind",
            "model_ref",
            "memory_ref",
            "policy_ref",
        ):
            _require_text(field_name, getattr(self, field_name))
        if self.max_steps <= 0:
            raise ValueError("max_steps must be positive")
        if len(set(self.tool_refs)) != len(self.tool_refs):
            raise ValueError("tool_refs must be unique")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise ValueError("capabilities must be unique")
        object.__setattr__(self, "tool_refs", tuple(self.tool_refs))
        object.__setattr__(self, "capabilities", tuple(self.capabilities))
