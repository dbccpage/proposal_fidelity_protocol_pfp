"""Value objects for the documentation-integrity bounded context."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class DocumentationCommand(str, Enum):
    INVENTORY = "inventory"
    VALIDATE = "validate"


@dataclass(frozen=True, slots=True)
class IntegrityRefusal:
    code: str
    message: str
    authority_effect: str = "None"


@dataclass(frozen=True, slots=True)
class IntegrityRequest:
    command: DocumentationCommand
    repo_root: Path
    options: Any


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    command: DocumentationCommand
    started_at: str
    exit_code: int
    error_count: int = 0
    warning_count: int = 0
    authority_effect: str = "None"


@dataclass(slots=True)
class FindingLedger:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def checked(self, message: str) -> None:
        self.checks.append(message)

    def as_dict(self) -> dict[str, Any]:
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "checks": self.checks,
            "ok": not self.errors,
        }
