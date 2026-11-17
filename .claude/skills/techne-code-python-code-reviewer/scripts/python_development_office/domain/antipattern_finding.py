"""AntipatternFinding domain entity for python_development_office."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AntipatternFinding:
    path: str
    line: int
    column: int
    rule_id: int
    rule_code: str
    category: str
    message: str
    remediation: str
    severity: str = "error"
