"""RecordTraceUseCase: Concurrency-safe atomic recording of diagnostic traces.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

try:
    from domain.evidence import DiagnosticObservation
    from domain.ports import FileLockPort, null_file_lock
except (ImportError, ValueError):
    from ...domain.evidence import DiagnosticObservation
    from ...domain.ports import FileLockPort, null_file_lock


class RecordTraceUseCase:
    """Application use case for appending diagnostic observation records safely."""

    def __init__(
        self,
        trace_path: Path,
        lock_path: Path,
        lock_port: FileLockPort | None = None,
    ) -> None:
        self.trace_path = trace_path
        self.lock_path = lock_path
        self.lock_port = lock_port if lock_port is not None else null_file_lock

    def record(self, observation: DiagnosticObservation) -> None:
        with self.lock_port(self.lock_path):
            records: List[Dict[str, Any]] = []
            if self.trace_path.exists():
                try:
                    records = json.loads(self.trace_path.read_text(encoding="utf-8"))
                except Exception:
                    records = []

            record_dict = {
                "skill_id": observation.skill_id,
                "run_id": observation.run_id,
                "phi_before": observation.phi_before,
                "phi_after": observation.phi_after,
                "delta_phi": observation.delta_phi,
                "authority_effect": "None",
            }
            records.append(record_dict)

            temp_path = self.trace_path.with_suffix(".tmp")
            temp_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
            temp_path.replace(self.trace_path)
