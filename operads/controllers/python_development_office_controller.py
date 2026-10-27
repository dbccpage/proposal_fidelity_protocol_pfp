"""Controller orchestrating Python Development Office architecture and pitfall scans."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, TextIO

from operads.application.python_development_office.project import (
    ProjectScanner,
)
from operads.application.python_development_office.quality_inventory import (
    PythonQualityInventoryGate,
    QualityInventoryDependencies,
)
from operads.application.python_development_office.rules.registry import (
    RuleRegistry,
)
from operads.domain.operad.errors import Err
from operads.domain.python_development_office import (
    ArchitectureConfig,
    ScanResult,
)
from operads.domain.python_development_office.quality_errors import (
    QualityPolicyLoadError,
)
from operads.infrastructure.python_development_office.config import (
    load_config,
)
from operads.infrastructure.python_development_office.output.console_output import (
    format_console_output,
)
from operads.infrastructure.python_development_office.output.json_output import (
    format_json_output,
)
from operads.infrastructure.python_development_office.output.quality_json_output import (
    format_quality_receipt,
    format_quality_refusal,
)
from operads.infrastructure.python_development_office.quality_adapters import (
    FileSystemPythonInventoryRepository,
    RuffComplexityAnalyzer,
)
from operads.infrastructure.python_development_office.quality_policy import (
    load_quality_policy,
)
from operads.infrastructure.python_development_office.source_repository import (
    FileSystemSourceRepository,
)
from operads.infrastructure.python_development_office.test_execution_receipts import (
    FileSystemTestExecutionReceiptRepository,
    SystemUtcClock,
)


@dataclass(frozen=True)
class AuditRenderRequest:
    """Presentation options for the architecture and pitfall scanner."""

    targets: Iterable[Path | str]
    arch_only: bool = False
    pitfalls_only: bool = False
    as_json: bool = False
    stream: TextIO | None = None
    project_root: Path | None = None


@dataclass(frozen=True)
class QualityInventoryRequest:
    """Presentation and filesystem inputs for the quality inventory."""

    target: Path | str
    project_root: Path
    policy_path: Path | None = None
    receipt_directory: Path | None = None
    stream: TextIO | None = None


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
            sources=FileSystemSourceRepository(),
        )
        return scanner.scan(
            targets=targets,
            arch_only=arch_only,
            pitfalls_only=pitfalls_only,
        )

    def audit_and_render(
        self,
        request: AuditRenderRequest,
    ) -> int:
        """Execute scan and render formatted results to stream."""
        out_stream = request.stream if request.stream is not None else sys.stdout
        result = self.scan_targets(
            targets=request.targets,
            arch_only=request.arch_only,
            pitfalls_only=request.pitfalls_only,
            project_root=request.project_root,
        )
        if request.as_json:
            out_stream.write(format_json_output(result) + "\n")
        else:
            format_console_output(result, stream=out_stream)

        # Return exit code: 1 if errors found, 0 otherwise
        has_errors = any(f.severity == "error" for f in result.findings)
        return 1 if has_errors else 0

    def quality_inventory_and_render(
        self,
        request: QualityInventoryRequest,
    ) -> int:
        """Execute the versioned fail-closed quality inventory and emit JSON."""

        out_stream = request.stream if request.stream is not None else sys.stdout
        try:
            policy, policy_bytes = load_quality_policy(request.policy_path)
        except QualityPolicyLoadError as exc:
            out_stream.write(format_quality_refusal(exc) + "\n")
            return 2
        gate = PythonQualityInventoryGate(
            QualityInventoryDependencies(
                project_root=request.project_root,
                policy=policy,
                policy_bytes=policy_bytes,
                sources=FileSystemPythonInventoryRepository(),
                complexity=RuffComplexityAnalyzer(),
                execution_receipts=FileSystemTestExecutionReceiptRepository(),
                clock=SystemUtcClock(),
            )
        )
        result = gate.run(
            request.target, receipt_directory=request.receipt_directory
        )
        if isinstance(result, Err):
            out_stream.write(format_quality_refusal(result.error) + "\n")
            return 2
        out_stream.write(format_quality_receipt(result.value) + "\n")
        return 0 if result.value.status == "STRUCTURAL_PASS" else 1
