"""Lifecycle evaluation and source-work coordination."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .archive_custody import (
    ArchiveCustodyError,
    checked_path,
    relative_parts,
)
from .digestion_models import (
    CHECKER_VERSION,
    CORPORA_MANIFEST_SCHEMA,
    EXTRACTOR_VERSION,
    SOURCE_SCHEMA,
    DigestionReceipt,
    _Extraction,
    _safe_component,
    _SourceWork,
)
from .transfer_custody import validate_candidate_revision


@dataclass(frozen=True)
class _TransferContext:
    run_id: str
    source_id: str
    manifest_sha256: str


class LifecycleOperations:
    def _candidate_file(self, seeder: Any, antibody_id: str) -> Path:
        lookup = getattr(seeder, "get_antibody_path", None)
        if callable(lookup):
            return Path(lookup(antibody_id))
        # Compatibility for injected pre-port seeders; production binds the lookup.
        for directory in (
            self.antibodies_dir, self.repo_root / "eis/antibodies", self._path("antibodies"),
        ):
            candidate = directory / f"{antibody_id}.json"
            if candidate.is_file():
                return candidate
        return self.antibodies_dir / f"{antibody_id}.json"

    def _transfers_for_findings(
        self,
        *,
        findings: Sequence[str],
        run_id: str,
        source_id: str,
        manifest_sha256: str,
    ) -> tuple[dict[str, dict[str, str]], list[str]]:
        if not findings:
            return {}, []
        warnings: list[str] = []
        try:
            seeder = self.seeder_factory(self.repo_root)
            farmed = seeder.farm_antibodies_from_defects(
                findings, run_id=run_id, task_id=f"digestion:{source_id}"
            )
        except Exception as exc:
            return {}, [f"DEFECT_TRANSFER_FAILED:{type(exc).__name__}:{exc}"]
        by_pattern = {getattr(antibody, "target_pattern", ""): antibody for antibody in farmed}
        transfers: dict[str, dict[str, str]] = {}
        receipt_rows: list[dict[str, str]] = []
        context = _TransferContext(run_id, source_id, manifest_sha256)
        for finding in findings:
            antibody = by_pattern.get(finding)
            if antibody is None:
                warnings.append(f"FINDING_TRANSFER_PENDING:{finding}")
                continue
            transfer = self._candidate_transfer(seeder, antibody, finding, context)
            if isinstance(transfer, str):
                warnings.append(transfer)
                continue
            transfers[finding] = transfer
            receipt_rows.append({"finding": finding, **transfer})
        if transfers:
            self._atomic_write_json(
                self.transfer_root / f"{source_id.removeprefix('sha256:')}.json",
                {
                    "schema_version": "core.intelligence.transfer-receipt.v1",
                    "source_id": source_id,
                    "source_manifest_sha256": manifest_sha256,
                    "transfers": sorted(receipt_rows, key=lambda row: row["finding"]),
                    "authority_effect": "None",
                },
            )
        return transfers, warnings

    def _candidate_transfer(
        self, seeder: Any, antibody: Any, finding: str, context: _TransferContext
    ) -> dict[str, str] | str:
        antibody_id = getattr(antibody, "antibody_id", "")
        if type(antibody_id) is not str or not antibody_id:
            return f"FINDING_DESTINATION_MISSING:{finding}"
        try:
            reference, locator = validate_candidate_revision(
                self.repo_root, self._candidate_file(seeder, antibody_id),
                self.transfer_root / "revisions", antibody_id=antibody_id,
                finding=finding, run_id=context.run_id, source_id=context.source_id,
            )
        except Exception as exc:
            return f"FINDING_DESTINATION_INVALID:{finding}:{type(exc).__name__}:{exc}"
        return {
            "destination_id": f"candidate_antibody:{antibody_id}",
            "target_revision": reference,
            "acknowledgement_ref": reference,
            "kind": "CANDIDATE_ANTIBODY_OPEN_OBLIGATION",
            "target_revision_locator": locator,
        }

    @staticmethod
    def _finding_id(finding: str) -> str:
        return "finding:sha256:" + hashlib.sha256(finding.encode("utf-8")).hexdigest()

    def _evaluate_lifecycle(
        self,
        *,
        sealed: Mapping[str, Any],
        extraction: _Extraction,
        transfers: Mapping[str, Mapping[str, str]],
    ) -> Mapping[str, Any]:
        if self.lifecycle is None:
            raise RuntimeError(
                "NATIVE_INTELLIGENCE_UNAVAILABLE: lifecycle adapter is not configured"
            )
        findings = []
        for finding in extraction.findings:
            row: dict[str, Any] = {
                "finding_id": self._finding_id(finding),
                "kind": "OBSERVED_DEFECT_OR_OBLIGATION",
                "applicable": True,
                "evidence_refs": [],
            }
            if finding in transfers:
                row["transfer"] = dict(transfers[finding])
            findings.append(row)
        request = {
            "source": {
                "source_id": sealed["source_id"],
                "producer_id": sealed["producer_id"],
                "source_class": sealed["source_class"],
                "source_schema_version": SOURCE_SCHEMA,
                "manifest_sha256": sealed["manifest_sha256"],
                "sealed": True,
                "producer_lease_active": False,
                "review_scope": "core.intelligence.digestion.v1",
            },
            "extraction": {
                "complete": not extraction.coverage_gaps and not extraction.parse_residuals,
                "extractor_version": EXTRACTOR_VERSION,
                "checker_version": CHECKER_VERSION,
                "coverage_gaps": extraction.coverage_gaps,
                "parse_residuals": extraction.parse_residuals,
            },
            "findings": findings,
        }
        return self.lifecycle.evaluate_lifecycle(request)

    @staticmethod
    def _residual_messages(decision: Mapping[str, Any]) -> list[str]:
        residuals = decision.get("residuals", [])
        if type(residuals) is not list:
            return ["NATIVE_LIFECYCLE_OUTPUT_INVALID: residuals must be a list"]
        return [
            f"{item.get('code', 'UNKNOWN')}:{item.get('message', '')}"
            for item in residuals
            if type(item) is dict
        ]

    def _archive_name(self, run_id: str, source_id: str) -> str:
        return f"{_safe_component(run_id)}--{source_id.removeprefix('sha256:')[:16]}"

    @staticmethod
    def _is_discovered_source(path: Path) -> bool:
        if path.name.startswith(".") or path.name.endswith(".tmp") or path.name == "data_types":
            return False
        if path.is_dir():
            return True
        return (
            path.is_file() and path.suffix.lower() in (".jsonl", ".json", ".md")
            and path.name not in ("README.md", "paper_reviews_digest.jsonl", "archive_manifest.json")
        )

    def _queue_directories(self, rel_queue: str) -> tuple[Path, ...]:
        primary = checked_path(
            self.repo_root, self.intelligence_path(self.repo_root, rel_queue),
        )
        candidates = [primary]
        adversary_prefix = "_intelligence/_adversary"
        if rel_queue == adversary_prefix or rel_queue.startswith(f"{adversary_prefix}/"):
            suffix = rel_queue.removeprefix(adversary_prefix).lstrip("/")
            historical = self.repo_root / "_ic" / "darpa" / "adversary" / suffix
            historical = checked_path(self.repo_root, historical)
            if historical != primary:
                candidates.append(historical)
        return tuple(path for path in candidates if path.is_dir())

    def _discover_queue(self, rel_queue: str) -> dict[str, _SourceWork]:
        items: dict[str, _SourceWork] = {}
        for queue_dir in self._queue_directories(rel_queue):
            for run_path in sorted(queue_dir.iterdir(), key=lambda path: path.name):
                checked_path(self.repo_root, run_path)
                if self._is_discovered_source(run_path):
                    items[self.source_locator(run_path)] = _SourceWork(run_path, rel_queue)
        return items

    def _discovered_work(self, receipt: DigestionReceipt) -> dict[str, _SourceWork]:
        items: dict[str, _SourceWork] = {}
        for rel_queue in self.ACTIVE_QUEUES:
            try:
                items.update(self._discover_queue(rel_queue))
            except Exception as exc:
                receipt.errors.append(
                    f"ARCHIVE_CUSTODY_SOURCE_DISCOVERY_REFUSED:{rel_queue}:{exc}"
                )
        return items

    def _pending_source(self, work: Mapping[str, Any], receipt: DigestionReceipt,
                        archived_sources: Mapping[str, Any]):
        locator, work_key, producer_id = (work.get(key) for key in (
            "source_locator", "work_key", "producer_id",
        ))
        if type(locator) is not str or type(work_key) is not str:
            receipt.errors.append("COLLECTION_WORK_INVALID: source_locator and work_key are required")
            return None
        if type(producer_id) is not str or not producer_id.strip():
            receipt.errors.append(f"ARCHIVE_CUSTODY_COLLECTION_PRODUCER_INVALID:{work_key}")
            return None
        try:
            relative_parts(locator)
            try:
                candidate = self.resolve_source_directory(locator)
            except Exception as exc:
                record = self._record_for_locator(archived_sources, locator)
                candidate = checked_path(self.repo_root, self.repo_root / locator)
                if (getattr(exc, "code", None) != "HISTORICAL_BYTES_UNAVAILABLE"
                        or not locator.startswith("_ic/") or record is None or candidate.exists()):
                    raise
                sealed = self._validate_archive(record["source_id"], record)
                self._require_archive_producer(sealed, producer_id)
            candidate = checked_path(self.repo_root, candidate)
        except Exception as exc:
            receipt.errors.append(f"COLLECTION_SOURCE_UNAVAILABLE:{locator}:{exc}")
            return None
        return locator, candidate, work_key, producer_id if type(producer_id) is str else None

    @staticmethod
    def _merge_pending_source(items, source) -> None:
        locator, candidate, work_key, producer_id = source
        prior = items.get(locator)
        if prior is None:
            items[locator] = _SourceWork(candidate, locator.rsplit("/", 1)[0], producer_id,
                                         (work_key,), locator)
            return
        if prior.producer_id is not None and prior.producer_id != producer_id:
            raise ArchiveCustodyError("ARCHIVE_CUSTODY_PRODUCER_CONFLICT", locator)
        work_keys = prior.work_keys if work_key in prior.work_keys else (*prior.work_keys, work_key)
        items[locator] = _SourceWork(
            candidate if candidate.is_dir() else prior.run_path, prior.source_queue,
            prior.producer_id or producer_id, work_keys, locator,
        )

    def _source_work_items(self, receipt: DigestionReceipt,
                           archived_sources: Mapping[str, Any] | None = None) -> list[_SourceWork]:
        """Deduplicate discovery and queued obligations by their bound logical locator."""
        items = self._discovered_work(receipt)
        if self.collection is None:
            return sorted(items.values(), key=lambda item: item.run_path.as_posix())
        try:
            pending = self.collection.pending_work()
        except Exception as exc:
            receipt.errors.append(f"COLLECTION_WORK_READ_FAILED:{type(exc).__name__}:{exc}")
            return sorted(items.values(), key=lambda item: item.run_path.as_posix())
        for work in pending:
            source = self._pending_source(work, receipt, archived_sources or {})
            if source is not None:
                try:
                    self._merge_pending_source(items, source)
                except ArchiveCustodyError as exc:
                    receipt.errors.append(str(exc))
        return sorted(items.values(), key=lambda item: item.run_path.as_posix())

    def _record_work_state(
        self,
        receipt: DigestionReceipt,
        work_keys: Sequence[str],
        *,
        lifecycle_state: str,
        detail: Mapping[str, Any],
        completed: bool = False,
    ) -> None:
        if self.collection is None:
            return
        for work_key in work_keys:
            try:
                if completed:
                    self.collection.complete_work(
                        work_key, lifecycle_state=lifecycle_state, detail=detail
                    )
                else:
                    self.collection.record_lifecycle(
                        work_key, lifecycle_state=lifecycle_state, detail=detail
                    )
            except Exception as exc:
                receipt.errors.append(
                    f"COLLECTION_WORK_UPDATE_FAILED:{work_key}:{type(exc).__name__}:{exc}"
                )

    def _archived_record_for_source_path(
        self, archived_sources: Mapping[str, Any], run_path: Path, locator: str | None = None,
    ) -> Mapping[str, Any] | None:
        try:
            original_path = locator if locator is not None else self.source_locator(run_path)
        except ValueError:
            return None
        return self._record_for_locator(archived_sources, original_path)

    @staticmethod
    def _record_for_locator(records: Mapping[str, Any], locator: str) -> Mapping[str, Any] | None:
        matches = [row for row in records.values() if row["original_path"] == locator]
        if len(matches) > 1:
            raise ArchiveCustodyError("ARCHIVE_CUSTODY_SOURCE_AMBIGUOUS", locator)
        return matches[0] if matches else None

    def _sync_corpora_manifest(self, manifest: Mapping[str, Any]) -> None:
        """Syncs the digested runs state to the consolidated corpora archive manifest."""
        manifest_payload: dict[str, Any] = {}
        if self.corpora_manifest_file.is_file():
            try:
                manifest_payload = json.loads(self.corpora_manifest_file.read_text(encoding="utf-8"))
            except Exception:
                manifest_payload = {}
        manifest_payload.setdefault("schema_version", CORPORA_MANIFEST_SCHEMA)
        manifest_payload.setdefault("authority_effect", "None")
        manifest_payload["updated_at_utc"] = self._now_utc()
        manifest_payload.setdefault("status", "TERMINALLY_DIGESTED")
        manifest_payload["digested_runs"] = {
            "manifest_path": self.manifest_file.relative_to(self.repo_root).as_posix(),
            "total_archived_sources": len(manifest.get("archived_sources", {})),
            "updated_at_utc": manifest.get("updated_at_utc", self._now_utc()),
        }
        self.filesystem.ensure_directory(self.corpora_manifest_file.parent)
        self._atomic_write_json(self.corpora_manifest_file, manifest_payload)
