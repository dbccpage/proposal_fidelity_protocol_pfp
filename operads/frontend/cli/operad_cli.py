"""
Operad CLI Entry Point.
=======================

CLI entry points for operad compilation, skill signature verification,
and budget audits.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from operads.application.operad import (
    OperadBudgetService,
    OperadCompilerService,
)


def _configure_encoding() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def run_compile(skills_dir: Path, output_json: bool = False) -> int:
    service = OperadCompilerService(skills_dir)
    receipt = service.compile_skills_garden(skills_dir)

    if output_json:
        print(json.dumps(receipt.to_dict(), indent=2))
        return 0 if receipt.passed else 1

    print("\n" + "=" * 60)
    print("=== OEWAS OPERAD COMPILATION REPORT ===")
    print("=" * 60)
    print(f"  Target Root:          {skills_dir}")
    print(f"  Receipt ID:           {receipt.receipt_id}")
    print(f"  Status:               {'PASSED' if receipt.passed else 'FAILED'}")
    print(f"  Emitted At:           {receipt.emitted_at}")
    print("  Observations:")
    for o in receipt.observations:
        print(f"    - {o.key}: {o.value}")
    print("=" * 60 + "\n")
    return 0 if receipt.passed else 1


def run_budget_audit(skills_dir: Path, output_json: bool = False) -> int:
    service = OperadBudgetService()
    receipt = service.audit_skills_directory(skills_dir)

    if output_json:
        print(json.dumps(receipt.to_dict(), indent=2))
        return 0 if receipt.passed else 1

    print("\n" + "=" * 60)
    print("=== OEWAS OPERAD BUDGET AUDIT REPORT ===")
    print("=" * 60)
    print(f"  Target Root:          {skills_dir}")
    print(f"  Receipt ID:           {receipt.receipt_id}")
    print(f"  Status:               {'PASSED' if receipt.passed else 'FAILED'}")
    print("  Observations:")
    for o in receipt.observations:
        print(f"    - {o.key}: {o.value}")
    print("=" * 60 + "\n")
    return 0 if receipt.passed else 1


def main(args: Optional[list[str]] = None) -> int:
    _configure_encoding()
    parser = argparse.ArgumentParser(description="OEWAS Coloured Operad Compiler & Budget CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available operad commands")

    compile_p = subparsers.add_parser("compile", help="Compile skills into ColouredOperad")
    compile_p.add_argument("--skills-dir", type=str, default="operads/skills", help="Path to skills directory")
    compile_p.add_argument("--json", action="store_true", help="Output JSON receipt")

    budget_p = subparsers.add_parser("budget", help="Audit skill line and byte budgets")
    budget_p.add_argument("--skills-dir", type=str, default="operads/skills", help="Path to skills directory")
    budget_p.add_argument("--json", action="store_true", help="Output JSON receipt")

    parsed = parser.parse_args(args)
    if not parsed.command:
        parser.print_help()
        return 0

    target = Path(parsed.skills_dir).resolve()
    if parsed.command == "compile":
        return run_compile(target, output_json=parsed.json)
    elif parsed.command == "budget":
        return run_budget_audit(target, output_json=parsed.json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
