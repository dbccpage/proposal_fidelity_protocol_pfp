"""Archive manifest and custody operations for intelligence digestion."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .archive_custody import (
    ArchiveCustodyError,
    archivable_source_path,
    bundle_entries,
    checked_path,
    relative_parts,
    require_digest,
    validate_sealed_manifest,
)
from .digestion_models import (
    ARCHIVE_JOURNAL_SCHEMA,
    ARCHIVE_MANIFEST_SCHEMA,
    ArchiveJournalUnreadable,
    ArchiveManifestUnreadable,
    DigestionRecord,
    _read_object,
    _reject_constant,
    _unique_object,
)


class ArchiveCustodyOperations:
    def _empty_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": ARCHIVE_MANIFEST_SCHEMA,
            "authority_effect": "None",
            "updated_at_utc": self._now_utc(),
            "archived_sources": {},
            "legacy_uncertified": {},
        }

    def load_manifest(self) -> dict[str, Any]:
        checked_path(self.repo_root, self.manifest_file)
        if not self.manifest_file.exists():
            return self._empty_manifest()
        try:
            manifest = _read_object(self.manifest_file)
        except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            raise ArchiveManifestUnreadable(
                f"ARCHIVE_MANIFEST_UNREADABLE: {self.manifest_file}: {exc}"
            ) from exc
        schema = manifest.get("schema_version")
        if schema == "omega.intelligence_archive_manifest.v1":
            # Preserve historical records exactly while making their lack of a
            # source-transfer certificate visible to the new registry.
            return {
                "schema_version": ARCHIVE_MANIFEST_SCHEMA,
                "authority_effect": "None",
                "updated_at_utc": manifest.get("updated_at_utc", self._now_utc()),
                "archived_sources": {},
                "legacy_uncertified": dict(manifest.get("archived_runs", {})),
            }
        if (schema != ARCHIVE_MANIFEST_SCHEMA or manifest.get("authority_effect") != "None"
                or type(manifest.get("archived_sources")) is not dict):
            raise ArchiveManifestUnreadable(
                "ARCHIVE_MANIFEST_UNREADABLE: manifest has an unsupported schema or archive map"
            )
        manifest.setdefault("legacy_uncertified", {})
        return manifest

    def _atomic_write_json(self, path: Path, payload: Mapping[str, Any]) -> None:
        checked_path(self.repo_root, path)
        self.filesystem.atomic_write_json(path, payload)

    def _write_manifest(self, manifest: Mapping[str, Any]) -> None:
        material = dict(manifest)
        material["schema_version"] = ARCHIVE_MANIFEST_SCHEMA
        material["authority_effect"] = "None"
        material["updated_at_utc"] = self._now_utc()
        self._atomic_write_json(self.manifest_file, material)
        self._sync_corpora_manifest(material)

    def _append_journal(self, event_type: str, **payload: Any) -> None:
        checked_path(self.repo_root, self.journal_file)
        event = {
            "schema_version": ARCHIVE_JOURNAL_SCHEMA,
            "event_type": event_type,
            "recorded_at_utc": self._now_utc(),
            "authority_effect": "None",
            **payload,
        }
        encoded = (
            json.dumps(event, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(
                "utf-8"
            )
            + b"\n"
        )
        self.filesystem.append_bytes(self.journal_file, encoded)

    @staticmethod
    def _decode_journal_event(line: str) -> dict[str, Any] | None:
        if not line.strip():
            return None
        value = json.loads(
            line, object_pairs_hook=_unique_object, parse_constant=_reject_constant,
        )
        valid = (
            type(value) is dict
            and value.get("schema_version") == ARCHIVE_JOURNAL_SCHEMA
            and value.get("authority_effect") == "None"
            and type(value.get("event_type")) is str
            and bool(value["event_type"].strip())
        )
        if not valid:
            raise ValueError("invalid journal record")
        return value

    def _journal_events(self) -> list[dict[str, Any]]:
        checked_path(self.repo_root, self.journal_file)
        if not self.journal_file.exists():
            return []
        try:
            if self.journal_file.stat().st_size > 16 * 1024 * 1024:
                raise ValueError("journal exceeds 16 MiB intake limit")
            with self.journal_file.open("r", encoding="utf-8") as handle:
                lines = tuple(handle)
        except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            raise ArchiveJournalUnreadable(
                f"ARCHIVE_JOURNAL_UNREADABLE: {self.journal_file}: {exc}"
            ) from exc
        events: list[dict[str, Any]] = []
        try:
            for line in lines:
                event = self._decode_journal_event(line)
                if event is not None:
                    events.append(event)
        except (ValueError, json.JSONDecodeError) as exc:
            raise ArchiveJournalUnreadable(
                f"ARCHIVE_JOURNAL_UNREADABLE: {self.journal_file}: {exc}"
            ) from exc
        return events

    def _archive_record_path(self, source_id: object, record: object) -> Path:
        require_digest(source_id)
        if (type(record) is not dict or set(record) != set(DigestionRecord.__dataclass_fields__)
                or record["source_id"] != source_id or record["authority_effect"] != "None"
                or record["storage_state"] != "COLD"
                or record["digestion_state"] not in {"ABSORBED", "DISCHARGED"}
                or record["status"] != record["digestion_state"]
                or type(record["defects_count"]) is not int or record["defects_count"] < 0
                or type(record["defects_extracted"]) is not list
                or record["defects_count"] != len(record["defects_extracted"])
                or any(type(item) is not str for item in record["defects_extracted"])
                or type(record["archived_at_utc"]) is not str or not record["archived_at_utc"]):
            raise ArchiveCustodyError("ARCHIVE_CUSTODY_RECORD_INVALID", str(source_id))
        require_digest(record["evidence_sha256"])
        if record["certificate_id"] is not None:
            require_digest(record["certificate_id"])
        original = relative_parts(record["original_path"])
        relative_parts(record["source_queue"])
        if len(relative_parts(record["run_id"])) != 1 or original[-1] != record["run_id"]:
            raise ArchiveCustodyError("ARCHIVE_CUSTODY_RECORD_INVALID", str(source_id))
        relative_parts(record["archive_path"])
        expected = checked_path(
            self.repo_root, self.archive_root / self._archive_name(record["run_id"], source_id),
        )
        if record["archive_path"] != expected.relative_to(self.repo_root).as_posix():
            raise ArchiveCustodyError("ARCHIVE_CUSTODY_LOCATION_MISMATCH", str(source_id))
        return expected

    def _validate_archive(self, source_id: str, record: dict[str, Any],
                          *, source_path: Path | None = None) -> Mapping[str, Any]:
        """Recompute native custody from bytes; never rewrite the saved source manifest."""
        destination = self._archive_record_path(source_id, record)
        manifest_path = checked_path(
            self.repo_root, self.source_manifest_root / f"{source_id.removeprefix('sha256:')}.json",
        )
        try:
            original = validate_sealed_manifest(_read_object(manifest_path))
            if (original["source_id"] != source_id
                    or original["manifest_sha256"] != record["evidence_sha256"]
                    or original["source_locator"] != record["original_path"]):
                raise ArchiveCustodyError("ARCHIVE_CUSTODY_MANIFEST_MISMATCH", source_id)
            if self.lifecycle is None:
                raise ArchiveCustodyError("NATIVE_INTELLIGENCE_UNAVAILABLE")
            if source_path is None and not destination.is_dir():
                raise ArchiveCustodyError("ARCHIVE_CUSTODY_BUNDLE_MISSING", source_id)
            entries = self._bundle_entries(source_path if source_path is not None else destination)
            sealed = validate_sealed_manifest(dict(self.lifecycle.seal_manifest({
                "producer_id": original["producer_id"], "source_class": original["source_class"],
                "source_locator": original["source_locator"], "entries": entries,
            })))
            if sealed != original:
                raise ArchiveCustodyError("ARCHIVE_CUSTODY_BYTES_MISMATCH", source_id)
            return original
        except ArchiveCustodyError:
            raise
        except Exception as exc:
            raise ArchiveCustodyError(
                "ARCHIVE_CUSTODY_VALIDATION_FAILED", f"{source_id}:{type(exc).__name__}:{exc}",
            ) from exc

    @staticmethod
    def _require_archive_producer(sealed: Mapping[str, Any], producer_id: str | None) -> None:
        if producer_id != sealed["producer_id"]:
            raise ArchiveCustodyError("ARCHIVE_CUSTODY_PRODUCER_MISMATCH", sealed["source_id"])

    def _apply_archive_event(
        self, event: Mapping[str, Any], prepared: dict[str, dict[str, Any]],
        terminal: set[str], refused: set[str],
    ) -> str | None:
        kind = event.get("event_type")
        if kind not in {"ARCHIVE_PREPARED", "ARCHIVE_COMMITTED", "ARCHIVE_RECOVERED"}:
            return None
        source_id, record = event.get("source_id"), event.get("record")
        try:
            self._archive_record_path(source_id, record)
            if source_id in refused:
                return None
            prior = prepared.get(source_id)
            if kind == "ARCHIVE_PREPARED" and prior is None:
                prepared[source_id] = record
            elif prior != record:
                raise ArchiveCustodyError("ARCHIVE_CUSTODY_JOURNAL_CONFLICT", source_id)
            if kind != "ARCHIVE_PREPARED":
                terminal.add(source_id)
        except (ArchiveCustodyError, OSError, TypeError) as exc:
            if type(source_id) is str:
                refused.add(source_id)
                prepared.pop(source_id, None)
                terminal.discard(source_id)
            return str(exc)
        return None

    def _archive_journal_state(self):
        prepared: dict[str, dict[str, Any]] = {}
        terminal: set[str] = set()
        refused: set[str] = set()
        residuals: list[str] = []
        for event in self._journal_events():
            residual = self._apply_archive_event(event, prepared, terminal, refused)
            if residual is not None:
                residuals.append(residual)
        return prepared, terminal, residuals

    def _validate_archive_projection(self, archive_map: Mapping[str, Any],
                                     prepared: Mapping[str, Any]) -> None:
        for source_id, record in archive_map.items():
            self._archive_record_path(source_id, record)
            if source_id not in prepared or record != prepared[source_id]:
                raise ArchiveCustodyError("ARCHIVE_CUSTODY_PROJECTION_MISMATCH", source_id)

    def _recover_prepared_archives(self, manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
        prepared, terminal, residuals = self._archive_journal_state()
        if residuals:
            raise ArchiveCustodyError("ARCHIVE_CUSTODY_JOURNAL_INVALID", ";".join(residuals))
        archive_map = manifest["archived_sources"]
        self._validate_archive_projection(archive_map, prepared)
        changed = False
        recovered = []
        for source_id, record in prepared.items():
            if source_id in terminal and source_id in archive_map:
                continue  # Existing cold bytes are checked when a work obligation consumes them.
            destination = self._archive_record_path(source_id, record)
            if not destination.exists():
                if source_id in terminal or source_id in archive_map:
                    raise ArchiveCustodyError("ARCHIVE_CUSTODY_BUNDLE_MISSING", source_id)
                continue  # A pre-move preparation may be retried with the original record.
            self._validate_archive(source_id, record)
            if source_id not in archive_map:
                archive_map[source_id] = record
                changed = True
            if source_id not in terminal:
                recovered.append((source_id, record))
        if changed or recovered:
            self._write_manifest(manifest)
        for source_id, record in recovered:
            self._append_journal("ARCHIVE_RECOVERED", source_id=source_id, record=record)
        return prepared

    def _write_recovery_projection(self) -> Path:
        """Project journal evidence without replacing a corrupt archive manifest."""
        projection = self._empty_manifest()
        projection["recovered_from"] = str(self.manifest_file.relative_to(self.repo_root)).replace(
            "\\", "/"
        )
        projection["recovery_mode"] = "DERIVED_FROM_ARCHIVE_JOURNAL"
        archived_sources = projection["archived_sources"]
        prepared, terminal, residuals = self._archive_journal_state()
        for source_id, record in prepared.items():
            try:
                if source_id not in terminal:
                    raise ArchiveCustodyError("ARCHIVE_CUSTODY_TERMINAL_MISSING", source_id)
                self._validate_archive(source_id, record)
                archived_sources[source_id] = record
            except (ArchiveCustodyError, OSError) as exc:
                residuals.append(str(exc))
        projection["recovery_residuals"] = residuals
        self._atomic_write_json(self.recovery_projection_file, projection)
        return self.recovery_projection_file

    def _bundle_entries(self, run_dir: Path) -> list[dict[str, Any]]:
        return bundle_entries(self.repo_root, run_dir)

    def _infer_producer_id(self, run_path: Path, rel_queue: str) -> str:
        if "research" in rel_queue:
            return "omega_research"
        if "omc" in rel_queue:
            return "omega_research_papers"
        if "paper_reviews" in rel_queue:
            return "omega_paper_review_swarm"
        if "harvest" in rel_queue or "snapshot" in rel_queue:
            return "omega_autopoiesis_harvest"
        if "_woland" in rel_queue:
            return "omega_woland"
        return "omega_symbol_game"

    def _infer_source_class(self, run_path: Path, rel_queue: str) -> str:
        if run_path.is_file():
            if "harvest" in rel_queue or run_path.name.startswith("snap_"):
                return "harvest_snapshot"
            if run_path.suffix.lower() == ".jsonl":
                return "omc_dag_report"
            if run_path.suffix.lower() == ".json":
                return "paper_review_receipt"
            if run_path.suffix.lower() == ".md":
                return "paper_review_markdown"
        if (run_path / "research_evidence_envelope.json").is_file():
            return "research_envelope"
        if (run_path / "mission.json").is_file() or (
            "research" in rel_queue and (run_path / "summary.json").is_file()
        ):
            return "research_run"
        if "paper_reviews" in rel_queue:
            return "paper_review_bundle"
        return "run_bundle"

    def _seal_source(
        self, run_dir: Path, rel_queue: str, producer_id: str | None = None
    ) -> Mapping[str, Any]:
        archivable_source_path(self.repo_root, run_dir)
        if self.lifecycle is None:
            raise RuntimeError(
                "NATIVE_INTELLIGENCE_UNAVAILABLE: lifecycle adapter is not configured"
            )
        entries = self._bundle_entries(run_dir)
        producer = producer_id or self._infer_producer_id(run_dir, rel_queue)
        source_class = self._infer_source_class(run_dir, rel_queue)
        locator = self.source_locator(run_dir)
        sealed = validate_sealed_manifest(dict(self.lifecycle.seal_manifest(
            {
                "producer_id": producer,
                "source_class": source_class,
                "source_locator": locator,
                "entries": entries,
            }
        )))
        if (sealed["producer_id"], sealed["source_class"], sealed["source_locator"], sealed["entries"]) != (
            producer, source_class, locator, entries,
        ):
            raise ArchiveCustodyError("NATIVE_MANIFEST_OUTPUT_INVALID")
        manifest_path = checked_path(
            self.repo_root,
            self.source_manifest_root / f"{sealed['source_id'].removeprefix('sha256:')}.json",
        )
        if manifest_path.exists():
            if validate_sealed_manifest(_read_object(manifest_path)) != sealed:
                raise ArchiveCustodyError("ARCHIVE_CUSTODY_MANIFEST_MISMATCH", sealed["source_id"])
        else:
            self._atomic_write_json(manifest_path, sealed)
        return sealed
