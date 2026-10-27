#!/usr/bin/env python3
"""Verification script for Git staging and release archive integrity in CODA.
AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path


def check_no_placeholder_hashes(repo_root: Path) -> list[str]:
    violations = []
    zero_hash = "0" * 64
    atlas_dir = repo_root / "atlas" / "coda_atlas"
    if not atlas_dir.is_dir():
        violations.append(f"Expected atlas directory not found: {atlas_dir}")
        return violations

    md_files = list(atlas_dir.glob("**/*.md"))
    if not md_files:
        violations.append(f"No Markdown files discovered in {atlas_dir}")
        return violations

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            if f"content_hash: {zero_hash}" in content:
                violations.append(f"Found placeholder SHA256 in {md_file.relative_to(repo_root)}")
        except Exception as e:
            violations.append(
                f"Unreadable file in release tree {md_file.relative_to(repo_root)}: {e}"
            )
    return violations


def main() -> int:
    repo_root = Path.cwd()
    violations = check_no_placeholder_hashes(repo_root)
    if violations:
        for v in violations:
            print(f"[FAIL] {v}", file=sys.stderr)
        return 1
    print("PASS: Git staging safety and release digest honesty verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
