#!/usr/bin/env python3
"""Mechanical Hook Gatekeeper: PostToolUse file verifier (legacy wrapper).

Delegates directly to post_tool_bom_linter to prevent policy drift.
AuthorityEffect: None.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from post_tool_bom_linter import check_and_clean_bom, main  # noqa: E402

__all__ = ["check_and_clean_bom", "check_file", "main", "subprocess"]


def check_file(file_path: Path) -> tuple[bool, str]:
    if not file_path.exists() or file_path.is_dir():
        return True, ""

    try:
        check_and_clean_bom(file_path)
    except Exception as exc:
        return False, str(exc)

    if file_path.suffix == ".py":
        try:
            res = subprocess.run(
                [sys.executable, "-m", "ruff", "check", "--no-fix", str(file_path)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode != 0:
                if "No module named ruff" in (res.stderr or ""):
                    return False, f"Ruff unavailable in interpreter: {res.stderr.strip()}"
                return (
                    False,
                    f"Ruff lint violations in {file_path}:\n{(res.stdout or res.stderr or '').strip()}",
                )
        except subprocess.TimeoutExpired:
            return False, f"Ruff lint check timed out for {file_path}"
        except OSError as exc:
            return False, f"Ruff execution error: {exc}"

    return True, ""


if __name__ == "__main__":
    sys.exit(main())
