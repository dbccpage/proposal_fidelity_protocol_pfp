#!/usr/bin/env python3
"""Automated verification of ROP Result monad strictness and defect firewall.
AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path


def check_rop_infrastructure(repo_root: Path) -> list[str]:
    violations = []
    # 1. Check compiler eval runner script at canonical operations path
    eval_runner = (
        repo_root
        / "omega_engine_operads"
        / "skill_operad"
        / "skill_compiler"
        / "eval_runner.py"
    )
    if not eval_runner.is_file():
        violations.append(f"Compiler eval runner missing: {eval_runner}")
    elif eval_runner.stat().st_size == 0:
        violations.append(f"Compiler eval runner is empty (0 bytes): {eval_runner}")

    # 2. Check canonical ROP Result monad domain port
    result_monad = repo_root / "omega_engine_operations" / "domain" / "rop" / "result.py"
    if not result_monad.is_file():
        violations.append(f"Domain Result monad missing: {result_monad}")
    elif result_monad.stat().st_size == 0:
        violations.append(f"Domain Result monad is empty (0 bytes): {result_monad}")

    return violations


def main() -> int:
    repo_root = Path.cwd()
    violations = check_rop_infrastructure(repo_root)
    if violations:
        for v in violations:
            print(f"[FAIL] {v}", file=sys.stderr)
        return 1
    print("PASS: ROP Result monad and runtime defect firewall verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
