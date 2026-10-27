#!/usr/bin/env python3
"""Post-execution hook: strict UTF-8 validation, BOM detection/stripping, and Ruff linting.

Inspects files modified by write_to_file / replace_file_content / multi_replace_file_content,
as well as Claude Code Write/Edit and Codex apply_patch events.

AuthorityEffect: None.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List

# Ensure hook_core is discoverable
_HOOKS_ROOT = Path(__file__).resolve().parent.parent
if str(_HOOKS_ROOT) not in sys.path:
    sys.path.insert(0, str(_HOOKS_ROOT))

import hook_core.linter  # noqa: E402
from hook_core.envelope import extract_payload  # noqa: E402
from hook_core.file_guard import (  # noqa: E402
    UTF8_BOM,
    check_workspace_containment,
    resolve_path,
)
from hook_core.file_guard import (  # noqa: E402
    check_and_clean_bom as _check_and_clean_bom,
)

__all__ = ["UTF8_BOM", "check_and_clean_bom", "extract_paths", "main", "run_ruff_lint"]


def extract_paths(raw_input: str) -> List[str]:
    """Extract modified target file paths from CLI args or stdin payload."""
    payload = extract_payload([raw_input] if raw_input else [], "", expected_kind="file")
    if payload.target_files:
        return payload.target_files
    cleaned = raw_input.strip("\"' ")
    return [cleaned] if cleaned else []


def check_and_clean_bom(file_path: Path) -> bool:
    """Check for UTF-8 BOM, strip it if found, and validate strict UTF-8 encoding."""
    return _check_and_clean_bom(file_path)


def run_ruff_lint(file_path: Path) -> int:
    """Run local ruff verification with safety flags and timeout handling."""
    # Synchronize subprocess reference to allow test patchers/monkeypatches
    hook_core.linter.subprocess = subprocess
    return hook_core.linter.run_ruff_lint(file_path)


def main() -> int:
    cli_args = sys.argv[1:]
    raw_stdin = ""
    if not cli_args:
        try:
            if not sys.stdin.isatty():
                raw_stdin = sys.stdin.read()
        except (OSError, ValueError):
            raw_stdin = ""

    payload = extract_payload(cli_args, raw_stdin, expected_kind="file")

    if payload.status == "INPUT_ERROR":
        sys.stderr.write(f"[POST_TOOL_INPUT_REFUSED] {payload.error_message}\n")
        return 2

    if payload.status == "NOT_APPLICABLE" or not payload.target_files:
        return 0

    exit_code = 0
    for path_str in payload.target_files:
        target = resolve_path(path_str, cwd=payload.cwd)
        if not target.is_file():
            sys.stderr.write(f"[POST_TOOL_INPUT_REFUSED] Modified file unavailable: {target}\n")
            return 2

        if payload.workspace_paths:
            if not check_workspace_containment(target, payload.workspace_paths):
                sys.stderr.write(
                    f"[POST_TOOL_INPUT_REFUSED] Target file {target} is outside declared workspace bounds: {payload.workspace_paths}\n"
                )
                return 2

        try:
            check_and_clean_bom(target)
        except ValueError as exc:
            sys.stderr.write(f"[POST_TOOL_INPUT_REFUSED] [RULE_FILE_STRICT_UTF8_001] {exc}\n")
            return 2

        exit_code = max(exit_code, run_ruff_lint(target))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
