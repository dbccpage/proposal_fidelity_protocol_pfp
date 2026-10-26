"""One pre-dispatch anti-skill boundary shared by both Woland bout entrances.

This screens request metadata against an active OEWAS anti-skill profile. It is
not instruction admission, content verification, or OEEIS antibody admission.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_operads.domain.anti_skills.anti_skill_v2 import (
    AntiSkillSubjectV1,
)

from ..domain.estate_ports import AntiSkillDecisionV1, AntiSkillGatePort
from ..domain.instruction_ingress import InstructionIngressReceiptV1, instruction_request_digest
from ..domain.models import WolandBoutRequestV1

_LOCUS = "omega_engine_woland.use_cases.anti_skill_predispatch"


def bout_dispatch_subject(
    producer_id: str,
    request: WolandBoutRequestV1,
    instruction_receipt: InstructionIngressReceiptV1 | None = None,
) -> AntiSkillSubjectV1:
    """Bind the metadata subject to the request and, when present, its OEWAS plan."""
    request_key = instruction_request_digest(request)
    evidence_scope = (f"task:{request.task_key}", f"request:{request_key}")
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
        claim_scope=("woland_bout_dispatch",),
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
    request: WolandBoutRequestV1,
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
        or decision.hit_ids
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


def require_candidate_clear(
    gate: AntiSkillGatePort,
    producer_id: str,
    request: WolandBoutRequestV1,
    stage: str,
    candidate_id: str,
    candidate_bytes: bytes,
    previous: AntiSkillDecisionV1 | None = None,
) -> Result[AntiSkillDecisionV1, Refusal]:
    """Screen consumed candidate bytes without granting verification or admission.

    Each stage has a distinct subject. All decisions in the bout must use the
    same registry and activation profile as the initial bound decision.
    """
    if stage not in ("POST_PRODUCTION", "PRE_SELECTION"):
        return Err(Refusal("ANTI_SKILL_CANDIDATE_STAGE_INVALID", stage, _LOCUS))
    subject = AntiSkillSubjectV1(
        claim_scope=("candidate_patch",),
        evidence_scope=(
            f"task:{request.task_key}",
            f"request:{instruction_request_digest(request)}",
            f"candidate:sha256:{hashlib.sha256(candidate_bytes).hexdigest()}",
            f"candidate_id:{candidate_id}",
            f"stage:{stage}",
        ),
        producer_identity=producer_id,
        verifier_identity="unbound",
        claim_mode="PROPOSAL",
        requested_effect="NONE",
        approval_reference="",
        nonclaims=("Metadata screening is not candidate verification or admission.",),
    )
    try:
        screened = gate.evaluate(stage, subject.to_dict())
    except Exception as exc:
        return Err(Refusal(
            "ANTI_SKILL_CANDIDATE_FAILED",
            f"{stage} anti-skill gate raised {type(exc).__name__}",
            _LOCUS,
        ))
    if isinstance(screened, Err):
        return screened
    if not isinstance(screened, Ok) or type(screened.value) is not AntiSkillDecisionV1:
        return Err(Refusal(
            "ANTI_SKILL_CANDIDATE_INVALID", "anti-skill gate returned no typed decision", _LOCUS
        ))
    decision = screened.value
    if (
        decision.stage != stage
        or decision.subject_id != subject.subject_id
        or decision.disposition != "CLEAR"
        or decision.hit_ids
        or not decision.registry_id
        or not decision.activation_profile_digest
        or not decision.receipt_id
        or (
            previous is not None
            and (
                decision.registry_id != previous.registry_id
                or decision.activation_profile_digest != previous.activation_profile_digest
            )
        )
    ):
        return Err(Refusal(
            "ANTI_SKILL_CANDIDATE_UNCLEARED",
            f"{stage} decision is not CLEAR for this candidate and activation snapshot",
            _LOCUS,
        ))
    return Ok(decision)


__all__ = ["bout_dispatch_subject", "require_pre_dispatch_clear", "require_candidate_clear"]
