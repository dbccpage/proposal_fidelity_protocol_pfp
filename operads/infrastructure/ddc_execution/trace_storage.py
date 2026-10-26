"""Strict trace custody; damaged or missing ledgers cannot become empty evidence."""

import json
import math
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from omega_engine_operads.domain.ddc_execution.constants import (
    EVIDENCE_TRACE_SCHEMA,
    REQUIRED_CONTRACTIVE_RUNS,
)
from omega_engine_operads.domain.ddc_execution.errors import TraceLedgerStorageError
from omega_engine_operads.domain.ddc_execution.value_objects import (
    ArtifactOutput,
    EvidenceTraceReport,
    ExecutionRunRecord,
)

from .registry import safe_skill_id

_HOSTS = (".agents", ".claude", ".codex", ".grok")


class FileTraceStorage:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def _path(self, skill_id: str, host: str = ".agents") -> Path:
        return self.repo_root / host / "skills" / safe_skill_id(skill_id) / "evidence_trace.json"

    def _destinations(self, skill_id: str) -> list[Path]:
        return [self._path(skill_id, host) for host in _HOSTS]

    def _require_mirrors(self, skill_id: str) -> None:
        for destination in self._destinations(skill_id):
            if not destination.parent.is_dir():
                raise ValueError(f"skill directory is absent: {destination}")

    def load_trace(self, skill_id: str) -> EvidenceTraceReport:
        path = self._path(skill_id)
        try:
            if path.stat().st_size > 1024 * 1024:
                raise ValueError("trace exceeds the 1 MiB limit")
            data = json.loads(path.read_text(encoding="utf-8"))
            if (
                not isinstance(data, dict)
                or data.get("schema") != EVIDENCE_TRACE_SCHEMA
                or data.get("skill_name") != skill_id
                or data.get("authority_effect") != "None"
            ):
                raise ValueError("trace schema, skill, or authority mismatch")
            rows = data["runs"]
            if not isinstance(rows, list):
                raise ValueError("runs must be a list")
            runs = []
            for row in rows:
                before, after = row["residual_before"], row["residual_after"]
                findings = row["findings_count"]
                if (
                    any(
                        type(value) not in (int, float) or not math.isfinite(value) or value < 0
                        for value in (before, after)
                    )
                    or type(findings) is not int
                    or findings < 0
                ):
                    raise ValueError("invalid residual or findings measurement")
                contractive = after < before and findings == 0
                if (
                    type(row["contractive"]) is not bool
                    or row["contractive"] != contractive
                    or row["residual_delta"] != after - before
                    or row["skill_name"] != skill_id
                ):
                    raise ValueError("inconsistent run measurement")
                output = row["output"]
                runs.append(
                    ExecutionRunRecord(
                        row["timestamp"],
                        skill_id,
                        tuple(row["source_colours"]),
                        row["target_colour"],
                        tuple(row.get("inputs", ())),
                        ArtifactOutput(output["path"], output["sha256"]),
                        before,
                        after,
                        after - before,
                        contractive,
                        findings,
                    )
                )
            total, contractive_count = len(runs), sum(run.contractive for run in runs)
            satisfied = contractive_count >= REQUIRED_CONTRACTIVE_RUNS
            if (
                type(data.get("total_runs")) is not int
                or data["total_runs"] != total
                or type(data.get("contractive_runs")) is not int
                or data["contractive_runs"] != contractive_count
                or data.get("required_contractive_runs") != REQUIRED_CONTRACTIVE_RUNS
                or type(data.get("residual_evidence_bar_satisfied")) is not bool
                or data["residual_evidence_bar_satisfied"] != satisfied
            ):
                raise ValueError("trace aggregates do not match its runs")
            self._require_mirrors(skill_id)
            return EvidenceTraceReport(
                EVIDENCE_TRACE_SCHEMA,
                skill_id,
                data["signature"],
                total,
                contractive_count,
                REQUIRED_CONTRACTIVE_RUNS,
                satisfied,
                "None",
                tuple(runs),
            )
        except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError) as exc:
            raise TraceLedgerStorageError(str(path), str(exc)) from exc

    def append_run(
        self, skill_id: str, record: ExecutionRunRecord, signature_str: str
    ) -> EvidenceTraceReport:
        previous = self.load_trace(skill_id)
        if previous.signature != signature_str:
            raise TraceLedgerStorageError(str(self._path(skill_id)), "signature mismatch")
        runs = (*previous.runs, record)
        count = sum(run.contractive for run in runs)
        report = EvidenceTraceReport(
            EVIDENCE_TRACE_SCHEMA,
            skill_id,
            signature_str,
            len(runs),
            count,
            REQUIRED_CONTRACTIVE_RUNS,
            count >= REQUIRED_CONTRACTIVE_RUNS,
            "None",
            runs,
        )
        encoded = (json.dumps(asdict(report), indent=2) + "\n").encode("utf-8")
        destinations = self._destinations(skill_id)
        priors = [
            destination.read_bytes() if destination.is_file() else None
            for destination in destinations
        ]
        temporary: list[Path] = []
        replaced: list[Path] = []
        try:
            for destination in destinations:
                with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
                    temporary.append(Path(handle.name))
                    handle.write(encoded)
                    handle.flush()
                    os.fsync(handle.fileno())
            for staging, destination in zip(temporary, destinations, strict=True):
                os.replace(staging, destination)
                replaced.append(destination)
        except OSError as exc:
            try:
                for destination, prior in zip(replaced, priors):
                    if prior is None:
                        destination.unlink(missing_ok=True)
                    else:
                        destination.write_bytes(prior)
            except OSError as restore_exc:
                raise TraceLedgerStorageError(
                    str(self._path(skill_id)),
                    f"{exc}; restoring replaced mirrors failed: {restore_exc}",
                ) from restore_exc
            raise TraceLedgerStorageError(str(self._path(skill_id)), str(exc)) from exc
        finally:
            for staging in temporary:
                staging.unlink(missing_ok=True)
        return report
