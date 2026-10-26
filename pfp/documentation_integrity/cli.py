"""Documentation-integrity bounded-context module. AuthorityEffect: None."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from omega_engine_pfp.domain.documentation_integrity.models import (
    DocumentationCommand,
    IntegrityRequest,
)
from omega_engine_pfp.use_cases.documentation_integrity import DocumentationIntegrityService

from .domain import SCRIPT_PATH, find_repo_root
from .runtime import ConsoleOutput, HostDocumentationGateway, LocalFileSystem, SystemClock


def _inventory_parser(subcommands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    inventory = subcommands.add_parser("inventory", help="Generate provenance ledger and locks.")
    inventory.add_argument("--check", action="store_true", help="Read-only validation shortcut.")
    inventory.add_argument(
        "--refresh-archive-lock",
        action="store_true",
        help="Allow an approved raw-archive lock refresh; never use for an accidental archive edit.",
    )
    inventory.add_argument(
        "--refresh-education-lock",
        action="store_true",
        help="Allow an approved curriculum-source lock refresh.",
    )


def _validate_parser(subcommands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    validate_parser = subcommands.add_parser("validate", help="Read-only integrity validation.")
    validate_parser.add_argument(
        "--content-scope",
        choices=("governed", "all"),
        default="governed",
        help="Validate opted-in canonical pages, or all non-raw Markdown pages.",
    )
    validate_parser.add_argument(
        "--strict-content",
        action="store_true",
        help="Require frontmatter, links, visual descriptions, and encoding health across all canonical Markdown.",
    )
    validate_parser.add_argument(
        "--require-education-copies",
        action="store_true",
        help="Fail while any declared byte-preserved curriculum copy is pending.",
    )
    validate_parser.add_argument(
        "--require-llms",
        action="store_true",
        help="Fail unless a scope-safe llms.txt is present.",
    )
    validate_parser.add_argument(
        "--require-archive-records",
        action="store_true",
        help="Fail unless every raw archive file has a hash-matched reader record.",
    )
    validate_parser.add_argument(
        "--changed-base",
        help="Git base revision; changed code requires a documentation mapping update or exemption.",
    )
    validate_parser.add_argument(
        "--changed-content",
        action="store_true",
        help="With --changed-base, require the full canonical-content contract for every changed Markdown page.",
    )
    validate_parser.add_argument("--check-archive", action="store_true", help=argparse.SUPPRESS)
    validate_parser.add_argument(
        "--check-education-lock", action="store_true", help=argparse.SUPPRESS
    )
    validate_parser.add_argument("--json-report", help="Optional JSON report path.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root", type=Path, default=None, help="Repository root; inferred by default."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    _inventory_parser(subcommands)
    _validate_parser(subcommands)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        repo_root = args.repo_root.resolve() if args.repo_root else find_repo_root(SCRIPT_PATH)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    command = DocumentationCommand(args.command)
    output = ConsoleOutput()
    service = DocumentationIntegrityService(
        HostDocumentationGateway(output, LocalFileSystem()), SystemClock()
    )
    result = service.execute(IntegrityRequest(command, repo_root, args))
    if result.is_err:
        print(f"ERROR: {result.unwrap_err().message}", file=sys.stderr)
        return 1
    return result.unwrap().exit_code
