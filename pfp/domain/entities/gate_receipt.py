"""GateReceipt entity: evaluated gate receipt verifying candidate compliance.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from ..exceptions import InvariantViolationError
from pfp.domain.shared_kernel import (
    AuthorityEffect,
    Disposition,
    GateId,
    validate_authority_effect_none,
)


@dataclass(frozen=True, slots=True)
class GateReceiptV1:
    """Evaluated gate receipt verifying candidate compliance."""

    gate_name: GateId
    disposition: Disposition
    message: str = ""
    retained_metrics: Mapping[str, object] = field(default_factory=dict)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE

    def __post_init__(self) -> None:
        validate_authority_effect_none(
            self.authority_effect.value if isinstance(self.authority_effect, AuthorityEffect) else str(self.authority_effect)
        )
        if not isinstance(self.gate_name, GateId):
            object.__setattr__(self, "gate_name", GateId.from_str(self.gate_name))
        if not isinstance(self.disposition, Disposition):
            object.__setattr__(self, "disposition", Disposition.from_str(self.disposition))
        if not isinstance(self.authority_effect, AuthorityEffect):
            object.__setattr__(self, "authority_effect", AuthorityEffect(self.authority_effect))

    @classmethod
    def create(
        cls,
        *,
        gate_name: str | GateId,
        disposition: str | Disposition,
        message: str = "",
        retained_metrics: Mapping[str, object] = field(default_factory=dict),
        authority_effect: str | AuthorityEffect = AuthorityEffect.NONE,
    ) -> GateReceiptV1:
        return cls(
            gate_name=GateId.from_str(gate_name),
            disposition=Disposition.from_str(disposition),
            message=str(message),
            retained_metrics=retained_metrics,
            authority_effect=AuthorityEffect(authority_effect) if isinstance(authority_effect, str) else authority_effect,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "gate_name": str(self.gate_name),
            "disposition": str(self.disposition),
            "message": self.message,
            "retained_metrics": dict(self.retained_metrics),
            "authority_effect": self.authority_effect.value if isinstance(self.authority_effect, AuthorityEffect) else str(self.authority_effect),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> GateReceiptV1:
        return cls.create(
            gate_name=str(data["gate_name"]),
            disposition=str(data["disposition"]),
            message=str(data.get("message", "")),
            retained_metrics=dict(data.get("retained_metrics", {})),  # type: ignore[arg-type]
            authority_effect=str(data.get("authority_effect", AuthorityEffect.NONE.value)),
        )
