"""Filesystem adapter for RunFolderV1 storage and sealing (U01).

AuthorityEffect: None.
Writes into staged temporary directories and atomically renames upon seal.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from omega_engine_operating_system.adapters.intelligence_custody.ic_routing import (
    IcMigrationRefusal,
    intelligence_path,
    read_activation,
    safe_path,
)
from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (
    try_resolve_intelligence_repo_root,
)
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_pfp.domain.ports.run_recorder import (
    RunId,
    RunRecorder,
    RunStream,
    RunTrigger,
)

MANIFEST_SCHEMA_V1 = "omega.run_folder.manifest.v1"
RECEIPT_SCHEMA_V1 = "omega.run_folder.receipt.v1"
AUTHORITY_EFFECT_NONE = "None"


def sanitize_task_slug(task: str) -> str:
    """Sanitize task slug to at most 40 safe characters."""
    slug = "".join(c if (c.isalnum() or c in ("_", "-")) else "_" for c in task)
    if not slug:
        slug = "task"
    return slug[:40]


def compute_file_sha256(path: Path) -> str:
    """Compute lowercase hex SHA-256 of file bytes."""
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_run_folder_name(
    utc: str,
    trigger: RunTrigger,
    task: str,
    nonce: int = 0,
) -> tuple[str, str]:
    """Compute canonical folder name <utc>_<trigger>_<slug>_<id>."""
    slug = sanitize_task_slug(task)
    hasher = hashlib.sha256()
    hasher.update(f"{utc}:{trigger.value}:{slug}:{nonce}".encode("utf-8"))
    digest = hasher.hexdigest()
    id_12 = digest[:12]
    return f"{utc}_{trigger.value}_{slug}_{id_12}", id_12


@dataclass
class _StagedRunInfo:
    run_id: RunId
    custody_root: Path
    staged_dir: Path
    final_dir: Path
    manifest: dict[str, Any]


class FileRunRecorder(RunRecorder):
    """File-backed RunRecorder streaming to staging dirs and sealing atomically."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root
        self._open_runs: dict[str, _StagedRunInfo] = {}

    def _resolve_runs_dir(self) -> Result[tuple[Path, Path], Refusal]:
        if self._root is not None:
            base = self._root
        else:
            res = try_resolve_intelligence_repo_root()
            if res.is_err:
                return Err(res.unwrap_err())
            base = res.unwrap()
        try:
            base = base.absolute()
            runs_dir = intelligence_path(base, "_intelligence/symbol_game/runs")
            runs_dir.mkdir(parents=True, exist_ok=True)
        except IcMigrationRefusal as exc:
            return Err(Refusal(
                code=exc.code,
                message=f"Run custody unavailable under {base}: {exc}",
                locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
            ))
        except OSError as e:
            return Err(
                Refusal(
                    code="RUN_DIRECTORY_CREATION_FAILED",
                    message=f"Failed to resolve or create runs directory under {base}: {e}",
                    locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
                )
            )
        return Ok((base, runs_dir))

    def _validate_run_custody(
        self, info: _StagedRunInfo, *filenames: str,
    ) -> Result[None, Refusal]:
        """Recheck the original owner and every target before a run mutation.

        This uses the existing cooperative filesystem boundary, not an OS
        sandbox against directory replacement concurrent with a checked write.
        """
        try:
            read_activation(info.custody_root)
            safe_path(info.custody_root, info.staged_dir.relative_to(info.custody_root).as_posix())
            targets = (
                info.final_dir,
                *(info.staged_dir / name for name in filenames),
                *info.staged_dir.iterdir(),
            )
            for target in targets:
                checked = safe_path(
                    info.custody_root, target.relative_to(info.custody_root).as_posix(),
                )
                if checked.is_file() and checked.stat().st_nlink != 1:
                    raise IcMigrationRefusal("HARD_LINK_REFUSED", str(checked))
        except IcMigrationRefusal as exc:
            return Err(Refusal(
                code=exc.code,
                message=f"Run custody unavailable: {exc}",
                locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
            ))
        except (OSError, ValueError) as exc:
            return Err(Refusal(
                code="RUN_CUSTODY_UNAVAILABLE",
                message=f"Could not validate run custody: {exc}",
                locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
            ))
        return Ok(None)

    def open_run(
        self,
        trigger: RunTrigger,
        task_slug: str,
        *,
        parent_run_ids: Sequence[str] = (),
        run_mode: str = "fixture",
        budget_micro_usd: int | None = None,
        code_hashes: Mapping[str, str] | None = None,
        model_registry_entries: Sequence[str] = (),
    ) -> Result[RunId, Refusal]:
        runs_dir_res = self._resolve_runs_dir()
        if runs_dir_res.is_err:
            return Err(runs_dir_res.unwrap_err())
        custody_root, runs_dir = runs_dir_res.unwrap()

        utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        folder_name, _ = generate_run_folder_name(utc, trigger, task_slug, os.getpid())
        final_dir = runs_dir / folder_name
        if final_dir.exists():
            return Err(
                Refusal(
                    code="RUN_FOLDER_EXISTS",
                    message=f"Run folder already exists: {final_dir}",
                    locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
                )
            )

        staged_dir = runs_dir / f".{folder_name}.{uuid.uuid4().hex[:8]}"
        try:
            staged_dir.mkdir(parents=True, exist_ok=False)
        except OSError as e:
            return Err(
                Refusal(
                    code="STAGING_DIR_CREATION_FAILED",
                    message=f"Could not create staging dir at {staged_dir}: {e}",
                    locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
                )
            )

        manifest = {
            "schema_version": MANIFEST_SCHEMA_V1,
            "run_id": folder_name,
            "utc": utc,
            "trigger": trigger.value,
            "task_slug": sanitize_task_slug(task_slug),
            "parent_run_ids": list(parent_run_ids),
            "git_revision": None,
            "git_dirty": False,
            "code_hashes": dict(code_hashes or {}),
            "model_registry_entries": list(model_registry_entries),
            "budget_ceiling_micro_usd": budget_micro_usd,
            "run_mode": run_mode,
            "authority_effect": AUTHORITY_EFFECT_NONE,
        }

        manifest_path = staged_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

        run_id = RunId(folder_name)
        self._open_runs[folder_name] = _StagedRunInfo(
            run_id=run_id,
            custody_root=custody_root,
            staged_dir=staged_dir,
            final_dir=final_dir,
            manifest=manifest,
        )
        return Ok(run_id)

    def append(
        self,
        run_id: RunId,
        stream: RunStream,
        row: Mapping[str, Any],
    ) -> Result[None, Refusal]:
        info = self._open_runs.get(run_id.value)
        if info is None:
            return Err(
                Refusal(
                    code="RUN_NOT_OPEN",
                    message=f"Run {run_id.value} is not open for writing",
                    locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
                )
            )

        custody = self._validate_run_custody(info, stream.value)
        if custody.is_err:
            return Err(custody.unwrap_err())
        stream_file = info.staged_dir / stream.value
        try:
            with stream_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(dict(row), sort_keys=True) + "\n")
                f.flush()
                os.fsync(f.fileno())
        except OSError as e:
            return Err(
                Refusal(
                    code="STREAM_APPEND_FAILED",
                    message=f"Failed to append to {stream.value}: {e}",
                    locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
                )
            )
        return Ok(None)

    def _seal_and_rename(
        self,
        info: _StagedRunInfo,
        status: str,
        reason: str | None = None,
    ) -> Result[str, Refusal]:
        custody = self._validate_run_custody(info, "receipt.json")
        if custody.is_err:
            return Err(custody.unwrap_err())
        # Compute hashes of all files in staged_dir except receipt.json
        files_map: dict[str, str] = {}
        try:
            for entry in info.staged_dir.iterdir():
                if entry.is_file() and entry.name != "receipt.json" and not entry.name.startswith("."):
                    files_map[entry.name] = compute_file_sha256(entry)
        except OSError as exc:
            return Err(Refusal(
                code="RUN_SEAL_FAILED",
                message=f"Could not hash run files: {exc}",
                locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
            ))

        utc_now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        receipt = {
            "schema_version": RECEIPT_SCHEMA_V1,
            "run_id": info.run_id.value,
            "status": status,
            "reason": reason,
            "files": dict(sorted(files_map.items())),
            "chain_heads": {},
            "sealed_at_utc": utc_now,
            "authority_effect": AUTHORITY_EFFECT_NONE,
        }

        receipt_path = info.staged_dir / "receipt.json"
        try:
            receipt_path.write_text(
                json.dumps(receipt, sort_keys=True, separators=(",", ":")), encoding="utf-8",
            )
        except OSError as exc:
            return Err(Refusal(
                code="RUN_SEAL_FAILED",
                message=f"Could not write run receipt: {exc}",
                locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
            ))

        # Atomic rename into final_dir
        if info.final_dir.exists():
            return Err(
                Refusal(
                    code="RUN_FOLDER_EXISTS",
                    message=f"Destination run directory already exists: {info.final_dir}",
                    locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
                )
            )
        try:
            info.staged_dir.rename(info.final_dir)
        except OSError as e:
            return Err(
                Refusal(
                    code="RUN_RENAME_FAILED",
                    message=f"Failed to atomically rename {info.staged_dir} to {info.final_dir}: {e}",
                    locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
                )
            )

        del self._open_runs[info.run_id.value]
        return Ok(str(info.final_dir))

    def close(
        self,
        run_id: RunId,
        summary: Mapping[str, Any],
        report_md: str,
    ) -> Result[str, Refusal]:
        info = self._open_runs.get(run_id.value)
        if info is None:
            return Err(
                Refusal(
                    code="RUN_NOT_OPEN",
                    message=f"Run {run_id.value} is not open",
                    locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
                )
            )

        custody = self._validate_run_custody(info, "summary.json", "report.md", "receipt.json")
        if custody.is_err:
            return Err(custody.unwrap_err())
        try:
            summary_path = info.staged_dir / "summary.json"
            summary_path.write_text(json.dumps(dict(summary), indent=2, sort_keys=True), encoding="utf-8")
            report_path = info.staged_dir / "report.md"
            report_path.write_text(report_md, encoding="utf-8")
        except OSError as exc:
            return Err(Refusal(
                code="RUN_WRITE_FAILED",
                message=f"Could not write run summary/report: {exc}",
                locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
            ))

        return self._seal_and_rename(info, status="SEALED")

    def abort(
        self,
        run_id: RunId,
        reason: str,
        *,
        summary: Mapping[str, Any] | None = None,
    ) -> Result[str, Refusal]:
        info = self._open_runs.get(run_id.value)
        if info is None:
            return Err(
                Refusal(
                    code="RUN_NOT_OPEN",
                    message=f"Run {run_id.value} is not open",
                    locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
                )
            )

        custody = self._validate_run_custody(info, "summary.json", "report.md", "receipt.json")
        if custody.is_err:
            return Err(custody.unwrap_err())
        summary_dict = dict(summary or {})
        summary_dict["status"] = "ABORTED"
        summary_dict["abort_reason"] = reason

        try:
            summary_path = info.staged_dir / "summary.json"
            summary_path.write_text(json.dumps(summary_dict, indent=2, sort_keys=True), encoding="utf-8")
            report_path = info.staged_dir / "report.md"
            report_path.write_text(f"# Run Aborted\n\nReason: {reason}\n", encoding="utf-8")
        except OSError as exc:
            return Err(Refusal(
                code="RUN_WRITE_FAILED",
                message=f"Could not write aborted summary/report: {exc}",
                locus="omega_engine_pfp.infrastructure.persistence.file_run_recorder",
            ))

        return self._seal_and_rename(info, status="ABORTED", reason=reason)


__all__ = [
    "AUTHORITY_EFFECT_NONE",
    "FileRunRecorder",
    "MANIFEST_SCHEMA_V1",
    "RECEIPT_SCHEMA_V1",
    "compute_file_sha256",
    "generate_run_folder_name",
    "sanitize_task_slug",
]
