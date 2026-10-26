from __future__ import annotations

from typing import Mapping, Sequence

from omega_engine_governance.domain.swarm_control.cas_land_license import (
    CasHeadDriftError,
    issue_cas_land_license,
    validate_cas_land_license,
)
from omega_engine_governance.domain.swarm_control.evidence_freshness_rebind import (
    EvidenceFreshnessAssessment,
    EvidenceFreshnessState,
    assess_evidence_freshness,
)
from omega_engine_governance.domain.swarm_control.universal_transport_receipt import (
    MutationShape,
    TransportReceiptError,
    TransportReceiptStatus,
    UniversalTransportReceipt,
)


class StrictModeMeasurementError(Exception):
    """Raised in STRICT mode when any mandatory measurement is NOT_MEASURED."""
    pass


class SelfJudgeTamperingError(Exception):
    """Raised when a candidate packet attempts to mutate its own admission gate or evaluators."""
    pass


#: Loci a candidate may not write, because writing them is a candidate editing
#: its own judge.
#:
#: The previous list was `("omega_engine_governance/", ".canon/rules/",
#: "quality_gates.md")`, which was wrong in both directions at once.
#:
#: Too broad: a bare `omega_engine_governance/` prefix blocked every write
#: anywhere under governance, including plain domain value objects and including
#: the files this very package consists of — so no swarm agent could land a
#: governance change at all.
#:
#: Too narrow: `.canon/rules/` does not exist in this repository, and the roots
#: that actually hold the skills, rules and gates were unlisted. A write set of
#: `['omega_engine_operads/skills/sprint-execution/SKILL.md',
#: '.claude/rules/authority/rl_gtla_rules_rubric.md',
#: 'omega_engine_operations/infrastructure/cicd/local_ci_host.py']` passed clean.
#: The canonical rule tree is `omega_engine_operads/rules/`. Protecting only
#: `.claude/rules/` refused the mirror and let the canon through.
#:
#: These are the real loci. `REQUIRED_PROTECTED_PATHS` in
#: `swarm_bootstrap_document_control` enumerates file-ownership ground for the
#: bootstrap gate; this tuple is the write-prefix gate.
PROTECTED_GOVERNANCE_PATTERNS: tuple[str, ...] = (
    # The skill estate, the canonical rule tree, and the skill mirrors: a
    # candidate rewriting one of these is rewriting the procedure it will be
    # judged by.
    "omega_engine_operads/skills/",
    "omega_engine_operads/workflows/",
    "omega_engine_operads/rules/",
    ".agents/skills/",
    ".claude/skills/",
    ".claude/rules/",
    ".codex/skills/",
    ".grok/skills/",
    # The gates and the review implementation that run against the candidate.
    # The local CI host lives under infrastructure, not use_cases.
    "omega_engine_operations/use_cases/cicd/",
    "omega_engine_operations/infrastructure/cicd/",
    "omega_engine_governance/infrastructure/cicd_process_flow/",
    # The contracts tree, the regime root the scanner reads, and the
    # swarm bootstrap control itself. `contract_scan_directories` scans
    # `_law/` when that directory exists; `contracts/` stays protected.
    "omega_engine_governance/contracts/",
    "omega_engine_governance/_law/",
    "omega_engine_governance/infrastructure/swarm_control/",
    # Sprint quality gates.
    "quality_gates.md",
)


def evaluate_chaos_head_change(
    candidate_id: str,
    bound_head: str,
    drifted_head: str,
) -> EvidenceFreshnessAssessment:
    """Evaluates chaos scenario where mainline head moves during review."""
    assessment = assess_evidence_freshness(
        obligation_id=f"review:{candidate_id}",
        bound_head=bound_head,
        observed_head=drifted_head,
    )
    if assessment.state != EvidenceFreshnessState.STALE_AFTER_HEAD_CHANGE:
        raise AssertionError(f"Expected STALE_AFTER_HEAD_CHANGE, got {assessment.state}")

    # Attempting to validate a land license against drifted head must fail closed
    license_obj = issue_cas_land_license(candidate_id, bound_head, current_epoch=100.0)
    try:
        validate_cas_land_license(license_obj, observed_head_sha=drifted_head, current_epoch=105.0)
        raise AssertionError("Expected CasHeadDriftError was not raised")
    except CasHeadDriftError:
        pass

    return assessment


def evaluate_chaos_transport_na(
    source_path: str,
    destination_path: str,
) -> bool:
    """Evaluates chaos scenario attempting to mark a moved path as NOT_APPLICABLE."""
    try:
        UniversalTransportReceipt(
            receipt_id="chaos_na_test",
            source_path=source_path,
            destination_path=destination_path,
            mutation_shape=MutationShape.PATH_ONLY,
            source_digest="sha_same",
            destination_digest="sha_same",
            status=TransportReceiptStatus.NOT_APPLICABLE,
        )
        raise AssertionError("Expected TransportReceiptError was not raised")
    except TransportReceiptError:
        return True


def evaluate_chaos_measurement_strict(
    measurements: Mapping[str, str],
    *,
    strict: bool = True,
) -> bool:
    """Evaluates chaos scenario where a required measurement is NOT_MEASURED."""
    unmeasured = [metric for metric, val in measurements.items() if val == "NOT_MEASURED"]
    if strict and unmeasured:
        raise StrictModeMeasurementError(
            f"STRICT mode refusal: Required metrics are NOT_MEASURED: {', '.join(unmeasured)}"
        )
    return True


def evaluate_chaos_self_judge(
    candidate_id: str,
    write_set: Sequence[str],
) -> bool:
    """Evaluates chaos scenario where candidate write set modifies protected gate/evaluator loci."""
    tampering = [
        path for path in write_set
        if any(protected in path for protected in PROTECTED_GOVERNANCE_PATTERNS)
    ]
    if tampering:
        raise SelfJudgeTamperingError(
            f"Self-judge tampering blocked: Candidate '{candidate_id}' cannot mutate protected gates: {tampering}"
        )
    return True
