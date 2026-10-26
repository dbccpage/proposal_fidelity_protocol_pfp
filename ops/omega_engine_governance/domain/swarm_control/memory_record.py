"""Memory Record Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from .agent_outcome import AgentOutcome
from .message import Message


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    agent_id: str
    task_id: str
    messages: tuple[Message, ...]
    outcome: AgentOutcome
