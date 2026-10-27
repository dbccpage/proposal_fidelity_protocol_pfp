"""No Agent Available Error.

AuthorityEffect: None.
"""

from __future__ import annotations

from .swarm_runtime_error import SwarmRuntimeError


class NoAgentAvailable(SwarmRuntimeError):
    """Raised when swarm cannot route a task to any active agent."""
