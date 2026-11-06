"""TransitionEvent domain value object specifying state transition inputs.

AuthorityEffect: None.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from paperrun.enums import (
    AUTHORITY_EFFECT,
    RoleType,
)


class TransitionEvent(BaseModel):
    """Fully typed immutable Pydantic event specification for state transitions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: RoleType
    event_type: str
    carrier_hash: str
    candidate_hash: str = ""
    post_build: bool = False
    source_mutated_after_build: bool = False
    claims_pass: bool = False
    authority_effect: str = AUTHORITY_EFFECT


__all__ = [
    "TransitionEvent",
]
