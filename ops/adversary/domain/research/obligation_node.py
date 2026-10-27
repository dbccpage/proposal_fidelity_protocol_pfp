"""ObligationNode value object representing a proof/audit obligation in the run graph.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from adversary.domain.research.enums import (
    ObligationDispositionType,
    ObligationKindType,
)


class ObligationNode(BaseModel):
    """Fully typed immutable Pydantic Value Object for proof/audit obligations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    obligation_id: str
    claim_id: str
    kind: ObligationKindType
    disposition: ObligationDispositionType = "unchecked"

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


__all__ = [
    "ObligationNode",
]
