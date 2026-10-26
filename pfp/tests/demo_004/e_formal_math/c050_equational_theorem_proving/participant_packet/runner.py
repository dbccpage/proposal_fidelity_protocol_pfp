"""Participant runner for C050: Equational Theorem Proving.
Validates the participant solver across public examples.
"""

import json
import sys
import time
from pathlib import Path

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from omega_engine_pfp.tests.demo_004.e_formal_math.c050_equational_theorem_proving.reference_solver import (
    solve,
)


def run_public_examples():
    ex_dir = Path(__file__).resolve().parent / "examples"
    case_files = sorted(ex_dir.glob("*.json"))

    print(f"Running C050 Participant Runner across {len(case_files)} public examples...")
    t0 = time.time()
    passed = 0

    for cf in case_files:
        with open(cf, "r", encoding="utf-8") as f:
            case = json.load(f)

        cid = case.get("case_id")
        res = solve(case)

        status = res.get("status")
        kind = res.get("kind")

        if status in ("SOLVED", "OUT_OF_SCOPE"):
            passed += 1
            print(f"  [PASS] {cid} (status: {status}, kind: {kind})")
        else:
            print(f"  [FAIL] {cid} -> {res}")

    elapsed = time.time() - t0
    print(f"\nResult: {passed}/{len(case_files)} passed in {elapsed:.3f}s")
    if passed == len(case_files):
        print("ALL PUBLIC EXAMPLES PASSED.")
    return passed == len(case_files)


if __name__ == "__main__":
    success = run_public_examples()
    sys.exit(0 if success else 1)
