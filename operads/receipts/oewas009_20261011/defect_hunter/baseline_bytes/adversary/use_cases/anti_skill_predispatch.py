"""One pre-dispatch anti-skill boundary shared by both Adversary bout entrances.

This screens request metadata against an active OEWAS anti-skill profile. It is
not instruction admission, content verification, or OEEIS antibody admission.
AuthorityEffect: None.
"""

from __future__ import annotations

from operations.domain.rop.result import Err, Ok, Refusal, Result
from workflows_agents_skills.domain.anti_skills.anti_skill_v2 import (
    AntiSkillSubjectV1,
)

from ..domain.estate_ports import AntiSkillDecisionV1, AntiSkillGatePort
from ..domain.instruction_ingress import InstructionIngressReceiptV1, instruction_request_digest
from ..domain.models import AdversaryBoutRequestV1

_LOCUS = "adversary.use_cases.anti_skill_predispatch"


def bout_dispatch_subject(
    producer_id: str,
    request: AdversaryBoutRequestV1,
    instruction_receipt: InstructionIngressReceiptV1 | None = None,
) -> AntiSkillSubjectV1:
    """Bind the metadata subject to the request and, when present, its OEWAS plan."""
    request_key = instruction_request_digest(request)
    evidence_scope = (f"request:{request_key}",)
    if instruction_receipt is not None:
        if (
            type(instruction_receipt) is not InstructionIngressReceiptV1
            or instruction_receipt.request_digest != request_key
        ):
            raise ValueError("instruction receipt does not bind this bout request")
        evidence_scope += (
            f"plan:{instruction_receipt.plan_digest}",
            f"source:{instruction_receipt.source_snapshot_digest}",
            f"manifest:{instruction_receipt.admission_receipt_id}",
        )
    return AntiSkillSubjectV1(
        claim_scope=("adversary_bout_dispatch",),
        evidence_scope=evidence_scope,
        producer_identity=producer_id,
        verifier_identity="unbound",
        claim_mode="PROPOSAL",
        requested_effect="ACTION_LICENSE" if request.request_external_admission else "NONE",
        approval_reference="",
        nonclaims=("No bout or checker evidence exists before dispatch.",),
    )


def require_pre_dispatch_clear(
    gate: AntiSkillGatePort | None,
    producer_id: str,
    request: AdversaryBoutRequestV1,
    instruction_receipt: InstructionIngressReceiptV1 | None = None,
) -> Result[AntiSkillDecisionV1, Refusal]:
    """Refuse unless an active profile cleared this request and optional plan."""
    if gate is None:
        return Err(Refusal(
            "ANTI_SKILL_PRE_DISPATCH_UNBOUND",
            "no active anti-skill gate is bound",
            _LOCUS,
        ))
    try:
        subject = bout_dispatch_subject(producer_id, request, instruction_receipt)
    except (TypeError, ValueError) as exc:
        return Err(Refusal(
            "ANTI_SKILL_PLAN_BINDING_INVALID",
            f"pre-dispatch subject could not bind the plan: {type(exc).__name__}",
            _LOCUS,
        ))
    try:
        screened = gate.evaluate("PRE_DISPATCH", subject.to_dict())
    except Exception as exc:
        return Err(Refusal(
            "ANTI_SKILL_PRE_DISPATCH_FAILED",
            f"anti-skill gate raised {type(exc).__name__}",
            _LOCUS,
        ))
    if isinstance(screened, Err):
        return screened
    if not isinstance(screened, Ok) or type(screened.value) is not AntiSkillDecisionV1:
        return Err(Refusal(
            "ANTI_SKILL_PRE_DISPATCH_INVALID",
            "anti-skill gate returned no typed decision",
            _LOCUS,
        ))
    decision = screened.value
    if (
        decision.stage != "PRE_DISPATCH"
        or decision.subject_id != subject.subject_id
        or decision.disposition != "CLEAR"
        or not decision.registry_id
        or not decision.activation_profile_digest
        or not decision.receipt_id
    ):
        return Err(Refusal(
            "ANTI_SKILL_PRE_DISPATCH_UNCLEARED",
            f"pre-dispatch anti-skill disposition {decision.disposition} is not bound CLEAR",
            _LOCUS,
        ))
    return Ok(decision)


__all__ = ["bout_dispatch_subject", "require_pre_dispatch_clear"]
