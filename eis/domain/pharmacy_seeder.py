"""Compatibility facade for deterministic antibody harvesting.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import fields
import hashlib
from pathlib import Path
import re
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from .pharmacy_catalog import PharmacyCatalogRepository
from .pharmacy_models import (
    Antibody,
    ConstraintType,
    LearningEvidencePreimageV1,
    Operatorizability,
    PharmacyStatus,
    RuntimeAction,
    Severity,
    compute_learning_evidence_sha256,
)
from .pharmacy_search import rule_content_sha256
from .pharmacy_templates import (
    ANTIBODY_TEMPLATES,
    CANONICAL_ANTIBODY_TEMPLATES,
    classify_failure,
    generic_template,
)
from .ports import CatalogByteSource
from .retired_antibodies import is_retired
from .thymus import ThymusGate
from .value_objects import DetectorRule


class PharmacySeeder:
    """Application service: classify run defects, build candidates, persist through repository."""

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        repository: Optional[PharmacyCatalogRepository] = None,
        *,
        byte_writer: Callable[[Path, bytes], None] | None = None,
        byte_source: CatalogByteSource | None = None,
    ):
        if repository is not None:
            self.repository = repository
            self.repo_root = repository.repo_root
        else:
            self.repo_root = (
                Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
            )
            self.repository = PharmacyCatalogRepository(
                self.repo_root, byte_writer=byte_writer, byte_source=byte_source
            )
        self.antibodies_dir = self.repository.antibodies_dir
        self.candidates_dir = self.repository.candidates_dir
        self.catalog_file = self.repository.catalog_file
        #: Ids skipped because they are on the retirement register. Recorded
        #: rather than silently dropped: a refusal nobody can see is the same
        #: shape of problem as the phantom it refuses.
        self.refused_retired: List[str] = []
        #: Ids observed again after a human judgement (admitted or rejected); their
        #: records are left untouched rather than rewritten as candidates.
        self.preserved_judged: List[str] = []

    def get_antibody_path(self, antibody_id: str, status: Optional[str] = None) -> Path:
        return self.repository.get_antibody_path(antibody_id, status)

    def farm_antibodies_from_defects(
        self,
        defects: Sequence[str],
        *,
        run_id: str,
        task_id: str,
    ) -> List[Antibody]:
        farmed: List[Antibody] = []
        self.refused_retired = []
        self.preserved_judged = []
        existing_catalog = self.repository.load_catalog()
        # Include repeated observations in this input; consulting only the
        # original on-disk snapshot loses every duplicate after the first.
        observed_counts: Dict[str, int] = {}

        for defect in defects:
            clean_defect = defect.strip()
            if not clean_defect:
                continue

            failure_class = classify_failure(clean_defect)
            template = ANTIBODY_TEMPLATES.get(failure_class) or generic_template(clean_defect)
            antibody_id = (
                f"ab_{failure_class}_{hashlib.sha256(clean_defect.encode('utf-8')).hexdigest()[:8]}"
            )
            prior_count = observed_counts.get(
                antibody_id,
                existing_catalog.get("antibodies", {}).get(antibody_id, {}).get("times_seen", 0),
            )
            evidence = hashlib.sha256(
                f"{antibody_id}:{clean_defect}:{run_id}:{task_id}".encode("utf-8")
            ).hexdigest()

            # A retired antibody guards against a defect that never existed.
            # Refarming it would resurrect the phantom under the same id, so the
            # register is checked before anything is built or written.
            if is_retired(antibody_id):
                self.refused_retired.append(antibody_id)
                continue

            # An antibody already judged (admitted or rejected) is not re-farmed:
            # `Antibody.farm` can only write CANDIDATE, so overwriting would demote
            # a human admission. The observation is reported, the record kept.
            recorded_status = (
                existing_catalog.get("antibodies", {}).get(antibody_id, {}).get("pharmacy_status")
            )
            if recorded_status not in (None, PharmacyStatus.CANDIDATE.value):
                self.preserved_judged.append(antibody_id)
                continue

            # `Antibody.farm` takes no status: harvesting cannot express
            # admission, so this call cannot mint its own evidence.
            antibody = Antibody.farm(
                antibody_id=antibody_id,
                failure_class=failure_class,
                target_pattern=clean_defect,
                constraint_type=template.constraint_type,
                operatorizability=template.operatorizability,
                action=template.action,
                severity=template.severity,
                description=template.description,
                negative_fixture=template.negative_fixture,
                positive_fixture=template.positive_fixture,
                times_seen=prior_count + 1,
                evidence_sha256=evidence,
                source_run_id=run_id,
                source_task_id=task_id,
            )
            farmed.append(antibody)
            observed_counts[antibody_id] = antibody.times_seen
            self.repository.save_antibody(antibody)

        if farmed:
            self.repository.update_catalog(farmed, run_id=run_id, task_id=task_id)
        return farmed

    # Compatibility shims for prior tests/callers.
    def _save_individual_antibody(self, antibody: Antibody) -> Path:
        return self.repository.save_antibody(antibody)

    def load_catalog(self) -> Dict[str, Any]:
        return self.repository.load_catalog()

    def _update_catalog(
        self, new_antibodies: Sequence[Antibody], *, run_id: str, task_id: str
    ) -> None:
        self.repository.update_catalog(new_antibodies, run_id=run_id, task_id=task_id)

    def record_reproduced_failure(
        self,
        *,
        prompt_id: str,
        preimage: LearningEvidencePreimageV1,
        target_pattern: str,
        positive_fixture: str,
        negative_fixture: str | None = None,
        description: str = "",
        guidance_text: str = "",
        run_id: str = "",
        task_id: str = "",
        scope_level: str = "prompt_line",
        family_id: str | None = None,
        society_id: str | None = None,
        civilization_id: str | None = None,
        producer_actor: str = "operative_seat",
        model_id: str = "unknown_model",
        scaffold_digest: str = "default_scaffold",
        precedent_set_digest: str = "default_precedent",
        lineage_root: str | None = None,
        registry: Any | None = None,
        self_panel: Sequence[str] | None = None,
    ) -> Antibody:
        return record_reproduced_failure(
            prompt_id=prompt_id,
            preimage=preimage,
            target_pattern=target_pattern,
            positive_fixture=positive_fixture,
            negative_fixture=negative_fixture,
            description=description,
            guidance_text=guidance_text,
            run_id=run_id,
            task_id=task_id,
            scope_level=scope_level,
            family_id=family_id,
            society_id=society_id,
            civilization_id=civilization_id,
            producer_actor=producer_actor,
            model_id=model_id,
            scaffold_digest=scaffold_digest,
            precedent_set_digest=precedent_set_digest,
            lineage_root=lineage_root,
            repository=self.repository,
            registry=registry,
            self_panel=self_panel,
        )


_ANTIBODY_FIELD_NAMES = frozenset(f.name for f in fields(Antibody))


def _sanitize_antibody_slug(raw: str) -> str:
    slug = re.sub(r"[^a-z0-9_]+", "_", raw.lower()).strip("_")
    return slug or "defect"


def _antibody_from_record(record: Mapping[str, Any]) -> Antibody:
    filtered = {k: v for k, v in record.items() if k in _ANTIBODY_FIELD_NAMES}
    return Antibody(**filtered)


def record_reproduced_failure(
    *,
    prompt_id: str,
    preimage: LearningEvidencePreimageV1,
    target_pattern: str,
    positive_fixture: str,
    negative_fixture: str | None = None,
    description: str = "",
    guidance_text: str = "",
    run_id: str = "",
    task_id: str = "",
    scope_level: str = "prompt_line",
    family_id: str | None = None,
    society_id: str | None = None,
    civilization_id: str | None = None,
    producer_actor: str = "operative_seat",
    model_id: str = "unknown_model",
    scaffold_digest: str = "default_scaffold",
    precedent_set_digest: str = "default_precedent",
    lineage_root: str | None = None,
    repository: PharmacyCatalogRepository,
    registry: Any | None = None,
    self_panel: Sequence[str] | None = None,
) -> Antibody:
    """Record a host-reproduced prompt failure as a CANDIDATE antibody (AuthorityEffect: None)."""
    if type(prompt_id) is not str or not prompt_id.strip():
        raise ValueError("PHARMACY_PROMPT_ID_REQUIRED: prompt_id is required")
    if type(preimage) is not LearningEvidencePreimageV1:
        raise TypeError("preimage must be an exact LearningEvidencePreimageV1")
    if preimage.prompt_id != prompt_id:
        raise ValueError("PHARMACY_PROMPT_ID_MISMATCH: preimage.prompt_id != prompt_id")
    if type(target_pattern) is not str or not target_pattern.strip():
        raise ValueError("PHARMACY_TARGET_PATTERN_REQUIRED: target_pattern must be non-empty")

    evidence = compute_learning_evidence_sha256(preimage)
    slug = _sanitize_antibody_slug(preimage.failure_class)
    pattern_hash = hashlib.sha256(target_pattern.encode("utf-8")).hexdigest()[:8]
    antibody_id = f"ab_{slug}_{pattern_hash}"

    if is_retired(antibody_id):
        raise ValueError(f"PHARMACY_ANTIBODY_RETIRED: {antibody_id}")

    existing_catalog = repository.load_catalog()
    existing_entry = existing_catalog.get("antibodies", {}).get(antibody_id)
    if existing_entry is not None and existing_entry.get("pharmacy_status") not in (
        None,
        PharmacyStatus.CANDIDATE.value,
        PharmacyStatus.PROVISIONAL.value,
    ):
        return _antibody_from_record(existing_entry)

    template = ANTIBODY_TEMPLATES.get(preimage.failure_class) or generic_template(target_pattern)
    resolved_neg = (
        negative_fixture
        if negative_fixture is not None
        else preimage.candidate_reply_bytes.decode("utf-8", errors="replace")
    )
    resolved_guidance = guidance_text or description or template.description
    scope_dict: Dict[str, Any] = {
        "domain": scope_level,
        "prompt_id": prompt_id,
    }
    if family_id:
        scope_dict["family_id"] = family_id
    if society_id:
        scope_dict["society_id"] = society_id
    if civilization_id:
        scope_dict["civilization_id"] = civilization_id

    prior_times = int(existing_entry.get("times_seen", 0)) if existing_entry else 0
    candidate_obj = Antibody.farm(
        antibody_id=antibody_id,
        failure_class=preimage.failure_class,
        target_pattern=target_pattern,
        constraint_type=template.constraint_type,
        operatorizability=template.operatorizability,
        action=template.action,
        severity=template.severity,
        description=description or template.description,
        negative_fixture=resolved_neg,
        positive_fixture=positive_fixture,
        times_seen=prior_times + 1,
        evidence_sha256=evidence,
        source_run_id=run_id,
        source_task_id=task_id,
        source_prompt_id=prompt_id,
        scope_level=scope_level,
        family_id=family_id,
        society_id=society_id,
        civilization_id=civilization_id,
        producer_actor=producer_actor,
        guidance_text=resolved_guidance,
        scope=scope_dict,
    )
    record = candidate_obj.to_dict()
    record["rule_sha256"] = rule_content_sha256(record)
    obs_list = list(existing_entry.get("observation_ids", [])) if existing_entry else []
    obs_id = f"{run_id or 'turn'}:{prompt_id}:{evidence[:12]}"
    if obs_id not in obs_list:
        obs_list.append(obs_id)
    record["observation_ids"] = sorted(obs_list)

    if registry is not None:
        registry.observe(
            target_pattern,
            obs_id,
            model_id=model_id,
            scaffold_digest=scaffold_digest,
            precedent_digest=precedent_set_digest,
            lineage_root=lineage_root or prompt_id,
        )
        reg_status = registry.status(target_pattern)
        current_status = existing_entry.get("pharmacy_status") if existing_entry else PharmacyStatus.CANDIDATE.value
        if reg_status.get("custody") == "Provisional" and current_status == PharmacyStatus.CANDIDATE.value:
            if self_panel is not None and len(self_panel) > 0:
                thymus = ThymusGate(self_panel=self_panel)
                sel = thymus.evaluate_rule(
                    DetectorRule(
                        rule_id=antibody_id,
                        target_epitope=preimage.failure_class,
                        match_pattern=target_pattern,
                    )
                )
                if sel.is_admitted:
                    record["pharmacy_status"] = PharmacyStatus.PROVISIONAL.value
                else:
                    record["pharmacy_status"] = PharmacyStatus.RETIRED.value
                    record["revoked"] = True
            else:
                record["pharmacy_status"] = PharmacyStatus.PROVISIONAL.value

    persisted = repository.upsert_managed_record(record)
    return _antibody_from_record(persisted)


__all__ = [
    "ConstraintType",
    "LearningEvidencePreimageV1",
    "Operatorizability",
    "RuntimeAction",
    "Severity",
    "PharmacyStatus",
    "Antibody",
    "CANONICAL_ANTIBODY_TEMPLATES",
    "PharmacySeeder",
    "compute_learning_evidence_sha256",
    "record_reproduced_failure",
]
