"""Ports through which the Adversary base swarm reaches its sister estates.

Every port returns ``Result[..., Refusal]`` and can be probed. A probe performs one real
round trip in a scratch root and returns a ``ConnectionReceiptV1``; Null adapters return
a disconnected receipt. Paths cross these ports as strings so the domain stays free of
filesystem libraries.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Protocol

from operations.domain.rop.result import Refusal, Result

from .connection import ConnectionReceiptV1, EstateName
from .evidence import is_sha256_ref
from .models import AdversaryBoutOutcomeV1, AdversaryBoutRequestV1
from .specialization import PortName
from .swarm_models import CodaEvaluationResult, LggrGluingResult, ResearchEvidenceEnvelopeV1

#: Act VII bout status -> core_types::routing::RoutingTerminal.
ROUTING_TERMINAL_BY_BOUT_STATUS = {
    "AUTHORIZED": "CheckPassed",
    "BOUNDED_RESIDUAL": "Repair",
    "NOT_MEASURED": "RequiresLift",
    "FIXTURE_ONLY": "Refusal",
    "ABLATED_WOULD_AUTHORIZE": "Refusal",
    "REFUSED": "Refused",
}

ANTI_SKILL_DISPOSITIONS = frozenset({"CLEAR", "FINDING", "HOLD", "REFUSE"})
#: The OEWAS anti-skill gate stages, in pipeline order.
ANTI_SKILL_STAGES = ("PRE_DISPATCH", "POST_PRODUCTION", "PRE_SELECTION", "PRE_SEAL")


@dataclass(frozen=True, slots=True)
class AntiSkillDecisionV1:
    stage: str
    subject_id: str
    disposition: str
    registry_id: str
    hit_ids: tuple[str, ...]
    receipt_id: str
    activation_profile_digest: str = ""
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.stage not in ANTI_SKILL_STAGES:
            raise ValueError(f"unknown anti-skill stage {self.stage!r}")
        if self.disposition not in ANTI_SKILL_DISPOSITIONS:
            raise ValueError(f"unknown anti-skill disposition {self.disposition!r}")
        if self.authority_effect != "None":
            raise ValueError("anti-skill decisions carry no authority")
        for name in ("subject_id", "registry_id", "receipt_id", "activation_profile_digest"):
            value = getattr(self, name)
            if value and not is_sha256_ref(value):
                raise ValueError(f"{name} must be a sha256 reference")
        if not is_sha256_ref(self.subject_id):
            raise ValueError("subject_id must be a sha256 reference")
        if type(self.hit_ids) is not tuple or any(not is_sha256_ref(hit) for hit in self.hit_ids):
            raise ValueError("hit_ids must be a tuple of sha256 references")


@dataclass(frozen=True, slots=True)
class AdmittedGuidanceV1:
    """Guidance lines from human-admitted antibodies; malformed records are named, not dropped."""

    lines: tuple[str, ...]
    malformed_ids: tuple[str, ...]
    authority_effect: str = "None"


class EstateProbePort(Protocol):
    estate: EstateName
    port: PortName

    def probe(self, scratch_root: str) -> ConnectionReceiptV1: ...


class BoutExecutionPort(EstateProbePort, Protocol):
    def execute_bout(self, request: AdversaryBoutRequestV1) -> Result[AdversaryBoutOutcomeV1, Refusal]: ...


class ImmuneAntibodyPort(EstateProbePort, Protocol):
    def record_candidates(
        self, defects: Sequence[str], *, run_id: str, task_id: str
    ) -> Result[tuple[str, ...], Refusal]: ...

    def admitted_guidance(self) -> Result[AdmittedGuidanceV1, Refusal]: ...


class PromptGenealogyPort(EstateProbePort, Protocol):
    def record_lineage(
        self, parent_key: str, child_key: str, deficiencies: Sequence[str], guidance: str
    ) -> Result[str, Refusal]: ...


class AntiSkillGatePort(EstateProbePort, Protocol):
    def evaluate(
        self, stage: str, subject: Mapping[str, Any]
    ) -> Result[AntiSkillDecisionV1, Refusal]: ...


class SgtTurnPort(EstateProbePort, Protocol):
    def record_turn(self, session_id: str, payload: Mapping[str, Any]) -> Result[str, Refusal]: ...


class CodaEvaluationPort(EstateProbePort, Protocol):
    def evaluate(
        self,
        task_id: str,
        x_vector: Sequence[Fraction],
        coboundary_d0: Sequence[Sequence[Fraction]] | None = None,
        coboundary_d1: Sequence[Sequence[Fraction]] | None = None,
        cert_name: str | None = None,
        *, binding: Mapping[str, str] | None = None,
    ) -> Result[CodaEvaluationResult, Refusal]: ...


class LggrGluingPort(EstateProbePort, Protocol):
    def evaluate(
        self,
        local_evaluators: Mapping[str, int],
        global_evaluator: int,
        corpus_samples: Sequence[tuple[Mapping[str, int], int]] | None = None,
        *, carrier: Mapping[str, Any] | None = None, binding: Mapping[str, str] | None = None,
        soundness: Mapping[str, Any] | None = None,
    ) -> Result[LggrGluingResult, Refusal]: ...


class EnvelopeStorePort(EstateProbePort, Protocol):
    def persist(
        self, envelope: ResearchEvidenceEnvelopeV1, output_dir: str | None = None
    ) -> Result[str, Refusal]: ...


__all__ = [
    "ANTI_SKILL_DISPOSITIONS",
    "ANTI_SKILL_STAGES",
    "ROUTING_TERMINAL_BY_BOUT_STATUS",
    "AdmittedGuidanceV1",
    "AntiSkillDecisionV1",
    "AntiSkillGatePort",
    "BoutExecutionPort",
    "CodaEvaluationPort",
    "EnvelopeStorePort",
    "EstateProbePort",
    "ImmuneAntibodyPort",
    "LggrGluingPort",
    "PromptGenealogyPort",
    "SgtTurnPort",
]
