#!/usr/bin/env python3
"""Audit script for agent panel definition files.

Usage:
    python operads/skills/auto-review-agents/scripts/agents_audit.py [--repo-root PATH]
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def repo_root_from(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".git").exists() and (candidate / "engine").is_dir():
            return candidate
    return Path.cwd().resolve()


def audit_agents(repo_root: Path) -> int:
    module_path = (
        repo_root / "operations/use_cases/packaging/agent_skill_manifest_audit.py"
    )
    spec = importlib.util.spec_from_file_location("agent_skill_manifest_audit", module_path)
    if spec is None or spec.loader is None:
        print(f"ERROR: cannot load manifest audit: {module_path}", file=sys.stderr)
        return 1
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    run_audit = module.audit_agents
    errors = module.errors

    findings, counts = run_audit(repo_root)
    print(f"=== AGENTS AUDIT ({counts['inventory']} canonical definitions) ===")
    print(f"licensed_edges={counts['licensed_edges']} empty_licenses={counts['empty_licenses']}")
    for finding in findings:
        print(finding.render())
    error_count = errors(findings)
    print(f"errors={error_count} warnings={len(findings) - error_count}")
    return error_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit agents in the agent panel.")
    parser.add_argument("--repo-root", default=None, help="Repository root path")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
    return audit_agents(root)


if __name__ == "__main__":
    sys.exit(main())
