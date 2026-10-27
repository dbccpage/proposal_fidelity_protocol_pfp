#!/usr/bin/env python3
"""Audit script for skill garden packages, meta-skills, families, and registry.

Usage:
    python operads/skills/auto-review-skills/scripts/skills_audit.py [--repo-root PATH]
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


def audit_meta_and_shared(repo_root: Path) -> dict[str, bool]:
    meta_status = {}

    # 1. Audit _shared
    shared_dir = repo_root / "operads" / "skills" / "_shared"
    required_shared_files = [
        "family_registry.md",
        "constraints.md",
        "coda_gtla_paper_compliance.md",
        "council_hierarchy.md",
    ]
    if shared_dir.is_dir():
        missing_shared = [f for f in required_shared_files if not (shared_dir / f).exists()]
        meta_status["_shared"] = len(missing_shared) == 0
        if missing_shared:
            print(f"  [!] _shared missing files: {missing_shared}")
    else:
        meta_status["_shared"] = False
        print(f"  [!] Missing _shared directory: {shared_dir}")

    # 2. Audit _templates
    templates_dir = repo_root / "operads" / "skills" / "_templates"
    required_template_files = [
        "meta_skill.md",
        "skill_family.md",
        "workflow_skill.md",
    ]
    if templates_dir.is_dir():
        missing_templates = [f for f in required_template_files if not (templates_dir / f).exists()]
        meta_status["_templates"] = len(missing_templates) == 0
        if missing_templates:
            print(f"  [!] _templates missing files: {missing_templates}")
    else:
        meta_status["_templates"] = False
        print(f"  [!] Missing _templates directory: {templates_dir}")

    # 3. Audit .agents/registry
    registry_dir = repo_root / "operads" / "registry"
    required_registry_files = [
        "aliases.yaml",
        "capabilities.yaml",
        "compatibility-epoch.yaml",
        "lifecycle.yaml",
        "providers.yaml",
        "roles.yaml",
    ]
    if registry_dir.is_dir():
        missing_registry = [f for f in required_registry_files if not (registry_dir / f).exists()]
        meta_status["registry"] = len(missing_registry) == 0
        if missing_registry:
            print(f"  [!] .agents/registry missing files: {missing_registry}")
    else:
        meta_status["registry"] = False
        print(f"  [!] Missing .agents/registry directory: {registry_dir}")

    return meta_status


def purge_expired_archives(
    repo_root: Path,
    max_age_days: int = 30,
    *,
    apply: bool | None = None,
) -> int:
    """Report archive age. Hard deletion is disabled until retirement evidence exists.

    Age alone is not a defensible retirement criterion for learned capabilities.
    A future destructive mode must require a reviewed allowlist or eval/telemetry
    receipt for each candidate.
    """
    import os
    import time

    requested_apply = apply
    if requested_apply is None:
        requested_apply = os.environ.get("CORE_SKILL_PURGE", "").strip() in ("1", "true", "yes")
    apply = False

    expired_count = 0
    purged_count = 0
    archive_dirs = [
        repo_root / "operads" / "skills" / "_archived",
        repo_root / "operads" / "skills" / "_archive",
    ]
    now = time.time()
    mode = "REPORT-ONLY (hard delete disabled pending retirement evidence)"

    print(f"\n=== ARCHIVE PURGE AUDIT (Max Age: {max_age_days} Days; {mode}) ===")
    for arch_dir in archive_dirs:
        if not arch_dir.is_dir():
            continue
        for item in arch_dir.iterdir():
            if item.name.startswith("."):
                continue
            mtime = item.stat().st_mtime
            age_days = (now - mtime) / 86400
            if age_days > max_age_days:
                expired_count += 1
                print(
                    f"  [EXPIRED-REPORT-ONLY] {item.relative_to(repo_root)} "
                    f"(Age: {age_days:.1f} days > {max_age_days} days)"
                )
            else:
                print(
                    f"  [RETAINED] {item.relative_to(repo_root)} "
                    f"(Age: {age_days:.1f} days <= {max_age_days} days)"
                )

    if expired_count == 0:
        print(f"  [PASS] No expired archive items found (>{max_age_days} days).")
    elif not apply:
        print(
            f"  [INFO] {expired_count} expired item(s) reported; none deleted "
            f"(report-only). Retirement needs eval/telemetry, not mtime alone."
        )
    if requested_apply:
        print("  [BLOCKED] CORE_SKILL_PURGE/apply requested, but hard delete is disabled.")
    return purged_count if apply else 0


def audit_skills(repo_root: Path) -> int:
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
    run_audit = module.audit_skills
    errors = module.errors

    print("=== META SKILLS, FAMILIES & REGISTRY AUDIT ===")
    meta_status = audit_meta_and_shared(repo_root)
    infrastructure_errors = 0 if all(meta_status.values()) else 1
    purge_expired_archives(repo_root, max_age_days=30)
    findings, counts = run_audit(repo_root)
    print(f"\n=== SKILLS AUDIT ({counts['inventory']} canonical packages) ===")
    print(
        f"typed={counts['typed']} registered={counts['registered']} "
        f"script_packages={counts['scripts']} test_packages={counts['tests']}"
    )
    for finding in findings:
        print(finding.render())
    error_count = errors(findings) + infrastructure_errors
    print(f"errors={error_count} warnings={len(findings) - errors(findings)}")
    return error_count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit skills, meta skills, families, and registry."
    )
    parser.add_argument("--repo-root", default=None, help="Repository root path")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
    return audit_skills(root)


if __name__ == "__main__":
    sys.exit(main())
