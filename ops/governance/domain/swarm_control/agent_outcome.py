"""Agent Outcome Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from .outcome_status import OutcomeStatus
from .task import Task


@dataclass(frozen=True, slots=True)
class AgentOutcome:
    agent_id: str
    task_id: str
    status: OutcomeStatus
    output: Any = None
    handoffs: tuple[Task, ...] = ()
