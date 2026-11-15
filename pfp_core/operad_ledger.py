"""Adapter wiring EIS/PCIV defect outcomes and cemetery headstones to pfp_operads ledger.

AuthorityEffect: None.
Governed by core_operad_canon registered taxonomies.
Only the host binary writes to the ledger: records are checked in Rust before
appending to the hash chain.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from pfp.infrastructure import operad_host
from pfp_core.exclusions import (
    ExclusionHypothesisV1,
    HeadstoneExclusionPolicyV1,
    headstone_exclusion,
)

CANONICAL_PHARMACY_FAILURE_CLASSES: frozenset[str] = frozenset(
    {
        "SELF_CERTIFICATION",
        "FAKE_RECEIPT",
        "CONCLUSION_PRELOAD",
        "SCHEMA_SEMANTIC_LAUNDERING",
        "THEOREM_NAME_LAUNDERING",
        "OPTIMALITY_HALLUCINATION",
        "COMPLEXITY_HALLUCINATION",
        "BRANCH_DROP_EXHAUSTION",
        "PERSONA_AUTHORITY_LEAK",
        "PRIVATE_COT_DEPENDENCY",
        "VERSION_DUPLICATION",
        "DETECT_REPAIR_COUPLING",
    }
)

CANONICAL_ANTI_SKILL_FAILURE_CLASSES: frozenset[str] = frozenset(
    {
        "SemanticHallucination",
        "ApproximateContradiction",
        "ToyPromotion",
        "UnmechanizedProofClaim",
        "SelfContradiction",
        "DualityGapNonZero",
        "BoundaryLeakage",
        "UnboundPortAssumption",
        "CounterfeitExactness",
        "SycophanticAgreement",
        "StructuralNonFit",
        "StaleCensusReference",
    }
)

CANONICAL_FAILURE_CLASSES: frozenset[str] = CANONICAL_PHARMACY_FAILURE_CLASSES | CANONICAL_ANTI_SKILL_FAILURE_CLASSES

CANONICAL_CAPABILITY_KINDS: frozenset[str] = frozenset(
    {
        "skill",
        "anti_skill",
        "rule",
        "helpful_pattern",
        "anti_pattern",
        "antibody",
    }
)

DDC_TRACE_LETTERS: frozenset[str] = frozenset(
    {
        "E",
        "R",
        "C",
        "I",
        "Λ",
        "D",
        "M",
        "T",
    }
)

CAUSE_OF_DEATH_MAP: Mapping[str, str] = {
    "REFUSED_FLATTERY_CONTEXT_SMUGGLE": "SycophanticAgreement",
    "FLATTERY": "SycophanticAgreement",
    "SYCOPHANCY": "SycophanticAgreement",
    "SYNTAX_ERROR": "StructuralNonFit",
    "STRUCTURAL_ERROR": "StructuralNonFit",
    "LAYER_VIOLATION": "BoundaryLeakage",
    "BOUNDARY_LEAK": "BoundaryLeakage",
    "CLEAN_ARCHITECTURE_VIOLATION": "BoundaryLeakage",
    "DIRECT_IMPORT": "BoundaryLeakage",
    "EMPTY_RESPONSE": "StructuralNonFit",
    "HALLUCINATION": "SemanticHallucination",
    "SELF_CONTRADICTION": "SelfContradiction",
    "UNBOUND_PORT": "UnboundPortAssumption",
    "DUALITY_GAP": "DualityGapNonZero",
    "CHSH_VIOLATION": "DualityGapNonZero",
    "FLOAT_IN_EXACT_PATH": "CounterfeitExactness",
    "UNREDUCED_RATIONAL": "CounterfeitExactness",
    "STALE_CENSUS": "StaleCensusReference",
    "TOY_PROMOTION": "ToyPromotion",
    "UNMECHANIZED_PROOF": "UnmechanizedProofClaim",
    "APPROXIMATE_CONTRADICTION": "ApproximateContradiction",
    "FAKERECEIPT": "FAKE_RECEIPT",
    "SELFCERTIFICATION": "SELF_CERTIFICATION",
    "CONCLUSIONPRELOAD": "CONCLUSION_PRELOAD",
    "OPTIMALITYHALLUCINATION": "OPTIMALITY_HALLUCINATION",
    "COMPLEXITYHALLUCINATION": "COMPLEXITY_HALLUCINATION",
    "BRANCHDROPEXHAUSTION": "BRANCH_DROP_EXHAUSTION",
    "PERSONAAUTHORITYLEAK": "PERSONA_AUTHORITY_LEAK",
    "PRIVATECOTDEPENDENCY": "PRIVATE_COT_DEPENDENCY",
    "VERSIONDUPLICATION": "VERSION_DUPLICATION",
    "DETECTREPAIRCOUPLING": "DETECT_REPAIR_COUPLING",
    "SCHEMASEMANTICLAUNDERING": "SCHEMA_SEMANTIC_LAUNDERING",
    "THEOREMNAMELAUNDERING": "THEOREM_NAME_LAUNDERING",
}


class OperadLedgerError(ValueError):
    """An invalid ledger parameter or refusal."""


def resolve_failure_class(cause_or_class: str) -> str:
    """Map a cause-of-death or raw status string to a canon failure class."""
    if cause_or_class in CANONICAL_FAILURE_CLASSES:
        return cause_or_class
    if cause_or_class in CAUSE_OF_DEATH_MAP:
        return CAUSE_OF_DEATH_MAP[cause_or_class]
    normalized = cause_or_class.upper().replace(" ", "_").replace("-", "_")
    if normalized in CAUSE_OF_DEATH_MAP:
        return CAUSE_OF_DEATH_MAP[normalized]
    stripped = normalized.replace("_", "")
    if stripped in CAUSE_OF_DEATH_MAP:
        return CAUSE_OF_DEATH_MAP[stripped]
    for key, target in CAUSE_OF_DEATH_MAP.items():
        if key in normalized or key in stripped:
            return target
    return cause_or_class


def is_valid_evidence_sha256(digest: str) -> bool:
    """True if text is exactly 64 lowercase hexadecimal digits."""
    if not isinstance(digest, str) or len(digest) != 64:
        return False
    return all(c in "0123456789abcdef" for c in digest)


def is_valid_ddc_trace(trace: str) -> bool:
    """True if text is a non-empty word over the canonical DDC trace alphabet."""
    if not isinstance(trace, str) or not trace:
        return False
    return all(c in DDC_TRACE_LETTERS for c in trace)


def record_failure(
    ledger_path: Path | str,
    *,
    failure_id: str,
    workflow: str,
    run: str,
    failure_class: str,
    ddc_trace: str,
    evidence_sha256: str,
) -> dict[str, Any]:
    """Append a Record::Failure to the operad failure ledger.

    Returns the host outcome dictionary with status PASS or REFUSED.
    """
    record = {
        "kind": "failure",
        "id": str(failure_id),
        "workflow": str(workflow),
        "run": str(run),
        "failure_class": str(failure_class),
        "ddc_trace": str(ddc_trace),
        "evidence_sha256": str(evidence_sha256),
    }
    return operad_host.ledger("append", ledger_path, record)


def record_headstone(
    ledger_path: Path | str,
    headstone: Any,
    *,
    workflow: str,
    failure_class: str | None = None,
    ddc_trace: str = "CRM",
    failure_id: str | None = None,
) -> dict[str, Any]:
    """Convert a cemetery headstone into a canonical Record::Failure and append it."""
    if isinstance(headstone, Mapping):
        candidate_id = str(headstone.get("candidate_id", ""))
        run_key = str(headstone.get("run_key", ""))
        scene_id = str(headstone.get("scene_id", ""))
        cause_of_death = str(headstone.get("cause_of_death", ""))
        raw_sha = str(headstone.get("candidate_payload_sha256", ""))
        hs_id = headstone.get("headstone_id") or headstone.get("id")
    else:
        candidate_id = str(getattr(headstone, "candidate_id", ""))
        run_key = str(getattr(headstone, "run_key", ""))
        scene_id = str(getattr(headstone, "scene_id", ""))
        cause_of_death = str(getattr(headstone, "cause_of_death", ""))
        raw_sha = str(getattr(headstone, "candidate_payload_sha256", ""))
        hs_id = getattr(headstone, "headstone_id", None)

    if failure_id is not None:
        effective_id = str(failure_id)
    elif candidate_id and run_key:
        effective_id = f"{candidate_id}@{run_key}"
    elif hs_id:
        effective_id = str(hs_id)
    else:
        effective_id = f"{candidate_id or 'failure'}@run"

    resolved_class = str(failure_class) if failure_class is not None else resolve_failure_class(cause_of_death)

    stripped_sha = raw_sha.removeprefix("sha256:")
    evidence_sha256 = stripped_sha.lower() if is_valid_evidence_sha256(stripped_sha.lower()) else raw_sha

    return record_failure(
        ledger_path,
        failure_id=effective_id,
        workflow=workflow or scene_id or "default_workflow",
        run=run_key or "default_run",
        failure_class=resolved_class,
        ddc_trace=ddc_trace,
        evidence_sha256=evidence_sha256,
    )


def propose_candidate(
    ledger_path: Path | str,
    *,
    candidate_id: str,
    capability_kind: str,
    constraint: str,
    derived_from: Sequence[str] | Iterable[str],
) -> dict[str, Any]:
    """Append a Record::Candidate to the ledger."""
    record = {
        "kind": "candidate",
        "id": str(candidate_id),
        "capability_kind": str(capability_kind),
        "constraint": str(constraint),
        "derived_from": [str(x) for x in derived_from],
    }
    return operad_host.ledger("append", ledger_path, record)


def record_trial(
    ledger_path: Path | str,
    *,
    candidate_id: str,
    held_out: Sequence[str] | Iterable[str],
    baseline_correct: int,
    treated_correct: int,
    clean_panel_hits: int,
) -> dict[str, Any]:
    """Append a Record::Trial with exact non-negative integer counts (u32)."""
    for name, value in (
        ("baseline_correct", baseline_correct),
        ("treated_correct", treated_correct),
        ("clean_panel_hits", clean_panel_hits),
    ):
        if type(value) is not int or value < 0 or value > 0xFFFFFFFF:
            raise OperadLedgerError(f"{name} must be a non-negative 32-bit unsigned integer, got {value!r}")
    record = {
        "kind": "trial",
        "candidate": str(candidate_id),
        "held_out": [str(x) for x in held_out],
        "baseline_correct": baseline_correct,
        "treated_correct": treated_correct,
        "clean_panel_hits": clean_panel_hits,
    }
    return operad_host.ledger("append", ledger_path, record)


def record_admission(
    ledger_path: Path | str,
    *,
    candidate_id: str,
    trial_seq: int,
) -> dict[str, Any]:
    """Append a Record::Admission referencing the sequence index of a passed trial."""
    if type(trial_seq) is not int or trial_seq < 0:
        raise OperadLedgerError(f"trial_seq must be a non-negative int, got {trial_seq!r}")
    record = {
        "kind": "admission",
        "candidate": str(candidate_id),
        "trial": trial_seq,
    }
    return operad_host.ledger("append", ledger_path, record)


def record_retirement(
    ledger_path: Path | str,
    *,
    candidate_id: str,
    reason: str,
) -> dict[str, Any]:
    """Append a Record::Retirement permanently retiring a candidate."""
    record = {
        "kind": "retirement",
        "candidate": str(candidate_id),
        "reason": str(reason),
    }
    return operad_host.ledger("append", ledger_path, record)


def verify(ledger_path: Path | str) -> dict[str, Any]:
    """Verify the hash chain and entry sequence of the ledger file."""
    return operad_host.ledger("verify", ledger_path)


def admitted(ledger_path: Path | str) -> list[dict[str, Any]]:
    """Return the list of currently admitted rules from the ledger."""
    outcome = operad_host.ledger("admitted", ledger_path)
    if outcome.get("status") == "PASS":
        result = outcome.get("result", [])
        if isinstance(result, list):
            return result
    return []


def headstone_to_exclusion_hypothesis(
    headstone: Any,
    policy: HeadstoneExclusionPolicyV1,
    *,
    falsifier: str,
    falsifier_cost: int,
) -> ExclusionHypothesisV1 | None:
    """Adapt a cemetery headstone into an ExclusionHypothesisV1 for retest planning."""
    if isinstance(headstone, Mapping):
        candidate_id = str(headstone.get("candidate_id", ""))
        run_key = str(headstone.get("run_key", ""))
        cause_of_death = str(headstone.get("cause_of_death", ""))
        killing_seat_id = str(headstone.get("killing_seat_id", ""))
        hs_id = str(headstone.get("headstone_id") or headstone.get("id") or f"{candidate_id}@{run_key}")

        class _DictHeadstone:
            def __init__(self) -> None:
                self.headstone_id = hs_id
                self.candidate_id = candidate_id
                self.cause_of_death = cause_of_death
                self.killing_seat_id = killing_seat_id

        target_headstone = _DictHeadstone()
    else:
        target_headstone = headstone

    return headstone_exclusion(
        target_headstone,
        policy,
        falsifier=falsifier,
        falsifier_cost=falsifier_cost,
    )


class OperadLedgerAdapter:
    """Bridging adapter between EIS/PCIV defect outcomes and pfp_operads ledger records."""

    def __init__(self, ledger_path: Path | str | None = None) -> None:
        self.ledger_path = Path(ledger_path) if ledger_path is not None else None

    def _target_path(self, override_path: Path | str | None) -> Path | str:
        target = override_path if override_path is not None else self.ledger_path
        if target is None:
            raise OperadLedgerError("ledger_path must be specified")
        return target

    def record_failure(
        self,
        ledger_path: Path | str | None = None,
        *,
        failure_id: str,
        workflow: str,
        run: str,
        failure_class: str,
        ddc_trace: str,
        evidence_sha256: str,
    ) -> dict[str, Any]:
        return record_failure(
            self._target_path(ledger_path),
            failure_id=failure_id,
            workflow=workflow,
            run=run,
            failure_class=failure_class,
            ddc_trace=ddc_trace,
            evidence_sha256=evidence_sha256,
        )

    def record_headstone(
        self,
        headstone: Any,
        ledger_path: Path | str | None = None,
        *,
        workflow: str,
        failure_class: str | None = None,
        ddc_trace: str = "CRM",
        failure_id: str | None = None,
    ) -> dict[str, Any]:
        return record_headstone(
            self._target_path(ledger_path),
            headstone=headstone,
            workflow=workflow,
            failure_class=failure_class,
            ddc_trace=ddc_trace,
            failure_id=failure_id,
        )

    def propose_candidate(
        self,
        ledger_path: Path | str | None = None,
        *,
        candidate_id: str,
        capability_kind: str,
        constraint: str,
        derived_from: Sequence[str] | Iterable[str],
    ) -> dict[str, Any]:
        return propose_candidate(
            self._target_path(ledger_path),
            candidate_id=candidate_id,
            capability_kind=capability_kind,
            constraint=constraint,
            derived_from=derived_from,
        )

    def record_trial(
        self,
        ledger_path: Path | str | None = None,
        *,
        candidate_id: str,
        held_out: Sequence[str] | Iterable[str],
        baseline_correct: int,
        treated_correct: int,
        clean_panel_hits: int,
    ) -> dict[str, Any]:
        return record_trial(
            self._target_path(ledger_path),
            candidate_id=candidate_id,
            held_out=held_out,
            baseline_correct=baseline_correct,
            treated_correct=treated_correct,
            clean_panel_hits=clean_panel_hits,
        )

    def record_admission(
        self,
        ledger_path: Path | str | None = None,
        *,
        candidate_id: str,
        trial_seq: int,
    ) -> dict[str, Any]:
        return record_admission(
            self._target_path(ledger_path),
            candidate_id=candidate_id,
            trial_seq=trial_seq,
        )

    def record_retirement(
        self,
        ledger_path: Path | str | None = None,
        *,
        candidate_id: str,
        reason: str,
    ) -> dict[str, Any]:
        return record_retirement(
            self._target_path(ledger_path),
            candidate_id=candidate_id,
            reason=reason,
        )

    def verify(self, ledger_path: Path | str | None = None) -> dict[str, Any]:
        return verify(self._target_path(ledger_path))

    def admitted(self, ledger_path: Path | str | None = None) -> list[dict[str, Any]]:
        return admitted(self._target_path(ledger_path))

    @staticmethod
    def headstone_to_exclusion_hypothesis(
        headstone: Any,
        policy: HeadstoneExclusionPolicyV1,
        *,
        falsifier: str,
        falsifier_cost: int,
    ) -> ExclusionHypothesisV1 | None:
        return headstone_to_exclusion_hypothesis(
            headstone,
            policy,
            falsifier=falsifier,
            falsifier_cost=falsifier_cost,
        )


__all__ = [
    "CANONICAL_ANTI_SKILL_FAILURE_CLASSES",
    "CANONICAL_CAPABILITY_KINDS",
    "CANONICAL_FAILURE_CLASSES",
    "CANONICAL_PHARMACY_FAILURE_CLASSES",
    "CAUSE_OF_DEATH_MAP",
    "DDC_TRACE_LETTERS",
    "OperadLedgerAdapter",
    "OperadLedgerError",
    "admitted",
    "headstone_to_exclusion_hypothesis",
    "is_valid_ddc_trace",
    "is_valid_evidence_sha256",
    "propose_candidate",
    "record_admission",
    "record_failure",
    "record_headstone",
    "record_retirement",
    "record_trial",
    "resolve_failure_class",
    "verify",
]
