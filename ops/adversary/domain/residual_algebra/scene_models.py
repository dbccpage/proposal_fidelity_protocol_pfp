"""Domain records for Adversary scene execution.

AuthorityEffect: None.
No dispatch, dialogue generation, or network behavior belongs here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from adversary.domain.residual_algebra.licensing_boundary import (
    ValuationReceipt,
)
from adversary.domain.residual_algebra.residual_sorts import (
    Residual,
    Residual1Cochain,
    ResidualSort,
)


@dataclass(frozen=True)
class SceneBeat:
    """A single dramatic and technical dialogue beat in a Adversary scene."""

    speaker: str
    cue: str
    dialogue: str
    operator_tag: str
    cochain: Optional[Residual1Cochain] = None


@dataclass(frozen=True)
class AdversaryScene:
    """Canonical specification of an enacted Adversary scene."""

    id: str
    title: str
    location: str
    source: str
    targets: Tuple[str, ...]
    fits: str
    multicategory_term_str: str
    residual_sort: ResidualSort
    beats: Tuple[Dict[str, str], ...]


@dataclass(frozen=True)
class SceneExecutionReceipt:
    """Deterministic execution receipt for a completed Adversary scene."""

    scene_id: str
    title: str
    timestamp: float
    carrier_in: Dict[str, Any]
    carrier_out: Dict[str, Any]
    multicategory_term: str
    cochains: Tuple[Residual1Cochain, ...]
    absorbed_residual: Residual
    valuation: ValuationReceipt
    licensing_verdict: str
    licensing_token: Optional[str]
    beats_executed: Tuple[SceneBeat, ...]
    evidence_sha256: str
    authority_effect: str = "None"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, SceneExecutionReceipt):
            return False
        return (
            self.scene_id == other.scene_id
            and self.title == other.title
            and self.timestamp == other.timestamp
            and self.carrier_in == other.carrier_in
            and self.carrier_out == other.carrier_out
            and self.multicategory_term == other.multicategory_term
            and self.cochains == other.cochains
            and self.absorbed_residual == other.absorbed_residual
            and self.valuation == other.valuation
            and self.licensing_verdict == other.licensing_verdict
            and self.licensing_token == other.licensing_token
            and self.beats_executed == other.beats_executed
            and self.evidence_sha256 == other.evidence_sha256
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.scene_id,
            self.title,
            self.timestamp,
            self.multicategory_term,
            self.cochains,
            self.absorbed_residual,
            self.valuation,
            self.licensing_verdict,
            self.licensing_token,
            self.beats_executed,
            self.evidence_sha256,
            self.authority_effect,
        ))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "title": self.title,
            "timestamp": self.timestamp,
            "multicategory_term": self.multicategory_term,
            "total_residual_mass": self.valuation.residual_norm_phi_1,
            "valuation": {
                "residual_norm_phi_1": self.valuation.residual_norm_phi_1,
                "is_exact_coboundary": self.valuation.is_exact_coboundary,
                "measurement_status": "MEASURED" if self.valuation.is_measured else "NOT_MEASURED",
                "diagnostics": dict(self.valuation.diagnostics),
            },
            "is_exact": self.valuation.is_exact_coboundary,
            "licensing_verdict": self.licensing_verdict,
            "licensing_token": self.licensing_token,
            "evidence_sha256": self.evidence_sha256,
            "authority_effect": self.authority_effect,
            "cochains_count": len(self.cochains),
            "beats_count": len(self.beats_executed),
        }
