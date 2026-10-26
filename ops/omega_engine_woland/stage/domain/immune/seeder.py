"""
seeder.py
=========

Swarm Immune System Pharmacy Seeder mining active defects into persistent antibodies.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Callable, List, Optional, Sequence

from .catalog_repository import PharmacyCatalogRepository
from .models import Antibody
from .templates import DEFAULT_ANTIBODY_TEMPLATES
from .text_source import CatalogTextSource


class ImmuneSeederV1:
    """Seeder computing canonical evidence digests binding detector, fixture, scope, and impl."""

    def compute_evidence_sha256(
        self,
        *,
        detector_bytes: bytes,
        fixture_bytes: bytes,
        scope: str,
        implementation_bytes: bytes,
    ) -> str:
        h = hashlib.sha256()
        h.update(b"ImmuneSeederV1:")
        h.update(hashlib.sha256(detector_bytes).digest())
        h.update(hashlib.sha256(fixture_bytes).digest())
        h.update(scope.encode("utf-8"))
        h.update(hashlib.sha256(implementation_bytes).digest())
        return h.hexdigest()

    def compute_legacy_digest(self, defect_str: str, run_id: str, task_id: str) -> str:
        seed_data = f"{defect_str}:{run_id}:{task_id}".encode("utf-8")
        return hashlib.sha256(seed_data).hexdigest()


class PharmacySeeder:
    """Mines active obstructions/defects into persistent antibodies and seeds the catalog."""

    def __init__(
        self,
        repo_root: Path,
        catalog_repo: Optional[PharmacyCatalogRepository] = None,
        *,
        text_writer: Callable[[Path, str], None] | None = None,
        text_source: CatalogTextSource | None = None,
    ):
        self.repo_root = Path(repo_root)
        if catalog_repo is None:
            if text_writer is None:
                raise RuntimeError("DOMAIN_DISK_WRITER_UNBOUND")
            catalog_repo = PharmacyCatalogRepository(
                self.repo_root, text_writer=text_writer, text_source=text_source
            )
        self.catalog_repo = catalog_repo

    def farm_antibodies_from_defects(
        self,
        defects: Sequence[str],
        *,
        run_id: str,
        task_id: str,
    ) -> List[Antibody]:
        if not defects:
            return []

        harvested: List[Antibody] = []
        for defect in defects:
            antibody = self._defect_to_antibody(defect, run_id=run_id, task_id=task_id)
            self.catalog_repo.save_antibody(antibody)
            harvested.append(antibody)

        self.catalog_repo.update_catalog(harvested, run_id=run_id, task_id=task_id)
        return harvested

    def _defect_to_antibody(self, defect_str: str, *, run_id: str, task_id: str) -> Antibody:
        clean = defect_str.strip()
        template_key = None
        if "clean_arch" in clean or "layer" in clean:
            template_key = "clean_arch_violation"
        elif "circular" in clean or "cycle" in clean:
            template_key = "circular_import"
        elif "unquoted" in clean or "annotation" in clean:
            template_key = "unquoted_annotation"
        elif "io" in clean or "uncontracted" in clean:
            template_key = "uncontracted_io"

        template = DEFAULT_ANTIBODY_TEMPLATES.get(
            template_key or "",
            {
                "failure_class": f"defect:{clean[:32]}",
                "target_pattern": re.escape(clean),
                "constraint_type": "ProjectOut",
                "operatorizability": "repairable",
                "action": "repair",
                "severity": "P1",
                "description": f"Auto-harvested antibody against obstruction: {clean}",
                "negative_fixture": f"# Triggering defect: {clean}\n",
                "positive_fixture": "# Repaired exact state\n",
            },
        )

        slug = re.sub(r"[^a-zA-Z0-9_]+", "_", clean).strip("_")[:40]
        seed_data = f"{defect_str}:{run_id}:{task_id}".encode("utf-8")
        evidence_sha256 = hashlib.sha256(seed_data).hexdigest()
        antibody_id = f"ab_{slug}_{evidence_sha256[:8]}"

        # `Antibody.farm` takes no status: a harvested antibody is a CANDIDATE
        # and there is no argument through which this call could say otherwise.
        return Antibody.farm(
            antibody_id=antibody_id,
            failure_class=template["failure_class"],
            target_pattern=template["target_pattern"],
            constraint_type=template["constraint_type"],
            operatorizability=template["operatorizability"],
            action=template["action"],
            severity=template["severity"],
            description=template["description"],
            negative_fixture=template["negative_fixture"],
            positive_fixture=template["positive_fixture"],
            times_seen=1,
            evidence_sha256=evidence_sha256,
        )
