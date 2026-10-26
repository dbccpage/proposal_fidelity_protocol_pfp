"""Profile-scoped anti-skill gates for the Woland factory."""

from __future__ import annotations

from omega_engine_operads.application.anti_skill.anti_skill_v2 import (
    ActiveAntiSkillRuntimeV1,
)
from omega_engine_operads.domain.anti_skills.anti_skill_v2 import (
    AntiSkillSubjectV1,
)

from .models import AntiSkillGateReceiptV1

TRUTH_BOUNDARY_TRIO = frozenset(
    {
        "truth-bounded-as-unrestricted",
        "truth-model-self-certification",
        "truth-proposal-authority-collapse",
    }
)
_SEVERITY = {"FINDING": 1, "HOLD": 2, "REFUSE": 3}


def evaluate_woland_anti_skill_gate(
    *,
    stage: str,
    subject: AntiSkillSubjectV1,
    runtime: ActiveAntiSkillRuntimeV1 | None,
) -> AntiSkillGateReceiptV1:
    """Detect only; no hit is repaired, admitted, or activated here."""

    if type(subject) is not AntiSkillSubjectV1:
        raise TypeError("subject must be exact AntiSkillSubjectV1")
    if runtime is None:
        return AntiSkillGateReceiptV1(
            stage=stage,
            subject_id=subject.subject_id,
            registry_id="",
            activation_profile_digest="",
            hit_ids=(),
            disposition="HOLD",
        )
    if type(runtime) is not ActiveAntiSkillRuntimeV1:
        raise TypeError("runtime must be exact ActiveAntiSkillRuntimeV1 or None")
    if set(runtime.profile.active_spec_ids) != TRUTH_BOUNDARY_TRIO:
        return AntiSkillGateReceiptV1(
            stage=stage,
            subject_id=subject.subject_id,
            registry_id=runtime.registry.registry_id,
            activation_profile_digest=runtime.profile.profile_digest,
            hit_ids=(),
            disposition="HOLD",
        )
    hits = runtime.evaluate(subject)
    disposition = (
        max((hit.disposition for hit in hits), key=_SEVERITY.__getitem__)
        if hits
        else "CLEAR"
    )
    return AntiSkillGateReceiptV1(
        stage=stage,
        subject_id=subject.subject_id,
        registry_id=runtime.registry.registry_id,
        activation_profile_digest=runtime.profile.profile_digest,
        hit_ids=tuple(hit.hit_id for hit in hits),
        disposition=disposition,
    )


__all__ = ["TRUTH_BOUNDARY_TRIO", "evaluate_woland_anti_skill_gate"]
