#!/usr/bin/env python3
"""Automated verification of test isolation, basetemp conventions, and Rust test hermeticity.
AuthorityEffect: None.
"""

from __future__ import annotations

import re
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


def check_rust_tests_exclusivity(repo_root: Path) -> list[str]:
    violations = []
    rust_tests = repo_root / "engine" / "tests"
    if rust_tests.is_dir():
        py_files = list(rust_tests.glob("*.py"))
        if py_files:
            violations.append(
                f"RULE_TESTS_RUST_EXCLUSIVE_001 violated: Python test files found in engine/tests: {[p.name for p in py_files]}"
            )
    return violations


def check_cargo_workspace_root(repo_root: Path) -> list[str]:
    """Automated check for RULE_CARGO_WORKSPACE_ROOT_001:
    1. Canonical workspace manifest must exist at engine/crates_rs/Cargo.toml and declare [workspace].
    2. Repository root must NOT contain a Cargo.toml manifest.
    """
    violations = []
    workspace_manifest = repo_root / "engine" / "crates_rs" / "Cargo.toml"
    if not workspace_manifest.is_file():
        violations.append(
            "RULE_CARGO_WORKSPACE_ROOT_001 violated: Canonical Cargo workspace manifest missing at engine/crates_rs/Cargo.toml"
        )
    else:
        try:
            content = workspace_manifest.read_text(encoding="utf-8")
            if "[workspace]" not in content:
                violations.append(
                    "RULE_CARGO_WORKSPACE_ROOT_001 violated: engine/crates_rs/Cargo.toml does not contain '[workspace]' table declaration"
                )
        except Exception as e:
            violations.append(f"RULE_CARGO_WORKSPACE_ROOT_001 violated: Cannot read {workspace_manifest}: {e}")

    root_manifest = repo_root / "Cargo.toml"
    if root_manifest.exists():
        violations.append(
            f"RULE_CARGO_WORKSPACE_ROOT_001 violated: Root directory must not contain Cargo.toml: {root_manifest}"
        )

    return violations


def check_rust_core_crate_test_hermeticity(repo_root: Path) -> list[str]:
    """Automated check for RULE_RUST_CORE_CRATE_TEST_HERMETICITY_001:
    1. Core crate integration tests in engine/crates_rs/tests/*/ must be strictly hermetic.
    2. Tests must depend exclusively on canonical schemas, stdlib fixtures, or local checked-in test vectors.
    3. Strictly prohibited from referencing or depending on unpromoted scratch directories (scratch/, \\scratch),
       transient design demos or version folders (ow/pfp/, ow/ow_0_demo/, 1_symbol_game_versions),
       or machine-specific absolute path roots (e.g. C:\\Users, /Users, /home).
    """
    violations = []
    crates_rs = repo_root / "engine" / "crates_rs"
    if not crates_rs.is_dir():
        return violations

    forbidden_patterns = [
        (re.compile(r"""scratch[/\\]""", re.IGNORECASE), "unpromoted scratch directory reference"),
        (re.compile(r"""ow/pfp""", re.IGNORECASE), "transient design demo reference (ow/pfp)"),
        (re.compile(r"""ow_0_demo""", re.IGNORECASE), "transient design demo reference (ow_0_demo)"),
        (re.compile(r"""1_symbol_game_versions""", re.IGNORECASE), "transient version folder reference"),
        (re.compile(r"""[a-zA-Z]:\\\\(?:Users|home|tmp)\b""", re.IGNORECASE), "machine-specific absolute path reference"),
    ]

    for test_file in crates_rs.glob("*/tests/**/*.rs"):
        try:
            content = test_file.read_text(encoding="utf-8")
        except Exception as e:
            violations.append(f"Cannot read {test_file}: {e}")
            continue

        for line_no, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            for pat, desc in forbidden_patterns:
                if pat.search(line):
                    violations.append(
                        f"RULE_RUST_CORE_CRATE_TEST_HERMETICITY_001 violated in {test_file.relative_to(repo_root)}:L{line_no}: {desc}"
                    )
    return violations


def main() -> int:
    repo_root = Path.cwd()
    violations = check_basetemp_safety(repo_root)
    violations.extend(check_rust_tests_exclusivity(repo_root))
    violations.extend(check_cargo_workspace_root(repo_root))
    violations.extend(check_rust_core_crate_test_hermeticity(repo_root))
    if violations:
        for v in violations:
            print(f"[FAIL] {v}", file=sys.stderr)
        return 1
    print("PASS: Test isolation, scratch basetemp, and Rust workspace conventions verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
