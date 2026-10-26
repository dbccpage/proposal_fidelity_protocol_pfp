"""Context Mismatch Error.

AuthorityEffect: None.
"""

from __future__ import annotations

from .swarm_runtime_error import SwarmRuntimeError


class ContextMismatch(SwarmRuntimeError):
    """Raised when agent receives a task outside its declared scope."""
