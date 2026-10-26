"""
catalog_repository.py
=====================

Pharmacy Catalog persistence repository for Swarm Immune Antibodies.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Sequence

from omega_engine_governance.domain.intelligence_community import canonical_intelligence_route

from .models import Antibody
from .text_source import CatalogTextSource


class PharmacyCatalogRepository:
    """Catalog persistence through an injected text writer and text source.

    An unbound writer raises DOMAIN_DISK_WRITER_UNBOUND. An unbound source
    raises DOMAIN_DISK_READER_UNBOUND. This type does not open paths.
    """

    def __init__(
        self,
        repo_root: Path,
        *,
        text_writer: Callable[[Path, str], None] | None = None,
        text_source: CatalogTextSource | None = None,
    ):
        self.repo_root = Path(repo_root)
        self._text_writer = text_writer
        self._text_source = text_source
        self.antibodies_dir = self.repo_root / canonical_intelligence_route("_intelligence/antibodies")
        self.telemetry_dir = self.repo_root / canonical_intelligence_route(
            "_intelligence/archive/telemetry/antibodies"
        )
        self.candidates_dir = self.telemetry_dir
        self.specs_dir = self.antibodies_dir / "specs"
        self.catalog_file = self.antibodies_dir / "pharmacy_catalog.json"

    def _write_text(self, path: Path, text: str) -> None:
        if self._text_writer is None:
            raise RuntimeError("DOMAIN_DISK_WRITER_UNBOUND")
        self._text_writer(path, text)

    def _source(self) -> CatalogTextSource:
        if self._text_source is None:
            raise RuntimeError("DOMAIN_DISK_READER_UNBOUND")
        return self._text_source

    def get_antibody_path(self, antibody_id: str, status: str | None = None) -> Path:
        cand_path = self.candidates_dir / f"{antibody_id}.json"
        if self._source().is_file(str(cand_path)):
            return cand_path
        for directory in (self.specs_dir, self.antibodies_dir):
            for ext in (".yaml", ".json"):
                spec_path = directory / f"{antibody_id}{ext}"
                if self._source().is_file(str(spec_path)):
                    return spec_path
        legacy_cand = self.antibodies_dir / "candidates" / f"{antibody_id}.json"
        if self._source().is_file(str(legacy_cand)):
            return legacy_cand
        if status == "candidate":
            return cand_path
        return self.antibodies_dir / f"{antibody_id}.json"

    def save_antibody(self, antibody: Antibody) -> Path:
        status = getattr(antibody, "pharmacy_status", "candidate")
        dest_dir = self.candidates_dir if status == "candidate" else self.antibodies_dir
        path = dest_dir / f"{antibody.antibody_id}.json"
        self._write_text(path, json.dumps(antibody.to_dict(), indent=2))
        return path

    def load_catalog(self) -> Dict[str, Any]:
        source = self._source()
        if not source.exists(str(self.catalog_file)):
            return self._empty_catalog(with_timestamp=True)
        try:
            return json.loads(source.read_text(str(self.catalog_file)))
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"pharmacy catalog is unreadable: {exc}") from exc

    def update_catalog(
        self,
        antibodies: Sequence[Antibody],
        *,
        run_id: str,
        task_id: str,
    ) -> None:
        catalog = self.load_catalog()
        catalog["updated_at"] = datetime.now(timezone.utc).isoformat()
        catalog["last_mined_run_id"] = run_id
        catalog["last_mined_task_id"] = task_id
        entries = catalog.setdefault("antibodies", {})
        for antibody in antibodies:
            entries[antibody.antibody_id] = antibody.to_dict()
        self._write_text(self.catalog_file, json.dumps(catalog, indent=2))

    @staticmethod
    def _empty_catalog(*, with_timestamp: bool) -> Dict[str, Any]:
        catalog: Dict[str, Any] = {
            "catalog_version": "1.0.0",
            "authority_effect": "None",
            "antibodies": {},
        }
        if with_timestamp:
            catalog["updated_at"] = datetime.now(timezone.utc).isoformat()
        return catalog
