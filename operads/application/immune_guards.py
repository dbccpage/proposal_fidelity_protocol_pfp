"""Immune-guarded operad operations, through the `ImmuneScreenPort`.

These used to live in OEWAS's domain and import the OEEIS domain directly
(`domain/workflow_graph.py`, `domain/planar_substitution.py`,
`domain/capability_catalog_v1.py`). The domain now holds only the operad
algebra; the immune decision is asked of OEEIS through the port, and the
concrete adapter is `infrastructure/immune/oeeis_immune_adapter.py`.
"""

from __future__ import annotations

from typing import Sequence

from ..domain.capability_catalog_v1 import CapabilityCatalogRefusal, SkillCapabilityV1
from ..domain.planar_substitution import OperadOperation, SubstitutionError, substitute
from ..domain.workflow_graph import DangerSignalPolicy, WorkflowFinding, WorkflowReport
from .ports.immune_screen_port import (
    DetectorIdentity,
    DetectorMatch,
    HostDangerObservation,
    ImmuneEvidenceRefusal,
    ImmuneScreenPort,
    SensorReading,
)


def immune_guarded_substitute(
    theta: OperadOperation,
    index: int,
    phi: OperadOperation,
    *,
    immune: ImmuneScreenPort,
    detector: DetectorIdentity,
    matches: Sequence[DetectorMatch] = (),
    danger: HostDangerObservation | None = None,
) -> OperadOperation:
    """`substitute`, refused when the danger gate suppresses or refuses the evidence.

    A suppression is DANGER_GATE_SUPPRESSION; refused evidence (for example a
    Signal 2 derived from the matches) carries the immune system's code, such
    as TWO_SIGNAL_COLLAPSE.
    """
    try:
        verdict = immune.danger_verdict(matches, danger, detector=detector)
    except ImmuneEvidenceRefusal as exc:
        raise SubstitutionError(exc.code, exc.detail) from exc
    if verdict.blocks:
        raise SubstitutionError(
            "DANGER_GATE_SUPPRESSION",
            f"Substitution of {phi.name} into {theta.name} slot {index} suppressed: {verdict.rationale}",
        )
    return substitute(theta, index, phi)


def allosteric_consensus_substitute(
    theta: OperadOperation,
    index: int,
    phi: OperadOperation,
    readings: Sequence[SensorReading],
    *,
    immune: ImmuneScreenPort,
) -> OperadOperation:
    """`substitute`, refused with ALLOSTERIC_QUORUM_NOT_MET below the immune gate's threshold."""
    try:
        verdict = immune.quorum_verdict(readings)
    except ImmuneEvidenceRefusal as exc:
        raise SubstitutionError(exc.code, exc.detail) from exc
    if verdict.blocks:
        raise SubstitutionError(
            "ALLOSTERIC_QUORUM_NOT_MET",
            f"Substitution of {phi.name} into {theta.name} slot {index} refused: {verdict.rationale}",
        )
    return substitute(theta, index, phi)


def validate_workflow_immune_guard(
    report: WorkflowReport,
    policy: DangerSignalPolicy,
    *,
    immune: ImmuneScreenPort,
    detector: DetectorIdentity,
    matches: Sequence[DetectorMatch] = (),
    danger: HostDangerObservation | None = None,
) -> WorkflowReport:
    """Add a finding when the policy enforces the gate and it suppresses or refuses the evidence."""
    if type(policy) is not DangerSignalPolicy:
        raise TypeError("policy must be an exact DangerSignalPolicy")
    if not policy.enforce_danger_gate:
        return report
    try:
        verdict = immune.danger_verdict(matches, danger, detector=detector)
    except ImmuneEvidenceRefusal as exc:
        code, detail = exc.code, exc.detail
    else:
        if not verdict.blocks:
            return report
        code, detail = "DANGER_GATE_SUPPRESSION", verdict.rationale
    finding = WorkflowFinding(workflow_id=report.workflow_id, code=code, detail=detail)
    return WorkflowReport(
        workflow_id=report.workflow_id,
        declared=report.declared,
        composed=None,
        findings=report.findings + (finding,),
    )


def admit_skill_with_thymus(
    skill: SkillCapabilityV1,
    *,
    immune: ImmuneScreenPort,
) -> SkillCapabilityV1:
    """Refuse a skill whose trigger phrases match the immune system's self panel.

    Triggers are literal phrases, not regexes ("c++" is not a repetition error
    and "." does not match every fixture); a skill with no non-blank trigger is
    screened by its name.
    """
    if type(skill) is not SkillCapabilityV1:
        raise TypeError("skill must be an exact SkillCapabilityV1")
    phrases = [trigger for trigger in skill.declared_triggers if trigger.strip()]
    if not phrases:
        phrases = [skill.name]
    verdict = immune.trigger_tolerance_verdict(f"SKILL-GATE-{skill.skill_id}", phrases)
    if verdict.blocks and verdict.decision == "REFUSED":
        raise CapabilityCatalogRefusal(
            "AUTOIMMUNE_REACTION_ERROR",
            skill.skill_id,
            f"skill triggers match healthy self-tissue: {verdict.rationale}",
        )
    if verdict.blocks:
        raise CapabilityCatalogRefusal(
            "TRIGGER_NOT_SCREENABLE",
            skill.skill_id,
            f"skill triggers could not be screened: {verdict.rationale}",
        )
    return skill


__all__ = [
    "admit_skill_with_thymus",
    "allosteric_consensus_substitute",
    "immune_guarded_substitute",
    "validate_workflow_immune_guard",
]
