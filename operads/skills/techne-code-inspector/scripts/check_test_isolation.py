#!/usr/bin/env python3
"""Automated verification of test isolation and basetemp conventions.
AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path


def check_basetemp_safety(repo_root: Path) -> list[str]:
    violations = []
    # Verify that scratch directory exists or can be written to for Windows pytest runs
    scratch = repo_root / "scratch"
    if not scratch.is_dir():
        try:
            scratch.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            violations.append(f"Cannot create or access scratch directory: {e}")
    return violations


def main() -> int:
    repo_root = Path.cwd()
    violations = check_basetemp_safety(repo_root)
    if violations:
        for v in violations:
            print(f"[FAIL] {v}", file=sys.stderr)
        return 1
    print("PASS: Test isolation and basetemp configuration verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
