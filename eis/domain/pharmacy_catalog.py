from __future__ import annotations

import json
import hashlib
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Sequence

from .external_admission import HumanAntiSkillAdmissionDecisionV1, HumanAdmissionApplierV1
from .pharmacy_models import Antibody, PharmacyStatus
from .pharmacy_search import rule_content_bytes, rule_content_sha256
from .ports import CatalogByteSource


@dataclass(frozen=True)
class PublicationDecision:
    """Ids committed by one publication, and the marker the caller deletes."""

    changed: tuple[str, ...]
    marker_path: str | None


class PharmacyCatalogRepository:
    """Filesystem persistence for individual antibodies and the aggregate catalog."""

    @staticmethod
    def catalog_path(
        repo_root: Path, byte_source: CatalogByteSource | None = None
    ) -> Path:
        """Where the catalog lives under ``repo_root``; computing it creates nothing."""
        agents_catalog = Path(repo_root) / "eis" / "antibodies" / "pharmacy_catalog.json"
        if byte_source is None:
            return agents_catalog
        if byte_source.is_file(str(agents_catalog)):
            return agents_catalog
        intel_catalog = Path(repo_root) / "_ic/cdc/antibodies" / "pharmacy_catalog.json"
        if byte_source.is_file(str(intel_catalog)):
            return intel_catalog
        return agents_catalog

    def __init__(
        self,
        repo_root: Path,
        *,
        catalog_file: Path | None = None,
        telemetry_dir: Path | None = None,
        byte_writer: Callable[[Path, bytes], None] | None = None,
        byte_source: CatalogByteSource | None = None,
    ):
        self.repo_root = Path(repo_root)
        self._byte_writer = byte_writer
        self._byte_source = byte_source
        self.catalog_file = (
            Path(catalog_file)
            if catalog_file is not None
            else self.catalog_path(self.repo_root, byte_source)
        )
        self.antibodies_dir = self.catalog_file.parent
        self.telemetry_dir = (
            Path(telemetry_dir)
            if telemetry_dir is not None
            else self.repo_root / "_ic/nara/_archive" / "telemetry" / "antibodies"
        )
        self.candidates_dir = self.telemetry_dir
        self.specs_dir = self.antibodies_dir / "specs"
        self.oeeis_specs_dir = (
            self.repo_root / "eis" / "antibodies" / "antibody_specs"
        )

    def target_dir_for_status(self, pharmacy_status: str) -> Path:
        """Isolate candidate telemetry into the telemetry directory; non-candidates remain in antibodies_dir."""
        if pharmacy_status == PharmacyStatus.CANDIDATE.value:
            return self.candidates_dir
        return self.antibodies_dir

    def get_antibody_path(self, antibody_id: str, status: str | None = None) -> Path:
        """Locates the path of an antibody file, checking telemetry candidates first, then specs, then antibodies_dir."""
        cand_path = self.candidates_dir / f"{antibody_id}.json"
        if self._is_file(cand_path):
            return cand_path
        # Check specs subfolder and root antibodies directory for YAML/JSON specs
        for directory in (self.oeeis_specs_dir, self.specs_dir, self.antibodies_dir):
            for ext in (".yaml", ".json"):
                spec_path = directory / f"{antibody_id}{ext}"
                if self._is_file(spec_path):
                    return spec_path
        # Check legacy candidates/ subfolder if it exists
        legacy_cand = self.antibodies_dir / "candidates" / f"{antibody_id}.json"
        if self._is_file(legacy_cand):
            return legacy_cand
        if status == PharmacyStatus.CANDIDATE.value:
            return cand_path
        return self.antibodies_dir / f"{antibody_id}.json"

    def save_antibody(self, antibody: Antibody) -> Path:
        """Saves an antibody record. Farmed candidates are isolated into the candidates/ subfolder."""
        dest_dir = self.target_dir_for_status(antibody.pharmacy_status)
        path = dest_dir / f"{antibody.antibody_id}.json"
        self._write_bytes(path, json.dumps(antibody.to_dict(), indent=2).encode("utf-8"))
        return path

    def _source(self) -> CatalogByteSource:
        if self._byte_source is None:
            raise RuntimeError("DOMAIN_DISK_READER_UNBOUND")
        return self._byte_source

    def _is_file(self, path: Path) -> bool:
        return self._source().is_file(str(path))

    def _exists(self, path: Path) -> bool:
        return self._source().exists(str(path))

    def _read_text(self, path: Path) -> str:
        return self._source().read_text(str(path))

    def _read_bytes(self, path: Path) -> bytes:
        return self._source().read_bytes(str(path))

    def load_catalog(self) -> Dict[str, Any]:
        if self._exists(self.publication_marker):
            raise ValueError("PHARMACY_PUBLICATION_INTERRUPTED")
        catalog = self._read_catalog()
        for antibody_id, relative in catalog.get("managed_projections", {}).items():
            path = self._projection_path(relative)
            expected = self._json_bytes(catalog["antibodies"][antibody_id])
            if not self._is_file(path) or self._read_bytes(path) != expected:
                raise ValueError(f"PHARMACY_PROJECTION_DRIFT:{antibody_id}")
        return catalog

    def _read_catalog(self) -> Dict[str, Any]:
        if not self._exists(self.catalog_file):
            return self._empty_catalog(with_timestamp=True)
        try:
            catalog = json.loads(self._read_text(self.catalog_file))
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(
                f"Corrupt or unreadable pharmacy catalog detected at {self.catalog_file}: {exc}"
            ) from exc
        if type(catalog) is not dict or type(catalog.get("antibodies", {})) is not dict:
            raise ValueError("Pharmacy catalog and antibodies must be JSON objects")
        if any(type(entry) is not dict for entry in catalog.get("antibodies", {}).values()):
            raise ValueError("Pharmacy catalog antibody entries must be JSON objects")
        projections = catalog.get("managed_projections", {})
        if not isinstance(projections, dict) or any(
            key not in catalog.get("antibodies", {}) or not isinstance(value, str)
            for key, value in projections.items()
        ):
            raise ValueError("PHARMACY_PROJECTION_MANIFEST_INVALID")
        return catalog

    @property
    def publication_marker(self) -> Path:
        return self.catalog_file.with_suffix(".publication.pending.json")

    @staticmethod
    def _json_bytes(value: Any) -> bytes:
        return (json.dumps(value, indent=2) + "\n").encode("utf-8")

    def _projection_path(self, relative: str) -> Path:
        path = (self.repo_root / relative).resolve()
        if not path.is_relative_to(self.repo_root.resolve()):
            raise ValueError("PHARMACY_PROJECTION_PATH_ESCAPE")
        return path

    def _write_bytes(self, path: Path, payload: bytes) -> None:
        if self._byte_writer is None:
            raise RuntimeError("DOMAIN_DISK_WRITER_UNBOUND")
        self._byte_writer(path, payload)

    def _atomic_write(self, path: Path, payload: bytes) -> None:
        self._write_bytes(path, payload)

    def publish_candidates(
        self, records: Sequence[Dict[str, Any]], *, observation_id: str
    ) -> PublicationDecision:
        """Publish an identified observation once; judgement remains a separate act.

        The catalog is the commit point. A marker exposes interruption between
        file replacements; recovery rebuilds managed projections from that
        authoritative snapshot. Historical projections are not rewritten.
        """
        if not isinstance(observation_id, str) or not observation_id.strip():
            raise ValueError("PHARMACY_OBSERVATION_ID_REQUIRED")
        catalog = self.load_catalog()
        entries = catalog.setdefault("antibodies", {})
        projections = catalog.setdefault("managed_projections", {})
        changed: list[str] = []
        for record in records:
            antibody_id = record.get("antibody_id", "")
            if not isinstance(antibody_id, str) or not re.fullmatch(r"[a-z0-9_-]+", antibody_id):
                raise ValueError("PHARMACY_ID_INVALID")
            if record.get("pharmacy_status") != "candidate" or record.get("admission"):
                raise ValueError("PHARMACY_CANDIDATE_REQUIRED")
            if record.get("authority_effect") != "None":
                raise ValueError("PHARMACY_AUTHORITY_EFFECT_NON_NONE")
            existing = entries.get(antibody_id)
            if existing and existing.get("pharmacy_status") != "candidate":
                continue
            if existing:
                # A revision cannot silently change the detector it names.
                for key in ("failure_class", "target_pattern", "evidence_sha256", "rule_sha256"):
                    if existing.get(key) != record.get(key):
                        raise ValueError(f"PHARMACY_RULE_ID_COLLISION:{antibody_id}")
                entry = dict(existing)
            else:
                entry = dict(record)
                entry["times_seen"] = 0
            observations = list(entry.get("observation_ids", []))
            if observation_id in observations:
                continue
            observations.append(observation_id)
            entry["observation_ids"] = sorted(observations)
            entry["times_seen"] += 1
            entries[antibody_id] = entry
            destination = self.candidates_dir / f"{antibody_id}.json"
            projections[antibody_id] = destination.resolve().relative_to(self.repo_root.resolve()).as_posix()
            changed.append(antibody_id)
        if not changed:
            return PublicationDecision((), None)
        self._commit_catalog(catalog, changed)
        return PublicationDecision(tuple(changed), str(self.publication_marker))

    def _commit_catalog(self, catalog: Dict[str, Any], changed: list[str]) -> None:
        entries = catalog["antibodies"]
        projections = catalog["managed_projections"]
        payload = self._json_bytes(catalog)
        marker = {"catalog_sha256": hashlib.sha256(payload).hexdigest(), "changed": changed}
        self._atomic_write(self.publication_marker, self._json_bytes(marker))
        for antibody_id in changed:
            self._atomic_write(self._projection_path(projections[antibody_id]), self._json_bytes(entries[antibody_id]))
        self._atomic_write(self.catalog_file, payload)

    def publish_admission(
        self, antibody_id: str, decision: HumanAntiSkillAdmissionDecisionV1,
        *, applier: HumanAdmissionApplierV1,
    ) -> tuple[Dict[str, str], str]:
        """Persist a separately supplied operator decision after the existing gate."""
        catalog = self.load_catalog()
        record = catalog["antibodies"][antibody_id]
        if antibody_id not in catalog.get("managed_projections", {}):
            raise ValueError("PHARMACY_UNMANAGED_REVISION")
        if record.get("rule_sha256") != rule_content_sha256(record):
            raise ValueError("PHARMACY_RULE_DIGEST_MISMATCH")
        result = applier.apply_admission(decision, rule_content_bytes(record))
        if result.get("status") != "ADMITTED":
            raise ValueError(f"PHARMACY_ADMISSION_REFUSED:{result.get('reason', 'unknown')}")
        record["admission"] = asdict(decision)
        record["pharmacy_status"] = "admitted"
        self._commit_catalog(catalog, [antibody_id])
        return result, str(self.publication_marker)

    def repair_projections(self) -> str | None:
        """Explicitly recover managed projections; never infer a catalog from files."""
        if not self._is_file(self.catalog_file):
            raise ValueError("PHARMACY_AUTHORITATIVE_CATALOG_MISSING")
        catalog = self._read_catalog()
        for antibody_id, relative in catalog.get("managed_projections", {}).items():
            self._atomic_write(self._projection_path(relative), self._json_bytes(catalog["antibodies"][antibody_id]))
        if self._exists(self.publication_marker):
            return str(self.publication_marker)
        return None

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

        payload = json.dumps(catalog, indent=2).encode("utf-8")
        bak_file = self.catalog_file.with_suffix(".json.bak")
        if self._is_file(self.catalog_file):
            self._write_bytes(bak_file, self._read_bytes(self.catalog_file))
        self._write_bytes(self.catalog_file, payload)

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
