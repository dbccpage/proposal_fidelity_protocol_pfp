"""Harvest mining and archive commit operations."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from .archive_custody import (
    ArchiveCustodyError,
    archivable_source_path,
)
from .digestion_models import (
    CORPORA_MANIFEST_SCHEMA,
    HARVEST_DIGESTION_RECEIPT_SCHEMA,
    DigestionReceipt,
    DigestionRecord,
    _SourceWork,
)


@dataclass(frozen=True)
class _HarvestPaths:
    source: Path
    receipts: Path
    destination: Path


@dataclass
class _HarvestFacts:
    categories: dict[str, int] = field(default_factory=dict)
    record_count: int = 0
    merkle_roots: set[str] = field(default_factory=set)
    antibodies: set[str] = field(default_factory=set)
    sessions: set[str] = field(default_factory=set)
    findings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ArchiveCommit:
    run_path: Path
    record: DigestionRecord
    work_keys: Sequence[str]
    prepared: bool = False
    producer_id: str | None = None


class HarvestArchiveOperations:
    def _harvest_paths(
        self, snapshots: Path | None, receipts: Path | None, destination: Path | None
    ) -> _HarvestPaths:
        return _HarvestPaths(
            Path(snapshots).resolve() if snapshots else self.harvest_snapshots_dir,
            Path(receipts).resolve() if receipts else self.harvest_receipts_dir,
            Path(destination).resolve() if destination else self.archive_harvest_snapshots_dir,
        )

    def _retained_harvest_receipts(self, directory: Path) -> list[dict[str, Any]]:
        if not directory.is_dir():
            return []
        retained: list[dict[str, Any]] = []
        for receipt_file in sorted(directory.iterdir(), key=lambda path: path.name):
            if not receipt_file.is_file() or not receipt_file.name.endswith(".receipt.json"):
                continue
            raw = receipt_file.read_bytes()
            try:
                payload = json.loads(raw.decode("utf-8"))
            except Exception:
                payload = {}
            retained.append({
                "receipt_id": payload.get("receipt_id", receipt_file.stem),
                "filename": receipt_file.name,
                "path": self._relative_path(receipt_file),
                "file_sha256": hashlib.sha256(raw).hexdigest(),
                "timestamp": payload.get("timestamp"),
                "teamwork_files_preserved": payload.get("teamwork_files_preserved", 0),
                "antibodies_cataloged": payload.get("antibodies_cataloged", 0),
                "skills_mined": payload.get("skills_mined", 0),
                "antibodies_mined": payload.get("antibodies_mined", 0),
                "cas_objects_written": payload.get("cas_objects_written", 0),
                "merkle_roots": payload.get("merkle_roots", {}),
                "authority_effect": payload.get("authority_effect", "None"),
                "status": "RETAINED",
            })
        return retained

    @staticmethod
    def _snapshots_in(directory: Path) -> list[Path]:
        if not directory.is_dir():
            return []
        return [
            path for path in sorted(directory.iterdir(), key=lambda item: item.name)
            if path.is_file() and path.name.startswith("snap_")
            and path.suffix.lower() == ".json"
        ]

    def _snapshot_sources(self, paths: _HarvestPaths) -> tuple[list[Path], bool]:
        snapshots = self._snapshots_in(paths.source)
        if snapshots:
            return snapshots, False
        archived = self._snapshots_in(paths.destination)
        return archived, bool(archived)

    @staticmethod
    def _mine_snapshot_records(
        source_name: object, records: object, facts: _HarvestFacts
    ) -> None:
        if type(records) is not list:
            facts.findings.append(f"SNAPSHOT_RECORDS_INVALID:{source_name}")
            return
        facts.record_count += len(records)
        for record in records:
            if type(record) is not dict:
                continue
            relative = record.get("relative_path")
            if source_name == "antibodies" and type(relative) is str and relative.startswith("ab_"):
                facts.antibodies.add(relative)
            if "teamwork" in str(source_name) and "/" in str(relative or ""):
                facts.sessions.add(str(relative).split("/")[0])

    def _mine_snapshot(self, path: Path, facts: _HarvestFacts) -> None:
        try:
            payload = json.loads(path.read_bytes().decode("utf-8"))
        except Exception as exc:
            facts.findings.append(f"UNREADABLE_SNAPSHOT:{path.name}:{exc}")
            return
        if type(payload) is not dict:
            facts.findings.append(f"SNAPSHOT_NOT_OBJECT:{path.name}")
            return
        source_name = payload.get("source_name", "unknown")
        facts.categories[str(source_name)] = facts.categories.get(str(source_name), 0) + 1
        merkle = payload.get("merkle_root")
        if merkle:
            facts.merkle_roots.add(str(merkle))
        self._mine_snapshot_records(source_name, payload.get("records", []), facts)

    def _archive_snapshots(
        self, snapshots: Sequence[Path], destination: Path, dry_run: bool, archived: bool
    ) -> list[str]:
        if archived:
            return [path.name for path in snapshots]
        if dry_run or not snapshots:
            return []
        self.filesystem.ensure_directory(destination)
        names: list[str] = []
        for snapshot in snapshots:
            self._move_path(snapshot, destination / snapshot.name)
            names.append(snapshot.name)
        return names

    def _relative_path(self, path: Path) -> str:
        try:
            return path.relative_to(self.repo_root).as_posix()
        except ValueError:
            return path.as_posix()

    def _harvest_entry(
        self, paths: _HarvestPaths, facts: _HarvestFacts,
        snapshots: Sequence[Path], archived_names: Sequence[str],
    ) -> dict[str, Any]:
        return {
            "original_path": self._relative_path(paths.source),
            "archive_path": self._relative_path(paths.destination),
            "total_snapshots_examined": len(snapshots),
            "snapshots_archived_count": len(archived_names),
            "snapshots_archived": sorted(archived_names),
            "snapshots_by_category": facts.categories,
            "total_records_indexed": facts.record_count,
            "unique_merkle_roots": sorted(facts.merkle_roots),
            "mined_antibody_references_count": len(facts.antibodies),
            "mined_antibody_references": sorted(facts.antibodies),
            "mined_teamwork_sessions_count": len(facts.sessions),
            "findings_count": len(facts.findings),
            "findings": facts.findings,
            "archived_at_utc": self._now_utc(),
        }

    def _harvest_result(
        self, facts: _HarvestFacts, retained: Sequence[Mapping[str, Any]],
        snapshots: Sequence[Path], archived_names: Sequence[str], dry_run: bool,
    ) -> dict[str, Any]:
        return {
            "schema_version": HARVEST_DIGESTION_RECEIPT_SCHEMA,
            "authority_effect": "None",
            "dry_run": dry_run,
            "total_snapshots_examined": len(snapshots),
            "snapshots_archived_count": len(archived_names),
            "retained_receipts_count": len(retained),
            "retained_receipts": list(retained),
            "categories": facts.categories,
            "total_records_indexed": facts.record_count,
            "unique_merkle_roots_count": len(facts.merkle_roots),
            "mined_antibody_references_count": len(facts.antibodies),
            "mined_teamwork_sessions_count": len(facts.sessions),
            "status": "PASS" if not facts.findings else "OBSTRUCTIONS_FOUND",
        }

    def mine_harvest_snapshots(
        self,
        *,
        snapshots_dir: Optional[Path] = None,
        receipts_dir: Optional[Path] = None,
        archive_dest: Optional[Path] = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Mine _ic/nara/harvest/snapshots/ into corpora_archive_manifest.json and retain receipts.

        Treats snapshot files (snap_*.json) as an input source to mine, extracts
        Merkle root linkages, category metrics, antibody references, and session files,
        safely archives cleared snapshots into cold storage, and retains all receipts in
        _ic/nara/harvest/ intact.
        """
        paths = self._harvest_paths(snapshots_dir, receipts_dir, archive_dest)
        retained = self._retained_harvest_receipts(paths.receipts)
        snapshots, already_archived = self._snapshot_sources(paths)
        facts = _HarvestFacts()
        for snapshot in snapshots:
            self._mine_snapshot(snapshot, facts)
        archived_names = self._archive_snapshots(
            snapshots, paths.destination, dry_run, already_archived,
        )
        manifest = self._load_corpora_manifest()
        manifest["harvest_snapshots"] = {
            **self._harvest_entry(paths, facts, snapshots, archived_names),
            "retained_receipts": retained,
        }
        if not dry_run:
            self.filesystem.ensure_directory(self.corpora_manifest_file.parent)
            self._atomic_write_json(self.corpora_manifest_file, manifest)
        return self._harvest_result(facts, retained, snapshots, archived_names, dry_run)

    def _load_corpora_manifest(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.corpora_manifest_file.is_file():
            try:
                payload = json.loads(self.corpora_manifest_file.read_text(encoding="utf-8"))
            except Exception:
                payload = {}
        payload.setdefault("schema_version", CORPORA_MANIFEST_SCHEMA)
        payload.setdefault("authority_effect", "None")
        payload["updated_at_utc"] = self._now_utc()
        payload.setdefault("status", "TERMINALLY_DIGESTED")
        return payload

    def _commit_archive_record(
        self, commit: ArchiveCommit, manifest: dict[str, Any], receipt: DigestionReceipt
    ) -> None:
        run_path, record = commit.run_path, commit.record
        source_id, payload = record.source_id, asdict(record)
        try:
            target_dir = self._archive_record_path(source_id, payload)
            archivable_source_path(self.repo_root, run_path)
            if target_dir.exists():
                raise ArchiveCustodyError("ARCHIVE_CUSTODY_TARGET_EXISTS", str(target_dir))
            sealed = self._validate_archive(source_id, payload, source_path=run_path)
            if commit.work_keys:
                self._require_archive_producer(sealed, commit.producer_id)
            if not commit.prepared:
                self._append_journal("ARCHIVE_PREPARED", source_id=source_id, record=payload)
            if run_path.is_file():
                if target_dir.exists():
                    raise ArchiveCustodyError("ARCHIVE_CUSTODY_TARGET_EXISTS", str(target_dir))
                self.filesystem.create_directory(target_dir)
                self._move_path(run_path, target_dir / run_path.name)
            else:
                self._move_path(run_path, target_dir)
            self._validate_archive(source_id, payload)
            manifest["archived_sources"][source_id] = payload
            self._write_manifest(manifest)
            self._append_journal("ARCHIVE_COMMITTED", source_id=source_id, record=payload)
            receipt.records.append(record)
            receipt.total_runs_archived += 1
            self._record_work_state(
                receipt, commit.work_keys, lifecycle_state=record.digestion_state,
                detail={"source_id": source_id, "archive_path": record.archive_path,
                        "certificate_id": record.certificate_id or ""}, completed=True,
            )
        except Exception as exc:
            message = f"ARCHIVE_COMMIT_FAILED:{source_id}:{type(exc).__name__}:{exc}"
            receipt.errors.append(message)
            self._record_work_state(receipt, commit.work_keys, lifecycle_state="BLOCKED",
                                    detail={"source_id": source_id, "reason": message})

    def _resume_archive_work(self, work: _SourceWork, manifest: dict[str, Any],
                              pending_prepared: Mapping[str, Any], receipt: DigestionReceipt) -> bool:
        try:
            recovered = self._archived_record_for_source_path(
                manifest["archived_sources"], work.run_path, work.locator,
            )
            pending = self._archived_record_for_source_path(
                pending_prepared, work.run_path, work.locator,
            )
            if recovered is not None and not work.run_path.exists():
                sealed = self._validate_archive(recovered["source_id"], recovered)
                self._require_archive_producer(sealed, work.producer_id)
                self._record_work_state(
                    receipt, work.work_keys, lifecycle_state=recovered["digestion_state"],
                    detail={"source_id": recovered["source_id"], "archive_path": recovered["archive_path"],
                            "archive_status": "RECOVERED"}, completed=True,
                )
                return True
            if pending is not None:
                self._commit_archive_record(
                    ArchiveCommit(
                        work.run_path, DigestionRecord(**pending), work.work_keys,
                        prepared=True, producer_id=work.producer_id,
                    ),
                    manifest,
                    receipt,
                )
                return True
        except Exception as exc:
            message = f"ARCHIVE_CUSTODY_SOURCE_REFUSED:{type(exc).__name__}:{exc}"
            receipt.errors.append(message)
            self._record_work_state(receipt, work.work_keys, lifecycle_state="BLOCKED",
                                    detail={"reason": message})
            return True
        return False
