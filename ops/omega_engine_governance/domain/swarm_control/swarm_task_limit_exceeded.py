"""Swarm Task Limit Exceeded Error.

AuthorityEffect: None.
"""

from __future__ import annotations

from .swarm_runtime_error import SwarmRuntimeError


class SwarmTaskLimitExceeded(SwarmRuntimeError):
    """Raised when total swarm concurrency exceeds global ceiling."""
