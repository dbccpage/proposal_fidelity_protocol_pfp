"""ScanResult domain entity for python_development_office."""

from __future__ import annotations

from dataclasses import dataclass, field

from python_development_office.domain.antipattern_finding import (
    AntipatternFinding,
)


@dataclass
class ScanResult:
    schema: str = "core.python_development_office.v1"
    files_scanned: int = 0
    modules_indexed: int = 0
    total_findings: int = 0
    findings: list[AntipatternFinding] = field(default_factory=list)
    authority_effect: str = "None"
