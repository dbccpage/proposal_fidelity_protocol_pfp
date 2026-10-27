"""Strict Adversary profile packets.

The records in this module are pure proposals and observations.  They do not
carry an ActionLicense, perform a host effect, or mutate a skill registry.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adversary.stage.domain.canonical import (
    AUTHORITY_EFFECT_NONE,
    digest,
    exact_bool,
    identifier,
    integer,
    semantic_id,
    string_tuple,
    text,
)
from adversary.stage.domain.packets import AgentResultV1

ANTI_SKILL_STAGE_ORDER = ("PRE_DISPATCH", "POST_PRODUCTION", "PRE_SELECTION", "PRE_SEAL")
ANTI_SKILL_STAGES = frozenset(ANTI_SKILL_STAGE_ORDER)
ANTI_SKILL_DISPOSITIONS = frozenset({"CLEAR", "FINDING", "HOLD", "REFUSE"})
MINED_LANES = frozenset({"SKILL_OOUTWIRE", "ANTI_SKILL_CANDIDATE"})


@dataclass(frozen=True, slots=True)
class PredictionReceiptV1:
    work_packet_id: str
    producer_agent_id: str
    prediction_key: str
    expected_gate_results: tuple[str, ...]
    expected_defect_classes: tuple[str, ...]
    resource_min_units: int
    resource_max_units: int
    bounded_confidence_bps: int
    nonclaims: tuple[str, ...]
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.adversary.prediction-receipt.v1"
    prediction_id: str = ""

    def __post_init__(self) -> None:
        digest(self.work_packet_id, "work_packet_id")
        identifier(self.producer_agent_id, "producer_agent_id")
        identifier(self.prediction_key, "prediction_key")
        object.__setattr__(
            self,
            "expected_gate_results",
            string_tuple(
                self.expected_gate_results,
                "expected_gate_results",
                identifiers=True,
            ),
        )
        object.__setattr__(
            self,
            "expected_defect_classes",
            string_tuple(
                self.expected_defect_classes,
                "expected_defect_classes",
                identifiers=True,
            ),
        )
        if not self.expected_gate_results:
            raise ValueError("prediction requires expected gate results")
        integer(self.resource_min_units, "resource_min_units")
        integer(self.resource_max_units, "resource_max_units")
        if self.resource_min_units > self.resource_max_units:
            raise ValueError("prediction resource range is inverted")
        integer(
            self.bounded_confidence_bps,
            "bounded_confidence_bps",
            maximum=10_000,
        )
        object.__setattr__(self, "nonclaims", string_tuple(self.nonclaims, "nonclaims"))
        if not self.nonclaims:
            raise ValueError("prediction requires nonclaims")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("prediction authority_effect must be None")
        if self.schema_version != "core.oeas.adversary.prediction-receipt.v1":
            raise ValueError("unsupported prediction receipt schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.prediction_id and self.prediction_id != expected:
            raise ValueError("prediction_id does not match canonical content")
        object.__setattr__(self, "prediction_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "work_packet_id": self.work_packet_id,
            "producer_agent_id": self.producer_agent_id,
            "prediction_key": self.prediction_key,
            "expected_gate_results": list(self.expected_gate_results),
            "expected_defect_classes": list(self.expected_defect_classes),
            "resource_min_units": self.resource_min_units,
            "resource_max_units": self.resource_max_units,
            "bounded_confidence_bps": self.bounded_confidence_bps,
            "nonclaims": list(self.nonclaims),
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "prediction_id": self.prediction_id}


@dataclass(frozen=True, slots=True)
class CalibrationReceiptV1:
    prediction_id: str
    observed_gate_results: tuple[str, ...]
    observed_defect_classes: tuple[str, ...]
    actual_resource_units: int
    observed_success: bool
    bounded_confidence_bps: int
    absolute_error_bps: int
    use_scope: str = "STRATEGY_TIE_BREAK_ONLY"
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.adversary.calibration-receipt.v1"
    calibration_id: str = ""

    def __post_init__(self) -> None:
        digest(self.prediction_id, "prediction_id")
        object.__setattr__(
            self,
            "observed_gate_results",
            string_tuple(
                self.observed_gate_results,
                "observed_gate_results",
                identifiers=True,
            ),
        )
        object.__setattr__(
            self,
            "observed_defect_classes",
            string_tuple(
                self.observed_defect_classes,
                "observed_defect_classes",
                identifiers=True,
            ),
        )
        integer(self.actual_resource_units, "actual_resource_units")
        exact_bool(self.observed_success, "observed_success")
        integer(
            self.bounded_confidence_bps,
            "bounded_confidence_bps",
            maximum=10_000,
        )
        expected_error = abs(
            self.bounded_confidence_bps - (10_000 if self.observed_success else 0)
        )
        if (
            type(self.absolute_error_bps) is not int
            or self.absolute_error_bps != expected_error
        ):
            raise ValueError("calibration error is not independently derived")
        if self.use_scope != "STRATEGY_TIE_BREAK_ONLY":
            raise ValueError("calibration cannot become truth or evidence")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("calibration authority_effect must be None")
        if self.schema_version != "core.oeas.adversary.calibration-receipt.v1":
            raise ValueError("unsupported calibration receipt schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.calibration_id and self.calibration_id != expected:
            raise ValueError("calibration_id does not match canonical content")
        object.__setattr__(self, "calibration_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "observed_gate_results": list(self.observed_gate_results),
            "observed_defect_classes": list(self.observed_defect_classes),
            "actual_resource_units": self.actual_resource_units,
            "observed_success": self.observed_success,
            "bounded_confidence_bps": self.bounded_confidence_bps,
            "absolute_error_bps": self.absolute_error_bps,
            "use_scope": self.use_scope,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "calibration_id": self.calibration_id}


def calibrate_prediction(
    prediction: PredictionReceiptV1,
    *,
    observed_gate_results: tuple[str, ...],
    observed_defect_classes: tuple[str, ...],
    actual_resource_units: int,
    observed_success: bool,
) -> CalibrationReceiptV1:
    if type(prediction) is not PredictionReceiptV1:
        raise TypeError("prediction must be exact PredictionReceiptV1")
    return CalibrationReceiptV1(
        prediction_id=prediction.prediction_id,
        observed_gate_results=observed_gate_results,
        observed_defect_classes=observed_defect_classes,
        actual_resource_units=actual_resource_units,
        observed_success=observed_success,
        bounded_confidence_bps=prediction.bounded_confidence_bps,
        absolute_error_bps=abs(
            prediction.bounded_confidence_bps - (10_000 if observed_success else 0)
        ),
    )


@dataclass(frozen=True, slots=True)
class AdversarySeatBindingV1:
    seat_id: str
    agent_id: str
    agent_license_id: str
    capability_slice_ref: str
    operad_signature_ref: str
    licensed_operation_ids: tuple[str, ...]
    licensed_colours: tuple[str, ...]

    def __post_init__(self) -> None:
        identifier(self.seat_id, "seat_id")
        identifier(self.agent_id, "agent_id")
        digest(self.agent_license_id, "agent_license_id")
        digest(self.capability_slice_ref, "capability_slice_ref")
        digest(self.operad_signature_ref, "operad_signature_ref")
        object.__setattr__(
            self,
            "licensed_operation_ids",
            string_tuple(
                self.licensed_operation_ids,
                "licensed_operation_ids",
                identifiers=True,
            ),
        )
        object.__setattr__(
            self,
            "licensed_colours",
            string_tuple(self.licensed_colours, "licensed_colours", identifiers=True),
        )
        if not self.licensed_operation_ids or not self.licensed_colours:
            raise ValueError("seat binding requires operations and colours")


@dataclass(frozen=True, slots=True)
class AdversarySeatResultV1:
    seat_id: str
    result: AgentResultV1

    def __post_init__(self) -> None:
        identifier(self.seat_id, "seat_id")
        if type(self.result) is not AgentResultV1:
            raise TypeError("seat result must contain exact AgentResultV1")


@dataclass(frozen=True, slots=True)
class AntiSkillGateReceiptV1:
    stage: str
    subject_id: str
    registry_id: str
    activation_profile_digest: str
    hit_ids: tuple[str, ...]
    disposition: str
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.adversary.anti-skill-gate-receipt.v1"
    receipt_id: str = ""

    def __post_init__(self) -> None:
        if self.stage not in ANTI_SKILL_STAGES:
            raise ValueError("anti-skill gate stage is not closed")
        digest(self.subject_id, "subject_id")
        digest(self.registry_id, "registry_id", allow_empty=True)
        digest(
            self.activation_profile_digest,
            "activation_profile_digest",
            allow_empty=True,
        )
        object.__setattr__(
            self, "hit_ids", string_tuple(self.hit_ids, "hit_ids", digests=True)
        )
        if self.disposition not in ANTI_SKILL_DISPOSITIONS:
            raise ValueError("anti-skill gate disposition is not closed")
        if (not self.registry_id or not self.activation_profile_digest) and (
            self.disposition != "HOLD" or self.hit_ids
        ):
            raise ValueError("an unavailable anti-skill profile must HOLD")
        if self.disposition == "CLEAR" and self.hit_ids:
            raise ValueError("a clear anti-skill gate cannot contain hits")
        if self.disposition in {"FINDING", "REFUSE"} and not self.hit_ids:
            raise ValueError("a non-clear anti-skill disposition requires hits")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("anti-skill gate authority_effect must be None")
        if self.schema_version != "core.oeas.adversary.anti-skill-gate-receipt.v1":
            raise ValueError("unsupported anti-skill gate receipt schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.receipt_id and self.receipt_id != expected:
            raise ValueError("receipt_id does not match canonical content")
        object.__setattr__(self, "receipt_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "subject_id": self.subject_id,
            "registry_id": self.registry_id,
            "activation_profile_digest": self.activation_profile_digest,
            "hit_ids": list(self.hit_ids),
            "disposition": self.disposition,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "receipt_id": self.receipt_id}


@dataclass(frozen=True, slots=True)
class InertMinedProposalV1:
    lane: str
    subject_ref: str
    evidence_refs: tuple[str, ...]
    statement: str
    status: str = "PROPOSED"
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.adversary.inert-mined-proposal.v1"
    proposal_id: str = ""

    def __post_init__(self) -> None:
        if self.lane not in MINED_LANES:
            raise ValueError("mined proposal lane is not closed")
        digest(self.subject_ref, "subject_ref")
        object.__setattr__(
            self,
            "evidence_refs",
            string_tuple(self.evidence_refs, "evidence_refs", digests=True),
        )
        if not self.evidence_refs:
            raise ValueError("mined proposal requires evidence")
        text(self.statement, "statement")
        if self.status != "PROPOSED":
            raise ValueError("mined proposal must remain PROPOSED")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("mined proposal authority_effect must be None")
        if self.schema_version != "core.oeas.adversary.inert-mined-proposal.v1":
            raise ValueError("unsupported mined proposal schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.proposal_id and self.proposal_id != expected:
            raise ValueError("proposal_id does not match canonical content")
        object.__setattr__(self, "proposal_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "lane": self.lane,
            "subject_ref": self.subject_ref,
            "evidence_refs": list(self.evidence_refs),
            "statement": self.statement,
            "status": self.status,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "proposal_id": self.proposal_id}


@dataclass(frozen=True, slots=True)
class AdversarySealPacketV1:
    run_receipt_id: str
    selection_proposal_id: str
    artifact_refs: tuple[str, ...]
    finding_refs: tuple[str, ...]
    valuation_receipt_ids: tuple[str, ...]
    prediction_receipt_ids: tuple[str, ...]
    calibration_receipt_ids: tuple[str, ...]
    anti_skill_gate_receipt_ids: tuple[str, ...]
    mined_proposals: tuple[InertMinedProposalV1, ...]
    draft_pr_text: str
    nonclaims: tuple[str, ...]
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.adversary.seal-packet.v1"
    packet_id: str = ""

    def __post_init__(self) -> None:
        for field in (
            "run_receipt_id",
            "selection_proposal_id",
        ):
            digest(getattr(self, field), field)
        for field in (
            "artifact_refs",
            "finding_refs",
            "valuation_receipt_ids",
            "prediction_receipt_ids",
            "calibration_receipt_ids",
            "anti_skill_gate_receipt_ids",
        ):
            object.__setattr__(
                self,
                field,
                string_tuple(getattr(self, field), field, digests=True),
            )
        if not self.artifact_refs or not self.valuation_receipt_ids:
            raise ValueError("seal packet requires artifacts and valuations")
        if type(self.mined_proposals) is not tuple or any(
            type(item) is not InertMinedProposalV1 for item in self.mined_proposals
        ):
            raise TypeError("mined_proposals must be an exact typed tuple")
        text(self.draft_pr_text, "draft_pr_text")
        object.__setattr__(self, "nonclaims", string_tuple(self.nonclaims, "nonclaims"))
        if not self.nonclaims:
            raise ValueError("seal packet requires nonclaims")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("seal packet authority_effect must be None")
        if self.schema_version != "core.oeas.adversary.seal-packet.v1":
            raise ValueError("unsupported Adversary seal packet schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.packet_id and self.packet_id != expected:
            raise ValueError("packet_id does not match canonical content")
        object.__setattr__(self, "packet_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "run_receipt_id": self.run_receipt_id,
            "selection_proposal_id": self.selection_proposal_id,
            "artifact_refs": list(self.artifact_refs),
            "finding_refs": list(self.finding_refs),
            "valuation_receipt_ids": list(self.valuation_receipt_ids),
            "prediction_receipt_ids": list(self.prediction_receipt_ids),
            "calibration_receipt_ids": list(self.calibration_receipt_ids),
            "anti_skill_gate_receipt_ids": list(self.anti_skill_gate_receipt_ids),
            "mined_proposals": [item.to_dict() for item in self.mined_proposals],
            "draft_pr_text": self.draft_pr_text,
            "nonclaims": list(self.nonclaims),
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "packet_id": self.packet_id}


__all__ = [
    "ANTI_SKILL_STAGES",
    "ANTI_SKILL_STAGE_ORDER",
    "AntiSkillGateReceiptV1",
    "CalibrationReceiptV1",
    "InertMinedProposalV1",
    "PredictionReceiptV1",
    "AdversarySealPacketV1",
    "AdversarySeatBindingV1",
    "AdversarySeatResultV1",
    "calibrate_prediction",
]
