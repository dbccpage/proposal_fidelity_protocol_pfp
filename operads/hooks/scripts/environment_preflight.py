#!/usr/bin/env python3
"""Environment Preflight Hook: validates runtime environment, tools, and worktree.

Checks:
1. Python interpreter version (pinning to Python 3.12).
2. Availability and versions of Git, Ruff, and Cargo.
3. Worktree repository root and active branch.
4. Reports baseline configuration without modifying state or installing dependencies.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from typing import Any, Dict


def check_tool(cmd: list[str]) -> Dict[str, Any]:
    """Execute tool version query and return status."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return {"available": True, "version": res.stdout.strip()}
        return {"available": False, "error": res.stderr.strip() or f"exit code {res.returncode}"}
    except FileNotFoundError:
        return {"available": False, "error": "executable not found on PATH"}
    except subprocess.TimeoutExpired:
        return {"available": False, "error": "timeout after 5s"}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def run_preflight() -> Dict[str, Any]:
    """Collect runtime environment metadata and verification status."""
    report: Dict[str, Any] = {
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "is_python_312": sys.version_info[:2] == (3, 12),
        },
        "tools": {
            "git": check_tool(["git", "--version"]),
            "ruff": check_tool([sys.executable, "-m", "ruff", "--version"]),
            "cargo": check_tool(["cargo", "--version"]),
        },
    }

    # Query Git repo status
    try:
        branch_res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        toplevel_res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        report["git_context"] = {
            "branch": branch_res.stdout.strip() if branch_res.returncode == 0 else "unknown",
            "repo_root": toplevel_res.stdout.strip() if toplevel_res.returncode == 0 else "unknown",
        }
    except Exception as exc:
        report["git_context"] = {"error": str(exc)}

    return report


def main() -> int:
    report = run_preflight()
    as_json = "--json" in sys.argv

    if as_json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        sys.stdout.write("\n[ENVIRONMENT_PREFLIGHT_STATUS]\n")
        py_info = report["python"]
        status_sym = "[OK]" if py_info["is_python_312"] else "[WARN]"
        sys.stdout.write(f"  {status_sym} Python: {py_info['version']} ({py_info['executable']})\n")
        for tool, status in report["tools"].items():
            sym = "[OK]" if status["available"] else "[WARN]"
            detail = status.get("version") or status.get("error")
            sys.stdout.write(f"  {sym} Tool {tool}: {detail}\n")
        git_ctx = report.get("git_context", {})
        if "branch" in git_ctx:
            sys.stdout.write(
                f"  [OK] Git Worktree: branch '{git_ctx['branch']}' at {git_ctx.get('repo_root')}\n"
            )
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
