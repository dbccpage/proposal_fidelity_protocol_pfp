"""CLI entrypoint for Python Development Office architecture and pitfall scans. AuthorityEffect: None."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from omega_engine_operads.controllers.python_development_office_controller import (
    AuditRenderRequest,
    PythonDevelopmentOfficeController,
    QualityInventoryRequest,
)
from omega_engine_operads.infrastructure.python_development_office.config import (
    load_config,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m omega_engine_operads.frontend.cli.python_dev_cli",
        description="Python Development Office: Clean Architecture & Anti-Pattern Auditor",
    )
    parser.add_argument(
        "targets",
        nargs="*",
        default=["omega_engine_operations"],
        help="Directories or files to scan",
    )
    parser.add_argument(
        "--config", type=Path, default=None, help="Path to architecture config JSON/YAML"
    )
    parser.add_argument("--json", action="store_true", help="Emit structured JSON output")
    parser.add_argument("--arch-only", action="store_true", help="Execute only architecture rules")
    parser.add_argument("--pitfalls-only", action="store_true", help="Execute only AST-level rules")
    parser.add_argument(
        "--quality-inventory",
        action="store_true",
        help="Run the versioned fail-closed Python quality inventory and emit JSON",
    )
    parser.add_argument(
        "--quality-policy",
        type=Path,
        default=None,
        help="Versioned Python quality policy JSON (defaults to the packaged v1 policy)",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root used to bind inventory paths",
    )
    parser.add_argument(
        "--test-receipts",
        type=Path,
        default=None,
        help="Directory containing source-bound test execution receipt JSON files",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    controller = PythonDevelopmentOfficeController(config=load_config(args.config))
    if args.quality_inventory:
        if len(args.targets) != 1:
            raise SystemExit("--quality-inventory requires exactly one target")
        return controller.quality_inventory_and_render(
            QualityInventoryRequest(
                target=args.targets[0],
                project_root=args.project_root,
                policy_path=args.quality_policy,
                receipt_directory=args.test_receipts,
            )
        )
    return controller.audit_and_render(
        AuditRenderRequest(
            targets=args.targets,
            arch_only=args.arch_only,
            pitfalls_only=args.pitfalls_only,
            as_json=args.json,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
