"""Tool Not Found Error.

AuthorityEffect: None.
"""

from __future__ import annotations

from .swarm_runtime_error import SwarmRuntimeError


class ToolNotFound(SwarmRuntimeError):
    """Raised when requested tool is not in agent capability manifest."""
