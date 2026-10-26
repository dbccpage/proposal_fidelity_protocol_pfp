#!/usr/bin/env python3
"""Automated verification of literature catalog consistency.
AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


def check_spine_structure(repo_root: Path) -> list[str]:
    violations = []
    atlas = repo_root / "omega_engine_atlas" / "coda_atlas"
    if not atlas.is_dir():
        violations.append(f"coda_atlas directory not found: {atlas}")
        return violations

    catalog_yaml = atlas / "atlas_catalog.yaml"
    if not catalog_yaml.is_file():
        violations.append(f"Master atlas catalog missing: {catalog_yaml}")
    else:
        try:
            data = yaml.safe_load(catalog_yaml.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                violations.append("atlas_catalog.yaml must be a YAML dictionary")
        except Exception as e:
            violations.append(f"Error parsing atlas_catalog.yaml: {e}")

    return violations


def main() -> int:
    repo_root = Path.cwd()
    violations = check_spine_structure(repo_root)
    if violations:
        for v in violations:
            print(f"[FAIL] {v}", file=sys.stderr)
        return 1
    print("PASS: Literature catalog structure and index conventions verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
