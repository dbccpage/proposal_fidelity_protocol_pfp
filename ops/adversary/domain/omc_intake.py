"""Domain models and classifiers for OMC DAG intake and obstruction farming.

Classifies incoming Operad Morphism Calculus (OMC) and Red Team Red Team
audit records into four canonical Engine domains:
  1. DDC: Discrete Deformation Calculus
  2. OEWAS: Engine Workflows, Agents & Skills
  3. OEEIS: Engine Epistemic Immune System
  4. OEPRMPTCIV: Prompt Civilization

Extracts decisive blockers, failing gates, and surviving invariants to seed
anti-skills (antibodies) and positive skills for the Adversary dialectic swarm.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


class OmcDomain(str, Enum):
    """Canonical Engine domains targeted during OMC intake."""

    DDC = "DDC"
    OEWAS = "OEWAS"
    OEEIS = "OEEIS"
    OEPRMPTCIV = "OEPRMPTCIV"


class ObstructionSeverity(str, Enum):
    BLOCKER = "BLOCKER"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    INFORMATIVE = "INFORMATIVE"


@dataclass(frozen=True, slots=True)
class OmcDagRecordV1:
    """Normalized domain representation of an ingested OMC record."""

    record_id: str
    source_file: str
    record_type: str  # audit_report | pr_preflight | subsystem_audit | audit_finding | raw
    raw_payload: dict[str, Any]
    target: str = ""
    target_hash: str = ""
    verdict: str = "UNKNOWN"
    decisive_blockers: tuple[str, ...] = ()
    audited_files: tuple[str, ...] = ()
    natural_science_gates: dict[str, str] = field(default_factory=dict)
    code_compliance: dict[str, bool] = field(default_factory=dict)
    what_survived: tuple[str, ...] = ()
    dual_witness_status: str = "UNKNOWN"
    authority_effect: str = "None"

    @property
    def digest(self) -> str:
        data = json.dumps(self.raw_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "source_file": self.source_file,
            "record_type": self.record_type,
            "target": self.target,
            "target_hash": self.target_hash,
            "verdict": self.verdict,
            "decisive_blockers": list(self.decisive_blockers),
            "audited_files": list(self.audited_files),
            "natural_science_gates": dict(self.natural_science_gates),
            "code_compliance": dict(self.code_compliance),
            "what_survived": list(self.what_survived),
            "dual_witness_status": self.dual_witness_status,
            "authority_effect": self.authority_effect,
            "digest": self.digest,
        }


@dataclass(frozen=True, slots=True)
class FarmedObstructionV1:
    """An obstruction extracted from OMC entrails, ready for Adversary farming."""

    obstruction_id: str
    source_record_id: str
    domains: tuple[OmcDomain, ...]
    description: str
    failure_class: str
    severity: ObstructionSeverity
    gate: str = ""
    suggested_anti_skill: str = ""
    suggested_skill_repair: str = ""
    evidence_refs: tuple[str, ...] = ()
    authority_effect: str = "None"

    def to_dict(self) -> dict[str, Any]:
        return {
            "obstruction_id": self.obstruction_id,
            "source_record_id": self.source_record_id,
            "domains": [d.value for d in self.domains],
            "description": self.description,
            "failure_class": self.failure_class,
            "severity": self.severity.value,
            "gate": self.gate,
            "suggested_anti_skill": self.suggested_anti_skill,
            "suggested_skill_repair": self.suggested_skill_repair,
            "evidence_refs": list(self.evidence_refs),
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True, slots=True)
class FarmedSurvivingSkillV1:
    """A positive surviving invariant or repair pattern suitable for skill cataloging."""

    skill_id: str
    source_record_id: str
    domains: tuple[OmcDomain, ...]
    description: str
    surviving_pattern: str
    suggested_skill_name: str
    evidence_refs: tuple[str, ...] = ()
    authority_effect: str = "None"

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "source_record_id": self.source_record_id,
            "domains": [d.value for d in self.domains],
            "description": self.description,
            "surviving_pattern": self.surviving_pattern,
            "suggested_skill_name": self.suggested_skill_name,
            "evidence_refs": list(self.evidence_refs),
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True, slots=True)
class OmcHarvestResultV1:
    """Aggregated result of intaking OMC DAGs across all 4 domains."""

    total_records: int
    records_by_domain: dict[str, int]
    obstructions: tuple[FarmedObstructionV1, ...]
    surviving_skills: tuple[FarmedSurvivingSkillV1, ...]
    authority_effect: str = "None"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "core.adversary.omc-harvest.v1",
            "total_records": self.total_records,
            "records_by_domain": dict(self.records_by_domain),
            "total_obstructions": len(self.obstructions),
            "total_surviving_skills": len(self.surviving_skills),
            "obstructions": [obs.to_dict() for obs in self.obstructions],
            "surviving_skills": [skill.to_dict() for skill in self.surviving_skills],
            "authority_effect": self.authority_effect,
        }


# =============================================================================
# Domain Classification Engine
# =============================================================================

_DDC_KEYWORDS = frozenset(
    {
        "ddc",
        "discrete_deformation",
        "deformation",
        "cochain",
        "carrier",
        "coboundary",
        "differential",
        "homotopy",
        "gauge",
        "regge",
        "meron",
        "laplacian",
        "dec_",
        "triangulation",
        "deficit",
        "holonomy",
        "pentachor",
        "schlafli",
        "witnessed_difference",
        "sovereignty_and_discrete_l1",
    }
)

_OEWAS_KEYWORDS = frozenset(
    {
        "oewas",
        "operad",
        "coloured_operad",
        "skill",
        "agent",
        "workflow",
        "degree_wise_dsl",
        "dsl",
        "dendroidal",
        "nerve",
        "tree",
        "multicategory",
        "action_trace",
        "hct_",
        "turn_stepper",
        "stage_runtime",
    }
)

_OEEIS_KEYWORDS = frozenset(
    {
        "oeeis",
        "epistemic_immune",
        "immune",
        "cemetery",
        "negative_result",
        "antibody",
        "failure_detector",
        "falsifier",
        "probe",
        "adversarial",
        "blocker",
        "defect",
        "obstacle",
        "decisive_blockers",
        "review_reproduction",
    }
)

_OEPRMPTCIV_KEYWORDS = frozenset(
    {
        "prompt_civ",
        "oeprmptciv",
        "prompt_civilization",
        "prompt_genealogy",
        "prompt",
        "locus_ancestry",
        "panel",
        "bout",
        "ancestral_rank",
        "civ_falsifiers",
    }
)


def _text_matches_keywords(text: str, keywords: frozenset[str]) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in keywords)


def classify_omc_record(record: OmcDagRecordV1) -> tuple[OmcDomain, ...]:
    """Classify an OMC record into a set of target Engine domains."""
    domains: set[OmcDomain] = set()

    corpus_parts = [
        record.record_id,
        record.target,
        record.source_file,
        record.verdict,
        " ".join(record.audited_files),
        " ".join(record.decisive_blockers),
        " ".join(record.what_survived),
        " ".join(record.natural_science_gates.keys()),
        " ".join(record.natural_science_gates.values()),
    ]
    if "checks" in record.raw_payload:
        checks_obj = record.raw_payload["checks"]
        if isinstance(checks_obj, dict):
            corpus_parts.extend(checks_obj.keys())
            for val in checks_obj.values():
                corpus_parts.append(str(val))
    if "pr_title" in record.raw_payload:
        corpus_parts.append(str(record.raw_payload["pr_title"]))
    if "branch" in record.raw_payload:
        corpus_parts.append(str(record.raw_payload["branch"]))
    if "subsystem" in record.raw_payload:
        corpus_parts.append(str(record.raw_payload["subsystem"]))

    full_text = " ".join(corpus_parts).lower()

    if _text_matches_keywords(full_text, _DDC_KEYWORDS):
        domains.add(OmcDomain.DDC)
    if _text_matches_keywords(full_text, _OEWAS_KEYWORDS):
        domains.add(OmcDomain.OEWAS)
    if _text_matches_keywords(full_text, _OEEIS_KEYWORDS):
        domains.add(OmcDomain.OEEIS)
    if _text_matches_keywords(full_text, _OEPRMPTCIV_KEYWORDS):
        domains.add(OmcDomain.OEPRMPTCIV)

    # Any record with decisive blockers or failing checks naturally triggers the Epistemic Immune System
    if record.decisive_blockers or record.verdict == "NO_GO":
        domains.add(OmcDomain.OEEIS)

    # Natural science gates with exact witness verification belong to DDC by definition
    if record.dual_witness_status in ("EXACT_VERIFIED", "PRIMAL_ONLY"):
        domains.add(OmcDomain.DDC)

    # Default fallback: if no specific domain matched, assign to OEEIS as general audit evidence
    if not domains:
        domains.add(OmcDomain.OEEIS)

    return tuple(sorted(domains, key=lambda d: d.value))


def farm_obstructions_from_record(record: OmcDagRecordV1) -> tuple[FarmedObstructionV1, ...]:
    """Extract actionable obstructions, failing gates, and defects from an OMC record."""
    obstructions: list[FarmedObstructionV1] = []
    domains = classify_omc_record(record)
    counter = 1

    # 1. Decisive blockers
    for blocker in record.decisive_blockers:
        blocker_clean = blocker.strip()
        if not blocker_clean:
            continue
        failure_class = _infer_failure_class(blocker_clean)
        anti_skill = _suggest_anti_skill_name(failure_class)
        repair = f"Address blocker: {blocker_clean}"
        obs_id = f"{record.record_id}-OBS-{counter:03d}"
        counter += 1
        obstructions.append(
            FarmedObstructionV1(
                obstruction_id=obs_id,
                source_record_id=record.record_id,
                domains=domains,
                description=blocker_clean,
                failure_class=failure_class,
                severity=ObstructionSeverity.BLOCKER,
                gate="decisive_blocker",
                suggested_anti_skill=anti_skill,
                suggested_skill_repair=repair,
                evidence_refs=(f"{record.source_file}:{record.record_id}",),
            )
        )

    # 2. Failing Natural Science Gates
    for gate_name, status in record.natural_science_gates.items():
        if status not in ("PASS", "EXACT_VERIFIED", "N_A"):
            failure_class = f"GATE_FAILURE_{gate_name.upper()}"
            anti_skill = f"anti-{gate_name.replace('_', '-')}-violation"
            repair = f"Refactor code to satisfy {gate_name} requirement (status was {status})"
            obs_id = f"{record.record_id}-OBS-{counter:03d}"
            counter += 1
            obstructions.append(
                FarmedObstructionV1(
                    obstruction_id=obs_id,
                    source_record_id=record.record_id,
                    domains=domains,
                    description=f"Natural Science Gate '{gate_name}' failed with status: {status}",
                    failure_class=failure_class,
                    severity=ObstructionSeverity.MAJOR,
                    gate=gate_name,
                    suggested_anti_skill=anti_skill,
                    suggested_skill_repair=repair,
                    evidence_refs=(f"{record.source_file}:{gate_name}",),
                )
            )

    # 3. Primal-only or uncertified dual witness status
    if record.dual_witness_status == "PRIMAL_ONLY":
        obs_id = f"{record.record_id}-OBS-{counter:03d}"
        counter += 1
        obstructions.append(
            FarmedObstructionV1(
                obstruction_id=obs_id,
                source_record_id=record.record_id,
                domains=domains,
                description="Dual certificate missing for alleged exact/minimal residual claim (PRIMAL_ONLY).",
                failure_class="UNCERTIFIED_PRIMAL_RESIDUAL",
                severity=ObstructionSeverity.MAJOR,
                gate="dual_witness",
                suggested_anti_skill="anti-primal-only-unverified-claim",
                suggested_skill_repair="Pair primal differential witness with exact dual rational certificate.",
                evidence_refs=(f"{record.source_file}:dual_witness",),
            )
        )

    # 4. PR Preflight failed checks
    if "checks" in record.raw_payload:
        checks_obj = record.raw_payload["checks"]
        if isinstance(checks_obj, dict):
            for check_name, check_val in checks_obj.items():
                if isinstance(check_val, dict):
                    status = check_val.get("status", "")
                    if status and status != "PASS":
                        obs_id = f"{record.record_id}-OBS-{counter:03d}"
                        counter += 1
                        obstructions.append(
                            FarmedObstructionV1(
                                obstruction_id=obs_id,
                                source_record_id=record.record_id,
                                domains=domains,
                                description=f"PR preflight check '{check_name}' reported {status}",
                                failure_class=f"CHECK_FAILURE_{check_name.upper()}",
                                severity=ObstructionSeverity.MAJOR,
                                gate=check_name,
                                suggested_anti_skill=f"anti-{check_name.replace('_', '-')}-defect",
                                suggested_skill_repair=f"Run local falsifier for {check_name}",
                                evidence_refs=(f"{record.source_file}:{check_name}",),
                            )
                        )
                elif isinstance(check_val, str) and check_val not in ("PASS", "OK"):
                    obs_id = f"{record.record_id}-OBS-{counter:03d}"
                    counter += 1
                    obstructions.append(
                        FarmedObstructionV1(
                            obstruction_id=obs_id,
                            source_record_id=record.record_id,
                            domains=domains,
                            description=f"Check '{check_name}' failed: {check_val}",
                            failure_class=f"CHECK_FAILURE_{check_name.upper()}",
                            severity=ObstructionSeverity.MAJOR,
                            gate=check_name,
                            suggested_anti_skill=f"anti-{check_name.replace('_', '-')}-defect",
                            suggested_skill_repair=f"Fix failing check {check_name}",
                            evidence_refs=(f"{record.source_file}:{check_name}",),
                        )
                    )

    return tuple(obstructions)


def farm_surviving_skills_from_record(record: OmcDagRecordV1) -> tuple[FarmedSurvivingSkillV1, ...]:
    """Extract surviving positive invariants and verification patterns from an OMC record."""
    skills: list[FarmedSurvivingSkillV1] = []
    domains = classify_omc_record(record)
    counter = 1

    for item in record.what_survived:
        clean_item = item.strip()
        if not clean_item:
            continue
        skill_id = f"{record.record_id}-SKILL-{counter:03d}"
        counter += 1
        suggested_name = _suggest_skill_name(clean_item)
        skills.append(
            FarmedSurvivingSkillV1(
                skill_id=skill_id,
                source_record_id=record.record_id,
                domains=domains,
                description=clean_item,
                surviving_pattern=clean_item,
                suggested_skill_name=suggested_name,
                evidence_refs=(f"{record.source_file}:{record.record_id}",),
            )
        )

    if record.dual_witness_status == "EXACT_VERIFIED":
        skill_id = f"{record.record_id}-SKILL-{counter:03d}"
        skills.append(
            FarmedSurvivingSkillV1(
                skill_id=skill_id,
                source_record_id=record.record_id,
                domains=domains,
                description="Exact primal and dual witness verification achieved.",
                surviving_pattern="Dual certificate pairing with zero gap",
                suggested_skill_name="governance-exact-dual-witness-verifier",
                evidence_refs=(f"{record.source_file}:dual_witness",),
            )
        )

    return tuple(skills)


def _infer_failure_class(blocker: str) -> str:
    b = blocker.lower()
    if "synthetic" in b or "max(" in b or "curve" in b:
        return "SYNTHETIC_CURVE_HACK"
    if "sorry" in b or "admit" in b or "unsafe" in b or "axiom" in b:
        return "UNPROVEN_LEAN_AXIOM"
    if "continuum" in b or "thermodynamic" in b or "limit" in b:
        return "CONTINUUM_EXTRAPOLATION_ERROR"
    if "dimension" in b or "carrier" in b or "unit" in b:
        return "DIMENSIONAL_MISMATCH"
    if "witness" in b or "dual" in b:
        return "DUAL_WITNESS_ABSENT"
    if "clean architecture" in b or "inward" in b or "import" in b:
        return "CLEAN_ARCHITECTURE_INWARD_VIOLATION"
    if "circular" in b or "cycle" in b:
        return "CIRCULAR_DEPENDENCY"
    if "manifest" in b or "sha256" in b or "digest" in b:
        return "MANIFEST_DIGEST_DIVERGENCE"
    if "unmanifested" in b or "silent skip" in b:
        return "PACKAGING_UNMANIFESTED_FILES"
    if "version" in b or "lineage" in b or "date" in b:
        return "PUBLICATION_VERSION_LINEAGE_CONFLICT"
    if "float" in b or "tolerance" in b or "precision" in b:
        return "FLOAT_TOLERANCE_LEAK"
    if "projector" in b or "sign" in b or "bitmask" in b:
        return "PROJECTOR_SIGN_INVERSION"
    if "mock" in b or "facade" in b or "vacuous" in b:
        return "VACUOUS_TEST_MOCK_FACADE"
    if "budget" in b or "token" in b or "exhaustion" in b:
        return "TOKEN_BUDGET_EXHAUSTION"
    return "OPERATIONAL_OBSTRUCTION"


def _suggest_anti_skill_name(failure_class: str) -> str:
    return "anti-" + failure_class.lower().replace("_", "-")


def _suggest_skill_name(surviving_text: str) -> str:
    t = surviving_text.lower()
    if "carrier boundary" in t or "limit" in t:
        return "governance-carrier-boundary-honesty"
    if "exact residual" in t or "primal differential" in t or "dual witness" in t:
        return "governance-dual-witness-certifier"
    if "figure generation" in t or "synthetic" in t:
        return "governance-dynamic-figure-authenticator"
    if "mechanized proof" in t or "lean" in t:
        return "governance-lean-axiom-totality"
    return "governance-surviving-invariant-guard"
