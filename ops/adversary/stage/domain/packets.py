"""Typed work, proposal, challenge, and plan packets for the Adversary stage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import (
    AUTHORITY_EFFECT_NONE,
    digest,
    exact_bool,
    identifier,
    integer,
    semantic_id,
    string_tuple,
    text,
)
from .ddc import DdaStepV1
from .topology import RESULT_STATUSES, NodeAssignmentV1

CHALLENGE_KINDS = frozenset(
    {"LOGIC", "COUNTERMODEL", "PROVENANCE", "SECURITY", "TEST", "OWNERSHIP", "REPLAY"}
)


@dataclass(frozen=True, slots=True)
class WorkPacketV1:
    task_key: str
    scene_id: str
    objective: str
    input_artifact_refs: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    budget_units: int
    evaluator_epoch_id: str
    causal_parent_ids: tuple[str, ...] = ()
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.work-packet.v1"
    packet_id: str = ""

    def __post_init__(self) -> None:
        identifier(self.task_key, "task_key")
        identifier(self.scene_id, "scene_id")
        text(self.objective, "objective")
        object.__setattr__(
            self,
            "input_artifact_refs",
            string_tuple(self.input_artifact_refs, "input_artifact_refs", digests=True),
        )
        object.__setattr__(
            self,
            "acceptance_criteria",
            string_tuple(self.acceptance_criteria, "acceptance_criteria"),
        )
        if not self.acceptance_criteria:
            raise ValueError("work packet requires acceptance criteria")
        integer(self.budget_units, "budget_units", minimum=1)
        digest(self.evaluator_epoch_id, "evaluator_epoch_id")
        object.__setattr__(
            self,
            "causal_parent_ids",
            string_tuple(self.causal_parent_ids, "causal_parent_ids", digests=True),
        )
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("work packet authority_effect must be None")
        if self.schema_version != "core.oeas.work-packet.v1":
            raise ValueError("unsupported work packet schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.packet_id and self.packet_id != expected:
            raise ValueError("packet_id does not match canonical content")
        object.__setattr__(self, "packet_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "task_key": self.task_key,
            "scene_id": self.scene_id,
            "objective": self.objective,
            "input_artifact_refs": list(self.input_artifact_refs),
            "acceptance_criteria": list(self.acceptance_criteria),
            "budget_units": self.budget_units,
            "evaluator_epoch_id": self.evaluator_epoch_id,
            "causal_parent_ids": list(self.causal_parent_ids),
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "packet_id": self.packet_id}


@dataclass(frozen=True, slots=True)
class CandidateProposalV1:
    producer_agent_id: str
    work_packet_id: str
    artifact_refs: tuple[str, ...]
    prediction_receipt_id: str
    nonclaims: tuple[str, ...]
    proposed_dda_step: DdaStepV1 | None = None
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.candidate-proposal.v1"
    candidate_id: str = ""

    def __post_init__(self) -> None:
        identifier(self.producer_agent_id, "producer_agent_id")
        digest(self.work_packet_id, "work_packet_id")
        object.__setattr__(
            self,
            "artifact_refs",
            string_tuple(self.artifact_refs, "artifact_refs", digests=True),
        )
        if not self.artifact_refs:
            raise ValueError("candidate proposal requires artifacts")
        digest(self.prediction_receipt_id, "prediction_receipt_id")
        object.__setattr__(self, "nonclaims", string_tuple(self.nonclaims, "nonclaims"))
        if not self.nonclaims:
            raise ValueError("candidate proposal requires nonclaims")
        if (
            self.proposed_dda_step is not None
            and type(self.proposed_dda_step) is not DdaStepV1
        ):
            raise TypeError("proposed_dda_step must be an exact DdaStepV1 or None")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("candidate proposal authority_effect must be None")
        if self.schema_version != "core.oeas.candidate-proposal.v1":
            raise ValueError("unsupported candidate proposal schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.candidate_id and self.candidate_id != expected:
            raise ValueError("candidate_id does not match canonical content")
        object.__setattr__(self, "candidate_id", expected)

    def _payload(self) -> dict[str, Any]:
        payload = {
            "producer_agent_id": self.producer_agent_id,
            "work_packet_id": self.work_packet_id,
            "artifact_refs": list(self.artifact_refs),
            "prediction_receipt_id": self.prediction_receipt_id,
            "nonclaims": list(self.nonclaims),
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }
        if self.proposed_dda_step is not None:
            payload["proposed_dda_step"] = self.proposed_dda_step.to_dict()
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "candidate_id": self.candidate_id}


@dataclass(frozen=True, slots=True)
class ChallengeV1:
    candidate_id: str
    critic_agent_id: str
    trust_domain: str
    challenge_kind: str
    statement: str
    evidence_refs: tuple[str, ...]
    blocking: bool
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.challenge.v1"
    challenge_id: str = ""

    def __post_init__(self) -> None:
        digest(self.candidate_id, "candidate_id")
        identifier(self.critic_agent_id, "critic_agent_id")
        identifier(self.trust_domain, "trust_domain")
        if self.challenge_kind not in CHALLENGE_KINDS:
            raise ValueError("challenge_kind is not closed")
        text(self.statement, "statement")
        object.__setattr__(
            self,
            "evidence_refs",
            string_tuple(self.evidence_refs, "evidence_refs", digests=True),
        )
        if not self.evidence_refs:
            raise ValueError("challenge requires evidence")
        exact_bool(self.blocking, "blocking")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("challenge authority_effect must be None")
        if self.schema_version != "core.oeas.challenge.v1":
            raise ValueError("unsupported challenge schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.challenge_id and self.challenge_id != expected:
            raise ValueError("challenge_id does not match canonical content")
        object.__setattr__(self, "challenge_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "critic_agent_id": self.critic_agent_id,
            "trust_domain": self.trust_domain,
            "challenge_kind": self.challenge_kind,
            "statement": self.statement,
            "evidence_refs": list(self.evidence_refs),
            "blocking": self.blocking,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "challenge_id": self.challenge_id}


@dataclass(frozen=True, slots=True)
class AgentResultV1:
    agent_id: str
    trust_domain: str
    scene_id: str
    work_packet_id: str
    status: str
    candidate_ids: tuple[str, ...] = ()
    challenge_ids: tuple[str, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    residual_codes: tuple[str, ...] = ()
    causal_parent_ids: tuple[str, ...] = ()
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.agent-result.v1"
    result_id: str = ""

    def __post_init__(self) -> None:
        identifier(self.agent_id, "agent_id")
        identifier(self.trust_domain, "trust_domain")
        identifier(self.scene_id, "scene_id")
        digest(self.work_packet_id, "work_packet_id")
        if self.status not in RESULT_STATUSES:
            raise ValueError("agent result status is not closed")
        for field in (
            "candidate_ids",
            "challenge_ids",
            "artifact_refs",
            "causal_parent_ids",
        ):
            object.__setattr__(
                self,
                field,
                string_tuple(getattr(self, field), field, digests=True),
            )
        object.__setattr__(
            self,
            "residual_codes",
            string_tuple(self.residual_codes, "residual_codes", identifiers=True),
        )
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("agent result authority_effect must be None")
        if self.schema_version != "core.oeas.agent-result.v1":
            raise ValueError("unsupported agent result schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.result_id and self.result_id != expected:
            raise ValueError("result_id does not match canonical content")
        object.__setattr__(self, "result_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "trust_domain": self.trust_domain,
            "scene_id": self.scene_id,
            "work_packet_id": self.work_packet_id,
            "status": self.status,
            "candidate_ids": list(self.candidate_ids),
            "challenge_ids": list(self.challenge_ids),
            "artifact_refs": list(self.artifact_refs),
            "residual_codes": list(self.residual_codes),
            "causal_parent_ids": list(self.causal_parent_ids),
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "result_id": self.result_id}


@dataclass(frozen=True, slots=True)
class MetaSkillPolicyV1:
    policy_name: str
    meta_skill_ids: tuple[str, ...]
    selectable_operation_ids: tuple[str, ...]
    phi_blind: bool = True
    path2_requires_equivalence_evidence: bool = True
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.meta-skill-policy.v1"
    policy_id: str = ""

    def __post_init__(self) -> None:
        identifier(self.policy_name, "policy_name")
        object.__setattr__(
            self,
            "meta_skill_ids",
            string_tuple(self.meta_skill_ids, "meta_skill_ids", identifiers=True),
        )
        object.__setattr__(
            self,
            "selectable_operation_ids",
            string_tuple(
                self.selectable_operation_ids,
                "selectable_operation_ids",
                identifiers=True,
            ),
        )
        if not self.meta_skill_ids or not self.selectable_operation_ids:
            raise ValueError("meta-skill policy requires skills and operations")
        if type(self.phi_blind) is not bool or not self.phi_blind:
            raise ValueError("meta-skills must remain Phi-blind")
        if (
            type(self.path2_requires_equivalence_evidence) is not bool
            or not self.path2_requires_equivalence_evidence
        ):
            raise ValueError("Path2 must require admitted equivalence evidence")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("meta-skill policy authority_effect must be None")
        if self.schema_version != "core.oeas.meta-skill-policy.v1":
            raise ValueError("unsupported meta-skill policy schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.policy_id and self.policy_id != expected:
            raise ValueError("policy_id does not match canonical content")
        object.__setattr__(self, "policy_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "policy_name": self.policy_name,
            "meta_skill_ids": list(self.meta_skill_ids),
            "selectable_operation_ids": list(self.selectable_operation_ids),
            "phi_blind": self.phi_blind,
            "path2_requires_equivalence_evidence": self.path2_requires_equivalence_evidence,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "policy_id": self.policy_id}


@dataclass(frozen=True, slots=True)
class LicensedWorkflowPlanV1:
    plan_name: str
    catalog_id: str
    assignments: tuple[NodeAssignmentV1, ...]
    normalized_operation_ids: tuple[str, ...]
    path2_evidence_ids: tuple[str, ...] = ()
    status: str = "PROPOSED"
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.licensed-workflow-plan.v1"
    plan_id: str = ""

    def __post_init__(self) -> None:
        identifier(self.plan_name, "plan_name")
        digest(self.catalog_id, "catalog_id")
        if type(self.assignments) is not tuple or not self.assignments:
            raise TypeError("assignments must be a nonempty exact tuple")
        if any(type(item) is not NodeAssignmentV1 for item in self.assignments):
            raise TypeError("workflow plan contains a non-exact assignment")
        keys = {(item.scene_id, item.seat_id) for item in self.assignments}
        if len(keys) != len(self.assignments):
            raise ValueError(
                "workflow plan assignments must be unique per scene and seat"
            )
        object.__setattr__(
            self,
            "normalized_operation_ids",
            string_tuple(
                self.normalized_operation_ids,
                "normalized_operation_ids",
                identifiers=True,
            ),
        )
        if not self.normalized_operation_ids:
            raise ValueError("workflow plan requires normalized operations")
        object.__setattr__(
            self,
            "path2_evidence_ids",
            string_tuple(self.path2_evidence_ids, "path2_evidence_ids", digests=True),
        )
        if self.status != "PROPOSED":
            raise ValueError("workflow plan status must remain PROPOSED")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("workflow plan authority_effect must be None")
        if self.schema_version != "core.oeas.licensed-workflow-plan.v1":
            raise ValueError("unsupported workflow plan schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.plan_id and self.plan_id != expected:
            raise ValueError("plan_id does not match canonical content")
        object.__setattr__(self, "plan_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "plan_name": self.plan_name,
            "catalog_id": self.catalog_id,
            "assignments": [item.to_dict() for item in self.assignments],
            "normalized_operation_ids": list(self.normalized_operation_ids),
            "path2_evidence_ids": list(self.path2_evidence_ids),
            "status": self.status,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "plan_id": self.plan_id}


__all__ = [
    "AgentResultV1",
    "CandidateProposalV1",
    "ChallengeV1",
    "LicensedWorkflowPlanV1",
    "MetaSkillPolicyV1",
    "WorkPacketV1",
]
