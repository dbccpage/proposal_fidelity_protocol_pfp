#!/usr/bin/env python3
"""
check_wdp.py — Master Consolidated Invariant Checker for WDP (Witnessed Difference Programme)

Executes the unified verification pipeline across:
1. CODA 9-Layer Stack Architecture (check_coda.py)
2. Dynamic Defect / Difference Calculus & 8-Letter Alphabet (check_ddc.py)
3. Algorithm Prime Triad & Protocol Stages (check_prime_algos.py)

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path


def main() -> int:
    scripts_dir = Path(__file__).resolve().parent
    scripts = [
        ("CODA Stack Invariants", scripts_dir / "check_coda.py"),
        ("DDC Trace & Automaton Invariants", scripts_dir / "check_ddc.py"),
        ("Algorithm Prime Stages & Anti-Cheat Laws", scripts_dir / "check_prime_algos.py"),
    ]

    failed = False
    print("=" * 60)
    print("WITNESSED DIFFERENCE PROGRAMME (WDP) MASTER CHECKER")
    print("=" * 60)

    for label, script_path in scripts:
        print(f"\nRunning: {label} ({script_path.name})...")
        if not script_path.is_file():
            print(f"  [ERROR] Script not found: {script_path}")
            failed = True
            continue

        res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  [PASS] {label}")
            if res.stdout.strip():
                for line in res.stdout.strip().splitlines()[-4:]:
                    print(f"    {line}")
        else:
            print(f"  [FAIL] {label} (exit {res.returncode})")
            if res.stdout.strip():
                print(res.stdout)
            if res.stderr.strip():
                print(res.stderr)
            failed = True

    print("\n" + "=" * 60)
    if failed:
        print("WDP GATE RESULT: REFUSE (one or more invariants failed)")
        print("=" * 60)
        return 1

    print("WDP GATE RESULT: PASS (all WDP, CODA, DDC, and Prime checks verified)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
