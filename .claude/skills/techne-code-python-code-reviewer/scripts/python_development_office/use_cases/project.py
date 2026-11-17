"""Project scanner, package resolution, module graph construction, and two-pass orchestration."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from python_development_office.domain import (
    AntipatternFinding,
    ArchitectureConfig,
    ModuleInfo,
    ScanResult,
)
from python_development_office.use_cases.rules.registry import (
    RuleRegistry,
)
from python_development_office.use_cases.visitor import (
    scan_file_ast,
)


class ProjectScanner:
    """Orchestrates two-pass scanning across files, modules, and architecture layers."""

    def __init__(
        self,
        config: ArchitectureConfig,
        registry: RuleRegistry | None = None,
        project_root: Path | None = None,
    ) -> None:
        self.config = config
        self.registry = registry or RuleRegistry.create_default()
        self.project_root = project_root or Path.cwd()
        self.modules: list[ModuleInfo] = []
        self.module_graph: dict[str, ModuleInfo] = {}
        self.unresolved_targets: list[Path] = []

    def discover_files(self, targets: Iterable[Path | str]) -> list[Path]:
        """Discover Python files across specified target directories and files."""
        discovered: set[Path] = set()
        self.unresolved_targets.clear()
        for t in targets:
            path = Path(t)
            if not path.is_absolute():
                path = (self.project_root / path).resolve()
            else:
                path = path.resolve()

            if path.is_file() and path.suffix == ".py":
                discovered.add(path)
            elif path.is_dir():
                directory_files = {f.resolve() for f in path.rglob("*.py") if f.is_file()}
                discovered.update(directory_files)
                if not directory_files:
                    self.unresolved_targets.append(path)
            else:
                self.unresolved_targets.append(path)
        return sorted(discovered)

    def compute_package_name(self, file_path: Path) -> str:
        """Compute Python dotted module path relative to repository or source roots."""
        resolved = file_path.resolve()
        try:
            rel = resolved.relative_to(self.project_root.resolve())
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
        all_findings: list[AntipatternFinding] = [
            AntipatternFinding(
                path=str(path),
                line=0,
                column=0,
                rule_id=0,
                rule_code="UNRESOLVED_SCAN_TARGET",
                category="pitfall",
                message="Scan target is missing or contains no Python files",
                remediation="Pass an existing Python file or nonempty Python tree",
                severity="error",
            )
            for path in self.unresolved_targets
        ]
        self.modules.clear()
        self.module_graph.clear()

        # Pass 1: AST Scan & Module Metadata Extraction
        ast_rules = () if arch_only else self.registry.ast_rules
        for file_path in files:
            findings, mod_info = scan_file_ast(file_path, ast_rules, self.config)
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
