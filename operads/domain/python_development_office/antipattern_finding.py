#!/usr/bin/env python3
"""AntipatternFinding domain value object for python_development_office."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AntipatternFinding:
    """Immutable finding emitted by python development office inspection rules."""

    path: str
    line: int
    column: int
    rule_id: int
    rule_code: str
    category: str
    message: str
    remediation: str
    severity: str = "error"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, AntipatternFinding)
        return (
            self.path == other.path
            and self.line == other.line
            and self.column == other.column
            and self.rule_id == other.rule_id
            and self.rule_code == other.rule_code
            and self.category == other.category
            and self.message == other.message
            and self.remediation == other.remediation
            and self.severity == other.severity
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.path,
                self.line,
                self.column,
                self.rule_id,
                self.rule_code,
                self.category,
                self.message,
                self.remediation,
                self.severity,
            )
        )
