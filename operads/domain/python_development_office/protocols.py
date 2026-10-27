# -*- coding: utf-8 -*-
"""protocols.py: Domain ports and interfaces for python development office scanning and architecture review.

Clean Architecture Layer: Domain Ports / Interfaces
AuthorityEffect: None
"""

from __future__ import annotations

from typing import Protocol, Sequence

from operads.domain.operad.errors import Result
from operads.domain.python_development_office.antipattern_finding import (
    AntipatternFinding,
)
from operads.domain.python_development_office.errors import (
    SourceReadError,
)
from operads.domain.python_development_office.module_info import (
    ModuleInfo,
)
from operads.domain.python_development_office.scan_result import (
    ScanResult,
)


class AstScannerProtocol(Protocol):
    """Abstract interface for parsing Python source files and extracting AST metadata."""

    def scan_file(self, path: str) -> ModuleInfo: ...

    def scan_tree(self, repo_root: str) -> list[ModuleInfo]: ...


class AntipatternRuleProtocol(Protocol):
    """Abstract interface for executing a single python antipattern verification rule."""

    def evaluate(self, module: ModuleInfo) -> list[AntipatternFinding]: ...


class ArchitectureAuditorProtocol(Protocol):
    """Abstract interface for auditing module dependencies against Clean Architecture layer rules."""

    def audit_module(self, module: ModuleInfo) -> list[AntipatternFinding]: ...


class PythonCodeReviewerProtocol(Protocol):
    """Abstract interface for executing full multi-rule Python code reviews."""

    def review_codebase(self, repo_root: str) -> ScanResult: ...


class SourceRepositoryProtocol(Protocol):
    """Filesystem-independent source acquisition boundary."""

    def current_directory(self) -> str: ...

    def resolve_path(self, path: str, project_root: str) -> str: ...

    def discover(self, targets: Sequence[str], project_root: str) -> tuple[str, ...]: ...

    def read_source(self, path: str) -> Result[str, SourceReadError]: ...
