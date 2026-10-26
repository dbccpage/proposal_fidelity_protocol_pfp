#!/usr/bin/env python3
"""Single-root layout plus the operations architecture scanner.

AuthorityEffect: None.

A context with single_root_enforced in bounded_contexts.yaml must not contain a
nested directory named applications. That directory is a second layer root.
"""

from __future__ import annotations

import sys
from pathlib import Path

from check_inward_dependencies import MANIFEST, load_manifest

NESTED_LAYER_ROOT = "applications"


def check_single_root(repo_root: Path, manifest: dict) -> list[str]:
    violations: list[str] = []
    for context in manifest["bounded_contexts"]:
        if context["single_root_enforced"] is not True:
            continue
        root_name = context["canonical_root"]
        context_root = repo_root / root_name
        if not context_root.is_dir():
            violations.append(f"Bounded context missing: {root_name}")
            continue
        nested = [path for path in context_root.glob(f"**/{NESTED_LAYER_ROOT}") if path.is_dir()]
        if nested:
            rendered = ", ".join(str(path.relative_to(repo_root)) for path in nested)
            violations.append(f"Nested layer root '{NESTED_LAYER_ROOT}' in {root_name}: {rendered}")
    return violations


def check_operations_scanner(repo_root: Path) -> list[str]:
    violations: list[str] = []
    repo_str = str(repo_root.resolve())
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)

    try:
        from omega_engine_operads.application.python_development_office.project import (
            ProjectScanner,
        )
        from omega_engine_operads.domain.python_development_office.architecture_config import (
            ArchitectureConfig,
        )
        from omega_engine_operads.infrastructure.python_development_office.source_repository import (
            FileSystemSourceRepository,
        )

        scanner = ProjectScanner(
            ArchitectureConfig(),
            project_root=str(repo_root),
            sources=FileSystemSourceRepository(),
        )
        result = scanner.scan(["omega_engine_operations"], arch_only=True)
        for finding in result.findings:
            if (
                finding.category == "clean_arch"
                or finding.rule_code == "CLEAN_DEPENDENCY_INVERSION"
            ):
                violations.append(
                    f"{finding.rule_code} at {finding.path}:{finding.line} - {finding.message}"
                )
    except Exception as exc:
        violations.append(f"Failed to execute architecture scanner: {exc}")
    return violations


def main() -> int:
    repo_root = Path.cwd()
    try:
        manifest = load_manifest(MANIFEST)
    except (OSError, UnicodeError, ValueError, ImportError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    violations = check_single_root(repo_root, manifest)
    violations.extend(check_operations_scanner(repo_root))
    if violations:
        for violation in violations:
            print(f"[FAIL] {violation}", file=sys.stderr)
        return 1
    print("PASS: single-root layout and operations inward dependencies verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
