"""Configuration Error.

AuthorityEffect: None.
"""

from __future__ import annotations

from .swarm_runtime_error import SwarmRuntimeError


class ConfigurationError(SwarmRuntimeError):
    """Raised when runtime or agent configuration is invalid."""
