"""PaperRunGraph: Fully typed Pydantic v2 Aggregate Root model for research repair carrier
and graph, with re-exports of domain value objects, enums, errors, and pure fail-closed
ROP transition verification services.

AuthorityEffect: None.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field

from omega_engine_operations.domain.rop.result import Refusal, Result
from omega_engine_woland.domain.research.claim_ir import (
    ClaimIRDocument,
    ClaimIRItem,
)
from omega_engine_woland.domain.research.claim_node import ClaimNode
from omega_engine_woland.domain.research.enums import (
    AUTHORITY_EFFECT,
    CLAIM_CEILINGS,
    SCHEMA_VERSION,
    ClaimCeilingType,
    ClaimKind,
    ClaimKindType,
    ObligationDisposition,
    ObligationDispositionType,
    ObligationKind,
    ObligationKindType,
    Role,
    RoleType,
)
from omega_engine_woland.domain.research.errors import PaperRunGraphError
from omega_engine_woland.domain.research.obligation_node import ObligationNode
from omega_engine_woland.domain.research.run_plan import RunPlan
from omega_engine_woland.domain.services import (
    ObligationPolicyService,
    StagePipelinePlanningService,
    TransitionValidatorService,
)
from omega_engine_woland.domain.research.transition_event import TransitionEvent


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _kind_from_claim_ir_class(mech: str) -> ClaimKindType:
    return ObligationPolicyService.kind_from_mechanization_class(mech)  # type: ignore[return-value]


def _obligations_for_kind(kind: str) -> list[ObligationKindType]:
    return ObligationPolicyService.obligations_for_kind(kind)  # type: ignore[return-value]


def _stages_for_obligations(obs: Iterable[str]) -> list[str]:
    return StagePipelinePlanningService.stages_for_obligations(obs)


# ============================================================================
# Aggregate Root: PaperRunGraph
# ============================================================================


class PaperRunGraph(BaseModel):
    """Fully typed Pydantic Aggregate Root for research repair carrier + graph."""

    model_config = ConfigDict(extra="forbid")

    paper_root: str
    carrier_hash: str
    claims: list[ClaimNode] = Field(default_factory=list)
    obligations: list[ObligationNode] = Field(default_factory=list)
    schema_version: str = SCHEMA_VERSION
    authority_effect: str = AUTHORITY_EFFECT
    frozen_at_utc: str = Field(default_factory=_utc_now)

    def add_claim(self, claim: ClaimNode) -> None:
        self.claims.append(claim)

    def add_obligation(self, obligation: ObligationNode) -> None:
        self.obligations.append(obligation)

    @classmethod
    def create(
        cls,
        paper_root: str,
        carrier_hash: str,
        claims: Iterable[ClaimNode],
    ) -> PaperRunGraph:
        claim_list = list(claims)
        obligations = ObligationPolicyService.derive_obligations(claim_list)
        return cls(
            paper_root=paper_root,
            carrier_hash=carrier_hash,
            claims=claim_list,
            obligations=obligations,
        )

    def to_dict(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        data["claim_count"] = len(self.claims)
        data["obligation_count"] = len(self.obligations)
        return data

    def to_yaml(self) -> str:
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:
            raise PaperRunGraphError("PyYAML required for YAML serialization") from exc
        return yaml.safe_dump(self.to_dict(), sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_text: str) -> PaperRunGraph:
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:
            raise PaperRunGraphError("PyYAML required for YAML deserialization") from exc
        raw = yaml.safe_load(yaml_text)
        if not isinstance(raw, dict):
            raise PaperRunGraphError("invalid YAML document: expected dict")
        raw.pop("claim_count", None)
        raw.pop("obligation_count", None)
        return cls.model_validate(raw)


# ============================================================================
# Fail-Closed ROP Transition Verification (Delegated to Domain Service)
# ============================================================================


def validate_transition(ev: TransitionEvent) -> Result[None, Refusal]:
    """Fail-closed ROP validation: returns Ok(None) or Err(Refusal)."""
    return TransitionValidatorService.validate_transition(ev)


def validate_transition_or_raise(ev: TransitionEvent) -> None:
    """Fail-closed exception-raising adapter for legacy callers."""
    TransitionValidatorService.validate_transition_or_raise(ev)


def validate_transition_dict(d: dict[str, Any]) -> Result[None, Refusal]:
    return TransitionValidatorService.validate_transition_dict(d)


__all__ = [
    "AUTHORITY_EFFECT",
    "CLAIM_CEILINGS",
    "ClaimCeilingType",
    "ClaimIRDocument",
    "ClaimIRItem",
    "ClaimKind",
    "ClaimKindType",
    "ClaimNode",
    "ObligationDisposition",
    "ObligationDispositionType",
    "ObligationKind",
    "ObligationKindType",
    "ObligationNode",
    "PaperRunGraph",
    "PaperRunGraphError",
    "Role",
    "RoleType",
    "RunPlan",
    "SCHEMA_VERSION",
    "TransitionEvent",
    "validate_transition",
    "validate_transition_dict",
    "validate_transition_or_raise",
]
