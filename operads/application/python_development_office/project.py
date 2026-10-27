"""Project scanner, package resolution, module graph construction, and two-pass orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from operads.application.python_development_office.rules.registry import (
    RuleRegistry,
)
from operads.application.python_development_office.visitor import (
    scan_source_ast,
)
from operads.domain.operad.errors import Err
from operads.domain.python_development_office import (
    AntipatternFinding,
    ArchitectureConfig,
    ModuleInfo,
    RuleCategory,
    ScanResult,
)
from operads.domain.python_development_office.protocols import (
    SourceRepositoryProtocol,
)


class ProjectScanner:
    """Orchestrates two-pass scanning across files, modules, and architecture layers."""

    def __init__(
        self,
        config: ArchitectureConfig,
        registry: RuleRegistry | None = None,
        project_root: Path | None = None,
        *,
        sources: SourceRepositoryProtocol,
    ) -> None:
        self.config = config
        self.registry = registry or RuleRegistry.create_default()
        self.sources = sources
        current_directory = sources.current_directory()
        self.project_root = Path(
            sources.resolve_path(str(project_root or current_directory), current_directory)
        )
        self.modules: list[ModuleInfo] = []
        self.module_graph: dict[str, ModuleInfo] = {}

    def discover_files(self, targets: Iterable[Path | str]) -> list[Path]:
        """Discover Python files across specified target directories and files."""
        return [
            Path(path)
            for path in self.sources.discover(
                tuple(str(target) for target in targets), str(self.project_root)
            )
        ]

    def compute_package_name(self, file_path: Path) -> str:
        """Compute Python dotted module path relative to repository or source roots."""
        resolved = Path(self.sources.resolve_path(str(file_path), str(self.project_root)))
        try:
            rel = resolved.relative_to(self.project_root)
            parts = list(rel.parts)
        except ValueError:
            parts = list(resolved.parts)

        # Strip .py extension
        if parts and parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]

        if parts and parts[-1] == "__init__":
            parts.pop()

        return ".".join(parts)

    def classify_layer(self, package_name: str, path: Path) -> str | None:
        """Classify module layer based on package naming and directory path tokens."""
        parts = set(package_name.split(".") + list(path.parts))
        for layer_name, patterns in self.config.layers.items():
            for pattern in patterns:
                if pattern in parts or any(p.startswith(pattern) for p in parts):
                    return layer_name
        return None

    def scan(
        self,
        targets: Iterable[Path | str],
        arch_only: bool = False,
        pitfalls_only: bool = False,
    ) -> ScanResult:
        """Execute two-pass analysis: AST pitfall scan + architecture module graph evaluation."""
        files = self.discover_files(targets)
        all_findings: list[AntipatternFinding] = []
        self.modules.clear()
        self.module_graph.clear()

        # Pass 1: AST Scan & Module Metadata Extraction
        ast_rules = () if arch_only else self.registry.ast_rules
        for file_path in files:
            source = self.sources.read_source(str(file_path))
            if isinstance(source, Err):
                all_findings.append(
                    AntipatternFinding(
                        path=str(file_path),
                        line=1,
                        column=0,
                        rule_id=0,
                        rule_code="UNPARSEABLE_FILE",
                        category=RuleCategory.PITFALL.value,
                        message=f"File could not be parsed: {source.error.detail}",
                        remediation="Ensure file has valid UTF-8 encoding and Python 3 syntax",
                        severity="error",
                    )
                )
                continue
            findings, mod_info = scan_source_ast(source.value, file_path, ast_rules, self.config)
            all_findings.extend(findings)

            if mod_info is not None:
                pkg_name = self.compute_package_name(file_path)
                mod_info.package = pkg_name
                mod_info.layer = self.classify_layer(pkg_name, file_path)
                self.modules.append(mod_info)
                self.module_graph[pkg_name] = mod_info

        # Build reverse dependency edges in module graph
        for mod in self.modules:
            for imp in mod.imports:
                if imp in self.module_graph:
                    self.module_graph[imp].imported_by.add(mod.package)

        # Pass 2: Architecture Rule Evaluation
        if not pitfalls_only and self.modules:
            for arch_rule in self.registry.architecture_rules:
                arch_findings = arch_rule.check_project(
                    self.modules, self.module_graph, self.config
                )
                all_findings.extend(arch_findings)

        # Sort findings canonically by (path, line, column, rule_id)
        sorted_findings = sorted(
            all_findings,
            key=lambda f: (f.path, f.line, f.column, f.rule_id),
        )

        return ScanResult(
            files_scanned=len(files),
            modules_indexed=len(self.modules),
            total_findings=len(sorted_findings),
            findings=sorted_findings,
            authority_effect="None",
        )
