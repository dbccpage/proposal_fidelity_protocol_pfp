"""Supervised intelligence digestion orchestration and public entry points.

Custody, extraction, lifecycle, and harvest responsibilities live in focused
application collaborators.  This module owns construction and the single
archive workflow orchestration boundary.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from governance.domain.intelligence_community import canonical_intelligence_route
from operations.domain.rop.result import Err, Ok, Refusal, Result
from adversary.domain.intelligence_digestion import (
    IntelligenceCollectionPort,
    IntelligenceDigestionFileSystemPort,
    IntelligenceLifecyclePort,
)
from adversary.domain.native import NativeOperationPort

from .archive_custody import ArchiveCustodyError, checked_path
from .archive_operations import ArchiveCustodyOperations
from .digestion_models import (
    ArchiveJournalUnreadable,
    ArchiveManifestUnreadable,
    BlockedDigestion,
    DigestionReceipt,
    DigestionRecord,
    _Extraction,
    _SourceWork,
)
from .finding_extraction import FindingExtractionOperations
from .harvest_operations import ArchiveCommit, HarvestArchiveOperations
from .lifecycle_operations import LifecycleOperations


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _move_path(source: Path, destination: Path) -> None:
    shutil.move(str(source), str(destination))


@dataclass(frozen=True)
class DigestionDependencies:
    lifecycle: IntelligenceLifecyclePort | None = None
    collection: IntelligenceCollectionPort | None = None
    seeder_factory: Callable[[Path], Any] | None = None
    intelligence_path: Callable[[Path, str], Path] | None = None
    source_locator: Callable[[Path], str] | None = None
    resolve_source_directory: Callable[[str], Path] | None = None
    antibodies_dir: Path | None = None
    clock: Callable[[], datetime] = _utc_now
    move_path: Callable[[Path, Path], None] = _move_path
    filesystem: IntelligenceDigestionFileSystemPort | None = None


@dataclass(frozen=True)
class _RecoveryState:
    manifest: dict[str, Any]
    prepared: Mapping[str, Any]


@dataclass(frozen=True)
class _SourceEvaluation:
    sealed: Mapping[str, Any]
    extraction: _Extraction
    decision: Mapping[str, Any]


class IntelligenceDigestionService(
    ArchiveCustodyOperations,
    FindingExtractionOperations,
    LifecycleOperations,
    HarvestArchiveOperations,
):
    ACTIVE_QUEUES = (
        "_intelligence/_adversary/runs",
        "_intelligence/symbol_game/runs",
        "_intelligence/research/runs",
        "_intelligence/omc_dags",
        "_intelligence/core_paper_reviews",
    )

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        *,
        dependencies: DigestionDependencies | None = None,
        native_support: NativeOperationPort, **overrides: Any,
    ) -> None:
        self._native_support = native_support
        deps = replace(dependencies or DigestionDependencies(), **overrides)
        self.repo_root = Path(repo_root).absolute() if repo_root else self._find_repo_root()
        checked_path(self.repo_root, self.repo_root)
        self.intelligence_path = deps.intelligence_path or (
            lambda root, relative: root / canonical_intelligence_route(relative)
        )
        self.source_locator = deps.source_locator or (
            lambda path: path.relative_to(self.repo_root).as_posix()
        )
        self.resolve_source_directory = deps.resolve_source_directory or (
            lambda locator: self.repo_root / locator
        )
        self.intelligence_root = self.repo_root / "_ic"  # canonical storage root
        self.archive_root = self._path("archive/digested_runs")
        checked_path(self.repo_root, self.archive_root)
        filesystem = deps.filesystem
        if filesystem is None:
            from adversary.infrastructure.intelligence_digestion_filesystem import (
                LocalIntelligenceDigestionFileSystem,
            )

            filesystem = LocalIntelligenceDigestionFileSystem(self.repo_root)
        self.filesystem = filesystem
        self.filesystem.ensure_directory(self.archive_root)
        self.manifest_file = self.archive_root / "archive_manifest.json"
        self.recovery_projection_file = self.archive_root / "archive_manifest.recovered.json"
        self.journal_file = self.archive_root / "archive_journal.jsonl"
        self.oeos_root = self._path("oeos")
        self.source_manifest_root = self.oeos_root / "source_manifests"
        self.transfer_root = self.oeos_root / "transfers"
        self.corpora_manifest_file = self._path("archive/corpora_archive_manifest.json")
        self.harvest_snapshots_dir = self._path("harvest/snapshots")
        self.harvest_receipts_dir = self._path("harvest")
        self.archive_harvest_snapshots_dir = (
            self._path("archive/harvest/snapshots")
        )
        antibodies_dir = deps.antibodies_dir
        if antibodies_dir is None:
            from eis.domain.pharmacy_catalog import (
                PharmacyCatalogRepository,
            )
            from eis.infrastructure.pharmacy_writer import (
                filesystem_catalog_bytes,
            )

            antibodies_dir = PharmacyCatalogRepository.catalog_path(
                self.repo_root, filesystem_catalog_bytes
            ).parent
        self.antibodies_dir = antibodies_dir
        self.filesystem.ensure_directory(self.antibodies_dir)
        self.lifecycle = deps.lifecycle
        self.collection = deps.collection
        self.seeder_factory = deps.seeder_factory or self._default_seeder
        self._clock = deps.clock
        self._move_path = deps.move_path

    def _clock_now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("DIGESTION_CLOCK_NAIVE: clock must return an aware datetime")
        return now.astimezone(timezone.utc)

    def _now_utc(self) -> str:
        return self._clock_now().isoformat()

    def _path(self, suffix: str) -> Path:
        return self.intelligence_path(self.repo_root, "_intelligence/" + suffix)

    @staticmethod
    def _find_repo_root() -> Path:
        from operating_system.adapters.intelligence_custody.intelligence_root import (
            resolve_intelligence_repo_root,
        )

        return resolve_intelligence_repo_root()

    @staticmethod
    def _default_seeder(repo_root: Path) -> Any:
        from eis.domain.pharmacy_seeder import PharmacySeeder
        from eis.infrastructure.pharmacy_writer import (
            filesystem_byte_writer,
            filesystem_catalog_bytes,
        )

        return PharmacySeeder(
            repo_root,
            byte_writer=filesystem_byte_writer,
            byte_source=filesystem_catalog_bytes,
        )

    def _new_receipt(self) -> DigestionReceipt:
        now = self._clock_now()
        return DigestionReceipt(
            receipt_id=f"DIGEST_{now.strftime('%Y%m%d_%H%M%S')}",
            timestamp_utc=now.isoformat(),
            authority_effect="None",
            total_runs_examined=0,
            total_runs_archived=0,
        )

    def _recover_state(self, receipt: DigestionReceipt) -> _RecoveryState | None:
        try:
            manifest = self.load_manifest()
            prepared = self._recover_prepared_archives(manifest)
        except ArchiveManifestUnreadable as exc:
            receipt.errors.append(str(exc))
            try:
                recovered = self._write_recovery_projection()
                receipt.warnings.append(
                    "ARCHIVE_MANIFEST_RECOVERY_PROJECTION_WRITTEN:"
                    + str(recovered.relative_to(self.repo_root)).replace("\\", "/")
                )
            except (ArchiveJournalUnreadable, ArchiveCustodyError) as journal_error:
                receipt.errors.append(str(journal_error))
            except OSError as recovery_error:
                receipt.errors.append(
                    f"ARCHIVE_MANIFEST_RECOVERY_PROJECTION_FAILED:{recovery_error}"
                )
            return None
        except (ArchiveJournalUnreadable, ArchiveCustodyError) as exc:
            receipt.errors.append(str(exc))
            return None
        except Exception as exc:
            receipt.errors.append(f"ARCHIVE_CUSTODY_RECOVERY_FAILED:{type(exc).__name__}:{exc}")
            return None
        return _RecoveryState(manifest, prepared)

    def _mine_pending_harvest(self, receipt: DigestionReceipt) -> None:
        if self.harvest_snapshots_dir.is_dir() and any(
            path.name.startswith("snap_") for path in self.harvest_snapshots_dir.glob("*.json")
        ):
            try:
                self.mine_harvest_snapshots()
            except Exception as exc:
                receipt.warnings.append(f"HARVEST_SNAPSHOTS_MINING_FAILED:{exc}")

    def _record_evaluation_failure(
        self, work: _SourceWork, receipt: DigestionReceipt,
        sealed: Mapping[str, Any] | None, error: Exception,
    ) -> None:
        source_id = str(sealed["source_id"]) if sealed else None
        message = f"DIGESTION_EVALUATION_FAILED:{type(error).__name__}:{error}"
        receipt.blocked.append(BlockedDigestion(
            work.run_path.name, work.source_queue, source_id, "BLOCKED", [message],
        ))
        try:
            self._append_journal(
                "LIFECYCLE_BLOCKED", source_id=source_id,
                source_queue=work.source_queue, reason=message,
            )
        except OSError as journal_error:
            receipt.errors.append(f"DIGESTION_JOURNAL_WRITE_FAILED:{journal_error}")
        self._record_work_state(
            receipt, work.work_keys, lifecycle_state="BLOCKED",
            detail={"reason": message, "source_queue": work.source_queue},
        )

    def _evaluate_source(
        self, work: _SourceWork, receipt: DigestionReceipt
    ) -> _SourceEvaluation | None:
        sealed: Mapping[str, Any] | None = None
        try:
            sealed = self._seal_source(work.run_path, work.source_queue, work.producer_id)
            source_id = str(sealed["source_id"])
            self._append_journal(
                "SOURCE_REGISTERED", source_id=source_id, source_queue=work.source_queue,
                source_manifest_sha256=sealed["manifest_sha256"],
            )
            extraction = self._extract_run_findings(work.run_path)
            transfers: dict[str, dict[str, str]] = {}
            warnings: list[str] = []
            if not extraction.parse_residuals and not extraction.coverage_gaps:
                transfers, warnings = self._transfers_for_findings(
                    findings=extraction.findings, run_id=work.run_path.name,
                    source_id=source_id, manifest_sha256=str(sealed["manifest_sha256"]),
                )
            receipt.warnings.extend(warnings)
            decision = self._evaluate_lifecycle(
                sealed=sealed, extraction=extraction, transfers=transfers,
            )
            self._append_journal(
                "LIFECYCLE_EVALUATED", source_id=source_id,
                state=decision.get("state"), decision=decision,
            )
            return _SourceEvaluation(sealed, extraction, decision)
        except Exception as exc:
            self._record_evaluation_failure(work, receipt, sealed, exc)
            return None

    def _block_ineligible(
        self, work: _SourceWork, receipt: DigestionReceipt, evaluation: _SourceEvaluation
    ) -> bool:
        state = evaluation.decision.get("state")
        if evaluation.decision.get("archive_eligible") is True and state in {
            "ABSORBED", "DISCHARGED",
        }:
            return False
        residuals = self._residual_messages(evaluation.decision)
        source_id = str(evaluation.sealed["source_id"])
        receipt.blocked.append(BlockedDigestion(
            work.run_path.name, work.source_queue, source_id,
            str(state or "BLOCKED"), residuals,
        ))
        self._record_work_state(
            receipt, work.work_keys, lifecycle_state=str(state or "BLOCKED"),
            detail={"source_id": source_id, "residuals": residuals},
        )
        return True

    def _archive_target(
        self, work: _SourceWork, receipt: DigestionReceipt,
        evaluation: _SourceEvaluation, archived: Mapping[str, Any],
    ) -> Path | None:
        source_id = str(evaluation.sealed["source_id"])
        message: str | None = None
        if source_id in archived:
            message = "ARCHIVE_ALREADY_REGISTERED_SOURCE_STILL_PRESENT"
            receipt.blocked.append(BlockedDigestion(
                work.run_path.name, work.source_queue, source_id, "BLOCKED", [message],
            ))
        target = self.archive_root / self._archive_name(work.run_path.name, source_id)
        if message is None and target.exists():
            message = f"ARCHIVE_TARGET_EXISTS:{target.relative_to(self.repo_root).as_posix()}"
            receipt.errors.append(message)
        if message is None:
            return target
        self._record_work_state(
            receipt, work.work_keys, lifecycle_state="BLOCKED",
            detail={"source_id": source_id, "reason": message},
        )
        return None

    def _digestion_record(
        self, work: _SourceWork, evaluation: _SourceEvaluation, target: Path
    ) -> DigestionRecord:
        state = str(evaluation.decision.get("state"))
        certificate = evaluation.decision.get("certificate")
        certificate_id = certificate.get("certificate_id") if type(certificate) is dict else None
        return DigestionRecord(
            run_id=work.run_path.name,
            source_id=str(evaluation.sealed["source_id"]),
            source_queue=work.source_queue,
            original_path=self.source_locator(work.run_path),
            archive_path=target.relative_to(self.repo_root).as_posix(),
            archived_at_utc=self._now_utc(),
            evidence_sha256=str(evaluation.sealed["manifest_sha256"]),
            defects_count=len(evaluation.extraction.findings),
            defects_extracted=evaluation.extraction.findings,
            digestion_state=state,
            storage_state="COLD",
            certificate_id=str(certificate_id) if certificate_id else None,
            status=state,
            authority_effect="None",
        )

    def _process_source(
        self, work: _SourceWork, state: _RecoveryState,
        pending: Mapping[str, Any], receipt: DigestionReceipt,
    ) -> None:
        receipt.total_runs_examined += 1
        if self._resume_archive_work(work, state.manifest, pending, receipt):
            return
        evaluation = self._evaluate_source(work, receipt)
        if evaluation is None or self._block_ineligible(work, receipt, evaluation):
            return
        archived = state.manifest["archived_sources"]
        target = self._archive_target(work, receipt, evaluation, archived)
        if target is None:
            return
        record = self._digestion_record(work, evaluation, target)
        self._commit_archive_record(
            ArchiveCommit(
                work.run_path, record, work.work_keys, producer_id=work.producer_id,
            ),
            state.manifest,
            receipt,
        )

    def digest_and_archive(self) -> DigestionReceipt:
        receipt = self._new_receipt()
        state = self._recover_state(receipt)
        if state is None:
            return receipt
        self._mine_pending_harvest(receipt)
        archived = state.manifest["archived_sources"]
        pending = {key: value for key, value in state.prepared.items() if key not in archived}
        for work in self._source_work_items(receipt, archived):
            self._process_source(work, state, pending, receipt)
        return receipt

    def digest_and_archive_result(self) -> Result[DigestionReceipt, Refusal]:
        """Execute the fallible archive boundary with a typed refusal rail."""
        try:
            return Ok(self.digest_and_archive())
        except (OSError, ValueError, TypeError, RuntimeError, ArchiveCustodyError) as exc:
            return Err(Refusal(
                code="INTELLIGENCE_DIGESTION_REFUSED",
                message=f"{type(exc).__name__}: {exc}",
                locus="adversary.intelligence_digestion",
            ))


def read_run_findings(source: Path, *, native_support: NativeOperationPort) -> _Extraction:
    """Inspect one source without lifecycle writes, candidates or archival.

    Extraction methods are stateless. Bypass service construction because its
    initializer creates archival/pharmacy directories even before any intake.
    Historical findings are observations, not proof they remain unresolved.
    """
    service = IntelligenceDigestionService.__new__(IntelligenceDigestionService)
    service._native_support = native_support
    return service._extract_run_findings(Path(source))


def read_run_findings_result(source: Path, *, native_support: NativeOperationPort) -> Result[_Extraction, Refusal]:
    """Inspect one source on a typed railway for mockable application callers."""
    try:
        return Ok(read_run_findings(source, native_support=native_support))
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return Err(Refusal(
            code="INTELLIGENCE_SOURCE_READ_REFUSED",
            message=f"{type(exc).__name__}: {exc}",
            locus="adversary.intelligence_digestion",
        ))


def read_teamwork_findings(payload: Mapping[str, Any]) -> _Extraction:
    """Inspect the actual decoded run through the same explicit source profile."""
    service = IntelligenceDigestionService.__new__(IntelligenceDigestionService)
    gaps: list[str] = []
    findings = service._teamwork_findings({"teamwork": payload}, "current_run", gaps)
    return _Extraction(sorted(set(findings)), sorted(set(gaps)), [])


def digest_and_archive_intelligence(
    repo_root: Optional[Path] = None,
    *,
    lifecycle: IntelligenceLifecyclePort | None = None,
    collection: IntelligenceCollectionPort | None = None,
    native_support: NativeOperationPort,
) -> DigestionReceipt:
    """Compatibility entrypoint with the native lifecycle adapter by default."""
    resolved_root = (
        Path(repo_root).absolute() if repo_root else IntelligenceDigestionService._find_repo_root()
    )
    checked_path(resolved_root, resolved_root)
    if lifecycle is None:
        from operations.infrastructure.intelligence_digestion import (
            NativeIntelligenceLifecycle,
        )

        lifecycle = NativeIntelligenceLifecycle()
    if collection is None:
        from operations.infrastructure.intelligence_digestion import (
            DurableIntelligenceCollector,
        )

        collection = DurableIntelligenceCollector(resolved_root)
    from functools import partial

    from operating_system.adapters.intelligence_custody.ic_routing import (
        intelligence_path,
        intelligence_source_locator,
        resolve_source_directory,
    )
    from operations.infrastructure.intelligence_digestion.routed_pharmacy import (
        build_routed_pharmacy_seeder,
        routed_catalog_path,
    )

    service = IntelligenceDigestionService(
        resolved_root,
        antibodies_dir=routed_catalog_path(resolved_root).parent,
        seeder_factory=build_routed_pharmacy_seeder,
        intelligence_path=intelligence_path,
        source_locator=partial(intelligence_source_locator, resolved_root),
        resolve_source_directory=partial(resolve_source_directory, resolved_root),
        lifecycle=lifecycle,
        collection=collection,
        native_support=native_support,
    )
    return service.digest_and_archive()


def main(*, native_support: NativeOperationPort) -> int:
    parser = argparse.ArgumentParser(
        description="Engine Intelligence Digestion & Archival Runner"
    )
    parser.add_argument("--repo-root", type=Path, default=None, help="Root of repository")
    parser.add_argument("--json", action="store_true", help="Emit receipt in JSON format")
    args = parser.parse_args()

    try:
        receipt = digest_and_archive_intelligence(args.repo_root, native_support=native_support)
    except Exception as exc:
        error = {
            "schema_version": "core.intelligence.digestion-error.v1",
            "authority_effect": "None",
            "error": f"{type(exc).__name__}: {exc}",
        }
        if args.json:
            print(json.dumps(error, indent=2))
        else:
            print(error["error"], file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(receipt.to_dict(), indent=2))
    else:
        print(
            "Intelligence Digestion Complete. "
            f"Examined: {receipt.total_runs_examined}, Archived: {receipt.total_runs_archived}"
        )
        for record in receipt.records:
            print(f"  - [{record.source_id}] {record.digestion_state} -> {record.archive_path}")
        for blocked in receipt.blocked:
            print(f"  ! [{blocked.run_id}] {blocked.state}: {'; '.join(blocked.residuals)}")
    if receipt.errors:
        for error in receipt.errors:
            print(f"  ! {error}", file=sys.stderr)
        return 1
    return 0
