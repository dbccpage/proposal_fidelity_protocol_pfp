"""Policy Denied Error.

AuthorityEffect: None.
"""

from __future__ import annotations

from .swarm_runtime_error import SwarmRuntimeError


class PolicyDenied(SwarmRuntimeError):
    """Raised when action is rejected by an immutable prime rule."""
