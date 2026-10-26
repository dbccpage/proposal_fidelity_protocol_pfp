"""Compatibility facade for deterministic antibody harvesting.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from .pharmacy_catalog import PharmacyCatalogRepository
from .ports import CatalogByteSource
from .pharmacy_models import (
    Antibody,
    ConstraintType,
    Operatorizability,
    PharmacyStatus,
    RuntimeAction,
    Severity,
)
from .pharmacy_templates import (
    ANTIBODY_TEMPLATES,
    CANONICAL_ANTIBODY_TEMPLATES,
    classify_failure,
    generic_template,
)
from .retired_antibodies import is_retired


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


__all__ = [
    "ConstraintType",
    "Operatorizability",
    "RuntimeAction",
    "Severity",
    "PharmacyStatus",
    "Antibody",
    "CANONICAL_ANTIBODY_TEMPLATES",
    "PharmacySeeder",
]
