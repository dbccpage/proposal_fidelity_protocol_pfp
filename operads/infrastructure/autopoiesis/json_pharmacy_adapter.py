"""Pharmacy catalog and antibody JSON adapter.

Manages loading and merging antibodies into:
  _intelligence/antibodies/pharmacy_catalog.json
and writing individual antibody files under:
  _intelligence/antibodies/ab_<id>.json

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from operads.domain.autopoiesis.entities import MinedAntibody
from operads.domain.autopoiesis.ports import PharmacyCatalogPort


class JsonPharmacyAdapter(PharmacyCatalogPort):
    """Filesystem adapter for managing antibody JSON files and pharmacy catalog."""

    def __init__(self, antibodies_dir: Path | str) -> None:
        self.antibodies_dir = Path(antibodies_dir).resolve()
        self.catalog_path = self.antibodies_dir / "pharmacy_catalog.json"
        self.antibodies_dir.mkdir(parents=True, exist_ok=True)

    def load_catalog(self) -> dict[str, Any]:
        """Loads the current pharmacy catalog or initializes a new one."""
        if not self.catalog_path.is_file():
            return {
                "catalog_version": "1.0.0",
                "authority_effect": "None",
                "antibodies": {},
            }
        try:
            return json.loads(self.catalog_path.read_text(encoding="utf-8"))
        except Exception:
            return {
                "catalog_version": "1.0.0",
                "authority_effect": "None",
                "antibodies": {},
            }

    def save_antibody(self, antibody: MinedAntibody) -> Path:
        """Persists an individual antibody JSON record."""
        target_path = self.antibodies_dir / f"{antibody.antibody_id}.json"
        payload = antibody.to_dict()
        target_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return target_path

    def merge_antibodies(self, antibodies: Sequence[MinedAntibody]) -> int:
        """Merges candidate antibodies into the catalog, incrementing sightings or creating entries."""
        catalog = self.load_catalog()
        entries = catalog.setdefault("antibodies", {})
        updated_count = 0

        for ab in antibodies:
            aid = ab.antibody_id
            if aid in entries:
                existing = entries[aid]
                existing["times_seen"] = existing.get("times_seen", 1) + 1
                updated_count += 1
            else:
                entries[aid] = ab.to_dict()
                entries[aid]["times_seen"] = 1
                updated_count += 1
            # Also ensure individual file is written
            self.save_antibody(ab)

        self.catalog_path.write_text(
            json.dumps(catalog, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return updated_count
