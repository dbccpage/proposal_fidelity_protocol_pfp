"""Step Limit Exceeded Error.

AuthorityEffect: None.
"""

from __future__ import annotations

from .swarm_runtime_error import SwarmRuntimeError


class StepLimitExceeded(SwarmRuntimeError):
    """Raised when agent exceeds maximum allowed execution steps."""
