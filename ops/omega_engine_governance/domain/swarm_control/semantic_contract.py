"""Semantic Contract Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from .authority_effect_v1 import AuthorityEffectV1
from .authority_fence_error import AuthorityFenceError
from .window_declaration import fence_authority_effect


@dataclass(frozen=True, slots=True, eq=False)
class SemanticContract:
    """Fenced semantic contract Value Object."""

    contract_id: str
    authority_effect: AuthorityEffectV1

    def __post_init__(self) -> None:
        if type(self) is not SemanticContract:
            raise AuthorityFenceError("SEMANTIC_CONTRACT_SUBCLASS_REFUSED")
        ae = fence_authority_effect(self.authority_effect)
        if ae != self.authority_effect:
            object.__setattr__(self, "authority_effect", ae)

    @classmethod
    def create(
        cls,
        contract_id: str,
        authority_effect: AuthorityEffectV1 | str | None = AuthorityEffectV1.NONE,
    ) -> SemanticContract:
        return cls(contract_id=contract_id, authority_effect=fence_authority_effect(authority_effect))

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.contract_id == other.contract_id and self.authority_effect == other.authority_effect

    def __hash__(self) -> int:
        return hash((type(self), self.contract_id, self.authority_effect))
