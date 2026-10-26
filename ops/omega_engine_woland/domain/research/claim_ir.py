"""Claim IR document schemas matching claim_ir.yaml.

AuthorityEffect: None.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from omega_engine_woland.domain.research.claim_node import ClaimNode
from omega_engine_woland.domain.research.enums import ClaimCeilingType
from omega_engine_woland.domain.services import ObligationPolicyService


class ClaimIRItem(BaseModel):
    """Pydantic schema matching individual claim items in docs/claim_ir.yaml."""

    model_config = ConfigDict(extra="ignore")

    claim_id: str
    mechanization_class: str = ""
    lean_na_reason: str = ""
    title: str = ""
    description: str = ""

    def to_claim_node(self) -> ClaimNode:
        kind = ObligationPolicyService.kind_from_mechanization_class(self.mechanization_class)
        ceiling: ClaimCeilingType = "SCOPE_FENCE" if kind == "scope_fence" else "DECLARED"
        if "LEAN" in self.mechanization_class.upper() and "TOY" not in self.mechanization_class.upper():
            ceiling = "MECHANIZED_CORE_ONLY"
        return ClaimNode(
            claim_id=self.claim_id,
            kind=kind,
            claim_ceiling=ceiling,
            mechanization_class=self.mechanization_class,
            lean_na_reason=self.lean_na_reason,
        )


class ClaimIRDocument(BaseModel):
    """Fully typed Pydantic document matching docs/claim_ir.yaml."""

    model_config = ConfigDict(extra="ignore")

    schema_version: str = "claim_ir/v1"
    claims: list[ClaimIRItem] = Field(default_factory=list)

    @classmethod
    def from_yaml(cls, yaml_text: str) -> ClaimIRDocument:
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:
            raise PaperRunGraphError("PyYAML required to parse claim_ir.yaml") from exc
        raw = yaml.safe_load(yaml_text) or {}
        if not isinstance(raw, dict):
            return cls(claims=[])
        return cls.model_validate(raw)

    def to_claim_nodes(self) -> list[ClaimNode]:
        return [item.to_claim_node() for item in self.claims if item.claim_id.strip()]


__all__ = [
    "ClaimIRDocument",
    "ClaimIRItem",
]
