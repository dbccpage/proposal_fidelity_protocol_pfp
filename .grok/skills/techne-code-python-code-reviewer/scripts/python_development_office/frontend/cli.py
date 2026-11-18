"""CLI entrypoint for Python Development Office architecture and pitfall scans."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from python_development_office.controllers.controller import (
    PythonDevelopmentOfficeController,
)
from python_development_office.infrastructure.config import (
    load_config,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python_antipattern_scanner.py",
        description=(
            "Python Development Office: Clean Architecture & Anti-Pattern "
            "Auditor. Findings are measurements; AuthorityEffect None."
        ),
    )
    parser.add_argument(
        "targets",
        nargs="*",
        default=["."],
        help="Directories or files to scan (default: the current directory)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to architecture config JSON",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON output instead of console formatting",
    )
    parser.add_argument(
        "--arch-only",
        action="store_true",
        help="Execute only architecture and layer boundary rules",
    )
    parser.add_argument(
        "--pitfalls-only",
        action="store_true",
        help="Execute only AST-level Python pitfall rules",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ValueError as exc:
        print(f"CONFIG_ERROR: {exc}", file=sys.stderr)
        return 2
    controller = PythonDevelopmentOfficeController(config=config)

    return controller.audit_and_render(
        targets=args.targets,
        arch_only=args.arch_only,
        pitfalls_only=args.pitfalls_only,
        as_json=args.json,
    )


if __name__ == "__main__":
    sys.exit(main())
