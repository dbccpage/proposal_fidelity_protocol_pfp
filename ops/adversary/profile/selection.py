"""Independent admissibility and productivity selection for Adversary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from operations.domain.rop.result import Err, Ok, Refusal, Result
from adversary.stage.domain import (
    CandidateSelectionProposalV1,
    EvaluatorEpochV1,
    ValuationReceiptV1,
)
from adversary.stage.domain.canonical import (
    AUTHORITY_EFFECT_NONE,
    digest,
    exact_bool,
    identifier,
    integer,
    semantic_id,
    string_tuple,
)

from .models import (
    ANTI_SKILL_STAGE_ORDER,
    ANTI_SKILL_STAGES,
    AntiSkillGateReceiptV1,
    CalibrationReceiptV1,
    PredictionReceiptV1,
)

REQUIRED_HARD_GATES = frozenset({"AUTHORITY", "TEST", "TRUTH"})


@dataclass(frozen=True, slots=True)
class HardGateResultV1:
    gate_id: str
    evidence_refs: tuple[str, ...]
    failed_obligation_refs: tuple[str, ...]
    implementation_digest: str
    independently_recomputed: bool
    passed: bool
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.adversary.hard-gate-result.v1"
    result_id: str = ""

    def __post_init__(self) -> None:
        identifier(self.gate_id, "gate_id")
        exact_bool(self.passed, "passed")
        object.__setattr__(
            self,
            "evidence_refs",
            string_tuple(self.evidence_refs, "evidence_refs", digests=True),
        )
        if not self.evidence_refs:
            raise ValueError("hard gate requires exact evidence references")
        object.__setattr__(
            self,
            "failed_obligation_refs",
            string_tuple(
                self.failed_obligation_refs,
                "failed_obligation_refs",
                digests=True,
            ),
        )
        digest(self.implementation_digest, "implementation_digest")
        exact_bool(self.independently_recomputed, "independently_recomputed")
        if not self.independently_recomputed:
            raise ValueError("hard gate must be independently recomputed")
        if self.passed != (not self.failed_obligation_refs):
            raise ValueError("hard gate PASS is not derived from explicit failures")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("hard gate authority_effect must be None")
        if self.schema_version != "core.oeas.adversary.hard-gate-result.v1":
            raise ValueError("unsupported hard gate result schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.result_id and self.result_id != expected:
            raise ValueError("result_id does not match canonical content")
        object.__setattr__(self, "result_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "passed": self.passed,
            "evidence_refs": list(self.evidence_refs),
            "failed_obligation_refs": list(self.failed_obligation_refs),
            "implementation_digest": self.implementation_digest,
            "independently_recomputed": self.independently_recomputed,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "result_id": self.result_id}


@dataclass(frozen=True, slots=True)
class CandidateProductivityAssessmentV1:
    candidate_id: str
    evaluator_epoch_id: str
    hard_gates: tuple[HardGateResultV1, ...]
    anti_skill_gates: tuple[AntiSkillGateReceiptV1, ...]
    valuation: ValuationReceiptV1
    prediction: PredictionReceiptV1
    calibration: CalibrationReceiptV1
    acceptance_criteria_closed: int
    mutation_witnesses: int
    property_witnesses: int
    adjudicated_findings_resolved: int
    retained_counterexamples: int
    hidden_counterexamples: int
    resource_cost_units: int
    latency_units: int
    evidence_refs: tuple[str, ...]
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.adversary.productivity-assessment.v1"
    assessment_id: str = ""

    def __post_init__(self) -> None:
        digest(self.candidate_id, "candidate_id")
        digest(self.evaluator_epoch_id, "evaluator_epoch_id")
        if type(self.hard_gates) is not tuple or any(
            type(item) is not HardGateResultV1 for item in self.hard_gates
        ):
            raise TypeError("hard_gates must be an exact typed tuple")
        if (
            tuple(sorted(self.hard_gates, key=lambda item: item.gate_id))
            != self.hard_gates
        ):
            raise ValueError("hard gates must be sorted by gate_id")
        if {item.gate_id for item in self.hard_gates} != REQUIRED_HARD_GATES:
            raise ValueError(
                "assessment requires exact truth, authority, and test gates"
            )
        if type(self.anti_skill_gates) is not tuple or any(
            type(item) is not AntiSkillGateReceiptV1 for item in self.anti_skill_gates
        ):
            raise TypeError("anti_skill_gates must be an exact typed tuple")
        if {item.stage for item in self.anti_skill_gates} != ANTI_SKILL_STAGES:
            raise ValueError("assessment requires all three anti-skill gate loci")
        if len(self.anti_skill_gates) != len(ANTI_SKILL_STAGES):
            raise ValueError("assessment duplicates an anti-skill gate locus")
        if (
            tuple(item.stage for item in self.anti_skill_gates)
            != ANTI_SKILL_STAGE_ORDER
        ):
            raise ValueError("anti-skill gates are not in canonical lifecycle order")
        if len({item.subject_id for item in self.anti_skill_gates}) != 1:
            raise ValueError("anti-skill gate subject was substituted across loci")
        if (
            len({item.registry_id for item in self.anti_skill_gates}) != 1
            or len({item.activation_profile_digest for item in self.anti_skill_gates})
            != 1
        ):
            raise ValueError("anti-skill registry/profile changed within one candidate")
        if type(self.valuation) is not ValuationReceiptV1:
            raise TypeError("valuation must be exact ValuationReceiptV1")
        if self.valuation.candidate_id != self.candidate_id:
            raise ValueError("valuation names another candidate")
        if self.valuation.evaluator_epoch_id != self.evaluator_epoch_id:
            raise ValueError("valuation names another evaluator epoch")
        if type(self.prediction) is not PredictionReceiptV1:
            raise TypeError("prediction must be exact PredictionReceiptV1")
        if type(self.calibration) is not CalibrationReceiptV1:
            raise TypeError("calibration must be exact CalibrationReceiptV1")
        if self.calibration.prediction_id != self.prediction.prediction_id:
            raise ValueError("calibration names another prediction")
        for field in (
            "acceptance_criteria_closed",
            "mutation_witnesses",
            "property_witnesses",
            "adjudicated_findings_resolved",
            "retained_counterexamples",
            "hidden_counterexamples",
            "resource_cost_units",
            "latency_units",
        ):
            integer(getattr(self, field), field)
        object.__setattr__(
            self,
            "evidence_refs",
            string_tuple(self.evidence_refs, "evidence_refs", digests=True),
        )
        if not self.evidence_refs:
            raise ValueError("assessment requires evidence references")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("assessment authority_effect must be None")
        if self.schema_version != "core.oeas.adversary.productivity-assessment.v1":
            raise ValueError("unsupported productivity assessment schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.assessment_id and self.assessment_id != expected:
            raise ValueError("assessment_id does not match canonical content")
        object.__setattr__(self, "assessment_id", expected)

    @property
    def hard_gates_pass(self) -> bool:
        return all(item.passed for item in self.hard_gates)

    @property
    def anti_skill_gates_clear(self) -> bool:
        return all(item.disposition == "CLEAR" for item in self.anti_skill_gates)

    @property
    def admissible(self) -> bool:
        return (
            self.hard_gates_pass
            and self.anti_skill_gates_clear
            and self.valuation.delta_phi <= 0
            and self.hidden_counterexamples == 0
        )

    def _payload(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "evaluator_epoch_id": self.evaluator_epoch_id,
            "hard_gates": [item.to_dict() for item in self.hard_gates],
            "anti_skill_gates": [item.to_dict() for item in self.anti_skill_gates],
            "valuation": self.valuation.to_dict(),
            "prediction": self.prediction.to_dict(),
            "calibration": self.calibration.to_dict(),
            "acceptance_criteria_closed": self.acceptance_criteria_closed,
            "mutation_witnesses": self.mutation_witnesses,
            "property_witnesses": self.property_witnesses,
            "adjudicated_findings_resolved": self.adjudicated_findings_resolved,
            "retained_counterexamples": self.retained_counterexamples,
            "hidden_counterexamples": self.hidden_counterexamples,
            "resource_cost_units": self.resource_cost_units,
            "latency_units": self.latency_units,
            "evidence_refs": list(self.evidence_refs),
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "assessment_id": self.assessment_id}


def candidate_may_advance(
    assessment: CandidateProductivityAssessmentV1,
) -> Result[None, Refusal]:
    if type(assessment) is not CandidateProductivityAssessmentV1:
        return Err(
            Refusal(
                "ADVERSARY_ASSESSMENT_REFUSED", "assessment type differs", "adversary-gate"
            )
        )
    if not assessment.hard_gates_pass:
        return Err(
            Refusal("ADVERSARY_HARD_GATE_REFUSED", "a hard gate failed", "adversary-gate")
        )
    if not assessment.anti_skill_gates_clear:
        return Err(
            Refusal(
                "ADVERSARY_ANTISKILL_REFUSED",
                "an anti-skill gate did not clear",
                "adversary-gate",
            )
        )
    if assessment.valuation.delta_phi > 0:
        return Err(
            Refusal(
                "ADVERSARY_PHI_INCREASE_REFUSED",
                "candidate increases frozen Phi",
                "adversary-gate",
            )
        )
    if assessment.hidden_counterexamples:
        return Err(
            Refusal(
                "ADVERSARY_COUNTEREXAMPLE_HIDING_REFUSED",
                "candidate hides counterexamples",
                "adversary-gate",
            )
        )
    return Ok(None)


def _rank(
    item: CandidateProductivityAssessmentV1,
) -> tuple[int, int, int, int, int, int, int, str]:
    return (
        -item.acceptance_criteria_closed,
        -(item.mutation_witnesses + item.property_witnesses),
        -item.adjudicated_findings_resolved,
        -item.retained_counterexamples,
        item.calibration.absolute_error_bps,
        item.resource_cost_units,
        item.latency_units,
        item.candidate_id,
    )


def select_adversary_candidate(
    *,
    selector_agent_id: str,
    epoch: EvaluatorEpochV1,
    assessments: tuple[CandidateProductivityAssessmentV1, ...],
) -> Result[CandidateSelectionProposalV1, Refusal]:
    try:
        identifier(selector_agent_id, "selector_agent_id")
        if type(epoch) is not EvaluatorEpochV1:
            raise TypeError("epoch must be exact EvaluatorEpochV1")
        if (
            type(assessments) is not tuple
            or not assessments
            or any(
                type(item) is not CandidateProductivityAssessmentV1
                for item in assessments
            )
        ):
            raise TypeError("assessments must be a nonempty exact typed tuple")
        if len({item.candidate_id for item in assessments}) != len(assessments):
            raise ValueError("candidate assessments are duplicated")
        if any(item.evaluator_epoch_id != epoch.epoch_id for item in assessments):
            raise ValueError("cross-epoch candidate comparison is forbidden")
        admissible = tuple(item for item in assessments if item.admissible)
        evidence = tuple(sorted(item.assessment_id for item in assessments))
        if not admissible:
            return Ok(
                CandidateSelectionProposalV1(
                    selector_agent_id=selector_agent_id,
                    evaluator_epoch_id=epoch.epoch_id,
                    frontier_candidate_ids=(),
                    selected_candidate_id="",
                    disposition="HOLD",
                    evidence_refs=evidence,
                    nonclaims=(
                        "No least-bad increasing candidate is selected.",
                        "This proposal is not an ActionLicense, merge, or publication.",
                    ),
                )
            )
        ordered = tuple(sorted(admissible, key=_rank))
        return Ok(
            CandidateSelectionProposalV1(
                selector_agent_id=selector_agent_id,
                evaluator_epoch_id=epoch.epoch_id,
                frontier_candidate_ids=tuple(
                    sorted(item.candidate_id for item in admissible)
                ),
                selected_candidate_id=ordered[0].candidate_id,
                disposition="SELECT",
                evidence_refs=evidence,
                nonclaims=(
                    "Selection is a supervised candidate proposal only.",
                    "No ActionLicense, Engine transition, push, merge, or publication is created.",
                ),
            )
        )
    except (TypeError, ValueError) as exc:
        return Err(Refusal("ADVERSARY_SELECTION_REFUSED", str(exc), "adversary-gate"))


__all__ = [
    "REQUIRED_HARD_GATES",
    "CandidateProductivityAssessmentV1",
    "HardGateResultV1",
    "candidate_may_advance",
    "select_adversary_candidate",
]
