"""Window Declaration Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from .authority_effect_v1 import AuthorityEffectV1
from .authority_fence_error import AuthorityFenceError


def fence_authority_effect(authority_effect: AuthorityEffectV1 | str | None) -> AuthorityEffectV1:
    if type(authority_effect) is AuthorityEffectV1:
        return authority_effect
    if authority_effect is None or (type(authority_effect) is str and authority_effect == "None"):
        return AuthorityEffectV1.NONE
    raise AuthorityFenceError(f"ILLEGAL_AUTHORITY_EFFECT:{authority_effect!r}")


@dataclass(frozen=True, slots=True, eq=False)
class WindowDeclaration:
    """Fenced window declaration Value Object."""

    name: str
    authority_effect: AuthorityEffectV1

    def __post_init__(self) -> None:
        if type(self) is not WindowDeclaration:
            raise AuthorityFenceError("WINDOW_DECLARATION_SUBCLASS_REFUSED")
        ae = fence_authority_effect(self.authority_effect)
        if ae != self.authority_effect:
            object.__setattr__(self, "authority_effect", ae)

    @classmethod
    def create(
        cls,
        name: str,
        authority_effect: AuthorityEffectV1 | str | None = AuthorityEffectV1.NONE,
    ) -> WindowDeclaration:
        return cls(name=name, authority_effect=fence_authority_effect(authority_effect))

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.name == other.name and self.authority_effect == other.authority_effect

    def __hash__(self) -> int:
        return hash((type(self), self.name, self.authority_effect))
