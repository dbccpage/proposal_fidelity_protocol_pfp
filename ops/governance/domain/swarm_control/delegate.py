"""Delegate Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from .task import Task


@dataclass(frozen=True, slots=True)
class Delegate:
    task: Task
