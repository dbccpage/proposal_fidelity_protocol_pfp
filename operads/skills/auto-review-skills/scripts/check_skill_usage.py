#!/usr/bin/env python3
"""Weak-hint skill reference scanner (NOT a primary retirement signal).

Phase 2 skill-compiler ruling: fixed-list substring hits are a **weak hint only**.
Zero external references is **not** sufficient evidence to archive/delete a skill.
Prefer: eval bank (`.agents/evals/skills/`), human retirement evidence, ooutwire.

Usage:
    python omega_engine_operads/skills/auto-review-skills/scripts/check_skill_usage.py [--repo-root PATH] [--skills SKILL1,SKILL2...]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

DEFAULT_TARGET_SKILLS = [
    "governance-wdp",
    "ai-safety",
    "epk-path-kernels",
    "cisco-defense-skill-scanner",
    "integration-audit-workflow",
    "maturin-verify",
    "omega-allopoietic-engine",
    "omega-lggr-qmcoda",
    "operad-lattice",
    "pydantic-models",
    "publication-quality-plotting",
    "projection-obstruction",
    "systematic-debugging",
    "woland",
]

SKIP_DIRS = {
    ".claude",
    ".codex",
    ".grok",
    ".git",
    ".venv",
    "__pycache__",
    "target",
    "node_modules",
}

SEARCH_EXTENSIONS = (
    ".md",
    ".py",
    ".rs",
    ".yaml",
    ".yml",
    ".json",
    ".sh",
    ".toml",
    ".ps1",
)


def repo_root_from(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".git").exists() and (candidate / "omega_engine_py").is_dir():
            return candidate
    return Path.cwd().resolve()


def check_usage(repo_root: Path, target_skills: list[str]) -> dict[str, list[str]]:
    results = {s: [] for s in target_skills}

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for f in files:
            if not f.endswith(SEARCH_EXTENSIONS):
                continue
            filepath = Path(root) / f
            rel_path = filepath.relative_to(repo_root).as_posix()
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                for s in target_skills:
                    if s in content:
                        # Skip counting references inside the skill's own package directory
                        if f"omega_engine_operads/skills/{s}/" in rel_path or any(
                            f"{host}/skills/{s}/" in rel_path
                            for host in (".agents", ".claude", ".codex", ".grok")
                        ):
                            continue
                        results[s].append(rel_path)
            except (OSError, UnicodeDecodeError):
                continue

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Check skill usage references in repo.")
    parser.add_argument("--repo-root", default=None, help="Repository root path")
    parser.add_argument("--skills", default=None, help="Comma-separated skill names")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
    skills = (
        [s.strip() for s in args.skills.split(",") if s.strip()]
        if args.skills
        else DEFAULT_TARGET_SKILLS
    )

    print(f"=== SKILL USAGE HINTS (weak only; {len(skills)} target skills) ===")
    print(
        "NOTE: Zero external refs is NOT a delete/archive mandate. "
        "Primary retirement evidence is human-approved + eval bank / ooutwire."
    )
    results = check_usage(root, skills)

    for s in skills:
        refs = results[s]
        print(f"\n--- {s} ({len(refs)} external references) ---")
        if not refs:
            print(
                "  [WEAK HINT] zero external substring hits — investigate; "
                "do not auto-retire on this alone."
            )
        else:
            for r in refs[:6]:
                print(f"  - {r}")
            if len(refs) > 6:
                print(f"  ... and {len(refs) - 6} more files.")

    print(
        "\nRetirement rule: check_skill_usage is weak telemetry only. "
        "See .agents/evals/skills/README.md."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
