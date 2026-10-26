"""Inward ports for documentation-integrity application orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from omega_engine_pfp.domain.kernel.result import Result

from .models import ExecutionReceipt, FindingLedger, IntegrityRefusal, IntegrityRequest


class ClockPort(Protocol):
    def now(self) -> str: ...


class DocumentationIntegrityGatewayPort(Protocol):
    def execute(
        self, request: IntegrityRequest, started_at: str
    ) -> Result[ExecutionReceipt, IntegrityRefusal]: ...


class FindingOutputPort(Protocol):
    def emit(self, findings: FindingLedger) -> None: ...
    def info(self, message: str) -> None: ...


class FileSystemPort(Protocol):
    def read_text(self, path: Path) -> str: ...
    def write_text_atomic(self, path: Path, text: str) -> None: ...
    def is_file(self, path: Path) -> bool: ...


class ProcessPort(Protocol):
    def run(
        self, argv: tuple[str, ...], cwd: Path, input_bytes: bytes | None = None
    ) -> tuple[int, bytes, bytes]: ...
