"""Local Ruff linter integration with explicit safety flags and diagnostic reporting.

Enforces:
1. Explicit `--no-fix` flag to prevent unintended file mutations during lint verification.
2. Lint coverage across Python modules, type stubs, and notebooks (`.py`, `.pyi`, `.ipynb`).
3. Clear distinction between lint findings (exit 1) and operational failures (missing tool,
   abnormal exit, timeout) which return exit 2.

AuthorityEffect: None.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RUFF_EXTENSIONS = {".py", ".pyi", ".ipynb"}


def run_ruff_lint(file_path: Path, timeout: int = 10) -> int:
    """Run `ruff check --no-fix` on a Python file or notebook."""
    if not file_path.is_file():
        return 0

    suffix = file_path.suffix.lower()
    if suffix not in RUFF_EXTENSIONS:
        return 0

    cmd = [sys.executable, "-m", "ruff", "check", "--no-fix", str(file_path)]

    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if res.returncode == 0:
            return 0

        # Check if python reported missing ruff module
        stderr_msg = res.stderr or ""
        stdout_msg = res.stdout or ""

        if "No module named ruff" in stderr_msg or "No module named ruff" in stdout_msg:
            sys.stderr.write(
                f"[POST_TOOL_RUFF_UNAVAILABLE] Ruff is not installed in interpreter {sys.executable}\n"
            )
            return 2

        if res.returncode == 1:
            findings = stdout_msg.strip() or stderr_msg.strip() or "Lint violations detected"
            sys.stderr.write(
                f"[POST_TOOL_RUFF_LINT_FINDINGS] Lint violations in {file_path.name}:\n{findings}\n"
            )
            return 1

        # Abnormal exit (code >= 2)
        sys.stderr.write(
            f"[POST_TOOL_RUFF_ERROR] Ruff exited with code {res.returncode}:\n{stderr_msg.strip()}\n"
        )
        return 2

    except subprocess.TimeoutExpired:
        sys.stderr.write(
            f"[POST_TOOL_RUFF_TIMEOUT] Ruff check timed out after {timeout}s for {file_path.name}\n"
        )
        return 2
    except OSError as exc:
        sys.stderr.write(f"[POST_TOOL_RUFF_UNAVAILABLE] {type(exc).__name__}: {exc}\n")
        return 2
