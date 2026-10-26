"""Duplicate Task Error.

AuthorityEffect: None.
"""

from __future__ import annotations

from .swarm_runtime_error import SwarmRuntimeError


class DuplicateTask(SwarmRuntimeError):
    """Raised when task ID already exists in runtime state."""
