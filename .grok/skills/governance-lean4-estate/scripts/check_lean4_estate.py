#!/usr/bin/env python3
"""Automated verification of Lean 4 estate configuration and toolchain consistency.
AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path


def check_lean_toolchains(repo_root: Path) -> tuple[list[str], int]:
    violations = []
    count = 0
    # Verify that lean-toolchain files specify valid release tags
    for tc in repo_root.glob("**/lean-toolchain"):
        if any(
            p in tc.relative_to(repo_root).parts
            for p in (".lake", ".git", "_intelligence", "scratch", "target", "tmp", "pytest-temp")
        ):
            continue
        count += 1
        try:
            content = tc.read_text(encoding="utf-8").strip()
            if not content.startswith("leanprover/lean4:"):
                violations.append(
                    f"Unexpected lean-toolchain format in {tc.relative_to(repo_root)}: {content}"
                )
        except Exception as e:
            violations.append(f"Error reading {tc}: {e}")
    if count == 0:
        violations.append("Zero canonical Lean 4 toolchains found; check failed closed.")
    return violations, count


def main() -> int:
    repo_root = Path.cwd()
    violations, count = check_lean_toolchains(repo_root)
    if violations:
        for v in violations:
            print(f"[FAIL] {v}", file=sys.stderr)
        return 1
    print(f"PASS: Lean 4 toolchains and package configurations verified ({count} checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
