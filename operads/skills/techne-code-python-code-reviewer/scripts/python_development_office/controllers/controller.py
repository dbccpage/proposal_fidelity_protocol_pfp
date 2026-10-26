"""Controller orchestrating Python Development Office architecture and pitfall scans."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, TextIO

from python_development_office.domain import (
    ArchitectureConfig,
    ScanResult,
)
from python_development_office.infrastructure.config import (
    load_config,
)
from python_development_office.use_cases.output.console_output import (
    format_console_output,
)
from python_development_office.use_cases.output.json_output import (
    format_json_output,
)
from python_development_office.use_cases.project import (
    ProjectScanner,
)
from python_development_office.use_cases.rules.registry import (
    RuleRegistry,
)


class PythonDevelopmentOfficeController:
    """Orchestrates codebase architecture scanning, rule evaluation, and output serialization."""

    def __init__(self, config: ArchitectureConfig | None = None) -> None:
        self.config = config or load_config()
        self.registry = RuleRegistry.create_default()

    def scan_targets(
        self,
        targets: Iterable[Path | str],
        arch_only: bool = False,
        pitfalls_only: bool = False,
        project_root: Path | None = None,
    ) -> ScanResult:
        """Execute scan across specified directories and files."""
        scanner = ProjectScanner(
            config=self.config,
            registry=self.registry,
            project_root=project_root,
        )
        return scanner.scan(
            targets=targets,
            arch_only=arch_only,
            pitfalls_only=pitfalls_only,
        )

    def audit_and_render(
        self,
        targets: Iterable[Path | str],
        arch_only: bool = False,
        pitfalls_only: bool = False,
        as_json: bool = False,
        stream: TextIO | None = None,
        project_root: Path | None = None,
    ) -> int:
        """Execute scan and render formatted results to stream."""
        out_stream = stream if stream is not None else sys.stdout
        result = self.scan_targets(
            targets=targets,
            arch_only=arch_only,
            pitfalls_only=pitfalls_only,
            project_root=project_root,
        )
        if as_json:
            out_stream.write(format_json_output(result) + "\n")
        else:
            format_console_output(result, stream=out_stream)

        # Return exit code: 1 if errors found, 0 otherwise
        has_errors = any(f.severity == "error" for f in result.findings)
        return 1 if has_errors else 0
