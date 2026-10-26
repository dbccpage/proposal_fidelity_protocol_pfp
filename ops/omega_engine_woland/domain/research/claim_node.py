"""ClaimNode value object representing a declared research claim in the run graph.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from omega_engine_woland.domain.research.enums import (
    ClaimCeilingType,
    ClaimKindType,
)


class ClaimNode(BaseModel):
    """Fully typed immutable Pydantic Value Object for declared research claims."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    claim_id: str
    kind: ClaimKindType = "unknown"
    claim_ceiling: ClaimCeilingType = "UNKNOWN"
    mechanization_class: str = ""
    lean_na_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


__all__ = [
    "ClaimNode",
]
