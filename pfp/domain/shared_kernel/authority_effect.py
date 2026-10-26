"""Shared Kernel: Authority effect Value Object and validation rule."""

from __future__ import annotations

from enum import Enum

from ..exceptions import ForbiddenAuthorityError


class AuthorityEffect(str, Enum):
    """AuthorityEffect enum enforcing invariant that no autonomous payload claims authority."""

    NONE = "None"


def validate_authority_effect_none(authority_effect: str | AuthorityEffect) -> None:
    """Invariant: Authority effect must strictly equal 'None' across all domain boundaries."""
    val = authority_effect.value if isinstance(authority_effect, AuthorityEffect) else str(authority_effect)
    if val != AuthorityEffect.NONE.value:
        raise ForbiddenAuthorityError(
            f"AuthorityEffect violation: expected {AuthorityEffect.NONE.value!r}, got {val!r}"
        )
