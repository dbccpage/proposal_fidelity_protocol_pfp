#!/usr/bin/env python3
"""Completion Verification Gate: validates worktree changes before turn completion.

Verifies:
1. All modified text files are clean UTF-8 without BOM.
2. All modified JSON, YAML, TOML, and notebook files are syntactically valid.
3. Modified Markdown files contain no corrupted LaTeX escape control characters.
4. Modified Python files pass read-only Ruff lint checks.

AuthorityEffect: None.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

_HOOKS_ROOT = Path(__file__).resolve().parent.parent
if str(_HOOKS_ROOT) not in sys.path:
    sys.path.insert(0, str(_HOOKS_ROOT))

from hook_core.file_guard import check_and_clean_bom  # noqa: E402
from hook_core.format_validator import validate_file_format  # noqa: E402
from hook_core.linter import run_ruff_lint  # noqa: E402


def get_modified_files(repo_root: Path) -> List[Path]:
    """Retrieve list of modified and untracked files via git status."""
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode != 0:
            return []
    except Exception:
        return []

    modified: List[Path] = []
    for line in res.stdout.splitlines():
        if not line.strip():
            continue
        parts = line[3:].strip().split(" -> ")
        filename = parts[-1].strip("\"' ")
        full_path = (repo_root / filename).resolve()
        if full_path.is_file():
            modified.append(full_path)
    return modified


def verify_file(file_path: Path) -> List[str]:
    """Execute all verification checks on a single modified file."""
    errors: List[str] = []

    # 1. Encoding & BOM
    try:
        check_and_clean_bom(file_path)
    except ValueError as exc:
        errors.append(f"Encoding check failed: {exc}")

    # 2. Format syntax
    valid_format, fmt_err = validate_file_format(file_path)
    if not valid_format:
        errors.append(f"Syntax validation failed: {fmt_err}")

    # 3. Python lint
    if file_path.suffix.lower() in (".py", ".pyi", ".ipynb"):
        rc = run_ruff_lint(file_path)
        if rc != 0:
            errors.append(f"Ruff lint check returned non-zero exit code: {rc}")

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]

    # Support passing specific files to verify
    cli_targets = [Path(arg).resolve() for arg in sys.argv[1:] if not arg.startswith("-")]

    targets = cli_targets if cli_targets else get_modified_files(repo_root)

    if not targets:
        sys.stdout.write("[COMPLETION_VERIFICATION_PASS] No files selected for verification.\n")
        return 0

    all_errors: List[Tuple[Path, List[str]]] = []
    for path in targets:
        if not path.is_file():
            continue
        errs = verify_file(path)
        if errs:
            all_errors.append((path, errs))

    if all_errors:
        sys.stderr.write(
            f"\n[COMPLETION_VERIFICATION_REFUSAL] {len(all_errors)} file(s) failed completion verification:\n"
        )
        for path, errs in all_errors:
            rel = path.relative_to(repo_root) if path.is_relative_to(repo_root) else path
            sys.stderr.write(f"  - {rel}:\n")
            for e in errs:
                sys.stderr.write(f"      * {e}\n")
        sys.stderr.write("\n")
        return 2

    sys.stdout.write(
        f"[COMPLETION_VERIFICATION_PASS] All {len(targets)} file(s) verified clean (UTF-8, syntax, lint).\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
