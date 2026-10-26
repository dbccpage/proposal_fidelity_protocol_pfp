"""Pinned native process adapter for Woland's finite report operation."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost


@dataclass(frozen=True)
class NativeReportOperation:
    binary: Path
    root: Path

    def identity(self) -> str:
        digest = hashlib.sha256(b"omega.report-operation-implementation.v1\0")
        # The binary covers Rust, embedded source and contract. Python byte pins
        # cover the actual orchestration and persistence used on both tasks.
        paths = [self.binary, *[self.root / path for path in (
            "omega_engine_woland/use_cases/report_operation.py",
            "omega_engine_woland/domain/report_operation_ports.py",
            "omega_engine_woland/use_cases/teamwork.py",
            "omega_engine_woland/use_cases/teamwork_pfp.py",
            "omega_engine_pfp/infrastructure/task_turn.py",
            "omega_engine_pfp/domain/contracts/pfp_runtime.py",
            "omega_engine_pfp/use_cases/pfp_prompt.py",
            "omega_engine_pfp/use_cases/pfp_proposal.py",
            "omega_engine_operations/domain/rop/result.py",
            "omega_engine_operating_system/adapters/rust_host/ffi.py",
            "omega_engine_operating_system/adapters/rust_host/report_operation.py",
            "omega_engine_operating_system/infrastructure/sqlite_report_episodes.py",
        )]]
        for path in paths:
            digest.update(path.stat().st_size.to_bytes(8, "big"))
            with path.open("rb") as stream:
                while data := stream.read(1024 * 1024):
                    digest.update(data)
        return digest.hexdigest()

    def invoke(self, action: str, payload: dict):
        return RustSymbolGameHost(binary=self.binary, timeout_seconds=30).invoke_runtime(action, payload)
