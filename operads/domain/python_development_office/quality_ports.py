"""Ports used by the Python quality inventory application service."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence

from omega_engine_operads.domain.python_development_office.test_execution_receipt import (
    TestExecutionReceipt,
)


class PythonInventoryRepository(Protocol):
    """Source acquisition boundary for deterministic inventory scans."""

    def discover_python(
        self, target: str, excluded_directories: Sequence[str]
    ) -> tuple[str, ...]: ...

    def read_text(self, path: str) -> str: ...


class ComplexityAnalyzer(Protocol):
    """External McCabe analyzer boundary."""

    def c901_findings(self, target: str, maximum: int) -> tuple[tuple[str, int, str], ...]: ...


class TestExecutionReceiptRepository(Protocol):
    """Port for loading untrusted execution receipts without running commands."""

    def load(self, receipt_directory: str) -> tuple[TestExecutionReceipt, ...]: ...


class UtcClock(Protocol):
    """Clock boundary used for deterministic freshness decisions."""

    def now(self) -> datetime: ...
